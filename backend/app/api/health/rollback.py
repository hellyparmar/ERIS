"""
Deployment Rollback System for Enterprise Retail Intelligence System

Provides safe deployment rollback capabilities:
- Version tracking and storage
- Rollback execution
- Rollback verification
- Rollback history
- Automatic rollback on health check failure
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from pathlib import Path
import logging
import asyncio

logger = logging.getLogger(__name__)


class RollbackStatus(str, Enum):
    """Rollback status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DeploymentVersion:
    """Represents a deployed version"""
    
    def __init__(self, version_id: str, timestamp: datetime, 
                 metadata: Dict[str, Any] = None, checksum: str = ""):
        self.version_id = version_id
        self.timestamp = timestamp
        self.metadata = metadata or {}
        self.checksum = checksum
        self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "version_id": self.version_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "checksum": self.checksum,
            "is_active": self.is_active
        }


class RollbackOperation:
    """Represents a rollback operation"""
    
    def __init__(self, from_version: str, to_version: str, reason: str = ""):
        self.from_version = from_version
        self.to_version = to_version
        self.reason = reason
        self.status = RollbackStatus.PENDING
        self.timestamp = datetime.utcnow()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.error_message = ""
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get rollback duration"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "reason": self.reason,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message
        }


class DeploymentVersionManager:
    """Manages deployment versions and history"""
    
    def __init__(self, storage_dir: str = "./deployment_versions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.versions: Dict[str, DeploymentVersion] = {}
        self.current_version: Optional[str] = None
        self.version_file = self.storage_dir / "versions.json"
        
        self._load_versions()
    
    def _load_versions(self):
        """Load version history from storage"""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    
                    for v_data in data.get("versions", []):
                        v = DeploymentVersion(
                            v_data["version_id"],
                            datetime.fromisoformat(v_data["timestamp"]),
                            v_data.get("metadata", {}),
                            v_data.get("checksum", "")
                        )
                        v.is_active = v_data.get("is_active", False)
                        self.versions[v.version_id] = v
                    
                    self.current_version = data.get("current_version")
        except Exception as e:
            logger.error(f"Error loading versions: {str(e)}")
    
    def _save_versions(self):
        """Save version history to storage"""
        try:
            data = {
                "versions": [v.to_dict() for v in self.versions.values()],
                "current_version": self.current_version,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            with open(self.version_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving versions: {str(e)}")
    
    def record_deployment(self, version_id: str, metadata: Dict[str, Any] = None,
                         checksum: str = "") -> DeploymentVersion:
        """Record a new deployment"""
        version = DeploymentVersion(
            version_id,
            datetime.utcnow(),
            metadata or {},
            checksum
        )
        
        # Mark previous active version as inactive
        if self.current_version and self.current_version in self.versions:
            self.versions[self.current_version].is_active = False
        
        # Mark new version as active
        version.is_active = True
        self.versions[version_id] = version
        self.current_version = version_id
        
        self._save_versions()
        logger.info(f"Recorded deployment version: {version_id}")
        return version
    
    def get_version(self, version_id: str) -> Optional[DeploymentVersion]:
        """Get specific version"""
        return self.versions.get(version_id)
    
    def get_current_version(self) -> Optional[DeploymentVersion]:
        """Get current active version"""
        if self.current_version:
            return self.versions.get(self.current_version)
        return None
    
    def get_previous_version(self) -> Optional[DeploymentVersion]:
        """Get previous version (for rollback)"""
        if not self.current_version:
            return None
        
        # Find version created before current
        versions_by_time = sorted(
            self.versions.values(),
            key=lambda v: v.timestamp,
            reverse=True
        )
        
        for v in versions_by_time:
            if v.version_id != self.current_version:
                return v
        
        return None
    
    def get_version_history(self, limit: int = 10) -> List[DeploymentVersion]:
        """Get version history"""
        versions_by_time = sorted(
            self.versions.values(),
            key=lambda v: v.timestamp,
            reverse=True
        )
        return versions_by_time[:limit]
    
    def is_rollback_available(self) -> bool:
        """Check if rollback to previous version is available"""
        return self.get_previous_version() is not None


class RollbackManager:
    """Manages rollback operations"""
    
    def __init__(self, version_manager: DeploymentVersionManager):
        self.version_manager = version_manager
        self.rollback_history: List[RollbackOperation] = []
        self.max_history = 50
        self.rollback_callbacks: Dict[str, callable] = {}
    
    def register_rollback_callback(self, component: str, callback: callable):
        """Register a component-specific rollback callback
        
        Callback receives (from_version, to_version) and should return True if successful
        """
        self.rollback_callbacks[component] = callback
    
    async def prepare_rollback(self, target_version: Optional[str] = None,
                               reason: str = "") -> Tuple[bool, str]:
        """Prepare rollback to specified or previous version"""
        
        current = self.version_manager.get_current_version()
        if not current:
            return False, "No current version recorded"
        
        # Determine target version
        if target_version is None:
            target = self.version_manager.get_previous_version()
            if not target:
                return False, "No previous version available for rollback"
        else:
            target = self.version_manager.get_version(target_version)
            if not target:
                return False, f"Version {target_version} not found"
        
        # Create rollback operation
        rollback_op = RollbackOperation(
            current.version_id,
            target.version_id,
            reason
        )
        rollback_op.status = RollbackStatus.IN_PROGRESS
        rollback_op.start_time = time.time()
        
        return True, f"Rollback prepared to version {target.version_id}"
    
    async def execute_rollback(self, target_version: Optional[str] = None,
                               reason: str = "") -> Tuple[bool, str]:
        """Execute rollback to specified or previous version"""
        
        current = self.version_manager.get_current_version()
        if not current:
            return False, "No current version recorded"
        
        # Determine target version
        if target_version is None:
            target = self.version_manager.get_previous_version()
            if not target:
                return False, "No previous version available for rollback"
        else:
            target = self.version_manager.get_version(target_version)
            if not target:
                return False, f"Version {target_version} not found"
        
        # Create rollback operation
        rollback_op = RollbackOperation(
            current.version_id,
            target.version_id,
            reason
        )
        rollback_op.status = RollbackStatus.IN_PROGRESS
        rollback_op.start_time = time.time()
        
        try:
            # Execute component-specific rollbacks
            for component, callback in self.rollback_callbacks.items():
                try:
                    success = await callback(current.version_id, target.version_id) \
                        if asyncio.iscoroutinefunction(callback) \
                        else callback(current.version_id, target.version_id)
                    
                    if not success:
                        raise Exception(f"Rollback failed for {component}")
                    
                    logger.info(f"Rolled back component {component} to {target.version_id}")
                except Exception as e:
                    logger.error(f"Error rolling back {component}: {str(e)}")
                    rollback_op.status = RollbackStatus.FAILED
                    rollback_op.error_message = f"Failed to rollback {component}: {str(e)}"
                    rollback_op.end_time = time.time()
                    self.rollback_history.append(rollback_op)
                    return False, rollback_op.error_message
            
            # Update version manager
            target.is_active = True
            current.is_active = False
            self.version_manager.current_version = target.version_id
            self.version_manager._save_versions()
            
            rollback_op.status = RollbackStatus.COMPLETED
            rollback_op.end_time = time.time()
            self.rollback_history.append(rollback_op)
            
            if len(self.rollback_history) > self.max_history:
                self.rollback_history.pop(0)
            
            message = f"Successfully rolled back to version {target.version_id}"
            logger.info(message)
            return True, message
            
        except Exception as e:
            rollback_op.status = RollbackStatus.FAILED
            rollback_op.error_message = str(e)
            rollback_op.end_time = time.time()
            self.rollback_history.append(rollback_op)
            
            logger.error(f"Rollback failed: {str(e)}")
            return False, f"Rollback failed: {str(e)}"
    
    async def auto_rollback_on_health_failure(self, health_check_result: Dict[str, Any],
                                              health_threshold: float = 0.5) -> Tuple[bool, str]:
        """Automatically rollback if health checks fail
        
        Rolls back if unhealthy ratio > health_threshold
        """
        try:
            summary = health_check_result.get("summary", {})
            total = summary.get("total_checks", 0)
            unhealthy = summary.get("unhealthy", 0)
            
            if total == 0:
                return False, "No health check data"
            
            unhealthy_ratio = unhealthy / total
            
            if unhealthy_ratio > health_threshold:
                reason = f"Auto-rollback: {unhealthy}/{total} checks unhealthy"
                success, message = await self.execute_rollback(reason=reason)
                return success, f"Auto-rollback triggered: {message}"
            
            return False, "Health checks within threshold"
            
        except Exception as e:
            logger.error(f"Error in auto-rollback check: {str(e)}")
            return False, str(e)
    
    def verify_rollback(self, rollback_op: RollbackOperation) -> bool:
        """Verify rollback was successful"""
        return rollback_op.status == RollbackStatus.COMPLETED
    
    def get_rollback_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get rollback history"""
        return [op.to_dict() for op in self.rollback_history[-limit:]]
    
    def get_last_rollback(self) -> Optional[RollbackOperation]:
        """Get last rollback operation"""
        if self.rollback_history:
            return self.rollback_history[-1]
        return None


# Helper function to check if rollback is needed
async def should_trigger_rollback(health_manager, rollback_manager,
                                  min_healthy_percentage: float = 70.0) -> Tuple[bool, str]:
    """Determine if automatic rollback should be triggered"""
    
    try:
        # Get current health status
        health_check = await health_manager.check_all(use_cache=False)
        
        summary = health_check.get("summary", {})
        total = summary.get("total_checks", 0)
        healthy = summary.get("healthy", 0)
        
        if total == 0:
            return False, "No health checks available"
        
        healthy_percentage = (healthy / total) * 100
        
        if healthy_percentage < min_healthy_percentage:
            return True, f"Health below threshold: {healthy_percentage:.1f}% < {min_healthy_percentage}%"
        
        return False, f"System health acceptable: {healthy_percentage:.1f}%"
        
    except Exception as e:
        logger.error(f"Error checking rollback trigger: {str(e)}")
        return False, str(e)
