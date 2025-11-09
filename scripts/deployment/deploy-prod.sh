#!/bin/bash
# Deploy to Production - Git-Tag-basiert
# Nur versionierte Git-Tags werden deployed!
# Tag-Pattern: rezept_version_DD_MM_YYYY

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
cd "$PROJECT_ROOT"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktion: Git-Tag validieren
validate_git_tag() {
    local tag=$1
    if [[ ! "$tag" =~ ^rezept_version_[0-9]{2}_[0-9]{2}_[0-9]{4}_[0-9]{3}$ ]]; then
        echo -e "${RED}❌ Ungültiges Tag-Format!${NC}"
        echo "   Erwartet: rezept_version_DD_MM_YYYY_NNN"
        echo "   Beispiel: rezept_version_05_11_2025_001"
        exit 1
    fi
}

# Prüfen ob Working Directory clean ist
echo "🔍 Checking Git status..."
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}❌ Working Directory ist nicht clean!${NC}"
    echo ""
    git status --short
    echo ""
    echo -e "${YELLOW}Du musst alle Änderungen committen, bevor du auf Prod deployen kannst.${NC}"
    echo ""
    echo "Uncommittete Änderungen können NICHT auf Prod deployed werden."
    echo "Das garantiert, dass nur versionierte Snapshots auf Prod landen."
    echo ""
    echo "Nächste Schritte:"
    echo "  1. git add <files>"
    echo "  2. git commit -m 'deine message'"
    echo "  3. ./scripts/tools/tag-version.sh  (erstellt automatisch einen Tag)"
    echo "  4. ./scripts/deployment/deploy-prod.sh rezept_version_DD_MM_YYYY"
    exit 1
fi

# Git-Tag aus Parameter (required!)
if [[ -z "$1" ]]; then
    echo -e "${RED}❌ Kein Git-Tag angegeben!${NC}"
    echo ""
    echo "Usage: ./scripts/deployment/deploy-prod.sh <GIT_TAG>"
    echo ""
    echo "Verfügbare Tags:"
    git tag | grep "^rezept_version_" || echo "  (noch keine Tags vorhanden)"
    echo ""
    echo "Neuen Tag erstellen:"
    echo "  ./scripts/tools/tag-version.sh"
    exit 1
fi

GIT_TAG=$1
validate_git_tag "$GIT_TAG"

# Prüfen ob Tag existiert
if ! git rev-parse "$GIT_TAG" >/dev/null 2>&1; then
    echo -e "${RED}❌ Git-Tag '$GIT_TAG' existiert nicht!${NC}"
    echo ""
    echo "Verfügbare Tags:"
    git tag | grep "^rezept_version_" || echo "  (noch keine Tags vorhanden)"
    echo ""
    echo "Neuen Tag erstellen:"
    echo "  ./scripts/tools/tag-version.sh"
    exit 1
fi

echo -e "${GREEN}✅ Git-Tag gefunden: $GIT_TAG${NC}"
echo ""

# Checkout des Git-Tags in temporäres Verzeichnis
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "📦 Exporting Git-Tag to temporary directory..."
git archive "$GIT_TAG" | tar -x -C "$TEMP_DIR"
echo ""

echo "🚀 Deploying Version: $GIT_TAG"
echo ""

# 1. Create automatic backup BEFORE deployment (PostgreSQL)
echo "📦 Step 1/6: Creating database backup..."
echo "  ⚠️  Using PostgreSQL - backup via pg_dump"
mkdir -p "$SCRIPT_DIR/../../data/prod/backups"
podman exec seaser-postgres pg_dump -U postgres rezepte > "$SCRIPT_DIR/../../data/prod/backups/rezepte-backup-before-$GIT_TAG.sql" 2>/dev/null || echo "  ℹ️  Backup skipped (PostgreSQL)"
echo ""

# 2. Build aus dem exportierten Git-Tag (nicht aus Working Directory!)
echo "🔨 Step 2/6: Building Image from Git-Tag..."
podman build --build-arg APP_VERSION=$GIT_TAG -t seaser-rezept-tagebuch:$GIT_TAG -f "$TEMP_DIR/Containerfile" "$TEMP_DIR"

# Tag als latest
echo ""
echo "🏷️  Step 3/6: Tagging as latest..."
podman tag seaser-rezept-tagebuch:$GIT_TAG seaser-rezept-tagebuch:latest

# 3. Build temporary container for migration
echo ""
echo "🔄 Step 4/6: Running database migrations..."
echo "  📍 Building temporary container for Alembic..."
podman build --build-arg APP_VERSION=$GIT_TAG -t seaser-rezept-tagebuch:migration-temp -f "$TEMP_DIR/Containerfile" "$TEMP_DIR"

echo "  📍 Running Alembic upgrade head on PROD DB..."
podman run --rm --network seaser-network \
  -v "$TEMP_DIR/alembic-prod.ini:/app/alembic.ini" \
  seaser-rezept-tagebuch:migration-temp \
  alembic upgrade head

echo "  ✅ Migrations erfolgreich angewendet"
podman rmi seaser-rezept-tagebuch:migration-temp 2>/dev/null || true

# 4. Prod Container neu starten
echo ""
echo "🔄 Step 5/6: Restarting Production Container..."
podman stop seaser-rezept-tagebuch 2>/dev/null || true
podman rm seaser-rezept-tagebuch 2>/dev/null || true

podman run -d --name seaser-rezept-tagebuch --network seaser-network -e DB_TYPE=postgresql -e POSTGRES_HOST=seaser-postgres -e POSTGRES_DB=rezepte -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=seaser -e DEEPL_API_KEY=a35ce617-15e4-46b2-8e99-a97bd1e6a853:fx -v /home/gabor/easer_projekte/rezept-tagebuch/data/prod:/data localhost/seaser-rezept-tagebuch:latest

# Systemd Service aktualisieren
echo ""
echo "⚙️  Step 6/6: Updating systemd service..."
podman generate systemd --new --name seaser-rezept-tagebuch > /home/gabor/.config/systemd/user/container-seaser-rezept-tagebuch.service
systemctl --user daemon-reload
systemctl --user enable container-seaser-rezept-tagebuch.service

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Production Deployment erfolgreich!${NC}"
echo "📦 Git-Tag: $GIT_TAG"
echo "📍 URL: http://192.168.2.139:8000/rezept-tagebuch/"
echo "🗄️  Database: Migrated to latest schema"
echo ""
echo "Container Status:"
podman ps | grep seaser-rezept-tagebuch
echo ""
echo "Available versions:"
podman images | grep seaser-rezept-tagebuch | head -5
echo ""
echo "💡 Rollback available via: ./scripts/deployment/rollback.sh $GIT_TAG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
