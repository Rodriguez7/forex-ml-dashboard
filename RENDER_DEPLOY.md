# Render Deployment Guide

Complete step-by-step guide to deploy the Forex ML Dashboard to Render's free tier.

## Overview

This guide deploys:
- **Flask Web Service** (free tier) - displays the dashboard
- **Cron Job** (free tier) - generates signals daily at 2:15 AM UTC
- **Supabase Database** (external) - stores trading signals

## Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Render Account** - Sign up at https://render.com (free tier available)
3. **Supabase Account** - Sign up at https://supabase.com (free tier available)
4. **Alpha Vantage API Key** - Get from https://www.alphavantage.co/support/#api-key
5. **Supabase Database** - Already set up with connection string ready

## Step 1: Prepare Your Repository

1. **Ensure all files are committed and pushed to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Verify model files are tracked:**
   ```bash
   git ls-files data/models/
   ```
   
   You should see:
   - `data/models/lgbm_baseline.pkl`
   - `data/models/lgbm_baseline_metadata.pkl`
   - `data/models/lgbm_baseline_features.txt`
   - `data/models/lgbm_optimized.pkl`
   - `data/models/lgbm_optimized_metadata.pkl`
   - `data/models/lgbm_optimized_features.txt`

   If not, add them:
   ```bash
   git add data/models/*.pkl data/models/*.txt
   git commit -m "Add model files for deployment"
   git push
   ```

## Step 2: Create Render Account

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended for easy repository access)
4. Authorize Render to access your GitHub repositories

## Step 3: Deploy Using Render Blueprint (Recommended)

If you have `render.yaml` in your repository:

1. **Go to Render Dashboard** → Click "New" → "Blueprint"
2. **Connect Repository:**
   - Select your GitHub repository
   - Branch: `main` (or your default branch)
   - Root Directory: leave empty (or `.` if needed)

3. **Review Blueprint:**
   - Render will detect `render.yaml`
   - You'll see 2 services:
     - Web Service (`forex-signals-dashboard`)
     - Cron Job (`daily-signal-generation`)

4. **Click "Apply"** to create all services

5. **Set Environment Variables:**
   
   **For Web Service (`forex-signals-dashboard`):**
   - Go to Web Service → Environment tab
   - Add: `ALPHA_VANTAGE_API_KEY` = `YOUR_API_KEY_HERE`
   - Add: `DATABASE_URL` = `your_supabase_connection_string`
     - Format: `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
     - Get from: Supabase Dashboard → Settings → Database → Connection string (Session mode)
   
   **For Cron Job (`daily-signal-generation`):**
   - Go to Cron Job → Environment tab
   - Add: `ALPHA_VANTAGE_API_KEY` = `YOUR_API_KEY_HERE`
   - Add: `DATABASE_URL` = `your_supabase_connection_string` (same as above)

6. **Wait for deployment** (5-10 minutes for first deploy)

## Step 4: Manual Deployment (Alternative)

If you prefer manual setup:

**Note:** This deployment uses Supabase database (external). Make sure you have:
- Supabase account and project created
- Supabase connection string ready
- See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for Supabase setup

### 4.1 Create Web Service

1. **Go to Dashboard** → Click "New" → "Web Service"
2. **Connect Repository:**
   - Select your GitHub repository
   - Branch: `main`
   - Root Directory: leave empty

3. **Settings:**
   - Name: `forex-signals-dashboard`
   - Environment: **Python 3**
   - Region: Choose closest to you
   - Branch: `main`
   - Root Directory: leave empty
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
   - Plan: **Free**

4. **Environment Variables:**
   - Click "Advanced" → "Add Environment Variable"
   - Key: `PYTHON_VERSION`, Value: `3.11.0`
   - Key: `ALPHA_VANTAGE_API_KEY`, Value: `YOUR_API_KEY_HERE`
   - Key: `DATABASE_URL`, Value: `your_supabase_connection_string`
     - Format: `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
     - Get from: Supabase Dashboard → Settings → Database → Connection string (Session mode)

5. **Click "Create Web Service"**

6. **Wait for first deployment** (5-10 minutes)

### 4.3 Create Cron Job

1. **Go to Dashboard** → Click "New" → "Cron Job"
2. **Connect Repository:**
   - Select your GitHub repository
   - Branch: `main`
   - Root Directory: leave empty

3. **Settings:**
   - Name: `daily-signal-generation`
   - Environment: **Python 3**
   - Region: Choose closest to you
   - Schedule: `15 2 * * *` (2:15 AM UTC daily)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python run_pipeline.py`
   - Plan: **Free**

4. **Environment Variables:**
   - Key: `PYTHON_VERSION`, Value: `3.11.0`
   - Key: `ALPHA_VANTAGE_API_KEY`, Value: `YOUR_API_KEY_HERE`
   - Key: `DATABASE_URL`, Value: `your_supabase_connection_string` (same as Web Service)

5. **Click "Create Cron Job"**

## Step 5: Initial Data Setup

After deployment, you need to populate the database with initial data:

1. **Go to Web Service** → Click "Shell" (or use Render's Shell feature)

2. **Run these commands in order:**
   ```bash
   # 1. Fetch forex data (7 API calls)
   python fetch_data.py
   
   # 2. Build features
   python build_features.py
   
   # 3. Generate labels
   python build_labels.py
   
   # 4. Generate initial signals
   python generate_signals.py --model lgbm_optimized --confidence 0.5
   ```

   This will:
   - Fetch latest forex data from Alpha Vantage
   - Build features (including regime and cross-pair)
   - Generate triple-barrier labels
   - Create initial trading signals and save to database

3. **Verify signals in database:**
   - Go to your dashboard URL
   - You should see signals displayed

## Step 6: Access Your Dashboard

1. **Find your dashboard URL:**
   - Go to Web Service → Settings
   - URL format: `https://forex-signals-dashboard.onrender.com`

