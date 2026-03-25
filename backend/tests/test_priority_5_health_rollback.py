"""
PRIORITY 5 Tests: Health Checks & Rollback

Tests for:
- Health check aggregation
- Readiness and liveness probes
- Version management
- Rollback operations
- Auto-rollback on health failure
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from api.health.health_checks import (
    HealthStatus, ServiceHealth, HealthCheckCache, HealthCheckManager,
    check_api_health, check_database_health
)
from api.health.rollback import (
    RollbackStatus, DeploymentVersion, RollbackOperation,
    DeploymentVersionManager, RollbackManager, should_trigger_rollback
)


class TestHealthCheckCache:
    """Test health check caching functionality"""
    
    def test_cache_store_and_retrieve(self):
        """Test storing and retrieving cached health checks"""
        cache = HealthCheckCache(ttl_seconds=60)
        
        health = ServiceHealth("test", HealthStatus.HEALTHY, 5.0, "Test service")
        cache.set("test", health)
        
        cached = cache.get("test")
        assert cached is not None
        assert cached.name == "test"
        assert cached.status == HealthStatus.HEALTHY
    
    def test_cache_expiry(self):
        """Test cache expiry after TTL"""
        cache = HealthCheckCache(ttl_seconds=1)
        
        health = ServiceHealth("test", HealthStatus.HEALTHY, 5.0, "Test service")
        cache.set("test", health)
        
        # Immediately should be cached
        assert cache.get("test") is not None
        
        # Wait for expiry
        import time
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("test") is None
    
    def test_cache_clear(self):
        """Test clearing cache"""
        cache = HealthCheckCache()
        
        health = ServiceHealth("test1", HealthStatus.HEALTHY, 5.0)
        cache.set("test1", health)
        
        assert cache.get("test1") is not None
        
        cache.clear()
        assert cache.get("test1") is None


class TestHealthCheckManager:
    """Test health check manager"""
    
    @pytest.mark.asyncio
    async def test_register_and_check_single(self):
        """Test registering and running a single health check"""
        manager = HealthCheckManager()
        
        async def mock_check():
            return ServiceHealth("mock", HealthStatus.HEALTHY, 2.0, "Mock service")
        
        manager.register_check("mock", mock_check)
        
        result = await manager.check_single("mock")
        assert result.name == "mock"
        assert result.status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_check_all_aggregates(self):
        """Test aggregating all health checks"""
        manager = HealthCheckManager()
        
        async def check1():
            return ServiceHealth("service1", HealthStatus.HEALTHY, 1.0)
        
        async def check2():
            return ServiceHealth("service2", HealthStatus.HEALTHY, 2.0)
        
        manager.register_check("service1", check1)
        manager.register_check("service2", check2)
        
        result = await manager.check_all()
        
        assert result["status"] == "healthy"
        assert result["summary"]["total_checks"] == 2
        assert result["summary"]["healthy"] == 2
    
    @pytest.mark.asyncio
    async def test_check_degraded_status(self):
        """Test degraded status detection"""
        manager = HealthCheckManager()
        
        async def healthy():
            return ServiceHealth("healthy", HealthStatus.HEALTHY, 1.0)
        
        async def degraded():
            return ServiceHealth("degraded", HealthStatus.DEGRADED, 2.0)
        
        manager.register_check("healthy", healthy)
        manager.register_check("degraded", degraded)
        
        result = await manager.check_all()
        
        assert result["status"] == "degraded"
        assert result["summary"]["degraded"] == 1
    
    @pytest.mark.asyncio
    async def test_check_unhealthy_status(self):
        """Test unhealthy status detection"""
        manager = HealthCheckManager()
        
        async def unhealthy():
            return ServiceHealth("bad", HealthStatus.UNHEALTHY, 1.0)
        
        manager.register_check("bad", unhealthy)
        
        result = await manager.check_all()
        
        assert result["status"] == "unhealthy"
        assert result["summary"]["unhealthy"] == 1
    
    @pytest.mark.asyncio
    async def test_readiness_probe(self):
        """Test readiness probe"""
        manager = HealthCheckManager()
        
        async def database():
            return ServiceHealth("database", HealthStatus.HEALTHY, 5.0)
        
        async def api():
            return ServiceHealth("api", HealthStatus.HEALTHY, 1.0)
        
        async def auth():
            return ServiceHealth("auth", HealthStatus.HEALTHY, 2.0)
        
        manager.register_check("database", database)
        manager.register_check("api", api)
        manager.register_check("auth", auth)
        
        result = await manager.readiness_probe()
        
        assert result["ready"] == True
    
    @pytest.mark.asyncio
    async def test_liveness_probe(self):
        """Test liveness probe"""
        manager = HealthCheckManager()
        
        async def api():
            return ServiceHealth("api", HealthStatus.HEALTHY, 1.0)
        
        manager.register_check("api", api)
        
        result = await manager.liveness_probe()
        
        assert result["alive"] == True
    
    @pytest.mark.asyncio
    async def test_health_history(self):
        """Test health check history"""
        manager = HealthCheckManager()
        
        async def service():
            return ServiceHealth("test", HealthStatus.HEALTHY, 1.0)
        
        manager.register_check("test", service)
        
        # Run multiple checks
        for _ in range(3):
            await manager.check_all()
        
        history = manager.get_history(limit=5)
        assert len(history) == 3
    
    @pytest.mark.asyncio
    async def test_health_statistics(self):
        """Test health statistics"""
        manager = HealthCheckManager()
        
        async def service():
            return ServiceHealth("test", HealthStatus.HEALTHY, 2.5)
        
        manager.register_check("test", service)
        
        # Run multiple checks
        for _ in range(3):
            await manager.check_all()
        
        stats = manager.get_stats()
        
        assert stats["total_checks"] == 3
        assert stats["avg_response_time_ms"] > 0
        assert stats["uptime_percentage"] == 100.0


class TestDeploymentVersionManager:
    """Test deployment version management"""
    
    def test_record_deployment(self, tmp_path):
        """Test recording a new deployment"""
        manager = DeploymentVersionManager(str(tmp_path))
        
        version = manager.record_deployment(
            "v1.0.0",
            {"feature": "initial"},
            "abc123"
        )
        
        assert version.version_id == "v1.0.0"
        assert version.is_active == True
        assert manager.current_version == "v1.0.0"
    
    def test_get_current_version(self, tmp_path):
        """Test retrieving current version"""
        manager = DeploymentVersionManager(str(tmp_path))
        
        manager.record_deployment("v1.0.0")
        manager.record_deployment("v1.0.1")
        
        current = manager.get_current_version()
        assert current.version_id == "v1.0.1"
    
    def test_get_previous_version(self, tmp_path):
        """Test retrieving previous version"""
        manager = DeploymentVersionManager(str(tmp_path))
        
        manager.record_deployment("v1.0.0")
        manager.record_deployment("v1.0.1")
        
        previous = manager.get_previous_version()
        assert previous.version_id == "v1.0.0"
    
    def test_version_history(self, tmp_path):
        """Test version history retrieval"""
        manager = DeploymentVersionManager(str(tmp_path))
        
        manager.record_deployment("v1.0.0")
        manager.record_deployment("v1.0.1")
        manager.record_deployment("v1.0.2")
        
        history = manager.get_version_history(limit=2)
        
        assert len(history) == 2
        assert history[0].version_id == "v1.0.2"
    
    def test_rollback_availability(self, tmp_path):
        """Test checking if rollback is available"""
        manager = DeploymentVersionManager(str(tmp_path))
        
        assert manager.is_rollback_available() == False
        
        manager.record_deployment("v1.0.0")
        assert manager.is_rollback_available() == False
        
        manager.record_deployment("v1.0.1")
        assert manager.is_rollback_available() == True


class TestRollbackOperation:
    """Test rollback operations"""
    
    def test_create_rollback_operation(self):
        """Test creating a rollback operation"""
        op = RollbackOperation("v1.0.1", "v1.0.0", "Critical bug fix")
        
        assert op.from_version == "v1.0.1"
        assert op.to_version == "v1.0.0"
        assert op.reason == "Critical bug fix"
        assert op.status == RollbackStatus.PENDING
    
    def test_rollback_duration(self):
        """Test calculating rollback duration"""
        import time
        op = RollbackOperation("v1.0.1", "v1.0.0")
        
        op.start_time = time.time()
        time.sleep(0.1)
        op.end_time = time.time()
        
        assert op.duration_seconds is not None
        assert op.duration_seconds >= 0.1


class TestRollbackManager:
    """Test rollback management"""
    
    @pytest.mark.asyncio
    async def test_prepare_rollback(self, tmp_path):
        """Test preparing rollback"""
        version_manager = DeploymentVersionManager(str(tmp_path))
        rollback_manager = RollbackManager(version_manager)
        
        version_manager.record_deployment("v1.0.0")
        version_manager.record_deployment("v1.0.1")
        
        success, message = await rollback_manager.prepare_rollback()
        
        assert success == True
        assert "v1.0.0" in message
    
    @pytest.mark.asyncio
    async def test_execute_rollback(self, tmp_path):
        """Test executing rollback"""
        version_manager = DeploymentVersionManager(str(tmp_path))
        rollback_manager = RollbackManager(version_manager)
        
        # Register a simple rollback callback
        async def mock_rollback(from_v, to_v):
            return True
        
        rollback_manager.register_rollback_callback("mock", mock_rollback)
        
        version_manager.record_deployment("v1.0.0")
        version_manager.record_deployment("v1.0.1")
        
        success, message = await rollback_manager.execute_rollback()
        
        assert success == True
        assert version_manager.current_version == "v1.0.0"
    
    @pytest.mark.asyncio
    async def test_rollback_history(self, tmp_path):
        """Test rollback history"""
        version_manager = DeploymentVersionManager(str(tmp_path))
        rollback_manager = RollbackManager(version_manager)
        
        async def mock_rollback(from_v, to_v):
            return True
        
        rollback_manager.register_rollback_callback("mock", mock_rollback)
        
        version_manager.record_deployment("v1.0.0")
        version_manager.record_deployment("v1.0.1")
        
        await rollback_manager.execute_rollback()
        
        history = rollback_manager.get_rollback_history()
        
        assert len(history) == 1
        assert history[0]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_auto_rollback_trigger(self, tmp_path):
        """Test automatic rollback trigger on health failure"""
        version_manager = DeploymentVersionManager(str(tmp_path))
        rollback_manager = RollbackManager(version_manager)
        
        async def mock_rollback(from_v, to_v):
            return True
        
        rollback_manager.register_rollback_callback("mock", mock_rollback)
        
        version_manager.record_deployment("v1.0.0")
        version_manager.record_deployment("v1.0.1")
        
        # Simulate health failure
        health_result = {
            "status": "unhealthy",
            "summary": {
                "total_checks": 5,
                "healthy": 1,
                "degraded": 1,
                "unhealthy": 3
            }
        }
        
        success, message = await rollback_manager.auto_rollback_on_health_failure(
            health_result,
            health_threshold=0.5
        )
        
        assert success == True
        assert "Auto-rollback" in message


class TestHealthCheckIntegration:
    """Integration tests for health checks and rollback"""
    
    @pytest.mark.asyncio
    async def test_full_health_monitoring_workflow(self):
        """Test complete health monitoring workflow"""
        manager = HealthCheckManager()
        
        async def service1():
            return ServiceHealth("service1", HealthStatus.HEALTHY, 1.0)
        
        async def service2():
            return ServiceHealth("service2", HealthStatus.HEALTHY, 2.0)
        
        manager.register_check("service1", service1)
        manager.register_check("service2", service2)
        
        # Run health checks
        health = await manager.check_all()
        
        assert health["status"] == "healthy"
        assert health["summary"]["total_checks"] == 2
        
        # Check readiness
        readiness = await manager.readiness_probe()
        assert readiness["ready"] == True
        
        # Check liveness
        liveness = await manager.liveness_probe()
        assert liveness["alive"] == True
    
    @pytest.mark.asyncio
    async def test_full_rollback_workflow(self, tmp_path):
        """Test complete rollback workflow"""
        version_manager = DeploymentVersionManager(str(tmp_path))
        rollback_manager = RollbackManager(version_manager)
        
        rollback_performed = []
        
        async def tracking_rollback(from_v, to_v):
            rollback_performed.append((from_v, to_v))
            return True
        
        rollback_manager.register_rollback_callback("test", tracking_rollback)
        
        # Record deployments
        v1 = version_manager.record_deployment("v1.0.0")
        v2 = version_manager.record_deployment("v1.0.1")
        
        assert v2.is_active == True
        assert v1.is_active == False
        
        # Execute rollback
        success, _ = await rollback_manager.execute_rollback()
        
        assert success == True
        assert len(rollback_performed) == 1
        assert rollback_performed[0] == ("v1.0.1", "v1.0.0")
        
        # Verify state
        current = version_manager.get_current_version()
        assert current.version_id == "v1.0.0"
        assert current.is_active == True


class TestHealthCheckPerformance:
    """Test health check performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        """Test concurrent health check execution"""
        manager = HealthCheckManager()
        
        async def fast_check():
            return ServiceHealth("fast", HealthStatus.HEALTHY, 1.0)
        
        async def slow_check():
            await asyncio.sleep(0.05)
            return ServiceHealth("slow", HealthStatus.HEALTHY, 50.0)
        
        manager.register_check("fast", fast_check)
        manager.register_check("slow", slow_check)
        
        # Run concurrently
        import time
        start = time.time()
        result = await manager.check_all()
        duration = (time.time() - start) * 1000
        
        # Should complete in ~50ms (duration of slowest check)
        # Not ~51ms (sequential)
        assert duration < 100  # Allow some overhead
    
    @pytest.mark.asyncio
    async def test_cache_improves_performance(self):
        """Test that caching improves performance"""
        manager = HealthCheckManager()
        
        call_count = [0]
        
        async def slow_check():
            call_count[0] += 1
            await asyncio.sleep(0.02)
            return ServiceHealth("slow", HealthStatus.HEALTHY, 20.0)
        
        manager.register_check("slow", slow_check)
        
        # First check (uncached)
        await manager.check_single("slow", use_cache=False)
        assert call_count[0] == 1
        
        # Second check (cached)
        await manager.check_single("slow", use_cache=True)
        assert call_count[0] == 1  # Not called again
        
        # Cache still valid
        await manager.check_single("slow", use_cache=True)
        assert call_count[0] == 1


