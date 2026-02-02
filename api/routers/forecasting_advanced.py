from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/forecasting")

class ForecastRequest(BaseModel):
    history_days: int = 30
    forecast_days: int = 7
    growth_rate: float = 0.0  # Percentage change simulation

class ImpactAnalysis(BaseModel):
    projected_revenue: float
    projected_margin: float
    warehouse_utilization: float
    shipping_risk: str

class ForecastPoint(BaseModel):
    date: str
    value: float
    lower_bound: float
    upper_bound: float

class ProphetResponse(BaseModel):
    forecast: List[ForecastPoint]
    metrics: dict
    impact: Optional[ImpactAnalysis] = None

@router.post("/prophet/predict", response_model=ProphetResponse)
async def generate_forecast(request: ForecastRequest):
    try:
        # 1. Generate realistic synthetic history data
        dates = pd.date_range(end=datetime.now(), periods=request.history_days)
        base_value = 1000
        trend = np.linspace(0, 500, request.history_days)
        seasonality = 200 * np.sin(np.linspace(0, 4 * np.pi, request.history_days))
        noise = np.random.normal(0, 50, request.history_days)
        values = base_value + trend + seasonality + noise
        
        # Apply growth
        if request.growth_rate != 0:
            values = values * (1 + request.growth_rate)

        df = pd.DataFrame({'ds': dates, 'y': values})

        # 2. Train Prophet Model
        m = Prophet(daily_seasonality=True, yearly_seasonality=False)
        m.fit(df)

        # 3. Predict Future
        future = m.make_future_dataframe(periods=request.forecast_days)
        forecast = m.predict(future)

        # 4. Format Response
        result = []
        future_forecast = forecast.tail(request.forecast_days)
        total_volume = 0
        
        for _, row in future_forecast.iterrows():
            val = max(0, row['yhat']) # Ensure no negative sales
            total_volume += val
            result.append({
                "date": row['ds'].strftime('%Y-%m-%d'),
                "value": round(val, 2),
                "lower_bound": round(max(0, row['yhat_lower']), 2),
                "upper_bound": round(max(0, row['yhat_upper']), 2)
            })

        # 5. Prescriptive Analysis Logic
        avg_price = 1250.0  # Avg ticket size
        margin_percent = 0.32 # 32% margin
        
        projected_rev = total_volume * avg_price
        projected_margin = projected_rev * margin_percent
        
        # Warehouse: 0.8 sq ft per unit required
        warehouse_sqft = total_volume * 0.8
        
        # Shipping Risk based on daily volume spikes
        max_daily_vol = future_forecast['yhat'].max()
        if max_daily_vol > 2000:
            shipping_risk = "High (Capacity Exceeded)"
        elif max_daily_vol > 1500:
            shipping_risk = "Medium (Delays Likely)"
        else:
            shipping_risk = "Low (Optimal)"

        impact_analysis = ImpactAnalysis(
            projected_revenue=round(projected_rev, 2),
            projected_margin=round(projected_margin, 2),
            warehouse_utilization=round(warehouse_sqft, 2),
            shipping_risk=shipping_risk
        )

        # Calculate basic metrics
        rmse = np.sqrt(np.mean((df['y'] - forecast['yhat'][:request.history_days])**2))

        return {
            "forecast": result,
            "metrics": {
                "rmse": round(rmse, 2),
                "status": "Success",
                "model": "Facebook Prophet"
            },
            "impact": impact_analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forecast/{store_id}/{product_id}")
async def get_forecast(store_id: int, product_id: int, days: int = 7, growth_rate: float = 0.0):
    """
    GET endpoint for frontend compatibility.
    Calls the POST /prophet/predict endpoint internally.
    """
    request = ForecastRequest(
        history_days=365,
        forecast_days=days,
        growth_rate=growth_rate
    )
    return await generate_forecast(request)
