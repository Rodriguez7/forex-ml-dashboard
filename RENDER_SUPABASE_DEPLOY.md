# Render + Supabase Deployment Guide

Complete guide for deploying the Forex ML Dashboard to Render using Supabase database.

## Overview

This deployment uses:
- **Render** - Hosts Flask web service and cron job (free tier)
- **Supabase** - PostgreSQL database (free tier, external)
- **Alpha Vantage** - Forex data API (free tier)

## Prerequisites

1. **GitHub Account** - Code must be in a GitHub repository
2. **Render Account** - Sign up at https://render.com
3. **Supabase Account** - Sign up at https://supabase.com
4. **Alpha Vantage API Key** - Get from https://www.alphavantage.co/support/#api-key

## Step 1: Set Up Supabase Database

### 1.1 Create Supabase Project

1. Go to https://supabase.com
2. Create a new project (or use existing)
3. Note your project reference (e.g., `zstusykclsbiosgrtwhw`)

### 1.2 Get Connection String

1. Go to Supabase Dashboard → Settings → Database
2. Scroll to **Connection string** section
3. Select **Session mode** (direct connection)
4. Copy the connection string
   - Format: `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
5. **Save this connection string** - you'll need it for Render

### 1.3 Initialize Database Schema

The schema will be created automatically on first connection, or you can initialize it locally:

```bash
# Set DATABASE_URL locally
export DATABASE_URL="your_supabase_connection_string"

# Initialize schema
python -c "from src.database import init_database; init_database()"
```

## Step 2: Prepare Repository

1. **Ensure all files are committed:**
   ```bash
   git add .
   git commit -m "Configure for Render + Supabase deployment"
   git push origin main
   ```

2. **Verify model files are tracked:**
   ```bash
   git ls-files data/models/
   ```
   
   Should include:
   - `lgbm_baseline.pkl`
   - `lgbm_optimized.pkl`
   - And their metadata files

## Step 3: Deploy to Render

### 3.1 Create Blueprint

1. Go to https://render.com/dashboard
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repository
4. Branch: `main`
5. Click **"Apply"**

### 3.2 Review Services

Render will detect `render.yaml` and create:
- **Web Service** (`forex-signals-dashboard`)
- **Cron Job** (`daily-signal-generation`)

**Note:** No PostgreSQL service - we're using Supabase!

### 3.3 Set Environment Variables

**For Web Service:**

1. Go to `forex-signals-dashboard` → **Environment** tab
2. Add environment variables:
   - `ALPHA_VANTAGE_API_KEY` = `your_alpha_vantage_api_key`
   - `DATABASE_URL` = `your_supabase_connection_string`
     - Use the connection string from Step 1.2
     - Make sure password is URL-encoded if it contains special characters

**For Cron Job:**

1. Go to `daily-signal-generation` → **Environment** tab
2. Add the same environment variables:
   - `ALPHA_VANTAGE_API_KEY` = `your_alpha_vantage_api_key`
   - `DATABASE_URL` = `your_supabase_connection_string` (same as Web Service)

### 3.4 Wait for Deployment

- First deployment: 5-10 minutes
- Watch build logs in Render dashboard
- Check for any build errors

## Step 4: Verify Deployment

### 4.1 Check Web Service

1. Go to Web Service → **Settings**
2. Note your service URL (e.g., `https://forex-signals-dashboard.onrender.com`)
3. Visit the URL to see the dashboard
4. Visit `/health` endpoint to verify database connection:
   - Should return: `{"status": "ok", "database": "available"}`

### 4.2 Check Cron Job

1. Go to Cron Job → **Recent Runs**
2. Verify it's scheduled correctly (2:15 AM UTC daily)
3. Check logs for any errors

### 4.3 Initial Data Setup

After deployment, populate the database:

1. Go to Web Service → **Shell** tab
2. Run these commands:
   ```bash
   python fetch_data.py
   python build_features.py
   python build_labels.py
   python generate_signals.py --model lgbm_optimized --confidence 0.5
   ```

