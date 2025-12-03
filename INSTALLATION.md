# Installation & Setup Guide

Complete step-by-step guide to set up the Forex Quant Pipeline.

## Prerequisites

- **Python 3.8+** (3.9 or 3.10 recommended)
- **pip** package manager
- **Alpha Vantage API key** (free, instant signup)
- **~500 MB disk space** for data storage
- **Internet connection** for initial data fetch

## Step-by-Step Installation

### 1. Verify Python Version

```bash
python --version
# Should show Python 3.8 or higher
```

If not installed, download from [python.org](https://www.python.org/downloads/)

### 2. Create Virtual Environment (Recommended)

```bash
# Navigate to project directory
cd forex

# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You should see (venv) in your prompt
```

### 3. Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# This installs:
# - pandas, numpy (data manipulation)
# - requests (API calls)
# - python-dotenv (environment variables)
# - pyarrow (parquet files)
# - lightgbm, scikit-learn (ML)
# - matplotlib, seaborn (visualization)
# - jupyter (notebooks)
```

**Expected time**: 2-3 minutes

### 4. Get Alpha Vantage API Key

1. Visit: https://www.alphavantage.co/support/#api-key
2. Enter your email
3. Click "GET FREE API KEY"
4. Copy your API key (looks like: `ABC123XYZ456...`)

**Free tier limits**:
- 25 API calls per day
- 5 API calls per minute
- Sufficient for this project (data is cached!)

### 5. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite editor
# On macOS/Linux:
nano .env

# On Windows:
notepad .env
```

Replace `your_api_key_here` with your actual API key:

```
ALPHA_VANTAGE_API_KEY=ABC123XYZ456
```

Save and close the file.

### 6. Verify Installation

```bash
# Test Python imports
python -c "import pandas; import numpy; import lightgbm; print('✓ All imports successful')"

# Test config loading
python -c "from src.config import FOREX_PAIRS; print(f'✓ Config loaded, {len(FOREX_PAIRS)} pairs configured')"

# Test API key
python -c "from src.config import ALPHA_VANTAGE_API_KEY; print('✓ API key loaded' if ALPHA_VANTAGE_API_KEY else '✗ API key not found')"
```

All checks should show ✓

## Running the Pipeline

### First-Time Setup (~3-5 minutes)

```bash
# Step 1: Fetch forex data from Alpha Vantage
python fetch_data.py
# This takes ~2 minutes due to rate limiting
# Data is cached - only runs once!

# Step 2: Compute technical features
python build_features.py
# Takes ~30 seconds

# Step 3: Generate trading labels
python build_labels.py
# Takes ~1-2 minutes

# Step 4: Verify everything worked
python verify_dataset.py
# Instant - shows summary statistics
```

### Expected Output

After successful pipeline run:

```
data/
├── raw/                    # 7 JSON files (~5 MB)
│   ├── fx_daily_EURUSD.json
│   ├── fx_daily_GBPUSD.json
│   └── ...
├── ohlcv/                  # 7 parquet files (~2 MB)
│   ├── EURUSD_D1.parquet
│   ├── GBPUSD_D1.parquet
│   └── ...
└── features/               # 2 parquet files (~50 MB)
    ├── features_raw.parquet
    └── features_labeled.parquet
```

### Subsequent Runs

After initial setup, you can skip fetching:

```bash
# Re-build features (if you modified feature engineering)
python build_features.py

# Re-generate labels (if you changed labeling parameters)
python build_labels.py

# Verify
python verify_dataset.py
```

Data fetching only needed once (or to refresh data later).

## Exploring the Data

### Launch Jupyter

```bash
jupyter notebook
```

Browser opens automatically. Navigate to `notebooks/01_eda.ipynb`

### Quick Python Exploration

```python
# In Python shell or Jupyter
from src.dataset import load_labeled_dataset, get_train_val_test_splits

# Load data
df = load_labeled_dataset()
print(df.head())

# Get ML-ready splits
X_train, y_train, X_val, y_val, X_test, y_test = get_train_val_test_splits()

print(f"Training samples: {len(X_train)}")
print(f"Features: {len(X_train.columns)}")
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'dotenv'"

Solution:
```bash
pip install python-dotenv
```

Or reinstall all dependencies:
```bash
pip install -r requirements.txt
```

### "ValueError: Alpha Vantage API key not found"

Check:
1. `.env` file exists in project root
2. File contains: `ALPHA_VANTAGE_API_KEY=your_actual_key`
3. No extra spaces or quotes around the key
4. Virtual environment is activated

Test:
```bash
cat .env
python -c "from src.config import ALPHA_VANTAGE_API_KEY; print(ALPHA_VANTAGE_API_KEY)"
```

### "FileNotFoundError: No OHLCV files found"

You need to fetch data first:
```bash
python fetch_data.py
```

### "Rate limit exceeded" or "Note: Thank you for using Alpha Vantage!"

This means you hit the 25 calls/day limit. Solutions:
1. **Wait 24 hours** for limit reset
2. **Use cached data** - once fetched, data is saved locally
3. **Premium API key** - if you need frequent refreshes

### "JSONDecodeError" or corrupt cache

Clear cache and re-fetch:
```bash
rm -rf data/raw/*.json
python fetch_data.py
```

### Import errors in notebooks

Make sure the path setup cell runs first:
```python
import sys
sys.path.insert(0, '..')
```

### Jupyter notebook doesn't find modules

Ensure Jupyter is using the correct kernel:
```bash
# Install ipykernel in your venv
pip install ipykernel

# Add venv as Jupyter kernel
python -m ipykernel install --user --name=forex-venv

# In Jupyter: Kernel > Change Kernel > forex-venv
```

## Uninstallation

To remove the project:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv/

# Remove data (optional, if you want to free up space)
rm -rf data/

# Remove the project directory (if desired)
cd ..
rm -rf forex/
```

## Updating Dependencies

To update all packages to latest versions:

```bash
pip install --upgrade -r requirements.txt
```

## System Requirements

### Minimum
- Python 3.8+
- 2 GB RAM
- 500 MB disk space
- 1 CPU core

### Recommended
- Python 3.9 or 3.10
- 4 GB RAM
- 1 GB disk space
- 2+ CPU cores

## Performance Notes

- **Data fetching**: ~2 minutes (rate limited, one-time)
- **Feature building**: ~30 seconds (7 pairs × 6,000 days each)
- **Labeling**: ~1-2 minutes (triple-barrier computation)
- **Total pipeline**: ~3-5 minutes first run
- **Subsequent runs**: <1 minute (uses cache)

## Next Steps

After successful installation:

1. Read [QUICKSTART.md](QUICKSTART.md) for usage guide
2. Read [README.md](README.md) for comprehensive documentation
3. Run the pipeline: `fetch_data.py` → `build_features.py` → `build_labels.py`
4. Explore data: `jupyter notebook` → `notebooks/01_eda.ipynb`
5. Check [PROJECT_STATUS.md](PROJECT_STATUS.md) for Phase 2 roadmap

## Getting Help

- Check [README.md](README.md) troubleshooting section
- Review docstrings in source code
- Verify all steps in this guide

---

**Installation complete?** Run `python verify_dataset.py` to confirm!




