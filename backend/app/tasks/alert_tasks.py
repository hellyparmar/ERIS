"""
Celery tasks for alert engine periodic execution.

Runs alert checks every 15 minutes for all active outlets.
"""

import logging
from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Outlet, AlertStatus as AlertStatusModel
from app.services.alert_engine_new import AlertEngine

logger = logging.getLogger(__name__)


@shared_task(name="run_alert_engine")
def run_alert_engine_task():
    """
    Periodic task to run alert engine for all active outlets.
    
    Scheduled to run every 15 minutes via Celery Beat.
    """
    db: Session = SessionLocal()
    
    try:
        # Get all active outlets
        outlets = db.query(Outlet).filter(Outlet.is_active == True).all()
        
        if not outlets:
            logger.warning("No active outlets found for alert engine")
            return {"status": "no_outlets"}
        
        engine = AlertEngine(db)
        results = {
            "total_outlets": len(outlets),
            "outlets_checked": 0,
            "total_alerts": 0,
            "failed_outlets": []
        }
        
        for outlet in outlets:
            try:
                outlet_results = engine.run_all_checks(outlet.outlet_id)
                results["outlets_checked"] += 1
                results["total_alerts"] += outlet_results.get("total_alerts", 0)
                
                logger.info(
                    f"Alert engine completed for outlet {outlet.name} ({outlet.outlet_id}): "
                    f"{outlet_results['total_alerts']} alerts"
                )
                
            except Exception as e:
                logger.error(f"Failed to run alert engine for outlet {outlet.outlet_id}: {str(e)}")
                results["failed_outlets"].append({
                    "outlet_id": str(outlet.outlet_id),
                    "outlet_name": outlet.name,
                    "error": str(e)
                })
        
        logger.info(f"Alert engine task completed: {results}")
        return results
    
    except Exception as e:
        logger.error(f"Critical error in alert engine task: {str(e)}")
        return {"status": "error", "error": str(e)}
    
    finally:
        db.close()


@shared_task(name="acknowledge_snoozed_alerts")
def acknowledge_snoozed_alerts_task():
    """
    Process snoozed alerts that have passed their snooze duration.
    
    Alerts snoozed for 4 hours are reactivated to remind users.
    """
    from app.models import AlertStatus
    
    db: Session = SessionLocal()
    
    try:
        snooze_duration = timedelta(hours=4)
        now = datetime.utcnow()
        
        # Find alerts that should be unsnoozed
        snoozed_alerts = db.query(AlertStatusModel).filter(
            AlertStatusModel.status == AlertStatus.snoozed
        ).all()
        
        reactivated_count = 0
        
        for alert in snoozed_alerts:
            if alert.updated_at and (now - alert.updated_at) > snooze_duration:
                alert.status = AlertStatus.active
                alert.updated_at = now
                reactivated_count += 1
        
        if reactivated_count > 0:
            db.commit()
            logger.info(f"Reactivated {reactivated_count} snoozed alerts")
        
        return {"reactivated_count": reactivated_count}
        
    except Exception as e:
        logger.error(f"Alert engine task failed: {str(e)}")
        raise
    finally:
        db.close()