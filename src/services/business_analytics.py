"""
Inventory Optimization Service
Week 14: EOQ, ABC Analysis, Reorder Alerts
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EOQResult:
    """Economic Order Quantity calculation result"""
    product_id: int
    product_name: str
    optimal_order_qty: int
    annual_demand: int
    ordering_cost: float
    holding_cost_rate: float
    reorder_point: int
    safety_stock: int
    total_annual_cost: float
    orders_per_year: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


class InventoryOptimizer:
    """
    Inventory optimization using classic operations research methods
    
    Methods:
    - EOQ (Economic Order Quantity)
    - Safety Stock calculation
    - Reorder Point optimization
    - ABC Analysis integration
    """
    
    def __init__(
        self,
        ordering_cost: float = 500,  # ₹500 per order
        holding_cost_rate: float = 0.20,  # 20% of item cost per year
        service_level: float = 0.95,  # 95% service level
        lead_time_days: int = 7
    ):
        self.ordering_cost = ordering_cost
        self.holding_cost_rate = holding_cost_rate
        self.service_level = service_level
        self.lead_time_days = lead_time_days
        self.results = {}
    
    def calculate_eoq(
        self,
        annual_demand: int,
        unit_cost: float,
        ordering_cost: float = None,
        holding_cost_rate: float = None
    ) -> Tuple[int, float]:
        """
        Calculate Economic Order Quantity
        
        EOQ = sqrt(2 * D * S / H)
        
        Args:
            annual_demand: Annual demand in units
            unit_cost: Cost per unit
            ordering_cost: Fixed cost per order
            holding_cost_rate: Annual holding cost as % of unit cost
        
        Returns:
            (optimal_quantity, annual_cost)
        """
        S = ordering_cost or self.ordering_cost
        H = unit_cost * (holding_cost_rate or self.holding_cost_rate)
        D = annual_demand
        
        if D <= 0 or H <= 0:
            return (1, S)
        
        # EOQ formula
        eoq = np.sqrt((2 * D * S) / H)
        eoq = max(1, int(round(eoq)))
        
        # Total annual cost
        annual_ordering_cost = (D / eoq) * S
        annual_holding_cost = (eoq / 2) * H
        total_cost = annual_ordering_cost + annual_holding_cost
        
        return (eoq, total_cost)
    
    def calculate_safety_stock(
        self,
        daily_demand_std: float,
        lead_time_days: int = None,
        service_level: float = None
    ) -> int:
        """
        Calculate safety stock for desired service level
        
        Safety Stock = Z * σ_d * sqrt(L)
        """
        from scipy import stats
        
        L = lead_time_days or self.lead_time_days
        sl = service_level or self.service_level
        
        # Z-score for service level
        z = stats.norm.ppf(sl)
        
        # Safety stock
        ss = z * daily_demand_std * np.sqrt(L)
        
        return max(0, int(round(ss)))
    
    def calculate_reorder_point(
        self,
        avg_daily_demand: float,
        lead_time_days: int = None,
        safety_stock: int = None,
        daily_demand_std: float = 0
    ) -> int:
        """
        Calculate reorder point
        
        ROP = (D_daily * L) + Safety Stock
        """
        L = lead_time_days or self.lead_time_days
        
        if safety_stock is None:
            safety_stock = self.calculate_safety_stock(daily_demand_std, L)
        
        rop = (avg_daily_demand * L) + safety_stock
        
        return max(1, int(round(rop)))
    
    def optimize_product(
        self,
        product_id: int,
        product_name: str,
        unit_cost: float,
        sales_history: pd.Series,  # Daily sales
        lead_time_days: int = None
    ) -> EOQResult:
        """
        Full optimization for a single product
        """
        # Calculate demand statistics
        daily_sales = sales_history.fillna(0)
        avg_daily_demand = daily_sales.mean()
        daily_demand_std = daily_sales.std()
        annual_demand = int(avg_daily_demand * 365)
        
        # EOQ
        eoq, annual_cost = self.calculate_eoq(annual_demand, unit_cost)
        
        # Safety stock
        safety_stock = self.calculate_safety_stock(
            daily_demand_std,
            lead_time_days or self.lead_time_days
        )
        
        # Reorder point
        rop = self.calculate_reorder_point(
            avg_daily_demand,
            lead_time_days or self.lead_time_days,
            safety_stock
        )
        
        # Orders per year
        orders_per_year = annual_demand / eoq if eoq > 0 else 0
        
        result = EOQResult(
            product_id=product_id,
            product_name=product_name,
            optimal_order_qty=eoq,
            annual_demand=annual_demand,
            ordering_cost=self.ordering_cost,
            holding_cost_rate=self.holding_cost_rate,
            reorder_point=rop,
            safety_stock=safety_stock,
            total_annual_cost=round(annual_cost, 2),
            orders_per_year=round(orders_per_year, 1)
        )
        
        self.results[product_id] = result
        return result
    
    def batch_optimize(
        self,
        products: pd.DataFrame,
        sales_data: pd.DataFrame
    ) -> List[EOQResult]:
        """
        Optimize multiple products
        
        Args:
            products: DataFrame with product_id, name, cost_price
            sales_data: DataFrame with product_id, date, quantity
        """
        results = []
        
        for _, product in products.iterrows():
            product_id = product['id']
            
            # Get sales history
            product_sales = sales_data[sales_data['product_id'] == product_id]['quantity']
            
            if len(product_sales) > 0:
                result = self.optimize_product(
                    product_id=product_id,
                    product_name=product.get('name', f'Product {product_id}'),
                    unit_cost=product.get('cost_price', 100),
                    sales_history=product_sales
                )
                results.append(result)
        
        return results


class ReorderAlertSystem:
    """
    Automated reorder alert system
    RQ4: Actionable alerts for inventory management
    """
    
    def __init__(self, optimizer: InventoryOptimizer = None):
        self.optimizer = optimizer or InventoryOptimizer()
        self.alerts = []
    
    def check_stock_levels(
        self,
        products: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Check all products for reorder alerts
        
        Args:
            products: DataFrame with id, name, stock_level, reorder_point
        """
        self.alerts = []
        
        for _, product in products.iterrows():
            stock = product.get('stock_level', 0)
            rop = product.get('reorder_point', 10)
            
            if stock <= 0:
                priority = 'CRITICAL'
                message = f"OUT OF STOCK - Order immediately"
            elif stock <= rop * 0.5:
                priority = 'HIGH'
                message = f"Stock critically low ({stock} units) - Order now"
            elif stock <= rop:
                priority = 'MEDIUM'
                message = f"Stock at reorder point ({stock}/{rop}) - Place order"
            elif stock <= rop * 1.2:
                priority = 'LOW'
                message = f"Stock approaching reorder point ({stock}/{rop})"
            else:
                continue  # No alert needed
            
            self.alerts.append({
                'product_id': product.get('id'),
                'product_name': product.get('name', 'Unknown'),
                'current_stock': stock,
                'reorder_point': rop,
                'priority': priority,
                'message': message,
                'suggested_order_qty': self.optimizer.results.get(
                    product.get('id'), EOQResult(0, '', 50, 0, 0, 0, 0, 0, 0, 0)
                ).optimal_order_qty,
                'created_at': datetime.now().isoformat()
            })
        
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        self.alerts.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return self.alerts
    
    def get_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        if not self.alerts:
            return {'total': 0, 'by_priority': {}}
        
        by_priority = {}
        for alert in self.alerts:
            p = alert['priority']
            by_priority[p] = by_priority.get(p, 0) + 1
        
        return {
            'total': len(self.alerts),
            'by_priority': by_priority,
            'critical_products': [
                a['product_name'] for a in self.alerts 
                if a['priority'] == 'CRITICAL'
            ][:5]
        }


