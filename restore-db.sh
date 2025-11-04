#!/bin/bash
# Database Restore Script with Migration Version Check

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

function show_help() {
    echo "Usage: ./restore-db.sh [ENV] [BACKUP_FILE]"
    echo ""
    echo "Environments:"
    echo "  dev   - Restore to development DB"
    echo "  prod  - Restore to production DB"
    echo ""
    echo "If BACKUP_FILE is not specified, shows available backups."
    echo ""
    echo "Examples:"
    echo "  ./restore-db.sh prod                           # List backups"
    echo "  ./restore-db.sh prod rezepte-20251104-*.db     # Restore specific backup"
}

ENV=$1

if [ -z "$ENV" ]; then
    show_help
    exit 1
fi

if [ "$ENV" = "dev" ]; then
    DB_PATH="/home/gabor/easer_projekte/rezept-tagebuch-data/rezepte.db"
    BACKUP_DIR="/home/gabor/easer_projekte/rezept-tagebuch-data/backups"
    export DB_PATH
elif [ "$ENV" = "prod" ]; then
    DB_PATH="/home/gabor/data/rezept-tagebuch/rezepte.db"
    BACKUP_DIR="/home/gabor/data/rezept-tagebuch/backups"
    export DB_PATH
else
    echo -e "${RED}❌ Invalid environment: $ENV${NC}"
    show_help
    exit 1
fi

# If no backup file specified, list available backups
if [ -z "$2" ]; then
    echo "📋 Available backups in $BACKUP_DIR:"
    echo ""

    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR"/rezepte-*.db 2>/dev/null)" ]; then
        echo "  No backups found"
        exit 0
    fi

    ls -lth "$BACKUP_DIR"/rezepte-*.db | awk '{print $9}' | while read -r backup; do
        basename_file=$(basename "$backup")
        if [ -f "${backup}.meta" ]; then
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "File: $basename_file"
            cat "${backup}.meta" | sed 's/^/  /'
        else
            echo "  $basename_file"
        fi
    done
    echo ""
    echo "To restore, run:"
    echo "  ./restore-db.sh $ENV <backup-filename>"
    exit 0
fi

BACKUP_FILE="$2"

# If backup file is just a filename, prepend backup dir
if [[ "$BACKUP_FILE" != /* ]]; then
    BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
fi

# Check if backup exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup not found: $BACKUP_FILE${NC}"
    exit 1
fi

# Get current migration version
cd /home/gabor/easer_projekte/rezept-tagebuch
CURRENT_MIGRATION=$(alembic current 2>/dev/null | grep -oP '(?<=\()[^\)]+' || echo "none")

# Get backup migration version
if [ -f "${BACKUP_FILE}.meta" ]; then
    BACKUP_MIGRATION=$(grep "migration_version:" "${BACKUP_FILE}.meta" | cut -d' ' -f2)
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Backup Metadata:"
    cat "${BACKUP_FILE}.meta"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    BACKUP_MIGRATION="unknown"
    echo -e "${YELLOW}⚠️  Warning: No metadata file found for backup${NC}"
fi

echo ""
echo -e "${YELLOW}⚠️  RESTORE CONFIRMATION${NC}"
echo "  Source: $BACKUP_FILE"
echo "  Target: $DB_PATH"
echo "  Current Migration: $CURRENT_MIGRATION"
echo "  Backup Migration:  $BACKUP_MIGRATION"
echo ""

# Warn if migration versions don't match
if [ "$CURRENT_MIGRATION" != "$BACKUP_MIGRATION" ] && [ "$BACKUP_MIGRATION" != "unknown" ]; then
    echo -e "${RED}⚠️  WARNING: Migration version mismatch!${NC}"
    echo "  This backup was created with a different schema version."
    echo "  Restoring may cause issues if schema has changed."
    echo ""
fi

read -p "Are you sure you want to restore? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Create safety backup of current DB
if [ -f "$DB_PATH" ]; then
    SAFETY_BACKUP="$DB_PATH.before-restore-$(date +%Y%m%d-%H%M%S)"
    echo ""
    echo "🔒 Creating safety backup of current DB..."
    cp "$DB_PATH" "$SAFETY_BACKUP"
    echo "  Safety backup: $SAFETY_BACKUP"
fi

# Restore backup
echo ""
echo "📥 Restoring backup..."
cp "$BACKUP_FILE" "$DB_PATH"

echo -e "${GREEN}✅ Database restored successfully${NC}"
echo ""
echo "Next steps:"
echo "  1. Verify database integrity"
echo "  2. Check migration version: ./migrate.sh current $ENV"
if [ "$CURRENT_MIGRATION" != "$BACKUP_MIGRATION" ]; then
    echo "  3. Run migrations if needed: ./migrate.sh upgrade $ENV"
fi
