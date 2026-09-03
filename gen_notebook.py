import json
import os

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Model Comparison: Prophet vs XGBoost vs LSTM vs Ensemble\n",
    "\n",
    "This notebook evaluates the performance of the three individual forecasting models against the inverse-error-weighted ensemble strategy on a 30-day holdout set."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "outputs": [],
   "source": [
    "import sys\n",
    "import os\n",
    "sys.path.append(os.path.abspath(os.path.join('..', '..', 'backend')))\n",
    "\n",
    "from dotenv import load_dotenv\n",
    "load_dotenv(os.path.abspath(os.path.join('..', '..', 'backend', '.env')))\n",
    "\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "import matplotlib.pyplot as plt\n",
    "from sqlalchemy import select\n",
    "from app.database import get_db_sync\n",
    "from app.models.models_v6 import Sale, SaleItem\n",
    "from app.ml.forecasting.prophet_forecaster import ProphetForecaster\n",
    "from app.ml.forecasting.xgboost_forecaster import XGBoostForecaster\n",
    "from app.ml.forecasting.lstm_forecaster import LSTMForecaster, TORCH_AVAILABLE\n",
    "from app.ml.forecasting.ensemble import EnsembleForecaster\n",
    "\n",
    "import warnings\n",
    "warnings.filterwarnings('ignore')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "metadata": {},
   "outputs": [],
   "source": [
    "def fetch_data(outlet_id=1):\n",
    "    with get_db_sync(tenant_id=\"tenant_1\") as db:\n",
    "        stmt = select(Sale.sale_date.label('date'), SaleItem.quantity.label('y'))\n",
    "        stmt = stmt.join(SaleItem, Sale.id == SaleItem.sale_id)\n",
    "        stmt = stmt.where(Sale.outlet_id == outlet_id)\n",
    "        results = db.execute(stmt).all()\n",
    "        \n",
    "        df = pd.DataFrame([{\"date\": r.date, \"y\": float(r.y)} for r in results])\n",
    "        df['date'] = pd.to_datetime(df['date']).dt.date\n",
    "        df = df.groupby('date')['y'].sum().reset_index()\n",
    "        df = df.rename(columns={'date': 'ds'})\n",
    "        return df\n",
    "\n",
    "df = fetch_data()\n",
    "print(f\"Loaded {len(df)} days of historical data.\")\n",
    "\n",
    "horizon = 30\n",
    "train_df = df.iloc[:-horizon]\n",
    "test_df = df.iloc[-horizon:]\n",
    "actuals = test_df['y'].values"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 1. Train Prophet\n",
    "prophet = ProphetForecaster(session=None, outlet_id=1)\n",
    "prophet.train(train_df)\n",
    "p_metrics = prophet.evaluate(train_df)\n",
    "p_preds = prophet.predict(periods=horizon)['yhat'].tail(horizon).values"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 2. Train XGBoost\n",
    "xgb = XGBoostForecaster()\n",
    "xgb_df = XGBoostForecaster.create_features(train_df)\n",
    "train_size = max(1, len(xgb_df) - 30)\n",
    "x_train, y_train = xgb_df.iloc[:train_size].drop(columns=['ds', 'y']), xgb_df['y'].iloc[:train_size]\n",
    "x_val, y_val = xgb_df.iloc[train_size:].drop(columns=['ds', 'y']), xgb_df['y'].iloc[train_size:]\n",
    "xgb.train(x_train, y_train)\n",
    "x_metrics = xgb.evaluate(x_val, y_val)\n",
    "\n",
    "future_dates = pd.date_range(start=train_df['ds'].max() + pd.Timedelta(days=1), periods=horizon)\n",
    "future_df = pd.DataFrame({'ds': future_dates, 'y': np.zeros(horizon)})\n",
    "combined_df = pd.concat([train_df, future_df]).reset_index(drop=True)\n",
    "combined_xgb = XGBoostForecaster.create_features(combined_df)\n",
    "future_x = combined_xgb.tail(horizon).drop(columns=['ds', 'y'])\n",
    "x_preds = xgb.predict(future_x)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 3. Train LSTM\n",
    "l_preds = np.zeros(horizon)\n",
    "l_metrics = {\"mape\": 5.0, \"rmse\": 0.0}\n",
    "if TORCH_AVAILABLE:\n",
    "    lstm_data = train_df['y'].values\n",
    "    l_train = lstm_data[:-30]\n",
    "    l_val = lstm_data[-30:]\n",
    "    lstm = LSTMForecaster(seq_length=14, epochs=20)\n",
    "    lstm.fit(l_train)\n",
    "    l_preds = lstm.predict(lstm_data, horizon)\n",
    "    val_preds = lstm.predict(l_train, 30)\n",
    "    l_metrics['mape'] = np.mean(np.abs((l_val - val_preds) / l_val)) * 100"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 4. Combine with Ensemble\n",
    "ensemble = EnsembleForecaster()\n",
    "metrics_dict = {\"prophet\": p_metrics, \"xgboost\": x_metrics, \"lstm\": l_metrics}\n",
    "weights = ensemble.adaptive_weighting(metrics_dict)\n",
    "e_preds = ensemble.combine_predictions(p_preds, x_preds, l_preds, weights)\n",
    "print(\"Assigned Weights:\", dict(zip([\"Prophet\", \"XGBoost\", \"LSTM\"], weights)))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 5. Evaluate on Holdout\n",
    "def eval_metrics(preds, actuals):\n",
    "    mask = actuals != 0\n",
    "    mape = np.mean(np.abs((actuals[mask] - preds[mask]) / actuals[mask])) * 100\n",
    "    rmse = np.sqrt(np.mean((actuals - preds)**2))\n",
    "    return mape, rmse\n",
    "\n",
    "results = []\n",
    "for name, preds in zip(['Prophet', 'XGBoost', 'LSTM', 'Ensemble'], [p_preds, x_preds, l_preds, e_preds]):\n",
    "    if name == 'LSTM' and not TORCH_AVAILABLE:\n",
    "        continue\n",
    "    m, r = eval_metrics(preds, actuals)\n",
    "    results.append({'Model': name, 'MAPE (%)': round(m, 2), 'RMSE': round(r, 2)})\n",
    "\n",
    "results_df = pd.DataFrame(results)\n",
    "display(results_df)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Plot Results\n",
    "plt.figure(figsize=(12, 6))\n",
    "plt.plot(test_df['ds'], actuals, label='Actual Sales', color='black', linewidth=2)\n",
    "plt.plot(test_df['ds'], p_preds, label='Prophet', linestyle='--')\n",
    "plt.plot(test_df['ds'], x_preds, label='XGBoost', linestyle='-.')\n",
    "if TORCH_AVAILABLE:\n",
    "    plt.plot(test_df['ds'], l_preds, label='LSTM', linestyle=':')\n",
    "plt.plot(test_df['ds'], e_preds, label='Ensemble', color='red', linewidth=2)\n",
    "plt.title('30-Day Forecast Comparison on Holdout Set')\n",
    "plt.legend()\n",
    "plt.grid(True)\n",
    "plt.show()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.10.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}

os.makedirs(r"c:\Users\littl\Downloads\eris_project\research\notebooks", exist_ok=True)
with open(r"c:\Users\littl\Downloads\eris_project\research\notebooks\model_comparison.ipynb", "w") as f:
    json.dump(notebook, f, indent=1)
