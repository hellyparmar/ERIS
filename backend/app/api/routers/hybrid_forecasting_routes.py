"""
Hybrid Forecasting API Routes

Endpoints:
- GET /api/forecasting/hybrid - Hybrid forecast with explanation
- GET /api/forecasting/hybrid/explain - Detailed SHAP explanation
- GET /api/forecasting/hybrid/comparison - Compare Prophet vs XGBoost
- POST /api/forecasting/hybrid/batch - Batch forecasts for multiple stores/products
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.db.session import get_db
from app.api.services.hybrid_forecasting import (
    HybridForecastingService,
    format_explanation_for_dashboard,
)

router = APIRouter(prefix="/api/forecasting", tags=["forecasting"])


@router.get("/hybrid")
async def get_hybrid_forecast(
    db: Session = Depends(get_db),
    store_id: Optional[int] = Query(None, description="Store ID"),
    product_id: Optional[int] = Query(None, description="Product ID (optional)"),
    horizon: int = Query(30, ge=1, le=90, description="Forecast days (1-90)"),
) -> dict:
    """
    Get hybrid forecast with SHAP-based explanations.
    
    Combines Prophet seasonality model with XGBoost trend detection.
    Returns predictions + human-readable explanations for dashboard.
    
    Example:
        GET /api/forecasting/hybrid?store_id=1&horizon=30
        
    Response:
    {
        "status": "success|fallback|error",
        "forecast": [
            {
                "date": "2026-03-03",
                "value": 15000.50,
                "lower_bound": 13500.45,
                "upper_bound": 16500.55,
                "prophet_value": 14800,
                "xgboost_value": 15200
            },
            ...
        ],
        "explanation": {
            "summary": "Predicted +20% increase driven by upcoming Holi festival and positive weekly trend",
            "predicted_value": 15000.50,
            "base_value": 12500.00,
            "change_pct": 20.0,
            "confidence": 0.85,
            "key_factors": [
                {
                    "factor": "is_holiday",
                    "impact": 35.2,
                    "direction": "positive",
                    "explanation": "Holiday impact is pushing sales UP"
                },
                {
                    "factor": "rolling_mean_7",
                    "impact": 28.1,
                    "direction": "positive",
                    "explanation": "Weekly average trend is pushing sales UP"
                }
            ]
        },
        "metadata": {
            "model_type": "hybrid",
            "data_points": 180
        }
    }
    """
    try:
        service = HybridForecastingService(db)
        result = service.forecast_with_explanation(
            store_id=store_id,
            product_id=product_id,
            horizon=horizon,
        )
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting error: {str(e)}")


@router.get("/hybrid/explain")
async def get_detailed_explanation(
    db: Session = Depends(get_db),
    store_id: Optional[int] = Query(None),
    product_id: Optional[int] = Query(None),
) -> dict:
    """
    Get detailed SHAP explanation for predictions.
    
    Returns granular feature importance analysis suitable for detailed
    admin dashboard "Why this prediction?" view.
    
    Response includes:
    - Summary of prediction direction and magnitude
    - Top 10 features driving the forecast
    - SHAP value (impact on prediction)
    - Contribution percentage
    - Business interpretation of each factor
    """
    try:
        service = HybridForecastingService(db)
        result = service.forecast_with_explanation(
            store_id=store_id,
            product_id=product_id,
            horizon=30,
        )
        
        explanation = result.get("explanation", {})
        return format_explanation_for_dashboard(explanation)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")


@router.get("/hybrid/comparison")
async def compare_models(
    db: Session = Depends(get_db),
    store_id: Optional[int] = Query(None),
    horizon: int = Query(30, ge=1, le=90),
) -> dict:
    """
    Compare Prophet vs XGBoost forecasts side-by-side.
    
    Useful for understanding model behavior and divergences.
    When predictions diverge significantly, it may indicate:
    - Prophet: Catching seasonal patterns
    - XGBoost: Detecting anomalies or trend spikes
    
    Response:
    {
        "comparison": [
            {
                "date": "2026-03-03",
                "prophet": 14800,
                "xgboost": 15200,
                "ensemble": 15000,
                "divergence_pct": 2.7
            },
            ...
        ],
        "summary": {
            "avg_prophet": 14500,
            "avg_xgboost": 15000,
            "avg_ensemble": 14750,
            "correlation": 0.92
        }
    }
    """
    try:
        service = HybridForecastingService(db)
        result = service.forecast_with_explanation(
            store_id=store_id,
            horizon=horizon,
        )
        
        forecast = result.get("forecast", [])
        
        comparison = []
        for point in forecast:
            divergence = (
                abs(point["prophet_value"] - point["xgboost_value"]) /
                (point["prophet_value"] + 1e-8) * 100
            )
            comparison.append({
                "date": point["date"],
                "prophet": point["prophet_value"],
                "xgboost": point["xgboost_value"],
                "ensemble": point["value"],
                "divergence_pct": divergence,
            })
        
        # Calculate summary statistics
        import numpy as np
        prophet_vals = [p["prophet"] for p in comparison]
        xgb_vals = [p["xgboost"] for p in comparison]
        
        summary = {
            "avg_prophet": float(np.mean(prophet_vals)) if prophet_vals else 0,
            "avg_xgboost": float(np.mean(xgb_vals)) if xgb_vals else 0,
            "avg_ensemble": float(np.mean([p["ensemble"] for p in comparison])) if comparison else 0,
            "correlation": float(
                np.corrcoef(prophet_vals, xgb_vals)[0, 1]
                if len(prophet_vals) > 1 and len(xgb_vals) > 1 else 1.0
            ),
        }
        
        return {
            "comparison": comparison,
            "summary": summary,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")


@router.post("/hybrid/batch")
async def batch_forecast(
    db: Session = Depends(get_db),
    stores: Optional[list] = Query(None, description="List of store IDs"),
    horizon: int = Query(30, ge=1, le=90),
) -> dict:
    """
    Generate forecasts for multiple stores in batch.
    
    Useful for:
    - Executive dashboard showing all stores
    - Automated supply chain recommendations
    - Multi-store performance comparison
    
    Request:
        POST /api/forecasting/hybrid/batch?stores=1&stores=2&stores=3&horizon=30
    
    Response:
    {
        "stores": {
            "1": {
                "forecast": [...],
                "explanation": {...},
                "status": "success"
            },
            "2": {
                "forecast": [...],
                "explanation": {...},
                "status": "success"
            }
        },
        "timestamp": "2026-03-02T10:30:00Z"
    }
    """
    try:
        if not stores:
            raise HTTPException(status_code=400, detail="No stores specified")
        
        service = HybridForecastingService(db)
        results = {}
        
        for store_id in stores:
            try:
                result = service.forecast_with_explanation(
                    store_id=store_id,
                    horizon=horizon,
                )
                results[str(store_id)] = result
            except Exception as e:
                results[str(store_id)] = {
                    "status": "error",
                    "error": str(e),
                }
        
        from datetime import datetime
        
        return {
            "stores": results,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch error: {str(e)}")


@router.get("/hybrid/dashboard-widget")
async def get_dashboard_widget(
    db: Session = Depends(get_db),
    store_id: Optional[int] = Query(None),
) -> dict:
    """
    Get prediction widget formatted for admin dashboard display.
    
    Simplified response perfect for dashboard card/widget rendering:
    - Compact summary
    - Visual indicators (up/down, confidence)
    - Color codes for risk levels
    
    Response:
    {
        "card_title": "30-Day Sales Forecast",
        "predicted_value": "₹15,000",
        "change": "+20%",
        "direction": "up",
        "confidence": "High (85%)",
        "summary": "Predicted increase driven by Holi festival...",
        "key_factor": "Upcoming holiday impact",
        "risk_level": "low",
        "forecast_points": [
            {"date": "Mar 3", "value": 15000}
        ]
    }
    """
    try:
        service = HybridForecastingService(db)
        result = service.forecast_with_explanation(
            store_id=store_id,
            horizon=30,
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail="Forecast generation failed")
        
        forecast = result.get("forecast", [])
        explanation = result.get("explanation", {})
        
        if not forecast:
            raise HTTPException(status_code=404, detail="No forecast data available")
        
        avg_value = sum(p["value"] for p in forecast) / len(forecast)
        change_pct = explanation.get("change_pct", 0)
        confidence = explanation.get("confidence_score", 0)
        
        # Determine risk level based on confidence and volatility
        if confidence < 0.5:
            risk_level = "high"
        elif confidence < 0.7:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Format key factors
        key_factors = explanation.get("key_factors", [])
        main_factor = (
            key_factors[0]["explanation"] if key_factors else "Historical trends"
        )
        
        # Compact forecast for widget (every 3 days)
        widget_forecast = [
            {
                "date": forecast[i]["date"][-5:],  # "MM-DD"
                "value": int(forecast[i]["value"]),
            }
            for i in range(0, len(forecast), 3)
        ]
        
        def format_currency(val):
            if val >= 100000:
                return f"₹{val/100000:.1f}L"
            elif val >= 1000:
                return f"₹{val/1000:.1f}K"
            return f"₹{int(val)}"
        
        return {
            "card_title": "30-Day Sales Forecast",
            "predicted_value": format_currency(avg_value),
            "change": f"{'+' if change_pct >= 0 else ''}{change_pct:.1f}%",
            "direction": "up" if change_pct >= 0 else "down",
            "confidence": f"{'High' if confidence > 0.7 else 'Medium' if confidence > 0.5 else 'Low'} ({confidence*100:.0f}%)",
            "summary": explanation.get("summary", ""),
            "key_factor": main_factor,
            "risk_level": risk_level,
            "forecast_points": widget_forecast,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Widget error: {str(e)}")
