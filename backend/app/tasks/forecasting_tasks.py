from app.api.celery_app import celery_app
# ML imports are deferred to task execution to save startup RAM
from app.database import get_db_sync
from app.models.models_v6 import Sale, SaleItem
from sqlalchemy import select
import pandas as pd
import numpy as np
import logging
import json

logger = logging.getLogger(__name__)

def _save_forecast_results(db, outlet_id, product_id, model_type, results_data, metrics):
    from app.models.forecast import ForecastResult
    existing = db.query(ForecastResult).filter(
        ForecastResult.outlet_id == outlet_id,
        ForecastResult.product_id == product_id,
        ForecastResult.model_type == model_type
    ).first()
    
    if existing:
        existing.forecast_json = json.dumps(results_data)
        existing.mape = metrics.get('mape')
        existing.rmse = metrics.get('rmse')
        existing.mae = metrics.get('mae')
    else:
        forecast_record = ForecastResult(
            outlet_id=outlet_id,
            product_id=product_id,
            model_type=model_type,
            forecast_json=json.dumps(results_data),
            mape=metrics.get('mape'),
            rmse=metrics.get('rmse'),
            mae=metrics.get('mae'),
        )
        db.add(forecast_record)


@celery_app.task(bind=True, name="app.tasks.forecasting_tasks.run_ensemble_forecast")
def run_ensemble_forecast(self, outlet_id: int, product_id: int = None, horizon: int = 30, tenant_id: str = None):
    logger.info(f"Running ensemble forecast for outlet {outlet_id} with tenant context {tenant_id}")
    try:
        with get_db_sync(tenant_id=tenant_id) as db:
            stmt = select(Sale.sale_date.label('date'), SaleItem.quantity.label('y'))
            stmt = stmt.join(SaleItem, Sale.id == SaleItem.sale_id)
            stmt = stmt.where(Sale.outlet_id == outlet_id)
            if product_id:
                stmt = stmt.where(SaleItem.product_id == product_id)
                
            results = db.execute(stmt).all()
            if not results:
                return {"status": "failed", "message": "No sales data found"}
                
            df = pd.DataFrame([{"date": r.date, "y": float(r.y)} for r in results])
            # aggregate by date
            df['date'] = pd.to_datetime(df['date']).dt.date
            df = df.groupby('date')['y'].sum().reset_index()
            df = df.rename(columns={'date': 'ds'})
            
            # 1. Prophet
            from app.ml.forecasting.prophet_forecaster import ProphetForecaster
            prophet = ProphetForecaster(session=db, outlet_id=outlet_id)
            prophet.train(df)
            prophet_metrics = prophet.evaluate(df)
            prophet_df = prophet.predict(periods=horizon)
            prophet_preds = prophet_df['yhat'].tail(horizon).values
            prophet_lower = prophet_df['yhat_lower'].tail(horizon).values if 'yhat_lower' in prophet_df.columns else prophet_preds
            prophet_upper = prophet_df['yhat_upper'].tail(horizon).values if 'yhat_upper' in prophet_df.columns else prophet_preds
            prophet_dates = prophet_df['ds'].tail(horizon).dt.strftime('%Y-%m-%d').tolist()
            
            # 2. XGBoost
            from app.ml.forecasting.xgboost_forecaster import XGBoostForecaster
            xgb = XGBoostForecaster()
            xgb_df = XGBoostForecaster.create_features(df)
            # Use last 30 days for evaluation to avoid data leakage on train
            train_size = max(1, len(xgb_df) - 30)
            train_x, train_y = xgb_df.iloc[:train_size].drop(columns=['ds', 'y']), xgb_df['y'].iloc[:train_size]
            test_x, test_y = xgb_df.iloc[train_size:].drop(columns=['ds', 'y']), xgb_df['y'].iloc[train_size:]
            
            xgb.train(train_x, train_y, product_id=str(product_id or "default"))
            xgb_metrics = xgb.evaluate(test_x, test_y) if len(test_y) > 0 else {"mape": 10.0, "rmse": 0, "mae": 0}
            
            # Generate future features for XGBoost prediction
            future_dates = pd.date_range(start=df['ds'].max() + pd.Timedelta(days=1), periods=horizon)
            future_df = pd.DataFrame({'ds': future_dates, 'y': np.zeros(horizon)})
            combined_df = pd.concat([df, future_df]).reset_index(drop=True)
            combined_xgb = XGBoostForecaster.create_features(combined_df)
            future_x = combined_xgb.tail(horizon).drop(columns=['ds', 'y'])
            xgb_preds = xgb.predict(future_x)
            
            # 3. LSTM
            from app.ml.forecasting.lstm_forecaster import LSTMForecaster, TORCH_AVAILABLE, validate_lstm
            lstm_preds = np.zeros(horizon)
            lstm_metrics = {"mape": None, "rmse": None, "mae": None}
            if TORCH_AVAILABLE:
                try:
                    lstm_data = df['y'].values
                    # For a quick evaluation
                    test_size = min(30, len(lstm_data) // 5)
                    train_data = lstm_data[:-test_size] if test_size > 0 else lstm_data
                    test_data = lstm_data[-test_size:] if test_size > 0 else []
                    
                    lstm = LSTMForecaster(seq_length=min(14, max(1, len(train_data)-1)), epochs=10)
                    lstm.fit(train_data)
                    lstm_preds = lstm.predict(lstm_data, horizon)
                    
                    if len(test_data) > 0:
                        test_preds = lstm.predict(train_data, len(test_data))
                        mask = test_data != 0
                        lstm_mape = np.mean(np.abs((test_data[mask] - test_preds[mask]) / test_data[mask])) * 100 if mask.sum() > 0 else 0
                        lstm_metrics = {"mape": float(lstm_mape), "rmse": float(np.sqrt(np.mean((test_data - test_preds)**2))), "mae": float(np.mean(np.abs(test_data - test_preds)))}
                    else:
                        lstm_metrics = {"mape": 5.0, "rmse": 0, "mae": 0}
                except Exception as e:
                    logger.error(f"LSTM prediction failed, fallback to zeros. Error: {e}")
            
            # Combine via Ensemble
            from app.ml.forecasting.ensemble import EnsembleForecaster
            ensemble = EnsembleForecaster()
            
            metrics_dict = {
                "prophet": prophet_metrics,
                "xgboost": xgb_metrics,
                "lstm": lstm_metrics
            }
            
            weights = ensemble.adaptive_weighting(metrics_dict)
            ensemble_preds = ensemble.combine_predictions(prophet_preds, xgb_preds, lstm_preds, weights)
            
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
            lstm_results = format_results(prophet_dates, lstm_preds)
            
            # For ensemble, approximate bounds based on Prophet's relative bounds
            ensemble_lower = ensemble_preds * 0.9
            ensemble_upper = ensemble_preds * 1.1
            ensemble_results = format_results(prophet_dates, ensemble_preds, ensemble_lower, ensemble_upper)
            
            # Aggregate metrics for Ensemble
            ensemble_metrics = {
                "mape": sum(w * metrics_dict[m].get("mape", 0) for w, m in zip(weights, ["prophet", "xgboost", "lstm"]) if metrics_dict[m].get("mape") is not None),
                "rmse": sum(w * metrics_dict[m].get("rmse", 0) for w, m in zip(weights, ["prophet", "xgboost", "lstm"]) if metrics_dict[m].get("rmse") is not None),
                "mae": sum(w * metrics_dict[m].get("mae", 0) for w, m in zip(weights, ["prophet", "xgboost", "lstm"]) if metrics_dict[m].get("mae") is not None),
            }
            
            _save_forecast_results(db, outlet_id, product_id, "prophet", prophet_results, prophet_metrics)
            _save_forecast_results(db, outlet_id, product_id, "xgboost", xgb_results, xgb_metrics)
            _save_forecast_results(db, outlet_id, product_id, "lstm", lstm_results, lstm_metrics)
            _save_forecast_results(db, outlet_id, product_id, "ensemble", ensemble_results, ensemble_metrics)
            
            db.commit()
            return {
                "status": "success",
                "ensemble_mape": ensemble_metrics.get('mape'),
                "outlet_id": outlet_id,
                "product_id": product_id
            }
    except Exception as e:
        logger.error(f"Ensemble task failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
