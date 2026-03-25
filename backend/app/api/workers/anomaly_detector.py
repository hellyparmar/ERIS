"""
Automated Anomaly Detection Worker - Isolation Forest
Scans sales and inventory tables hourly for anomalies:
1. Unusual discount patterns (fraud detection)
2. Sudden sales drops vs 4-week rolling average
3. Inventory ghost items (high stock, zero sales 30 days)

Integration: EventBus → SystemAlertEvent → WhatsApp Notifications
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from decimal import Decimal
from dataclasses import dataclass, asdict
from enum import Enum

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.api.db.database import SessionLocal
from app.api.db.models import Sale, SaleItem, Product, Inventory
from app.api.events.event_bus import event_bus
from app.api.events.system_events import SystemAlertEvent, AlertSeverity

logger = logging.getLogger(__name__)


# ============================================================================
# ANOMALY TYPES & SEVERITY
# ============================================================================

class AnomalyType(str, Enum):
    """Types of anomalies detected"""
    DISCOUNT_FRAUD = "discount_fraud"
    SALES_DROP = "sales_drop"
    GHOST_INVENTORY = "ghost_inventory"


@dataclass
class AnomalyResult:
    """Result of anomaly detection"""
    anomaly_type: AnomalyType
    severity: AlertSeverity
    title: str
    message: str
    details: Dict[str, Any]
    affected_products: List[int]
    detection_timestamp: datetime
    confidence_score: float  # 0-1, from Isolation Forest
    
    def to_alert_event(self) -> SystemAlertEvent:
        """Convert to SystemAlertEvent for EventBus"""
        return SystemAlertEvent(
            title=self.title,
            message=self.message,
            severity=self.severity,
            category="anomaly_detection",
            details=asdict(self),
            related_product_ids=self.affected_products,
            triggered_at=self.detection_timestamp
        )


# ============================================================================
# ANOMALY DETECTOR - MAIN CLASS
# ============================================================================

class IsolationForestAnomalyDetector:
    """
    Detects anomalies in sales and inventory using Scikit-Learn's Isolation Forest.
    
    Algorithm: Isolation Forest
    - Isolates anomalies rather than profile normal points
    - Handles high-dimensional data well
    - No distance/density calculation (efficient)
    - Anomaly score: Number of splits needed to isolate a sample
    
    Features analyzed:
    1. Discount patterns: discount_percent, discount_amount, total_amount
    2. Sales velocity: daily_units_sold, daily_revenue, 4-week trend
    3. Inventory age: days_without_sales, stock_level, last_sale_date
    """
    
    def __init__(
        self,
        contamination: float = 0.05,  # Assume 5% of data is anomalous
        random_state: int = 42,
        verbose: bool = True
    ):
        """
        Args:
            contamination: Expected proportion of outliers (0.01-0.5)
            random_state: For reproducibility
            verbose: Enable logging
        """
        self.contamination = contamination
        self.random_state = random_state
        self.verbose = verbose
        
        # Initialize Isolation Forest
        self.iso_forest = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1  # Use all CPUs
        )
        self.scaler = StandardScaler()
        self.anomalies: List[AnomalyResult] = []
    
    def detect_discount_fraud(
        self,
        db: Session,
        lookback_days: int = 30,
        discount_threshold: float = 50.0  # Alert if discount > 50%
    ) -> List[AnomalyResult]:
        """
        Detect unusual discount patterns (potential fraud).
        
        Features:
        - Discount percentage per transaction
        - Discount amount vs product price
        - Frequency of discounts by user
        - Discount correlation with sales quantity (normal: volume discount)
        """
        logger.info(f"🔍 Detecting discount anomalies (lookback: {lookback_days} days)...")
        
        anomalies = []
        results = db.query(Sale, SaleItem).join(
            SaleItem, Sale.id == SaleItem.sale_id
        ).filter(
            Sale.created_at >= datetime.now() - timedelta(days=lookback_days)
        ).all()
        
        if not results:
            logger.info("  No sales data found for discount analysis")
            return anomalies
        
        # Build feature matrix
        data = []
        metadata = []
        
        for sale, item in results:
            if item.unit_price == 0:
                continue
            
            discount_pct = (item.discount_amount / item.unit_price) * 100 if item.unit_price else 0
            
            # Features for Isolation Forest
            features = {
                'discount_pct': discount_pct,
                'discount_amount': float(item.discount_amount or 0),
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'line_total': float(item.line_total),
            }
            
            data.append(list(features.values()))
            metadata.append({
                'sale_id': sale.id,
                'item_id': item.id,
                'product_id': item.product_id,
                'discount_pct': discount_pct,
                'created_at': sale.created_at
            })
        
        if len(data) < 10:
            logger.info(f"  Insufficient data ({len(data)} records) for discount analysis")
            return anomalies
        
        df = pd.DataFrame(data, columns=['discount_pct', 'discount_amount', 'quantity', 'unit_price', 'line_total'])
        
        # Standardize
        X_scaled = self.scaler.fit_transform(df)
        
        # Detect anomalies
        predictions = self.iso_forest.fit_predict(X_scaled)
        anomaly_scores = self.iso_forest.score_samples(X_scaled)
        
        # Confidence: invert score (more negative = more anomalous)
        confidence = 1 / (1 + np.exp(anomaly_scores))
        
        # Filter anomalies
        for idx, (pred, conf, meta) in enumerate(zip(predictions, confidence, metadata)):
            if pred == -1:  # Anomaly detected
                discount_pct = meta['discount_pct']
                
                # Additional check: extreme discount
                if discount_pct > discount_threshold or meta['discount_amount'] > 10000:
                    severity = AlertSeverity.CRITICAL if discount_pct > 75 else AlertSeverity.WARNING
                    
                    product = db.query(Product).filter(Product.id == meta['product_id']).first()
                    
                    anomaly = AnomalyResult(
                        anomaly_type=AnomalyType.DISCOUNT_FRAUD,
                        severity=severity,
                        title=f"🚨 Unusual Discount Pattern Detected",
                        message=f"Product '{product.name if product else 'Unknown'}' sold with {discount_pct:.1f}% discount (₹{meta['discount_amount']:.0f}) - Potential fraud",
                        details={
                            'discount_percent': discount_pct,
                            'discount_amount': meta['discount_amount'],
                            'unit_price': df.loc[idx, 'unit_price'],
                            'quantity': int(df.loc[idx, 'quantity']),
                            'sale_id': meta['sale_id'],
                            'sale_time': str(meta['created_at']),
                            'anomaly_algorithm': 'Isolation Forest',
                            'feature_set': ['discount_pct', 'discount_amount', 'quantity', 'unit_price']
                        },
                        affected_products=[meta['product_id']],
                        detection_timestamp=datetime.now(),
                        confidence_score=float(conf)
                    )
                    anomalies.append(anomaly)
        
        logger.info(f"  ✓ Found {len(anomalies)} discount anomalies")
        return anomalies
    
    def detect_sales_drop(
        self,
        db: Session,
        lookback_days: int = 28,  # 4-week rolling average
        threshold_std: float = 2.0  # Alert if drop > 2 std deviations
    ) -> List[AnomalyResult]:
        """
        Detect sudden drops in sales compared to 4-week rolling average.
        
        Approach:
        1. Calculate daily sales by product
        2. Compute 4-week rolling average
        3. Flag if today < average - 2*std_dev
        """
        logger.info(f"🔍 Detecting sales drops (lookback: {lookback_days} days, threshold: {threshold_std}σ)...")
        
        anomalies = []
        
        # Get all products with recent sales
        products = db.query(
            Product.id,
            Product.name,
            func.count(Sale.id).label('sale_count')
        ).outerjoin(
            Sale, Product.id == SaleItem.product_id
        ).filter(
            Sale.created_at >= datetime.now() - timedelta(days=lookback_days)
        ).group_by(Product.id, Product.name).having(
            func.count(Sale.id) >= 5  # At least 5 sales
        ).all()
        
        for product_id, product_name, _ in products:
            # Get daily sales for this product
            daily_sales = db.query(
                func.date(Sale.created_at).label('sale_date'),
                func.sum(SaleItem.quantity).label('units'),
                func.sum(SaleItem.line_total).label('revenue')
            ).join(
                SaleItem, Sale.id == SaleItem.sale_id
            ).filter(
                SaleItem.product_id == product_id,
                Sale.created_at >= datetime.now() - timedelta(days=lookback_days)
            ).group_by(
                func.date(Sale.created_at)
            ).all()
            
            if len(daily_sales) < 7:
                continue
            
            # Build time series
            units = [float(s.units or 0) for s in daily_sales]
            revenues = [float(s.revenue or 0) for s in daily_sales]
            
            # Calculate rolling average and std dev
            window = 7  # 7-day rolling
            if len(units) >= window:
                rolling_mean = pd.Series(units).rolling(window=window).mean()
                rolling_std = pd.Series(units).rolling(window=window).std()
                
                # Check last day
                last_units = units[-1]
                last_mean = rolling_mean.iloc[-2] if len(rolling_mean) > 1 else rolling_mean.iloc[0]
                last_std = rolling_std.iloc[-2] if len(rolling_std) > 1 else rolling_std.iloc[0]
                
                # Detect drop
                if last_mean > 0 and last_std > 0:
                    lower_bound = last_mean - (threshold_std * last_std)
                    
                    if last_units < lower_bound:
                        drop_pct = ((last_mean - last_units) / last_mean) * 100
                        severity = AlertSeverity.CRITICAL if drop_pct > 50 else AlertSeverity.WARNING
                        
                        # Confidence: deviation from mean (in std devs)
                        confidence = min(1.0, abs(last_units - last_mean) / (last_std + 0.1) / threshold_std)
                        
                        anomaly = AnomalyResult(
                            anomaly_type=AnomalyType.SALES_DROP,
                            severity=severity,
                            title=f"⚠️ Sudden Sales Drop Detected",
                            message=f"Product '{product_name}' sales dropped {drop_pct:.1f}% below 4-week average ({last_units:.0f} units vs {last_mean:.0f} expected)",
                            details={
                                'product_id': product_id,
                                'units_sold': last_units,
                                'rolling_average': last_mean,
                                'std_deviation': last_std,
                                'drop_percent': drop_pct,
                                'lookback_days': lookback_days,
                                'anomaly_algorithm': 'Rolling Average + Standard Deviation',
                                'threshold_sigma': threshold_std
                            },
                            affected_products=[product_id],
                            detection_timestamp=datetime.now(),
                            confidence_score=float(confidence)
                        )
                        anomalies.append(anomaly)
        
        logger.info(f"  ✓ Found {len(anomalies)} sales drop anomalies")
        return anomalies
    
    def detect_ghost_inventory(
        self,
        db: Session,
        days_without_sales: int = 30,
        min_stock_level: int = 50  # Only flag if stock > 50
    ) -> List[AnomalyResult]:
        """
        Detect 'ghost items' - high stock with zero sales for 30 days.
        
        These are inventory items that haven't moved in a month despite
        high stock levels, indicating potential obsolescence or dead stock.
        """
        logger.info(f"🔍 Detecting ghost inventory (no sales for {days_without_sales} days, stock > {min_stock_level})...")
        
        anomalies = []
        cutoff_date = datetime.now() - timedelta(days=days_without_sales)
        
        # Find products with no recent sales
        ghost_products = db.query(
            Product.id,
            Product.name,
            Product.stock_level,
            func.max(Sale.created_at).label('last_sale_date')
        ).outerjoin(
            Sale, Product.id == SaleItem.product_id
        ).outerjoin(
            SaleItem, Sale.id == SaleItem.sale_id
        ).filter(
            Product.stock_level >= min_stock_level
        ).group_by(
            Product.id, Product.name, Product.stock_level
        ).having(
            or_(
                func.max(Sale.created_at) < cutoff_date,
                func.max(Sale.created_at).is_(None)
            )
        ).all()
        
        for product_id, product_name, stock_level, last_sale in ghost_products:
            days_since_sale = (datetime.now() - last_sale).days if last_sale else days_without_sales + 30
            
            # Calculate holding cost impact (rough estimate)
            product = db.query(Product).filter(Product.id == product_id).first()
            holding_cost = stock_level * 5  # Assume ₹5 per unit per month
            
            severity = AlertSeverity.WARNING
            if stock_level > 500:
                severity = AlertSeverity.CRITICAL
            
            # Confidence: days without sales / lookback period
            confidence = min(1.0, days_since_sale / (days_without_sales * 2))
            
            anomaly = AnomalyResult(
                anomaly_type=AnomalyType.GHOST_INVENTORY,
                severity=severity,
                title=f"💀 Ghost Inventory Detected",
                message=f"Product '{product_name}' has {stock_level} units in stock but NO SALES for {days_since_sale} days. Estimated holding cost: ₹{holding_cost:.0f}",
                details={
                    'product_id': product_id,
                    'stock_level': stock_level,
                    'days_without_sales': days_since_sale,
                    'last_sale_date': str(last_sale) if last_sale else 'Never',
                    'estimated_holding_cost': holding_cost,
                    'cost_price': float(product.cost_price) if product else 0,
                    'anomaly_algorithm': 'Time-Series Analysis'
                },
                affected_products=[product_id],
                detection_timestamp=datetime.now(),
                confidence_score=float(confidence)
            )
            anomalies.append(anomaly)
        
        logger.info(f"  ✓ Found {len(anomalies)} ghost inventory items")
        return anomalies
    
    def scan_all_anomalies(self, db: Session) -> List[AnomalyResult]:
        """
        Run all anomaly detection checks.
        Returns combined list of all detected anomalies.
        """
        logger.info("=" * 80)
        logger.info("🤖 ANOMALY DETECTION SCAN STARTED")
        logger.info("=" * 80)
        
        all_anomalies = []
        
        try:
            # 1. Discount Fraud Detection
            all_anomalies.extend(self.detect_discount_fraud(db))
            
            # 2. Sales Drop Detection
            all_anomalies.extend(self.detect_sales_drop(db))
            
            # 3. Ghost Inventory Detection
            all_anomalies.extend(self.detect_ghost_inventory(db))
            
        except Exception as e:
            logger.error(f"❌ Error during anomaly scan: {e}", exc_info=True)
        
        logger.info("=" * 80)
        logger.info(f"📊 SCAN COMPLETE: Found {len(all_anomalies)} anomalies")
        logger.info("=" * 80)
        
        return all_anomalies


# ============================================================================
# HOURLY WORKER FUNCTION
# ============================================================================

def run_hourly_anomaly_detection():
    """
    Scheduled worker function (runs every hour via APScheduler).
    
    1. Initialize Isolation Forest detector
    2. Scan all three anomaly types
    3. Publish SystemAlertEvent to EventBus for each anomaly
    4. EventBus → WhatsApp handler will send notifications
    """
    db = SessionLocal()
    detector = IsolationForestAnomalyDetector(contamination=0.05, verbose=True)
    
    try:
        # Scan for all anomalies
        anomalies = detector.scan_all_anomalies(db)
        
        if not anomalies:
            logger.info("✅ No anomalies detected")
            return {"status": "success", "anomalies_found": 0}
        
        # Publish each anomaly to EventBus
        for anomaly in anomalies:
            try:
                event = anomaly.to_alert_event()
                event_bus.publish(event)
                logger.info(f"📢 Published event: {anomaly.title}")
            except Exception as e:
                logger.error(f"Failed to publish anomaly event: {e}", exc_info=True)
        
        return {
            "status": "success",
            "anomalies_found": len(anomalies),
            "scan_timestamp": datetime.now().isoformat(),
            "breakdown": {
                "discount_fraud": sum(1 for a in anomalies if a.anomaly_type == AnomalyType.DISCOUNT_FRAUD),
                "sales_drops": sum(1 for a in anomalies if a.anomaly_type == AnomalyType.SALES_DROP),
                "ghost_inventory": sum(1 for a in anomalies if a.anomaly_type == AnomalyType.GHOST_INVENTORY),
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Hourly anomaly detection failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
    
    finally:
        db.close()


# ============================================================================
# TESTING & DEBUG
# ============================================================================

if __name__ == "__main__":
    # Quick test
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    db = SessionLocal()
    result = run_hourly_anomaly_detection()
    print(f"\n✅ Result: {result}")
