# src/backtest.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Tuple, Optional
from pathlib import Path
from .config import BACKTEST_DIR, RISK_PER_TRADE, CONFIDENCE_THRESHOLD
from .models import load_model
from .dataset import load_labeled_dataset


def run_backtest(
    df: pd.DataFrame,
    model,
    feature_columns: list,
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
    risk_per_trade: float = RISK_PER_TRADE,
    initial_capital: float = 10000.0,
) -> Tuple[pd.DataFrame, Dict]:
    """
    Run backtest on labeled dataset with trained model.
    
    Strategy:
    - If prob >= confidence_threshold: take LONG
    - If prob <= (1 - confidence_threshold): take SHORT
    - Otherwise: no trade
    
    Outcome based on labels:
    - Long trade + label=1 (long win): +R
    - Long trade + label=-1 (short win): -R
    - Short trade + label=-1 (short win): +R
    - Short trade + label=1 (long win): -R
    
    Where R = risk_per_trade * equity
    
    Args:
        df: DataFrame with features, labels, time, symbol
        model: Trained model
        feature_columns: List of feature column names
        confidence_threshold: Probability threshold for trades
        risk_per_trade: Risk per trade as fraction of equity
        initial_capital: Starting capital
    
    Returns:
        Tuple of (trades_df, metrics_dict)
    """
    print(f"Running backtest...")
    print(f"  Confidence threshold: {confidence_threshold}")
    print(f"  Risk per trade: {risk_per_trade*100:.1f}%")
    print(f"  Initial capital: ${initial_capital:,.2f}")
    
    # Sort by time
    df = df.sort_values('time').reset_index(drop=True)
    
    # Predict probabilities
    X = df[feature_columns]
    probs = model.predict_proba(X)[:, 1]  # Probability of long win
    
    # Determine signals
    signals = np.zeros(len(df))
    signals[probs >= confidence_threshold] = 1  # Long
    signals[probs <= (1 - confidence_threshold)] = -1  # Short
    
    # Initialize tracking
    trades = []
    equity = initial_capital
    equity_curve = [initial_capital]
    
    for i in range(len(df)):
        signal = signals[i]
        
        if signal == 0:
            equity_curve.append(equity)
            continue
        
        # Trade details
        label = df.iloc[i]['label']
        time = df.iloc[i]['time']
        symbol = df.iloc[i]['symbol']
        prob = probs[i]
        
        # Determine outcome
        if signal == 1:  # Long trade
            win = (label == 1)
        else:  # Short trade
            win = (label == -1)
        
        # Calculate P&L
        risk_amount = equity * risk_per_trade
        
        if win:
            # Assume TP = 1.8 * SL, so R:R = 1.8:1
            pnl = risk_amount * 1.8
        else:
            pnl = -risk_amount
        
        equity += pnl
        equity_curve.append(equity)
        
        # Record trade
        trades.append({
            'time': time,
            'symbol': symbol,
            'signal': 'LONG' if signal == 1 else 'SHORT',
            'prob': prob,
            'label': label,
            'win': win,
            'risk': risk_amount,
            'pnl': pnl,
            'equity': equity,
        })
    
    # Create trades DataFrame
    trades_df = pd.DataFrame(trades)
    
    # Calculate metrics
    if len(trades_df) == 0:
        print("⚠️  No trades generated!")
        return trades_df, {}
    
    metrics = calculate_backtest_metrics(trades_df, equity_curve, initial_capital)
    
    return trades_df, metrics


