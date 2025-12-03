# Supabase Connection - Ready to Connect

## ✅ What's Been Set Up

1. **Connection Test Script** (`connect_supabase.py`)
   - Tests database connection
   - Initializes database schema automatically
   - Tests write and read operations
   - Provides helpful error messages

2. **Setup Helper Script** (`setup_supabase.sh`)
   - Interactive script to set DATABASE_URL
   - Tests connection after setting

3. **Quick Reference Guide** (`QUICK_CONNECT_SUPABASE.md`)
   - Multiple ways to set up the connection
   - Instructions for getting your connection string

## 🚀 Next Steps

### Step 1: Set Your DATABASE_URL

You have your Supabase connection string. Choose one method:

**Method A: Environment Variable (Current Session)**
```bash
export DATABASE_URL="postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres"
```

**Method B: Interactive Setup Script**
```bash
./setup_supabase.sh
```

**Method C: .env File (Recommended)**
```bash
echo 'DATABASE_URL=postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres' > .env
```

Replace `[password]` and `[ref]` with your actual Supabase credentials.

### Step 2: Test the Connection

Run the connection test:

```bash
python3 connect_supabase.py
```

This will:
- ✓ Verify the connection works
- ✓ Create the `signals` table and indexes
- ✓ Test saving a sample signal
- ✓ Test retrieving signals

### Step 3: Verify Success

You should see:
```
✓ ALL TESTS PASSED - Supabase connection is working!
```

## 📋 What Gets Created

The database schema includes:

- **signals table** with columns:
  - id (primary key)
  - timestamp
  - symbol
  - direction
  - confidence
  - prob_long
  - entry_price
  - tp_price
  - sl_price
  - atr
  - risk_reward_ratio
  - created_at

- **Indexes** for fast queries:
  - idx_signals_timestamp
  - idx_signals_symbol
  - idx_signals_created_at

## 🎯 After Connection is Working

Once connected, you can:

1. **Run the pipeline** to generate signals:
   ```bash
   python run_pipeline.py
   ```

2. **Start the dashboard** to view signals:
   ```bash
   python app.py
   ```

3. **Generate signals manually**:
   ```bash
   python generate_signals.py --model lgbm_optimized --confidence 0.5
   ```

## 🔍 Troubleshooting

**Connection fails?**
- Verify your connection string is correct
- Check Supabase dashboard to ensure database is running
- Verify your IP isn't blocked (check Supabase network settings)
- Try connection pooling mode if session mode doesn't work

**Schema already exists?**
- That's OK! The script uses `CREATE TABLE IF NOT EXISTS`
- It will skip creation if tables already exist

**Need help?**
- See `SUPABASE_SETUP.md` for detailed setup instructions
- See `QUICK_CONNECT_SUPABASE.md` for quick reference

