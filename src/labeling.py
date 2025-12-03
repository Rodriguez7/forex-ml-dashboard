# src/labeling.py

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .config import (
    FEATURE_DIR,
    ATR_PERIOD,
    TP_ATR_MULT,
    SL_ATR_MULT,
    MIN_HORIZON_DAYS,
    MAX_HORIZON_DAYS,
)


def apply_triple_barrier_for_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply IMPROVED triple-barrier labeling method for a single symbol.
    
    Improvements:
    1. Volatility-adjusted horizon (low vol = longer, high vol = shorter)
    2. Dynamic TP/SL based on trend regime
    3. Better label quality for model training
    
    For each candle at index i:
    1. Entry at close[i]
    2. Define TP/SL using ATR-based distances (adaptive):
       - Trending: wider TP (2.5× ATR)
       - Low vol: tighter TP (1.5× ATR)
       - Default: 1.8× ATR
    3. Scan forward with volatility-adjusted horizon
    4. Detect first barrier hit using high/low of each bar
    5. Assign label:
       - +1 if long wins (hits TP before SL)
       - -1 if short wins (hits TP before SL)
       - 0 if ambiguous or no clear winner
    
    Args:
        df: DataFrame with OHLCV, 'atr', 'vol_ratio', 'trend_strength' columns
    
    Returns:
        pd.DataFrame: Input DataFrame with 'label' column added
    """
    df = df.sort_values("time").reset_index(drop=True)
    
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    atr = df["atr"].values
    
    # Get regime features for adaptive labeling
    vol_ratio = df["vol_ratio"].values if "vol_ratio" in df.columns else np.ones(len(df))
    trend_strength = df["trend_strength"].values if "trend_strength" in df.columns else np.zeros(len(df))
    
    n = len(df)
    labels = np.zeros(n, dtype=int)
    
    print(f"  Applying IMPROVED triple-barrier labeling to {n} candles...")
    
    # Process each candle
    for i in range(n):
        # Skip if ATR not available
        if np.isnan(atr[i]) or atr[i] == 0:
            labels[i] = 0
            continue
        
        entry = close[i]
        
        # IMPROVEMENT 1: Dynamic TP/SL based on regime
        # Get current regime
        current_vol_ratio = vol_ratio[i] if not np.isnan(vol_ratio[i]) else 1.0
        current_trend = trend_strength[i] if not np.isnan(trend_strength[i]) else 0.0
        
        # Adjust TP multiplier based on trend strength
        if current_trend > 30:  # Strong trend
            tp_mult = 2.5  # Wider target in trends
        elif current_vol_ratio < 0.8:  # Low volatility
            tp_mult = 1.5  # Tighter in ranges
        else:
            tp_mult = TP_ATR_MULT  # Default 1.8
        
        # SL stays consistent
        sl_mult = SL_ATR_MULT
        
        # Define barriers for long position
        tp_long = entry + tp_mult * atr[i]
        sl_long = entry - sl_mult * atr[i]
        
        # Define barriers for short position
        tp_short = entry - tp_mult * atr[i]
        sl_short = entry + sl_mult * atr[i]
        
        # IMPROVEMENT 2: Volatility-adjusted horizon
        # High volatility = shorter horizon, Low volatility = longer horizon
        if current_vol_ratio > 1.5:  # Extreme volatility
            horizon = max(MIN_HORIZON_DAYS, int(MAX_HORIZON_DAYS * 0.5))
        elif current_vol_ratio > 1.2:  # High volatility
            horizon = max(MIN_HORIZON_DAYS, int(MAX_HORIZON_DAYS * 0.7))
        elif current_vol_ratio < 0.8:  # Low volatility
            horizon = min(int(MAX_HORIZON_DAYS * 1.3), 13)  # Extend slightly
        else:
            horizon = MAX_HORIZON_DAYS
        
        # Define forward-looking window
        start = i + 1
        end = min(i + horizon + 1, n)
        
        if start >= n:
            labels[i] = 0
            continue
        
        # Track first hit for long and short
        hit_long = None  # (bar_idx, "tp" or "sl")
        hit_short = None  # (bar_idx, "tp" or "sl")
        
        # Scan forward bars
        for j in range(start, end):
            # Check long position barriers
            if hit_long is None:
                if high[j] >= tp_long:
                    hit_long = (j, "tp")
                elif low[j] <= sl_long:
                    hit_long = (j, "sl")
            
            # Check short position barriers
            if hit_short is None:
                if low[j] <= tp_short:
                    hit_short = (j, "tp")
                elif high[j] >= sl_short:
                    hit_short = (j, "sl")
            
            # Both hit, can stop scanning
            if hit_long is not None and hit_short is not None:
                break
        
        # Determine label based on outcomes
        if hit_long is None and hit_short is None:
            # Neither hit within horizon
            labels[i] = 0
        else:
            # Calculate outcome scores
            long_outcome = 0
            short_outcome = 0
            
            if hit_long is not None:
                long_outcome = 1 if hit_long[1] == "tp" else -1
            
            if hit_short is not None:
                short_outcome = 1 if hit_short[1] == "tp" else -1
            
            # Assign label based on which side performed better
            if long_outcome > short_outcome:
                labels[i] = 1  # Long wins
            elif short_outcome > long_outcome:
                labels[i] = -1  # Short wins
            else:
                labels[i] = 0  # Ambiguous (both won or both lost)
    
    df["label"] = labels
    
    # Summary statistics
    label_counts = pd.Series(labels).value_counts().sort_index()
    print(f"  Label distribution:")
    for label, count in label_counts.items():
        label_name = {1: "Long", -1: "Short", 0: "Neutral"}.get(label, "Unknown")
        print(f"    {label_name:8s} ({label:+2d}): {count:6,} ({count/n*100:5.1f}%)")
    
    return df


def build_labeled_dataset():
    """
    Build labeled dataset with triple-barrier labels for all symbols.
    
    Loads features_raw.parquet, applies triple-barrier labeling per symbol,
    and saves to features_labeled.parquet.
    """
    print("Building labeled dataset...")
    print("=" * 80)
    
    # Load feature dataset
    features_path = FEATURE_DIR / "features_raw.parquet"
    if not features_path.exists():
        raise FileNotFoundError(
            f"Feature dataset not found: {features_path}. "
            f"Run features.build_feature_dataset() first."
        )
    
    print(f"Loading features from {features_path}...")
    df = pd.read_parquet(features_path)
    print(f"Loaded {len(df):,} rows, {len(df['symbol'].unique())} symbols")
    
    # Check for ATR column
    if "atr" not in df.columns:
        raise ValueError("ATR column not found in features. Cannot compute labels.")
    
    # Apply labeling per symbol
    print("\nApplying triple-barrier labeling per symbol...")
    df = df.sort_values(["symbol", "time"])
    df = df.groupby("symbol", group_keys=False).apply(apply_triple_barrier_for_symbol)
    
    # Overall summary
    print("\n" + "=" * 80)
    print("Overall label distribution:")
    label_counts = df["label"].value_counts().sort_index()
    for label, count in label_counts.items():
        label_name = {1: "Long", -1: "Short", 0: "Neutral"}.get(label, "Unknown")
        print(f"  {label_name:8s} ({label:+2d}): {count:6,} ({count/len(df)*100:5.1f}%)")
    
    # Save labeled dataset
    out_path = FEATURE_DIR / "features_labeled.parquet"
    df.to_parquet(out_path, index=False)
    
    print("\n" + "=" * 80)
    print(f"✓ Labeled dataset saved to {out_path}")
    print(f"  Shape: {df.shape}")
    print(f"  Date range: {df['time'].min().date()} to {df['time'].max().date()}")
    
    # Provide guidance on next steps
    non_neutral = (df["label"] != 0).sum()
    print(f"\n  Non-neutral labels: {non_neutral:,} ({non_neutral/len(df)*100:.1f}%)")
    print(f"  These will be used for model training.")


def get_label_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get detailed label statistics per symbol.
    
    Args:
        df: DataFrame with 'symbol' and 'label' columns
    
    Returns:
        pd.DataFrame: Statistics per symbol
    """
    stats = []
    
    for symbol in sorted(df["symbol"].unique()):
        symbol_df = df[df["symbol"] == symbol]
        labels = symbol_df["label"]
        
        stats.append({
            "symbol": symbol,
            "total": len(labels),
            "long_wins": (labels == 1).sum(),
            "short_wins": (labels == -1).sum(),
            "neutral": (labels == 0).sum(),
            "long_pct": (labels == 1).sum() / len(labels) * 100,
            "short_pct": (labels == -1).sum() / len(labels) * 100,
            "neutral_pct": (labels == 0).sum() / len(labels) * 100,
        })
    
    return pd.DataFrame(stats)


if __name__ == "__main__":
    build_labeled_dataset()


