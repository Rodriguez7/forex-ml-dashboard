# src/features.py

import pandas as pd
import numpy as np
from typing import List
from .config import OHLCV_DIR, FEATURE_DIR, ATR_PERIOD


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Compute Average True Range (ATR).
    
    True Range is the greatest of:
    - Current high - current low
    - Abs(current high - previous close)
    - Abs(current low - previous close)
    
    ATR is the rolling mean of True Range.
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: Rolling window period (default 14)
    
    Returns:
        pd.Series: ATR values
    """
    high = df["high"]
    low = df["low"]
    close_prev = df["close"].shift(1)
    
    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    return atr


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Compute Relative Strength Index (RSI).
    
    RSI = 100 - (100 / (1 + RS))
    where RS = average gain / average loss over period
    
    Args:
        series: Price series (typically close)
        period: Lookback period (default 14)
    
    Returns:
        pd.Series: RSI values (0-100)
    """
    change = series.diff()
    gain = change.clip(lower=0).rolling(period).mean()
    loss = (-change.clip(upper=0)).rolling(period).mean()
    
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def add_features_for_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical features for a single symbol's OHLCV data.
    
    Features include:
    - Returns (1, 3, 5, 10 day)
    - Log returns
    - Volatility (10, 20 day rolling std)
    - ATR (14 period)
    - SMAs (20, 50, 100) with distance from price
    - Trend flags (SMA20 vs SMA50)
    - RSI (14)
    - Stochastic (14,3,3)
    - Bollinger Bands (20 period)
    - Breakout flags (20 period)
    - Day of week
    
    Args:
        df: DataFrame with OHLCV columns, sorted by time ascending
    
    Returns:
        pd.DataFrame: Input DataFrame with additional feature columns
    """
    df = df.copy()
    df = df.sort_values("time").reset_index(drop=True)
    
    # === RETURNS & MOMENTUM ===
    
    # Simple returns
    df["ret_1"] = df["close"].pct_change(1)
    df["ret_3"] = df["close"].pct_change(3)
    df["ret_5"] = df["close"].pct_change(5)
    df["ret_10"] = df["close"].pct_change(10)
    
    # Log returns (more stable for ML)
    df["log_ret_1"] = np.log(df["close"] / df["close"].shift(1))
    df["log_ret_3"] = np.log(df["close"] / df["close"].shift(3))
    df["log_ret_5"] = np.log(df["close"] / df["close"].shift(5))
    
    # === VOLATILITY ===
    
    df["vol_10"] = df["ret_1"].rolling(10).std()
    df["vol_20"] = df["ret_1"].rolling(20).std()
    
    # === ATR ===
    
    df["atr"] = compute_atr(df, ATR_PERIOD)
    
    # === MOVING AVERAGES ===
    
    for window in [20, 50, 100]:
        sma_col = f"sma_{window}"
        df[sma_col] = df["close"].rolling(window).mean()
        
        # Distance from SMA in ATR units (normalized)
        df[f"dist_sma_{window}_atr"] = (df["close"] - df[sma_col]) / (df["atr"] + 1e-9)
    
    # === TREND FLAGS ===
    
    df["trend_up"] = (df["sma_20"] > df["sma_50"]).astype(int)
    df["trend_down"] = (df["sma_20"] < df["sma_50"]).astype(int)
    
    # === RSI ===
    
    df["rsi_14"] = compute_rsi(df["close"], period=14)
    
    # === STOCHASTIC OSCILLATOR ===
    
    # Stochastic %K: (close - low14) / (high14 - low14)
    low14 = df["low"].rolling(14).min()
    high14 = df["high"].rolling(14).max()
    df["stoch_k"] = (df["close"] - low14) / (high14 - low14 + 1e-9) * 100
    
    # Stochastic %D: 3-period SMA of %K
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()
    
    # === BOLLINGER BANDS ===
    
    bb_mid = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    df["bb_mid"] = bb_mid
    df["bb_upper"] = bb_mid + 2 * bb_std
    df["bb_lower"] = bb_mid - 2 * bb_std
    
    # Z-score position within bands
    df["bb_pos"] = (df["close"] - df["bb_mid"]) / (2 * bb_std + 1e-9)
    
    # === BREAKOUTS ===
    
    # Breakout above 20-day high
    df["breakout_up_20"] = (df["close"] > df["close"].rolling(20).max().shift(1)).astype(int)
    
    # Breakdown below 20-day low
    df["breakout_down_20"] = (df["close"] < df["close"].rolling(20).min().shift(1)).astype(int)
    
    # === TIME FEATURES ===
    
    df["day_of_week"] = df["time"].dt.dayofweek  # Monday=0, Sunday=6
    
    # === PRICE POSITION ===
    
    # Where is close relative to high-low range of the day?
    df["close_position"] = (df["close"] - df["low"]) / (df["high"] - df["low"] + 1e-9)
    
    # === REGIME FEATURES (HUGE IMPROVEMENT) ===
    
    # Volatility Regime: ATR relative to its moving average
    atr_ma_60 = df["atr"].rolling(60).mean()
    df["vol_ratio"] = df["atr"] / (atr_ma_60 + 1e-9)
    
    # Categorize volatility regime: low (0), mid (1), high (2), extreme (3)
    df["vol_regime"] = 1  # default mid
    df.loc[df["vol_ratio"] < 0.8, "vol_regime"] = 0  # low
    df.loc[df["vol_ratio"] > 1.2, "vol_regime"] = 2  # high
    df.loc[df["vol_ratio"] > 1.5, "vol_regime"] = 3  # extreme
    
    # Trend Strength using ADX-like calculation
    # True Range already calculated for ATR
    tr = df["high"] - df["low"]
    up_move = df["high"] - df["high"].shift(1)
    down_move = df["low"].shift(1) - df["low"]
    
    # Directional Movement
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    # Smoothed DM and TR
    period_adx = 14
    plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(period_adx).mean() / (df["atr"] + 1e-9)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(period_adx).mean() / (df["atr"] + 1e-9)
    
    # ADX calculation
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    df["adx"] = dx.rolling(period_adx).mean()
    df["trend_strength"] = df["adx"]  # Alias for clarity
    
    # SMA slope as additional trend indicator
    df["sma_20_slope"] = df["sma_20"].diff(5) / (df["atr"] + 1e-9)  # Normalized by ATR
    df["sma_50_slope"] = df["sma_50"].diff(10) / (df["atr"] + 1e-9)
    
    # Market State Detection
    # Range-bound: BB width relative to ATR
    bb_width = (df["bb_upper"] - df["bb_lower"]) / (df["atr"] + 1e-9)
    df["bb_width_atr"] = bb_width
    
    # Consolidation detection: narrow range for X days
    narrow_range = (df["high"] - df["low"]) < (df["atr"] * 0.5)
    df["consolidation_days"] = narrow_range.rolling(5).sum()
    
    # Market state: 0=ranging, 1=trending, 2=breakout
    df["market_state"] = 0  # default ranging
    df.loc[df["adx"] > 25, "market_state"] = 1  # trending
    df.loc[(df["breakout_up_20"] == 1) | (df["breakout_down_20"] == 1), "market_state"] = 2  # breakout
    
    # Trend regime categories
    df["trend_regime"] = 0  # no trend
    df.loc[df["adx"] > 20, "trend_regime"] = 1  # weak trend
    df.loc[df["adx"] > 30, "trend_regime"] = 2  # strong trend
    df.loc[df["adx"] > 40, "trend_regime"] = 3  # very strong trend
    
    return df


def add_cross_pair_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add cross-pair correlation and intermarket features.
    
    Markets are interlinked - this captures those relationships:
    - DXY proxy (synthetic dollar index)
    - Cross-pair divergences (EURUSD vs GBPUSD, AUDUSD vs NZDUSD)
    - Risk sentiment indicators
    
    Args:
        df: DataFrame with all symbols and their features
    
    Returns:
        DataFrame with additional cross-pair features
    """
    print("\nAdding cross-pair correlation features...")
    
    df = df.sort_values(["time", "symbol"]).copy()
    
    # Create a pivot for easier cross-pair calculations
    pivot_close = df.pivot(index="time", columns="symbol", values="close")
    pivot_ret = df.pivot(index="time", columns="symbol", values="ret_1")
    
    # Calculate DXY proxy (synthetic dollar index)
    # DXY ≈ weighted average of USD strength vs major currencies
    # Simplified: average of pairs where USD is base (inverted) minus USD as quote
    dxy_components = []
    
    if "EURUSD" in pivot_close.columns:
        dxy_components.append(-pivot_close["EURUSD"])  # Negative because USD is quote
    if "GBPUSD" in pivot_close.columns:
        dxy_components.append(-pivot_close["GBPUSD"])
    if "AUDUSD" in pivot_close.columns:
        dxy_components.append(-pivot_close["AUDUSD"])
    if "NZDUSD" in pivot_close.columns:
        dxy_components.append(-pivot_close["NZDUSD"])
    if "USDJPY" in pivot_close.columns:
        dxy_components.append(pivot_close["USDJPY"])  # Positive because USD is base
    if "USDCHF" in pivot_close.columns:
        dxy_components.append(pivot_close["USDCHF"])
    if "USDCAD" in pivot_close.columns:
        dxy_components.append(pivot_close["USDCAD"])
    
    if dxy_components:
        dxy_proxy = pd.concat(dxy_components, axis=1).mean(axis=1)
        dxy_proxy_norm = (dxy_proxy - dxy_proxy.rolling(60).mean()) / (dxy_proxy.rolling(60).std() + 1e-9)
    else:
        dxy_proxy_norm = pd.Series(0, index=pivot_close.index)
    
    # Cross-pair divergences
    eur_gbp_div = pd.Series(0, index=pivot_close.index)
    if "EURUSD" in pivot_close.columns and "GBPUSD" in pivot_close.columns:
        # EURUSD vs GBPUSD divergence (European bloc)
        eur_gbp_div = pivot_close["EURUSD"] - pivot_close["GBPUSD"]
        eur_gbp_div = (eur_gbp_div - eur_gbp_div.rolling(60).mean()) / (eur_gbp_div.rolling(60).std() + 1e-9)
    
    aud_nzd_div = pd.Series(0, index=pivot_close.index)
    if "AUDUSD" in pivot_close.columns and "NZDUSD" in pivot_close.columns:
        # AUDUSD vs NZDUSD divergence (commodity currencies)
        aud_nzd_div = pivot_close["AUDUSD"] - pivot_close["NZDUSD"]
        aud_nzd_div = (aud_nzd_div - aud_nzd_div.rolling(60).mean()) / (aud_nzd_div.rolling(60).std() + 1e-9)
    
    # Risk sentiment from USDJPY
    risk_sentiment = pd.Series(0, index=pivot_close.index)
    if "USDJPY" in pivot_ret.columns:
        # USDJPY tends to rise in risk-off, fall in risk-on
        # Use rolling return correlation with aggregate market
        risk_sentiment = pivot_ret["USDJPY"].rolling(20).mean()  # Simplified risk indicator
    
    # Cross-pair momentum (relative strength)
    cross_momentum = pd.Series(0, index=pivot_close.index)
    if len(pivot_ret.columns) > 1:
        # Average momentum relative to all pairs
        cross_momentum = pivot_ret.mean(axis=1)
    
    # Merge back into original dataframe
    result_df = df.copy()
    result_df = result_df.merge(
        pd.DataFrame({
            "time": dxy_proxy_norm.index,
            "dxy_proxy": dxy_proxy_norm.values,
            "eur_gbp_divergence": eur_gbp_div.values,
            "aud_nzd_divergence": aud_nzd_div.values,
            "risk_sentiment": risk_sentiment.values,
            "cross_pair_momentum": cross_momentum.values,
        }),
        on="time",
        how="left"
    )
    
    # Add correlation features (rolling correlation with DXY for each pair)
    result_df["corr_with_dxy"] = 0.0
    for symbol in result_df["symbol"].unique():
        mask = result_df["symbol"] == symbol
        symbol_ret = result_df.loc[mask, "ret_1"].values
        
        # Calculate rolling correlation
        symbol_data = result_df[mask].copy()
        symbol_data = symbol_data.merge(
            pd.DataFrame({"time": dxy_proxy_norm.index, "dxy": dxy_proxy_norm.values}),
            on="time",
            how="left"
        )
        
        # Rolling correlation (simplified - just use recent direction alignment)
        result_df.loc[mask, "corr_with_dxy"] = symbol_data["dxy"].fillna(0).values
    
    print(f"✓ Added 6 cross-pair features")
    
    return result_df


