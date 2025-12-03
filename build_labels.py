#!/usr/bin/env python3
"""
Generate labels using triple-barrier method.

This script applies ATR-based triple-barrier labeling to the feature dataset
and saves the labeled dataset to data/features/features_labeled.parquet.

Usage:
    python build_labels.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.labeling import build_labeled_dataset
from src.config import TP_ATR_MULT, SL_ATR_MULT, MIN_HORIZON_DAYS, MAX_HORIZON_DAYS


def main():
    print("=" * 80)
    print("TRIPLE-BARRIER LABELING")
    print("=" * 80)
    print("\nThis will apply triple-barrier method to label each candle.")
    print("\nParameters:")
    print(f"  Take Profit:  {TP_ATR_MULT}× ATR")
    print(f"  Stop Loss:    {SL_ATR_MULT}× ATR")
    print(f"  Horizon:      {MIN_HORIZON_DAYS}-{MAX_HORIZON_DAYS} days")
    print("\nLabels:")
    print("  +1 = Long wins (TP hit before SL)")
    print("  -1 = Short wins (TP hit before SL)")
    print("   0 = Neutral/ambiguous")
    print("\n" + "=" * 80 + "\n")
    
    try:
        build_labeled_dataset()
        print("\n" + "=" * 80)
        print("✓ Labeling complete!")
        print("\nNext step: Verify dataset with:")
        print("  python -c \"from src.dataset import print_dataset_summary; print_dataset_summary()\"")
        print("\nOr start exploring in Jupyter notebooks!")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure you have run 'python build_features.py' first")
        return 1


if __name__ == "__main__":
    sys.exit(main())




