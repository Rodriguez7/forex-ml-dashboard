#!/usr/bin/env python3
"""
Automated Forex ML Pipeline

Runs the complete pipeline to fetch data, build features, generate labels,
and create trading signals. Designed to run daily via cron.

Usage:
    python run_pipeline.py

Cron schedule (2:15 AM daily):
    15 2 * * * cd /path/to/forex && /usr/bin/python3 run_pipeline.py >> cron.log 2>&1
"""

import subprocess
import datetime
import sys
from pathlib import Path


def run(cmd, description=""):
    """
    Run a shell command and handle errors.
    
    Args:
        cmd: Command to run
        description: Description of the command
    """
    if description:
        print(f"\n{'='*80}")
        print(f"{description}")
        print(f"{'='*80}")
    
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print(result.stdout)
        
        print(f"✓ {description} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error in {description}:")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False


def main():
    """
    Run the complete forex ML pipeline.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 80)
    print("FOREX ML PIPELINE - AUTOMATED RUN")
    print("=" * 80)
    print(f"Started: {timestamp}")
    print("=" * 80)
    
    # Check if we're in the correct directory
    if not Path("src").exists():
        print("✗ Error: src/ directory not found. Are you in the correct directory?")
        sys.exit(1)
    
    # Initialize database if available
    try:
        from src.database import init_database, is_database_available
        if is_database_available():
            print("\n" + "=" * 80)
            print("INITIALIZING DATABASE")
            print("=" * 80)
            init_database()
            print("✓ Database ready for signal storage")
    except Exception as e:
        print(f"⚠️  Database initialization skipped: {e}")
        print("   Signals will be saved to JSON files only")
    
    # Step 1: Fetch fresh FX data from Alpha Vantage
    # This fetches 7 pairs, well within free tier limits (25 calls/day, 5/min)
    success = run(
        "python fetch_data.py",
        "Step 1: Fetching Latest Forex Data (7 pairs)"
    )
    if not success:
        print("\n✗ Pipeline failed at data fetching step")
        sys.exit(1)
    
    # Step 2: Rebuild features with all improvements
    # Includes 45 features: base + regime + cross-pair
    success = run(
        "python build_features.py",
        "Step 2: Building Features (45 features including regime + cross-pair)"
    )
    if not success:
        print("\n✗ Pipeline failed at feature building step")
        sys.exit(1)
    
    # Step 3: Rebuild triple-barrier labels
    # Uses improved volatility-adjusted horizons and dynamic TP/SL
    success = run(
        "python build_labels.py",
        "Step 3: Generating Labels (Volatility-Adjusted Triple-Barrier)"
    )
    if not success:
        print("\n✗ Pipeline failed at labeling step")
        sys.exit(1)
    
    # Step 4: Generate trading signals using optimized model
    # Uses lgbm_optimized model (Optuna-tuned with 100 trials)
    success = run(
        "python generate_signals.py --model lgbm_optimized --confidence 0.5",
        "Step 4: Generating Trading Signals (Optimized Model)"
    )
    if not success:
        print("\n✗ Pipeline failed at signal generation step")
        sys.exit(1)
    
    # Pipeline completed successfully
    end_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "=" * 80)
    print("✓ PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"Started:  {timestamp}")
    print(f"Finished: {end_timestamp}")
    # Check where signals were saved
    try:
        from src.database import is_database_available
        if is_database_available():
            print("\nNew signals have been generated and saved to PostgreSQL database")
        else:
            print("\nNew signals have been generated and saved to data/signals/")
    except:
        print("\nNew signals have been generated and saved to data/signals/")
    
    print("View them at your dashboard URL (or http://localhost:5000 if running locally)")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n✗ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



