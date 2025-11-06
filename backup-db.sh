#!/bin/bash
# Database Backup Script with Migration Version Tracking

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

function show_help() {
    echo "Usage: ./backup-db.sh [ENV] [DESCRIPTION]"
    echo ""
    echo "Environments:"
    echo "  dev   - Backup development DB"
    echo "  prod  - Backup production DB (default)"
    echo ""
    echo "Examples:"
    echo "  ./backup-db.sh prod              # Auto backup before deployment"
    echo "  ./backup-db.sh prod \"before v2.2\"  # Manual backup with description"
}

ENV=${1:-prod}
DESCRIPTION=${2:-"auto"}
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

if [ "$ENV" = "dev" ]; then
    DB_PATH="/home/gabor/easer_projekte/rezept-tagebuch/data/dev/rezepte.db"
    BACKUP_DIR="/home/gabor/easer_projekte/rezept-tagebuch/data/dev/backups"
    export DB_PATH
else
    DB_PATH="/home/gabor/easer_projekte/rezept-tagebuch/data/prod/rezepte.db"
    BACKUP_DIR="/home/gabor/easer_projekte/rezept-tagebuch/data/prod/backups"
    export DB_PATH
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if DB exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}❌ Database not found: $DB_PATH${NC}"
    exit 1
fi

# Get current migration version
cd /home/gabor/easer_projekte/rezept-tagebuch
MIGRATION_VERSION=$(alembic current 2>/dev/null | grep -oP '(?<=\()[^\)]+' || echo "none")

# Backup filename
BACKUP_FILE="$BACKUP_DIR/rezepte-${TIMESTAMP}-${MIGRATION_VERSION}-${DESCRIPTION}.db"

# Create backup
echo -e "${YELLOW}📦 Creating backup...${NC}"
echo "  Source: $DB_PATH"
echo "  Target: $BACKUP_FILE"
echo "  Migration: $MIGRATION_VERSION"
echo ""

cp "$DB_PATH" "$BACKUP_FILE"

# Create metadata file
cat > "${BACKUP_FILE}.meta" <<EOF
timestamp: $TIMESTAMP
environment: $ENV
migration_version: $MIGRATION_VERSION
description: $DESCRIPTION
db_size: $(du -h "$DB_PATH" | cut -f1)
EOF

echo -e "${GREEN}✅ Backup created successfully${NC}"
echo ""

# Show backup info
echo "Backup Details:"
cat "${BACKUP_FILE}.meta"
echo ""

# Cleanup old backups (keep last 10)
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/rezepte-*.db 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 10 ]; then
    echo "🧹 Cleaning up old backups (keeping last 10)..."
    ls -1t "$BACKUP_DIR"/rezepte-*.db | tail -n +11 | while read -r old_backup; do
        echo "  Removing: $(basename "$old_backup")"
        rm -f "$old_backup" "${old_backup}.meta"
    done
    echo -e "${GREEN}✅ Cleanup complete${NC}"
fi

echo ""
echo "Available backups in $BACKUP_DIR:"
ls -lth "$BACKUP_DIR"/rezepte-*.db | head -10
