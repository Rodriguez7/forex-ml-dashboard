#!/usr/bin/env python3
"""
Generate trading signals.

This script loads a trained model and generates trading signals
for all forex pairs based on the latest data.

Usage:
    python generate_signals.py [--model MODEL_NAME] [--confidence THRESHOLD]
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.signal_engine import get_latest_signals, analyze_signal_history
from src.config import CONFIDENCE_THRESHOLD


def main():
    parser = argparse.ArgumentParser(description="Generate trading signals")
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
        "--no-save",
        action="store_true",
        help="Don't save signals to file"
    )
    parser.add_argument(
        "--history",
        type=int,
        help="Analyze signal history over last N days (instead of generating latest)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("FOREX SIGNAL GENERATOR")
    print("=" * 80)
    print(f"\nModel: {args.model}")
    print(f"Confidence threshold: {args.confidence}")
    print("\n" + "=" * 80 + "\n")
    
    try:
        if args.history:
            # Analyze signal history
            signals_df = analyze_signal_history(
                model_name=args.model,
                confidence_threshold=args.confidence,
                days_back=args.history,
            )
            
            if len(signals_df) > 0:
                # Save history
                history_path = f"signal_history_{args.history}days.csv"
                signals_df.to_csv(history_path, index=False)
                print(f"\n✓ Signal history saved to {history_path}")
        else:
            # Generate latest signals
            signals = get_latest_signals(
                model_name=args.model,
                confidence_threshold=args.confidence,
                save_to_file=not args.no_save,
            )
            
            if len(signals) == 0:
                print("\n💡 Tips for getting more signals:")
                print("   - Lower confidence threshold (--confidence 0.6)")
                print("   - Check if data is up to date")
                print("   - Review model performance (python run_backtest.py)")
        
        print("\n" + "=" * 80)
        print("✓ Signal generation complete!")
        print("\n⚠️  DISCLAIMER:")
        print("   Signals are for research purposes only.")
        print("   Always validate signals independently.")
        print("   Use proper risk management.")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error generating signals: {e}")
        print("\nMake sure you have:")
        print("  1. Trained a model (python train_model.py)")
        print("  2. Data is available (python fetch_data.py)")
        return 1


if __name__ == "__main__":
    sys.exit(main())




