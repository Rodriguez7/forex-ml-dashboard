#!/usr/bin/env python3
"""
Hyperparameter tuning using Optuna.

This script uses Optuna to find optimal LightGBM hyperparameters
that maximize ROC-AUC on the validation set.

Usage:
    python tune_hyperparameters.py [--trials N] [--timeout SECONDS]
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.hyperparameter_tuning import tune_hyperparameters, train_optimized_model


def main():
    parser = argparse.ArgumentParser(description="Tune LightGBM hyperparameters")
    parser.add_argument(
        "--trials",
        type=int,
        default=100,
        help="Number of optimization trials (default: 100)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds (default: None)"
    )
    parser.add_argument(
        "--model-name",
        default="lgbm_optimized",
        help="Name for the optimized model (default: lgbm_optimized)"
    )
    
    args = parser.parse_args()
    
    try:
        # Run optimization
        print(f"Starting hyperparameter optimization with {args.trials} trials...")
        results = tune_hyperparameters(
            n_trials=args.trials,
            timeout=args.timeout
        )
        
        # Train final model
        print("\nTraining final model with best parameters...")
        model, metadata = train_optimized_model(
            results['best_params'],
            model_name=args.model_name
        )
        
        print("\n" + "=" * 80)
        print("✓ Hyperparameter tuning complete!")
        print("\nNext steps:")
        print(f"  1. python run_backtest.py --model {args.model_name}")
        print(f"  2. python generate_signals.py --model {args.model_name}")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during optimization: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())



