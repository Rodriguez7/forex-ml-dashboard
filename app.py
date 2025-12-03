# app.py
"""
Flask Web Application for Forex ML Trading Signals Dashboard

Displays the latest ML-generated trading signals in a clean web interface.
Uses Supabase database if available, falls back to JSON files (local development).
"""

import os
from flask import Flask, render_template
import json
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# Path to signals directory (for JSON fallback)
SIGNALS_DIR = Path("data/signals")

# Check if database is available (Render sets DATABASE_URL)
DATABASE_URL = os.getenv('DATABASE_URL')

# Try to import database functions
try:
    from src.database import (
        get_latest_signals as get_latest_signals_db,
        get_signals_grouped_by_timestamp,
        get_latest_signal_timestamp,
        init_database,
        is_database_available
    )
    DB_AVAILABLE = is_database_available()
except ImportError:
    DB_AVAILABLE = False
    print("⚠️  Database module not available - using JSON files only")


# Initialize database on startup if available
if DB_AVAILABLE:
    try:
        init_database()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        DB_AVAILABLE = False


def load_latest_signal_file():
    """
    Load the most recent signal JSON file (fallback method).
    
    Returns:
        Path to latest signal file, or None if no signals exist
    """
    if not SIGNALS_DIR.exists():
        return None
    
    files = sorted(SIGNALS_DIR.glob("signals_*.json"))
    if not files:
        return None
    
    return files[-1]


def load_latest_signals_from_db():
    """
    Load latest signals from Supabase database.
    
    Returns:
        Tuple of (signals list, timestamp string) or (None, None) if unavailable
    """
    if not DB_AVAILABLE:
        return None, None
    
    try:
        # Get signals grouped by timestamp (most recent batch)
        grouped = get_signals_grouped_by_timestamp()
        if not grouped:
            return None, None
        
        # Get the most recent timestamp and its signals
        latest_timestamp_str = max(grouped.keys())
        signals = grouped[latest_timestamp_str]
        
        # Format timestamp for display
        try:
            timestamp_dt = datetime.fromisoformat(latest_timestamp_str.replace('Z', '+00:00'))
            formatted_timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_timestamp = latest_timestamp_str
        
        return signals, formatted_timestamp
        
    except Exception as e:
        print(f"⚠️  Error loading signals from database: {e}")
        return None, None


@app.route("/")
def index():
    """
    Main dashboard route showing latest trading signals.
    """
    # Try database first
    signals, timestamp = load_latest_signals_from_db()
    
    # Fallback to JSON files
    if signals is None:
        latest_file = load_latest_signal_file()
        
        if not latest_file:
            return """
            <html>
            <head><title>Forex ML Signals</title></head>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h2>No signals found.</h2>
                <p>Generate signals by running: <code>python generate_signals.py</code></p>
                <p>Or wait for the automated pipeline to generate signals.</p>
            </body>
            </html>
            """
        
        # Load signals from JSON
        with open(latest_file, 'r') as f:
            signals = json.load(f)
        
        # Extract timestamp from filename (format: signals_YYYYMMDD_HHMMSS.json)
        timestamp = latest_file.stem.replace("signals_", "")
        
        # Format timestamp for display
        try:
            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_timestamp = timestamp
        
        timestamp = formatted_timestamp
    
    return render_template(
        "signals.html",
        signals=signals,
        timestamp=timestamp,
        num_signals=len(signals),
        num_long=sum(1 for s in signals if s['direction'] == 'LONG'),
        num_short=sum(1 for s in signals if s['direction'] == 'SHORT'),
    )


@app.route("/health")
def health():
    """
    Health check endpoint with database status.
    """
    status = {
        "status": "ok",
        "service": "forex-ml-signals",
        "database": "available" if DB_AVAILABLE else "unavailable",
    }
    
    # Check database connectivity if available
    if DB_AVAILABLE:
        try:
            from src.database import get_latest_signal_timestamp
            latest = get_latest_signal_timestamp()
            status["latest_signal"] = latest.isoformat() if latest else None
        except:
            status["database"] = "error"
    
    return status


@app.route("/admin/init-db")
def admin_init_db():
    """
    Admin endpoint to initialize database schema.
    Useful when Shell access is not available (free tier).
    """
    if not DB_AVAILABLE:
        return {"status": "error", "message": "Database not available"}, 400
    
    try:
        init_database()
        return {
            "status": "success",
            "message": "Database schema initialized successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to initialize database: {str(e)}"
        }, 500


@app.route("/admin/run-pipeline")
def admin_run_pipeline():
    """
    Admin endpoint to trigger the data pipeline.
    Note: This runs synchronously and may take several minutes.
    For production, use the cron job instead.
    """
    if not DB_AVAILABLE:
        return {"status": "error", "message": "Database not available"}, 400
    
    try:
        import subprocess
        import threading
        
        def run_pipeline():
            subprocess.run(["python", "run_pipeline.py"], check=False)
        
        # Run in background thread to avoid timeout
        thread = threading.Thread(target=run_pipeline)
        thread.daemon = True
        thread.start()
        
        return {
            "status": "started",
            "message": "Pipeline started in background. Check logs for progress."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to start pipeline: {str(e)}"
        }, 500


if __name__ == "__main__":
    # Get PORT from environment (Render sets this) or default to 5001
    PORT = int(os.environ.get('PORT', 5001))
    
    # Run Flask app
    print("=" * 80)
    print("FOREX ML SIGNAL DASHBOARD")
    print("=" * 80)
    print(f"\nStarting Flask web server on port {PORT}...")
    
    if DB_AVAILABLE:
        print("✓ Database: Available (Supabase)")
    else:
        print("⚠️  Database: Unavailable (using JSON files)")
    
    print(f"Dashboard will be available at: http://localhost:{PORT}")
    print("\nPress CTRL+C to stop the server")
    print("=" * 80 + "\n")
    
    app.run(host="0.0.0.0", port=PORT, debug=False)