2. **Open in browser:**
   - The dashboard should display your latest signals
   - Signals update automatically via cron job

3. **Health Check:**
   - Visit: `https://your-url.onrender.com/health`
   - Should return: `{"status": "ok", "database": "available", ...}`

## Step 7: Verify Cron Job

1. **Go to Cron Job** → "Recent Runs"
2. **Wait for scheduled run** (or trigger manually for testing)
3. **Check logs** to verify:
   - Data fetched successfully
   - Features built
   - Labels generated
   - Signals created and saved to database

## Troubleshooting

### "No signals found" on dashboard

**Problem:** Database is empty or signals weren't generated.

**Solution:**
1. Check cron job logs for errors
2. Run initial data setup manually (Step 5)
3. Verify database connection:
   ```bash
   # In Render Shell
   python -c "from src.database import init_database, is_database_available; print('DB Available:', is_database_available()); init_database()"
   ```

### Database connection errors

**Problem:** `DATABASE_URL` not set or incorrect.

**Solution:**
1. Verify `DATABASE_URL` environment variable is set in Web Service and Cron Job
2. Check Supabase connection string format: `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
3. Ensure password is URL-encoded if it contains special characters
4. Verify Supabase database is running and accessible
5. Check Supabase dashboard for connection issues or IP restrictions

### Model files not found

**Problem:** Models missing on deployment.

**Solution:**
1. Verify models are committed to Git:
   ```bash
   git ls-files data/models/
   ```
2. If missing, add and commit:
   ```bash
   git add data/models/*.pkl data/models/*.txt
   git commit -m "Add models"
   git push
   ```
3. Redeploy the web service

### API rate limit errors

**Problem:** Alpha Vantage free tier limits exceeded.

**Solution:**
- Free tier: 25 calls/day, 5/min
- We use 7 calls (one per pair) - safe!
- Cron runs once daily at 2:15 AM UTC
- Don't manually trigger multiple times in one day

### Build fails with missing dependencies

**Problem:** Requirements not installing correctly.

**Solution:**
1. Verify `requirements.txt` has all dependencies
2. Check build logs for specific error
3. Common fixes:
   - Update Python version in environment variables
   - Check for version conflicts in requirements.txt

### Cron job fails silently

**Problem:** Cron job runs but doesn't produce signals.

**Solution:**
1. Check cron job logs (Recent Runs → View Logs)
2. Verify environment variables are set
3. Test pipeline manually in Shell:
   ```bash
   python run_pipeline.py
   ```
4. Check database for errors

## Free Tier Limitations

### Render Free Tier:
- **Web Service**: Spins down after 15 minutes of inactivity (cold start ~30-60 seconds)
- **Cron Jobs**: Run on schedule, may have delays

### Supabase Free Tier:
- **Database Size**: 500 MB
- **Bandwidth**: 2 GB/month
- **Connections**: Up to 60 direct connections, unlimited pooled
- **Retention**: Generous free tier limits

### Alpha Vantage Free Tier:
- **Rate Limits**: 25 calls/day, 5 calls/minute
- **Our Usage**: 7 calls/day (7 pairs) - well within limits
- **Schedule**: Daily at 2:15 AM UTC

### Model Files:
- **Size**: ~68KB total (small enough for Git)
- **Location**: Committed to repository
- **Update**: Retrain and commit new models when needed

## Updating Models

If you retrain models locally:

1. **Train new model:**
   ```bash
   python train_model.py
   # or
   python tune_hyperparameters.py
   ```

2. **Commit new models:**
   ```bash
   git add data/models/*.pkl data/models/*.txt
   git commit -m "Update models"
   git push
   ```

3. **Redeploy** (Render auto-deploys on push, or manually trigger)

## Monitoring

### Check Dashboard Status:
- Web Service → Metrics: View CPU, memory, response times
- Web Service → Logs: View application logs

### Check Cron Job:
- Cron Job → Recent Runs: View execution history
- Cron Job → Logs: View detailed logs

### Check Database:
- Supabase → Dashboard: View database usage and logs

### Health Endpoint:
- Visit: `https://your-url.onrender.com/health`
- Returns database status and latest signal timestamp

## Custom Domain (Optional)

1. **Go to Web Service** → Settings → Custom Domain
2. **Add your domain**
3. **Follow DNS configuration instructions**
4. **SSL certificate** is automatically provisioned

## Cost Estimate

**Free Tier:**
- Supabase: $0/month (free tier)
- Web Service: $0/month
- Cron Job: $0/month
- **Total: $0/month**

**If you need:**
- Always-on web service: $7/month (Starter plan)
- Larger database: $7/month (Starter plan)

## Next Steps

1. ✅ Deploy to Render
2. ✅ Run initial data setup
3. ✅ Verify dashboard is working
4. ✅ Monitor cron job execution
5. ✅ Set up custom domain (optional)
6. ✅ Configure alerts/notifications (optional)

## Support

- **Render Docs**: https://render.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Alpha Vantage Docs**: https://www.alphavantage.co/documentation/

## Success Checklist

- [ ] Repository pushed to GitHub with model files
- [ ] Supabase database configured and connection string ready
- [ ] Web service deployed and accessible
- [ ] Cron job created and scheduled
- [ ] Environment variables set (API key, database URL)
- [ ] Initial data setup completed
- [ ] Dashboard displays signals
- [ ] Cron job runs successfully
- [ ] Health endpoint returns OK status

Congratulations! Your Forex ML Dashboard is now live on Render! 🚀

