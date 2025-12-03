#!/usr/bin/env python3
"""
Train the forex trading model.

This script trains a LightGBM classifier on the labeled dataset,
evaluates performance, and saves the trained model.

Usage:
    python train_model.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models import train_and_evaluate_model


def main():
    print("=" * 80)
    print("FOREX ML MODEL TRAINING")
    print("=" * 80)
    print("\nThis will:")
    print("  1. Load labeled dataset (train/val/test splits)")
    print("  2. Train LightGBM classifier")
    print("  3. Evaluate on all splits")
    print("  4. Analyze probability buckets (confidence filtering)")
    print("  5. Display feature importance")
    print("  6. Save trained model")
    print("\n" + "=" * 80 + "\n")
    
    try:
        # Train model with default parameters
        model, metadata = train_and_evaluate_model(
            params=None,  # Use defaults
            model_name="lgbm_baseline"
        )
        
        print("\n" + "=" * 80)
        print("✓ Model training complete!")
        print("\nNext steps:")
        print("  1. python run_backtest.py    - Run backtest on test set")
        print("  2. python generate_signals.py - Generate trading signals")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during training: {e}")
        print("\nMake sure you have:")
        print("  1. Run the Phase 1 pipeline (fetch_data, build_features, build_labels)")
        print("  2. Installed all dependencies (pip install -r requirements.txt)")
        return 1


if __name__ == "__main__":
    sys.exit(main())




