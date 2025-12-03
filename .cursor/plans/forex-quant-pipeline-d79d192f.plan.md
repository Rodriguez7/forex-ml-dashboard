<!-- d79d192f-09ee-44c6-a21b-e855ef0ec5e4 8ad7cfb3-0471-42bc-a7ae-60c41d2777f8 -->
# Render Free Tier Deployment Plan

## Overview

Deploy the Forex ML dashboard to Render's free tier with PostgreSQL for signal storage and Git-committed models. The free tier doesn't support persistent disks, so we'll use Render's included PostgreSQL database for signals and commit small model files (68KB) to Git.

## Architecture Changes

1. **PostgreSQL Integration**: Store signals in database instead of JSON files
2. **Git Models**: Commit trained model files to repository (small enough)
3. **Render Configuration**: Set up web service and cron job
4. **Environment Variables**: Configure API keys and database connections
5. **Startup Scripts**: Initialize database schema and load data on first deploy

## Implementation Steps

### 1. Add PostgreSQL Dependencies

**File**: [`requirements.txt`](requirements.txt)

- Add `psycopg2-binary>=2.9.0` for PostgreSQL connection
- Add `gunicorn>=21.2.0` for production WSGI server
- Add `sqlalchemy>=2.0.0` for ORM (optional but cleaner)

### 2. Create Database Schema Module

**File**: [`src/database.py`](src/database.py) (new file)

- Define SQLAlchemy models or raw SQL schema
- Table: `signals` with columns:
  - `id` (primary key, auto-increment)
  - `timestamp` (datetime, indexed)
  - `symbol` (string)
  - `direction` (string: LONG/SHORT)
  - `confidence` (float)
  - `prob_long` (float)
  - `entry_price` (float)
  - `tp_price` (float)
  - `sl_price` (float)
  - `atr` (float)
  - `risk_reward_ratio` (float)
  - `created_at` (datetime, default now)
- Functions:
  - `init_database()` - Create tables if not exist
  - `save_signals_db(signals: List[Dict])` - Insert signals
  - `get_latest_signals(limit: int = 100)` - Query latest signals
  - `get_latest_signal_timestamp()` - Get most recent signal time

### 3. Update Signal Engine for PostgreSQL

**File**: [`src/signal_engine.py`](src/signal_engine.py)

- Modify `save_signals()` function:
  - Add optional parameter `use_database: bool = True`
  - If database available, save to PostgreSQL
  - Fallback to JSON file if database unavailable
- Update `get_latest_signals()` to query from database
- Import database functions from `src/database.py`

### 4. Update Flask App for PostgreSQL

**File**: [`app.py`](app.py)

- Import database functions
- Update `load_latest_signal_file()` → `load_latest_signals_db()`
- Query signals from PostgreSQL instead of JSON files
- Handle database connection errors gracefully
- Add `/health` endpoint that checks database connectivity
- Use Render's `DATABASE_URL` environment variable
- Update route to use database queries

Key changes:

```python
from src.database import get_latest_signals, init_database
import os

DATABASE_URL = os.getenv('DATABASE_URL')  # Render provides this

@app.before_first_request
def init_db():
    init_database()
```

### 5. Update Config for Database

**File**: [`src/config.py`](src/config.py)

- Add `DATABASE_URL` environment variable support
- Add helper function to check if database is available
- Keep JSON file fallback for local development

### 6. Update Pipeline Script for Database

**File**: [`run_pipeline.py`](run_pipeline.py)

- After generating signals, save to PostgreSQL instead of JSON
- Initialize database connection before signal generation
- Handle database errors gracefully

### 7. Render Configuration Files

**File**: [`render.yaml`](render.yaml) (new file)

- Web Service configuration:
  - Build command: `pip install -r requirements.txt`
  - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
  - Environment: Python 3
  - Environment variables: `ALPHA_VANTAGE_API_KEY`
  - Free tier plan
- Cron Job configuration:
  - Schedule: `15 2 * * *` (2:15 AM UTC daily)
  - Same build/start commands
  - Same environment variables
- PostgreSQL Database:
  - Free tier PostgreSQL instance
  - Auto-connects via `DATABASE_URL` env var

**File**: [`Procfile`](Procfile) (alternative, simpler)

- Define web process: `web: gunicorn app:app --bind 0.0.0.0:$PORT`
- Optional: worker process for background tasks

