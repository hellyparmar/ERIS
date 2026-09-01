"""
Causal Inference Engine - Week 9-10
DoWhy/CausalML-style implementation for retail causal analysis

This module implements causal inference methods for quantifying the impact
of treatments (holidays, weather, promotions) on retail outcomes.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Statistical imports will be lazy-loaded in methods that need them

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CausalEffect:
    """Represents a causal effect estimate"""
    treatment: str
    effect_type: str  # ATE, ATT, CATE
    estimate: float
    std_error: float
    confidence_interval: Tuple[float, float]
    p_value: float
    method: str
    sample_size: int
    treated_count: int
    control_count: int
    
    def to_dict(self) -> Dict:
        return {
            'treatment': self.treatment,
            'effect_type': self.effect_type,
            'estimate': round(self.estimate, 2),
            'std_error': round(self.std_error, 4),
            'ci_lower': round(self.confidence_interval[0], 2),
            'ci_upper': round(self.confidence_interval[1], 2),
            'p_value': round(self.p_value, 4),
            'significant': self.p_value < 0.05,
            'method': self.method,
            'sample_size': self.sample_size,
            'treated_count': self.treated_count,
            'control_count': self.control_count
        }
    
    def interpret(self) -> str:
        """Human-readable interpretation"""
        if self.p_value < 0.05:
            direction = "increases" if self.estimate > 0 else "decreases"
            return (f"{self.treatment} {direction} the outcome by {abs(self.estimate):.2f} units "
                   f"(95% CI: [{self.confidence_interval[0]:.2f}, {self.confidence_interval[1]:.2f}], "
                   f"p={self.p_value:.4f})")
        else:
            return f"{self.treatment} has no statistically significant effect (p={self.p_value:.4f})"


class CausalModel:
    """
    Causal Model for retail analytics
    
    Implements various causal inference methods:
    - Difference-in-Means (naive estimator)
    - Regression Adjustment
    - Inverse Propensity Weighting (IPW)
    - Doubly Robust / Double Machine Learning (DML)
    - Matching Estimators
    """
    
    def __init__(
        self,
        treatment_col: str,
        outcome_col: str,
        covariates: List[str] = None,
        propensity_model: str = 'logistic'
    ):
        """
        Initialize causal model
        
        Args:
            treatment_col: Name of treatment variable column (binary)
            outcome_col: Name of outcome variable column
            covariates: List of covariate column names for adjustment
            propensity_model: Model for propensity scores ('logistic', 'rf')
        """
        self.treatment_col = treatment_col
        self.outcome_col = outcome_col
        self.covariates = covariates or []
        self.propensity_model = propensity_model
        
        self.data = None
        self.propensity_scores = None
        self.effects = {}
    
    def fit(self, data: pd.DataFrame) -> 'CausalModel':
        """Fit the causal model with data"""
        self.data = data.copy()
        
        # Validate columns
        required = [self.treatment_col, self.outcome_col] + self.covariates
        missing = [c for c in required if c not in data.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        
        # Estimate propensity scores
        if self.covariates:
            self._estimate_propensity_scores()
        
        logger.info(f"Fitted causal model with {len(data)} observations")
        return self
    
    def _estimate_propensity_scores(self):
        """Estimate propensity scores P(T=1|X)"""
        X = self.data[self.covariates].values
        T = self.data[self.treatment_col].values
        
        # Standardize covariates
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LogisticRegression
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        if self.propensity_model == 'logistic':
            model = LogisticRegression(max_iter=1000, solver='lbfgs')
        else:
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=100, max_depth=5)
        
        model.fit(X_scaled, T)
        self.propensity_scores = model.predict_proba(X_scaled)[:, 1]
        
        # Clip to avoid extreme weights
        self.propensity_scores = np.clip(self.propensity_scores, 0.01, 0.99)
        
        logger.info(f"Propensity scores: mean={self.propensity_scores.mean():.3f}, "
                   f"std={self.propensity_scores.std():.3f}")
    
    def estimate_ate_naive(self) -> CausalEffect:
        """
        Naive difference-in-means estimator
        ATE = E[Y|T=1] - E[Y|T=0]
        Assumes no confounding (often unrealistic)
        """
        treated = self.data[self.data[self.treatment_col] == 1][self.outcome_col]
        control = self.data[self.data[self.treatment_col] == 0][self.outcome_col]
        
        ate = treated.mean() - control.mean()
        
        # Standard error using pooled variance
        se = np.sqrt(treated.var() / len(treated) + control.var() / len(control))
        
        # Welch's t-test
        from scipy import stats
        t_stat, p_value = stats.ttest_ind(treated, control, equal_var=False)
        
        ci = (ate - 1.96 * se, ate + 1.96 * se)
        
        effect = CausalEffect(
            treatment=self.treatment_col,
            effect_type='ATE',
            estimate=ate,
            std_error=se,
            confidence_interval=ci,
            p_value=p_value,
            method='Difference-in-Means',
            sample_size=len(self.data),
            treated_count=len(treated),
            control_count=len(control)
        )
        
        self.effects['naive'] = effect
        return effect
    
    def estimate_ate_regression(self) -> CausalEffect:
        """
        Regression adjustment estimator
        Controls for covariates via OLS
        Y = β₀ + β₁*T + β₂*X + ε
        """
        # Prepare data
        X = self.data[self.covariates + [self.treatment_col]].copy()
        X = sm.add_constant(X)
        y = self.data[self.outcome_col].values
        
        # Fit OLS
        model = sm.OLS(y, X).fit()
        
        # Treatment effect is coefficient on treatment variable
        ate = model.params[self.treatment_col]
        se = model.bse[self.treatment_col]
        p_value = model.pvalues[self.treatment_col]
        
        ci = model.conf_int().loc[self.treatment_col].values
        
        treated = self.data[self.data[self.treatment_col] == 1]
        control = self.data[self.data[self.treatment_col] == 0]
        
        effect = CausalEffect(
            treatment=self.treatment_col,
            effect_type='ATE',
            estimate=ate,
            std_error=se,
            confidence_interval=(ci[0], ci[1]),
            p_value=p_value,
            method='Regression Adjustment (OLS)',
            sample_size=len(self.data),
            treated_count=len(treated),
            control_count=len(control)
        )
        
        self.effects['regression'] = effect
        return effect
    
    def estimate_ate_ipw(self) -> CausalEffect:
        """
        Inverse Propensity Weighting (IPW) estimator
        
        ATE = E[Y*T/e(X)] - E[Y*(1-T)/(1-e(X))]
        
        Reweights observations to approximate randomized experiment
        """
        if self.propensity_scores is None:
            self._estimate_propensity_scores()
        
        T = self.data[self.treatment_col].values
        Y = self.data[self.outcome_col].values
        e = self.propensity_scores
        
        # IPW weights
        weights_treated = T / e
        weights_control = (1 - T) / (1 - e)
        
        # Weighted means
        y_treated_weighted = np.sum(Y * weights_treated) / np.sum(weights_treated)
        y_control_weighted = np.sum(Y * weights_control) / np.sum(weights_control)
        
        ate = y_treated_weighted - y_control_weighted
        
        # Bootstrap for standard error
        bootstrap_ates = []
        n_bootstrap = 200
        n = len(self.data)
        
        for _ in range(n_bootstrap):
            idx = np.random.choice(n, size=n, replace=True)
            T_b, Y_b, e_b = T[idx], Y[idx], e[idx]
            
            w_t = T_b / e_b
            w_c = (1 - T_b) / (1 - e_b)
            
            y_t = np.sum(Y_b * w_t) / np.sum(w_t)
            y_c = np.sum(Y_b * w_c) / np.sum(w_c)
            
            bootstrap_ates.append(y_t - y_c)
        
        se = np.std(bootstrap_ates)
        ci = (np.percentile(bootstrap_ates, 2.5), np.percentile(bootstrap_ates, 97.5))
        
        # Approximate p-value
        z_stat = ate / se if se > 0 else 0
        from scipy import stats
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        treated_count = int(T.sum())
        
        effect = CausalEffect(
            treatment=self.treatment_col,
            effect_type='ATE',
            estimate=ate,
            std_error=se,
            confidence_interval=ci,
            p_value=p_value,
            method='Inverse Propensity Weighting (IPW)',
            sample_size=len(self.data),
            treated_count=treated_count,
            control_count=len(self.data) - treated_count
        )
        
        self.effects['ipw'] = effect
        return effect
    
    def estimate_ate_doubly_robust(self) -> CausalEffect:
        """
        Doubly Robust / Augmented IPW (AIPW) estimator
        
        Combines regression adjustment and IPW
        Consistent if either propensity OR outcome model is correct
        
        Also known as Double Machine Learning (DML) foundation
        """
        if self.propensity_scores is None:
            self._estimate_propensity_scores()
        
        T = self.data[self.treatment_col].values
        Y = self.data[self.outcome_col].values
        X = self.data[self.covariates].values
        e = self.propensity_scores
        
        # Fit outcome models for treated and control
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import Ridge
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Model E[Y|X, T=1]
        model_t1 = Ridge(alpha=1.0)
        mask_t1 = T == 1
        if mask_t1.sum() > 0:
            model_t1.fit(X_scaled[mask_t1], Y[mask_t1])
            mu1 = model_t1.predict(X_scaled)
        else:
            mu1 = np.zeros(len(Y))
        
        # Model E[Y|X, T=0]
        model_t0 = Ridge(alpha=1.0)
        mask_t0 = T == 0
        if mask_t0.sum() > 0:
            model_t0.fit(X_scaled[mask_t0], Y[mask_t0])
            mu0 = model_t0.predict(X_scaled)
        else:
            mu0 = np.zeros(len(Y))
        
        # AIPW estimator
        psi1 = mu1 + T * (Y - mu1) / e
        psi0 = mu0 + (1 - T) * (Y - mu0) / (1 - e)
        
        ate = np.mean(psi1 - psi0)
        
        # Influence function based variance
        influence = psi1 - psi0 - ate
        var_ate = np.var(influence) / len(influence)
        se = np.sqrt(var_ate)
        
        z_stat = ate / se if se > 0 else 0
        from scipy import stats
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        ci = (ate - 1.96 * se, ate + 1.96 * se)
        
        treated_count = int(T.sum())
        
        effect = CausalEffect(
            treatment=self.treatment_col,
            effect_type='ATE',
            estimate=ate,
            std_error=se,
            confidence_interval=ci,
            p_value=p_value,
            method='Doubly Robust (AIPW)',
            sample_size=len(self.data),
            treated_count=treated_count,
            control_count=len(self.data) - treated_count
        )
        
        self.effects['doubly_robust'] = effect
        return effect
    
    def estimate_ate_matching(self, n_neighbors: int = 5) -> CausalEffect:
        """
        Matching estimator using nearest neighbors
        
        For each treated unit, find similar control units and vice versa
        """
        X = self.data[self.covariates].values
        T = self.data[self.treatment_col].values
        Y = self.data[self.outcome_col].values
        
        from sklearn.preprocessing import StandardScaler
        from sklearn.neighbors import NearestNeighbors
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        treated_idx = np.where(T == 1)[0]
        control_idx = np.where(T == 0)[0]
        
        # Match treated to controls
        if len(control_idx) >= n_neighbors:
            nn_control = NearestNeighbors(n_neighbors=n_neighbors)
            nn_control.fit(X_scaled[control_idx])
            
            _, neighbor_idx = nn_control.kneighbors(X_scaled[treated_idx])
            matched_control_outcomes = Y[control_idx[neighbor_idx]].mean(axis=1)
            
            # ATT: Average Treatment Effect on Treated
            att = np.mean(Y[treated_idx] - matched_control_outcomes)
        else:
            att = Y[treated_idx].mean() - Y[control_idx].mean() if len(control_idx) > 0 else 0
        
        # Match controls to treated
        if len(treated_idx) >= n_neighbors:
            nn_treated = NearestNeighbors(n_neighbors=n_neighbors)
            nn_treated.fit(X_scaled[treated_idx])
            
            _, neighbor_idx = nn_treated.kneighbors(X_scaled[control_idx])
            matched_treated_outcomes = Y[treated_idx[neighbor_idx]].mean(axis=1)
            
            # ATC: Average Treatment Effect on Controls
            atc = np.mean(matched_treated_outcomes - Y[control_idx])
        else:
            atc = att
        
        # ATE as weighted average
        n_t = len(treated_idx)
        n_c = len(control_idx)
        ate = (n_t * att + n_c * atc) / (n_t + n_c) if (n_t + n_c) > 0 else 0
        
        # Bootstrap for SE
        bootstrap_ates = []
        for _ in range(100):
            idx = np.random.choice(len(self.data), size=len(self.data), replace=True)
            if len(np.unique(T[idx])) < 2:
                continue
            
            t_mask = T[idx] == 1
            c_mask = T[idx] == 0
            
            if t_mask.sum() > 0 and c_mask.sum() > 0:
                diff = Y[idx][t_mask].mean() - Y[idx][c_mask].mean()
                bootstrap_ates.append(diff)
        
        se = np.std(bootstrap_ates) if bootstrap_ates else 0
        ci = (np.percentile(bootstrap_ates, 2.5) if bootstrap_ates else ate - 2*se,
              np.percentile(bootstrap_ates, 97.5) if bootstrap_ates else ate + 2*se)
        
        z_stat = ate / se if se > 0 else 0
        from scipy import stats
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        effect = CausalEffect(
            treatment=self.treatment_col,
            effect_type='ATE',
            estimate=ate,
            std_error=se,
            confidence_interval=ci,
            p_value=p_value,
            method=f'Nearest Neighbor Matching (k={n_neighbors})',
            sample_size=len(self.data),
            treated_count=len(treated_idx),
            control_count=len(control_idx)
        )
        
        self.effects['matching'] = effect
        return effect
    
    def estimate_all(self) -> Dict[str, CausalEffect]:
        """Run all estimation methods"""
        self.estimate_ate_naive()
        
        if self.covariates:
            self.estimate_ate_regression()
            self.estimate_ate_ipw()
            self.estimate_ate_doubly_robust()
            self.estimate_ate_matching()
        
        return self.effects
    
    def summary(self) -> pd.DataFrame:
        """Generate summary table of all estimates"""
        if not self.effects:
            self.estimate_all()
        
        rows = []
        for method, effect in self.effects.items():
            rows.append({
                'Method': effect.method,
                'Estimate': effect.estimate,
                'Std Error': effect.std_error,
                'CI Lower': effect.confidence_interval[0],
                'CI Upper': effect.confidence_interval[1],
                'P-Value': effect.p_value,
                'Significant': effect.p_value < 0.05
            })
        
        return pd.DataFrame(rows)


class RetailCausalAnalyzer:
    """
    High-level causal analyzer for retail data
    Analyzes impact of holidays, weather, promotions on sales
    """
    
    def __init__(self, data: pd.DataFrame = None):
        self.data = data
        self.results = {}
    
    def load_data(self, path: str = 'data/transformed') -> pd.DataFrame:
        """Load and prepare retail data for causal analysis"""
        data_path = Path(path)
        
        orders_path = data_path / 'orders_transformed.csv'
        items_path = data_path / 'order_items_transformed.csv'
        
        if orders_path.exists() and items_path.exists():
            orders = pd.read_csv(orders_path)
            items = pd.read_csv(items_path)
            
            orders['order_date'] = pd.to_datetime(orders['order_date'])
            
            # Aggregate to daily
            merged = items.merge(
                orders[['order_id', 'order_date', 'is_holiday', 'is_monsoon']],
                left_on='invoice_number', right_on='order_id', how='left'
            )
            
            daily = merged.groupby(merged['order_date'].dt.date).agg({
                'price_inr': 'sum',
                'order_id': 'nunique',
                'is_holiday': 'max',
                'is_monsoon': 'max'
            }).reset_index()
            
            daily.columns = ['date', 'revenue', 'orders', 'is_holiday', 'is_monsoon']
            daily['date'] = pd.to_datetime(daily['date'])
            
            self.data = daily
        else:
            self.data = self._generate_synthetic_data()
        
        # Add time features
        self.data['day_of_week'] = self.data['date'].dt.dayofweek
        self.data['month'] = self.data['date'].dt.month
        self.data['is_weekend'] = self.data['day_of_week'].isin([5, 6]).astype(int)
        
        logger.info(f"Loaded {len(self.data)} days of data")
        return self.data
    
    def _generate_synthetic_data(self) -> pd.DataFrame:
        """Generate synthetic data with known causal effects"""
        np.random.seed(42)
        dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')
        
        data = []
        base_revenue = 50000
        
        # TRUE CAUSAL EFFECTS (for validation)
        HOLIDAY_EFFECT = 18000  # +₹18,000 during holidays
        MONSOON_EFFECT = -7500  # -₹7,500 during monsoon
        
        for i, date in enumerate(dates):
            # Base with trend
            revenue = base_revenue * (1 + 0.0002 * i)
            
            # Day of week effect
            dow = date.dayofweek
            revenue *= 1 + 0.08 * np.sin(dow * 2 * np.pi / 7)
            
            # Treatment variables
            is_holiday = 1 if (date.month == 10 and 20 <= date.day <= 30) or \
                             (date.month == 3 and 5 <= date.day <= 10) or \
                             (date.month == 12 and 23 <= date.day <= 26) else 0
            
            is_monsoon = 1 if date.month in [6, 7, 8, 9] else 0
            
            # Apply TRUE causal effects
            if is_holiday:
                revenue += HOLIDAY_EFFECT
            
            if is_monsoon:
                revenue += MONSOON_EFFECT
            
            # Random noise
            revenue += np.random.normal(0, 5000)
            revenue = max(revenue, 10000)
            
            data.append({
                'date': date,
                'revenue': revenue,
                'orders': int(revenue / 500),
                'is_holiday': is_holiday,
                'is_monsoon': is_monsoon
            })
        
        logger.info(f"Generated synthetic data with TRUE effects: Holiday=+{HOLIDAY_EFFECT}, Monsoon={MONSOON_EFFECT}")
        
        return pd.DataFrame(data)
    
    def analyze_holiday_effect(self) -> Dict[str, Any]:
        """
        Analyze causal effect of holidays on sales
        """
        if self.data is None:
            self.load_data()
        
        covariates = ['day_of_week', 'month', 'is_weekend']
        available_covariates = [c for c in covariates if c in self.data.columns]
        
        model = CausalModel(
            treatment_col='is_holiday',
            outcome_col='revenue',
            covariates=available_covariates
        )
        
        model.fit(self.data)
        effects = model.estimate_all()
        
        summary = model.summary()
        
        # Best estimate (use doubly robust if available)
        best_method = 'doubly_robust' if 'doubly_robust' in effects else 'naive'
        best_effect = effects[best_method]
        
        result = {
            'treatment': 'Holiday',
            'best_estimate': best_effect.to_dict(),
            'interpretation': best_effect.interpret(),
            'all_methods': {k: v.to_dict() for k, v in effects.items()},
            'summary_table': summary.to_dict('records'),
            'recommendation': self._holiday_recommendation(best_effect)
        }
        
        self.results['holiday'] = result
        return result
    
    def analyze_monsoon_effect(self) -> Dict[str, Any]:
        """
        Analyze causal effect of monsoon season on sales
        """
        if self.data is None:
            self.load_data()
        
        covariates = ['day_of_week', 'month', 'is_weekend']
        available_covariates = [c for c in covariates if c in self.data.columns]
        
        model = CausalModel(
            treatment_col='is_monsoon',
            outcome_col='revenue',
            covariates=available_covariates
        )
        
        model.fit(self.data)
        effects = model.estimate_all()
        
        summary = model.summary()
        
        best_method = 'doubly_robust' if 'doubly_robust' in effects else 'naive'
        best_effect = effects[best_method]
        
        result = {
            'treatment': 'Monsoon',
            'best_estimate': best_effect.to_dict(),
            'interpretation': best_effect.interpret(),
            'all_methods': {k: v.to_dict() for k, v in effects.items()},
            'summary_table': summary.to_dict('records'),
            'recommendation': self._monsoon_recommendation(best_effect)
        }
        
        self.results['monsoon'] = result
        return result
    
    def _holiday_recommendation(self, effect: CausalEffect) -> str:
        """Generate business recommendation based on holiday effect"""
        if effect.p_value >= 0.05:
            return "Holiday effect not statistically significant. Review data quality."
        
        if effect.estimate > 0:
            lift_pct = (effect.estimate / self.data['revenue'].mean()) * 100
            return (f"Holidays increase revenue by ₹{effect.estimate:,.0f} ({lift_pct:.1f}%). "
                   f"Recommendations: (1) Increase inventory 2 weeks before major holidays, "
                   f"(2) Schedule additional staff, (3) Plan targeted marketing campaigns.")
        else:
            return "Unexpected negative holiday effect. Investigate operational issues."
    
    def _monsoon_recommendation(self, effect: CausalEffect) -> str:
        """Generate business recommendation based on monsoon effect"""
        if effect.p_value >= 0.05:
            return "Monsoon effect not statistically significant."
        
        if effect.estimate < 0:
            loss_pct = abs(effect.estimate / self.data['revenue'].mean()) * 100
            return (f"Monsoon decreases revenue by ₹{abs(effect.estimate):,.0f} ({loss_pct:.1f}%). "
                   f"Recommendations: (1) Reduce perishable inventory during monsoon, "
                   f"(2) Promote indoor/home products, (3) Offer monsoon discounts to maintain footfall.")
        else:
            return "Positive monsoon effect - likely monsoon-specific products doing well."
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete causal analysis"""
        if self.data is None:
            self.load_data()
        
        logger.info("Running full causal analysis...")
        
        holiday_results = self.analyze_holiday_effect()
        monsoon_results = self.analyze_monsoon_effect()
        
        return {
            'generated_at': datetime.now().isoformat(),
            'data_summary': {
                'total_days': len(self.data),
                'date_range': f"{self.data['date'].min()} to {self.data['date'].max()}",
                'avg_daily_revenue': self.data['revenue'].mean(),
                'holiday_days': self.data['is_holiday'].sum(),
                'monsoon_days': self.data['is_monsoon'].sum()
            },
            'holiday_analysis': holiday_results,
            'monsoon_analysis': monsoon_results,
            'thesis_rq1_answer': self._generate_rq1_answer()
        }
    
    def _generate_rq1_answer(self) -> str:
        """Generate answer for RQ1"""
        holiday = self.results.get('holiday', {}).get('best_estimate', {})
        monsoon = self.results.get('monsoon', {}).get('best_estimate', {})
        
        h_sig = "significantly" if holiday.get('significant', False) else "not significantly"
        m_sig = "significantly" if monsoon.get('significant', False) else "not significantly"
        
        return (f"RQ1: Holidays {h_sig} affect retail sales (effect: ₹{holiday.get('estimate', 0):,.0f}). "
               f"Monsoon {m_sig} affects sales (effect: ₹{monsoon.get('estimate', 0):,.0f}). "
               f"These findings support the use of causal inference for retail decision-making.")


