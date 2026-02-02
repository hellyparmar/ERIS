"""
Counterfactual Analysis Module - Week 11-12
What-if scenarios and intervention analysis for retail
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CounterfactualResult:
    """Result of a counterfactual query"""
    scenario: str
    factual_outcome: float
    counterfactual_outcome: float
    estimated_effect: float
    effect_percent: float
    confidence_interval: Tuple[float, float]
    actionable_insight: str
    
    def to_dict(self) -> Dict:
        return {
            'scenario': self.scenario,
            'factual_outcome': round(self.factual_outcome, 2),
            'counterfactual_outcome': round(self.counterfactual_outcome, 2),
            'estimated_effect': round(self.estimated_effect, 2),
            'effect_percent': round(self.effect_percent, 2),
            'ci_lower': round(self.confidence_interval[0], 2),
            'ci_upper': round(self.confidence_interval[1], 2),
            'actionable_insight': self.actionable_insight
        }


class CounterfactualAnalyzer:
    """
    Counterfactual analysis for retail scenarios
    
    Answers questions like:
    - "What would revenue have been if it hadn't rained last Tuesday?"
    - "What if we had run a promotion during Diwali week?"
    - "How much revenue did we lose due to monsoon?"
    """
    
    def __init__(self, data: pd.DataFrame = None):
        self.data = data
        self.outcome_model = None
        self.scaler = StandardScaler()
        self.feature_cols = []
        self.results = {}
    
    def fit_outcome_model(
        self,
        data: pd.DataFrame,
        outcome_col: str = 'revenue',
        feature_cols: List[str] = None,
        model_type: str = 'gradient_boosting'
    ):
        """
        Fit outcome prediction model for counterfactual estimation
        
        Args:
            data: Training data
            outcome_col: Outcome variable
            feature_cols: Features to use
            model_type: 'gradient_boosting', 'random_forest', or 'linear'
        """
        self.data = data.copy()
        self.outcome_col = outcome_col
        
        # Default features
        if feature_cols is None:
            feature_cols = ['is_holiday', 'is_monsoon', 'is_weekend', 'day_of_week', 'month']
        
        self.feature_cols = [c for c in feature_cols if c in data.columns]
        
        X = data[self.feature_cols].values
        y = data[outcome_col].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit model
        if model_type == 'gradient_boosting':
            self.outcome_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=42
            )
        elif model_type == 'random_forest':
            self.outcome_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=6,
                random_state=42
            )
        else:
            self.outcome_model = Ridge(alpha=1.0)
        
        self.outcome_model.fit(X_scaled, y)
        
        # Calculate training R²
        y_pred = self.outcome_model.predict(X_scaled)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        
        logger.info(f"Outcome model fitted. R² = {r2:.4f}")
        
        return self
    
    def predict_counterfactual(
        self,
        features: pd.DataFrame,
        intervention: Dict[str, Any]
    ) -> np.ndarray:
        """
        Predict outcomes under intervention
        
        Args:
            features: Original feature values
            intervention: Dict of {column: new_value} to modify
        
        Returns:
            Predicted outcomes under intervention
        """
        cf_features = features.copy()
        
        for col, value in intervention.items():
            if col in cf_features.columns:
                cf_features[col] = value
        
        X = cf_features[self.feature_cols].values
        X_scaled = self.scaler.transform(X)
        
        return self.outcome_model.predict(X_scaled)
    
    def what_if_no_monsoon(self) -> CounterfactualResult:
        """
        Counterfactual: What if there was no monsoon effect?
        Estimates revenue if monsoon hadn't reduced footfall
        """
        if self.data is None or self.outcome_model is None:
            raise ValueError("Must fit model first")
        
        monsoon_days = self.data[self.data['is_monsoon'] == 1].copy()
        
        if len(monsoon_days) == 0:
            return CounterfactualResult(
                scenario="No Monsoon",
                factual_outcome=0,
                counterfactual_outcome=0,
                estimated_effect=0,
                effect_percent=0,
                confidence_interval=(0, 0),
                actionable_insight="No monsoon days in data"
            )
        
        # Factual: actual revenue during monsoon
        factual = monsoon_days[self.outcome_col].sum()
        
        # Counterfactual: predicted revenue if is_monsoon = 0
        cf_predictions = self.predict_counterfactual(
            monsoon_days[self.feature_cols],
            {'is_monsoon': 0}
        )
        counterfactual = cf_predictions.sum()
        
        # Effect
        effect = counterfactual - factual
        effect_pct = (effect / factual) * 100 if factual > 0 else 0
        
        # Bootstrap CI
        bootstrap_effects = []
        for _ in range(100):
            idx = np.random.choice(len(monsoon_days), size=len(monsoon_days), replace=True)
            sample_factual = monsoon_days.iloc[idx][self.outcome_col].sum()
            sample_cf = cf_predictions[idx].sum()
            bootstrap_effects.append(sample_cf - sample_factual)
        
        ci = (np.percentile(bootstrap_effects, 2.5), np.percentile(bootstrap_effects, 97.5))
        
        result = CounterfactualResult(
            scenario="What if there was no monsoon effect?",
            factual_outcome=factual,
            counterfactual_outcome=counterfactual,
            estimated_effect=effect,
            effect_percent=effect_pct,
            confidence_interval=ci,
            actionable_insight=f"Monsoon reduced revenue by ₹{abs(effect):,.0f} ({abs(effect_pct):.1f}%). "
                              f"Consider monsoon-specific promotions and inventory adjustments."
        )
        
        self.results['no_monsoon'] = result
        return result
    
    def what_if_every_day_holiday(self) -> CounterfactualResult:
        """
        Counterfactual: What if every day had holiday-level demand?
        Upper bound of potential revenue
        """
        if self.data is None or self.outcome_model is None:
            raise ValueError("Must fit model first")
        
        non_holiday_days = self.data[self.data['is_holiday'] == 0].copy()
        
        # Factual
        factual = non_holiday_days[self.outcome_col].sum()
        
        # Counterfactual
        cf_predictions = self.predict_counterfactual(
            non_holiday_days[self.feature_cols],
            {'is_holiday': 1}
        )
        counterfactual = cf_predictions.sum()
        
        effect = counterfactual - factual
        effect_pct = (effect / factual) * 100 if factual > 0 else 0
        
        result = CounterfactualResult(
            scenario="What if every day had holiday-level demand?",
            factual_outcome=factual,
            counterfactual_outcome=counterfactual,
            estimated_effect=effect,
            effect_percent=effect_pct,
            confidence_interval=(effect * 0.8, effect * 1.2),
            actionable_insight=f"Maximum potential revenue increase: ₹{effect:,.0f} ({effect_pct:.1f}%). "
                              f"This represents the theoretical maximum if we could sustain holiday engagement year-round."
        )
        
        self.results['all_holidays'] = result
        return result
    
    def what_if_weekend_promotion(self, promotion_lift: float = 0.15) -> CounterfactualResult:
        """
        Counterfactual: What if we ran promotions every weekend?
        
        Args:
            promotion_lift: Expected lift from promotion (default 15%)
        """
        if self.data is None:
            raise ValueError("Must fit model first")
        
        weekend_days = self.data[self.data['is_weekend'] == 1].copy()
        
        # Factual
        factual = weekend_days[self.outcome_col].sum()
        
        # Counterfactual: add promotion lift
        counterfactual = factual * (1 + promotion_lift)
        
        effect = counterfactual - factual
        effect_pct = promotion_lift * 100
        
        # Estimate CI based on variance in weekend sales
        weekend_std = weekend_days[self.outcome_col].std()
        ci_effect = 1.96 * weekend_std * np.sqrt(len(weekend_days))
        ci = (effect - ci_effect, effect + ci_effect)
        
        result = CounterfactualResult(
            scenario=f"What if we ran {promotion_lift*100:.0f}% promotions every weekend?",
            factual_outcome=factual,
            counterfactual_outcome=counterfactual,
            estimated_effect=effect,
            effect_percent=effect_pct,
            confidence_interval=ci,
            actionable_insight=f"Weekend promotions could generate ₹{effect:,.0f} additional revenue. "
                              f"ROI depends on promotion costs. Target: keep promotion cost under {effect * 0.3:,.0f} (30% of lift)."
        )
        
        self.results['weekend_promotion'] = result
        return result
    
    def estimate_lost_revenue(
        self,
        treatment_col: str,
        treatment_value: int = 1
    ) -> Dict[str, Any]:
        """
        Estimate revenue lost/gained due to a treatment condition
        
        Args:
            treatment_col: Column representing treatment (e.g., 'is_monsoon')
            treatment_value: Value indicating treatment is active
        
        Returns:
            Dict with lost/gained revenue analysis
        """
        if self.data is None or self.outcome_model is None:
            raise ValueError("Must fit model first")
        
        # Get treated observations
        treated = self.data[self.data[treatment_col] == treatment_value].copy()
        
        if len(treated) == 0:
            return {'error': f'No observations with {treatment_col}={treatment_value}'}
        
        # Factual
        factual_total = treated[self.outcome_col].sum()
        factual_mean = treated[self.outcome_col].mean()
        
        # Counterfactual (treatment removed)
        cf_value = 0 if treatment_value == 1 else 1
        cf_predictions = self.predict_counterfactual(
            treated[self.feature_cols],
            {treatment_col: cf_value}
        )
        
        cf_total = cf_predictions.sum()
        cf_mean = cf_predictions.mean()
        
        # Revenue difference
        revenue_diff = cf_total - factual_total
        
        return {
            'treatment': treatment_col,
            'treatment_value': treatment_value,
            'days_affected': len(treated),
            'factual_total': round(factual_total, 2),
            'factual_daily_mean': round(factual_mean, 2),
            'counterfactual_total': round(cf_total, 2),
            'counterfactual_daily_mean': round(cf_mean, 2),
            'revenue_difference': round(revenue_diff, 2),
            'interpretation': f"{'Lost' if revenue_diff > 0 else 'Gained'} ₹{abs(revenue_diff):,.0f} "
                            f"due to {treatment_col}={treatment_value}"
        }
    
    def generate_intervention_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate prioritized intervention recommendations
        based on counterfactual analysis
        """
        recommendations = []
        
        # Analyze different scenarios
        if 'is_monsoon' in self.feature_cols:
            monsoon = self.what_if_no_monsoon()
            if abs(monsoon.estimated_effect) > 0:
                recommendations.append({
                    'priority': 1 if abs(monsoon.estimated_effect) > 100000 else 2,
                    'category': 'Seasonal Adjustment',
                    'intervention': 'Monsoon Strategy',
                    'estimated_impact': monsoon.estimated_effect,
                    'action_items': [
                        'Reduce perishable inventory by 20% during monsoon',
                        'Increase rain-appropriate product placement',
                        'Launch "Monsoon Essentials" campaign',
                        'Consider delivery partnerships for rainy days'
                    ]
                })
        
        if 'is_holiday' in self.feature_cols:
            holiday = self.what_if_every_day_holiday()
            recommendations.append({
                'priority': 1,
                'category': 'Demand Optimization',
                'intervention': 'Holiday Demand Capture',
                'estimated_impact': holiday.estimated_effect * 0.1,  # Assume capture 10%
                'action_items': [
                    'Extend holiday operating hours year-round on weekends',
                    'Create "everyday festival" promotional events',
                    'Implement loyalty rewards with holiday-like discounts',
                    'Partner with local events for increased traffic'
                ]
            })
        
        # Weekend promotions
        weekend = self.what_if_weekend_promotion(0.15)
        recommendations.append({
            'priority': 2,
            'category': 'Promotional Strategy',
            'intervention': 'Weekend Promotions',
            'estimated_impact': weekend.estimated_effect,
            'action_items': [
                'Implement 15% weekend discounts on slow-moving items',
                'Create "Weekend Specials" category highlighting deals',
                'Use SMS/WhatsApp notifications Friday evening',
                'Bundle products for higher basket size'
            ]
        })
        
        # Sort by priority and impact
        recommendations.sort(key=lambda x: (x['priority'], -abs(x['estimated_impact'])))
        
        return recommendations
    
    def run_full_counterfactual_analysis(self) -> Dict[str, Any]:
        """Run all counterfactual analyses"""
        results = {
            'generated_at': datetime.now().isoformat(),
            'scenarios': {}
        }
        
        try:
            results['scenarios']['no_monsoon'] = self.what_if_no_monsoon().to_dict()
        except Exception as e:
            results['scenarios']['no_monsoon'] = {'error': str(e)}
        
        try:
            results['scenarios']['all_holidays'] = self.what_if_every_day_holiday().to_dict()
        except Exception as e:
            results['scenarios']['all_holidays'] = {'error': str(e)}
        
        try:
            results['scenarios']['weekend_promotion'] = self.what_if_weekend_promotion().to_dict()
        except Exception as e:
            results['scenarios']['weekend_promotion'] = {'error': str(e)}
        
        results['recommendations'] = self.generate_intervention_recommendations()
        
        return results