def calculate_backtest_metrics(
    trades_df: pd.DataFrame,
    equity_curve: list,
    initial_capital: float,
) -> Dict:
    """
    Calculate comprehensive backtest metrics.
    
    Args:
        trades_df: DataFrame with trade results
        equity_curve: List of equity values over time
        initial_capital: Starting capital
    
    Returns:
        Dict with metrics
    """
    n_trades = len(trades_df)
    n_wins = trades_df['win'].sum()
    n_losses = n_trades - n_wins
    
    win_rate = n_wins / n_trades if n_trades > 0 else 0
    
    # Profit/Loss
    total_pnl = trades_df['pnl'].sum()
    total_return = (trades_df['equity'].iloc[-1] - initial_capital) / initial_capital
    
    # Profit factor
    gross_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
    gross_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf
    
    # Average win/loss
    avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if n_wins > 0 else 0
    avg_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].mean()) if n_losses > 0 else 0
    
    # Expectancy (average R)
    avg_r = trades_df['pnl'].mean() / trades_df['risk'].mean() if n_trades > 0 else 0
    
    # Drawdown
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.cummax()
    drawdown = (equity_series - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Sharpe-like metric (simple version)
    returns = equity_series.pct_change().dropna()
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 1 and returns.std() > 0 else 0
    
    metrics = {
        'n_trades': n_trades,
        'n_wins': n_wins,
        'n_losses': n_losses,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'total_return': total_return,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'avg_r': avg_r,
        'max_drawdown': max_drawdown,
        'sharpe': sharpe,
        'final_equity': equity_series.iloc[-1],
    }
    
    return metrics


def print_backtest_results(trades_df: pd.DataFrame, metrics: Dict):
    """Print formatted backtest results."""
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    
    print("\n📊 Trade Statistics:")
    print(f"  Total Trades:    {metrics['n_trades']:,}")
    print(f"  Winning Trades:  {metrics['n_wins']:,}")
    print(f"  Losing Trades:   {metrics['n_losses']:,}")
    print(f"  Win Rate:        {metrics['win_rate']*100:.2f}%")
    
    print("\n💰 Performance:")
    print(f"  Total P&L:       ${metrics['total_pnl']:,.2f}")
    print(f"  Total Return:    {metrics['total_return']*100:+.2f}%")
    print(f"  Profit Factor:   {metrics['profit_factor']:.2f}")
    print(f"  Average Win:     ${metrics['avg_win']:,.2f}")
    print(f"  Average Loss:    ${metrics['avg_loss']:,.2f}")
    print(f"  Average R:       {metrics['avg_r']:+.2f}R")
    
    print("\n📉 Risk Metrics:")
    print(f"  Max Drawdown:    {metrics['max_drawdown']*100:.2f}%")
    print(f"  Sharpe Ratio:    {metrics['sharpe']:.2f}")
    print(f"  Final Equity:    ${metrics['final_equity']:,.2f}")
    
    # Per-symbol breakdown
    if 'symbol' in trades_df.columns:
        print("\n📈 Per-Symbol Breakdown:")
        symbol_stats = trades_df.groupby('symbol').agg({
            'win': ['count', 'sum', 'mean'],
            'pnl': 'sum'
        }).round(4)
        symbol_stats.columns = ['Trades', 'Wins', 'WinRate', 'P&L']
        print(symbol_stats.to_string())


def plot_equity_curve(
    trades_df: pd.DataFrame,
    save_path: Optional[Path] = None,
):
    """
    Plot equity curve over time.
    
    Args:
        trades_df: DataFrame with trade results
        save_path: Optional path to save plot
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Equity curve
    ax = axes[0]
    ax.plot(trades_df['time'], trades_df['equity'], linewidth=1.5)
    ax.set_title('Equity Curve', fontsize=14, fontweight='bold')
    ax.set_ylabel('Equity ($)')
    ax.grid(alpha=0.3)
    ax.axhline(y=trades_df['equity'].iloc[0], color='gray', linestyle='--', alpha=0.5, label='Initial')
    
    # Cumulative returns
    ax = axes[1]
    initial = trades_df['equity'].iloc[0]
    cumulative_return = (trades_df['equity'] - initial) / initial * 100
    ax.plot(trades_df['time'], cumulative_return, linewidth=1.5, color='green')
    ax.fill_between(trades_df['time'], 0, cumulative_return, alpha=0.3, color='green')
    ax.set_title('Cumulative Return', fontsize=14, fontweight='bold')
    ax.set_ylabel('Return (%)')
    ax.set_xlabel('Date')
    ax.grid(alpha=0.3)
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Equity curve saved to {save_path}")
    else:
        plt.show()


def save_backtest_results(
    trades_df: pd.DataFrame,
    metrics: Dict,
    name: str = "baseline",
):
    """
    Save backtest results to disk.
    
    Args:
        trades_df: DataFrame with trade results
        metrics: Dict with metrics
        name: Name for saved results
    """
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save trades
    trades_path = BACKTEST_DIR / f"{name}_trades.parquet"
    trades_df.to_parquet(trades_path, index=False)
    print(f"✓ Trades saved to {trades_path}")
    
    # Save metrics
    metrics_path = BACKTEST_DIR / f"{name}_metrics.csv"
    pd.DataFrame([metrics]).to_csv(metrics_path, index=False)
    print(f"✓ Metrics saved to {metrics_path}")
    
    # Plot equity curve
    plot_path = BACKTEST_DIR / f"{name}_equity_curve.png"
    plot_equity_curve(trades_df, plot_path)


def backtest_with_confidence_levels(
    model_name: str = "lgbm_baseline",
    confidence_levels: list = None,
) -> pd.DataFrame:
    """
    Run backtests at different confidence levels to find optimal threshold.
    
    Args:
        model_name: Name of saved model
        confidence_levels: List of confidence thresholds to test
    
    Returns:
        DataFrame with results for each confidence level
    """
    if confidence_levels is None:
        confidence_levels = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]
    
    print("=" * 80)
    print("CONFIDENCE LEVEL OPTIMIZATION")
    print("=" * 80)
    
    # Load model and test data
    print("\nLoading model and data...")
    model, feature_names, metadata = load_model(model_name)
    
    from .dataset import get_train_val_test_splits
    X_train, y_train, X_val, y_val, X_test, y_test = get_train_val_test_splits()
    
    # Get full labeled dataset for test period
    df_full = load_labeled_dataset()
    df_full = df_full[df_full['label'] != 0].copy()  # Filter neutral
    
    # Split by time to get test set
    from .config import TEST_START_DATE
    test_df = df_full[df_full['time'] >= pd.to_datetime(TEST_START_DATE)].copy()
    
    print(f"Test set: {len(test_df):,} rows")
    
    # Run backtests
    results = []
    
    for conf in confidence_levels:
        print(f"\nTesting confidence threshold: {conf:.2f}")
        trades_df, metrics = run_backtest(
            test_df,
            model,
            feature_names,
            confidence_threshold=conf,
        )
        
        if len(trades_df) > 0:
            results.append({
                'confidence': conf,
                **metrics
            })
    
    results_df = pd.DataFrame(results)
    
    print("\n" + "=" * 80)
    print("CONFIDENCE LEVEL COMPARISON")
    print("=" * 80)
    print(results_df.to_string(index=False))
    
    return results_df


if __name__ == "__main__":
    # Run baseline backtest
    print("Running backtest on test set...")
    
    # Load model
    model, feature_names, metadata = load_model("lgbm_baseline")
    
    # Get test data
    from .dataset import get_train_val_test_splits
    X_train, y_train, X_val, y_val, X_test, y_test = get_train_val_test_splits()
    
    # Get full dataset for test period
    df_full = load_labeled_dataset()
    df_full = df_full[df_full['label'] != 0].copy()
    
    from .config import TEST_START_DATE
    test_df = df_full[df_full['time'] >= pd.to_datetime(TEST_START_DATE)].copy()
    
    # Run backtest
    trades_df, metrics = run_backtest(test_df, model, feature_names)
    
    # Print results
    print_backtest_results(trades_df, metrics)
    
    # Save results
    save_backtest_results(trades_df, metrics, "baseline")




