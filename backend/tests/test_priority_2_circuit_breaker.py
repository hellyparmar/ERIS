"""
PRIORITY 2: Circuit Breaker Integration Tests
Validates resilience patterns are working correctly
"""

import pytest
import time
import logging
from unittest.mock import Mock, patch, MagicMock
from api.utils.resilient_services import (
    ResilientServiceCall,
    ServiceHealthStatus,
    tally_service,
    whatsapp_service,
    email_service_resilient,
    weather_service,
    ollama_service,
    payment_service
)

logger = logging.getLogger(__name__)


class TestResilientServiceCall:
    """Test the ResilientServiceCall implementation"""
    
    def test_service_initialization(self):
        """Test service is initialized correctly"""
        service = ResilientServiceCall("TestService")
        assert service.service_name == "TestService"
        assert service.failure_count == 0
        assert service.success_count == 0
        assert service.circuit_open == False
    
    def test_successful_call_execution(self):
        """Test successful function execution"""
        service = ResilientServiceCall("TestService")
        
        def successful_func():
            return {"status": "success"}
        
        result, is_fallback = service.execute_with_retry(successful_func)
        
        assert is_fallback == False
        assert result == {"status": "success"}
        assert service.total_successes == 1
        assert service.total_calls == 1
        assert service.failure_count == 0
    
    def test_retry_with_eventual_success(self):
        """Test that retries work when initial attempts fail"""
        service = ResilientServiceCall("TestService", max_retries=3)
        
        call_count = 0
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return {"status": "success"}
        
        result, is_fallback = service.execute_with_retry(flaky_func)
        
        assert is_fallback == False
        assert result == {"status": "success"}
        assert service.total_retries >= 1
        assert service.total_successes == 1
    
    def test_circuit_opens_after_threshold(self):
        """Test circuit opens after failure threshold reached"""
        service = ResilientServiceCall(
            "TestService",
            failure_threshold=3,
            max_retries=1
        )
        
        def always_fails():
            raise ConnectionError("Service down")
        
        # Attempt 3 times to trigger circuit open
        for i in range(3):
            result, is_fallback = service.execute_with_retry(
                always_fails,
                fallback_response={"status": "fallback"}
            )
        
        # Fourth call should use fallback immediately
        result, is_fallback = service.execute_with_retry(
            always_fails,
            fallback_response={"status": "fallback"}
        )
        
        assert is_fallback == True
        assert result == {"status": "fallback"}
        assert service.is_circuit_open() == True
    
    def test_circuit_recovery_timeout(self):
        """Test circuit enters HALF_OPEN after recovery timeout"""
        service = ResilientServiceCall(
            "TestService",
            failure_threshold=2,
            recovery_timeout_seconds=1,
            max_retries=1
        )
        
        def fails():
            raise ConnectionError("Failed")
        
        def succeeds():
            return {"status": "recovered"}
        
        # Trigger circuit open
        for i in range(2):
            service.execute_with_retry(fails, fallback_response={"status": "fallback"})
        
        assert service.is_circuit_open() == True
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Circuit should attempt recovery (HALF_OPEN)
        assert service.is_circuit_open() == False
        
        # Successful call should keep it closed
        result, is_fallback = service.execute_with_retry(succeeds)
        assert is_fallback == False
        assert result == {"status": "recovered"}
    
    def test_health_status_reporting(self):
        """Test health status is reported correctly"""
        service = ResilientServiceCall("TestService")
        
        def success():
            return {"ok": True}
        
        # Make some successful calls
        for i in range(5):
            service.execute_with_retry(success)
        
        status = service.get_health_status()
        
        assert status["service"] == "TestService"
        assert status["circuit_open"] == False
        assert status["metrics"]["total_calls"] == 5
        assert status["metrics"]["total_successes"] == 5
        assert status["metrics"]["success_rate_percent"] == 100.0
    
    def test_exponential_backoff_calculation(self):
        """Test exponential backoff increases correctly"""
        service = ResilientServiceCall(
            "TestService",
            initial_backoff_seconds=1.0,
            max_backoff_seconds=30.0
        )
        
        # Test backoff increases exponentially
        backoff_0 = service.calculate_backoff(0)  # ~1 second
        backoff_1 = service.calculate_backoff(1)  # ~2 seconds
        backoff_2 = service.calculate_backoff(2)  # ~4 seconds
        backoff_3 = service.calculate_backoff(3)  # ~8 seconds
        
        # Should be roughly doubling (with jitter)
        assert 0.5 < backoff_0 < 1.5
        assert 1.5 < backoff_1 < 3
        assert 3 < backoff_2 < 6
        assert 7 < backoff_3 < 10


