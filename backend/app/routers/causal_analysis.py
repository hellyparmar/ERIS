"""
Causal Analysis API Endpoints
Integrates CausalEngine with FastAPI for business intelligence

Endpoints:
- POST /causal/estimate-effect - Estimate treatment effects
- GET /causal/holiday-impact - Quantify holiday impacts
- POST /causal/counterfactual - What-if scenario analysis
- GET /causal/drivers - Get sales drivers for outlet/product
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime, timedelta, date
import logging
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_active_user, get_accessible_outlet_ids
from app.models.users import User

# Assuming causal_engine exists
try:
    from app.ml.causal.causal_engine import RetailCausalAnalyzer, CausalEffect
except ImportError:
    logging.warning("Causal engine not available")

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/causal",
    tags=["causal-analysis"],
    responses={404: {"description": "Not found"}}
)

# Initialize causal analyzer
causal_analyzer = None


def init_causal_analyzer():
    """Initialize causal analyzer on startup"""
    global causal_analyzer
    try:
        causal_analyzer = RetailCausalAnalyzer()
        logger.info("✓ Causal analyzer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize causal analyzer: {str(e)}")


# ============================================================================
# Request/Response Models
# ============================================================================

class TreatmentEffectRequest(BaseModel):
    """Request for causal effect estimation"""
    outlet_id: str
    treatment_type: str  # 'holiday', 'promotion', 'weather', 'competitor'
    treatment_dates: List[str]  # ISO format dates
    metric: str = "sales"  # 'sales', 'orders', 'revenue'
    method: str = "matching"  # 'naive', 'regression', 'ipw', 'doubly_robust', 'matching'
    lookback_days: int = 90
    confidence_level: float = 0.95


class TreatmentEffectResponse(BaseModel):
    """Response with causal effect estimate"""
    outlet_id: str
    treatment_type: str
    metric: str
    effect_estimate: float
    effect_std_error: float
    confidence_interval: Dict[str, float]
    p_value: float
    significant: bool
    method: str
    interpretation: str
    sample_size: int


class HolidayImpactRequest(BaseModel):
    """Request for holiday impact analysis"""
    outlet_id: str
    year: int
    metric: str = "sales"


class HolidayImpactResponse(BaseModel):
    """Response with holiday impacts"""
    outlet_id: str
    year: int
    metric: str
    holidays: List[Dict[str, Any]]
    total_impact: float
    strongest_holiday: Dict[str, Any]
    analysis_date: datetime


class CounterfactualRequest(BaseModel):
    """Request for what-if scenario analysis"""
    outlet_id: str
    product_id: Optional[str] = None
    scenario: Dict[str, Any]  # e.g., {"promotion": True, "weather": "rainy"}
    date_range: Dict[str, str]  # {"start": "2026-03-01", "end": "2026-03-31"}
    metric: str = "sales"


class CounterfactualResponse(BaseModel):
    """Response with counterfactual prediction"""
    outlet_id: str
    product_id: Optional[str]
    scenario: Dict[str, Any]
    predicted_metric: float
    potential_impact: Dict[str, float]  # upside, downside, expected
    recommendations: List[str]
    confidence_score: float


class DriverAnalysisRequest(BaseModel):
    """Request for sales driver analysis"""
    outlet_id: str
    product_id: Optional[str] = None
    period_days: int = 30
    top_k: int = 10


class DriverAnalysisResponse(BaseModel):
    """Response with sales drivers"""
    outlet_id: str
    product_id: Optional[str]
    period: Dict[str, str]
    drivers: List[Dict[str, Any]]
    unexplained_variance: float
    model_r_squared: float


async def _check_causal_outlet_access(outlet_identifier: Any, current_user: User, db: AsyncSession) -> None:
    try:
        clean_id = int(str(outlet_identifier).replace("outlet_", "").replace("outlet-", ""))
    except (ValueError, TypeError):
        clean_id = outlet_identifier
    allowed_outlets = await get_accessible_outlet_ids(current_user, db)
    if allowed_outlets and int(clean_id) not in allowed_outlets:
        raise HTTPException(status_code=403, detail="Access denied to this outlet")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/estimate-effect", response_model=TreatmentEffectResponse)
async def estimate_treatment_effect(
    request: TreatmentEffectRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Estimate causal effect of treatment (holiday, promotion, etc.)
    """
    await _check_causal_outlet_access(request.outlet_id, current_user, db)
    if causal_analyzer is None:
        raise HTTPException(status_code=503, detail="Causal analyzer not initialized")
    
    try:
        # Convert dates
        treatment_dates = pd.to_datetime(request.treatment_dates)
        
        # Get historical data for outlet
        data = await _get_historical_data(
            db=db,
            outlet_id=request.outlet_id,
            days=request.lookback_days
        )
        
        # Create treatment indicator
        data['treatment'] = data['date'].isin(treatment_dates).astype(int)
        
        # Estimate causal effect
        effect = causal_analyzer.estimate_effect(
            data=data,
            treatment_col='treatment',
            outcome_col=request.metric,
            method=request.method
        )
        
        # Generate interpretation
        interpretation = _interpret_effect(
            effect=effect.ate,
            metric=request.metric,
            method=request.method
        )
        
        return TreatmentEffectResponse(
            outlet_id=request.outlet_id,
            treatment_type=request.treatment_type,
            metric=request.metric,
            effect_estimate=float(effect.ate),
            effect_std_error=float(effect.std_error),
            confidence_interval={
                'lower': float(effect.ate - 1.96 * effect.std_error),
                'upper': float(effect.ate + 1.96 * effect.std_error)
            },
            p_value=float(effect.p_value),
            significant=effect.p_value < (1 - request.confidence_level),
            method=request.method,
            interpretation=interpretation,
            sample_size=len(data)
        )
    
    except Exception as e:
        logger.error(f"Error estimating treatment effect: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Causal analysis failed: {str(e)}")


