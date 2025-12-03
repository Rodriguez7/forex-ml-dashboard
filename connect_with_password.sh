#!/bin/bash
# Connect to Supabase with password as argument

if [ -z "$1" ]; then
    echo "Usage: ./connect_with_password.sh <database_password>"
    echo ""
    echo "Example:"
    echo "  ./connect_with_password.sh 'your_password_here'"
    echo ""
    echo "Or set as environment variable:"
    echo "  export SUPABASE_PASSWORD='your_password'"
    echo "  ./connect_with_password.sh"
    exit 1
fi

PASSWORD="${1:-$SUPABASE_PASSWORD}"
PROJECT_REF="zstusykclsbiosgrtwhw"

# Use session mode (direct connection) - simpler and always available
CONNECTION_STRING="postgresql://postgres:${PASSWORD}@db.${PROJECT_REF}.supabase.co:5432/postgres"

echo "Setting DATABASE_URL..."
export DATABASE_URL="$CONNECTION_STRING"

# Also save to .env file
echo "DATABASE_URL=$CONNECTION_STRING" >> .env
echo "✓ DATABASE_URL set and saved to .env file"

echo ""
echo "Testing connection..."
python3 connect_supabase.py

