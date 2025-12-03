# Simple Supabase Connection Setup

Since Transaction Mode isn't available in your dashboard, we'll use **Session Mode** (direct connection), which is simpler and works perfectly for this application.

## Quick Setup (3 Steps)

### Step 1: Get Your Database Password

You're already on the Database Settings page. You can see the "Database password" section with a "Reset database password" button.

**Option A: Use existing password** (if you remember it)
- Use the password you set when creating the project

**Option B: Reset password** (if you forgot it)
1. Click **"Reset database password"** button
2. Set a new password (save it securely!)
3. Use this new password

### Step 2: Set Connection String

Use this format (replace `[PASSWORD]` with your actual password):

```bash
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.zstusykclsbiosgrtwhw.supabase.co:5432/postgres"
```

**Or use the helper script:**
```bash
./connect_with_password.sh 'your_password_here'
```

**Or create `.env` file:**
```bash
echo 'DATABASE_URL=postgresql://postgres:[PASSWORD]@db.zstusykclsbiosgrtwhw.supabase.co:5432/postgres' > .env
```

### Step 3: Test Connection

```bash
python3 connect_supabase.py
```

You should see:
```
✓ ALL TESTS PASSED - Supabase connection is working!
```

## Connection String Format

**Session Mode (Direct Connection):**
```
postgresql://postgres:[PASSWORD]@db.zstusykclsbiosgrtwhw.supabase.co:5432/postgres
```

Where:
- `[PASSWORD]` = Your database password
- `zstusykclsbiosgrtwhw` = Your project reference (already filled in)
- `5432` = Standard PostgreSQL port

## Example

If your password is `MySecurePassword123`, the connection string would be:

```bash
export DATABASE_URL="postgresql://postgres:MySecurePassword123@db.zstusykclsbiosgrtwhw.supabase.co:5432/postgres"
```

## That's It!

Once connected, the application will:
- ✓ Create the `signals` table automatically
- ✓ Set up indexes for fast queries
- ✓ Be ready to store trading signals

## Need Help?

- See `connect_supabase.py` - Run this to test your connection
- See `GET_CONNECTION_STRING.md` - More detailed instructions
- Check Supabase docs: https://supabase.com/docs/guides/database/connecting-to-postgres