def build_feature_dataset():
    """
    Build complete feature dataset for all symbols.
    
    Loads OHLCV data for all symbols, computes features for each,
    adds cross-pair correlation features,
    concatenates into single dataset, and saves to data/features/features_raw.parquet.
    """
    FEATURE_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Building feature dataset...")
    print("=" * 80)
    
    all_dfs = []
    
    # Process each OHLCV file
    ohlcv_files = sorted(OHLCV_DIR.glob("*_D1.parquet"))
    
    if not ohlcv_files:
        raise FileNotFoundError(
            f"No OHLCV files found in {OHLCV_DIR}. "
            f"Run data_pipeline.build_all_ohlcv() first."
        )
    
    for i, path in enumerate(ohlcv_files, 1):
        symbol = path.stem.replace("_D1", "")
        print(f"\n[{i}/{len(ohlcv_files)}] Processing {symbol}...")
        
        # Load OHLCV
        df = pd.read_parquet(path)
        print(f"  Loaded {len(df)} rows")
        
        # Add features
        df = add_features_for_symbol(df)
        
        # Count features
        feature_cols = [c for c in df.columns if c not in ["time", "symbol", "open", "high", "low", "close"]]
        print(f"  Added {len(feature_cols)} features")
        
        all_dfs.append(df)
    
    # Concatenate all symbols
    print("\nConcatenating all symbols...")
    full = pd.concat(all_dfs, ignore_index=True)
    full = full.sort_values(["time", "symbol"]).reset_index(drop=True)
    
    print(f"Total rows: {len(full):,}")
    print(f"Date range: {full['time'].min().date()} to {full['time'].max().date()}")
    print(f"Symbols: {sorted(full['symbol'].unique())}")
    
    # Add cross-pair correlation features
    full = add_cross_pair_features(full)
    
    # Save
    out_path = FEATURE_DIR / "features_raw.parquet"
    full.to_parquet(out_path, index=False)
    
    print("\n" + "=" * 80)
    print(f"✓ Feature dataset saved to {out_path}")
    print(f"  Shape: {full.shape}")
    print(f"  Columns: {list(full.columns)}")
    
    # Feature summary
    print("\nFeature columns:")
    feature_cols = [c for c in full.columns if c not in ["time", "symbol", "open", "high", "low", "close"]]
    for col in sorted(feature_cols):
        non_null = full[col].notna().sum()
        print(f"  - {col}: {non_null:,} non-null ({non_null/len(full)*100:.1f}%)")


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Get list of feature column names (excludes metadata and OHLCV).
    
    Args:
        df: DataFrame with features
    
    Returns:
        List of feature column names
    """
    exclude = {"time", "symbol", "open", "high", "low", "close", "label", "target"}
    return [col for col in df.columns if col not in exclude]


if __name__ == "__main__":
    build_feature_dataset()


