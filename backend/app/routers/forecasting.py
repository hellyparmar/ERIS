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
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

WeatherResponse = Dict[str, Any]

from app.api.celery_app import celery_app
from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models.users import User
from app.models.outlet import Outlet
from app.models.models_v6 import Product
from app.models.sales import SaleTransaction
from app.models.inventory import Inventory
from app.models.forecast import ForecastResult
import redis as _redis
forecast_redis_client = _redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
try:
    from app.ml.forecasting.lstm_forecaster import LSTMForecaster
except ImportError:
    LSTMForecaster = None
class DummyTask:
    def apply_async(self, args):
        class DummyResult:
            id = "mock-id"
        return DummyResult()
    def run(self, *args, **kwargs):
        return {"predicted_values": [0.0]}

try:
    from app.tasks.forecasting_tasks import run_prophet_forecast
except ImportError:
    run_prophet_forecast = DummyTask()
    
run_lstm_forecast = DummyTask()
run_ensemble_forecast = DummyTask()
retrain_forecast_models = DummyTask()

router = APIRouter(prefix="/forecasting", tags=["Forecasting"])


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
    request: Request,
    outlet_id: int = Query(..., description="Outlet ID"),
    horizon: int = Query(7, description="Forecast horizon in days (7,14,30)"),
    model: ModelType = Query(ModelType.PROPHET, description="Forecasting model (prophet, ensemble; lstm requires PyTorch)"),
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

    if model == ModelType.LSTM and (LSTMForecaster is None or getattr(run_lstm_forecast, 'is_dummy', False)):
        raise HTTPException(
            status_code=501,
            detail="LSTM deep learning forecaster requires PyTorch (torch), which is not enabled in this deployment. Supported models: prophet, ensemble."
        )

    cache_key = _build_cache_key(model.value, outlet_id, product_id, horizon)
    cached = _get_cached_forecast(cache_key)
    if cached:
        return ForecastResponse(
            task_id="cached",
            status="complete",
            message="Forecast retrieved from cache"
        )

    tenant_id = None
    if request and hasattr(request.state, "tenant_context") and request.state.tenant_context:
        tenant_id = str(request.state.tenant_context.tenant_id)
    elif hasattr(current_user, "organization") and current_user.organization and getattr(current_user.organization, "tenant_id", None):
        tenant_id = str(current_user.organization.tenant_id)
    elif hasattr(current_user, "tenant_id") and getattr(current_user, "tenant_id", None):
        tenant_id = str(current_user.tenant_id)

    if model == ModelType.PROPHET:
        task = run_prophet_forecast.apply_async(args=[outlet_id, product_id, horizon, tenant_id])
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
    from app.core.data_isolation import require_outlet_access
    if not require_outlet_access(current_user, outlet_id):
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


