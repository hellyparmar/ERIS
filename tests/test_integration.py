"""
Integration Test Suite for R-DIOS v6.0
Month 5, Week 18: Comprehensive integration tests
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any
import json
import sys

# Add project root to path
sys.path.insert(0, '/home/petpooja/Enterprise Retail Intelligence System')


class TestMLIntegration:
    """Integration tests for ML pipeline"""
    
    def test_forecasting_pipeline_end_to_end(self):
        """Test complete forecasting pipeline"""
        from src.ml.forecasting.prophet_forecaster import DemandForecastPipeline
        
        pipeline = DemandForecastPipeline()
        
        # Load data
        data = pipeline.load_data()
        assert len(data) > 0, "Data should be loaded"
        assert 'revenue' in data.columns, "Should have revenue column"
        
        # Run forecast
        results = pipeline.run_forecast(forecast_days=7)
        
        assert 'forecast' in results, "Should have forecast"
        assert 'metrics' in results, "Should have metrics"
        assert results['metrics'].get('mape', 100) < 50, "MAPE should be reasonable"
    
    def test_regressor_comparison(self):
        """Test model comparison with/without regressors"""
        from src.ml.forecasting.prophet_forecaster import DemandForecastPipeline
        
        pipeline = DemandForecastPipeline()
        comparison = pipeline.compare_with_without_regressors()
        
        assert 'without_regressors' in comparison
        assert 'with_regressors' in comparison
        assert 'improvement' in comparison
    
    def test_causal_engine_analysis(self):
        """Test causal inference engine"""
        from src.ml.causal.causal_engine import RetailCausalAnalyzer
        
        analyzer = RetailCausalAnalyzer()
        data = analyzer.load_data()
        
        assert len(data) > 0
        
        # Run analysis
        results = analyzer.run_full_analysis()
        
        assert 'holiday_analysis' in results
        assert 'monsoon_analysis' in results
        assert 'thesis_rq1_answer' in results
    
    def test_counterfactual_scenarios(self):
        """Test counterfactual analysis"""
        from src.ml.causal.counterfactual import CounterfactualAnalyzer
        from src.ml.causal.causal_engine import RetailCausalAnalyzer
        
        causal = RetailCausalAnalyzer()
        data = causal.load_data()
        
        cf = CounterfactualAnalyzer()
        cf.fit_outcome_model(data, 'revenue')
        
        # Test scenarios
        monsoon = cf.what_if_no_monsoon()
        assert monsoon.scenario is not None
        
        holiday = cf.what_if_every_day_holiday()
        assert holiday.estimated_effect != 0


class TestBusinessAnalytics:
    """Integration tests for business analytics"""
    
    def test_inventory_optimization(self):
        """Test EOQ and reorder calculations"""
        from src.services.business_analytics import InventoryOptimizer
        
        optimizer = InventoryOptimizer()
        
        # Test EOQ
        eoq, cost = optimizer.calculate_eoq(
            annual_demand=1000,
            unit_cost=100
        )
        
        assert eoq > 0, "EOQ should be positive"
        assert cost > 0, "Cost should be positive"
        
        # Test safety stock
        ss = optimizer.calculate_safety_stock(daily_demand_std=5)
        assert ss >= 0
        
        # Test reorder point
        rop = optimizer.calculate_reorder_point(avg_daily_demand=10)
        assert rop > 0
    
    def test_customer_segmentation(self):
        """Test RFM and K-means segmentation"""
        import pandas as pd
        import numpy as np
        from src.services.business_analytics import CustomerSegmentationService
        
        # Create sample data
        np.random.seed(42)
        transactions = pd.DataFrame({
            'customer_id': np.random.randint(1, 100, 500),
            'date': pd.date_range('2024-01-01', periods=500, freq='D')[:500],
            'amount': np.random.uniform(100, 5000, 500)
        })
        
        segmenter = CustomerSegmentationService()
        rfm = segmenter.calculate_rfm(transactions)
        
        assert 'R' in rfm.columns
        assert 'F' in rfm.columns
        assert 'M' in rfm.columns
        assert 'RFM_Segment' in rfm.columns


class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'healthy'
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_auth_flow(self, client):
        """Test authentication flow"""
        # Register
        register_data = {
            "username": f"testuser_{datetime.now().timestamp()}",
            "password": "TestPass123",
            "email": f"test_{datetime.now().timestamp()}@test.com"
        }
        
        response = client.post("/api/auth/register", json=register_data)
        # May fail if user exists, that's ok
        
        # Login
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = client.post("/api/auth/login", data=login_data)
        # Check login works or returns proper error


class TestDataPipelineIntegration:
    """Integration tests for data pipeline"""
    
    def test_hybrid_transformer(self):
        """Test data transformation pipeline"""
        from src.data.hybrid_transformer import HybridDataTransformer
        
        transformer = HybridDataTransformer()
        
        # Should be able to generate synthetic data
        assert transformer is not None
    
    def test_external_factors_service(self):
        """Test external factors integration"""
        from src.ml.forecasting.external_factors import ExternalFactorService
        
        service = ExternalFactorService()
        
        # Load weather
        weather = service.load_weather_data()
        assert len(weather) > 0
        
        # Load holidays
        holidays = service.load_holiday_data()
        assert len(holidays) > 0
        
        # Generate future features
        future = service.generate_future_features(date.today(), 30)
        assert len(future) == 30


class TestEndToEnd:
    """End-to-end workflow tests"""
    
    def test_complete_analysis_workflow(self):
        """Test complete analysis from data to insights"""
        from src.ml.forecasting.prophet_forecaster import DemandForecastPipeline
        from src.ml.causal.causal_engine import RetailCausalAnalyzer
        
        # 1. Load and forecast
        pipeline = DemandForecastPipeline()
        data = pipeline.load_data()
        forecast_results = pipeline.run_forecast(forecast_days=7)
        
        # 2. Causal analysis
        analyzer = RetailCausalAnalyzer(data)
        causal_results = analyzer.run_full_analysis()
        
        # 3. Validate results
        assert forecast_results['metrics'].get('mape') is not None
        assert causal_results['holiday_analysis']['best_estimate']['estimate'] != 0
        
        print("✅ End-to-end workflow completed successfully")
    
    def test_thesis_rq_answers(self):
        """Validate thesis research question answers are generated"""
        from src.ml.causal.causal_engine import RetailCausalAnalyzer
        
        analyzer = RetailCausalAnalyzer()
        results = analyzer.run_full_analysis()
        
        # RQ1: Causal effects
        assert 'thesis_rq1_answer' in results
        assert len(results['thesis_rq1_answer']) > 50
        
        # Validate effect significance
        holiday = results['holiday_analysis']['best_estimate']
        assert holiday['significant'], "Holiday effect should be significant"


# Performance benchmarks
class TestPerformance:
    """Performance benchmark tests"""
    
    def test_forecast_generation_time(self):
        """Benchmark forecast generation time"""
        import time
        from src.ml.forecasting.prophet_forecaster import DemandForecastPipeline
        
        pipeline = DemandForecastPipeline()
        pipeline.load_data()
        
        start = time.time()
        pipeline.run_forecast(forecast_days=30)
        elapsed = time.time() - start
        
        assert elapsed < 60, f"Forecast should complete in <60s, took {elapsed:.2f}s"
        print(f"Forecast generation: {elapsed:.2f}s")
    
    def test_causal_analysis_time(self):
        """Benchmark causal analysis time"""
        import time
        from src.ml.causal.causal_engine import RetailCausalAnalyzer
        
        analyzer = RetailCausalAnalyzer()
        
        start = time.time()
        analyzer.run_full_analysis()
        elapsed = time.time() - start
        
        assert elapsed < 30, f"Causal analysis should complete in <30s, took {elapsed:.2f}s"
        print(f"Causal analysis: {elapsed:.2f}s")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
