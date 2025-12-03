# src/dataset.py

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
from .config import FEATURE_DIR, VAL_START_DATE, TEST_START_DATE


def load_labeled_dataset() -> pd.DataFrame:
    """
    Load the labeled feature dataset.
    
    Returns:
        pd.DataFrame: Labeled dataset
    
    Raises:
        FileNotFoundError: If labeled dataset doesn't exist
    """
    labeled_path = FEATURE_DIR / "features_labeled.parquet"
    if not labeled_path.exists():
        raise FileNotFoundError(
            f"Labeled dataset not found: {labeled_path}. "
            f"Run labeling.build_labeled_dataset() first."
        )
    return pd.read_parquet(labeled_path)


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Get list of feature column names.
    
    Excludes metadata columns: time, symbol, open, high, low, close, label, target
    
    Args:
        df: DataFrame with features
    
    Returns:
        List of feature column names
    """
    exclude = {"time", "symbol", "open", "high", "low", "close", "label", "target"}
    return [col for col in df.columns if col not in exclude]


def prepare_ml_dataset(
    df: pd.DataFrame,
    drop_neutral: bool = True,
    drop_na: bool = True,
) -> pd.DataFrame:
    """
    Prepare dataset for ML training.
    
    Args:
        df: Labeled feature dataset
        drop_neutral: If True, remove rows where label == 0
        drop_na: If True, drop rows with any NaN in feature columns
    
    Returns:
        pd.DataFrame: Cleaned dataset ready for ML
    """
    df = df.copy()
    
    # Filter neutral labels
    if drop_neutral:
        df = df[df["label"] != 0].copy()
        print(f"After dropping neutral labels: {len(df):,} rows")
    
    # Create binary target: 1 = long win, 0 = short win
    df["target"] = (df["label"] == 1).astype(int)
    
    # Drop rows with missing values in features
    if drop_na:
        feature_cols = get_feature_columns(df)
        before = len(df)
        df = df.dropna(subset=feature_cols)
        dropped = before - len(df)
        if dropped > 0:
            print(f"Dropped {dropped:,} rows with NaN in features ({dropped/before*100:.1f}%)")
    
    return df


def split_train_val_test(
    df: pd.DataFrame,
    val_start: str = VAL_START_DATE,
    test_start: str = TEST_START_DATE,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into train/val/test sets using time-based split.
    
    Time-respecting split (NO data leakage):
    - Train: time < val_start
    - Val:   val_start <= time < test_start
    - Test:  time >= test_start
    
    Args:
        df: DataFrame with 'time' column
        val_start: Start date for validation set (inclusive)
        test_start: Start date for test set (inclusive)
    
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    df = df.sort_values("time").reset_index(drop=True)
    
    val_start = pd.to_datetime(val_start)
    test_start = pd.to_datetime(test_start)
    
    train_df = df[df["time"] < val_start].copy()
    val_df = df[(df["time"] >= val_start) & (df["time"] < test_start)].copy()
    test_df = df[df["time"] >= test_start].copy()
    
    print("\nTime-based split:")
    print(f"  Train: {len(train_df):6,} rows  ({train_df['time'].min().date()} to {train_df['time'].max().date()})")
    print(f"  Val:   {len(val_df):6,} rows  ({val_df['time'].min().date()} to {val_df['time'].max().date()})")
    print(f"  Test:  {len(test_df):6,} rows  ({test_df['time'].min().date()} to {test_df['time'].max().date()})")
    
    # Check for data leakage (should never happen with time-based split)
    assert train_df["time"].max() < val_df["time"].min(), "Data leakage: train overlaps with val!"
    assert val_df["time"].max() < test_df["time"].min(), "Data leakage: val overlaps with test!"
    
    return train_df, val_df, test_df


def get_train_val_test_splits(
    df: pd.DataFrame = None,
    val_start: str = VAL_START_DATE,
    test_start: str = TEST_START_DATE,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Get X, y for train, val, and test sets.
    
    Args:
        df: Labeled dataset (loads from disk if not provided)
        val_start: Start date for validation set
        test_start: Start date for test set
    
    Returns:
        Tuple of (X_train, y_train, X_val, y_val, X_test, y_test)
        where X are DataFrames with features only, y are Series with binary targets
    """
    if df is None:
        print("Loading labeled dataset...")
        df = load_labeled_dataset()
    
    print(f"Preparing ML dataset from {len(df):,} rows...")
    df = prepare_ml_dataset(df, drop_neutral=True, drop_na=True)
    
    # Get feature columns
    feature_cols = get_feature_columns(df)
    print(f"Using {len(feature_cols)} features")
    
    # Split by time
    train_df, val_df, test_df = split_train_val_test(df, val_start, test_start)
    
    # Extract X, y
    X_train = train_df[feature_cols]
    y_train = train_df["target"]
    
    X_val = val_df[feature_cols]
    y_val = val_df["target"]
    
    X_test = test_df[feature_cols]
    y_test = test_df["target"]
    
    # Summary
    print("\nTarget distribution:")
    print(f"  Train: {y_train.mean()*100:.1f}% positive (long wins)")
    print(f"  Val:   {y_val.mean()*100:.1f}% positive (long wins)")
    print(f"  Test:  {y_test.mean()*100:.1f}% positive (long wins)")
    
    return X_train, y_train, X_val, y_val, X_test, y_test