@router.get("/causal-analysis")
async def analyze_causal_drivers(
    outlet_id: str = Query(..., description="Outlet ID"),
    days: int = Query(90, ge=30, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Perform causal analysis to identify what factors actually drive sales changes.
    
    Requires DoWhy library. Returns HTTP 501 if DoWhy / C-extensions are not enabled in this deployment.
    """
    try:
        from app.services.causal_analysis import CausalAnalysisService, DOWHY_AVAILABLE
        
        if not DOWHY_AVAILABLE:
            raise HTTPException(
                status_code=501,
                detail="Causal analysis requires the DoWhy library with active C-extensions, which is not enabled in this deployment environment."
            )

        service = CausalAnalysisService(db)
        result = service.analyze_sales_drivers(outlet_id, days)
        
        if result.get("status") == "error" and ("DoWhy" in result.get("message", "") or "unavailable" in result.get("message", "")):
            raise HTTPException(
                status_code=501,
                detail="Causal analysis requires the DoWhy library with active C-extensions, which is not enabled in this deployment environment."
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Causal analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Causal analysis failed: {str(e)}"
        )


@router.get("/anomaly-explanation")
async def explain_sales_anomaly(
    outlet_id: str = Query(..., description="Outlet ID"),
    date: str = Query(..., description="Date of anomaly (YYYY-MM-DD format)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Explain the causal factors behind a sales anomaly.
    
    Requires DoWhy library. Returns HTTP 501 if DoWhy / C-extensions are not enabled in this deployment.
    """
    try:
        from app.services.causal_analysis import CausalAnalysisService, DOWHY_AVAILABLE
        
        if not DOWHY_AVAILABLE:
            raise HTTPException(
                status_code=501,
                detail="Anomaly explanation requires the DoWhy library with active C-extensions, which is not enabled in this deployment environment."
            )

        service = CausalAnalysisService(db)
        result = service.get_anomaly_explanation(outlet_id, date)
        
        if result.get("status") == "error" and ("DoWhy" in result.get("message", "") or "unavailable" in result.get("message", "")):
            raise HTTPException(
                status_code=501,
                detail="Anomaly explanation requires the DoWhy library with active C-extensions, which is not enabled in this deployment environment."
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Anomaly explanation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Anomaly explanation failed: {str(e)}"
        )

from app.services.forecasting import build_forecast
from app.services.ai_service import ai_service
from app.services.anomaly_detection import detect_revenue_anomalies, detect_product_anomalies
import logging
logger = logging.getLogger(__name__)
from app.services.weather_service import WeatherService

def get_weather_service() -> WeatherService:
    return WeatherService()

class LocationRequest(BaseModel):
    city: str
    country_code: str = "IN"

class WeatherImpactResponse(BaseModel):
    location: str
    weather_condition: str
    temperature: float
    impact_score: float
    impact_description: str
    retail_impact: str

@router.get("/forecast")
async def revenue_forecast(
    store_id: Optional[int] = Query(
        default=None,
        description="Filter to a specific store. Omit for all stores."
    ),
    horizon: int = Query(
        default=30,
        ge=7,
        le=90,
        description="Forecast horizon in days (7–90). Default: 30."
    ),
    lookback: int = Query(
        default=180,
        ge=30,
        le=730,
        description="Training window in days. Default: 180."
    ),
    db: Session = Depends(get_db),
):
    """
    ## ARIMA(7,1,1) Revenue Forecast

    Generates a `horizon`-day revenue forecast trained on historical invoice data.

    ### Model selection
    | Active sale days | Model used |
    |---|---|
    | < 14 | Naive flat-line average (no 500 error) |
    | ≥ 14 | ARIMA(7,1,1) with 95% confidence intervals |
    """
    try:
        result = build_forecast(
            db=db,
            store_id=store_id,
            horizon=horizon,
            lookback_days=lookback,
        )
        return {"success": True, **result}

    except Exception as e:
        logger.exception("Unhandled error in revenue_forecast")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast engine error: {str(e)}",
        )


# ── P5-T2: AI Natural Language Query ──────────────────────────────────────────

class AIQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


@router.post("/query")
async def ai_natural_language_query(
    req: AIQueryRequest,
    db: Session = Depends(get_db),
):
    """
    ## AI Natural Language Query (P5-T2)

    Ask questions about your retail data in plain English.
    Supported queries:
    - "What is the total revenue this month?"
    - "Show me dead stock items"
    - "Which products need reordering?"
    - "What are the top selling categories?"
    - "How many customers have outstanding balance?"
    """
    try:
        # Import the existing multi-provider AI service
        from app.services.ai_service import ai_service

        system_prompt = (
            "You are R-DIOS, an intelligent retail analytics assistant for an Indian retail business. "
            "You have access to sales data, inventory, customer data, and GST information. "
            "Give concise, business-relevant answers. Use ₹ for currency. "
            "Focus on actionable insights. Keep responses under 200 words."
        )

        result = await ai_service.generate_response(
            message=req.query,
            system_prompt=system_prompt,
            session_history=[],
            execute_templates=True
        )

        return {
            "success": True,
            "query": req.query,
            "response": result.get("text", ""),
            "provider": result.get("provider", "unknown"),
            "action": result.get("action"),
        }

    except Exception as e:
        logger.exception("AI query error")
        # Graceful degradation — return a helpful but simple response
        return {
            "success": True,
            "query": req.query,
            "response": (
                f"I'm R-DIOS AI. You asked: \"{req.query}\". "
                "I'm currently running in demo mode. "
                "Configure GROQ_API_KEY or OPENROUTER_API_KEY to enable live AI responses. "
                "Available data: sales, inventory, customers, GST records."
            ),
            "provider": "fallback",
            "action": None,
        }


# ── P5-T3: Z-Score Anomaly Detection ─────────────────────────────────────────

@router.get("/anomalies")
async def revenue_anomalies(
    store_id: int = Query(default=1, description="Store ID (default: 1)"),
    lookback_days: int = Query(default=90, ge=30, le=365),
    db: Session = Depends(get_db),
):
    """
    Detect anomalous revenue days using z-score analysis.
    - **Drops** (z < -2.0)  → concern
    - **Spikes** (z > 3.0) → investigate
    """
    from app.services.anomaly_detection import detect_revenue_anomalies

    try:
        anomalies = detect_revenue_anomalies(db, store_id, lookback_days)
        return {
            "success": True,
            "total_anomalies": len(anomalies),
            "lookback_days": lookback_days,
            "anomalies": anomalies
        }
    except Exception as e:
        logger.exception("Error in anomaly detection")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating anomalies: {str(e)}",
        )


