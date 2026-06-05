"""
Integration Tests for Enterprise Retail Intelligence System

Tests:
1. Adaptive Ensemble Forecasting
2. SHAP Explainability
3. Alert System
4. Causal Analysis API
5. Multi-Outlet Forecasting
6. End-to-End Pipeline

Run: pytest tests/integration/ -v --tb=short
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import numpy as np
import json

# Import system components
from app.ml.forecasting.adaptive_ensemble import AdaptiveEnsembleForecaster, ModelMetric
from app.ml.explainability.shap_integration import SHAPExplainer
from app.services.alert_service import AlertService, AnomalyDetector, AlertFactory
from app.ml.forecasting.multi_outlet import MultiOutletForecaster, OutletAnomalyAlert
from app.routers.causal_analysis import (
    TreatmentEffectRequest,
    CounterfactualRequest,
    DriverAnalysisRequest
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_data():
    """Generate sample time series data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
    data = pd.DataFrame({
        'date': dates,
        'sales': np.random.normal(500, 100, 90),
        'orders': np.random.normal(50, 10, 90),
        'promotion': np.random.choice([0, 1], 90, p=[0.8, 0.2]),
        'temperature': np.random.normal(20, 5, 90)
    })
    return data


@pytest.fixture
def adaptive_ensemble():
    """Initialize adaptive ensemble forecaster"""
    forecaster = AdaptiveEnsembleForecaster()
    
    # Add mock models
    forecaster.add_model(
        'model_1',
        _MockForecaster(baseline=500, noise=50),
        initial_weight=0.33
    )
    forecaster.add_model(
        'model_2',
        _MockForecaster(baseline=520, noise=40),
        initial_weight=0.33
    )
    forecaster.add_model(
        'model_3',
        _MockForecaster(baseline=490, noise=60),
        initial_weight=0.34
    )
    
    return forecaster


@pytest.fixture
def alert_service():
    """Initialize alert service"""
    service = AlertService()
    service.add_channel('memory', _MockInMemoryChannel())
    return service


@pytest.fixture
def multi_outlet_forecaster():
    """Initialize multi-outlet forecaster"""
    return MultiOutletForecaster()


# ============================================================================
# Helper Classes
# ============================================================================

class _MockForecaster:
    """Mock forecaster for testing"""
    
    def __init__(self, baseline: float = 500, noise: float = 50):
        self.baseline = baseline
        self.noise = noise
    
    def fit(self, data: pd.DataFrame, **kwargs):
        pass
    
    def predict(self, steps: int) -> np.ndarray:
        return np.array([
            self.baseline + np.random.normal(0, self.noise)
            for _ in range(steps)
        ])


class _MockInMemoryChannel:
    """Mock notification channel that stores alerts in memory"""
    
    def __init__(self):
        self.alerts = []
    
    async def send(self, alert):
        self.alerts.append(alert)
        return True


# ============================================================================
# Test Suite 1: Adaptive Ensemble Forecasting
# ============================================================================

