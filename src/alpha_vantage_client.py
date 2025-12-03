# src/alpha_vantage_client.py

import time
import requests
import json
from pathlib import Path
from typing import Optional
from .config import ALPHA_VANTAGE_API_KEY, ALPHA_VANTAGE_BASE_URL, RAW_DIR


class AlphaVantageClient:
    """
    Client for Alpha Vantage FX API with caching and rate limiting.
    
    Free tier constraints:
    - 25 requests per day
    - 5 requests per minute
    
    All responses are cached to disk to minimize API calls.
    """
    
    def __init__(self, api_key: Optional[str] = None, pause_seconds: float = 15.0):
        """
        Initialize the Alpha Vantage client.
        
        Args:
            api_key: Alpha Vantage API key (defaults to env var)
            pause_seconds: Seconds to pause between API calls (default 15s for safety)
        """
        self.api_key = api_key or ALPHA_VANTAGE_API_KEY
        if not self.api_key:
            raise ValueError(
                "Alpha Vantage API key not found. "
                "Set ALPHA_VANTAGE_API_KEY environment variable or pass api_key parameter."
            )
        self.pause_seconds = pause_seconds
        RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    def get_fx_daily_raw(self, from_symbol: str, to_symbol: str, outputsize: str = "full") -> dict:
        """
        Fetch FX daily data from Alpha Vantage or load from cache.
        
        Args:
            from_symbol: Base currency (e.g., "EUR")
            to_symbol: Quote currency (e.g., "USD")
            outputsize: "compact" (100 datapoints) or "full" (all available history)
        
        Returns:
            dict: Raw JSON response from Alpha Vantage
        
        Raises:
            ValueError: If API response is invalid
            requests.HTTPError: If API request fails
        """
        # Check cache first
        cache_filename = RAW_DIR / f"fx_daily_{from_symbol}{to_symbol}.json"
        if cache_filename.exists():
            print(f"Loading cached data for {from_symbol}/{to_symbol} from {cache_filename}")
            with open(cache_filename, "r") as f:
                return json.load(f)
        
        # Make API call
        print(f"Fetching {from_symbol}/{to_symbol} from Alpha Vantage API...")
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "outputsize": outputsize,
            "apikey": self.api_key,
        }
        
        resp = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # Validate response
        if "Time Series FX (Daily)" not in data:
            error_msg = data.get("Error Message", data.get("Note", str(data)))
            raise ValueError(
                f"Unexpected Alpha Vantage response for {from_symbol}/{to_symbol}: {error_msg}"
            )
        
        # Cache the response
        with open(cache_filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Cached data to {cache_filename}")
        
        # Rate limiting
        print(f"Pausing {self.pause_seconds}s for rate limiting...")
        time.sleep(self.pause_seconds)
        
        return data
    
    def clear_cache(self, from_symbol: Optional[str] = None, to_symbol: Optional[str] = None):
        """
        Clear cached data.
        
        Args:
            from_symbol: If provided, only clear cache for this specific pair
            to_symbol: Required if from_symbol is provided
        """
        if from_symbol and to_symbol:
            cache_file = RAW_DIR / f"fx_daily_{from_symbol}{to_symbol}.json"
            if cache_file.exists():
                cache_file.unlink()
                print(f"Cleared cache for {from_symbol}/{to_symbol}")
        elif from_symbol or to_symbol:
            raise ValueError("Both from_symbol and to_symbol must be provided together")
        else:
            # Clear all cache
            for cache_file in RAW_DIR.glob("fx_daily_*.json"):
                cache_file.unlink()
            print(f"Cleared all cached FX data from {RAW_DIR}")


if __name__ == "__main__":
    # Example usage
    client = AlphaVantageClient()
    data = client.get_fx_daily_raw("EUR", "USD")
    print(f"Fetched {len(data.get('Time Series FX (Daily)', {}))} days of EUR/USD data")




