"""
Forecasting Tasks - Celery tasks for asynchronous sales forecasting and model retraining.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.celery_app import celery_app
from app.ml.forecasting.prophet_forecaster import ProphetForecaster, redis_client as forecast_redis_client
from app.ml.forecasting.lstm_forecaster import LSTMForecaster
from app.models import SaleTransaction, ForecastResult, Product, Inventory

logger = logging.getLogger(__name__)


def _build_cache_key(
    model_type: str,
    outlet_id: int,
    product_id: Optional[int],
    horizon: int,
) -> str:
    product_key = str(product_id) if product_id is not None else "general"
    return f"forecast:{outlet_id}:{product_key}:{horizon}:{model_type}"


def _cache_forecast_result(cache_key: str, payload: Dict[str, Any], ttl: int = 21600) -> None:
    if forecast_redis_client:
        try:
            forecast_redis_client.setex(cache_key, ttl, json.dumps(payload))
            logger.info(f"Cached forecast result: {cache_key}")
        except Exception as e:
            logger.warning(f"Unable to cache forecast result: {e}")


def _get_recent_mape(db: Session, outlet_id: int, product_id: Optional[int]) -> float:
    cutoff = datetime.utcnow() - timedelta(days=30)
    stmt = db.query(SaleTransaction.quantity).filter(
        SaleTransaction.outlet_id == outlet_id,
        SaleTransaction.transaction_date >= cutoff,
    )
    if product_id is not None:
        stmt = stmt.filter(SaleTransaction.product_id == product_id)

    actuals = np.array([row[0] for row in stmt.all()])
    if len(actuals) == 0:
        return 0.0
    mean_value = actuals.mean()
    if mean_value == 0:
        return 0.0
    return float(np.mean(np.abs((actuals - mean_value) / mean_value)) * 100)


def _save_forecast_result(
    db: Session,
    outlet_id: int,
    product_id: Optional[int],
    model_type: str,
    forecast_payload: Dict[str, Any],
    mape: float,
) -> None:
    record = ForecastResult(
        outlet_id=outlet_id,
        product_id=product_id,
        model_type=model_type,
        forecast_json=json.dumps(forecast_payload),
        mape=mape,
        rmse=None,
        mae=None,
    )
    db.add(record)
    db.commit()
    logger.info(f"Saved ForecastResult for outlet={outlet_id}, product={product_id}, model={model_type}")


def _build_sales_dataframe(
    db: Session,
    outlet_id: int,
    product_id: Optional[int],
    lookback_days: int = 365,
) -> pd.DataFrame:
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    stmt = db.query(SaleTransaction.transaction_date, SaleTransaction.quantity).filter(
        SaleTransaction.outlet_id == outlet_id,
        SaleTransaction.transaction_date >= cutoff,
    )
    if product_id is not None:
        stmt = stmt.filter(SaleTransaction.product_id == product_id)

    rows = stmt.order_by(SaleTransaction.transaction_date).all()
    if not rows:
        return pd.DataFrame()

    return pd.DataFrame([{"date": row[0], "sales": row[1]} for row in rows])


@celery_app.task(name="forecasting.run_prophet_forecast")
def run_prophet_forecast(
    outlet_id: int,
    product_id: Optional[int],
    horizon: int,
) -> Dict[str, Any]:
    db: Session = next(get_db())
    try:
        sales_df = _build_sales_dataframe(db, outlet_id, product_id)
        if sales_df.empty:
            raise ValueError("No sales history available for forecasting")

        forecaster = ProphetForecaster(country_code="IN", session=db)
        forecaster.load_external_regressors(
            start_date=datetime.utcnow() - timedelta(days=365),
            end_date=datetime.utcnow(),
        )

        product_key = str(product_id) if product_id is not None else "general"
        forecaster.train(
            data=sales_df,
            product_id=product_key,
            outlet_id=outlet_id,
        )

        forecast_df = forecaster.predict(
            days_ahead=horizon,
            product_id=product_key,
            outlet_id=outlet_id,
            use_cache=True,
        )

        response = {
            "dates": forecast_df["date"].dt.strftime("%Y-%m-%d").tolist(),
            "predicted_values": forecast_df["yhat"].clip(lower=0).tolist(),
            "lower_bounds": forecast_df["yhat_lower"].clip(lower=0).tolist(),
            "upper_bounds": forecast_df["yhat_upper"].clip(lower=0).tolist(),
            "model_used": "prophet",
            "explanation_text": forecast_df["explanation"].iloc[0] if "explanation" in forecast_df.columns and len(forecast_df) > 0 else "Forecast generated using Prophet.",
        }

        mape = _get_recent_mape(db, outlet_id, product_id)
        _save_forecast_result(db, outlet_id, product_id, "prophet", response, mape)

        _cache_forecast_result(_build_cache_key("prophet", outlet_id, product_id, horizon), response)
        return response

    except Exception as exc:
        logger.error(f"Prophet forecast task failed: {exc}")
        raise
    finally:
        db.close()


@celery_app.task(name="forecasting.run_lstm_forecast")
def run_lstm_forecast(
    outlet_id: int,
    product_id: int,
    horizon: int,
) -> Dict[str, Any]:
    db: Session = next(get_db())
    try:
        forecaster = LSTMForecaster(outlet_id=outlet_id, product_id=product_id, db=db)
        forecast_data = forecaster.forecast(horizon_days=horizon, model_type="lstm")

        response = {
            "dates": forecast_data["dates"],
            "predicted_values": forecast_data["predicted_units"],
            "lower_bounds": forecast_data["confidence_lower"],
            "upper_bounds": forecast_data["confidence_upper"],
            "model_used": "lstm",
            "explanation_text": "Forecast generated using LSTM neural network.",
        }

        mape = _get_recent_mape(db, outlet_id, product_id)
        _save_forecast_result(db, outlet_id, product_id, "lstm", response, mape)

        _cache_forecast_result(_build_cache_key("lstm", outlet_id, product_id, horizon), response)
        return response

    except Exception as exc:
        logger.error(f"LSTM forecast task failed: {exc}")
        raise
    finally:
        db.close()


@celery_app.task(name="forecasting.run_ensemble_forecast")
def run_ensemble_forecast(
    outlet_id: int,
    product_id: int,
    horizon: int,
) -> Dict[str, Any]:
    db: Session = next(get_db())
    try:
        prophet_result = run_prophet_forecast.run(outlet_id, product_id, horizon)
        lstm_result = run_lstm_forecast.run(outlet_id, product_id, horizon)

        prophet_vals = np.array(prophet_result["predicted_values"])
        lstm_vals = np.array(lstm_result["predicted_values"])

        ensemble_vals = (0.6 * prophet_vals + 0.4 * lstm_vals).tolist()
        ensemble_lower = (0.6 * np.array(prophet_result["lower_bounds"]) + 0.4 * np.array(lstm_result["lower_bounds"])).tolist()
        ensemble_upper = (0.6 * np.array(prophet_result["upper_bounds"]) + 0.4 * np.array(lstm_result["upper_bounds"])).tolist()

        response = {
            "dates": prophet_result["dates"],
            "predicted_values": ensemble_vals,
            "lower_bounds": ensemble_lower,
            "upper_bounds": ensemble_upper,
            "model_used": "ensemble",
            "explanation_text": "Weighted ensemble forecast from Prophet and LSTM.",
        }

        mape = _get_recent_mape(db, outlet_id, product_id)
        _save_forecast_result(db, outlet_id, product_id, "ensemble", response, mape)

        _cache_forecast_result(_build_cache_key("ensemble", outlet_id, product_id, horizon), response)
        return response

    except Exception as exc:
        logger.error(f"Ensemble forecast task failed: {exc}")
        raise
    finally:
        db.close()


@celery_app.task(name="forecasting.retrain_models")
def retrain_forecast_models(outlet_id: int) -> Dict[str, Any]:
    db: Session = next(get_db())
    try:
        product_ids = [pid for (pid,) in db.query(Product.id).join(
            Inventory,
            (Inventory.product_id == Product.id) & (Inventory.outlet_id == outlet_id)
        ).distinct().all()]

        retrained = []
        for product_id in product_ids:
            try:
                prophet_task = run_prophet_forecast.run(outlet_id, product_id, 30)
                lstm_task = run_lstm_forecast.run(outlet_id, product_id, 30)
                retrained.append({
                    "product_id": product_id,
                    "prophet": "ok",
                    "lstm": "ok",
                })
            except Exception as inner_exc:
                logger.warning(f"Retrain failed for product {product_id}: {inner_exc}")
                retrained.append({
                    "product_id": product_id,
                    "error": str(inner_exc),
                })

        return {
            "outlet_id": outlet_id,
            "products_retrained": len(product_ids),
            "details": retrained,
        }

    except Exception as exc:
        logger.error(f"Retraining task failed: {exc}")
        raise
    finally:
        db.close()
