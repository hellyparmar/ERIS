import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(backend_dir)
os.chdir(backend_dir)

from dotenv import load_dotenv
load_dotenv('.env')

import pandas as pd
import numpy as np
from sqlalchemy import select
from app.database import get_db_sync
from app.models.models_v6 import Sale, SaleItem
from app.ml.forecasting.prophet_forecaster import ProphetForecaster
from app.ml.forecasting.xgboost_forecaster import XGBoostForecaster
from app.ml.forecasting.lstm_forecaster import LSTMForecaster, TORCH_AVAILABLE
from app.ml.forecasting.ensemble import EnsembleForecaster

def run_comparison():
    print("Fetching historical data...")
    with get_db_sync(tenant_id="tenant_1") as db:
        stmt = select(Sale.sale_date.label('date'), SaleItem.quantity.label('y'))
        stmt = stmt.join(SaleItem, Sale.id == SaleItem.sale_id)
        stmt = stmt.where(Sale.outlet_id == 1)
        results = db.execute(stmt).all()
        if not results:
            print("No data found!")
            return
            
        df = pd.DataFrame([{"date": r.date, "y": float(r.y)} for r in results])
        df['date'] = pd.to_datetime(df['date']).dt.date
        df = df.groupby('date')['y'].sum().reset_index()
        df = df.rename(columns={'date': 'ds'})

    if len(df) < 60:
        print(f"Not enough data to run comparison: {len(df)} rows")
        return

    # Hold out last 30 days
    train_df = df.iloc[:-30]
    test_df = df.iloc[-30:]
    horizon = 30
    
    print("Training Prophet...")
    prophet = ProphetForecaster(session=None, outlet_id=1)
    prophet.train(train_df)
    prophet_metrics = prophet.evaluate(train_df)
    prophet_preds = prophet.predict(periods=horizon)['yhat'].tail(horizon).values
    
    print("Training XGBoost...")
    xgb = XGBoostForecaster()
    xgb_df = XGBoostForecaster.create_features(train_df)
    train_size = max(1, len(xgb_df) - 30)
    xgb_train_x, xgb_train_y = xgb_df.iloc[:train_size].drop(columns=['ds', 'y']), xgb_df['y'].iloc[:train_size]
    xgb_test_x, xgb_test_y = xgb_df.iloc[train_size:].drop(columns=['ds', 'y']), xgb_df['y'].iloc[train_size:]
    xgb.train(xgb_train_x, xgb_train_y, product_id="test")
    xgb_metrics = xgb.evaluate(xgb_test_x, xgb_test_y)
    
    future_dates = pd.date_range(start=train_df['ds'].max() + pd.Timedelta(days=1), periods=horizon)
    future_df = pd.DataFrame({'ds': future_dates, 'y': np.zeros(horizon)})
    combined_df = pd.concat([train_df, future_df]).reset_index(drop=True)
    combined_xgb = XGBoostForecaster.create_features(combined_df)
    future_x = combined_xgb.tail(horizon).drop(columns=['ds', 'y'])
    xgb_preds = xgb.predict(future_x)
    
    lstm_preds = np.zeros(horizon)
    lstm_metrics = {"mape": 5.0, "rmse": 0, "mae": 0}
    if TORCH_AVAILABLE:
        print("Training LSTM...")
        lstm_data = train_df['y'].values
        val_size = min(30, len(lstm_data) // 5)
        l_train = lstm_data[:-val_size] if val_size > 0 else lstm_data
        l_val = lstm_data[-val_size:] if val_size > 0 else []
        lstm = LSTMForecaster(seq_length=min(14, len(l_train)-1), epochs=20)
        lstm.fit(l_train)
        lstm_preds = lstm.predict(lstm_data, horizon)
        
        if len(l_val) > 0:
            val_preds = lstm.predict(l_train, len(l_val))
            mask = l_val != 0
            l_mape = np.mean(np.abs((l_val[mask] - val_preds[mask]) / l_val[mask])) * 100 if mask.sum() > 0 else 0
            lstm_metrics = {"mape": float(l_mape), "rmse": float(np.sqrt(np.mean((l_val - val_preds)**2))), "mae": float(np.mean(np.abs(l_val - val_preds)))}
            
    print("Combining Ensemble...")
    ensemble = EnsembleForecaster()
    metrics_dict = {"prophet": prophet_metrics, "xgboost": xgb_metrics, "lstm": lstm_metrics}
    weights = ensemble.adaptive_weighting(metrics_dict)
    ensemble_preds = ensemble.combine_predictions(prophet_preds, xgb_preds, lstm_preds, weights)
    
    actuals = test_df['y'].values
    
    def calc_metrics(preds):
        mask = actuals != 0
        mape = np.mean(np.abs((actuals[mask] - preds[mask]) / actuals[mask])) * 100
        rmse = np.sqrt(np.mean((actuals - preds)**2))
        return mape, rmse

    print("\n--- Model Comparison on Holdout (30 days) ---")
    p_mape, p_rmse = calc_metrics(prophet_preds)
    x_mape, x_rmse = calc_metrics(xgb_preds)
    l_mape, l_rmse = calc_metrics(lstm_preds) if TORCH_AVAILABLE else (0, 0)
    e_mape, e_rmse = calc_metrics(ensemble_preds)
    
    print(f"Prophet: MAPE={p_mape:.2f}%, RMSE={p_rmse:.2f}")
    print(f"XGBoost: MAPE={x_mape:.2f}%, RMSE={x_rmse:.2f}")
    if TORCH_AVAILABLE:
        print(f"LSTM: MAPE={l_mape:.2f}%, RMSE={l_rmse:.2f}")
    print(f"Ensemble: MAPE={e_mape:.2f}%, RMSE={e_rmse:.2f}")
    print(f"Ensemble Weights: Prophet={weights[0]:.2f}, XGBoost={weights[1]:.2f}, LSTM={weights[2]:.2f}")

if __name__ == '__main__':
    run_comparison()
