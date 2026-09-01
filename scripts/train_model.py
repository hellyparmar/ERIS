#!/usr/bin/env python3
"""
Enterprise Retail Intelligence System v3.0
TRAINING SCRIPT - End-to-End ML Pipeline

This script demonstrates the complete workflow:
1. Data Loading → 2. Feature Engineering → 3. Model Training → 4. Evaluation

Usage:
    python scripts/train_model.py --use-sample
    python scripts/train_model.py --sales-path data/sales.csv --model random_forest
"""

import sys
sys.path.append('src')

import argparse
from ml import MLPipeline


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Train R-DIOS retail forecasting model"
    )
    
    parser.add_argument(
        '--sales-path',
        type=str,
        default=None,
        help='Path to sales CSV file'
    )
    
    parser.add_argument(
        '--inventory-path',
        type=str,
        default=None,
        help='Path to inventory CSV file (optional)'
    )
    
    parser.add_argument(
        '--use-sample',
        action='store_true',
        help='Use synthetic sample data (for testing)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='random_forest',
        choices=['random_forest', 'gradient_boosting'],
        help='Model type to train'
    )
    
    parser.add_argument(
        '--n-estimators',
        type=int,
        default=100,
        help='Number of trees for ensemble models'
    )
    
    parser.add_argument(
        '--max-depth',
        type=int,
        default=10,
        help='Maximum tree depth'
    )
    
    args = parser.parse_args()
    
    # Banner
    print("\n" + "="*80)
    print(" "*25 + "R-DIOS TRAINING PIPELINE")
    print("="*80)
    print(f"Model Type: {args.model}")
    print(f"Use Sample Data: {args.use_sample}")
    if args.sales_path:
        print(f"Sales Data: {args.sales_path}")
    print("="*80)
    
    # Initialize pipeline
    pipeline = MLPipeline(
        data_dir="data",
        model_dir="models",
        random_state=42
    )
    
    # Run full pipeline
    try:
        test_metrics = pipeline.run_full_pipeline(
            sales_path=args.sales_path,
            model_type=args.model,
            use_sample=args.use_sample
        )
        
        # Print final summary
        print("\n" + "="*80)
        print(" "*30 + "TRAINING COMPLETE")
        print("="*80)
        print("\n✅ Model trained and saved successfully!")
        print(f"\n📊 Final Test Metrics:")
        for metric, value in test_metrics.items():
            print(f"   {metric}: {value:.4f}")
        
        # Feature importance
        if args.model == 'random_forest':
            print("\n🔍 Top 10 Most Important Features:")
            importance = pipeline.model.get_feature_importance(top_n=10)
            for idx, row in importance.iterrows():
                print(f"   {idx+1:2d}. {row['feature']:30s} {row['importance']:.4f}")
        
        print("\n" + "="*80)
        print("🎯 Next Steps:")
        print("   1. Review model performance metrics")
        print("   2. Tune hyperparameters if needed")
        print("   3. Deploy model to production")
        print("   4. Integrate with dashboard frontend")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
