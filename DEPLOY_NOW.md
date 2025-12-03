# Quick Deploy Guide - Render

## 🚀 Deploy in 5 Steps

### 1. Go to Render Dashboard
- Visit: https://render.com
- Sign in with GitHub

### 2. Create Blueprint
- Click **"New"** → **"Blueprint"**
- Connect repository: `Rodriguez7/forex-ml-dashboard`
- Branch: `main`
- Click **"Apply"**

### 3. Set Environment Variables
After services are created, add environment variables:

**Web Service (`forex-signals-dashboard`):**
- Go to service → **Environment** tab
- Add: `ALPHA_VANTAGE_API_KEY` = `YOUR_API_KEY`
- Add: `DATABASE_URL` = `your_supabase_connection_string`
  - Format: `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
  - Get from: Supabase Dashboard → Settings → Database → Connection string (Session mode)

**Cron Job (`daily-signal-generation`):**
- Go to service → **Environment** tab  
- Add: `ALPHA_VANTAGE_API_KEY` = `YOUR_API_KEY`
- Add: `DATABASE_URL` = `your_supabase_connection_string` (same as Web Service)

### 4. Wait for Deployment
- First deploy: 5-10 minutes
- Watch build logs in dashboard

### 5. Initial Data Setup
After deployment completes:

1. Go to **Web Service** → **Shell** tab
2. Run these commands:
   ```bash
   python fetch_data.py
   python build_features.py
   python build_labels.py
   python generate_signals.py --model lgbm_optimized --confidence 0.5
   ```

## ✅ Verify Deployment

1. **Dashboard URL**: Check Web Service → Settings for your URL
   - Format: `https://forex-signals-dashboard.onrender.com`

2. **Health Check**: Visit `/health` endpoint
   - Should return: `{"status": "ok", "database": "available"}`

3. **View Signals**: Visit root URL to see dashboard

## 📝 Notes

- **Free Tier**: Web service spins down after 15 min inactivity (cold start ~30-60s)
- **Cron Schedule**: Runs daily at 2:15 AM UTC
- **API Limits**: Alpha Vantage free tier = 25 calls/day (we use 7/day - safe!)

## 🔧 Troubleshooting

**No signals showing?**
- Run initial data setup (Step 5)
- Check cron job logs

**Build fails?**
- Check build logs for errors
- Verify `requirements.txt` is correct

**Database errors?**
- Verify `DATABASE_URL` is set (Supabase connection string)
- Check Supabase database is running and accessible

## 🎉 Success!

Once deployed, your dashboard will:
- Display latest trading signals
- Update automatically via cron job
- Store data in Supabase database