### 8. Update App.py for Render Compatibility

**File**: [`app.py`](app.py)

- Read `PORT` from environment (Render sets this)
- Default to 5000 for local development
- Update startup message
- Add error handling for missing database

### 9. Add Database Initialization Script

**File**: [`init_database.py`](init_database.py) (new file, optional)

- Standalone script to initialize database schema
- Can be run manually or during deployment
- Useful for testing database connection

### 10. Add Models to Git

**Files**: Commit existing model files to repository

- `data/models/lgbm_baseline.pkl`
- `data/models/lgbm_baseline_metadata.pkl`
- `data/models/lgbm_baseline_features.txt`
- `data/models/lgbm_optimized.pkl`
- `data/models/lgbm_optimized_metadata.pkl`
- `data/models/lgbm_optimized_features.txt`

These are small (68KB total) and should be committed to Git so they're available on Render.

### 11. Update .gitignore (if needed)

**File**: [`.gitignore`](.gitignore)

- Keep models directory tracked (or explicitly add `!data/models/*.pkl`)
- Ignore local `.env` files but allow models
- Keep data files ignored (OHLCV, features, etc.) but allow models

### 12. Create Deployment Documentation

**File**: [`RENDER_DEPLOY.md`](RENDER_DEPLOY.md) (new file)

- Step-by-step Render deployment guide
- Environment variable setup instructions
- Database initialization steps
- Troubleshooting section
- Free tier limitations and workarounds

### 13. Update Requirements

**File**: [`requirements.txt`](requirements.txt)

- Add: `psycopg2-binary>=2.9.0`
- Add: `gunicorn>=21.2.0`
- Add: `sqlalchemy>=2.0.0` (optional but recommended)

## Database Schema

```sql
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
);

CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
```

## Key Considerations

1. **Free Tier Limitations**:

   - No persistent disk (data files regenerated from API)
   - PostgreSQL free tier: 90 days retention, 256MB storage
   - Models committed to Git (68KB total)

2. **API Rate Limits**:

   - Alpha Vantage: 25 calls/day, 5/min
   - Pipeline uses 7 calls (one per pair) - safe for daily cron

3. **Startup Time**:

   - Models load from Git (fast)
   - Data can be cached in PostgreSQL or regenerated on-demand
   - First deploy may need manual data fetch

4. **Fallback Strategy**:

   - If database unavailable, fall back to JSON files
   - If models missing, show error message
   - Graceful degradation for missing data

## Testing Plan

1. Test database connection locally using local PostgreSQL
2. Test signal saving and retrieval from database
3. Test Flask app with database backend
4. Test pipeline script with database integration
5. Verify models load correctly from Git
6. Test deployment on Render (staging if possible)

## Success Criteria

- Flask app runs on Render and displays signals from PostgreSQL
- Cron job successfully generates and saves signals daily
- Models load correctly from Git repository
- Database schema initializes automatically
- Graceful error handling for missing data/database
- Free tier resource limits respected

### To-dos

- [ ] Implement LightGBM training with cross-validation
- [ ] Add confidence-based evaluation and metrics
- [ ] Build backtesting engine with equity curves
- [ ] Implement signal generation for production use
- [ ] Create CLI tools for training and backtesting
- [ ] Update documentation for Phase 2
- [ ] Duplicate - already completed in Phase 1
- [ ] Duplicate - already completed in Phase 1
- [ ] Duplicate - already completed in Phase 1
- [ ] Duplicate - already completed in Phase 1
- [ ] Duplicate - already completed in Phase 1
- [ ] Duplicate - already completed in Phase 1
- [ ] Duplicate - already completed in Phase 1
- [ ] Duplicate - already completed in Phase 1
- [ ] Duplicate - completed as diagnostics
- [ ] Duplicate - completed as regime-features
- [ ] Duplicate - completed as improved-labels
- [ ] Duplicate - completed as cross-pair-features
- [ ] Duplicate - completed as optuna-tuning
- [ ] Optional - skipped for Phase 3
- [ ] Optional - analysis only
- [ ] Create model diagnostics notebook and analyze current performance
- [ ] Add volatility and trend regime features
- [ ] Implement volatility-adjusted labeling
- [ ] Add cross-pair correlation and intermarket features
- [ ] Implement Optuna hyperparameter optimization