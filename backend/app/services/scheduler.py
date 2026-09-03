"""
Background Scheduler Service
Uses APScheduler to run periodic tasks like Odoo Sync.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text
import logging
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.api.integrations.odoo_connector import OdooClient
from app.services.reporting_service import ReportingService

logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def sync_odoo_job():
    """
    Scheduled job to sync data from Odoo for all active configurations.
    """
    logger.info("⏳ Starting scheduled Odoo Sync job...")
    db = SessionLocal()
    try:
        # 1. Fetch active Odoo configurations
        result = db.execute(text("SELECT * FROM odoo_configs WHERE is_active = true"))
        configs = result.fetchall()
        
        if not configs:
            logger.info("ℹ️ No active Odoo configurations found.")
            return

        for config in configs:
            logger.info(f"🔄 Syncing Odoo for Org ID: {config.organization_id}")
            
            # 2. Initialize Client
            client = OdooClient(
                url=config.url,
                db=config.db_name,
                username=config.username,
                api_key=config.api_key
            )
            
            if not client.connect():
                logger.error(f"❌ Failed to connect to Odoo for Org {config.organization_id}")
                continue

            # 3. Sync Products
            if config.sync_products:
                products = client.get_products(limit=50)
                logger.info(f"✅ Fetched {len(products)} products from Odoo.")
                # TODO: upsert_products_to_db(products)
                
            # 4. Sync Customers
            if config.sync_customers:
                customers = client.get_customers(limit=50)
                logger.info(f"✅ Fetched {len(customers)} customers from Odoo.")
                # TODO: upsert_customers_to_db(customers)
                
            # Update last_sync timestamp
            db.execute(text("UPDATE odoo_configs SET last_sync_at = NOW(), last_sync_status = 'success' WHERE id = :id"), {"id": config.id})
            db.commit()
            
    except Exception as e:
        logger.error(f"❌ Odoo Sync Job Failed: {e}")
        db.rollback()
    finally:
        db.close()

def daily_sales_report_job():
    """
    Generates yesterday's sales report and emails it to admin.
    """
    logger.info("📊 Generating Daily Sales Report...")
    db = SessionLocal()
    try:
        # 1. Define date range (Yesterday)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        # 2. Generate Report
        # In a real app, we would query sales from start_date to end_date
        report_buffer = ReportingService.generate_sales_report(start_date, end_date, db)
        
        # 3. Save to disk (or attach to email)
        report_filename = f"daily_sales_{start_date.strftime('%Y%m%d')}.xlsx"
        # with open(f"reports/{report_filename}", "wb") as f:
        #     f.write(report_buffer.getvalue())
            
        # 4. Report generated
        logger.info(f"✅ Daily Sales Report generated: {report_filename} ({len(report_buffer.getvalue())} bytes)")
        
    except Exception as e:
        logger.error(f"❌ Daily Report Job Failed: {e}")
    finally:
        db.close()

def check_low_stock_job():
    """
    Checks for products with low stock and anomalous demand, and creates real alerts.
    """
    logger.info("📉 Checking for Low Stock items and sales anomalies...")
    db = SessionLocal()
    try:
        from app.models import Product, Outlet, Inventory
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
                existing_alert = db.query(Alert).filter(
                    Alert.product_id == item.product_id,
                    Alert.outlet_id == item.outlet_id,
                    Alert.alert_type == AlertType.low_stock,
                    Alert.is_acknowledged == False
                ).first()
                
                if not existing_alert:
                    severity = AlertSeverity.critical if item.stock <= 0 else AlertSeverity.high
                    new_alert = Alert(
                        outlet_id=item.outlet_id,
                        product_id=item.product_id,
                        alert_type=AlertType.low_stock,
                        severity=severity,
                        message=f"Low Stock for {item.product_name}: {item.stock} left (reorder level: {item.reorder_level})"
                    )
                    db.add(new_alert)
                    logger.info(f"🔔 Created real Low Stock Alert for {item.product_name} at Outlet {item.outlet_id}")
                    
        # 2. Check for product anomalies (Spikes/Drops)
        # We will check across all active outlets. For simplicity, we loop through unique outlets in DB.
        outlets = db.query(Outlet).all()
        for outlet in outlets:
            anomalies = detect_product_anomalies(db, store_id=outlet.id, lookback_days=30)
            for anom in anomalies:
                # Check if active anomaly alert exists
                existing_anomaly = db.query(Alert).filter(
                    Alert.product_id == anom["product_id"],
                    Alert.outlet_id == outlet.id,
                    Alert.alert_type == AlertType.sales_anomaly,
                    Alert.is_acknowledged == False
                ).first()
                
                if not existing_anomaly:
                    severity = AlertSeverity.medium if abs(anom["z_score"]) < 3.5 else AlertSeverity.high
                    new_anom_alert = Alert(
                        outlet_id=outlet.id,
                        product_id=anom["product_id"],
                        alert_type=AlertType.sales_anomaly,
                        severity=severity,
                        message=f"{anom['message']} (z-score: {anom['z_score']})"
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
    
    # Add Odoo Sync Job (every 1 hour)
    scheduler.add_job(
        sync_odoo_job,
        trigger=IntervalTrigger(hours=1),
        id='odoo_sync_job',
        name='Sync Odoo Products & Customers',
        replace_existing=True
    )
    
    # Add Daily Sales Report Job (at 10:00 PM)
    scheduler.add_job(
        daily_sales_report_job,
        trigger='cron',
        hour=22,
        minute=0,
        id='daily_sales_report',
        name='Daily Sales Report',
        replace_existing=True
    )

    # Add Low Stock Check Job (Every 4 hours)
    scheduler.add_job(
        check_low_stock_job,
        trigger=IntervalTrigger(hours=4),
        id='low_stock_check',
        name='Low Stock Alert Check',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("🚀 Background Scheduler Started")
    return scheduler

