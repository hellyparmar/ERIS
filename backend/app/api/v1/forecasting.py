"""
Forecasting V1 Router - Asynchronous sales and inventory forecasting.
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any

import numpy as np
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.api.celery_app import celery_app
from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models import User, Outlet, Product, Inventory, SaleTransaction, ForecastResult
from app.ml.forecasting.prophet_forecaster import ProphetForecaster, redis_client as forecast_redis_client
from app.ml.forecasting.lstm_forecaster import LSTMForecaster
from app.api.tasks.forecasting_tasks import (
    run_prophet_forecast,
    run_lstm_forecast,
    run_ensemble_forecast,
    retrain_forecast_models,
)

router = APIRouter(prefix="/forecasting", tags=["forecasting"])


class ModelType(str, Enum):
    PROPHET = "prophet"
    LSTM = "lstm"
    ENSEMBLE = "ensemble"


class ForecastResponse(BaseModel):
    task_id: str
    status: str
    message: str


class InventoryDepletionItem(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    daily_demand_forecast: float
    days_until_stockout: Optional[float]
    reorder_recommended_by_date: str
    urgency_score: int


class InventoryDepletionResponse(BaseModel):
    outlet_id: int
    products: List[InventoryDepletionItem]


class ForecastScenario(BaseModel):
    scenario: str
    daily_units: float
    assumption: str


class ForecastScenariosResponse(BaseModel):
    outlet_id: int
    scenarios: List[Dict[str, Any]]


class ForecastAccuracyResponse(BaseModel):
    period: str
    models: Dict[str, Dict[str, Any]]
    total_forecasts: int


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    raw_state: str
    result: Optional[Any] = None


def _get_outlet_with_access_check(outlet_id: int, current_user: User, db: Session) -> Outlet:
    """Get outlet and check user access permissions."""
    stmt = select(Outlet).where(Outlet.id == outlet_id)
    outlet = db.execute(stmt).scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    if current_user.role not in ["super_admin", "area_manager"] and current_user.outlet_id != outlet_id:
        raise HTTPException(status_code=403, detail="Access denied to this outlet")

    return outlet


def _calculate_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Calculate Mean Absolute Percentage Error."""
    if actual.size == 0 or predicted.size == 0:
        return 0.0
    mask = actual != 0
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def _get_last_30d_actuals(outlet_id: int, product_id: Optional[int], db: Session) -> np.ndarray:
    """Get actual sales data for the last 30 days."""
    cutoff = datetime.utcnow() - timedelta(days=30)
    stmt = select(SaleTransaction.quantity).where(
        and_(
            SaleTransaction.outlet_id == outlet_id,
            SaleTransaction.transaction_date >= cutoff,
        )
    )
    if product_id is not None:
        stmt = stmt.where(SaleTransaction.product_id == product_id)

    results = db.execute(stmt).scalars().all()
    return np.array(results) if results else np.array([])


def _build_cache_key(model_type: str, outlet_id: int, product_id: Optional[int], horizon: int) -> str:
    """Build Redis cache key for forecast results."""
    product_key = str(product_id) if product_id is not None else "general"
    return f"forecast:{outlet_id}:{product_key}:{horizon}:{model_type}"


