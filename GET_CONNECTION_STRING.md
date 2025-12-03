# Get Your Supabase Connection String

You've provided:
- **Project URL**: https://zstusykclsbiosgrtwhw.supabase.co
- **Project Reference**: `zstusykclsbiosgrtwhw`

## What You Need

You need your **database password** (the one you set when creating the Supabase project).

## Option 1: Construct Connection String Manually (Easiest)

Since Transaction Mode may not be visible in your dashboard, use **Session Mode** (direct connection):

1. Get your database password from the Database Settings page
   - If you forgot it, click **"Reset database password"** button
2. Use this connection string format:

```bash
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.zstusykclsbiosgrtwhw.supabase.co:5432/postgres"
```

Or add to `.env` file:
```bash
echo 'DATABASE_URL=postgresql://postgres:[PASSWORD]@db.zstusykclsbiosgrtwhw.supabase.co:5432/postgres' > .env
```

Replace `[PASSWORD]` with your actual database password.

## Option 2: Use the Helper Script

If you have your database password, run:

```bash
./connect_with_password.sh 'your_database_password_here'
```

This will:
- Set DATABASE_URL environment variable
- Save it to .env file
- Test the connection automatically

## Option 3: Manual Setup

If you know your database password, use **Session Mode** (direct connection):

```bash
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.zstusykclsbiosgrtwhw.supabase.co:5432/postgres"
```

Replace `[PASSWORD]` with your actual database password.

**Note:** Session Mode is simpler and works perfectly for this application. It doesn't require connection pooling configuration.

## If You Forgot Your Password

1. Go to Supabase Dashboard → Settings → Database
2. Click **Reset database password**
3. Set a new password
4. Use the new password in your connection string

## Test the Connection

After setting DATABASE_URL:

```bash
python3 connect_supabase.py
```

This will verify the connection, initialize the schema, and test read/write operations.

## Quick Reference

Your project details:
- **Project Reference**: `zstusykclsbiosgrtwhw`
- **Project URL**: https://zstusykclsbiosgrtwhw.supabase.co
- **Dashboard**: https://supabase.com/dashboard/project/zstusykclsbiosgrtwhw

