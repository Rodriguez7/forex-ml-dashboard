#!/bin/bash
# Quick setup script for Supabase connection

echo "=========================================="
echo "Supabase Connection Setup"
echo "=========================================="
echo ""
echo "Please provide your Supabase connection string."
echo "You can find it in: Supabase Dashboard → Settings → Database → Connection string"
echo ""
echo "Format examples:"
echo "  Session mode: postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres"
echo "  Pooling mode: postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"
echo ""
read -p "Enter your DATABASE_URL: " db_url

if [ -z "$db_url" ]; then
    echo "❌ No connection string provided. Exiting."
    exit 1
fi

# Export for current session
export DATABASE_URL="$db_url"
echo ""
echo "✓ DATABASE_URL set for current session"
echo ""
echo "To make this permanent, add to your shell profile (~/.zshrc or ~/.bashrc):"
echo "  export DATABASE_URL=\"$db_url\""
echo ""
echo "Or create a .env file in the project root:"
echo "  echo 'DATABASE_URL=$db_url' > .env"
echo ""
echo "Testing connection..."
python3 connect_supabase.py