class TestExternalServiceIntegration:
    """Test that all external services have circuit breaker protection"""
    
    def test_tally_service_exists(self):
        """Verify Tally service is configured"""
        assert tally_service.service_name == "Tally ERP"
        assert tally_service.failure_threshold == 3
        assert tally_service.recovery_timeout_seconds == 120
    
    def test_whatsapp_service_exists(self):
        """Verify WhatsApp service is configured"""
        assert whatsapp_service.service_name == "WhatsApp API"
        assert whatsapp_service.failure_threshold == 5
        assert whatsapp_service.recovery_timeout_seconds == 60
    
    def test_email_service_exists(self):
        """Verify Email service is configured"""
        assert email_service_resilient.service_name == "SMTP Email"
        assert email_service_resilient.failure_threshold == 5
    
    def test_weather_service_exists(self):
        """Verify Weather service is configured"""
        assert weather_service.service_name == "OpenWeather API"
        assert weather_service.failure_threshold == 3
        assert weather_service.recovery_timeout_seconds == 30
    
    def test_ollama_service_exists(self):
        """Verify Ollama AI service is configured"""
        assert ollama_service.service_name == "Ollama AI"
        assert ollama_service.failure_threshold == 3
    
    def test_payment_service_exists(self):
        """Verify Payment service is configured"""
        assert payment_service.service_name == "Payment Gateway"
        assert payment_service.failure_threshold == 2


class TestCircuitBreakerMetrics:
    """Test metrics collection and reporting"""
    
    def test_metrics_collection(self):
        """Test that metrics are collected accurately"""
        service = ResilientServiceCall("MetricsTest")
        
        def success():
            return {"ok": True}
        
        def failure():
            raise Exception("Test failure")
        
        # 3 successes
        for i in range(3):
            service.execute_with_retry(success)
        
        # 2 failures with retries (1 retry per failure)
        for i in range(2):
            service.execute_with_retry(failure, fallback_response={"status": "fallback"})
        
        assert service.total_calls == 5
        assert service.total_successes == 3
        assert service.total_failures == 2
        assert service.total_retries >= 2
    
    def test_success_rate_calculation(self):
        """Test success rate is calculated correctly"""
        service = ResilientServiceCall("RateTest")
        
        def success():
            return {"ok": True}
        
        # 8 successes, 2 failures
        for i in range(8):
            service.execute_with_retry(success)
        
        for i in range(2):
            service.execute_with_retry(
                lambda: (_ for _ in ()).throw(Exception("Fail")),
                fallback_response={"status": "fallback"}
            )
        
        status = service.get_health_status()
        success_rate = status["metrics"]["success_rate_percent"]
        
        # Should be around 80%
        assert 75 < success_rate < 85


class TestCircuitBreakerStateTransitions:
    """Test circuit breaker state machine transitions"""
    
    def test_closed_to_open_transition(self):
        """Test transition from CLOSED to OPEN"""
        service = ResilientServiceCall(
            "StateTest",
            failure_threshold=2,
            max_retries=1
        )
        
        def fails():
            raise ConnectionError("Failed")
        
        # Initially closed
        assert service.is_circuit_open() == False
        
        # After threshold failures, should open
        for i in range(2):
            service.execute_with_retry(fails, fallback_response={})
        
        assert service.is_circuit_open() == True
    
    def test_half_open_state_recovery(self):
        """Test recovery from HALF_OPEN state"""
        service = ResilientServiceCall(
            "HalfOpenTest",
            failure_threshold=1,
            recovery_timeout_seconds=1,
            max_retries=1
        )
        
        def fails():
            raise ConnectionError("Failed")
        
        def succeeds():
            return {"recovered": True}
        
        # Open circuit
        service.execute_with_retry(fails, fallback_response={})
        assert service.is_circuit_open() == True
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Circuit should attempt recovery
        assert service.is_circuit_open() == False
        
        # Successful call should keep it closed
        result, is_fallback = service.execute_with_retry(succeeds)
        assert not is_fallback
        assert service.failure_count == 0


def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("PRIORITY 2: CIRCUIT BREAKER INTEGRATION TESTS")
    print("="*80)
    
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_integration_tests()
