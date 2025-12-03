# src/signal_engine.py

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional
from datetime import datetime
from .config import CONFIDENCE_THRESHOLD, FOREX_PAIRS, TP_ATR_MULT, SL_ATR_MULT, DATA_DIR
from .models import load_model
from .features import add_features_for_symbol, add_cross_pair_features
from .data_pipeline import load_all_ohlcv
from .database import save_signals_db, is_database_available


def generate_signals(
    model_name: str = "lgbm_baseline",
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
    use_latest_only: bool = True,
) -> List[Dict]:
    """
    Generate trading signals for all forex pairs.
    
    Args:
        model_name: Name of trained model to use
        confidence_threshold: Minimum probability for signal generation
        use_latest_only: If True, generate signals only for most recent candle
    
    Returns:
        List of signal dictionaries
    """
    print("=" * 80)
    print("SIGNAL GENERATION ENGINE")
    print("=" * 80)
    
    # Load model
    print(f"\nLoading model: {model_name}")
    model, feature_names, metadata = load_model(model_name)
    print(f"✓ Model loaded (trained on {metadata['n_train']:,} samples)")
    
    # Load OHLCV data
    print("\nLoading latest OHLCV data...")
    df = load_all_ohlcv()
    print(f"✓ Loaded {len(df):,} rows across {df['symbol'].nunique()} symbols")
    
    # Add features per symbol
    print("\nComputing features...")
    df = df.groupby('symbol', group_keys=False).apply(add_features_for_symbol)
    
    # Add cross-pair features (Phase 3 improvement)
    df = add_cross_pair_features(df)
    print(f"✓ Features computed (including cross-pair)")
    
    # Generate signals
    signals = []
    
    for symbol in sorted(df['symbol'].unique()):
        symbol_df = df[df['symbol'] == symbol].sort_values('time')
        
        if use_latest_only:
            # Use only the most recent candle
            symbol_df = symbol_df.tail(1)
        
        # Filter out rows with missing features
        symbol_df = symbol_df.dropna(subset=feature_names)
        
        if len(symbol_df) == 0:
            print(f"  ⚠️  {symbol}: No valid data")
            continue
        
        # Predict
        X = symbol_df[feature_names]
        probs = model.predict_proba(X)[:, 1]  # Probability of long win
        
        # Generate signals for each row
        for idx in symbol_df.index:
            row = symbol_df.loc[idx]
            prob = probs[symbol_df.index.get_loc(idx)]
            
            # Determine direction
            if prob >= confidence_threshold:
                direction = "LONG"
                confidence = prob
            elif prob <= (1 - confidence_threshold):
                direction = "SHORT"
                confidence = 1 - prob
            else:
                direction = "NONE"
                confidence = max(prob, 1 - prob)
            
            if direction == "NONE":
                continue
            
            # Calculate TP/SL levels
            close = row['close']
            atr = row['atr']
            
            if pd.isna(atr) or atr == 0:
                continue
            
            if direction == "LONG":
                tp_price = close + TP_ATR_MULT * atr
                sl_price = close - SL_ATR_MULT * atr
            else:  # SHORT
                tp_price = close - TP_ATR_MULT * atr
                sl_price = close + SL_ATR_MULT * atr
            
            # Create signal
            signal = {
                'timestamp': row['time'].isoformat(),
                'symbol': row['symbol'],
                'direction': direction,
                'confidence': float(confidence),
                'prob_long': float(prob),
                'entry_price': float(close),
                'tp_price': float(tp_price),
                'sl_price': float(sl_price),
                'atr': float(atr),
                'risk_reward_ratio': float(TP_ATR_MULT / SL_ATR_MULT),
            }
            
            signals.append(signal)
            
            # Print signal
            print(f"\n  {symbol} - {direction}")
            print(f"    Confidence:  {confidence*100:.1f}%")
            print(f"    Entry:       {close:.5f}")
            print(f"    Take Profit: {tp_price:.5f} ({TP_ATR_MULT}× ATR)")
            print(f"    Stop Loss:   {sl_price:.5f} ({SL_ATR_MULT}× ATR)")
            print(f"    Risk/Reward: 1:{TP_ATR_MULT/SL_ATR_MULT:.1f}")
    
    print("\n" + "=" * 80)
    print(f"✓ Generated {len(signals)} signals")
    print("=" * 80)
    
    return signals


