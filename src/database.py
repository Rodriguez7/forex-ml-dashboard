# src/database.py
"""
Supabase database module for storing and retrieving trading signals.

Handles database connections, schema initialization, and signal CRUD operations.
Supabase is built on PostgreSQL, so we use standard PostgreSQL drivers.
"""

import os
from typing import List, Dict, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import pool
from contextlib import contextmanager


def get_database_url() -> Optional[str]:
    """
    Get database URL from environment variable.
    
    Supports Supabase connection strings (PostgreSQL-compatible).
    Format: postgresql://user:password@host:port/database
    
    Returns:
        Database URL string or None if not set
    """
    return os.getenv('DATABASE_URL')


def is_database_available() -> bool:
    """
    Check if database is available and configured.
    
    Returns:
        True if DATABASE_URL is set, False otherwise
    """
    return get_database_url() is not None


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    
    Yields:
        psycopg2 connection object
    """
    db_url = get_database_url()
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def init_database():
    """
    Initialize database schema if it doesn't exist.
    
    Creates the signals table and indexes.
    """
    if not is_database_available():
        print("⚠️  DATABASE_URL not set - skipping database initialization")
        return False
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create signals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    confidence FLOAT NOT NULL,
                    prob_long FLOAT NOT NULL,
                    entry_price FLOAT NOT NULL,
                    tp_price FLOAT NOT NULL,
                    sl_price FLOAT NOT NULL,
                    atr FLOAT,
                    risk_reward_ratio FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_timestamp 
                ON signals(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_symbol 
                ON signals(symbol)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_created_at 
                ON signals(created_at DESC)
            """)
            
            conn.commit()
            print("✓ Database schema initialized successfully")
            return True
            
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        return False


def save_signals_db(signals: List[Dict]) -> bool:
    """
    Save signals to Supabase database.
    
    Args:
        signals: List of signal dictionaries
    
    Returns:
        True if successful, False otherwise
    """
    if not signals:
        return True
    
    if not is_database_available():
        print("⚠️  DATABASE_URL not set - cannot save to database")
        return False
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Prepare data for bulk insert
            values = []
            for signal in signals:
                # Parse timestamp
                if isinstance(signal.get('timestamp'), str):
                    timestamp = datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00'))
                else:
                    timestamp = signal.get('timestamp', datetime.now())
                
                values.append((
                    timestamp,
                    signal['symbol'],
                    signal['direction'],
                    float(signal['confidence']),
                    float(signal.get('prob_long', 0.0)),
                    float(signal['entry_price']),
                    float(signal['tp_price']),
                    float(signal['sl_price']),
                    float(signal.get('atr', 0.0)) if signal.get('atr') is not None else None,
                    float(signal['risk_reward_ratio']),
                ))
            
            # Bulk insert (simple insert - duplicates allowed for historical tracking)
            execute_values(
                cursor,
                """
                INSERT INTO signals 
                (timestamp, symbol, direction, confidence, prob_long, 
                 entry_price, tp_price, sl_price, atr, risk_reward_ratio)
                VALUES %s
                """,
                values
            )
            
            conn.commit()
            print(f"✓ Saved {len(signals)} signals to database")
            return True
            
    except Exception as e:
        print(f"✗ Error saving signals to database: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_latest_signals(limit: int = 100) -> List[Dict]:
    """
    Get latest signals from database.
    
    Args:
        limit: Maximum number of signals to return
    
    Returns:
        List of signal dictionaries, ordered by timestamp (newest first)
    """
    if not is_database_available():
        return []
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    timestamp, symbol, direction, confidence, prob_long,
                    entry_price, tp_price, sl_price, atr, risk_reward_ratio,
                    created_at
                FROM signals
                ORDER BY timestamp DESC, created_at DESC
                LIMIT %s
            """, (limit,))
            
            rows = cursor.fetchall()
            
            signals = []
            for row in rows:
                signals.append({
                    'timestamp': row[0].isoformat() if row[0] else None,
                    'symbol': row[1],
                    'direction': row[2],
                    'confidence': float(row[3]),
                    'prob_long': float(row[4]),
                    'entry_price': float(row[5]),
                    'tp_price': float(row[6]),
                    'sl_price': float(row[7]),
                    'atr': float(row[8]) if row[8] is not None else None,
                    'risk_reward_ratio': float(row[9]),
                    'created_at': row[10].isoformat() if row[10] else None,
                })
            
            return signals
            
    except Exception as e:
        print(f"✗ Error retrieving signals from database: {e}")
        return []


def get_latest_signal_timestamp() -> Optional[datetime]:
    """
    Get the timestamp of the most recent signal.
    
    Returns:
        Datetime of latest signal, or None if no signals exist
    """
    if not is_database_available():
        return None
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MAX(timestamp) FROM signals
            """)
            
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
            
    except Exception as e:
        print(f"✗ Error getting latest signal timestamp: {e}")
        return None