# CLI for testing
if __name__ == "__main__":
    print("Testing Causal Inference Engine...")
    
    analyzer = RetailCausalAnalyzer()
    data = analyzer.load_data()
    
    print(f"\nData loaded: {len(data)} days")
    print(f"Holiday days: {data['is_holiday'].sum()}")
    print(f"Monsoon days: {data['is_monsoon'].sum()}")
    
    # Run analysis
    results = analyzer.run_full_analysis()
    
    print("\n=== Holiday Effect ===")
    holiday = results['holiday_analysis']['best_estimate']
    print(f"Estimate: ₹{holiday['estimate']:,.0f}")
    print(f"95% CI: [₹{holiday['ci_lower']:,.0f}, ₹{holiday['ci_upper']:,.0f}]")
    print(f"P-value: {holiday['p_value']:.4f}")
    print(f"Significant: {holiday['significant']}")
    
    print("\n=== Monsoon Effect ===")
    monsoon = results['monsoon_analysis']['best_estimate']
    print(f"Estimate: ₹{monsoon['estimate']:,.0f}")
    print(f"95% CI: [₹{monsoon['ci_lower']:,.0f}, ₹{monsoon['ci_upper']:,.0f}]")
    print(f"P-value: {monsoon['p_value']:.4f}")
    print(f"Significant: {monsoon['significant']}")
    
    print(f"\n=== Thesis Answer ===")
    print(results['thesis_rq1_answer'])