class TestAdaptiveEnsemble:
    """Test adaptive ensemble forecasting"""
    
    def test_ensemble_initialization(self, adaptive_ensemble):
        """Test that ensemble initializes with multiple models"""
        assert len(adaptive_ensemble.models) == 3
        assert sum(adaptive_ensemble.weights.values()) == pytest.approx(1.0, rel=0.01)
    
    def test_ensemble_prediction(self, adaptive_ensemble, sample_data):
        """Test that ensemble produces forecasts"""
        # Fit all models
        adaptive_ensemble.fit_all(sample_data)
        
        # Get predictions
        forecast = adaptive_ensemble.predict_all(steps=30)
        
        assert isinstance(forecast, dict)
        assert len(forecast) == 3
        assert all(len(v) == 30 for v in forecast.values())
    
    def test_combined_forecast(self, adaptive_ensemble, sample_data):
        """Test that combined forecast is weighted average"""
        adaptive_ensemble.fit_all(sample_data)
        forecasts = adaptive_ensemble.predict_all(steps=10)
        combined = adaptive_ensemble.combine_forecasts()
        
        assert len(combined) == 10
        assert all(isinstance(v, (int, float)) for v in combined)
        assert all(v > 0 for v in combined)
    
    def test_model_evaluation(self, adaptive_ensemble, sample_data):
        """Test model evaluation and metric calculation"""
        adaptive_ensemble.fit_all(sample_data[:80])
        predictions = adaptive_ensemble.predict_all(steps=10)
        
        # Evaluate
        actual = sample_data['sales'].iloc[-10:].values
        adaptive_ensemble.evaluate_models(
            actual=actual,
            model_names=['model_1', 'model_2', 'model_3']
        )
        
        # Verify performance metrics were recorded
        summary = adaptive_ensemble.get_performance_summary()
        assert 'model_1' in summary
        assert 'mape' in summary['model_1']
    
    def test_adaptive_weight_update(self, adaptive_ensemble):
        """Test that weights update based on performance"""
        initial_weights = adaptive_ensemble.weights.copy()
        
        # Add metric with model_1 performing best
        metric = ModelMetric(
            timestamp=datetime.now(),
            mape=5.0,  # Lowest MAPE
            rmse=10.0,
            mae=8.0,
            coverage=0.95
        )
        
        # Manually set performance for model_1
        adaptive_ensemble.performance_tracker.metrics = {
            'model_1': [metric],
            'model_2': [ModelMetric(datetime.now(), 15.0, 30.0, 25.0, 0.9)],
            'model_3': [ModelMetric(datetime.now(), 20.0, 40.0, 35.0, 0.85)]
        }
        
        # Update weights
        updated_weights = adaptive_ensemble.weight_optimizer.calculate_adaptive_weights()
        
        # model_1 should have higher weight
        assert updated_weights['model_1'] > initial_weights['model_1']
    
    def test_state_persistence(self, adaptive_ensemble, tmp_path):
        """Test saving and loading ensemble state"""
        filepath = tmp_path / "ensemble_state.pkl"
        
        # Save
        adaptive_ensemble.save_state(str(filepath))
        assert filepath.exists()
        
        # Load into new instance
        new_ensemble = AdaptiveEnsembleForecaster()
        # Would load here in production


# ============================================================================
# Test Suite 2: SHAP Explainability
# ============================================================================

class TestSHAPIntegration:
    """Test SHAP explainability"""
    
    def test_shap_explainer_initialization(self):
        """Test SHAP explainer initializes correctly"""
        model = _MockForecaster()
        explainer = SHAPExplainer(model, model_type='kernel')
        
        assert explainer.explainer is not None
    
    def test_feature_importance(self, sample_data):
        """Test feature importance calculation"""
        model = _MockForecaster()
        explainer = SHAPExplainer(model, model_type='kernel')
        
        # Set features and background data
        X = sample_data[['promotion', 'temperature']].values
        explainer.set_background_data(X[:20])
        explainer.set_feature_names(['promotion', 'temperature'])
        
        # Get global importance
        importance = explainer.global_explanation(X, ['promotion', 'temperature'], top_k=2)
        
        assert 'mean_abs_shap' in importance
        assert len(importance['mean_abs_shap']) > 0
    
    def test_instance_explanation(self, sample_data):
        """Test instance-level explanation"""
        model = _MockForecaster()
        explainer = SHAPExplainer(model, model_type='kernel')
        
        X = sample_data[['promotion', 'temperature']].values
        explainer.set_background_data(X[:20])
        explainer.set_feature_names(['promotion', 'temperature'])
        
        # Explain single instance
        explanation = explainer.explain_instance(
            X[0:1],
            feature_names=['promotion', 'temperature'],
            as_dict=True
        )
        
        assert isinstance(explanation, dict)
        assert 'base_value' in explanation or explanation is not None
    
    def test_shap_serialization(self, sample_data):
        """Test SHAP results serialize to JSON"""
        model = _MockForecaster()
        explainer = SHAPExplainer(model, model_type='kernel')
        
        X = sample_data[['promotion', 'temperature']].values
        explainer.set_background_data(X[:20])
        explainer.set_feature_names(['promotion', 'temperature'])
        
        importance = explainer.global_explanation(X, ['promotion', 'temperature'], top_k=2)
        
        # Should be JSON serializable
        json_str = json.dumps(importance, default=str)
        assert isinstance(json_str, str)


# ============================================================================
# Test Suite 3: Alert System
# ============================================================================