def get_signals_by_symbol(symbol: str, limit: int = 10) -> List[Dict]:
    """
    Get latest signals for a specific symbol.
    
    Args:
        symbol: Forex pair symbol (e.g., 'EURUSD')
        limit: Maximum number of signals to return
    
    Returns:
        List of signal dictionaries for the symbol
    """
    if not is_database_available():
        return []
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    timestamp, symbol, direction, confidence, prob_long,
                    entry_price, tp_price, sl_price, atr, risk_reward_ratio,
                    created_at
                FROM signals
                WHERE symbol = %s
                ORDER BY timestamp DESC, created_at DESC
                LIMIT %s
            """, (symbol, limit))
            
            rows = cursor.fetchall()
            
            signals = []
            for row in rows:
                signals.append({
                    'timestamp': row[0].isoformat() if row[0] else None,
                    'symbol': row[1],
                    'direction': row[2],
                    'confidence': float(row[3]),
                    'prob_long': float(row[4]),
                    'entry_price': float(row[5]),
                    'tp_price': float(row[6]),
                    'sl_price': float(row[7]),
                    'atr': float(row[8]) if row[8] is not None else None,
                    'risk_reward_ratio': float(row[9]),
                    'created_at': row[10].isoformat() if row[10] else None,
                })
            
            return signals
            
    except Exception as e:
        print(f"✗ Error retrieving signals for {symbol}: {e}")
        return []


def get_signals_grouped_by_timestamp() -> Dict[str, List[Dict]]:
    """
    Get signals grouped by timestamp (most recent batch).
    
    Returns:
        Dictionary mapping timestamp string to list of signals
    """
    if not is_database_available():
        return {}
    
    try:
        # Get the most recent timestamp
        latest_timestamp = get_latest_signal_timestamp()
        if not latest_timestamp:
            return {}
        
        # Get all signals for this timestamp
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    timestamp, symbol, direction, confidence, prob_long,
                    entry_price, tp_price, sl_price, atr, risk_reward_ratio,
                    created_at
                FROM signals
                WHERE timestamp = %s
                ORDER BY symbol
            """, (latest_timestamp,))
            
            rows = cursor.fetchall()
            
            signals = []
            for row in rows:
                signals.append({
                    'timestamp': row[0].isoformat() if row[0] else None,
                    'symbol': row[1],
                    'direction': row[2],
                    'confidence': float(row[3]),
                    'prob_long': float(row[4]),
                    'entry_price': float(row[5]),
                    'tp_price': float(row[6]),
                    'sl_price': float(row[7]),
                    'atr': float(row[8]) if row[8] is not None else None,
                    'risk_reward_ratio': float(row[9]),
                    'created_at': row[10].isoformat() if row[10] else None,
                })
            
            timestamp_str = latest_timestamp.isoformat()
            return {timestamp_str: signals}
            
    except Exception as e:
        print(f"✗ Error retrieving grouped signals: {e}")
        return {}


if __name__ == "__main__":
    # Test database connection and initialization
    print("Testing database connection...")
    
    if not is_database_available():
        print("DATABASE_URL not set. Set it as an environment variable to test.")
    else:
        print("DATABASE_URL found. Initializing database...")
        init_database()
        
        # Test saving a sample signal
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
        
        print("\nTesting signal save...")
        save_signals_db(test_signal)
        
        print("\nTesting signal retrieval...")
        signals = get_latest_signals(limit=5)
        print(f"Retrieved {len(signals)} signals")
        for sig in signals:
            print(f"  - {sig['symbol']} {sig['direction']} @ {sig['entry_price']}")