class CustomerSegmentationService:
    """
    Week 15: Customer Analytics with RFM and K-means
    """
    
    def __init__(self):
        self.segments = {}
        self.rfm_data = None
    
    def calculate_rfm(
        self,
        transactions: pd.DataFrame,
        customer_id_col: str = 'customer_id',
        date_col: str = 'date',
        amount_col: str = 'amount',
        reference_date: date = None
    ) -> pd.DataFrame:
        """
        Calculate RFM scores for all customers
        """
        if reference_date is None:
            reference_date = transactions[date_col].max()
        
        # Group by customer
        rfm = transactions.groupby(customer_id_col).agg({
            date_col: lambda x: (reference_date - x.max()).days,  # Recency
            amount_col: ['count', 'sum']  # Frequency, Monetary
        })
        
        rfm.columns = ['recency', 'frequency', 'monetary']
        rfm = rfm.reset_index()
        
        # Score (1-5)
        rfm['R'] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1]).astype(int)
        rfm['F'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
        rfm['M'] = pd.qcut(rfm['monetary'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
        
        rfm['RFM_Score'] = rfm['R'] + rfm['F'] + rfm['M']
        rfm['RFM_Segment'] = rfm.apply(self._assign_segment, axis=1)
        
        self.rfm_data = rfm
        return rfm
    
    def _assign_segment(self, row) -> str:
        """Assign customer segment based on RFM scores"""
        r, f, m = row['R'], row['F'], row['M']
        
        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions'
        elif r >= 3 and f >= 3 and m >= 4:
            return 'Loyal'
        elif r >= 4 and f <= 2:
            return 'New'
        elif r >= 3 and f >= 3:
            return 'Potential Loyalist'
        elif r <= 2 and f >= 3 and m >= 3:
            return 'At Risk'
        elif r <= 2 and m >= 4:
            return 'Cant Lose'
        elif r <= 2:
            return 'Hibernating'
        else:
            return 'Regular'
    
    def cluster_customers(
        self,
        rfm_data: pd.DataFrame = None,
        n_clusters: int = 5
    ) -> pd.DataFrame:
        """
        K-means clustering on RFM features
        """
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        
        rfm = rfm_data if rfm_data is not None else self.rfm_data
        
        if rfm is None:
            raise ValueError("Must calculate RFM first or provide rfm_data")
        
        # Features
        X = rfm[['recency', 'frequency', 'monetary']].values
        
        # Scale
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Cluster
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        rfm['Cluster'] = kmeans.fit_predict(X_scaled)
        
        # Name clusters
        cluster_summary = rfm.groupby('Cluster').agg({
            'recency': 'mean',
            'frequency': 'mean',
            'monetary': 'mean'
        })
        
        cluster_names = {}
        for cluster in range(n_clusters):
            stats = cluster_summary.loc[cluster]
            if stats['monetary'] > cluster_summary['monetary'].median() and stats['frequency'] > cluster_summary['frequency'].median():
                cluster_names[cluster] = 'High Value'
            elif stats['recency'] < cluster_summary['recency'].median():
                cluster_names[cluster] = 'Active'
            elif stats['recency'] > cluster_summary['recency'].quantile(0.75):
                cluster_names[cluster] = 'Churned'
            else:
                cluster_names[cluster] = f'Segment {cluster}'
        
        rfm['Cluster_Name'] = rfm['Cluster'].map(cluster_names)
        
        self.rfm_data = rfm
        return rfm
    
    def get_segment_summary(self) -> Dict[str, Any]:
        """Get segment distribution summary"""
        if self.rfm_data is None:
            return {}
        
        summary = self.rfm_data.groupby('RFM_Segment').agg({
            'customer_id': 'count',
            'monetary': ['mean', 'sum'],
            'frequency': 'mean'
        }).round(2)
        
        summary.columns = ['count', 'avg_value', 'total_value', 'avg_frequency']
        
        return summary.to_dict('index')


class ModelExplainer:
    """
    Week 16: Model Explainability with SHAP-like explanations
    """
    
    def __init__(self, model=None):
        self.model = model
        self.feature_names = []
        self.importance = {}
    
    def explain_prediction(
        self,
        model,
        X: np.ndarray,
        feature_names: List[str],
        prediction: float
    ) -> Dict[str, Any]:
        """
        Generate feature-level explanation for a prediction
        Using permutation-based importance approximation
        """
        self.model = model
        self.feature_names = feature_names
        
        n_features = X.shape[1] if len(X.shape) > 1 else len(X)
        X_flat = X.flatten() if len(X.shape) > 1 else X
        
        # Baseline prediction
        baseline = model.predict(X.reshape(1, -1))[0]
        
        # Feature contributions (approximate SHAP-like)
        contributions = {}
        
        for i, name in enumerate(feature_names[:n_features]):
            # Perturb feature
            X_perturbed = X_flat.copy()
            X_perturbed[i] = 0  # Zero out feature
            
            perturbed_pred = model.predict(X_perturbed.reshape(1, -1))[0]
            contribution = baseline - perturbed_pred
            contributions[name] = round(float(contribution), 2)
        
        # Sort by absolute contribution
        sorted_contributions = dict(sorted(
            contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        ))
        
        return {
            'prediction': round(float(prediction), 2),
            'feature_contributions': sorted_contributions,
            'top_positive': [k for k, v in sorted_contributions.items() if v > 0][:3],
            'top_negative': [k for k, v in sorted_contributions.items() if v < 0][:3],
            'explanation': self._generate_explanation(sorted_contributions, prediction)
        }
    
    def _generate_explanation(
        self,
        contributions: Dict[str, float],
        prediction: float
    ) -> str:
        """Generate human-readable explanation"""
        positive = [(k, v) for k, v in contributions.items() if v > 0][:2]
        negative = [(k, v) for k, v in contributions.items() if v < 0][:2]
        
        parts = [f"Predicted value: {prediction:.0f}"]
        
        if positive:
            pos_str = ', '.join([f"{k} (+{v:.0f})" for k, v in positive])
            parts.append(f"Key drivers: {pos_str}")
        
        if negative:
            neg_str = ', '.join([f"{k} ({v:.0f})" for k, v in negative])
            parts.append(f"Reducing factors: {neg_str}")
        
        return ". ".join(parts)
    
    def get_global_importance(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str]
    ) -> Dict[str, float]:
        """
        Calculate global feature importance using permutation
        """
        from sklearn.metrics import mean_squared_error
        
        baseline_mse = mean_squared_error(y, model.predict(X))
        importance = {}
        
        for i, name in enumerate(feature_names):
            X_permuted = X.copy()
            np.random.shuffle(X_permuted[:, i])
            
            permuted_mse = mean_squared_error(y, model.predict(X_permuted))
            importance[name] = round((permuted_mse - baseline_mse) / baseline_mse * 100, 2)
        
        self.importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        return self.importance


# CLI for testing
if __name__ == "__main__":
    print("Testing Inventory Optimization...")
    
    # EOQ test
    optimizer = InventoryOptimizer()
    eoq, cost = optimizer.calculate_eoq(
        annual_demand=1000,
        unit_cost=100
    )
    print(f"EOQ: {eoq} units, Annual Cost: ₹{cost:,.2f}")
    
    # Safety stock
    ss = optimizer.calculate_safety_stock(daily_demand_std=5)
    print(f"Safety Stock: {ss} units")
    
    # Reorder point
    rop = optimizer.calculate_reorder_point(avg_daily_demand=10)
    print(f"Reorder Point: {rop} units")
    
    print("\nTesting Customer Segmentation...")
    
    # Mock data
    np.random.seed(42)
    transactions = pd.DataFrame({
        'customer_id': np.random.randint(1, 100, 1000),
        'date': pd.date_range('2024-01-01', periods=1000, freq='D')[:1000],
        'amount': np.random.uniform(100, 5000, 1000)
    })
    
    segmenter = CustomerSegmentationService()
    rfm = segmenter.calculate_rfm(transactions)
    print(f"RFM calculated for {len(rfm)} customers")
    print(f"Segments: {rfm['RFM_Segment'].value_counts().to_dict()}")
