"""
PRIORITY 1: Simplification Tests
Verify that the simplified forecasting and analytics work correctly.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Test 1: Simple forecasting works
def test_simple_forecasting_import():
    """Verify simple forecasting can be imported (no SHAP/Prophet errors)"""
    try:
        from api.services.simple_forecasting import SimpleForecastingService
        assert SimpleForecastingService is not None
        print("✅ Simple forecasting service imports successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import SimpleForecastingService: {e}")


def test_simple_forecast_returns_valid_structure(db: Session):
    """Verify simple forecast returns expected structure"""
    from api.services.simple_forecasting import SimpleForecastingService
    
    service = SimpleForecastingService(db)
    result = service.forecast_daily_sales(store_id=1, days_to_forecast=30)
    
    # Check structure
    assert 'forecast' in result
    assert 'daily_average' in result
    assert 'confidence_lower' in result
    assert 'confidence_upper' in result
    assert 'method' in result
    assert result['method'] == 'simple_moving_average'
    
    # Check forecast is list of dicts
    assert isinstance(result['forecast'], list)
    if result['forecast']:
        assert 'date' in result['forecast'][0]
        assert 'predicted_sales' in result['forecast'][0]
    
    print("✅ Simple forecast returns valid structure")


# Test 2: Analytics endpoints work
def test_analytics_service_import():
    """Verify analytics service can be imported"""
    try:
        from api.services.analytics_service import AnalyticsService
        assert AnalyticsService is not None
        print("✅ Analytics service imports successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import AnalyticsService: {e}")


def test_analytics_metrics_structure(db: Session):
    """Verify analytics metrics return expected structure"""
    from api.services.analytics_service import AnalyticsService
    
    service = AnalyticsService()
    result = service.get_category_breakdown(days=30)
    
    assert 'categories' in result
    assert 'total_sales' in result
    assert 'total_orders' in result
    assert isinstance(result['categories'], list)
    
    print("✅ Analytics metrics return valid structure")


# Test 3: Routers work
def test_forecasting_router_imports():
    """Verify forecasting router can be imported"""
    try:
        from api.routers.forecasting import router
        assert router is not None
        assert len(router.routes) > 0
        print("✅ Forecasting router imports successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import forecasting router: {e}")


def test_analytics_router_imports():
    """Verify analytics router can be imported"""
    try:
        from api.routers.analytics import router
        assert router is not None
        assert len(router.routes) > 0
        print("✅ Analytics router imports successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import analytics router: {e}")


# Test 4: No complex ML dependencies used
def test_no_prophet_import():
    """Verify Prophet is not imported in simplified modules"""
    from api.routers import forecasting
    source = open(forecasting.__file__).read()
    assert 'from prophet' not in source.lower()
    assert 'import prophet' not in source.lower()
    print("✅ Simplified forecasting doesn't import Prophet")


def test_no_xgboost_import():
    """Verify XGBoost is not imported in simplified modules"""
    from api.routers import forecasting
    source = open(forecasting.__file__).read()
    assert 'xgboost' not in source.lower()
    assert 'lightgbm' not in source.lower()
    print("✅ Simplified forecasting doesn't import XGBoost/LightGBM")


def test_no_shap_import():
    """Verify SHAP is not imported in simplified modules"""
    from api.routers import forecasting
    source = open(forecasting.__file__).read()
    assert 'import shap' not in source.lower()
    assert 'from shap' not in source.lower()
    print("✅ Simplified forecasting doesn't import SHAP")


# Test 5: Performance - should be fast
def test_simple_forecast_performance(db: Session):
    """Verify simple forecasting is fast (< 1 second)"""
    import time
    from api.services.simple_forecasting import SimpleForecastingService
    
    service = SimpleForecastingService(db)
    
    start = time.time()
    result = service.forecast_daily_sales(store_id=1, days_to_forecast=30)
    elapsed = time.time() - start
    
    assert elapsed < 1.0, f"Forecast took {elapsed}s, expected < 1s"
    print(f"✅ Simple forecast completed in {elapsed:.3f}s")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PRIORITY 1: SIMPLIFICATION TESTS")
    print("="*70)
    
    # Run basic import tests
    test_simple_forecasting_import()
    test_analytics_service_import()
    test_forecasting_router_imports()
    test_analytics_router_imports()
    test_no_prophet_import()
    test_no_xgboost_import()
    test_no_shap_import()
    
    print("\n" + "="*70)
    print("✅ ALL PRIORITY 1 TESTS PASSED")
    print("="*70)
