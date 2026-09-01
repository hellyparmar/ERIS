"""
R-DIOS Forecast Validation Framework - Part 2
Time-Series Cross-Validation, Visualization, and Reporting

Continuation of forecast_validation_framework.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import time
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

# Import from part 1
from forecast_validation_framework import (
    ValidationConfig,
    ModelMetrics,
    ValidationResults,
    ForecastModel,
    ProphetModel,
    ARIMAModel,
    NaiveModel,
    SeasonalNaiveModel,
    MetricsCalculator
)


# ============================================================================
# TIME-SERIES CROSS-VALIDATION
# ============================================================================

class TimeSeriesCrossValidator:
    """
    Time-series cross-validation with proper temporal ordering
    Prevents data leakage by respecting chronological order
    """
    
    def __init__(self, n_splits: int = 5, forecast_horizon: int = 7):
        """
        Initialize cross-validator
        
        Args:
            n_splits: Number of cross-validation folds
            forecast_horizon: Number of days to forecast
        """
        self.n_splits = n_splits
        self.forecast_horizon = forecast_horizon
    
    def split(self, data: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Generate train/test splits respecting temporal order
        
        Args:
            data: DataFrame with 'ds' (date) and 'y' (target) columns
            
        Returns:
            List of (train, test) DataFrame tuples
        """
        data = data.sort_values('ds').reset_index(drop=True)
        n = len(data)
        
        # Calculate minimum training size (need enough data for seasonality)
        min_train_size = max(60, n // (self.n_splits + 1))  # At least 60 days
        
        splits = []
        
        for i in range(self.n_splits):
            # Expanding window: training set grows with each split
            train_end_idx = min_train_size + (i * self.forecast_horizon)
            test_start_idx = train_end_idx
            test_end_idx = min(test_start_idx + self.forecast_horizon, n)
            
            if test_end_idx > n:
                break
            
            train = data.iloc[:train_end_idx].copy()
            test = data.iloc[test_start_idx:test_end_idx].copy()
            
            if len(test) > 0:
                splits.append((train, test))
        
        logger.info(f"Generated {len(splits)} time-series cross-validation splits")
        return splits


# ============================================================================
# VALIDATION ENGINE
# ============================================================================

class ForecastValidationEngine:
    """Main validation engine orchestrating the entire validation process"""
    
    def __init__(self, config: ValidationConfig):
        """
        Initialize validation engine
        
        Args:
            config: Validation configuration
        """
        self.config = config
        self.models: Dict[str, ForecastModel] = {}
        self.results: Optional[ValidationResults] = None
    
    def register_model(self, model: ForecastModel):
        """Register a model for validation"""
        self.models[model.name] = model
        logger.info(f"Registered model: {model.name}")
    
    def load_data(self, data_path: Path) -> pd.DataFrame:
        """
        Load and prepare data for validation
        
        Args:
            data_path: Path to CSV file with columns: date, revenue
            
        Returns:
            Prepared DataFrame with 'ds' and 'y' columns
        """
        logger.info(f"Loading data from {data_path}")
        
        df = pd.read_csv(data_path)
        
        # Standardize column names
        if 'date' in df.columns and 'revenue' in df.columns:
            df = df.rename(columns={'date': 'ds', 'revenue': 'y'})
        
        # Convert date to datetime
        df['ds'] = pd.to_datetime(df['ds'])
        
        # Aggregate by date if multiple stores
        if 'store_id' in df.columns:
            logger.info("Aggregating data across all stores")
            df = df.groupby('ds').agg({'y': 'sum'}).reset_index()
        
        # Sort by date
        df = df.sort_values('ds').reset_index(drop=True)
        
        logger.info(f"Loaded {len(df)} days of data from {df['ds'].min()} to {df['ds'].max()}")
        logger.info(f"Total revenue: ₹{df['y'].sum():,.0f}")
        logger.info(f"Average daily revenue: ₹{df['y'].mean():,.0f}")
        
        return df[['ds', 'y']]
    
    def split_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train/validation/test sets
        
        Args:
            data: Full dataset
            
        Returns:
            Tuple of (train, validation, test) DataFrames
        """
        n = len(data)
        train_size = int(n * self.config.train_ratio)
        val_size = int(n * self.config.validation_ratio)
        
        train = data.iloc[:train_size].copy()
        validation = data.iloc[train_size:train_size + val_size].copy()
        test = data.iloc[train_size + val_size:].copy()
        
        logger.info(f"Data split - Train: {len(train)}, Val: {len(validation)}, Test: {len(test)}")
        
        return train, validation, test
    
    def validate_model(
        self,
        model: ForecastModel,
        train: pd.DataFrame,
        test: pd.DataFrame
    ) -> Tuple[ModelMetrics, pd.DataFrame]:
        """
        Validate a single model
        
        Args:
            model: Model to validate
            train: Training data
            test: Test data
            
        Returns:
            Tuple of (metrics, predictions DataFrame)
        """
        # Train model
        start_time = time.time()
        model.fit(train)
        training_time = time.time() - start_time
        
        # Generate predictions
        start_time = time.time()
        predictions = model.predict(horizon=len(test))
        prediction_time = time.time() - start_time
        
        # Ensure both dataframes have datetime type for ds column
        predictions['ds'] = pd.to_datetime(predictions['ds'])
        test_copy = test.copy()
        test_copy['ds'] = pd.to_datetime(test_copy['ds'])
        
        # Debug: Check date ranges
        logger.debug(f"Predictions date range: {predictions['ds'].min()} to {predictions['ds'].max()}")
        logger.debug(f"Test date range: {test_copy['ds'].min()} to {test_copy['ds'].max()}")
        logger.debug(f"Predictions shape: {predictions.shape}, Test shape: {test_copy.shape}")
        
        # Merge with actual values
        merged = predictions.merge(
            test_copy[['ds', 'y']].rename(columns={'y': 'actual'}),
            on='ds',
            how='inner'
        )
        
        logger.debug(f"Merged shape: {merged.shape}")
        
        # If merge failed, try left join and fill missing actuals
        if len(merged) == 0:
            logger.warning(f"Inner merge failed for {model.name}. Trying left join...")
            merged = predictions.merge(
                test_copy[['ds', 'y']].rename(columns={'y': 'actual'}),
                on='ds',
                how='left'
            )
            
            # If still no matches, use positional alignment as fallback
            if merged['actual'].isnull().all():
                logger.warning(f"Date merge failed completely. Using positional alignment...")
                if len(predictions) == len(test_copy):
                    merged['actual'] = test_copy['y'].values
                else:
                    raise ValueError(f"Cannot align predictions ({len(predictions)}) with test data ({len(test_copy)})")
        
        # Calculate metrics only on non-null values
        valid_mask = ~merged['actual'].isnull() & ~merged['yhat'].isnull()
        valid_data = merged[valid_mask]
        
        if len(valid_data) == 0:
            raise ValueError(f"No valid data points after merge for {model.name}")
        
        # Calculate metrics
        metrics = MetricsCalculator.calculate_all_metrics(
            y_true=valid_data['actual'].values,
            y_pred=valid_data['yhat'].values,
            model_name=model.name,
            training_time=training_time,
            prediction_time=prediction_time
        )
        
        return metrics, merged
    
    def cross_validate(self, data: pd.DataFrame) -> Dict[str, List[ModelMetrics]]:
        """
        Perform time-series cross-validation
        
        Args:
            data: Full dataset
            
        Returns:
            Dictionary mapping model names to list of metrics from each fold
        """
        cv = TimeSeriesCrossValidator(
            n_splits=self.config.n_splits,
            forecast_horizon=self.config.forecast_horizon
        )
        
        splits = cv.split(data)
        cv_results = {name: [] for name in self.models.keys()}
        
        logger.info(f"Starting {self.config.n_splits}-fold cross-validation...")
        
        for fold_idx, (train, test) in enumerate(tqdm(splits, desc="CV Folds")):
            logger.info(f"\nFold {fold_idx + 1}/{len(splits)}")
            logger.info(f"Train: {train['ds'].min()} to {train['ds'].max()} ({len(train)} days)")
            logger.info(f"Test: {test['ds'].min()} to {test['ds'].max()} ({len(test)} days)")
            
            for model_name, model in self.models.items():
                try:
                    metrics, _ = self.validate_model(model, train, test)
                    cv_results[model_name].append(metrics)
                    logger.info(f"  {model_name} - MAPE: {metrics.mape:.2f}%")
                except Exception as e:
                    logger.error(f"  {model_name} failed: {str(e)}")
        
        return cv_results
    
    def run_validation(self, data_path: Path) -> ValidationResults:
        """
        Run complete validation pipeline
        
        Args:
            data_path: Path to data file
            
        Returns:
            ValidationResults object
        """
        logger.info("=" * 80)
        logger.info("STARTING FORECAST VALIDATION")
        logger.info("=" * 80)
        
        # Load data
        data = self.load_data(data_path)
        
        # Split data
        train, validation, test = self.split_data(data)
        
        # Train and evaluate on test set
        logger.info("\n" + "=" * 80)
        logger.info("FINAL MODEL EVALUATION ON TEST SET")
        logger.info("=" * 80)
        
        final_metrics = {}
        final_predictions = {}
        
        for model_name, model in tqdm(self.models.items(), desc="Training models"):
            logger.info(f"\nEvaluating {model_name}...")
            metrics, predictions = self.validate_model(model, train, test)
            final_metrics[model_name] = metrics
            final_predictions[model_name] = predictions
            logger.info(str(metrics))
        
        # Baseline comparison
        baseline_comparison = self._calculate_baseline_comparison(final_metrics)
        
        # Statistical tests
        statistical_tests = self._perform_statistical_tests(final_predictions)
        
        # Error analysis
        error_analysis = self._analyze_errors(final_predictions, test)
        
        # Create results object
        self.results = ValidationResults(
            metrics=final_metrics,
            predictions=final_predictions,
            baseline_comparison=baseline_comparison,
            statistical_tests=statistical_tests,
            error_analysis=error_analysis,
            config=self.config,
            timestamp=pd.Timestamp.now().isoformat()
        )
        
        # Save results
        self._save_results()
        
        # Generate visualizations
        if self.config.save_plots:
            self._generate_visualizations()
        
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION COMPLETE")
        logger.info("=" * 80)
        
        return self.results
    
    def _calculate_baseline_comparison(self, metrics: Dict[str, ModelMetrics]) -> Dict[str, float]:
        """Calculate improvement over baseline"""
        baseline_mape = metrics.get('Naive Baseline', metrics.get('Seasonal Naive'))
        
        if baseline_mape is None:
            return {}
        
        comparisons = {}
        for name, model_metrics in metrics.items():
            if name not in ['Naive Baseline', 'Seasonal Naive']:
                improvement = ((baseline_mape.mape - model_metrics.mape) / baseline_mape.mape) * 100
                comparisons[name] = improvement
        
        return comparisons
    
    def _perform_statistical_tests(self, predictions: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Perform statistical significance tests"""
        from scipy import stats
        
        tests = {}
        
        # Get baseline errors
        baseline_name = 'Naive Baseline' if 'Naive Baseline' in predictions else 'Seasonal Naive'
        if baseline_name not in predictions:
            return tests
        
        baseline_errors = np.abs(
            predictions[baseline_name]['actual'] - predictions[baseline_name]['yhat']
        )
        
        # Compare each model to baseline
        for name, pred_df in predictions.items():
            if name != baseline_name:
                model_errors = np.abs(pred_df['actual'] - pred_df['yhat'])
                
                # Paired t-test
                t_stat, p_value = stats.ttest_rel(baseline_errors, model_errors)
                
                tests[name] = {
                    't_statistic': float(t_stat),
                    'p_value': float(p_value),
                    'significant': p_value < self.config.significance_level,
                    'interpretation': 'Significantly better than baseline' if p_value < 0.05 and t_stat > 0 else 'Not significantly different'
                }
        
        return tests
    
    def _analyze_errors(self, predictions: Dict[str, pd.DataFrame], test: pd.DataFrame) -> Dict[str, Any]:
        """Analyze error patterns"""
        analysis = {}
        
        for name, pred_df in predictions.items():
            errors = pred_df['actual'] - pred_df['yhat']
            pct_errors = (errors / pred_df['actual']) * 100
            
            analysis[name] = {
                'mean_error': float(errors.mean()),
                'std_error': float(errors.std()),
                'mean_pct_error': float(pct_errors.mean()),
                'median_pct_error': float(pct_errors.median()),
                'max_overestimate': float(errors.min()),
                'max_underestimate': float(errors.max()),
                'error_distribution': {
                    'q25': float(pct_errors.quantile(0.25)),
                    'q50': float(pct_errors.quantile(0.50)),
                    'q75': float(pct_errors.quantile(0.75))
                }
            }
        
        return analysis
    
    def _save_results(self):
        """Save validation results"""
        # Save JSON results
        json_path = self.config.output_dir / 'validation_results.json'
        self.results.save(json_path)
        
        # Save predictions CSV
        if self.config.save_predictions:
            for name, pred_df in self.results.predictions.items():
                csv_path = self.config.output_dir / f'predictions_{name.lower().replace(" ", "_")}.csv'
                pred_df.to_csv(csv_path, index=False)
                logger.info(f"Saved predictions to {csv_path}")
        
        # Save summary report
        self._generate_summary_report()
    
    def _generate_summary_report(self):
        """Generate markdown summary report"""
        report_path = self.config.output_dir / 'VALIDATION_REPORT.md'
        
        with open(report_path, 'w') as f:
            f.write("# R-DIOS Forecast Validation Report\n\n")
            f.write(f"**Generated:** {self.results.timestamp}\n\n")
            f.write("---\n\n")
            
            # Configuration
            f.write("## Configuration\n\n")
            f.write(f"- **Forecast Horizon:** {self.config.forecast_horizon} days\n")
            f.write(f"- **Train/Val/Test Split:** {self.config.train_ratio:.0%} / {self.config.validation_ratio:.0%} / {self.config.test_ratio:.0%}\n")
            f.write(f"- **Cross-Validation Folds:** {self.config.n_splits}\n")
            f.write(f"- **Confidence Level:** {self.config.confidence_level:.0%}\n\n")
            
            # Model Performance
            f.write("## Model Performance Summary\n\n")
            f.write("| Model | MAPE | RMSE | MAE | R² | 95% CI |\n")
            f.write("|-------|------|------|-----|----|---------|\n")
            
            for name, metrics in sorted(self.results.metrics.items(), key=lambda x: x[1].mape):
                f.write(f"| {name} | {metrics.mape:.2f}% | ₹{metrics.rmse:,.0f} | ₹{metrics.mae:,.0f} | {metrics.r2:.4f} | [{metrics.mape_ci_lower:.2f}%, {metrics.mape_ci_upper:.2f}%] |\n")
            
            f.write("\n")
            
            # Baseline Comparison
            if self.results.baseline_comparison:
                f.write("## Improvement Over Baseline\n\n")
                for name, improvement in sorted(self.results.baseline_comparison.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- **{name}:** {improvement:+.1f}% improvement\n")
                f.write("\n")
            
            # Statistical Significance
            if self.results.statistical_tests:
                f.write("## Statistical Significance Tests\n\n")
                for name, test in self.results.statistical_tests.items():
                    sig_marker = "✅" if test['significant'] else "❌"
                    f.write(f"- **{name}:** {sig_marker} {test['interpretation']} (p={test['p_value']:.4f})\n")
                f.write("\n")
            
            # Error Analysis
            f.write("## Error Analysis\n\n")
            for name, analysis in self.results.error_analysis.items():
                f.write(f"### {name}\n\n")
                f.write(f"- Mean Error: ₹{analysis['mean_error']:,.0f}\n")
                f.write(f"- Std Dev: ₹{analysis['std_error']:,.0f}\n")
                f.write(f"- Median % Error: {analysis['median_pct_error']:.2f}%\n")
                f.write(f"- Max Overestimate: ₹{abs(analysis['max_overestimate']):,.0f}\n")
                f.write(f"- Max Underestimate: ₹{analysis['max_underestimate']:,.0f}\n\n")
        
        logger.info(f"Saved summary report to {report_path}")
    
    def _generate_visualizations(self):
        """Generate validation visualizations"""
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 6)
        
        # 1. Predicted vs Actual
        self._plot_predictions()
        
        # 2. Error Distribution
        self._plot_error_distribution()
        
        # 3. Model Comparison
        self._plot_model_comparison()
        
        # 4. Residual Analysis
        self._plot_residuals()
    
    def _plot_predictions(self):
        """Plot predicted vs actual values"""
        n_models = len(self.results.predictions)
        fig, axes = plt.subplots(n_models, 1, figsize=(14, 4 * n_models))
        
        if n_models == 1:
            axes = [axes]
        
        for idx, (name, pred_df) in enumerate(self.results.predictions.items()):
            ax = axes[idx]
            
            # Plot actual
            ax.plot(pred_df['ds'], pred_df['actual'], 'o-', label='Actual', linewidth=2, markersize=6)
            
            # Plot predicted
            ax.plot(pred_df['ds'], pred_df['yhat'], 's--', label='Predicted', linewidth=2, markersize=6, alpha=0.7)
            
            # Confidence interval
            if 'yhat_lower' in pred_df.columns:
                ax.fill_between(
                    pred_df['ds'],
                    pred_df['yhat_lower'],
                    pred_df['yhat_upper'],
                    alpha=0.2,
                    label='95% CI'
                )
            
            metrics = self.results.metrics[name]
            ax.set_title(f'{name} - MAPE: {metrics.mape:.2f}%, R²: {metrics.r2:.4f}', fontsize=14, fontweight='bold')
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Revenue (₹)', fontsize=12)
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plot_path = self.config.output_dir / 'predicted_vs_actual.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved plot: {plot_path}")
    
    def _plot_error_distribution(self):
        """Plot error distribution histograms"""
        n_models = len(self.results.predictions)
        fig, axes = plt.subplots(1, n_models, figsize=(5 * n_models, 5))
        
        if n_models == 1:
            axes = [axes]
        
        for idx, (name, pred_df) in enumerate(self.results.predictions.items()):
            ax = axes[idx]
            
            errors = ((pred_df['actual'] - pred_df['yhat']) / pred_df['actual']) * 100
            
            ax.hist(errors, bins=20, edgecolor='black', alpha=0.7)
            ax.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero Error')
            ax.axvline(errors.mean(), color='green', linestyle='--', linewidth=2, label=f'Mean: {errors.mean():.1f}%')
            
            ax.set_title(f'{name}\nError Distribution', fontsize=12, fontweight='bold')
            ax.set_xlabel('Percentage Error (%)', fontsize=10)
            ax.set_ylabel('Frequency', fontsize=10)
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_path = self.config.output_dir / 'error_distribution.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved plot: {plot_path}")
    
    def _plot_model_comparison(self):
        """Plot model comparison bar chart"""
        model_names = list(self.results.metrics.keys())
        mapes = [self.results.metrics[name].mape for name in model_names]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = ['#2ecc71' if mape < 15 else '#f39c12' if mape < 20 else '#e74c3c' for mape in mapes]
        bars = ax.barh(model_names, mapes, color=colors, edgecolor='black', linewidth=1.5)
        
        # Add value labels
        for bar, mape in zip(bars, mapes):
            ax.text(mape + 0.5, bar.get_y() + bar.get_height()/2, f'{mape:.2f}%', 
                   va='center', fontsize=11, fontweight='bold')
        
        ax.set_xlabel('MAPE (%)', fontsize=12, fontweight='bold')
        ax.set_title('Model Comparison - Mean Absolute Percentage Error', fontsize=14, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3)
        
        # Add target line
        ax.axvline(15, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Target (15%)')
        ax.legend()
        
        plt.tight_layout()
        plot_path = self.config.output_dir / 'model_comparison.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved plot: {plot_path}")
    
    def _plot_residuals(self):
        """Plot residual analysis"""
        n_models = len(self.results.predictions)
        fig, axes = plt.subplots(n_models, 2, figsize=(14, 4 * n_models))
        
        if n_models == 1:
            axes = axes.reshape(1, -1)
        
        for idx, (name, pred_df) in enumerate(self.results.predictions.items()):
            # Residuals vs Predicted
            ax1 = axes[idx, 0]
            residuals = pred_df['actual'] - pred_df['yhat']
            ax1.scatter(pred_df['yhat'], residuals, alpha=0.6, s=80)
            ax1.axhline(0, color='red', linestyle='--', linewidth=2)
            ax1.set_xlabel('Predicted Revenue (₹)', fontsize=10)
            ax1.set_ylabel('Residuals (₹)', fontsize=10)
            ax1.set_title(f'{name} - Residuals vs Predicted', fontsize=11, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            # Q-Q Plot
            ax2 = axes[idx, 1]
            from scipy import stats
            stats.probplot(residuals, dist="norm", plot=ax2)
            ax2.set_title(f'{name} - Q-Q Plot', fontsize=11, fontweight='bold')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_path = self.config.output_dir / 'residual_analysis.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved plot: {plot_path}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    # Configuration
    config = ValidationConfig(
        train_ratio=0.70,
        validation_ratio=0.15,
        test_ratio=0.15,
        n_splits=5,
        forecast_horizon=7,
        output_dir=Path('validation_results'),
        save_plots=True,
        save_predictions=True
    )
    
    # Initialize validation engine
    engine = ForecastValidationEngine(config)
    
    # Register models
    engine.register_model(ProphetModel(**config.prophet_params))
    engine.register_model(ARIMAModel(**config.arima_params))
    engine.register_model(NaiveModel())
    engine.register_model(SeasonalNaiveModel(season_length=7))
    
    # Run validation
    data_path = Path('data/validation_dataset.csv')
    results = engine.run_validation(data_path)
    
    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    for name, metrics in sorted(results.metrics.items(), key=lambda x: x[1].mape):
        print(f"\n{metrics}")
    
    print("\n" + "=" * 80)
    print("✅ VALIDATION COMPLETE")
    print("=" * 80)
    print(f"\nResults saved to: {config.output_dir}")


if __name__ == "__main__":
    main()
