"""
APScheduler Integration - Anomaly Detection Worker
Schedules hourly anomaly detection scans.

Configuration:
- Hourly: Anomaly detection scan
- Batch processing: WhatsApp notifications (every 5 minutes)
- Cleanup: Alert acknowledgment timeout
"""

import logging
from sqlalchemy import select
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.api.workers.anomaly_detector import run_hourly_anomaly_detection
from app.api.handlers.whatsapp_anomaly_handler import get_whatsapp_handler

logger = logging.getLogger(__name__)


# ============================================================================
# SCHEDULER SETUP
# ============================================================================

scheduler: BackgroundScheduler = None


def init_anomaly_detection_scheduler():
    """
    Initialize APScheduler with anomaly detection jobs.
    
    Called during FastAPI app startup.
    """
    global scheduler
    
    if scheduler is not None:
        return scheduler
    
    scheduler = BackgroundScheduler()
    
    # ========================================================================
    # JOB 1: HOURLY ANOMALY DETECTION
    # ========================================================================
    scheduler.add_job(
        func=_anomaly_detection_job,
        trigger=IntervalTrigger(hours=1),
        id='anomaly_detection_hourly',
        name='Hourly Anomaly Detection Scan',
        replace_existing=True,
        max_instances=1,  # Prevent concurrent runs
        coalesce=True,     # Skip missed runs
    )
    logger.info("✅ Added job: Hourly Anomaly Detection Scan")
    
    # ========================================================================
    # JOB 2: BATCH WHATSAPP NOTIFICATIONS
    # ========================================================================
    scheduler.add_job(
        func=_batch_notifications_job,
        trigger=IntervalTrigger(minutes=5),
        id='batch_whatsapp_notifications',
        name='Batch WhatsApp Notifications',
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✅ Added job: Batch WhatsApp Notifications (every 5 min)")
    
    # ========================================================================
    # JOB 3: CLEANUP OLD ALERTS
    # ========================================================================
    scheduler.add_job(
        func=_cleanup_old_alerts_job,
        trigger=CronTrigger(hour=2, minute=0),  # 2 AM daily
        id='cleanup_old_alerts',
        name='Cleanup Old Alerts',
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✅ Added job: Cleanup Old Alerts (daily at 2 AM)")
    
    # Start the scheduler
    scheduler.start()
    logger.info("🚀 Anomaly Detection Scheduler started")
    
    return scheduler


def shutdown_anomaly_detection_scheduler():
    """Shutdown the scheduler gracefully."""
    global scheduler
    
    if scheduler:
        scheduler.shutdown(wait=True)
        logger.info("🛑 Anomaly Detection Scheduler shut down")


# ============================================================================
# SCHEDULER JOB HANDLERS
# ============================================================================

def _anomaly_detection_job():
    """
    Background job: Run anomaly detection hourly.
    
    This is the main worker that:
    1. Scans sales for discount fraud
    2. Scans sales for drops
    3. Scans inventory for ghost items
    4. Publishes events to EventBus
    5. EventBus routes to WhatsApp handler
    """
    try:
        logger.info("🤖 Running hourly anomaly detection...")
        start_time = datetime.now()
        
        result = run_hourly_anomaly_detection()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if result['status'] == 'success':
            logger.info(f"✅ Anomaly detection complete ({elapsed:.1f}s)")
            logger.info(f"   Found: {result['anomalies_found']} anomalies")
            if result['anomalies_found'] > 0:
                logger.info(f"     - Discount fraud: {result['breakdown']['discount_fraud']}")
                logger.info(f"     - Sales drops: {result['breakdown']['sales_drops']}")
                logger.info(f"     - Ghost inventory: {result['breakdown']['ghost_inventory']}")
        else:
            logger.error(f"❌ Anomaly detection failed: {result['message']}")
    
    except Exception as e:
        logger.error(f"❌ Error in anomaly detection job: {e}", exc_info=True)


def _batch_notifications_job():
    """
    Background job: Send batched WhatsApp notifications every 5 minutes.
    
    Collects all pending notifications and sends them in batches
    to optimize API calls and reduce costs.
    """
    try:
        import asyncio
        
        handler = get_whatsapp_handler()
        
        # Check if there are pending messages
        if not handler.message_queue.empty():
            logger.info("📨 Processing WhatsApp notification batch...")
            
            # Run async batch send
            asyncio.run(handler.send_batch())
            
            logger.info("✅ Batch WhatsApp notifications sent")
    
    except Exception as e:
        logger.error(f"❌ Error in batch notifications job: {e}", exc_info=True)


def _cleanup_old_alerts_job():
    """
    Background job: Cleanup old unacknowledged alerts daily.
    
    Marks old (>7 days) unacknowledged alerts as archived
    to keep the system clean.
    """
    try:
        from datetime import timedelta
        from sqlalchemy import and_
        from app.api.db.database import SessionLocal
        from app.api.db.models import Alert
        
        logger.info("🧹 Cleaning up old alerts...")
        
        db = SessionLocal()
        try:
            # Find old unacknowledged alerts
            cutoff_date = datetime.now() - timedelta(days=7)
            
            old_alerts = db.query(Alert).filter(and_(
                    Alert.is_acknowledged == False,
                    Alert.created_at < cutoff_date
                )).all()
            
            count = len(old_alerts)
            
            if count > 0:
                for alert in old_alerts:
                    alert.is_acknowledged = True
                    alert.acknowledged_at = datetime.now()
                
                db.commit()
                logger.info(f"✅ Archived {count} old alerts")
            else:
                logger.info("✅ No old alerts to cleanup")
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"❌ Error in cleanup job: {e}", exc_info=True)


# ============================================================================
# MONITORING & STATUS
# ============================================================================

def get_scheduler_status():
    """
    Get current scheduler status and job information.
    
    Returns:
        Dict with scheduler state, running jobs, next scheduled times
    """
    if scheduler is None:
        return {"status": "not_initialized"}
    
    jobs_info = []
    for job in scheduler.get_jobs():
        jobs_info.append({
            'id': job.id,
            'name': job.name,
            'trigger': str(job.trigger),
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'executor': job.executor,
            'max_instances': job.max_instances,
        })
    
    return {
        'status': 'running' if scheduler.running else 'stopped',
        'jobs': jobs_info,
        'job_count': len(jobs_info),
    }


def pause_scheduler():
    """Pause the scheduler."""
    if scheduler:
        scheduler.pause()
        logger.info("⏸️ Scheduler paused")


def resume_scheduler():
    """Resume the scheduler."""
    if scheduler:
        scheduler.resume()
        logger.info("▶️ Scheduler resumed")


# ============================================================================
# INTEGRATION WITH FASTAPI
# ============================================================================

async def startup_event():
    """Called on FastAPI startup"""
    init_anomaly_detection_scheduler()


async def shutdown_event():
    """Called on FastAPI shutdown"""
    shutdown_anomaly_detection_scheduler()


# Example usage in main.py:
"""
from contextlib import asynccontextmanager
from app.api.services.anomaly_scheduler import startup_event, shutdown_event

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_event()
    yield
    # Shutdown
    await shutdown_event()

app = FastAPI(lifespan=lifespan)
"""


# ============================================================================
# API ENDPOINTS FOR MONITORING
# ============================================================================

def create_scheduler_routes(app):
    """
    Create FastAPI routes for scheduler monitoring.
    
    Endpoints:
    - GET /api/v1/admin/scheduler/status
    - POST /api/v1/admin/scheduler/pause
    - POST /api/v1/admin/scheduler/resume
    - GET /api/v1/admin/scheduler/jobs
    """
    
    @app.get("/api/v1/admin/scheduler/status", tags=["Admin"])
    async def scheduler_status():
        """Get scheduler status"""
        return get_scheduler_status()
    
    @app.post("/api/v1/admin/scheduler/pause", tags=["Admin"])
    async def pause():
        """Pause the scheduler"""
        pause_scheduler()
        return {"status": "paused"}
    
    @app.post("/api/v1/admin/scheduler/resume", tags=["Admin"])
    async def resume():
        """Resume the scheduler"""
        resume_scheduler()
        return {"status": "resumed"}
    
    @app.get("/api/v1/admin/scheduler/jobs", tags=["Admin"])
    async def list_jobs():
        """List scheduled jobs"""
        status = get_scheduler_status()
        return status.get('jobs', [])
    
    @app.post("/api/v1/admin/scheduler/jobs/{job_id}/trigger", tags=["Admin"])
    async def trigger_job(job_id: str):
        """Manually trigger a job"""
        try:
            if scheduler and scheduler.running:
                job = scheduler.get_job(job_id)
                if job:
                    job.func()
                    return {"status": "success", "job_id": job_id}
                else:
                    return {"status": "error", "message": f"Job {job_id} not found"}
            else:
                return {"status": "error", "message": "Scheduler not running"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize
    init_anomaly_detection_scheduler()
    
    # Print status
    status = get_scheduler_status()
    print("\n" + "=" * 80)
    print("SCHEDULER STATUS")
    print("=" * 80)
    print(f"Status: {status['status']}")
    print(f"Jobs: {status['job_count']}")
    for job in status['jobs']:
        print(f"  - {job['name']} (next: {job['next_run_time']})")
    
    print("\n(Press Ctrl+C to stop)")
    
    try:
        # Keep running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        shutdown_anomaly_detection_scheduler()