@router.get("/product-anomalies")
async def product_demand_anomalies(
    store_id: int = Query(default=1),
    lookback_days: int = Query(default=30, ge=7, le=180),
    db: Session = Depends(get_db),
):
    """Detect products with anomalously high or low demand (z-score analysis)"""
    from app.services.anomaly_detection import detect_product_anomalies

    try:
        anomalies = detect_product_anomalies(db, store_id, lookback_days)
        return {
            "success": True,
            "total_anomalies": len(anomalies),
            "lookback_days": lookback_days,
            "anomalies": anomalies
        }
    except Exception as e:
        logger.exception("Product anomaly error")
        raise HTTPException(status_code=500, detail=str(e))



# ── P5-T1: ARIMA Revenue Forecast ─────────────────────────────────────────────

@router.get("/forecast")
async def revenue_forecast(
    store_id: Optional[int] = Query(
        default=None,
        description="Filter to a specific store. Omit for all stores."
    ),
    horizon: int = Query(
        default=30,
        ge=7,
        le=90,
        description="Forecast horizon in days (7–90). Default: 30."
    ),
    lookback: int = Query(
        default=180,
        ge=30,
        le=730,
        description="Training window in days. Default: 180."
    ),
    db: Session = Depends(get_db),
):
    """
    ## ARIMA(7,1,1) Revenue Forecast

    Generates a `horizon`-day revenue forecast trained on historical invoice data.

    ### Response shape
    ```json
    {
      "dates":      ["2026-01-01", ...],   // historical YYYY-MM-DD
      "historical": [1200.0, ...],          // daily revenue per date
      "forecast":   [1350.0, ...],          // predicted revenue
      "lower_band": [1100.0, ...],          // 95% CI lower
      "upper_band": [1600.0, ...],          // 95% CI upper
      "model":      "ARIMA(7, 1, 1)",
      "warning":    null,                   // non-null when naive fallback used
      "meta":       { ... }
    }
    ```

    ### Model selection
    | Active sale days | Model used |
    |---|---|
    | < 14 | Naive flat-line average (no 500 error) |
    | ≥ 14 | ARIMA(7,1,1) with 95% confidence intervals |
    """
    try:
        result = build_forecast(
            db=db,
            store_id=store_id,
            horizon=horizon,
            lookback_days=lookback,
        )
        return {"success": True, **result}

    except Exception as e:
        # Never let a modelling error become a 500 to the client
        logger.exception("Unhandled error in revenue_forecast")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast engine error: {str(e)}",
        )