def get_dataset_summary(df: pd.DataFrame = None) -> Dict:
    """
    Get summary statistics of the dataset.
    
    Args:
        df: Labeled dataset (loads from disk if not provided)
    
    Returns:
        Dict with summary statistics
    """
    if df is None:
        df = load_labeled_dataset()
    
    # Prepare ML dataset
    ml_df = prepare_ml_dataset(df, drop_neutral=True, drop_na=True)
    
    # Split
    train_df, val_df, test_df = split_train_val_test(ml_df)
    
    feature_cols = get_feature_columns(ml_df)
    
    summary = {
        "total_rows": len(df),
        "ml_ready_rows": len(ml_df),
        "num_features": len(feature_cols),
        "num_symbols": df["symbol"].nunique(),
        "date_range": (df["time"].min().date(), df["time"].max().date()),
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "train_positive_rate": train_df["target"].mean(),
        "val_positive_rate": val_df["target"].mean(),
        "test_positive_rate": test_df["target"].mean(),
        "feature_columns": feature_cols,
    }
    
    return summary


def print_dataset_summary():
    """Print a comprehensive summary of the dataset."""
    print("=" * 80)
    print("DATASET SUMMARY")
    print("=" * 80)
    
    summary = get_dataset_summary()
    
    print(f"\nData Overview:")
    print(f"  Total rows:        {summary['total_rows']:,}")
    print(f"  ML-ready rows:     {summary['ml_ready_rows']:,}")
    print(f"  Number of symbols: {summary['num_symbols']}")
    print(f"  Date range:        {summary['date_range'][0]} to {summary['date_range'][1]}")
    
    print(f"\nFeatures:")
    print(f"  Number of features: {summary['num_features']}")
    
    print(f"\nSplit Sizes:")
    print(f"  Train: {summary['train_size']:6,} rows ({summary['train_size']/summary['ml_ready_rows']*100:5.1f}%)")
    print(f"  Val:   {summary['val_size']:6,} rows ({summary['val_size']/summary['ml_ready_rows']*100:5.1f}%)")
    print(f"  Test:  {summary['test_size']:6,} rows ({summary['test_size']/summary['ml_ready_rows']*100:5.1f}%)")
    
    print(f"\nTarget Distribution (Long Wins %):")
    print(f"  Train: {summary['train_positive_rate']*100:5.1f}%")
    print(f"  Val:   {summary['val_positive_rate']*100:5.1f}%")
    print(f"  Test:  {summary['test_positive_rate']*100:5.1f}%")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print_dataset_summary()