class HolidayImpactQuantifier:
    """
    Specific analysis for holiday impact quantification
    Week 11 thesis requirement
    """
    
    def __init__(self, data: pd.DataFrame = None):
        self.data = data
        self.results = {}
    
    def quantify_diwali_effect(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Quantify specific Diwali effect"""
        self.data = data
        
        # Identify Diwali period (October 20-30 approximately)
        data['is_diwali'] = ((data['date'].dt.month == 10) & 
                            (data['date'].dt.day >= 20) & 
                            (data['date'].dt.day <= 30)).astype(int)
        
        diwali_days = data[data['is_diwali'] == 1]
        normal_oct = data[(data['date'].dt.month == 10) & (data['is_diwali'] == 0)]
        
        diwali_avg = diwali_days['revenue'].mean() if len(diwali_days) > 0 else 0
        normal_avg = normal_oct['revenue'].mean() if len(normal_oct) > 0 else 0
        
        effect = diwali_avg - normal_avg
        effect_pct = (effect / normal_avg * 100) if normal_avg > 0 else 0
        
        return {
            'holiday': 'Diwali',
            'diwali_days': len(diwali_days),
            'avg_diwali_revenue': round(diwali_avg, 2),
            'avg_normal_october_revenue': round(normal_avg, 2),
            'estimated_effect': round(effect, 2),
            'effect_percent': round(effect_pct, 2),
            'total_diwali_revenue': round(diwali_days['revenue'].sum(), 2),
            'interpretation': f"Diwali increases daily revenue by {effect_pct:.1f}% (₹{effect:,.0f}/day)"
        }
    
    def quantify_all_major_holidays(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Quantify effect of all major Indian holidays"""
        self.data = data
        
        holiday_effects = {}
        
        # Define holiday periods
        holidays = {
            'Diwali': {'month': 10, 'days': range(20, 31)},
            'Holi': {'month': 3, 'days': range(5, 12)},
            'Christmas': {'month': 12, 'days': range(23, 27)},
            'Independence_Day': {'month': 8, 'days': range(14, 17)},
            'Republic_Day': {'month': 1, 'days': range(25, 28)}
        }
        
        # Overall average for comparison
        overall_avg = data['revenue'].mean()
        
        for holiday_name, period in holidays.items():
            holiday_data = data[
                (data['date'].dt.month == period['month']) & 
                (data['date'].dt.day.isin(period['days']))
            ]
            
            if len(holiday_data) > 0:
                holiday_avg = holiday_data['revenue'].mean()
                effect = holiday_avg - overall_avg
                effect_pct = (effect / overall_avg * 100)
                
                holiday_effects[holiday_name] = {
                    'days_analyzed': len(holiday_data),
                    'avg_revenue': round(holiday_avg, 2),
                    'effect_vs_baseline': round(effect, 2),
                    'effect_percent': round(effect_pct, 2),
                    'significant': abs(effect_pct) > 10
                }
        
        # Rank holidays by impact
        ranked = sorted(
            holiday_effects.items(),
            key=lambda x: abs(x[1]['effect_percent']),
            reverse=True
        )
        
        return {
            'baseline_avg_revenue': round(overall_avg, 2),
            'holiday_effects': dict(ranked),
            'top_holiday': ranked[0][0] if ranked else None,
            'total_holiday_contribution': sum(
                h['effect_vs_baseline'] * h['days_analyzed'] 
                for h in holiday_effects.values()
            )
        }


# Package init
class CausalPackage:
    """Convenience class for causal analysis"""
    
    @staticmethod
    def quick_analysis(data: pd.DataFrame) -> Dict[str, Any]:
        """Run quick causal analysis on data"""
        from .causal_engine import RetailCausalAnalyzer
        
        analyzer = RetailCausalAnalyzer(data)
        return analyzer.run_full_analysis()


# CLI
if __name__ == "__main__":
    print("Testing Counterfactual Analysis...")
    
    # Generate synthetic data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    
    data = pd.DataFrame({
        'date': dates,
        'revenue': [50000 + np.random.normal(0, 5000) for _ in dates],
        'is_holiday': ((dates.month == 10) & (dates.day >= 20) & (dates.day <= 30)).astype(int),
        'is_monsoon': (dates.month.isin([6, 7, 8, 9])).astype(int),
        'is_weekend': (dates.dayofweek >= 5).astype(int),
        'day_of_week': dates.dayofweek,
        'month': dates.month
    })
    
    # Apply effects
    data.loc[data['is_holiday'] == 1, 'revenue'] += 15000
    data.loc[data['is_monsoon'] == 1, 'revenue'] -= 8000
    
    print(f"Data: {len(data)} days")
    
    # Counterfactual analysis
    analyzer = CounterfactualAnalyzer()
    analyzer.fit_outcome_model(data, 'revenue')
    
    # What-if scenarios
    monsoon = analyzer.what_if_no_monsoon()
    print(f"\n=== No Monsoon Scenario ===")
    print(f"Factual: ₹{monsoon.factual_outcome:,.0f}")
    print(f"Counterfactual: ₹{monsoon.counterfactual_outcome:,.0f}")
    print(f"Lost revenue: ₹{monsoon.estimated_effect:,.0f}")
    
    holiday = analyzer.what_if_every_day_holiday()
    print(f"\n=== Every Day Holiday Scenario ===")
    print(f"Potential gain: ₹{holiday.estimated_effect:,.0f}")
    
    weekend = analyzer.what_if_weekend_promotion()
    print(f"\n=== Weekend Promotion Scenario ===")
    print(f"Expected gain: ₹{weekend.estimated_effect:,.0f}")
    
    # Recommendations
    recs = analyzer.generate_intervention_recommendations()
    print(f"\n=== Recommendations ===")
    for rec in recs:
        print(f"P{rec['priority']}: {rec['intervention']} - ₹{rec['estimated_impact']:,.0f}")
