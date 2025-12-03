#!/bin/bash
# Setup Supabase connection using project URL and API key

PROJECT_URL="https://zstusykclsbiosgrtwhw.supabase.co"
PROJECT_REF="zstusykclsbiosgrtwhw"
API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpzdHVzeWtjbHNiaW9zZ3J0d2h3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ3ODYzMDcsImV4cCI6MjA4MDM2MjMwN30.qyT4vJLEyP3h-GSa-Tq_10iJwIJgmxUiEQgSIsD0XvQ"

echo "=========================================="
echo "Setting up Supabase connection"
echo "=========================================="
echo "Project URL: $PROJECT_URL"
echo "Project Reference: $PROJECT_REF"
echo ""

# Save project URL and API key to .env
if [ -f .env ]; then
    # Update existing .env
    if ! grep -q "SUPABASE_URL=" .env; then
        echo "" >> .env
        echo "# Supabase Configuration" >> .env
        echo "SUPABASE_URL=$PROJECT_URL" >> .env
        echo "SUPABASE_KEY=$API_KEY" >> .env
    fi
else
    # Create new .env
    cat > .env << EOF
# Supabase Configuration
SUPABASE_URL=$PROJECT_URL
SUPABASE_KEY=$API_KEY

# Database Connection (set this with your database password)
# DATABASE_URL=postgresql://postgres:[PASSWORD]@db.$PROJECT_REF.supabase.co:5432/postgres
EOF
fi

echo "✓ Saved Supabase URL and API key to .env file"
echo ""

# Check if password is provided as argument
if [ -n "$1" ]; then
    PASSWORD="$1"
    # URL-encode the password for connection string
    # Using Python to properly encode special characters
    ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$PASSWORD', safe=''))")
    CONNECTION_STRING="postgresql://postgres:${ENCODED_PASSWORD}@db.${PROJECT_REF}.supabase.co:5432/postgres"
    
    # Update .env with DATABASE_URL
    if grep -q "DATABASE_URL=" .env; then
        # Update existing DATABASE_URL
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=$CONNECTION_STRING|" .env
        else
            # Linux
            sed -i "s|DATABASE_URL=.*|DATABASE_URL=$CONNECTION_STRING|" .env
        fi
    else
        # Add DATABASE_URL
        echo "DATABASE_URL=$CONNECTION_STRING" >> .env
    fi
    
    export DATABASE_URL="$CONNECTION_STRING"
    echo "✓ DATABASE_URL set using project URL"
    echo "✓ Connection string: postgresql://postgres:***@db.$PROJECT_REF.supabase.co:5432/postgres"
    echo ""
    echo "Testing connection..."
    python3 connect_supabase.py
else
    echo "To complete the connection, you need your database password."
    echo ""
    echo "Option 1: Run with password as argument:"
    echo "  ./setup_from_project_url.sh 'your_database_password'"
    echo ""
    echo "Option 2: Set DATABASE_URL manually:"
    echo "  export DATABASE_URL='postgresql://postgres:[PASSWORD]@db.$PROJECT_REF.supabase.co:5432/postgres'"
    echo "  python3 connect_supabase.py"
    echo ""
    echo "Option 3: Add to .env file:"
    echo "  echo 'DATABASE_URL=postgresql://postgres:[PASSWORD]@db.$PROJECT_REF.supabase.co:5432/postgres' >> .env"
    echo ""
    echo "Your project is configured with:"
    echo "  - Project URL: $PROJECT_URL"
    echo "  - API Key: Saved to .env"
    echo "  - Connection format: postgresql://postgres:[PASSWORD]@db.$PROJECT_REF.supabase.co:5432/postgres"
fi

