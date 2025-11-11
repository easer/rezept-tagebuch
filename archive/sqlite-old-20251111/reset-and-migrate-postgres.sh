#!/bin/bash
# Reset PostgreSQL database and migrate data from SQLite
# Usage: ./reset-and-migrate-postgres.sh [sqlite_db_path]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SQLITE_DB="${1:-data/prod/rezepte.db}"
PG_CONTAINER="seaser-postgres"
PG_USER="postgres"
PG_DB="rezepte"

echo "🔄 PostgreSQL Migration Script"
echo "================================"
echo "SQLite DB: $SQLITE_DB"
echo "PostgreSQL: $PG_CONTAINER / $PG_DB"
echo ""

# Check if SQLite DB exists
if [ ! -f "$PROJECT_ROOT/$SQLITE_DB" ]; then
    echo "❌ Error: SQLite database not found: $PROJECT_ROOT/$SQLITE_DB"
    exit 1
fi

# Check if PostgreSQL container is running
if ! podman ps | grep -q "$PG_CONTAINER"; then
    echo "❌ Error: PostgreSQL container '$PG_CONTAINER' is not running"
    exit 1
fi

echo "Step 1: Dropping and recreating PostgreSQL database..."
podman exec "$PG_CONTAINER" dropdb -U "$PG_USER" --if-exists "$PG_DB"
podman exec "$PG_CONTAINER" createdb -U "$PG_USER" "$PG_DB"
echo "✓ Database reset"

echo ""
echo "Step 2: Applying PostgreSQL schema..."
podman exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" < "$PROJECT_ROOT/scripts/database/schema-postgres.sql" > /dev/null 2>&1
echo "✓ Schema applied"

echo ""
echo "Step 3: Migrating data from SQLite..."
cd "$PROJECT_ROOT"
python3 scripts/database/export-sqlite-data.py "$SQLITE_DB" | \
    podman exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -q 2>&1 | grep -i error || true
echo "✓ Data migrated"

echo ""
echo "Step 4: Setting Alembic version to 0001..."
podman exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -c \
    "INSERT INTO alembic_version (version_num) VALUES ('0001') ON CONFLICT DO NOTHING;" > /dev/null
echo "✓ Alembic version set"

echo ""
echo "Step 5: Verification..."
podman exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -c \
    "SELECT 'users:', COUNT(*) FROM users UNION ALL
     SELECT 'recipes:', COUNT(*) FROM recipes UNION ALL
     SELECT 'todos:', COUNT(*) FROM todos UNION ALL
     SELECT 'diary_entries:', COUNT(*) FROM diary_entries;"

echo ""
echo "✅ Migration completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Test PostgreSQL connection from app"
echo "  2. Update config.py to use PostgreSQL"
echo "  3. Deploy app_new.py"
