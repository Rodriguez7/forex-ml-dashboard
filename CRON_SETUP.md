# Automated Daily Signal Updates with Cron

This guide explains how to set up automated daily updates for your Forex ML trading signals using cron.

---

## Overview

The `run_pipeline.py` script automates the complete workflow:
1. Fetches latest forex data from Alpha Vantage
2. Builds features (45 features including regime + cross-pair)
3. Generates triple-barrier labels
4. Creates trading signals using the optimized model

**Schedule**: Run once daily at 2:15 AM to ensure:
- All daily candles are closed
- Alpha Vantage API limits are respected (7 calls for 7 pairs, well within 25/day limit)
- Fresh signals available each morning

---

## Alpha Vantage API Limits

**Free Tier Limits:**
- **25 API calls per day**
- **5 API calls per minute**

**Our Usage:**
- 7 forex pairs = 7 API calls per run
- 1 run per day = 7 daily calls
- **Well within limits** ✅

---

## Setup Instructions

### 1. Test the Pipeline Manually

Before setting up cron, test that the pipeline works:

```bash
cd /Users/rod/forex
python run_pipeline.py
```

This should complete all 4 steps successfully and generate new signals in `data/signals/`.

---

### 2. Set Up Environment Variables

Cron runs in a minimal environment, so you need to export your API key.

**Option A: Add to `~/.bash_profile` (recommended for macOS)**

```bash
# Open your bash profile
nano ~/.bash_profile

# Add this line (replace with your actual key)
export ALPHA_VANTAGE_API_KEY="U9GOCNQL7ZWZI3BB"

# Save and reload
source ~/.bash_profile
```

**Option B: Add to `~/.bashrc` (for Linux)**

```bash
# Open bashrc
nano ~/.bashrc

# Add the same export line
export ALPHA_VANTAGE_API_KEY="U9GOCNQL7ZWZI3BB"

# Save and reload
source ~/.bashrc
```

**Verify it's set:**
```bash
echo $ALPHA_VANTAGE_API_KEY
```

---

### 3. Create Cron Job

**Open crontab editor:**
```bash
crontab -e
```

**Add this line** (adjust paths to your actual setup):

```bash
# Forex ML Pipeline - Daily signal updates at 2:15 AM
SHELL=/bin/bash
BASH_ENV=/Users/rod/.bash_profile
15 2 * * * cd /Users/rod/forex && /usr/bin/python3 /Users/rod/forex/run_pipeline.py >> /Users/rod/forex/cron.log 2>&1
```

**Explanation:**
- `15 2 * * *` = Run at 2:15 AM every day
- `SHELL=/bin/bash` = Use bash shell
- `BASH_ENV=...` = Load environment variables from bash_profile
- `cd /Users/rod/forex` = Change to project directory
- `/usr/bin/python3` = Full path to Python (required for cron)
- `>> .../cron.log 2>&1` = Append output to log file

**Find your Python path:**
```bash
which python3
```

---

### 4. Verify Cron Job is Active

**List active cron jobs:**
```bash
crontab -l
```

You should see your forex pipeline entry.

**Test cron job manually** (run as if it's 2:15 AM):
```bash
cd /Users/rod/forex && /usr/bin/python3 /Users/rod/forex/run_pipeline.py >> /Users/rod/forex/cron.log 2>&1
```

---

## Monitoring & Logs

### Check Cron Log

```bash
tail -f /Users/rod/forex/cron.log
```

This shows the output of each pipeline run.

### Check Latest Signals

```bash
ls -ltr /Users/rod/forex/data/signals/
```

New signal files should appear daily after 2:15 AM.

### View Signals in Web Dashboard

Start the Flask app:
```bash
cd /Users/rod/forex
python app.py
```

Then open: `http://localhost:5000`

---

## Troubleshooting

### Pipeline Fails with "API Key Not Found"

**Problem:** Cron can't access environment variables.

**Solution:** 
1. Verify API key is in `~/.bash_profile`
2. Make sure `BASH_ENV` is set in crontab
3. Alternative: Hard-code in `.env` file (already done)

### Pipeline Fails with "Module Not Found"

**Problem:** Wrong Python environment or missing dependencies.

**Solution:**
```bash
# Use full path to python in your environment
which python3

# If using virtual environment, activate it in the cron command:
15 2 * * * cd /Users/rod/forex && source venv/bin/activate && python run_pipeline.py >> cron.log 2>&1
```

### No Signals Generated

**Problem:** Model or data issue.

**Solution:**
1. Check `cron.log` for errors
2. Run pipeline manually to see detailed output:
   ```bash
   python run_pipeline.py
   ```
3. Verify data directory exists and has permissions

### Cron Not Running

**Problem:** Cron service disabled or syntax error.

**Solution:**
```bash
# Check if cron is running (macOS)
sudo launchctl list | grep cron

# Check crontab syntax
crontab -l

# Test cron timing
* * * * * echo "Cron works" >> /tmp/cron_test.log
# Wait 1 minute, then check:
cat /tmp/cron_test.log
```

---

## Alternative Schedule Options

### Run every 6 hours
```bash
0 */6 * * * cd /Users/rod/forex && python3 run_pipeline.py >> cron.log 2>&1
```

### Run on weekdays only (Monday-Friday)
```bash
15 2 * * 1-5 cd /Users/rod/forex && python3 run_pipeline.py >> cron.log 2>&1
```

### Run twice daily (6 AM and 6 PM)
```bash
0 6,18 * * * cd /Users/rod/forex && python3 run_pipeline.py >> cron.log 2>&1
```

**Note:** Don't run too frequently to stay within API limits!

---

## Running on a Server

If deploying to a cloud server (AWS, DigitalOcean, etc.):

1. **Copy project to server**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables**
4. **Configure cron as above**
5. **Optional: Set up Flask as a service** (systemd, supervisor, etc.)

---

## Keep Flask App Running 24/7

To keep the web dashboard running continuously:

### Option 1: Use Screen (simple)
```bash
screen -S forex-dashboard
python app.py
# Press Ctrl+A, then D to detach
# Reattach with: screen -r forex-dashboard
```

### Option 2: Use systemd service (production)

Create `/etc/systemd/system/forex-dashboard.service`:
```ini
[Unit]
Description=Forex ML Signal Dashboard
After=network.target

[Service]
Type=simple
User=rod
WorkingDirectory=/Users/rod/forex
Environment="ALPHA_VANTAGE_API_KEY=U9GOCNQL7ZWZI3BB"
ExecStart=/usr/bin/python3 /Users/rod/forex/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable forex-dashboard
sudo systemctl start forex-dashboard
sudo systemctl status forex-dashboard
```

---

## Summary

✅ **Setup Complete When:**
- Pipeline runs manually without errors
- Cron job scheduled (verify with `crontab -l`)
- API key accessible in cron environment
- Log file shows successful runs
- New signals appear in `data/signals/` daily
- Flask dashboard displays latest signals

**Next Steps:**
1. Wait for 2:15 AM next day
2. Check `cron.log` for success
3. View new signals at `http://localhost:5000`
4. Monitor for a week to ensure stability

---

**Questions?** Check the main [README.md](README.md) or review `cron.log` for errors.



