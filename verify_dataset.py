#!/usr/bin/env python3
"""
Verify and display dataset summary.

This script prints a comprehensive summary of the labeled dataset
including split sizes, date ranges, and target distributions.

Usage:
    python verify_dataset.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.dataset import print_dataset_summary


def main():
    try:
        print_dataset_summary()
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure you have completed all previous steps:")
        print("  1. python fetch_data.py")
        print("  2. python build_features.py")
        print("  3. python build_labels.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())