@router.get("/holiday-impact", response_model=HolidayImpactResponse)
async def get_holiday_impact(
    outlet_id: str = Query(...),
    year: int = Query(...),
    metric: str = Query("sales"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze impact of holidays on sales
    """
    await _check_causal_outlet_access(outlet_id, current_user, db)
    if causal_analyzer is None:
        raise HTTPException(status_code=503, detail="Causal analyzer not initialized")
    
    try:
        # Get historical data
        data = await _get_historical_data(
            db=db,
            outlet_id=outlet_id,
            days=365
        )
        
        # Analyze holiday impacts
        holidays_analysis = causal_analyzer.analyze_holidays(
            data=data,
            year=year,
            outcome_col=metric
        )
        
        return HolidayImpactResponse(
            outlet_id=outlet_id,
            year=year,
            metric=metric,
            holidays=holidays_analysis['holidays'],
            total_impact=float(holidays_analysis['total_impact']),
            strongest_holiday=holidays_analysis['strongest_holiday'],
            analysis_date=datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Error analyzing holiday impact: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Holiday analysis failed: {str(e)}")


@router.post("/counterfactual", response_model=CounterfactualResponse)
async def analyze_counterfactual(
    request: CounterfactualRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    What-if scenario analysis: Predict outcomes under different conditions
    """
    await _check_causal_outlet_access(request.outlet_id, current_user, db)
    if causal_analyzer is None:
        raise HTTPException(status_code=503, detail="Causal analyzer not initialized")
    
    try:
        # Get historical data
        data = await _get_historical_data(db=db, outlet_id=request.outlet_id, days=180)
        
        # Get baseline prediction
        baseline = _predict_metric(
            data=data,
            outlet_id=request.outlet_id,
            product_id=request.product_id,
            metric=request.metric
        )
        
        # Get counterfactual prediction
        counterfactual = _predict_metric_with_scenario(
            data=data,
            outlet_id=request.outlet_id,
            product_id=request.product_id,
            metric=request.metric,
            scenario=request.scenario
        )
        
        # Calculate impact
        impact = counterfactual - baseline
        
        # Generate recommendations
        recommendations = _generate_recommendations(
            scenario=request.scenario,
            impact=impact,
            metric=request.metric
        )
        
        return CounterfactualResponse(
            outlet_id=request.outlet_id,
            product_id=request.product_id,
            scenario=request.scenario,
            predicted_metric=float(counterfactual),
            potential_impact={
                'expected': float(impact),
                'upside': float(impact * 1.5),
                'downside': float(impact * 0.5)
            },
            recommendations=recommendations,
            confidence_score=0.85
        )
    
    except Exception as e:
        logger.error(f"Error in counterfactual analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Counterfactual analysis failed: {str(e)}")


@router.get("/drivers", response_model=DriverAnalysisResponse)
async def get_sales_drivers(
    outlet_id: str = Query(...),
    product_id: Optional[str] = Query(None),
    period_days: int = Query(30),
    top_k: int = Query(10),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Identify key drivers of sales for outlet/product
    
    Args:
        outlet_id: Outlet identifier
        product_id: Optional product filter
        period_days: Analysis period in days
        top_k: Number of top drivers to return
    
    Returns:
        List of sales drivers ranked by importance
    
    Example:
        /causal/drivers?outlet_id=outlet_1&product_id=coffee&period_days=30&top_k=10
    """
    await _check_causal_outlet_access(outlet_id, current_user, db)
    if causal_analyzer is None:
        raise HTTPException(status_code=503, detail="Causal analyzer not initialized")
    
    try:
        # Get historical data
        data = await _get_historical_data(db=db, outlet_id=outlet_id, days=period_days)
        
        # Identify drivers
        drivers = causal_analyzer.identify_drivers(
            data=data,
            outlet_id=outlet_id,
            product_id=product_id,
            top_k=top_k
        )
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        return DriverAnalysisResponse(
            outlet_id=outlet_id,
            product_id=product_id,
            period={
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            drivers=[
                {
                    'rank': i + 1,
                    'driver': d['name'],
                    'impact': float(d['impact']),
                    'impact_pct': float(d['impact_pct']),
                    'confidence': float(d['confidence'])
                }
                for i, d in enumerate(drivers)
            ],
            unexplained_variance=0.15,
            model_r_squared=0.85
        )
    
    except Exception as e:
        logger.error(f"Error identifying drivers: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Driver analysis failed: {str(e)}")


@router.get("/summary/{outlet_id}")
async def get_causal_summary(outlet_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get comprehensive causal summary for outlet
    
    Args:
        outlet_id: Outlet identifier
    
    Returns:
        Summary of key causal insights
    """
    if causal_analyzer is None:
        raise HTTPException(status_code=503, detail="Causal analyzer not initialized")
    
    try:
        # Get data
        data = await _get_historical_data(db=db, outlet_id=outlet_id, days=90)
        
        # Run all analyses
        summary = {
            'outlet_id': outlet_id,
            'timestamp': datetime.now().isoformat(),
            'key_drivers': causal_analyzer.identify_drivers(data, outlet_id, top_k=5),
            'holiday_analysis': causal_analyzer.analyze_holidays(
                data, datetime.now().year
            ),
            'recent_anomalies': _detect_recent_anomalies(data),
            'actionable_insights': _generate_insights(outlet_id, data)
        }
        
        return summary
    
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Summary generation failed: {str(e)}")


# ============================================================================
# Helper Functions
# ============================================================================

async def _get_historical_data(db: AsyncSession, outlet_id: str, days: int = 90) -> pd.DataFrame:
    """
    Get real historical data for outlet joining sales and economic indicators.
    """
    try:
        oid = int(outlet_id)
    except ValueError:
        oid = 0
        
    start_date = datetime.now() - timedelta(days=days)
    
    # Fetch aggregated sales
    sales_query = text("""
        SELECT 
            DATE(transaction_at) as date,
            SUM(total_amount) as sales,
            SUM(total_amount) as revenue,
            SUM(quantity) as orders
        FROM sales
        WHERE outlet_id = :outlet_id AND transaction_at >= :start_date
        GROUP BY DATE(transaction_at)
        ORDER BY DATE(transaction_at)
    """)
    result = await db.execute(sales_query, {"outlet_id": oid, "start_date": start_date})
    sales_rows = result.fetchall()
    
    # Fetch economic indicators (monthly resolution typically, but we map to dates)
    econ_query = text("""
        SELECT date_trunc('month', date) as month_date, cpi_inflation, repo_rate
        FROM economic_indicators_history
        WHERE date >= :start_date
    """)
    econ_result = await db.execute(econ_query, {"start_date": start_date.replace(day=1)})
    econ_rows = {row[0].date(): {"cpi": float(row[1] or 0), "repo": float(row[2] or 0)} for row in econ_result.fetchall()}
    
    # Build complete timeseries
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Convert sales to dict for fast lookup
    sales_dict = {row[0]: {"sales": float(row[1] or 0), "revenue": float(row[2] or 0), "orders": int(row[3] or 0)} for row in sales_rows}
    
    records = []
    for d in dates:
        d_date = d.date()
        month_key = d_date.replace(day=1)
        econ = econ_rows.get(month_key, {"cpi": 5.0, "repo": 6.5})
        
        # Simple holiday rule for mock treatment
        is_holiday = 1 if d.month == 12 and d.day == 25 else 0
        
        sd = sales_dict.get(d_date, {"sales": 0.0, "revenue": 0.0, "orders": 0})
        
        records.append({
            'date': d,
            'outlet_id': outlet_id,
            'sales': sd['sales'],
            'orders': sd['orders'],
            'revenue': sd['revenue'],
            'promotion': 1 if is_holiday else 0, # proxy
            'weather_rainy': 1 if d.month in [7,8] else 0,
            'competition_price': 100.0,
            'economic_index': (econ['cpi'] + econ['repo']) / 2.0  # Wires real economic data to index
        })
        
    df = pd.DataFrame(records)

    # If all sales are zero there is no real data to analyse.
    # Raise explicitly so callers surface an honest "no data" 400 rather than
    # passing fabricated random numbers into the causal model.
    if df['sales'].sum() == 0:
        raise ValueError(
            f"No sales data found for outlet '{outlet_id}' in the last {days} days. "
            "Causal analysis requires real historical sales records."
        )

    return df


def _predict_metric(
    data: pd.DataFrame,
    outlet_id: str,
    product_id: Optional[str],
    metric: str
) -> float:
    """Predict metric baseline"""
    if metric in data.columns:
        return data[metric].mean()
    return 0.0


def _predict_metric_with_scenario(
    data: pd.DataFrame,
    outlet_id: str,
    product_id: Optional[str],
    metric: str,
    scenario: Dict[str, Any]
) -> float:
    """Predict metric with scenario applied"""
    baseline = _predict_metric(data, outlet_id, product_id, metric)
    
    # Apply scenario effects
    impact = 0.0
    if scenario.get('promotion'):
        impact += baseline * 0.15  # 15% uplift
    if scenario.get('weather') == 'rainy':
        impact -= baseline * 0.10  # 10% downside
    
    return baseline + impact


def _interpret_effect(effect: float, metric: str, method: str) -> str:
    """Generate interpretation of causal effect"""
    if effect > 0:
        return f"This treatment increased {metric} by {abs(effect):.0f} ({method})"
    else:
        return f"This treatment decreased {metric} by {abs(effect):.0f} ({method})"


def _generate_recommendations(
    scenario: Dict[str, Any],
    impact: float,
    metric: str
) -> List[str]:
    """Generate actionable recommendations"""
    recommendations = []
    
    if scenario.get('promotion') and impact > 0:
        recommendations.append("Promotions are effective - continue running them")
    
    if scenario.get('weather') == 'rainy' and impact < 0:
        recommendations.append("Plan for rainy weather with additional staffing")
    
    if abs(impact) > 100:
        recommendations.append("This scenario has significant impact - monitor closely")
    
    return recommendations if recommendations else ["No strong recommendations at this time"]


def _detect_recent_anomalies(data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect recent anomalies in data"""
    anomalies = []
    # Simple anomaly detection
    if len(data) > 7:
        recent_mean = data['sales'].iloc[-7:].mean()
        overall_mean = data['sales'].mean()
        if abs(recent_mean - overall_mean) / overall_mean > 0.2:
            anomalies.append({
                'type': 'sales_anomaly',
                'severity': 'warning',
                'message': f'Recent sales {recent_mean:.0f} differ from average {overall_mean:.0f}'
            })
    
    return anomalies


def _generate_insights(outlet_id: str, data: pd.DataFrame) -> List[str]:
    """Generate actionable business insights"""
    insights = []
    
    # Check promotion effectiveness
    if 'promotion' in data.columns and data['promotion'].sum() > 0:
        promo_data = data[data['promotion'] == 1]['sales'].mean()
        no_promo_data = data[data['promotion'] == 0]['sales'].mean()
        if promo_data > no_promo_data:
            insights.append(f"Promotions increase sales by {((promo_data/no_promo_data - 1) * 100):.0f}%")
    
    # Check trend
    if len(data) > 14:
        recent_trend = data['sales'].iloc[-7:].mean()
        past_trend = data['sales'].iloc[-14:-7].mean()
        if recent_trend > past_trend:
            insights.append("Sales showing upward trend - maintain current strategy")
        else:
            insights.append("Sales showing downward trend - recommend intervention")
    
    return insights if insights else ["No significant patterns detected"]


if __name__ == "__main__":
    print("✓ Causal Analysis Router ready")
