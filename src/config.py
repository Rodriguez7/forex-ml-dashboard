# src/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
OHLCV_DIR = DATA_DIR / "ohlcv"
FEATURE_DIR = DATA_DIR / "features"
MODEL_DIR = DATA_DIR / "models"
BACKTEST_DIR = DATA_DIR / "backtests"

# Forex pairs (from_symbol, to_symbol)
FOREX_PAIRS = [
    ("EUR", "USD"),
    ("GBP", "USD"),
    ("USD", "JPY"),
    ("USD", "CHF"),
    ("AUD", "USD"),
    ("USD", "CAD"),
    ("NZD", "USD"),
]

# Timeframe
TIMEFRAME = "1D"

# Labeling parameters (ATR-based triple barrier)
ATR_PERIOD = 14
TP_ATR_MULT = 1.8    # Take profit distance in ATR multiples
SL_ATR_MULT = 1.0    # Stop loss distance in ATR multiples
MIN_HORIZON_DAYS = 3
MAX_HORIZON_DAYS = 10

# Training splits (time-respecting)
VAL_START_DATE = "2020-01-01"
TEST_START_DATE = "2022-01-01"

# Signal generation
CONFIDENCE_THRESHOLD = 0.7  # Probability threshold for high-confidence trades

# Risk management
RISK_PER_TRADE = 0.01       # 1% equity per trade

# Alpha Vantage API configuration
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# Database configuration (PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")  # Render provides this automatically

def is_database_available() -> bool:
    """
    Check if database is available and configured.
    
    Returns:
        True if DATABASE_URL is set, False otherwise
    """
    return DATABASE_URL is not None

# Ensure directories exist
for directory in [RAW_DIR, OHLCV_DIR, FEATURE_DIR, MODEL_DIR, BACKTEST_DIR]:
    directory.mkdir(parents=True, exist_ok=True)




