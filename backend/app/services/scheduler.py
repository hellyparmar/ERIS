"""
Background scheduler for operational reports and alerts.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text
import logging
from app.database import SessionLocal

logger = logging.getLogger(__name__)


def check_low_stock_job():
    """
    Checks for products with low stock and anomalous demand, and creates real alerts.
    """
    logger.info("📉 Checking for Low Stock items and sales anomalies...")
    db = SessionLocal()
    try:
        from app.models import Outlet
        from app.models.alert import Alert, AlertType, AlertSeverity
        from app.services.anomaly_detection import detect_product_anomalies

        # 1. Check for stock below reorder level
        low_stock_query = text("""
            SELECT p.id as product_id, p.name as product_name, i.current_stock as stock, p.reorder_level, i.outlet_id
            FROM products p
            JOIN inventory i ON p.id = i.product_id
            WHERE i.current_stock <= p.reorder_level
        """)
        low_stock_items = db.execute(low_stock_query).fetchall()

        if low_stock_items:
            logger.warning(f"⚠️ Found {len(low_stock_items)} low stock items!")
            for item in low_stock_items:
                # Check if an active alert already exists for this product at this outlet
                existing_alert = (
                    db.query(Alert)
                    .filter(
                        Alert.product_id == item.product_id,
                        Alert.outlet_id == item.outlet_id,
                        Alert.alert_type == AlertType.low_stock,
                        Alert.is_acknowledged.is_(False),
                    )
                    .first()
                )

                if not existing_alert:
                    severity = AlertSeverity.critical if item.stock <= 0 else AlertSeverity.high
                    new_alert = Alert(
                        outlet_id=item.outlet_id,
                        product_id=item.product_id,
                        alert_type=AlertType.low_stock,
                        severity=severity,
                        message=f"Low Stock for {item.product_name}: {item.stock} left (reorder level: {item.reorder_level})",
                    )
                    db.add(new_alert)
                    logger.info(f"🔔 Created real Low Stock Alert for {item.product_name} at Outlet {item.outlet_id}")

        # 2. Check for product anomalies (Spikes/Drops)
        # We will check across all active outlets. For simplicity, we loop through unique outlets in DB.
        outlets = db.query(Outlet).all()
        for outlet in outlets:
            anomalies = detect_product_anomalies(db, outlet_id=outlet.id, lookback_days=30)
            for anom in anomalies:
                # Check if active anomaly alert exists
                existing_anomaly = (
                    db.query(Alert)
                    .filter(
                        Alert.product_id == anom["product_id"],
                        Alert.outlet_id == outlet.id,
                        Alert.alert_type == AlertType.sales_anomaly,
                        Alert.is_acknowledged.is_(False),
                    )
                    .first()
                )

                if not existing_anomaly:
                    severity = AlertSeverity.medium if abs(anom["z_score"]) < 3.5 else AlertSeverity.high
                    new_anom_alert = Alert(
                        outlet_id=outlet.id,
                        product_id=anom["product_id"],
                        alert_type=AlertType.sales_anomaly,
                        severity=severity,
                        message=f"{anom['message']} (z-score: {anom['z_score']})",
                    )
                    db.add(new_anom_alert)
                    logger.info(f"🔔 Created real Sales Anomaly Alert for {anom['product_name']} at Outlet {outlet.id}")

        db.commit()
        logger.info("✅ Inventory and anomaly checks completed.")

    except Exception as e:
        logger.error(f"❌ Low Stock & Anomaly Job Failed: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Initialize and start the background scheduler"""
    scheduler = BackgroundScheduler()

    # Add Low Stock Check Job (Every 4 hours)
    scheduler.add_job(
        check_low_stock_job,
        trigger=IntervalTrigger(hours=4),
        id="low_stock_check",
        name="Low Stock Alert Check",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("🚀 Background Scheduler Started")
    return scheduler
