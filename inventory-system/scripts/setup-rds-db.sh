#!/bin/bash
# setup-rds-db.sh - Create database on RDS PostgreSQL
# Usage: DB_PASSWORD=your_password ./scripts/setup-rds-db.sh

set -e

DB_HOST="${DB_HOST:-openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-tang_inventory}"
DB_PASSWORD="${DB_PASSWORD}"

if [ -z "$DB_PASSWORD" ]; then
    echo "❌ Error: DB_PASSWORD environment variable is required"
    echo "Usage: DB_PASSWORD=your_password ./scripts/setup-rds-db.sh"
    exit 1
fi

echo "🔌 Connecting to RDS: $DB_HOST"
echo "👤 User: $DB_USER"
echo "📦 Target Database: $DB_NAME"
echo ""

# Test connection first
echo "Testing connection..."
if ! PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -c "SELECT version();" > /dev/null 2>&1; then
    echo "❌ Connection failed. Please check:"
    echo "   1. DB_PASSWORD is correct"
    echo "   2. RDS security group allows connection from this IP"
    echo "   3. RDS instance is available"
    exit 1
fi

echo "✅ Connection successful"
echo ""

# Check if database exists
echo "Checking if database '$DB_NAME' exists..."
DB_EXISTS=$(PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null)

if [ "$DB_EXISTS" = "1" ]; then
    echo "✅ Database '$DB_NAME' already exists"
else
    echo "🆕 Creating database '$DB_NAME'..."
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d postgres \
        -c "CREATE DATABASE $DB_NAME;"
    echo "✅ Database created successfully"
fi

echo ""
echo "📊 Database Information:"
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -c "\l $DB_NAME"

echo ""
echo "✅ RDS Database Setup Complete!"
echo ""
echo "Next steps:"
echo "  1. Update .env with your DB_PASSWORD"
echo "  2. Run: docker-compose up -d"
echo "  3. The backend will auto-run migrations"
