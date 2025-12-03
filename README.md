# Forex Swing Trading ML Predictor (Quant Edition)

A research-grade machine learning system for predicting directional swing trades (3-10 day horizon) on major forex pairs using proper quant methodology.

## 🎯 Project Goals

- **Predict swing trades** on major FX pairs (EURUSD, GBPUSD, USDJPY, etc.)
- **No data leakage**: time-respecting splits, no lookahead bias
- **Triple-barrier labeling**: ATR-based take-profit and stop-loss levels
- **Confidence filtering**: High-probability trade subset (70-80% win rate)
- **Decision support**: Not auto-trading, but trade idea generation

## 🏗️ Architecture

### Phase 1: Data Pipeline & Features ✅ COMPLETE

1. Alpha Vantage FX data fetching with caching
2. Feature engineering (50+ technical indicators)
3. Triple-barrier labeling with ATR-based TP/SL
4. Time-respecting train/val/test splits

### Phase 2: Modeling & Backtesting ✅ COMPLETE

1. LightGBM classifier training with evaluation
2. Confidence-based probability analysis
3. Comprehensive backtesting engine with equity curves
4. Performance metrics (win rate, profit factor, Sharpe, drawdown)
5. Signal generation for live trading ideas

### Phase 3: Performance Improvements ✅ COMPLETE

1. Regime-aware features (volatility & trend detection)
2. Cross-pair correlation features (intermarket analysis)
3. Improved labeling (volatility-adjusted horizons)
4. Optuna hyperparameter optimization (100 trials)
5. Model diagnostics and analysis

### Phase 4: Web Dashboard & Automation ✅ COMPLETE

1. **Flask web application** for signal visualization
2. **Automated daily updates** via cron
3. Beautiful, responsive dashboard with live signals
4. Respects Alpha Vantage free-tier limits

## 🌐 Web Dashboard

View your trading signals in a beautiful web interface!

### Quick Start

```bash
# Start the Flask web server
python app.py
```

Then open your browser to: **http://localhost:5000**

### Features

- **Real-time signal display** for all 7 forex pairs
- **Color-coded directions** (green for LONG, red for SHORT)
- **Confidence levels** displayed as percentages
- **Entry, TP, and SL prices** for each signal
- **Risk:Reward ratios** (1:1.8)
- **Last update timestamp**
- **Responsive design** (works on mobile, tablet, desktop)

### Dashboard Preview

The dashboard displays:
- Total signals count
- Number of LONG vs SHORT positions
- Full table with all signal details
- Model performance statistics
- Automatic updates when new signals are generated

## ⏰ Automated Daily Updates

Set up once, get fresh signals every day automatically!

### Quick Setup

```bash
# Test the pipeline manually
python run_pipeline.py
```

### Cron Automation

Run signals daily at 2:15 AM (respects API limits):

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths):
15 2 * * * cd /Users/rod/forex && python3 run_pipeline.py >> cron.log 2>&1
```

**See [CRON_SETUP.md](CRON_SETUP.md) for detailed instructions**

### What the Pipeline Does

1. **Fetches latest forex data** (7 pairs, within free tier)
2. **Builds 45 features** (regime + cross-pair + technical)
3. **Generates labels** (volatility-adjusted triple-barrier)
4. **Creates signals** (using optimized LightGBM model)

All automatically, respecting Alpha Vantage limits (7 calls/day out of 25 allowed).

## 📁 Project Structure

```
forex_swing_quant/
├── data/
│   ├── raw/                  # Cached Alpha Vantage JSON
│   ├── ohlcv/                # Clean OHLCV parquet files
│   ├── features/             # Feature datasets
│   ├── models/               # Trained models
│   ├── backtests/            # Backtest results
│   └── signals/              # Generated signals (NEW!)
├── src/
│   ├── config.py             # Configuration & parameters
│   ├── alpha_vantage_client.py  # API client with caching
│   ├── data_pipeline.py      # OHLCV data processing
│   ├── features.py           # Feature engineering (45 features)
│   ├── labeling.py           # Triple-barrier labeling
│   ├── dataset.py            # ML dataset preparation
│   ├── models.py             # Model training & evaluation
│   ├── backtest.py           # Backtesting engine
│   ├── signal_engine.py      # Signal generation
│   └── hyperparameter_tuning.py  # Optuna optimization (NEW!)
├── templates/
│   └── signals.html          # Flask dashboard template (NEW!)
├── notebooks/                # Jupyter notebooks for analysis
├── app.py                    # Flask web application (NEW!)
├── run_pipeline.py           # Automated pipeline script (NEW!)
├── fetch_data.py            # CLI: Fetch FX data
├── build_features.py        # CLI: Build features
├── build_labels.py          # CLI: Generate labels
├── train_model.py           # CLI: Train model
├── tune_hyperparameters.py  # CLI: Optimize hyperparameters (NEW!)
├── run_backtest.py          # CLI: Run backtest
├── generate_signals.py      # CLI: Generate signals
├── requirements.txt         # Dependencies (includes Flask)
├── CRON_SETUP.md            # Automated updates guide (NEW!)
└── README.md
```

## 🚀 Setup

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Get Alpha Vantage API Key

1. Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Sign up for a free API key (25 requests/day, 5 requests/minute)
3. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` and add your API key:
   ```
   ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
   ```

## 📊 Usage

### Phase 1: Data Pipeline

```bash
# Step 1: Fetch forex data (~2 minutes)
python fetch_data.py

# Step 2: Build features (~30 seconds)
python build_features.py

# Step 3: Generate labels (~1-2 minutes)
python build_labels.py

# Step 4: Verify dataset
python verify_dataset.py
```

