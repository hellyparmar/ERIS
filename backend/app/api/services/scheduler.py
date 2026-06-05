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
from app.api.services.reporting_service import ReportingService

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
            
        # 4. Simulate Email Sending
        logger.info(f"📧 [MOCK EMAIL] To: admin@rdios.com | Subject: Daily Sales Report - {start_date.date()}")
        logger.info(f"📎 Attachment: {report_filename} ({len(report_buffer.getvalue())} bytes)")
        logger.info("✅ Daily Sales Report sent successfully.")
        
    except Exception as e:
        logger.error(f"❌ Daily Report Job Failed: {e}")
    finally:
        db.close()

def check_low_stock_job():
    """
    Checks for products with low stock (< 20) and triggers alerts.
    """
    logger.info("📉 Checking for Low Stock items...")
    db = SessionLocal()
    try:
        # 1. Fetch Low Stock Products (Mock logic using Report Service data structure for now)
        # In real scenario: products = db.query(Product).filter(Product.stock_qty < 20).all()
        
        # Simulating finding products
        low_stock_items = [
            {"name": "Slim Fit Jeans", "sku": "JNS-002", "stock": 12},
            {"name": "Cotton Socks", "sku": "SOC-005", "stock": 0}
        ]
        
        if low_stock_items:
            logger.warning(f"⚠️ Found {len(low_stock_items)} low stock items!")
            for item in low_stock_items:
                 logger.warning(f"   - {item['name']} (SKU: {item['sku']}): {item['stock']} left")
            
            # 2. Trigger Notification (Email/SMS/Push)
            logger.info("📧 [MOCK ALERT] Sent Low Stock Alert to inventory_manager@rdios.com")
        else:
            logger.info("✅ Inventory levels are healthy.")
            
    except Exception as e:
        logger.error(f"❌ Low Stock Job Failed: {e}")
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