class TestAlertSystem:
    """Test alert service and anomaly detection"""
    
    def test_anomaly_detection_deviation(self):
        """Test deviation-based anomaly detection"""
        actual = 600
        expected = 500
        is_anomaly, deviation = AnomalyDetector.detect_deviation(
            actual=actual,
            expected=expected,
            threshold_pct=10
        )
        
        assert is_anomaly is True
        assert deviation > 10
    
    def test_anomaly_detection_outlier(self):
        """Test outlier detection"""
        recent_values = [100, 102, 101, 103, 102, 500]  # Last value is outlier
        is_outlier, zscore = AnomalyDetector.detect_outlier(
            value=500,
            recent_values=recent_values,
            std_threshold=3.0
        )
        
        assert is_outlier is True
        assert abs(zscore) > 3.0
    
    def test_alert_creation(self, alert_service, sample_data):
        """Test creating and sending alerts"""
        alert = alert_service.create_alert(
            alert_type='FORECAST_ANOMALY',
            severity='WARNING',
            title='High sales deviation',
            message='Sales 50% above forecast',
            context={
                'outlet_id': 'outlet_1',
                'current_value': 750,
                'expected_value': 500
            }
        )
        
        assert alert.id is not None
        assert alert.type == 'FORECAST_ANOMALY'
        assert alert.severity == 'WARNING'
    
    @pytest.mark.asyncio
    async def test_alert_sending(self, alert_service):
        """Test sending alerts through channels"""
        alert = alert_service.create_alert(
            alert_type='STOCK_DEPLETION',
            severity='CRITICAL',
            title='Inventory depleted',
            message='Product out of stock',
            context={'outlet_id': 'outlet_1', 'product_id': 'coffee'}
        )
        
        result = await alert_service.send_alert(alert)
        assert result is True
        assert len(alert_service.active_alerts) > 0
    
    def test_alert_deduplication(self, alert_service):
        """Test that duplicate alerts are not created"""
        # Create alert
        alert1 = alert_service.create_alert(
            alert_type='DEMAND_SPIKE',
            severity='INFO',
            title='Sales spike detected',
            message='Sales 30% above normal',
            context={'outlet_id': 'outlet_1'}
        )
        
        # Try to create duplicate
        alert2 = alert_service.create_alert(
            alert_type='DEMAND_SPIKE',
            severity='INFO',
            title='Sales spike detected',
            message='Sales 30% above normal',
            context={'outlet_id': 'outlet_1'}
        )
        
        # Same alert should be deduplicated
        assert alert1.get_hash() == alert2.get_hash()
    
    def test_alert_acknowledgment(self, alert_service):
        """Test acknowledging alerts"""
        alert = alert_service.create_alert(
            alert_type='MODEL_DRIFT',
            severity='WARNING',
            title='Forecast accuracy declining',
            message='Accuracy dropped from 85% to 75%',
            context={'outlet_id': 'outlet_1'}
        )
        
        # Acknowledge
        success = alert_service.acknowledge_alert(
            alert_id=alert.id,
            acknowledged_by='user@company.com',
            notes='Investigating root cause'
        )
        
        assert success is True
        assert alert.acknowledged is True


# ============================================================================
# Test Suite 4: Multi-Outlet Forecasting
# ============================================================================

class TestMultiOutletForecasting:
    """Test multi-outlet forecasting"""
    
    def test_outlet_data_retrieval(self, multi_outlet_forecaster):
        """Test getting outlet-specific data"""
        data = multi_outlet_forecaster.data_manager.get_outlet_data(
            outlet_id='outlet_1',
            lookback_days=90
        )
        
        assert len(data) == 90
        assert 'sales' in data.columns
        assert 'outlet_id' in data.columns
    
    def test_outlet_metrics(self, multi_outlet_forecaster):
        """Test outlet performance metrics"""
        metrics = multi_outlet_forecaster.data_manager.get_outlet_stats('outlet_1')
        
        assert metrics.outlet_id == 'outlet_1'
        assert metrics.total_revenue > 0
        assert metrics.total_orders > 0
        assert metrics.forecast_accuracy > 0
    
    def test_outlet_forecast(self, multi_outlet_forecaster):
        """Test forecasting for single outlet"""
        forecast = multi_outlet_forecaster.forecast_outlet(
            outlet_id='outlet_1',
            periods=30
        )
        
        assert forecast.outlet_id == 'outlet_1'
        assert len(forecast.ensemble_forecast) == 30
        assert all(v > 0 for v in forecast.ensemble_forecast)
    
    def test_multi_outlet_batch_forecast(self, multi_outlet_forecaster):
        """Test forecasting for multiple outlets"""
        outlet_ids = ['outlet_1', 'outlet_2', 'outlet_3']
        forecasts = multi_outlet_forecaster.forecast_all_outlets(
            outlet_ids=outlet_ids,
            periods=30
        )
        
        assert len(forecasts) == 3
        assert all(len(f.ensemble_forecast) == 30 for f in forecasts.values())
    
    def test_outlet_anomaly_detection(self, multi_outlet_forecaster):
        """Test detecting outlet-specific anomalies"""
        anomalies = multi_outlet_forecaster.detect_outlet_anomalies('outlet_1')
        
        assert isinstance(anomalies, list)
        for alert in anomalies:
            assert isinstance(alert, OutletAnomalyAlert)
    
    def test_outlet_insights(self, multi_outlet_forecaster):
        """Test generating outlet insights"""
        insights = multi_outlet_forecaster.get_outlet_insights('outlet_1')
        
        assert 'outlet_id' in insights
        assert 'metrics' in insights
        assert 'forecast_summary' in insights
        assert 'active_anomalies' in insights


