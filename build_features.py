#!/usr/bin/env python3
"""
Build feature dataset from OHLCV data.

This script loads OHLCV data, computes technical features,
and saves the feature dataset to data/features/features_raw.parquet.

Usage:
    python build_features.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.features import build_feature_dataset


def main():
    print("=" * 80)
    print("FEATURE BUILDER")
    print("=" * 80)
    print("\nThis will compute technical features from OHLCV data.")
    print("Features include:")
    print("  - Returns & momentum (1, 3, 5, 10 day)")
    print("  - Volatility measures")
    print("  - ATR (Average True Range)")
    print("  - Moving averages (SMA 20, 50, 100)")
    print("  - Trend indicators")
    print("  - RSI, Stochastic, Bollinger Bands")
    print("  - Breakout flags")
    print("  - Time features")
    print("\n" + "=" * 80 + "\n")
    
    try:
        build_feature_dataset()
        print("\n" + "=" * 80)
        print("✓ Feature building complete!")
        print("\nNext step: python build_labels.py")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure you have run 'python fetch_data.py' first")
        return 1


if __name__ == "__main__":
    sys.exit(main())




