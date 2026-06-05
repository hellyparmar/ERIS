"""
Alert Engine Service - Automated Alert Generation and Notification Dispatch

Provides comprehensive alert monitoring for:
- Inventory levels and stockouts
- Sales anomalies and performance deviations
- Forecast accuracy monitoring

Integrates with MSG91 for WhatsApp notifications and SMTP for email alerts.
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session
from uuid import UUID

from app.models import (
    Alert, AlertType, AlertStatus, User, Outlet, Inventory, Product,
    Sale, ForecastResult
)

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Intelligent alert engine for retail operations monitoring.
    Handles inventory, sales, and forecast alerts.
    """

    def __init__(self, db: Session):
        """
        Initialize AlertEngine
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.msg91_api_key = os.getenv("MSG91_API_KEY")
        self.msg91_sender_id = os.getenv("MSG91_SENDER_ID")
        self.smtp_configured = os.getenv("SMTP_HOST") is not None

    def check_inventory_alerts(self, outlet_id: UUID) -> List[Alert]:
        """
        Check inventory levels and create/resolve alerts.
        
        Checks for:
        - Stockout (current_stock == 0)
        - Low stock (current_stock <= reorder_level)
        
        Args:
            outlet_id: UUID of outlet to check
            
        Returns:
            List of created alerts
        """
        alerts_created = []
        
        try:
            inventories = self.db.query(Inventory).filter(
                Inventory.outlet_id == outlet_id
            ).all()
            
            for inventory in inventories:
                product = inventory.product
                
                # Check for stockout
                if inventory.current_stock == 0:
                    alert = self._create_or_update_alert(
                        outlet_id=outlet_id,
                        product_id=inventory.product_id,
                        alert_type=AlertType.low_stock,
                        severity="critical",
                        current_value=float(inventory.current_stock),
                        threshold_value=float(product.reorder_level),
                        message=f"CRITICAL: Product '{product.name}' is out of stock"
                    )
                    if alert:
                        alerts_created.append(alert)
                
                # Check for low stock
                elif inventory.current_stock <= product.reorder_level:
                    alert = self._create_or_update_alert(
                        outlet_id=outlet_id,
                        product_id=inventory.product_id,
                        alert_type=AlertType.low_stock,
                        severity="high",
                        current_value=float(inventory.current_stock),
                        threshold_value=float(product.reorder_level),
                        message=f"Low stock for '{product.name}': {inventory.current_stock} units"
                    )
                    if alert:
                        alerts_created.append(alert)
                
                # Resolve if stock now adequate
                else:
                    self._resolve_alert(
                        outlet_id=outlet_id,
                        product_id=inventory.product_id,
                        alert_type=AlertType.low_stock
                    )
            
            logger.info(f"Inventory check for outlet {outlet_id}: {len(alerts_created)} alerts")
            
        except Exception as e:
            logger.error(f"Error checking inventory for outlet {outlet_id}: {str(e)}")
        
        return alerts_created

    def check_sales_anomalies(self, outlet_id: UUID) -> List[Alert]:
        """
        Detect sales anomalies by comparing to 30-day average.
        
        Args:
            outlet_id: UUID of outlet to check
            
        Returns:
            List of created alerts
        """
        alerts_created = []
        
        try:
            today = date.today()
            
            # Get today's revenue
            today_sales = self.db.query(
                func.sum(Sale.total_amount)
            ).filter(
                and_(
                    Sale.outlet_id == outlet_id,
                    Sale.sale_date == today
                )
            ).scalar() or 0
            
            # Get 30-day average
            thirty_days_ago = today - timedelta(days=30)
            avg_sales = self.db.query(
                func.avg(func.sum(Sale.total_amount))
            ).filter(
                and_(
                    Sale.outlet_id == outlet_id,
                    Sale.sale_date >= thirty_days_ago,
                    Sale.sale_date < today
                )
            ).group_by(Sale.sale_date).scalar() or today_sales
            
            if avg_sales > 0:
                # Check for 30% drop
                if today_sales < (avg_sales * 0.70):
                    alert = self._create_or_update_alert(
                        outlet_id=outlet_id,
                        product_id=None,
                        alert_type=AlertType.sales_drop,
                        severity="high",
                        current_value=float(today_sales),
                        threshold_value=float(avg_sales * 0.70),
                        message=f"Sales are 30%+ below 30-day average. Today: ₹{today_sales:.2f} vs Avg: ₹{avg_sales:.2f}"
                    )
                    if alert:
                        alerts_created.append(alert)
                
                # Check for 50% surge
                elif today_sales > (avg_sales * 1.50):
                    alert = self._create_or_update_alert(
                        outlet_id=outlet_id,
                        product_id=None,
                        alert_type=AlertType.sales_drop,
                        severity="low",
                        current_value=float(today_sales),
                        threshold_value=float(avg_sales * 1.50),
                        message=f"Sales are 50%+ above average — check stock adequacy"
                    )
                    if alert:
                        alerts_created.append(alert)
                
                # Resolve if back to normal
                else:
                    self._resolve_alert(
                        outlet_id=outlet_id,
                        product_id=None,
                        alert_type=AlertType.sales_drop
                    )
            
            logger.info(f"Sales anomaly check for outlet {outlet_id}: {len(alerts_created)} alerts")
            
        except Exception as e:
            logger.error(f"Error checking sales anomalies for outlet {outlet_id}: {str(e)}")
        
        return alerts_created

    def check_forecast_deviation(self, outlet_id: UUID) -> List[Alert]:
        """
        Compare yesterday's actual vs forecast sales.
        
        Creates alert if deviation > 25%
        
        Args:
            outlet_id: UUID of outlet to check
            
        Returns:
            List of created alerts
        """
        alerts_created = []
        
        try:
            yesterday = date.today() - timedelta(days=1)
            
            # Get yesterday's actual revenue
            actual_revenue = self.db.query(
                func.sum(Sale.total_amount)
            ).filter(
                and_(
                    Sale.outlet_id == outlet_id,
                    Sale.sale_date == yesterday
                )
            ).scalar() or 0
            
            # Get yesterday's forecast
            forecast = self.db.query(ForecastResult).filter(
                and_(
                    ForecastResult.outlet_id == outlet_id,
                    ForecastResult.forecast_date == yesterday,
                    ForecastResult.forecast_type == "sales"
                )
            ).first()
            
            if forecast and forecast.predicted_value > 0:
                deviation_pct = abs(actual_revenue - forecast.predicted_value) / forecast.predicted_value * 100
                
                if deviation_pct > 25:
                    alert = self._create_or_update_alert(
                        outlet_id=outlet_id,
                        product_id=None,
                        alert_type=AlertType.forecast_deviation,
                        severity="medium",
                        current_value=float(actual_revenue),
                        threshold_value=float(forecast.predicted_value),
                        message=f"Forecast deviation for {yesterday}: Actual ₹{actual_revenue:.2f} vs Forecasted ₹{forecast.predicted_value:.2f} ({deviation_pct:.1f}%)"
                    )
                    if alert:
                        alerts_created.append(alert)
            
            logger.info(f"Forecast deviation check for outlet {outlet_id}: {len(alerts_created)} alerts")
            
        except Exception as e:
            logger.error(f"Error checking forecast deviations for outlet {outlet_id}: {str(e)}")
        
        return alerts_created

    def dispatch_notifications(self, alert: Alert, users: List[User]) -> bool:
        """
        Dispatch notifications for critical/high alerts.
        
        Args:
            alert: Alert to dispatch
            users: Users to notify
            
        Returns:
            True if sent successfully
        """
        try:
            outlet = alert.outlet
            message = f"ERIS Alert [{alert.severity}]: {alert.message} — {outlet.name}"
            
            notification_sent = False
            
            for user in users:
                # Send WhatsApp if configured
                if self.msg91_api_key and hasattr(user, 'phone') and user.phone:
                    notification_sent |= self._send_whatsapp(user.phone, message)
                
                # Send Email if configured
                if self.smtp_configured and user.email:
                    notification_sent |= self._send_email(
                        user.email,
                        f"ERIS Alert [{alert.severity}]",
                        message,
                        outlet.name
                    )
            
            if notification_sent:
                alert.updated_at = datetime.utcnow()
                self.db.commit()
            
            return notification_sent
        
        except Exception as e:
            logger.error(f"Error dispatching notifications for alert {alert.alert_id}: {str(e)}")
            return False

    def run_all_checks(self, outlet_id: UUID) -> Dict[str, int]:
        """
        Run all alert checks for a given outlet.
        
        Args:
            outlet_id: UUID of outlet to check
            
        Returns:
            Dict with alert counts
        """
        results = {
            "inventory_alerts": 0,
            "sales_anomalies": 0,
            "forecast_deviations": 0,
            "total_alerts": 0
        }
        
        try:
            logger.info(f"Starting alert engine run for outlet {outlet_id}")
            
            inventory_alerts = self.check_inventory_alerts(outlet_id)
            sales_alerts = self.check_sales_anomalies(outlet_id)
            forecast_alerts = self.check_forecast_deviation(outlet_id)
            
            results["inventory_alerts"] = len(inventory_alerts)
            results["sales_anomalies"] = len(sales_alerts)
            results["forecast_deviations"] = len(forecast_alerts)
            results["total_alerts"] = sum([len(inventory_alerts), len(sales_alerts), len(forecast_alerts)])
            
            # Notify managers of critical/high alerts
            outlet = self.db.query(Outlet).filter(Outlet.outlet_id == outlet_id).first()
            if outlet:
                managers = self.db.query(User).filter(
                    and_(
                        User.outlet_id == outlet_id,
                        User.role.in_(["super_admin", "outlet_manager"])
                    )
                ).all()
                
                all_alerts = inventory_alerts + sales_alerts + forecast_alerts
                for alert in all_alerts:
                    if alert.severity in ["critical", "high"]:
                        self.dispatch_notifications(alert, managers)
            
            logger.info(f"Alert engine run completed for outlet {outlet_id}. Total: {results['total_alerts']}")
            
        except Exception as e:
            logger.error(f"Error in alert engine run for outlet {outlet_id}: {str(e)}")
        
        return results

    # ===== Private Helpers =====

    def _create_or_update_alert(
        self,
        outlet_id: UUID,
        product_id: Optional[UUID],
        alert_type: AlertType,
        severity: str,
        current_value: float,
        threshold_value: float,
        message: str
    ) -> Optional[Alert]:
        """
        Create or update unacknowledged alert of same type.
        """
        try:
            existing_alert = self.db.query(Alert).filter(
                and_(
                    Alert.outlet_id == outlet_id,
                    Alert.product_id == product_id,
                    Alert.alert_type == alert_type,
                    Alert.status == AlertStatus.active
                )
            ).first()
            
            if existing_alert:
                existing_alert.current_value = current_value
                existing_alert.updated_at = datetime.utcnow()
                self.db.commit()
                return existing_alert
            else:
                new_alert = Alert(
                    outlet_id=outlet_id,
                    product_id=product_id,
                    alert_type=alert_type,
                    threshold_value=threshold_value,
                    current_value=current_value,
                    status=AlertStatus.active,
                    message=message,
                    severity=severity
                )
                self.db.add(new_alert)
                self.db.commit()
                self.db.refresh(new_alert)
                return new_alert
        
        except Exception as e:
            logger.error(f"Error creating/updating alert: {str(e)}")
            self.db.rollback()
            return None

    def _resolve_alert(
        self,
        outlet_id: UUID,
        product_id: Optional[UUID],
        alert_type: AlertType
    ) -> None:
        """
        Resolve all active alerts of a specific type.
        """
        try:
            alerts = self.db.query(Alert).filter(
                and_(
                    Alert.outlet_id == outlet_id,
                    Alert.product_id == product_id,
                    Alert.alert_type == alert_type,
                    Alert.status == AlertStatus.active
                )
            ).all()
            
            for alert in alerts:
                alert.status = AlertStatus.resolved
                alert.resolved_at = datetime.utcnow()
            
            if alerts:
                self.db.commit()
                logger.info(f"Resolved {len(alerts)} alerts for outlet {outlet_id}")
        
        except Exception as e:
            logger.error(f"Error resolving alerts: {str(e)}")
            self.db.rollback()

    def _send_whatsapp(self, phone_number: str, message: str) -> bool:
        """
        Send WhatsApp via MSG91 API.
        """
        try:
            import requests
            
            url = "https://control.msg91.com/api/sendhttp.php"
            params = {
                "authkey": self.msg91_api_key,
                "mobiles": phone_number,
                "message": message,
                "sender": self.msg91_sender_id or "ERIS",
                "route": "4",
                "unicode": "1"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"WhatsApp sent to {phone_number}")
                return True
            else:
                logger.warning(f"WhatsApp send failed: {response.text}")
                return False
        
        except ImportError:
            logger.warning("requests library not available for WhatsApp")
            return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp: {str(e)}")
            return False

    def _send_email(self, email: str, subject: str, message: str, outlet_name: str) -> bool:
        """
        Send email notification via SMTP.
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_host = os.getenv("SMTP_HOST")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = email
            msg["Subject"] = subject
            
            body = f"{message}\n\nOutlet: {outlet_name}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {email}")
            return True
        
        except Exception as e:
            logger.warning(f"Error sending email: {str(e)}")
            return False