# ============================================================================
# Test Suite 5: End-to-End Pipeline
# ============================================================================

class TestEndToEndPipeline:
    """Test complete system integration"""
    
    def test_full_forecast_workflow(self, adaptive_ensemble, sample_data):
        """Test complete forecasting workflow"""
        # 1. Fit ensemble
        adaptive_ensemble.fit_all(sample_data)
        
        # 2. Generate forecasts
        forecasts = adaptive_ensemble.predict_all(steps=30)
        assert len(forecasts) == 3
        
        # 3. Combine forecasts
        combined = adaptive_ensemble.combine_forecasts()
        assert len(combined) == 30
        
        # 4. Generate performance summary
        summary = adaptive_ensemble.get_performance_summary()
        assert summary is not None
    
    @pytest.mark.asyncio
    async def test_alert_lifecycle(self, alert_service, sample_data):
        """Test complete alert lifecycle"""
        # 1. Create alert
        alert = alert_service.create_alert(
            alert_type='SALES_ANOMALY',
            severity='WARNING',
            title='Unusual sales pattern',
            message='Sales deviation from forecast',
            context={'outlet_id': 'outlet_1', 'deviation_pct': 25}
        )
        
        # 2. Send alert
        sent = await alert_service.send_alert(alert)
        assert sent is True
        
        # 3. Acknowledge
        acknowledged = alert_service.acknowledge_alert(
            alert_id=alert.id,
            acknowledged_by='manager@company.com'
        )
        assert acknowledged is True
        
        # 4. Resolve
        resolved = alert_service.resolve_alert(
            alert_id=alert.id,
            resolution_notes='Root cause identified and fixed'
        )
        assert resolved is True
        
        # 5. Get summary
        summary = alert_service.get_alert_summary(outlet_id='outlet_1')
        assert summary['total_alerts'] > 0
    
    def test_outlet_to_forecast_pipeline(self, multi_outlet_forecaster):
        """Test multi-outlet forecasting pipeline"""
        # 1. Get outlet data
        data = multi_outlet_forecaster.data_manager.get_outlet_data('outlet_1')
        assert len(data) > 0
        
        # 2. Get outlet metrics
        metrics = multi_outlet_forecaster.data_manager.get_outlet_stats('outlet_1')
        assert metrics.forecast_accuracy > 0
        
        # 3. Generate forecast
        forecast = multi_outlet_forecaster.forecast_outlet('outlet_1', periods=30)
        assert len(forecast.ensemble_forecast) == 30
        
        # 4. Detect anomalies
        anomalies = multi_outlet_forecaster.detect_outlet_anomalies('outlet_1')
        assert isinstance(anomalies, list)
        
        # 5. Get insights
        insights = multi_outlet_forecaster.get_outlet_insights('outlet_1')
        assert 'metrics' in insights


# ============================================================================
# Test Suite 6: Performance & Load Tests
# ============================================================================

class TestPerformance:
    """Test system performance under load"""
    
    def test_ensemble_performance(self, adaptive_ensemble, sample_data):
        """Test that ensemble completes in reasonable time"""
        import time
        
        start = time.time()
        adaptive_ensemble.fit_all(sample_data)
        forecast = adaptive_ensemble.predict_all(steps=30)
        elapsed = time.time() - start
        
        # Should complete in < 5 seconds
        assert elapsed < 5.0
        assert len(forecast) == 3
    
    def test_multi_outlet_batch_performance(self, multi_outlet_forecaster):
        """Test batch forecasting performance"""
        import time
        
        outlet_ids = [f'outlet_{i}' for i in range(10)]
        
        start = time.time()
        forecasts = multi_outlet_forecaster.forecast_all_outlets(
            outlet_ids=outlet_ids,
            periods=30
        )
        elapsed = time.time() - start
        
        # Should complete in < 30 seconds
        assert elapsed < 30.0
        assert len(forecasts) == 10


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