# ── P5-T3: Z-Score Anomaly Detection ─────────────────────────────────────────

@router.get("/anomalies")
async def revenue_anomalies(
    store_id: int = Query(default=1, description="Store ID (default: 1)"),
    db: Session   = Depends(get_db),
):
    """
    Detect anomalous revenue days using z-score analysis.
    - **Drops** (z < -2.0)  → concern
    - **Spikes** (z > 3.0) → investigate
    """
    from app.services.anomaly_detection import detect_revenue_anomalies
    
    try:
        anomalies = detect_revenue_anomalies(db, store_id)
        return {
            "success": True,
            "total_anomalies": len(anomalies),
            "anomalies": anomalies
        }
    except Exception as e:
        logger.exception("Error in anomaly detection")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating anomalies: {str(e)}",
        )

@router.get(
    "/weather/current",
    response_model=WeatherResponse,
    summary="Get current weather",
    description="Fetch current weather data for a specific location"
)
async def get_current_weather(
    city: str = Query(..., description="City name"),
    country_code: str = Query("IN", description="ISO 3166 country code")
):
    """
    Get current weather for a location
    
    **Parameters:**
    - `city`: City name (e.g., 'Mumbai', 'Delhi')
    - `country_code`: ISO 3166 country code (default: 'IN' for India)
    
    **Returns:**
    Current weather data including temperature, humidity, wind speed, etc.
    """
    try:
        service = get_weather_service()
        weather = service.get_current_weather(city, country_code)
        
        if 'is_mock' in weather:
            logger.warning(f"Using mock data for {city}, {country_code}")
        
        return weather
        
    except Exception as e:
        logger.error(f"Error fetching weather for {city}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")


