#!/usr/bin/env python3
"""
Supabase Connection Test and Setup Script

Tests the connection to Supabase and initializes the database schema.
"""

import os
import sys
from src.database import (
    is_database_available,
    init_database,
    get_db_connection,
    save_signals_db,
    get_latest_signals
)
from datetime import datetime


def test_connection():
    """Test basic database connection."""
    print("Testing database connection...")
    
    if not is_database_available():
        print("❌ DATABASE_URL environment variable is not set")
        print("\nTo set it, run:")
        print("  export DATABASE_URL='your_supabase_connection_string'")
        print("\nOr add it to your .env file:")
        print("  DATABASE_URL=your_supabase_connection_string")
        return False
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✓ Connected to database successfully")
            print(f"  Database version: {version[:50]}...")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nPlease check:")
        print("  1. Your DATABASE_URL is correct")
        print("  2. Your Supabase database is running")
        print("  3. Your IP is not blocked (check Supabase dashboard)")
        print("  4. Your password is correct")
        return False


def initialize_schema():
    """Initialize the database schema."""
    print("\nInitializing database schema...")
    
    try:
        success = init_database()
        if success:
            print("✓ Database schema initialized successfully")
            return True
        else:
            print("❌ Failed to initialize database schema")
            return False
    except Exception as e:
        print(f"❌ Error initializing schema: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_write_operation():
    """Test writing a signal to the database."""
    print("\nTesting write operation...")
    
    test_signal = [{
        'timestamp': datetime.now().isoformat(),
        'symbol': 'EURUSD',
        'direction': 'LONG',
        'confidence': 0.75,
        'prob_long': 0.75,
        'entry_price': 1.08500,
        'tp_price': 1.09500,
        'sl_price': 1.08000,
        'atr': 0.00500,
        'risk_reward_ratio': 1.8,
    }]
    
    try:
        success = save_signals_db(test_signal)
        if success:
            print("✓ Write operation successful")
            return True
        else:
            print("❌ Write operation failed")
            return False
    except Exception as e:
        print(f"❌ Error writing to database: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_read_operation():
    """Test reading signals from the database."""
    print("\nTesting read operation...")
    
    try:
        signals = get_latest_signals(limit=5)
        if signals:
            print(f"✓ Read operation successful - retrieved {len(signals)} signal(s)")
            print("\nLatest signal:")
            latest = signals[0]
            print(f"  Symbol: {latest['symbol']}")
            print(f"  Direction: {latest['direction']}")
            print(f"  Entry Price: {latest['entry_price']}")
            print(f"  Confidence: {latest['confidence']:.2%}")
            return True
        else:
            print("⚠️  No signals found in database (this is OK if it's a new database)")
            return True
    except Exception as e:
        print(f"❌ Error reading from database: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all connection tests."""
    print("=" * 80)
    print("SUPABASE CONNECTION TEST")
    print("=" * 80)
    
    # Step 1: Test connection
    if not test_connection():
        sys.exit(1)
    
    # Step 2: Initialize schema
    if not initialize_schema():
        sys.exit(1)
    
    # Step 3: Test write operation
    if not test_write_operation():
        sys.exit(1)
    
    # Step 4: Test read operation
    if not test_read_operation():
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED - Supabase connection is working!")
    print("=" * 80)
    print("\nYour database is ready to use.")
    print("You can now run the pipeline to generate and save signals:")
    print("  python run_pipeline.py")
    print("\nOr start the dashboard:")
    print("  python app.py")


if __name__ == "__main__":
    main()

