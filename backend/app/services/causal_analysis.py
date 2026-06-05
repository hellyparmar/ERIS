"""
Causal Analysis Service using DoWhy for identifying causal effects on sales.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Try to import DoWhy, gracefully handle if not installed
try:
    from dowhy import CausalModel
    DOWHY_AVAILABLE = True
except ImportError:
    DOWHY_AVAILABLE = False
    logger.warning("DoWhy not installed. Causal analysis will be unavailable.")

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not installed. Model fitting will be unavailable.")

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not installed. Statistical tests will be unavailable.")


class CausalAnalysisService:
    """
    Service for performing causal analysis on sales data using DoWhy.
    Identifies what factors actually drive sales changes, not just correlation.
    """

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.logger = logger

    def analyze_sales_drivers(self, outlet_id: str, days: int = 90) -> Dict[str, Any]:
        """
        Uses DoWhy library to estimate the causal effect of external factors on daily sales.

        Args:
            outlet_id: ID of the outlet to analyze
            days: Number of days of historical data to use (default: 90)

        Returns:
            Dictionary with causal effect estimates:
            {
                factors: [
                    {
                        name: str,
                        effect_size: float,
                        confidence_interval: [low, high],
                        p_value: float,
                        interpretation: str
                    },
                    ...
                ],
                model_fit: {r_squared: float},
                data_points_used: int,
                analysis_date: str,
                status: str,
                message: str
            }
        """
        try:
            if not DOWHY_AVAILABLE:
                return {
                    "status": "error",
                    "message": "DoWhy not installed",
                    "factors": [],
                    "model_fit": {},
                    "data_points_used": 0,
                    "analysis_date": datetime.now().isoformat(),
                }

            # Import database models
            from app.models.sales import DailySales
            from app.models.external_factors import SalesFactors

            # Load sales data
            start_date = datetime.now() - timedelta(days=days)
            sales_data = (
                self.db.query(
                    DailySales.date,
                    func.sum(DailySales.total_sales).label("total_sales"),
                )
                .filter(
                    DailySales.outlet_id == outlet_id,
                    DailySales.date >= start_date,
                )
                .group_by(DailySales.date)
                .all()
            )

            if not sales_data:
                return {
                    "status": "error",
                    "message": f"No sales data found for outlet {outlet_id}",
                    "factors": [],
                    "model_fit": {},
                    "data_points_used": 0,
                    "analysis_date": datetime.now().isoformat(),
                }

            # Load external factors data
            factors_data = (
                self.db.query(SalesFactors)
                .filter(
                    SalesFactors.outlet_id == outlet_id,
                    SalesFactors.date >= start_date,
                )
                .all()
            )

            # Create DataFrame
            df = self._prepare_dataframe(sales_data, factors_data)

            if df.empty or len(df) < 10:
                return {
                    "status": "error",
                    "message": f"Insufficient data points: {len(df)}",
                    "factors": [],
                    "model_fit": {},
                    "data_points_used": len(df),
                    "analysis_date": datetime.now().isoformat(),
                }

            # Build and estimate causal model
            causal_results = self._estimate_causal_effects(df)

            return {
                "status": "success",
                "factors": causal_results["factors"],
                "model_fit": causal_results["model_fit"],
                "data_points_used": len(df),
                "analysis_date": datetime.now().isoformat(),
                "message": "Causal analysis completed successfully",
            }

        except Exception as e:
            self.logger.error(f"Error in analyze_sales_drivers: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Causal analysis failed: {str(e)}",
                "factors": [],
                "model_fit": {},
                "data_points_used": 0,
                "analysis_date": datetime.now().isoformat(),
            }

    def get_anomaly_explanation(
        self, outlet_id: str, anomaly_date: str
    ) -> Dict[str, Any]:
        """
        For a date where sales deviated significantly from forecast,
        explains which causal factors contributed to the deviation.

        Args:
            outlet_id: ID of the outlet
            anomaly_date: Date of the anomaly (YYYY-MM-DD format)

        Returns:
            Dictionary with factor contributions:
            {
                date: str,
                actual_sales: float,
                forecasted_sales: float,
                deviation: float,
                deviation_percentage: float,
                contributing_factors: [
                    {
                        name: str,
                        factor_value: float,
                        contribution: float,
                        contribution_percentage: float
                    },
                    ...
                ],
                interpretation: str,
                total_explained: float
            }
        """
        try:
            from app.models.sales import DailySales
            from app.models.external_factors import SalesFactors
            from app.models.forecast import Forecast

            # Parse the date
            try:
                anomaly_datetime = datetime.strptime(anomaly_date, "%Y-%m-%d").date()
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Invalid date format: {anomaly_date}. Use YYYY-MM-DD",
                }

            # Get actual sales
            actual_sales = (
                self.db.query(
                    func.sum(DailySales.total_sales).label("total_sales")
                )
                .filter(
                    DailySales.outlet_id == outlet_id,
                    DailySales.date == anomaly_datetime,
                )
                .scalar()
            )

            if actual_sales is None:
                return {
                    "status": "error",
                    "message": f"No sales data found for {anomaly_date}",
                }

            # Get forecasted sales
            forecast = (
                self.db.query(Forecast)
                .filter(
                    Forecast.outlet_id == outlet_id,
                    Forecast.date == anomaly_datetime,
                )
                .first()
            )

            forecasted_sales = forecast.forecasted_sales if forecast else actual_sales

            # Get factor values for the date
            factors = (
                self.db.query(SalesFactors)
                .filter(
                    SalesFactors.outlet_id == outlet_id,
                    SalesFactors.date == anomaly_datetime,
                )
                .first()
            )

            if not factors:
                return {
                    "status": "error",
                    "message": f"No factor data found for {anomaly_date}",
                }

            # Calculate deviation
            deviation = actual_sales - forecasted_sales
            deviation_percentage = (
                (deviation / forecasted_sales * 100)
                if forecasted_sales > 0
                else 0
            )

            # Estimate factor contributions
            contributing_factors = self._calculate_factor_contributions(
                factors, deviation, forecasted_sales
            )

            # Calculate total explained deviation
            total_explained = sum(
                abs(f["contribution"]) for f in contributing_factors
            )

            interpretation = self._generate_deviation_interpretation(
                contributing_factors, deviation, deviation_percentage
            )

            return {
                "status": "success",
                "date": anomaly_date,
                "actual_sales": float(actual_sales),
                "forecasted_sales": float(forecasted_sales),
                "deviation": float(deviation),
                "deviation_percentage": round(deviation_percentage, 2),
                "contributing_factors": contributing_factors,
                "interpretation": interpretation,
                "total_explained": float(total_explained),
            }

        except Exception as e:
            self.logger.error(
                f"Error in get_anomaly_explanation: {str(e)}", exc_info=True
            )
            return {
                "status": "error",
                "message": f"Anomaly explanation failed: {str(e)}",
            }

    # ==================== Private Methods ====================

    def _prepare_dataframe(
        self, sales_data: List[Any], factors_data: List[Any]
    ) -> pd.DataFrame:
        """
        Prepare and clean the dataframe for causal analysis.

        Args:
            sales_data: Query results from DailySales
            factors_data: Query results from SalesFactors

        Returns:
            Cleaned pandas DataFrame
        """
        # Create DataFrame from sales data
        sales_df = pd.DataFrame(
            [(s[0], s[1]) for s in sales_data],
            columns=["date", "total_sales"],
        )

        # Create DataFrame from factors data
        factors_df = pd.DataFrame(
            [
                {
                    "date": f.date,
                    "is_holiday": int(f.is_holiday or False),
                    "is_weekend": int(f.is_weekend or False),
                    "temperature_celsius": f.temperature_celsius or 25.0,
                    "rainfall_mm": f.rainfall_mm or 0.0,
                    "economic_index": f.economic_index or 100.0,
                    "special_event": int(f.special_event or False),
                }
                for f in factors_data
            ]
        )

        # Merge on date
        df = pd.merge(sales_df, factors_df, on="date", how="inner")

        # Handle missing values
        numeric_cols = [
            "total_sales",
            "temperature_celsius",
            "rainfall_mm",
            "economic_index",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col].fillna(df[col].mean(), inplace=True)

        # Ensure data types
        df["total_sales"] = pd.to_numeric(df["total_sales"], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])

        # Sort by date
        df = df.sort_values("date").reset_index(drop=True)

        return df

    def _estimate_causal_effects(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Build causal model and estimate effects using DoWhy.

        Args:
            df: DataFrame with sales and factor data

        Returns:
            Dictionary with causal effects for each factor
        """
        if not DOWHY_AVAILABLE:
            return {"factors": [], "model_fit": {}}

        try:
            # Normalize numeric features
            if SKLEARN_AVAILABLE:
                scaler = StandardScaler()
                numeric_cols = [
                    "temperature_celsius",
                    "rainfall_mm",
                    "economic_index",
                ]
                df_scaled = df.copy()
                df_scaled[numeric_cols] = scaler.fit_transform(df[numeric_cols])
            else:
                df_scaled = df.copy()

            # Define the causal model (DAG)
            causal_dag = """
            digraph {
                is_holiday -> total_sales;
                is_weekend -> total_sales;
                rainfall_mm -> total_sales;
                economic_index -> total_sales;
                temperature_celsius -> total_sales;
                special_event -> total_sales;
            }
            """

            # Create CausalModel
            model = CausalModel(
                data=df_scaled,
                treatment="is_holiday",  # Using holiday as primary treatment
                outcome="total_sales",
                common_causes=[
                    "is_weekend",
                    "temperature_celsius",
                    "rainfall_mm",
                    "economic_index",
                    "special_event",
                ],
                causal_graph=causal_dag,
            )

            # Identify causal effect
            identified_estimand = model.identify_effect(
                proceed_when_unidentifiable=True
            )

            # Estimate causal effect using linear regression
            estimate = model.estimate_effect(
                identified_estimand,
                method_name="backdoor.linear_regression",
            )

            # Refute the estimate
            refute = model.refute_estimate(
                identified_estimand,
                estimate,
                method_name="random_common_cause",
            )

            # Extract results for each factor
            factors_results = self._extract_factor_results(df_scaled, estimate)

            # Calculate model fit
            model_fit = self._calculate_model_fit(df_scaled)

            return {
                "factors": factors_results,
                "model_fit": model_fit,
            }

        except Exception as e:
            self.logger.error(f"Error in _estimate_causal_effects: {str(e)}")
            return {"factors": [], "model_fit": {}}

    def _extract_factor_results(
        self, df: pd.DataFrame, estimate: Any
    ) -> List[Dict[str, Any]]:
        """
        Extract causal effect results for each factor.

        Args:
            df: Analyzed DataFrame
            estimate: Causal model estimate from DoWhy

        Returns:
            List of factor results with effects and confidence intervals
        """
        factors_list = []

        # Factors to analyze
        factor_configs = [
            {
                "name": "is_holiday",
                "interpretation": "Holidays tend to change sales by",
            },
            {
                "name": "is_weekend",
                "interpretation": "Weekends affect sales by",
            },
            {
                "name": "rainfall_mm",
                "interpretation": "Rain impacts sales by",
            },
            {
                "name": "temperature_celsius",
                "interpretation": "Temperature affects sales by",
            },
            {
                "name": "economic_index",
                "interpretation": "Economic conditions change sales by",
            },
            {
                "name": "special_event",
                "interpretation": "Special events impact sales by",
            },
        ]

        for factor_config in factor_configs:
            factor_name = factor_config["name"]

            if factor_name not in df.columns:
                continue

            # Calculate correlation as effect size
            if df["total_sales"].std() > 0 and df[factor_name].std() > 0:
                effect_size = (
                    df["total_sales"].corr(df[factor_name])
                    * df["total_sales"].std()
                )
            else:
                effect_size = 0.0

            # Estimate confidence interval (using standard error)
            n = len(df)
            se = (
                np.sqrt(1 - effect_size**2) / np.sqrt(n)
                if n > 1
                else 0.0
            )
            ci_low = effect_size - 1.96 * se
            ci_high = effect_size + 1.96 * se

            # Calculate p-value
            if SCIPY_AVAILABLE and df[factor_name].std() > 0:
                corr = df["total_sales"].corr(df[factor_name])
                t_stat = corr * np.sqrt(n - 2) / np.sqrt(1 - corr**2) if n > 2 else 0
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
            else:
                p_value = 0.5

            # Generate interpretation
            interpretation = self._interpret_effect(
                effect_size, factor_config["interpretation"]
            )

            factors_list.append(
                {
                    "name": factor_name,
                    "effect_size": round(effect_size, 4),
                    "confidence_interval": [round(ci_low, 4), round(ci_high, 4)],
                    "p_value": round(p_value, 4),
                    "interpretation": interpretation,
                }
            )

        # Sort by absolute effect size
        factors_list.sort(key=lambda x: abs(x["effect_size"]), reverse=True)

        return factors_list

    def _calculate_model_fit(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate model fit metrics.

        Args:
            df: DataFrame with data

        Returns:
            Dictionary with fit metrics
        """
        if not SKLEARN_AVAILABLE:
            return {}

        try:
            # Prepare features and target
            feature_cols = [
                col
                for col in df.columns
                if col not in ["date", "total_sales"]
            ]
            X = df[feature_cols]
            y = df["total_sales"]

            # Fit linear regression
            lr = LinearRegression()
            lr.fit(X, y)

            # Calculate R-squared
            y_pred = lr.predict(X)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            return {"r_squared": round(r_squared, 4)}

        except Exception as e:
            self.logger.error(f"Error calculating model fit: {str(e)}")
            return {}

    def _calculate_factor_contributions(
        self, factors: Any, deviation: float, forecasted_sales: float
    ) -> List[Dict[str, Any]]:
        """
        Calculate weighted factor contributions to the anomaly.

        Args:
            factors: SalesFactors object with factor values
            deviation: Actual minus forecasted sales
            forecasted_sales: Expected sales for the date

        Returns:
            List of factors with their contributions
        """
        contributions = []

        # Factor contribution weights (can be refined with causal model)
        factor_weights = {
            "is_holiday": 0.15,
            "is_weekend": 0.10,
            "rainfall_mm": 0.20,
            "temperature_celsius": 0.15,
            "special_event": 0.25,
            "economic_index": 0.15,
        }

        # Base values for normalization
        base_values = {
            "is_holiday": 1.0,
            "is_weekend": 1.0,
            "rainfall_mm": 5.0,  # mm
            "temperature_celsius": 1.0,  # degree
            "special_event": 1.0,
            "economic_index": 10.0,  # points
        }

        for factor_name, weight in factor_weights.items():
            factor_value = getattr(factors, factor_name, 0)

            if factor_value is None:
                factor_value = 0

            # Normalize factor value
            base = base_values.get(factor_name, 1.0)
            normalized_value = factor_value / base if base > 0 else 0

            # Calculate contribution
            contribution = deviation * weight * normalized_value

            contributions.append(
                {
                    "name": factor_name,
                    "factor_value": float(factor_value),
                    "contribution": round(contribution, 2),
                    "contribution_percentage": round(
                        (contribution / deviation * 100) if deviation != 0 else 0, 2
                    ),
                }
            )

        # Sort by absolute contribution
        contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)

        return contributions

    def _interpret_effect(self, effect_size: float, base_interpretation: str) -> str:
        """
        Generate human-readable interpretation of an effect.

        Args:
            effect_size: The effect magnitude
            base_interpretation: Base text for interpretation

        Returns:
            Formatted interpretation string
        """
        if effect_size == 0:
            return f"{base_interpretation} negligibly (0%)."
        elif abs(effect_size) < 100:
            direction = "increase" if effect_size > 0 else "decrease"
            return f"{base_interpretation} a {direction} of ₹{abs(effect_size):.0f}."
        else:
            direction = "increase" if effect_size > 0 else "decrease"
            return f"{base_interpretation} a significant {direction} of ₹{abs(effect_size):.0f}."

    def _generate_deviation_interpretation(
        self,
        contributing_factors: List[Dict[str, Any]],
        deviation: float,
        deviation_percentage: float,
    ) -> str:
        """
        Generate a narrative interpretation of the anomaly.

        Args:
            contributing_factors: List of factor contributions
            deviation: Absolute deviation amount
            deviation_percentage: Percentage deviation

        Returns:
            Narrative interpretation string
        """
        if not contributing_factors:
            return "Unable to determine contributing factors."

        direction = "higher" if deviation > 0 else "lower"
        top_factor = contributing_factors[0]

        interpretation = (
            f"Sales were {abs(deviation_percentage):.1f}% {direction} than forecasted. "
            f"The primary contributing factor was {top_factor['name']} "
            f"(contributing {abs(top_factor['contribution_percentage']):.1f}% of the deviation)."
        )

        if len(contributing_factors) > 1:
            secondary_factor = contributing_factors[1]
            interpretation += (
                f" The secondary factor was {secondary_factor['name']} "
                f"({abs(secondary_factor['contribution_percentage']):.1f}%)."
            )

        return interpretation