class TestSecurityObjectivesP5:
    """Test that PRIORITY 5 objectives are met"""
    
    @pytest.mark.asyncio
    async def test_health_check_aggregation_implemented(self):
        """Verify health check aggregation is implemented"""
        manager = HealthCheckManager()
        
        async def check1():
            return ServiceHealth("api", HealthStatus.HEALTHY, 1.0)
        
        manager.register_check("api", check1)
        
        result = await manager.check_all()
        
        assert "status" in result
        assert "summary" in result
        assert "checks" in result
        assert result["summary"]["total_checks"] >= 1
    
    @pytest.mark.asyncio
    async def test_readiness_liveness_probes_implemented(self):
        """Verify readiness and liveness probes are implemented"""
        manager = HealthCheckManager()
        
        async def service():
            return ServiceHealth("api", HealthStatus.HEALTHY, 1.0)
        
        manager.register_check("api", service)
        
        readiness = await manager.readiness_probe()
        assert "ready" in readiness
        
        liveness = await manager.liveness_probe()
        assert "alive" in liveness
    
    @pytest.mark.asyncio
    async def test_rollback_mechanism_implemented(self, tmp_path):
        """Verify rollback mechanism is implemented"""
        version_manager = DeploymentVersionManager(str(tmp_path))
        rollback_manager = RollbackManager(version_manager)
        
        async def callback(from_v, to_v):
            return True
        
        rollback_manager.register_rollback_callback("test", callback)
        
        version_manager.record_deployment("v1.0.0")
        version_manager.record_deployment("v1.0.1")
        
        success, _ = await rollback_manager.execute_rollback()
        
        assert success == True
        assert version_manager.current_version == "v1.0.0"
    
    @pytest.mark.asyncio
    async def test_health_status_reporting_implemented(self):
        """Verify health status reporting is implemented"""
        manager = HealthCheckManager()
        
        async def service():
            return ServiceHealth("api", HealthStatus.HEALTHY, 1.0)
        
        manager.register_check("api", service)
        
        # Run checks
        for _ in range(3):
            await manager.check_all()
        
        # Get history
        history = manager.get_history(limit=5)
        assert len(history) > 0
        
        # Get stats
        stats = manager.get_stats()
        assert "uptime_percentage" in stats
        assert "avg_response_time_ms" in stats