def _get_cached_forecast(cache_key: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached forecast from Redis."""
    if not forecast_redis_client:
        return None
    try:
        raw = forecast_redis_client.get(cache_key)
        if raw:
            return json.loads(raw)
    except Exception:
        return None
    return None


def _save_forecast_result(
    outlet_id: int,
    product_id: Optional[int],
    model_type: str,
    forecast_data: Dict[str, Any],
    mape: float,
    db: Session,
) -> None:
    """Save forecast result to database."""
    forecast_record = ForecastResult(
        outlet_id=outlet_id,
        product_id=product_id,
        model_type=model_type,
        forecast_json=json.dumps(forecast_data),
        mape=mape,
        rmse=None,
        mae=None,
    )
    db.add(forecast_record)
    db.commit()


@router.get("/sales", response_model=ForecastResponse)
async def get_sales_forecast(
    outlet_id: int = Query(..., description="Outlet ID"),
    horizon: int = Query(7, description="Forecast horizon in days (7,14,30)"),
    model: ModelType = Query(ModelType.PROPHET, description="Forecasting model"),
    product_id: Optional[int] = Query(None, description="Product ID (required for LSTM/ensemble)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ForecastResponse:
    """Generate sales forecast using specified model."""
    _get_outlet_with_access_check(outlet_id, current_user, db)

    if horizon not in [7, 14, 30]:
        raise HTTPException(status_code=400, detail="Horizon must be 7, 14, or 30 days")

    if model in [ModelType.LSTM, ModelType.ENSEMBLE] and product_id is None:
        raise HTTPException(status_code=400, detail="product_id is required for LSTM and ensemble forecasts")

    cache_key = _build_cache_key(model.value, outlet_id, product_id, horizon)
    cached = _get_cached_forecast(cache_key)
    if cached:
        return ForecastResponse(
            task_id="cached",
            status="complete",
            message="Forecast retrieved from cache"
        )

    if model == ModelType.PROPHET:
        task = run_prophet_forecast.apply_async(args=[outlet_id, product_id, horizon])
    elif model == ModelType.LSTM:
        task = run_lstm_forecast.apply_async(args=[outlet_id, product_id, horizon])
    else:
        task = run_ensemble_forecast.apply_async(args=[outlet_id, product_id, horizon])

    return ForecastResponse(
        task_id=task.id,
        status="pending",
        message="Forecast computation has started. Check /api/v1/forecasting/status/{task_id}",
    )


@router.get("/inventory-depletion", response_model=InventoryDepletionResponse)
async def get_inventory_depletion(
    outlet_id: int = Query(..., description="Outlet ID"),
    product_ids: List[int] = Query(..., description="List of product IDs"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InventoryDepletionResponse:
    """Calculate inventory depletion forecasts and reorder recommendations."""
    _get_outlet_with_access_check(outlet_id, current_user, db)

    results: List[InventoryDepletionItem] = []
    for product_id in product_ids:
        product = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
        if not product:
            continue

        inventory = db.execute(
            select(Inventory).where(
                and_(
                    Inventory.outlet_id == outlet_id,
                    Inventory.product_id == product_id,
                )
            )
        ).scalar_one_or_none()

        current_stock = inventory.stock_level if inventory else 0
        forecast = run_lstm_forecast.run(outlet_id, product_id, 30)
        daily_demand = float(np.mean(forecast["predicted_values"])) if forecast["predicted_values"] else 0.0

        days_until_stockout = float('inf')
        if daily_demand > 0:
            days_until_stockout = max(0.0, current_stock / daily_demand)

        reorder_date = (
            datetime.utcnow() + timedelta(days=max(0.0, days_until_stockout - 3))
        ).strftime("%Y-%m-%d")

        results.append(InventoryDepletionItem(
            product_id=product_id,
            product_name=product.name,
            current_stock=int(current_stock),
            daily_demand_forecast=round(daily_demand, 2),
            days_until_stockout=round(days_until_stockout, 1) if np.isfinite(days_until_stockout) else None,
            reorder_recommended_by_date=reorder_date,
            urgency_score=100 - min(100, days_until_stockout * 3) if np.isfinite(days_until_stockout) else 0,
        ))

    results.sort(key=lambda item: item.urgency_score, reverse=True)
    return InventoryDepletionResponse(outlet_id=outlet_id, products=results)


@router.get("/scenarios", response_model=ForecastScenariosResponse)
async def get_forecast_scenarios(
    outlet_id: int = Query(..., description="Outlet ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ForecastScenariosResponse:
    """Generate forecast scenarios based on historical sales data."""
    _get_outlet_with_access_check(outlet_id, current_user, db)

    cutoff = datetime.utcnow() - timedelta(days=365)
    stmt = select(SaleTransaction.quantity).where(
        and_(
            SaleTransaction.outlet_id == outlet_id,
            SaleTransaction.transaction_date >= cutoff,
        )
    )
    results = db.execute(stmt).scalars().all()
    if not results:
        raise HTTPException(status_code=404, detail="No sales data available")

    sales_array = np.array(results)
    mean_sales = float(sales_array.mean())
    std_sales = float(sales_array.std())

    scenarios = [
        {
            "scenario": "base",
            "7_day_revenue": round(mean_sales * 7, 2),
            "30_day_revenue": round(mean_sales * 30, 2),
            "daily_units": round(mean_sales, 2),
            "assumption": "Historical average performance continues",
        },
        {
            "scenario": "optimistic",
            "7_day_revenue": round((mean_sales + std_sales) * 7, 2),
            "30_day_revenue": round((mean_sales + std_sales) * 30, 2),
            "daily_units": round(mean_sales + std_sales, 2),
            "assumption": "Sales increase by one standard deviation",
        },
        {
            "scenario": "pessimistic",
            "7_day_revenue": round(max(0, mean_sales - std_sales) * 7, 2),
            "30_day_revenue": round(max(0, mean_sales - std_sales) * 30, 2),
            "daily_units": round(max(0, mean_sales - std_sales), 2),
            "assumption": "Sales decrease by one standard deviation",
        },
    ]

    return ForecastScenariosResponse(outlet_id=outlet_id, scenarios=scenarios)


@router.post("/retrain", response_model=ForecastResponse)
async def retrain_models(
    outlet_id: int = Query(..., description="Outlet ID"),
    current_user: User = Depends(require_role("super_admin", "outlet_manager")),
    db: Session = Depends(get_db),
) -> ForecastResponse:
    """Retrain forecasting models with latest data."""
    if current_user.role == "outlet_manager" and current_user.outlet_id != outlet_id:
        raise HTTPException(status_code=403, detail="Cannot retrain models for another outlet")

    task = retrain_forecast_models.apply_async(args=[outlet_id])
    return ForecastResponse(
        task_id=task.id,
        status="retraining_started",
        message="Model retraining is running in the background.",
    )


@router.get("/accuracy", response_model=ForecastAccuracyResponse)
async def get_forecast_accuracy(
    outlet_id: Optional[int] = Query(None, description="Filter by outlet ID"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ForecastAccuracyResponse:
    """Get forecast accuracy metrics for the last 90 days."""
    cutoff = datetime.utcnow() - timedelta(days=90)
    stmt = select(ForecastResult).where(ForecastResult.created_at >= cutoff)

    if outlet_id is not None:
        _get_outlet_with_access_check(outlet_id, current_user, db)
        stmt = stmt.where(ForecastResult.outlet_id == outlet_id)
    elif current_user.role == "outlet_manager":
        stmt = stmt.where(ForecastResult.outlet_id == current_user.outlet_id)

    if model_type:
        stmt = stmt.where(ForecastResult.model_type == model_type)

    results = db.execute(stmt).scalars().all()
    metrics: Dict[str, Dict[str, Any]] = {}

    for record in results:
        model_name = record.model_type
        if model_name not in metrics:
            metrics[model_name] = {
                "forecast_count": 0,
                "mape_values": [],
            }
        metrics[model_name]["forecast_count"] += 1
        if record.mape is not None:
            metrics[model_name]["mape_values"].append(record.mape)

    summary = {}
    for model_name, data in metrics.items():
        values = np.array(data["mape_values"])
        summary[model_name] = {
            "forecast_count": data["forecast_count"],
            "avg_mape": float(values.mean()) if values.size else 0.0,
            "std_mape": float(values.std()) if values.size else 0.0,
            "min_mape": float(values.min()) if values.size else 0.0,
            "max_mape": float(values.max()) if values.size else 0.0,
        }

    return ForecastAccuracyResponse(
        period="last 90 days",
        models=summary,
        total_forecasts=sum(item["forecast_count"] for item in summary.values()),
    )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_forecast_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> TaskStatusResponse:
    """Check the status of a forecasting task."""
    result = AsyncResult(task_id, app=celery_app)
    state = result.state
    status_map = {
        "PENDING": "pending",
        "STARTED": "running",
        "RETRY": "running",
        "SUCCESS": "complete",
        "FAILURE": "failed",
        "REVOKED": "failed",
    }
    execution_status = status_map.get(state, "pending")

    response = TaskStatusResponse(
        task_id=task_id,
        status=execution_status,
        raw_state=state,
    )

    if result.ready():
        response.result = result.result if state == "SUCCESS" else str(result.result)

    return response
