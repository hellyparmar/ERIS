from app.api.celery_app import celery_app
# ML imports are deferred to task execution to save startup RAM
from app.database import get_db_sync
from app.models.sales import SaleTransaction
from sqlalchemy import select
import pandas as pd
import logging
import json

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.forecasting_tasks.run_prophet_forecast")
def run_prophet_forecast(self, outlet_id: int, product_id: int = None, horizon: int = 30, tenant_id: str = None):
    logger.info(f"Running prophet forecast for outlet {outlet_id} with tenant context {tenant_id}")
    try:
        with get_db_sync(tenant_id=tenant_id) as db:
            stmt = select(SaleTransaction.transaction_date.label('date'), SaleTransaction.quantity.label('y'))
            stmt = stmt.where(SaleTransaction.outlet_id == outlet_id)
            if product_id:
                stmt = stmt.where(SaleTransaction.product_id == product_id)
                
            results = db.execute(stmt).all()
            if not results:
                return {"status": "failed", "message": "No sales data found"}
                
            df = pd.DataFrame([{"date": r.date, "y": float(r.y)} for r in results])
            # aggregate by date
            df['date'] = pd.to_datetime(df['date']).dt.date
            df = df.groupby('date')['y'].sum().reset_index()
            
            from app.ml.forecasting.prophet_forecaster import ProphetForecaster
            forecaster = ProphetForecaster(session=db, outlet_id=outlet_id)
            forecaster.train(df)
            forecast_df = forecaster.predict(periods=horizon)
            
            # Save results
            from app.models.forecast import ForecastResult
            
            metrics = forecaster.evaluate(df)
            mape = metrics.get('mape', 0.0)
            
            forecast_data = forecast_df[['ds', 'yhat']].tail(horizon).copy()
            forecast_data['ds'] = forecast_data['ds'].dt.strftime('%Y-%m-%d')
            result_data = forecast_data.to_dict('records')
            
            # Check if exists
            existing = db.query(ForecastResult).filter(
                ForecastResult.outlet_id == outlet_id,
                ForecastResult.product_id == product_id,
                ForecastResult.model_type == "prophet"
            ).first()
            
            if existing:
                existing.forecast_json = json.dumps(result_data)
                existing.mape = mape
            else:
                forecast_record = ForecastResult(
                    outlet_id=outlet_id,
                    product_id=product_id,
                    model_type="prophet",
                    forecast_json=json.dumps(result_data),
                    mape=mape,
                    rmse=None,
                    mae=None,
                )
                db.add(forecast_record)
            db.commit()
            
            return {"status": "success", "mape": mape}
    except Exception as e:
        logger.error(f"Prophet task failed: {e}")
        return {"status": "failed", "error": str(e)}
