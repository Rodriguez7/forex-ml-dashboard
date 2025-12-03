#!/usr/bin/env python3
"""
Run backtest on test set.

This script loads a trained model and runs a backtest on the test set,
generating equity curves and performance metrics.

Usage:
    python run_backtest.py [--model MODEL_NAME] [--confidence THRESHOLD]
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.backtest import (
    run_backtest,
    print_backtest_results,
    save_backtest_results,
    backtest_with_confidence_levels,
)
from src.models import load_model
from src.dataset import load_labeled_dataset
from src.config import TEST_START_DATE, CONFIDENCE_THRESHOLD
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Run backtest on test set")
    parser.add_argument(
        "--model",
        default="lgbm_baseline",
        help="Name of trained model (default: lgbm_baseline)"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=CONFIDENCE_THRESHOLD,
        help=f"Confidence threshold (default: {CONFIDENCE_THRESHOLD})"
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Test multiple confidence levels to find optimal"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("FOREX BACKTEST ENGINE")
    print("=" * 80)
    print(f"\nModel: {args.model}")
    print(f"Confidence threshold: {args.confidence}")
    print("\n" + "=" * 80 + "\n")
    
    try:
        if args.optimize:
            # Run optimization across confidence levels
            print("Running confidence level optimization...\n")
            results_df = backtest_with_confidence_levels(
                model_name=args.model,
                confidence_levels=[0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]
            )
            
            # Save optimization results
            results_path = Path("data/backtests") / f"{args.model}_optimization.csv"
            results_df.to_csv(results_path, index=False)
            print(f"\n✓ Optimization results saved to {results_path}")
            
        else:
            # Load model
            print("Loading model...")
            model, feature_names, metadata = load_model(args.model)
            print(f"✓ Model loaded\n")
            
            # Load test data
            print("Loading test data...")
            df_full = load_labeled_dataset()
            df_full = df_full[df_full['label'] != 0].copy()  # Filter neutral
            test_df = df_full[df_full['time'] >= pd.to_datetime(TEST_START_DATE)].copy()
            print(f"✓ Loaded {len(test_df):,} test samples\n")
            
            # Run backtest
            trades_df, metrics = run_backtest(
                test_df,
                model,
                feature_names,
                confidence_threshold=args.confidence,
            )
            
            # Print results
            print_backtest_results(trades_df, metrics)
            
            # Save results
            save_name = f"{args.model}_conf{int(args.confidence*100)}"
            save_backtest_results(trades_df, metrics, save_name)
        
        print("\n" + "=" * 80)
        print("✓ Backtest complete!")
        print("\nNext step: python generate_signals.py")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during backtest: {e}")
        print("\nMake sure you have:")
        print("  1. Trained a model (python train_model.py)")
        print("  2. Run the Phase 1 pipeline")
        return 1


if __name__ == "__main__":
    sys.exit(main())




