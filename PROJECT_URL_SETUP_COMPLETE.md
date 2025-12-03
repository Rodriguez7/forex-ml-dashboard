# Supabase Connection Setup - Using Project URL

## ✅ What's Been Configured

Your Supabase project details have been automatically configured:

- **Project URL**: `https://zstusykclsbiosgrtwhw.supabase.co`
- **Project Reference**: `zstusykclsbiosgrtwhw`
- **API Key**: Saved to `.env` file
- **Connection Format**: Automatically constructed from project URL

## 📋 Current Status

The project URL and API key have been saved to your `.env` file. 

To complete the database connection, you just need to add your **database password**.

## 🚀 Quick Connect (3 Options)

### Option 1: Use the Setup Script (Easiest)

```bash
./setup_from_project_url.sh 'your_database_password'
```

This will:
- ✓ Set DATABASE_URL using your project URL
- ✓ Save it to .env file
- ✓ Test the connection automatically

### Option 2: Set Environment Variable

```bash
export DATABASE_URL="postgresql://postgres:your_password@db.zstusykclsbiosgrtwhw.supabase.co:5432/postgres"
python3 connect_supabase.py
```

### Option 3: Add to .env File

```bash
echo 'DATABASE_URL=postgresql://postgres:your_password@db.zstusykclsbiosgrtwhw.supabase.co:5432/postgres' >> .env
python3 connect_supabase.py
```

## 🔑 Getting Your Database Password

1. Go to: https://supabase.com/dashboard/project/zstusykclsbiosgrtwhw/settings/database
2. In the "Database password" section, you can:
   - Use your existing password (if you remember it)
   - Click **"Reset database password"** to set a new one

## 📝 Connection String Format

The connection string is automatically constructed from your project URL:

```
postgresql://postgres:[PASSWORD]@db.zstusykclsbiosgrtwhw.supabase.co:5432/postgres
```

Just replace `[PASSWORD]` with your actual database password.

## ✅ After Connection

Once you provide your password and run the connection test, you'll have:

- ✓ Database connection configured
- ✓ Schema initialized (signals table created)
- ✓ Ready to store trading signals

## 🎯 Next Steps

1. **Get your database password** from Supabase dashboard
2. **Run the setup script**: `./setup_from_project_url.sh 'your_password'`
3. **Verify success**: You should see "ALL TESTS PASSED"
4. **Start using**: Run `python3 run_pipeline.py` to generate signals

## 📁 Files Created

- `setup_from_project_url.sh` - Automated setup script using project URL
- `.env` - Contains your Supabase URL and API key (password needed to complete)

## 💡 Note

The project URL and API key are already saved. You only need to provide the database password to complete the connection. The connection string format is automatically constructed from your project URL, so you don't need to manually figure out the host or port.

