"""
P5: Intelligence Router
GET /api/v1/intelligence/forecast  — ARIMA-based revenue forecasting (P5-T1)
POST /api/v1/intelligence/query    — AI Natural Language Query (P5-T2)
GET /api/v1/intelligence/anomalies — Z-score anomaly detection (P5-T3)
GET /api/v1/intelligence/product-anomalies — Product demand anomalies (P5-T3)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.db import get_db
from app.api.services.forecasting import build_forecast

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intelligence", tags=["Intelligence"])


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
        from app.api.services.ai_service import ai_service

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
    from app.api.services.anomaly_detection import detect_revenue_anomalies

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
    from app.api.services.anomaly_detection import detect_product_anomalies

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
    from app.api.services.anomaly_detection import detect_revenue_anomalies
    
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
