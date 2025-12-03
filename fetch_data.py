#!/usr/bin/env python3
"""
Fetch forex data from Alpha Vantage API.

This script fetches daily OHLCV data for all configured forex pairs
and saves them to data/ohlcv/ directory.

Usage:
    python fetch_data.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_pipeline import build_all_ohlcv


def main():
    print("=" * 80)
    print("FOREX DATA FETCHER")
    print("=" * 80)
    print("\nThis will fetch daily OHLCV data for all configured forex pairs.")
    print("Data will be cached in data/raw/ and saved to data/ohlcv/")
    print("\nNote: Cached data will be reused on subsequent runs.")
    print("      Delete data/raw/*.json to force re-fetch from API.")
    print("\n" + "=" * 80 + "\n")
    
    try:
        build_all_ohlcv()
        print("\n" + "=" * 80)
        print("✓ Data fetch complete!")
        print("\nNext step: python build_features.py")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure you have set ALPHA_VANTAGE_API_KEY in .env file")
        return 1


if __name__ == "__main__":
    sys.exit(main())




