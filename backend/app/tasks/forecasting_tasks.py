"""Forecast computation invoked by the web process background-job runner."""

# ML imports are deferred to task execution to save startup RAM.
from app.database import get_db_sync
from app.models.commerce import Sale, SaleItem
from sqlalchemy import select
import pandas as pd
import logging
import json

logger = logging.getLogger(__name__)


def _save_forecast_results(db, outlet_id, product_id, model_type, results_data, metrics):
    from app.models.forecast import ForecastResult

    existing = (
        db.query(ForecastResult)
        .filter(
            ForecastResult.outlet_id == outlet_id,
            ForecastResult.product_id == product_id,
            ForecastResult.model_type == model_type,
        )
        .first()
    )

    if existing:
        existing.forecast_json = json.dumps(results_data)
        existing.mape = metrics.get("mape")
        existing.rmse = metrics.get("rmse")
        existing.mae = metrics.get("mae")
    else:
        forecast_record = ForecastResult(
            outlet_id=outlet_id,
            product_id=product_id,
            model_type=model_type,
            forecast_json=json.dumps(results_data),
            mape=metrics.get("mape"),
            rmse=metrics.get("rmse"),
            mae=metrics.get("mae"),
        )
        db.add(forecast_record)


def run_ensemble_forecast(outlet_id: int, product_id: int = None, horizon: int = 30):
    logger.info(f"Running ensemble forecast for outlet {outlet_id}")
    try:
        with get_db_sync() as db:
            stmt = select(Sale.sale_date.label("date"), SaleItem.quantity.label("y"))
            stmt = stmt.join(SaleItem, Sale.id == SaleItem.sale_id)
            stmt = stmt.where(Sale.outlet_id == outlet_id)
            if product_id:
                stmt = stmt.where(SaleItem.product_id == product_id)

            results = db.execute(stmt).all()
            if not results:
                return {"status": "failed", "message": "No sales data found"}

            df = pd.DataFrame([{"date": r.date, "y": float(r.y)} for r in results])
            # aggregate by date
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df = df.groupby("date")["y"].sum().reset_index()
            df = df.rename(columns={"date": "ds"})
            df["ds"] = pd.to_datetime(df["ds"])
            full_dates = pd.date_range(df["ds"].min(), df["ds"].max(), freq="D")
            df = df.set_index("ds").reindex(full_dates, fill_value=0).rename_axis("ds").reset_index()
            if len(df) < 60:
                return {"status": "failed", "message": "At least 60 days of sales history are required"}

            validation_days = min(30, max(14, len(df) // 5))
            train_df = df.iloc[:-validation_days].copy()
            validation_df = df.iloc[-validation_days:].copy()

            # 1. Prophet
            from app.ml.forecasting.prophet_forecaster import ProphetForecaster

            prophet = ProphetForecaster(session=db, outlet_id=outlet_id)
            prophet.train(train_df)
            prophet_metrics = prophet.evaluate(validation_df)
            prophet.train(df)
            prophet_df = prophet.predict(periods=horizon)
            prophet_preds = prophet_df["yhat"].tail(horizon).values
            prophet_lower = (
                prophet_df["yhat_lower"].tail(horizon).values if "yhat_lower" in prophet_df.columns else prophet_preds
            )
            prophet_upper = (
                prophet_df["yhat_upper"].tail(horizon).values if "yhat_upper" in prophet_df.columns else prophet_preds
            )
            prophet_dates = prophet_df["ds"].tail(horizon).dt.strftime("%Y-%m-%d").tolist()

            # 2. XGBoost
            from app.ml.forecasting.xgboost_forecaster import XGBoostForecaster

            xgb = XGBoostForecaster()
            xgb_df = XGBoostForecaster.create_features(df)
            # Use last 30 days for evaluation to avoid data leakage on train
            train_size = max(1, len(xgb_df) - 30)
            train_x, train_y = xgb_df.iloc[:train_size].drop(columns=["ds", "y"]), xgb_df["y"].iloc[:train_size]
            test_x, test_y = xgb_df.iloc[train_size:].drop(columns=["ds", "y"]), xgb_df["y"].iloc[train_size:]

            xgb.train(train_x, train_y, product_id=str(product_id or "default"))
            xgb_metrics = xgb.evaluate(test_x, test_y) if len(test_y) > 0 else {"mape": None, "rmse": None, "mae": None}
            all_x, all_y = xgb_df.drop(columns=["ds", "y"]), xgb_df["y"]
            xgb.train(all_x, all_y, product_id=str(product_id or "default"))

            xgb_preds = xgb.forecast(df, horizon)

            # Combine via Ensemble
            from app.ml.forecasting.ensemble import EnsembleForecaster

            ensemble = EnsembleForecaster()

            metrics_dict = {
                "prophet": prophet_metrics,
                "xgboost": xgb_metrics,
            }

            weights = ensemble.adaptive_weighting(metrics_dict)
            ensemble_preds = ensemble.combine_predictions(prophet_preds, xgb_preds, weights)

            # Prepare result arrays
            def format_results(dates, preds, lower=None, upper=None):
                results = []
                for i, (d, p) in enumerate(zip(dates, preds)):
                    r = {"date": d, "forecast": float(p)}
                    if lower is not None and upper is not None:
                        r["lower_bound"] = float(lower[i])
                        r["upper_bound"] = float(upper[i])
                    results.append(r)
                return results

            prophet_results = format_results(prophet_dates, prophet_preds, prophet_lower, prophet_upper)
            xgb_results = format_results(prophet_dates, xgb_preds)
            # For ensemble, approximate bounds based on Prophet's relative bounds
            ensemble_lower = ensemble_preds * 0.9
            ensemble_upper = ensemble_preds * 1.1
            ensemble_results = format_results(prophet_dates, ensemble_preds, ensemble_lower, ensemble_upper)

            # Aggregate metrics for Ensemble
            ensemble_metrics = {
                metric: sum(
                    weight * metrics_dict[model].get(metric, 0)
                    for weight, model in zip(weights, ["prophet", "xgboost"])
                    if metrics_dict[model].get(metric) is not None
                )
                for metric in ("mape", "rmse", "mae")
            }

            _save_forecast_results(db, outlet_id, product_id, "prophet", prophet_results, prophet_metrics)
            _save_forecast_results(db, outlet_id, product_id, "xgboost", xgb_results, xgb_metrics)
            _save_forecast_results(db, outlet_id, product_id, "ensemble", ensemble_results, ensemble_metrics)

            db.commit()
            return {
                "status": "success",
                "ensemble_mape": ensemble_metrics.get("mape"),
                "outlet_id": outlet_id,
                "product_id": product_id,
            }
    except Exception as e:
        logger.error(f"Ensemble task failed: {e}", exc_info=True)
        return {"status": "failed", "message": "Forecast generation failed"}
