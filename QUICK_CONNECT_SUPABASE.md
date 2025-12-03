# Quick Connect to Supabase

## Option 1: Set Environment Variable (Current Session)

```bash
export DATABASE_URL="postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres"
```

Then test the connection:
```bash
python3 connect_supabase.py
```

## Option 2: Use Setup Script

```bash
./setup_supabase.sh
```

This will prompt you for your connection string and test it.

## Option 3: Set in .env File (Recommended for Development)

Create a `.env` file in the project root:

```bash
echo 'DATABASE_URL=postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres' > .env
```

The application will automatically load it (python-dotenv is already configured).

## Getting Your Supabase Connection String

1. Go to your Supabase project dashboard
2. Click **Settings** (gear icon) → **Database**
3. Scroll to **Connection string**
4. Choose:
   - **Session mode** (port 5432) - for direct connections
   - **Transaction mode** (port 6543) - for connection pooling (recommended for serverless)

## Test Connection

After setting DATABASE_URL, run:

```bash
python3 connect_supabase.py
```

This will:
- ✓ Test the connection
- ✓ Initialize the database schema
- ✓ Test write operations
- ✓ Test read operations

## Make It Permanent

To make DATABASE_URL persist across terminal sessions, add to your shell profile:

**For zsh (macOS default):**
```bash
echo 'export DATABASE_URL="your_connection_string_here"' >> ~/.zshrc
source ~/.zshrc
```

**For bash:**
```bash
echo 'export DATABASE_URL="your_connection_string_here"' >> ~/.bashrc
source ~/.bashrc
```