def save_signals(
    signals: List[Dict],
    filepath: str = None,
    use_database: bool = True,
):
    """
    Save signals to database (if available) or JSON file.
    
    Args:
        signals: List of signal dictionaries
        filepath: Optional custom filepath (only used for JSON fallback)
        use_database: If True, try to save to database first
    """
    # Try database first if available
    if use_database and is_database_available():
        if save_signals_db(signals):
            # Also save JSON as backup
            if filepath is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                signals_dir = DATA_DIR / "signals"
                signals_dir.mkdir(parents=True, exist_ok=True)
                filepath = signals_dir / f"signals_{timestamp}.json"
            
            with open(filepath, 'w') as f:
                json.dump(signals, f, indent=2)
            print(f"✓ Signals also saved to {filepath} (backup)")
            return
    
    # Fallback to JSON file
    if filepath is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        signals_dir = DATA_DIR / "signals"
        signals_dir.mkdir(parents=True, exist_ok=True)
        filepath = signals_dir / f"signals_{timestamp}.json"
    
    with open(filepath, 'w') as f:
        json.dump(signals, f, indent=2)
    
    print(f"✓ Signals saved to {filepath}")


def format_signals_report(signals: List[Dict]) -> str:
    """
    Format signals into a human-readable report.
    
    Args:
        signals: List of signal dictionaries
    
    Returns:
        Formatted string report
    """
    if len(signals) == 0:
        return "No signals generated."
    
    report = []
    report.append("=" * 80)
    report.append("TRADING SIGNALS REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Group by direction
    long_signals = [s for s in signals if s['direction'] == 'LONG']
    short_signals = [s for s in signals if s['direction'] == 'SHORT']
    
    report.append(f"Total Signals: {len(signals)}")
    report.append(f"  Long:  {len(long_signals)}")
    report.append(f"  Short: {len(short_signals)}")
    report.append("")
    
    # Detail each signal
    for i, signal in enumerate(signals, 1):
        report.append(f"{i}. {signal['symbol']} - {signal['direction']}")
        report.append(f"   Timestamp:   {signal['timestamp']}")
        report.append(f"   Confidence:  {signal['confidence']*100:.1f}%")
        report.append(f"   Entry:       {signal['entry_price']:.5f}")
        report.append(f"   Take Profit: {signal['tp_price']:.5f}")
        report.append(f"   Stop Loss:   {signal['sl_price']:.5f}")
        report.append(f"   R:R Ratio:   1:{signal['risk_reward_ratio']:.1f}")
        report.append("")
    
    report.append("=" * 80)
    report.append("DISCLAIMER: Signals are for research purposes only.")
    report.append("Always validate signals independently and use proper risk management.")
    report.append("=" * 80)
    
    return "\n".join(report)


def get_latest_signals(
    model_name: str = "lgbm_baseline",
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
    save_to_file: bool = True,
) -> List[Dict]:
    """
    Get latest trading signals and optionally save to file.
    
    Args:
        model_name: Name of trained model
        confidence_threshold: Confidence threshold for signals
        save_to_file: Whether to save signals to JSON file
    
    Returns:
        List of signal dictionaries
    """
    signals = generate_signals(
        model_name=model_name,
        confidence_threshold=confidence_threshold,
        use_latest_only=True,
    )
    
    if len(signals) > 0:
        # Print report
        report = format_signals_report(signals)
        print("\n" + report)
        
        # Save to file
        if save_to_file:
            save_signals(signals)
    else:
        print("\n⚠️  No signals generated.")
        print("   Either all pairs are neutral or data is missing.")
        print("   Try lowering the confidence threshold.")
    
    return signals


def analyze_signal_history(
    model_name: str = "lgbm_baseline",
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
    days_back: int = 30,
) -> pd.DataFrame:
    """
    Analyze signals over recent history.
    
    Useful for understanding signal frequency and distribution.
    
    Args:
        model_name: Name of trained model
        confidence_threshold: Confidence threshold
        days_back: Number of days to analyze
    
    Returns:
        DataFrame with signal history
    """
    print(f"Analyzing signal history (last {days_back} days)...")
    
    # Generate signals for recent history
    signals = generate_signals(
        model_name=model_name,
        confidence_threshold=confidence_threshold,
        use_latest_only=False,
    )
    
    if len(signals) == 0:
        print("No signals in history.")
        return pd.DataFrame()
    
    # Convert to DataFrame
    signals_df = pd.DataFrame(signals)
    signals_df['timestamp'] = pd.to_datetime(signals_df['timestamp'])
    
    # Filter to recent days
    cutoff = signals_df['timestamp'].max() - pd.Timedelta(days=days_back)
    signals_df = signals_df[signals_df['timestamp'] >= cutoff]
    
    print(f"\nSignal Statistics (last {days_back} days):")
    print(f"  Total signals: {len(signals_df)}")
    print(f"  Long signals:  {(signals_df['direction']=='LONG').sum()}")
    print(f"  Short signals: {(signals_df['direction']=='SHORT').sum()}")
    print(f"  Avg confidence: {signals_df['confidence'].mean()*100:.1f}%")
    
    # Per-symbol breakdown
    print("\nPer-symbol breakdown:")
    symbol_counts = signals_df.groupby(['symbol', 'direction']).size().unstack(fill_value=0)
    print(symbol_counts)
    
    return signals_df


if __name__ == "__main__":
    # Generate latest signals
    signals = get_latest_signals()