**Phase 1 Output**: Labeled dataset with 30,000+ samples, 50+ features, ready for ML.

### Phase 2: Model Training & Backtesting

```bash
# Step 5: Train model (~1-2 minutes)
python train_model.py

# Step 6: Run backtest
python run_backtest.py

# Step 7: Generate trading signals
python generate_signals.py
```

**Phase 2 Output**: Trained model, backtest results with equity curve, live trading signals.

### Phase 3: Hyperparameter Optimization

```bash
# Run Optuna optimization (100 trials, ~30-60 min)
python tune_hyperparameters.py --trials 100

# Use optimized model
python run_backtest.py --model lgbm_optimized
python generate_signals.py --model lgbm_optimized
```

### Phase 4: Web Dashboard

```bash
# Start web dashboard
python app.py

# Open browser to http://localhost:5000

# Automate daily updates
python run_pipeline.py  # Test pipeline
# Then set up cron (see CRON_SETUP.md)
```

### Advanced Usage

```bash
# Backtest with different confidence threshold
python run_backtest.py --confidence 0.8

# Optimize confidence threshold
python run_backtest.py --optimize

# Generate signals with custom threshold
python generate_signals.py --confidence 0.75

# Analyze signal history
python generate_signals.py --history 30
```

## 🧪 Key Methodology

### Triple-Barrier Labeling

For each trading day at index `i`:

1. **Entry**: close price at day `i`
2. **Barriers**:
   - Long TP = entry + 1.8× ATR
   - Long SL = entry - 1.0× ATR
   - Short TP = entry - 1.8× ATR
   - Short SL = entry + 1.0× ATR
3. **Horizon**: Scan forward 3-10 days
4. **Detection**: Use high/low of each bar to detect first hit
5. **Label**: Compare long vs short outcome, assign best direction

### Time-Respecting Splits (No Leakage)

- **Train**: All data before 2020-01-01
- **Val**: 2020-01-01 to 2021-12-31
- **Test**: 2022-01-01 onwards

No overlap! Model never sees future data.

### Feature Engineering Principles

- All features use **only past data** (no lookahead)
- Normalized distances (e.g., price from SMA in ATR units)
- Mix of trend, momentum, volatility, and oscillator signals
- Clean, interpretable features (no black-box transforms)

## 🔍 Data Sources

- **Alpha Vantage FX API**: Free tier, daily OHLCV data
- **Pairs**: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD
- **History**: Typically 20+ years of data per pair
- **Update frequency**: Can refresh weekly/monthly (manual re-fetch)

## 📈 Expected Performance

### Realistic Targets

- **All signals**: 50-60% win rate, R:R ≥ 1.5
- **High-confidence subset** (prob ≥ 0.7): 70-80% win rate
- **Trade frequency**: Varies by confidence threshold
- **Horizon**: 3-10 day holding period

Not magic - this is achievable with proper feature engineering and filtering!

## 🛠️ Troubleshooting

### "No module named 'dotenv'"

```bash
pip install python-dotenv
```

### "ALPHA_VANTAGE_API_KEY not found"

Check your `.env` file exists and contains the key.

### "API limit reached"

Free tier: 25 calls/day. Wait 24 hours or use cached data. Cached data works indefinitely once fetched!

### "No OHLCV files found"

Run `python fetch_data.py` first.

## 📝 Development Roadmap

### Phase 1: ✅ Data Pipeline (COMPLETE)
- [x] Alpha Vantage integration
- [x] OHLCV processing
- [x] Feature engineering
- [x] Triple-barrier labeling
- [x] Dataset preparation

### Phase 2: ✅ Modeling & Backtesting (COMPLETE)
- [x] LightGBM training pipeline
- [x] Probability bucket analysis
- [x] Feature importance analysis
- [x] Model evaluation metrics
- [x] Equity curve simulation
- [x] Performance metrics (Sharpe, PF, DD)
- [x] Trade-level analysis
- [x] Confidence-filtered backtests
- [x] Signal generation engine

### Phase 3: 🚧 Production Enhancements (Future)
- [ ] Streamlit dashboard
- [ ] Real-time data updates
- [ ] Advanced hyperparameter tuning (Optuna)
- [ ] Ensemble models
- [ ] Trade logging & monitoring
- [ ] Alert system (email/SMS)
- [ ] Portfolio optimization

## 🔬 Research & Analysis

Use Jupyter notebooks for exploration:

```bash
jupyter notebook
```

Create notebooks in `notebooks/` directory:
- `01_eda.ipynb`: Exploratory data analysis
- `02_feature_analysis.ipynb`: Feature correlations & importance
- `03_label_analysis.ipynb`: Label distribution & quality

## ⚠️ Disclaimer

This is a **research tool** for educational purposes and trade idea generation. Not financial advice. Always:
- Validate signals independently
- Use proper risk management
- Never risk more than you can afford to lose
- Backtest results != future performance

## 📚 References

- Triple-barrier method: López de Prado, "Advances in Financial Machine Learning"
- Time-series cross-validation: Best practices for financial ML
- Alpha Vantage API: https://www.alphavantage.co/documentation/

## 🤝 Contributing

This is a personal research project. Suggestions welcome via issues!

## 📄 License

MIT License - Feel free to use for research and learning.

---

**Built with**: Python, pandas, scikit-learn, LightGBM, Alpha Vantage API

**Author**: Quantitative trading research project

**Version**: Phase 1 (Data Pipeline)