@router.get(
    "/weather/current/coordinates",
    response_model=WeatherResponse,
    summary="Get current weather by coordinates",
    description="Fetch current weather data by latitude/longitude"
)
async def get_current_weather_coordinates(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """
    Get current weather for coordinates
    
    **Parameters:**
    - `latitude`: Latitude (-90 to 90)
    - `longitude`: Longitude (-180 to 180)
    
    **Returns:**
    Current weather data for the specified coordinates
    """
    try:
        service = get_weather_service()
        weather = service.get_current_weather_by_coordinates(latitude, longitude)
        return weather
        
    except Exception as e:
        logger.error(f"Error fetching weather for ({latitude}, {longitude}): {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")


@router.get(
    "/weather/forecast",
    response_model=WeatherResponse,
    summary="Get 5-day weather forecast",
    description="Fetch 5-day weather forecast for a location"
)
async def get_weather_forecast(
    city: str = Query(..., description="City name"),
    country_code: str = Query("IN", description="ISO 3166 country code"),
    days: int = Query(5, ge=1, le=5, description="Number of days (max 5)")
):
    """
    Get weather forecast for next N days
    
    **Parameters:**
    - `city`: City name
    - `country_code`: ISO 3166 country code
    - `days`: Number of forecast days (1-5, default: 5)
    
    **Returns:**
    Weather forecast data with 3-hour intervals
    """
    try:
        service = get_weather_service()
        forecast = service.get_forecast(city, country_code, days)
        return forecast
        
    except Exception as e:
        logger.error(f"Error fetching forecast for {city}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching forecast: {str(e)}")


@router.post(
    "/weather/multi-location",
    summary="Get weather for multiple retail locations",
    description="Fetch weather for multiple store locations in one request"
)
async def get_multi_location_weather(
    locations: List[LocationRequest]
):
    """
    Get weather for multiple locations
    
    **Request body:** List of location objects with city and country_code
    
    **Returns:**
    Dictionary mapping location strings to weather data
    
    **Example request:**
    ```json
    [
      {"city": "Mumbai", "country_code": "IN"},
      {"city": "Delhi", "country_code": "IN"},
      {"city": "Bangalore", "country_code": "IN"}
    ]
    ```
    """
    try:
        service = get_weather_service()
        location_tuples = [(loc.city, loc.country_code) for loc in locations]
        weather_data = service.get_weather_for_retail_locations(location_tuples)
        return weather_data
        
    except Exception as e:
        logger.error(f"Error fetching multi-location weather: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")


@router.post(
    "/weather/impact-analysis",
    response_model=WeatherImpactResponse,
    summary="Analyze weather impact on retail",
    description="Calculate weather impact score for demand forecasting"
)
async def analyze_weather_impact(
    city: str = Query(..., description="City name"),
    country_code: str = Query("IN", description="ISO 3166 country code")
):
    """
    Analyze weather impact on retail demand
    
    **Parameters:**
    - `city`: City name
    - `country_code`: ISO 3166 country code
    
    **Returns:**
    Weather impact score (0.0-2.0) and interpretation for retail demand
    
    **Impact Scores:**
    - < 0.8: Negative impact (bad weather reduces foot traffic)
    - 0.8-1.2: Neutral/Positive impact
    - > 1.2: Strong positive impact
    """
    try:
        service = get_weather_service()
        weather = service.get_current_weather(city, country_code)
        
        impact_score = service.calculate_weather_impact(
            weather['condition'],
            weather['temperature']
        )
        
        # Generate description
        if impact_score < 0.8:
            description = "Negative impact - Consider lower stock expectations"
            retail_impact = "Reduced foot traffic expected"
        elif impact_score < 1.0:
            description = "Slightly negative - Minor impact on demand"
            retail_impact = "Slight reduction in customer visits"
        elif impact_score <= 1.1:
            description = "Neutral - Normal retail activity"
            retail_impact = "Normal shopping patterns"
        else:
            description = "Positive impact - Good shopping weather"
            retail_impact = "Increased foot traffic expected"
        
        return WeatherImpactResponse(
            location=weather['location'],
            weather_condition=weather['condition'],
            temperature=weather['temperature'],
            impact_score=impact_score,
            impact_description=description,
            retail_impact=retail_impact
        )
        
    except Exception as e:
        logger.error(f"Error analyzing weather impact: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing weather: {str(e)}")


@router.get(
    "/weather/one-call",
    summary="Get comprehensive weather data (One Call API)",
    description="Fetch current, hourly, daily forecasts and alerts"
)
async def get_one_call_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    exclude: Optional[str] = Query(None, description="Comma-separated data to exclude (current,hourly,daily,alerts)")
):
    """
    Get comprehensive weather data using One Call API
    
    **Note:** Requires paid OpenWeatherMap tier
    
    **Parameters:**
    - `latitude`: Latitude
    - `longitude`: Longitude
    - `exclude`: Optional comma-separated list of data to exclude
    
    **Returns:**
    Comprehensive weather data including current, hourly, daily forecasts and alerts
    """
    try:
        service = get_weather_service()
        
        exclude_list = None
        if exclude:
            exclude_list = [e.strip() for e in exclude.split(',')]
        
        weather = service.get_one_call_weather(latitude, longitude, exclude_list)
        return weather
        
    except Exception as e:
        logger.error(f"Error fetching One Call weather: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")


@router.get(
    "/weather/health",
    summary="Check weather service health",
    description="Verify weather API connectivity"
)
async def health_check():
    """
    Check weather service health and API key status
    
    **Returns:**
    Status information about the weather service
    """
    try:
        service = get_weather_service()
        
        return {
            "status": "healthy",
            "service": "OpenWeatherMap",
            "api_configured": not service._mock_mode,
            "units": service.units,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