This will:
- Fetch forex data from Alpha Vantage
- Build features
- Generate labels
- Create initial trading signals

## Step 5: Connection String Format

Your Supabase connection string should be:

```
postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

**Important Notes:**
- Replace `[PASSWORD]` with your actual database password
- Replace `[PROJECT_REF]` with your Supabase project reference
- If password contains special characters, URL-encode them:
  - `@` → `%40`
  - `!` → `%21`
  - `#` → `%23`
  - etc.

**Example:**
```
postgresql://postgres:MyPass%40word123@db.zstusykclsbiosgrtwhw.supabase.co:5432/postgres
```

## Troubleshooting

### Database Connection Fails

**Symptoms:** Health check shows `"database": "unavailable"` or connection errors in logs.

**Solutions:**
1. Verify `DATABASE_URL` is set correctly in Render dashboard
2. Check connection string format matches Supabase format
3. Ensure password is URL-encoded if it has special characters
4. Verify Supabase database is running (check Supabase dashboard)
5. Check Supabase network settings (IP restrictions)

### Build Fails

**Symptoms:** Build logs show errors.

**Solutions:**
1. Check `requirements.txt` is correct
2. Verify Python version (3.11.0) is set
3. Check for missing dependencies in build logs

### Cron Job Not Running

**Symptoms:** No signals generated, cron job shows errors.

**Solutions:**
1. Check cron job logs in Render dashboard
2. Verify environment variables are set
3. Test pipeline manually in Shell:
   ```bash
   python run_pipeline.py
   ```
4. Check Supabase database for connection issues

### No Signals Showing

**Symptoms:** Dashboard loads but shows "No signals found".

**Solutions:**
1. Run initial data setup (Step 4.3)
2. Check cron job has run successfully
3. Verify signals are being saved to Supabase:
   - Check Supabase dashboard → Table Editor → `signals` table
4. Check application logs for errors

## Free Tier Limits

### Render Free Tier
- **Web Service**: Spins down after 15 min inactivity (cold start ~30-60s)
- **Cron Jobs**: Run on schedule, may have delays
- **Build Time**: Limited build minutes per month

### Supabase Free Tier
- **Database Size**: 500 MB
- **Bandwidth**: 2 GB/month
- **Connections**: Up to 60 direct connections
- **API Requests**: Unlimited (with rate limits)

### Alpha Vantage Free Tier
- **Rate Limits**: 25 calls/day, 5 calls/minute
- **Our Usage**: 7 calls/day (one per forex pair)
- **Schedule**: Daily at 2:15 AM UTC

## Updating Deployment

### Update Code

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update code"
   git push origin main
   ```
3. Render will auto-deploy (or trigger manually)

### Update Environment Variables

1. Go to service → **Environment** tab
2. Edit or add variables
3. Save changes
4. Service will restart automatically

### Update Database Connection

If you need to change Supabase connection:

1. Get new connection string from Supabase dashboard
2. Update `DATABASE_URL` in both Web Service and Cron Job
3. Services will restart automatically

## Security Best Practices

1. **Never commit connection strings to Git**
   - Use environment variables only
   - `.env` file should be in `.gitignore`

2. **Use strong database passwords**
   - Rotate passwords regularly
   - Store passwords securely

3. **Monitor Supabase usage**
   - Check bandwidth and storage usage
   - Set up alerts if needed

4. **Keep API keys secure**
   - Don't expose in logs or public repos
   - Rotate keys periodically

## Additional Resources

- **Render Docs**: https://render.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Supabase Database Guide**: https://supabase.com/docs/guides/database/connecting-to-postgres
- **Alpha Vantage API**: https://www.alphavantage.co/documentation/

## Summary

This deployment uses:
- ✅ Render for hosting (web service + cron job)
- ✅ Supabase for database (external PostgreSQL)
- ✅ Environment variables for configuration
- ✅ Automatic schema initialization
- ✅ Daily automated signal generation

Your dashboard will be available at your Render service URL and will automatically update daily with new trading signals!

