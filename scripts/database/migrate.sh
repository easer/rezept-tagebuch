#!/bin/bash
# Database Migration Helper Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function show_help() {
    echo "Usage: ./migrate.sh [COMMAND] [ENV]"
    echo ""
    echo "Commands:"
    echo "  upgrade [env]   - Apply all pending migrations (default: dev)"
    echo "  downgrade [env] - Rollback last migration"
    echo "  current [env]   - Show current migration version"
    echo "  history [env]   - Show migration history"
    echo "  create <name>   - Create new migration file"
    echo ""
    echo "Environments:"
    echo "  dev   - Development DB (/home/gabor/easer_projekte/rezept-tagebuch-data/rezepte.db)"
    echo "  prod  - Production DB (/home/gabor/data/rezept-tagebuch/rezepte.db)"
    echo ""
    echo "Examples:"
    echo "  ./migrate.sh upgrade dev     # Apply migrations to dev DB"
    echo "  ./migrate.sh upgrade prod    # Apply migrations to prod DB"
    echo "  ./migrate.sh create add_kategorie  # Create new migration"
}

function set_db_path() {
    local env=$1
    if [ "$env" = "prod" ]; then
        export DB_PATH="/home/gabor/data/rezept-tagebuch/rezepte.db"
        echo -e "${YELLOW}Target: PRODUCTION DB${NC}"
    else
        export DB_PATH="/home/gabor/easer_projekte/rezept-tagebuch-data/rezepte.db"
        echo -e "${GREEN}Target: DEVELOPMENT DB${NC}"
    fi
    echo "DB Path: $DB_PATH"
    echo ""
}

case "$1" in
    upgrade)
        ENV=${2:-dev}
        set_db_path "$ENV"
        echo "📈 Applying migrations..."
        python3 -m alembic upgrade head
        echo -e "${GREEN}✅ Migrations applied successfully${NC}"
        ;;

    downgrade)
        ENV=${2:-dev}
        set_db_path "$ENV"
        echo "📉 Rolling back last migration..."
        python3 -m alembic downgrade -1
        echo -e "${GREEN}✅ Migration rolled back${NC}"
        ;;

    current)
        ENV=${2:-dev}
        set_db_path "$ENV"
        echo "📍 Current migration version:"
        python3 -m alembic current
        ;;

    history)
        ENV=${2:-dev}
        set_db_path "$ENV"
        echo "📜 Migration history:"
        python3 -m alembic history
        ;;

    create)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Error: Migration name required${NC}"
            echo "Usage: ./migrate.sh create <name>"
            exit 1
        fi
        echo "📝 Creating new migration: $2"
        python3 -m alembic revision -m "$2"
        echo -e "${GREEN}✅ Migration file created in migrations/versions/${NC}"
        ;;

    help|--help|-h)
        show_help
        ;;

    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
