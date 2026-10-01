"""
Forecasting V1 Router - Asynchronous sales and inventory forecasting.
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any

import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_outlet_scope, require_role
from app.database import get_db_sync_dependency
from app.models.users import User
from app.models.outlet import Outlet
from app.models.commerce import Product, SaleItem
from app.models.commerce import Sale as SaleTransaction
from app.models.inventory import Inventory
from app.models.forecast import ForecastResult
from app.services.background_jobs import create_job, get_job, run_job
from app.tasks.forecasting_tasks import run_ensemble_forecast

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/forecasting",
    tags=["Forecasting"],
    dependencies=[Depends(get_current_user)],
)


class ModelType(str, Enum):
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
    stmt = select(Outlet).where(
        Outlet.id == outlet_id,
        Outlet.organization_id == current_user.organization_id,
        Outlet.is_deleted.is_(False),
    )
    outlet = db.execute(stmt).scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    from app.core.data_isolation import require_outlet_access

    if not require_outlet_access(current_user, outlet_id):
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
    stmt = (
        select(SaleItem.quantity)
        .join(SaleTransaction, SaleTransaction.id == SaleItem.sale_id)
        .where(
            and_(
                SaleTransaction.outlet_id == outlet_id,
                SaleTransaction.sale_date >= cutoff,
            )
        )
    )
    if product_id is not None:
        stmt = stmt.where(SaleItem.product_id == product_id)

    results = db.execute(stmt).scalars().all()
    return np.array(results) if results else np.array([])


@router.post("/sales", response_model=ForecastResponse)
async def get_sales_forecast(
    background_tasks: BackgroundTasks,
    outlet_id: int = Query(..., description="Outlet ID"),
    horizon: int = Query(7, description="Forecast horizon in days (7,14,30)"),
    model: ModelType = Query(ModelType.ENSEMBLE, description="Forecasting model"),
    product_id: Optional[int] = Query(None, description="Product ID for product-level forecasting"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_sync_dependency),
) -> ForecastResponse:
    """Generate sales forecast using specified model."""
    _get_outlet_with_access_check(outlet_id, current_user, db)

    if horizon not in [7, 14, 30]:
        raise HTTPException(status_code=400, detail="Horizon must be 7, 14, or 30 days")

    if model != ModelType.ENSEMBLE:
        raise HTTPException(status_code=400, detail="The supported production model is ensemble")

    task_id = create_job(owner_user_id=current_user.id, outlet_id=outlet_id)
    background_tasks.add_task(
        run_job,
        task_id,
        run_ensemble_forecast,
        outlet_id,
        product_id,
        horizon,
    )

    return ForecastResponse(
        task_id=task_id,
        status="pending",
        message="Forecast computation has started. Check /api/v1/forecasting/status/{task_id}",
    )


@router.get("/inventory-depletion", response_model=InventoryDepletionResponse)
async def get_inventory_depletion(
    outlet_id: int = Query(..., description="Outlet ID"),
    product_ids: List[int] = Query(..., description="List of product IDs"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_sync_dependency),
) -> InventoryDepletionResponse:
    """Calculate inventory depletion forecasts and reorder recommendations."""
    _get_outlet_with_access_check(outlet_id, current_user, db)

    results: List[InventoryDepletionItem] = []
    for product_id in product_ids:
        product = db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.organization_id == current_user.organization_id,
                Product.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
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

        current_stock = inventory.current_stock if inventory else 0
        actuals = _get_last_30d_actuals(outlet_id, product_id, db)
        daily_demand = float(actuals.sum() / 30) if actuals.size else 0.0

        days_until_stockout = float("inf")
        if daily_demand > 0:
            days_until_stockout = max(0.0, current_stock / daily_demand)

        reorder_date = (datetime.utcnow() + timedelta(days=max(0.0, days_until_stockout - 3))).strftime("%Y-%m-%d")

        results.append(
            InventoryDepletionItem(
                product_id=product_id,
                product_name=product.name,
                current_stock=int(current_stock),
                daily_demand_forecast=round(daily_demand, 2),
                days_until_stockout=round(days_until_stockout, 1) if np.isfinite(days_until_stockout) else None,
                reorder_recommended_by_date=reorder_date,
                urgency_score=100 - min(100, days_until_stockout * 3) if np.isfinite(days_until_stockout) else 0,
            )
        )

    results.sort(key=lambda item: item.urgency_score, reverse=True)
    return InventoryDepletionResponse(outlet_id=outlet_id, products=results)


@router.get("/scenarios", response_model=ForecastScenariosResponse)
async def get_forecast_scenarios(
    outlet_id: int = Query(..., description="Outlet ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_sync_dependency),
) -> ForecastScenariosResponse:
    """Generate forecast scenarios based on historical sales data."""
    _get_outlet_with_access_check(outlet_id, current_user, db)

    cutoff = datetime.utcnow() - timedelta(days=365)
    stmt = (
        select(
            func.date(SaleTransaction.sale_date),
            func.sum(SaleItem.quantity),
        )
        .join(SaleItem, SaleItem.sale_id == SaleTransaction.id)
        .where(
            and_(
                SaleTransaction.outlet_id == outlet_id,
                SaleTransaction.sale_date >= cutoff,
            )
        )
    )
    stmt = stmt.group_by(func.date(SaleTransaction.sale_date)).order_by(func.date(SaleTransaction.sale_date))
    results = [float(row[1] or 0) for row in db.execute(stmt).all()]
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
    background_tasks: BackgroundTasks,
    outlet_id: int = Query(..., description="Outlet ID"),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db_sync_dependency),
) -> ForecastResponse:
    """Retrain forecasting models with latest data."""
    from app.core.data_isolation import require_outlet_access

    if not require_outlet_access(current_user, outlet_id):
        raise HTTPException(status_code=403, detail="Cannot retrain models for another outlet")

    task_id = create_job(owner_user_id=current_user.id, outlet_id=outlet_id)
    background_tasks.add_task(run_job, task_id, run_ensemble_forecast, outlet_id, None, 30)
    return ForecastResponse(
        task_id=task_id,
        status="retraining_started",
        message="Model retraining is running in the background.",
    )


@router.get("/accuracy", response_model=ForecastAccuracyResponse)
async def get_forecast_accuracy(
    outlet_id: Optional[int] = Query(None, description="Filter by outlet ID"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_sync_dependency),
) -> ForecastAccuracyResponse:
    """Get forecast accuracy metrics for the last 90 days."""
    cutoff = datetime.utcnow() - timedelta(days=90)
    stmt = select(ForecastResult).where(ForecastResult.created_at >= cutoff)

    if outlet_id is not None:
        _get_outlet_with_access_check(outlet_id, current_user, db)
        stmt = stmt.where(ForecastResult.outlet_id == outlet_id)
    else:
        allowed_outlets = get_outlet_scope(current_user, db)
        stmt = stmt.where(ForecastResult.outlet_id.in_(allowed_outlets or [-1]))

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
    db: Session = Depends(get_db_sync_dependency),
) -> TaskStatusResponse:
    """Check the status of a forecasting task."""
    job = get_job(task_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Forecast job not found or expired")
    if job.get("owner_user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Forecast job not found or expired")
    execution_status = job["status"]
    raw_state = execution_status.upper()

    response = TaskStatusResponse(
        task_id=task_id,
        status=execution_status,
        raw_state=raw_state,
    )

    if execution_status in {"complete", "failed"}:
        job_result = job.get("result")
        if execution_status == "complete" and isinstance(job_result, dict):
            # Fetch the actual forecast data from the database
            outlet_id = job_result.get("outlet_id")
            product_id = job_result.get("product_id")

            if outlet_id is not None:
                _get_outlet_with_access_check(int(outlet_id), current_user, db)
                # Get the latest forecasts for this outlet/product combination
                records = (
                    db.query(ForecastResult)
                    .filter(ForecastResult.outlet_id == outlet_id, ForecastResult.product_id == product_id)
                    .order_by(ForecastResult.created_at.desc())
                    .limit(10)
                    .all()
                )

                models_data = {}
                metrics_data = {}
                for rec in records:
                    if rec.model_type not in models_data:
                        try:
                            models_data[rec.model_type] = json.loads(rec.forecast_json)
                        except (TypeError, ValueError, json.JSONDecodeError):
                            models_data[rec.model_type] = []
                        metrics_data[rec.model_type] = {
                            "mape": rec.mape,
                            "rmse": rec.rmse,
                            "mae": rec.mae,
                        }

                # Format into a merged array for the frontend Recharts
                merged_forecasts = []
                # Use ensemble as the base for dates
                ensemble_data = models_data.get("ensemble", [])

                for i, row in enumerate(ensemble_data):
                    date_val = row.get("date")
                    merged_point = {
                        "date": date_val,
                        "forecast": row.get("forecast"),
                        "lower_bound": row.get("lower_bound"),
                        "upper_bound": row.get("upper_bound"),
                        "isHistorical": False,
                    }

                    if "prophet" in models_data and i < len(models_data["prophet"]):
                        merged_point["prophet"] = models_data["prophet"][i].get("forecast")
                        merged_point["prophetLower"] = models_data["prophet"][i].get("lower_bound")
                        merged_point["prophetUpper"] = models_data["prophet"][i].get("upper_bound")
                    if "xgboost" in models_data and i < len(models_data["xgboost"]):
                        merged_point["xgboost"] = models_data["xgboost"][i].get("forecast")
                    merged_forecasts.append(merged_point)

                response.result = {"task_result": job_result, "forecasts": merged_forecasts, "metrics": metrics_data}
            else:
                response.result = job_result
        else:
            response.result = {"status": "failed", "message": "Forecast generation failed"}

    return response


# ── P5-T3: Z-Score Anomaly Detection ─────────────────────────────────────────


@router.get("/anomalies")
async def revenue_anomalies(
    outlet_id: int = Query(default=1, description="Outlet ID"),
    lookback_days: int = Query(default=90, ge=30, le=365),
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(get_current_user),
):
    """
    Detect anomalous revenue days using z-score analysis.
    - **Drops** (z < -2.0)  → concern
    - **Spikes** (z > 3.0) → investigate
    """
    from app.services.anomaly_detection import detect_revenue_anomalies

    try:
        _get_outlet_with_access_check(outlet_id, current_user, db)
        anomalies = detect_revenue_anomalies(db, outlet_id, lookback_days)
        return {
            "success": True,
            "total_anomalies": len(anomalies),
            "lookback_days": lookback_days,
            "anomalies": anomalies,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error in anomaly detection")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error evaluating anomalies",
        )


@router.get("/product-anomalies")
async def product_demand_anomalies(
    outlet_id: int = Query(default=1, description="Outlet ID"),
    lookback_days: int = Query(default=30, ge=7, le=180),
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(get_current_user),
):
    """Detect products with anomalously high or low demand (z-score analysis)"""
    from app.services.anomaly_detection import detect_product_anomalies

    try:
        _get_outlet_with_access_check(outlet_id, current_user, db)
        anomalies = detect_product_anomalies(db, outlet_id, lookback_days)
        return {
            "success": True,
            "total_anomalies": len(anomalies),
            "lookback_days": lookback_days,
            "anomalies": anomalies,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Product anomaly error")
        raise HTTPException(status_code=500, detail="Product anomaly analysis failed")
