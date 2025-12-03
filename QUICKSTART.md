# Quick Start Guide

Get your forex quant pipeline running in 5 minutes!

## ⚡ Fast Setup

### 1. Install & Configure (2 minutes)

```bash
# Clone and enter directory
cd forex

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup API key
cp .env.example .env
# Edit .env and add your Alpha Vantage API key
```

**Get API Key**: Visit https://www.alphavantage.co/support/#api-key (Free, instant)

### 2. Run the Pipeline (3 minutes + wait time)

```bash
# Step 1: Fetch data (~2 min due to rate limits)
python fetch_data.py

# Step 2: Build features (~30 sec)
python build_features.py

# Step 3: Generate labels (~1-2 min)
python build_labels.py

# Step 4: Verify everything worked
python verify_dataset.py
```

## ✅ What You Get

After running the pipeline, you'll have:

- **7 forex pairs** with 20+ years of data each
- **50+ technical features** per trading day
- **Triple-barrier labels** (long/short/neutral)
- **Train/val/test splits** (time-respecting, no leakage)
- **~30,000+ labeled examples** ready for ML

## 📊 Next Steps

### Explore the Data

```bash
jupyter notebook
```

Create a notebook to explore:

```python
import pandas as pd
from src.dataset import load_labeled_dataset, get_train_val_test_splits

# Load data
df = load_labeled_dataset()

# Check it out
print(df.head())
print(df.columns)
print(df['label'].value_counts())

# Get ML-ready splits
X_train, y_train, X_val, y_val, X_test, y_test = get_train_val_test_splits()

print(f"Train: {len(X_train)} samples")
print(f"Features: {len(X_train.columns)}")
```

### Train a Model (Phase 2 - Coming Soon)

```python
import lightgbm as lgb

# Simple baseline
model = lgb.LGBMClassifier(n_estimators=100, max_depth=5)
model.fit(X_train, y_train)

# Evaluate
from sklearn.metrics import accuracy_score, classification_report
y_pred = model.predict(X_val)
print(f"Accuracy: {accuracy_score(y_val, y_pred):.3f}")
```

## 🔍 Understanding the Data

### Labels Explained

- **+1 (Long)**: If you went long, TP was hit before SL within 3-10 days
- **-1 (Short)**: If you went short, TP was hit before SL within 3-10 days
- **0 (Neutral)**: Ambiguous outcome (filtered out for ML training)

### Features Overview

| Category | Features | Description |
|----------|----------|-------------|
| Returns | `ret_1`, `ret_3`, `ret_5`, `ret_10`, `log_ret_*` | Price momentum |
| Volatility | `vol_10`, `vol_20`, `atr` | Market volatility |
| Trend | `sma_20`, `sma_50`, `sma_100`, `trend_up`, `trend_down` | Trend direction |
| Oscillators | `rsi_14`, `stoch_k`, `stoch_d` | Overbought/oversold |
| Bands | `bb_pos`, `bb_upper`, `bb_lower` | Bollinger position |
| Breakouts | `breakout_up_20`, `breakout_down_20` | Price breakouts |

## 🛠️ Troubleshooting

### "API key not found"
Edit `.env` file and add your key:
```
ALPHA_VANTAGE_API_KEY=ABC123XYZ
```

### "No OHLCV files found"
Run `python fetch_data.py` first to fetch data.

### "Rate limit exceeded"
Free tier: 25 calls/day. Wait 24h or use cached data (data is auto-cached!).

### Import errors
```bash
# Make sure you activated venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📈 Pipeline Visualization

```
Alpha Vantage API
       ↓
   Raw JSON Cache (data/raw/)
       ↓
   OHLCV Parquet (data/ohlcv/)
       ↓
   Feature Engineering (50+ features)
       ↓
   Features Dataset (data/features/features_raw.parquet)
       ↓
   Triple-Barrier Labeling
       ↓
   Labeled Dataset (data/features/features_labeled.parquet)
       ↓
   Train/Val/Test Split (time-respecting)
       ↓
   Ready for ML!
```

## 💡 Pro Tips

1. **Data is cached**: Re-running pipeline is fast after first fetch
2. **Incremental development**: Each step saves to disk, no need to re-run everything
3. **Explore before modeling**: Use notebooks to understand data first
4. **Time-respecting**: Never train on future data - splits respect time
5. **Feature importance**: Use model.feature_importances_ to find best features

## 📚 Learn More

- Full details: See [README.md](README.md)
- Methodology: Triple-barrier method from "Advances in Financial Machine Learning"
- API docs: https://www.alphavantage.co/documentation/

---

**Ready to build something awesome? 🚀**

Start with `python fetch_data.py` and you're on your way!




