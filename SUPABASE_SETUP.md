# Supabase Database Setup Guide

This guide explains how to set up and configure Supabase as the database for the Forex ML Trading Signals system.

## What is Supabase?

Supabase is an open-source Firebase alternative built on PostgreSQL. It provides:
- PostgreSQL database (fully compatible with standard PostgreSQL)
- REST API and real-time subscriptions
- Built-in authentication and storage
- Free tier with generous limits

## Step 1: Create Supabase Account

1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub (recommended) or email
4. Create a new organization (if needed)

## Step 2: Create a New Project

1. Click "New Project"
2. Fill in project details:
   - **Name**: `forex-ml-signals` (or your preferred name)
   - **Database Password**: Choose a strong password (save it securely!)
   - **Region**: Choose closest to your deployment region
   - **Pricing Plan**: Free tier is sufficient for development
3. Click "Create new project"
4. Wait 2-3 minutes for project to be provisioned

## Step 3: Get Connection String

1. Go to your project dashboard
2. Click on **Settings** (gear icon) → **Database**
3. Scroll down to **Connection string**
4. Select **Connection pooling** tab (recommended for serverless)
5. Copy the connection string (URI format)
   - Format: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
   - Or use **Session mode** for direct connections:
     - Format: `postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres`

## Step 4: Set Environment Variable

### For Local Development

Create or update `.env` file in project root:

```bash
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

Replace:
- `[YOUR_PASSWORD]` with your database password
- `[PROJECT_REF]` with your project reference (found in project settings)

### For Production/Deployment

Set the `DATABASE_URL` environment variable in your deployment platform:

**Render:**
- Go to Web Service → Environment
- Add: `DATABASE_URL` = `your_supabase_connection_string`

**Heroku:**
```bash
heroku config:set DATABASE_URL=your_supabase_connection_string
```

**Other platforms:**
- Add `DATABASE_URL` to your environment variables

## Step 5: Initialize Database Schema

The application will automatically create the required tables on first run. To manually initialize:

```bash
python -c "from src.database import init_database; init_database()"
```

Or run the pipeline which will initialize automatically:

```bash
python run_pipeline.py
```

## Step 6: Verify Connection

Test the database connection:

```bash
python -c "from src.database import is_database_available, init_database; print('Available:', is_database_available()); init_database()"
```

You should see:
```
✓ Database schema initialized successfully
```

## Connection String Formats

Supabase provides different connection string formats:

### Session Mode (Direct Connection)
- Best for: Long-running connections, migrations, admin tasks
- Format: `postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres`
- Port: `5432`

### Transaction Mode (Connection Pooling)
- Best for: Serverless functions, short-lived connections
- Format: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
- Port: `6543`

### Recommended for This Project

For Flask web service and cron jobs, use **Transaction Mode** (connection pooling) as it handles connection management better for serverless environments.

## Security Best Practices

1. **Never commit connection strings to Git**
   - Use environment variables
   - Add `.env` to `.gitignore`

2. **Use connection pooling** for production
   - Reduces connection overhead
   - Better for serverless deployments

3. **Rotate passwords regularly**
   - Update in Supabase dashboard
   - Update `DATABASE_URL` environment variable

4. **Enable Row Level Security (RLS)** if needed
   - Configure in Supabase dashboard
   - Add policies for your use case

## Free Tier Limits

Supabase free tier includes:
- **Database Size**: 500 MB
- **Bandwidth**: 2 GB/month
- **API Requests**: Unlimited (with rate limits)
- **Database Connections**: Up to 60 direct connections, unlimited pooled

For this Forex ML project, the free tier is more than sufficient.

## Troubleshooting

### Connection Timeout
- Check if you're using the correct connection string format
- Verify your IP is not blocked (check Supabase dashboard)
- Try connection pooling mode instead of session mode

### Authentication Failed
- Verify password is correct
- Check connection string format
- Ensure you're using the right project reference

### Schema Not Created
- Check database logs in Supabase dashboard
- Verify `DATABASE_URL` is set correctly
- Run `init_database()` manually

### Connection Pool Exhausted
- Switch to transaction mode (pooling)
- Reduce connection timeout
- Check for connection leaks in your code

## Migration from Render PostgreSQL

If you were previously using Render's PostgreSQL:

1. Export data from Render (if needed):
   ```bash
   pg_dump $RENDER_DATABASE_URL > backup.sql
   ```

2. Create new Supabase project

3. Import data to Supabase:
   ```bash
   psql $SUPABASE_DATABASE_URL < backup.sql
   ```

4. Update `DATABASE_URL` environment variable

5. Restart your services

## Additional Resources

- **Supabase Docs**: https://supabase.com/docs
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Connection Pooling Guide**: https://supabase.com/docs/guides/database/connecting-to-postgres

