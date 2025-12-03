# src/data_pipeline.py

import pandas as pd
from pathlib import Path
from typing import Tuple
from .config import FOREX_PAIRS, OHLCV_DIR
from .alpha_vantage_client import AlphaVantageClient


def fx_daily_to_ohlcv(from_symbol: str, to_symbol: str, client: AlphaVantageClient) -> pd.DataFrame:
    """
    Convert Alpha Vantage FX daily JSON to clean OHLCV DataFrame.
    
    Args:
        from_symbol: Base currency (e.g., "EUR")
        to_symbol: Quote currency (e.g., "USD")
        client: AlphaVantageClient instance
    
    Returns:
        pd.DataFrame: Clean OHLCV data with columns:
            - time: datetime
            - symbol: str (e.g., "EURUSD")
            - open: float
            - high: float
            - low: float
            - close: float
    """
    # Fetch raw data
    raw = client.get_fx_daily_raw(from_symbol, to_symbol)
    ts = raw["Time Series FX (Daily)"]
    
    # Parse into records
    records = []
    for date_str, values in ts.items():
        records.append({
            "time": pd.to_datetime(date_str),
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
        })
    
    # Create DataFrame
    df = pd.DataFrame(records)
    
    # Sort by time ascending (oldest first)
    df = df.sort_values("time").reset_index(drop=True)
    
    # Add symbol column
    df["symbol"] = f"{from_symbol}{to_symbol}"
    
    # Reorder columns
    df = df[["time", "symbol", "open", "high", "low", "close"]]
    
    print(f"Parsed {len(df)} days of {from_symbol}/{to_symbol} data "
          f"({df['time'].min().date()} to {df['time'].max().date()})")
    
    return df


def build_all_ohlcv(client: AlphaVantageClient = None):
    """
    Build OHLCV datasets for all configured forex pairs.
    
    Fetches data from Alpha Vantage (or cache) and saves as parquet files
    in data/ohlcv/ directory.
    
    Args:
        client: Optional AlphaVantageClient instance (creates new one if not provided)
    """
    OHLCV_DIR.mkdir(parents=True, exist_ok=True)
    
    if client is None:
        client = AlphaVantageClient()
    
    print(f"Building OHLCV datasets for {len(FOREX_PAIRS)} forex pairs...")
    print("=" * 80)
    
    for i, (from_sym, to_sym) in enumerate(FOREX_PAIRS, 1):
        print(f"\n[{i}/{len(FOREX_PAIRS)}] Processing {from_sym}/{to_sym}...")
        
        try:
            # Convert to OHLCV
            df = fx_daily_to_ohlcv(from_sym, to_sym, client)
            
            # Save as parquet
            out_path = OHLCV_DIR / f"{from_sym}{to_sym}_D1.parquet"
            df.to_parquet(out_path, index=False)
            print(f"✓ Saved to {out_path}")
            
        except Exception as e:
            print(f"✗ Error processing {from_sym}/{to_sym}: {e}")
            continue
    
    print("\n" + "=" * 80)
    print("OHLCV build complete!")
    
    # Summary
    saved_files = list(OHLCV_DIR.glob("*_D1.parquet"))
    print(f"\nSaved {len(saved_files)} OHLCV files:")
    for f in sorted(saved_files):
        df = pd.read_parquet(f)
        print(f"  - {f.name}: {len(df)} rows, {df['time'].min().date()} to {df['time'].max().date()}")


def load_ohlcv(symbol: str) -> pd.DataFrame:
    """
    Load OHLCV data for a specific symbol.
    
    Args:
        symbol: Currency pair symbol (e.g., "EURUSD")
    
    Returns:
        pd.DataFrame: OHLCV data
    
    Raises:
        FileNotFoundError: If OHLCV file doesn't exist
    """
    filepath = OHLCV_DIR / f"{symbol}_D1.parquet"
    if not filepath.exists():
        raise FileNotFoundError(
            f"OHLCV file not found: {filepath}. "
            f"Run build_all_ohlcv() first to fetch data."
        )
    return pd.read_parquet(filepath)


def load_all_ohlcv() -> pd.DataFrame:
    """
    Load and concatenate OHLCV data for all symbols.
    
    Returns:
        pd.DataFrame: Combined OHLCV data for all symbols
    """
    all_dfs = []
    for filepath in sorted(OHLCV_DIR.glob("*_D1.parquet")):
        df = pd.read_parquet(filepath)
        all_dfs.append(df)
    
    if not all_dfs:
        raise FileNotFoundError(
            f"No OHLCV files found in {OHLCV_DIR}. "
            f"Run build_all_ohlcv() first to fetch data."
        )
    
    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.sort_values(["time", "symbol"]).reset_index(drop=True)
    return combined


if __name__ == "__main__":
    build_all_ohlcv()




