#!/bin/bash
# Test Migration auf TEST-Umgebung mit Git-Tag-Freigabe
# Workflow:
# 1. TEST Container aus Git-Tag bauen & starten
# 2. Alembic Migration auf TEST DB
# 3. Automatische Tests laufen lassen
# 4. Bei Erfolg: Tag wird für PROD freigegeben
# 5. Optional: DEV Container aktualisieren

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
cd "$PROJECT_ROOT"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktion: Git-Tag validieren
validate_git_tag() {
    local tag=$1
    if [[ ! "$tag" =~ ^rezept_version_[0-9]{2}_[0-9]{2}_[0-9]{4}_[0-9]{3}$ ]]; then
        echo -e "${RED}❌ Ungültiges Tag-Format!${NC}"
        echo "   Erwartet: rezept_version_DD_MM_YYYY_NNN"
        echo "   Beispiel: rezept_version_09_11_2025_001"
        exit 1
    fi
}

# Git-Tag aus Parameter (required!)
if [[ -z "$1" ]]; then
    echo -e "${RED}❌ Kein Git-Tag angegeben!${NC}"
    echo ""
    echo "Usage: ./scripts/database/test-migration.sh <GIT_TAG>"
    echo ""
    echo "Verfügbare Tags:"
    git tag | grep "^rezept_version_" | tail -5 || echo "  (noch keine Tags vorhanden)"
    echo ""
    echo "Neuen Tag erstellen:"
    echo "  git tag -a rezept_version_DD_MM_YYYY_NNN -m 'Release message'"
    exit 1
fi

GIT_TAG=$1
validate_git_tag "$GIT_TAG"

# Prüfen ob Tag existiert
if ! git rev-parse "$GIT_TAG" >/dev/null 2>&1; then
    echo -e "${RED}❌ Git-Tag '$GIT_TAG' existiert nicht!${NC}"
    echo ""
    echo "Verfügbare Tags:"
    git tag | grep "^rezept_version_" | tail -5 || echo "  (noch keine Tags vorhanden)"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🧪 TEST MIGRATION WORKFLOW${NC}"
echo -e "${GREEN}📦 Git-Tag: $GIT_TAG${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Checkout des Git-Tags in temporäres Verzeichnis
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "📦 Exporting Git-Tag to temporary directory..."
git archive "$GIT_TAG" | tar -x -C "$TEMP_DIR"
echo ""

# Step 1: Build TEST Container aus Git-Tag
echo -e "${BLUE}🔨 Step 1/6: Building TEST Container from Git-Tag...${NC}"
podman build -t seaser-rezept-tagebuch:test -f "$TEMP_DIR/Containerfile" "$TEMP_DIR"
echo ""

# Step 2: Start TEST Container
echo -e "${BLUE}🚀 Step 2/6: Starting TEST Container...${NC}"
podman stop seaser-rezept-tagebuch-test 2>/dev/null || true
podman rm seaser-rezept-tagebuch-test 2>/dev/null || true

podman run -d --name seaser-rezept-tagebuch-test \
  --network seaser-network \
  -e DB_TYPE=postgresql \
  -e TESTING_MODE=true \
  -e POSTGRES_HOST=seaser-postgres-test \
  -e POSTGRES_DB=rezepte_test \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=test \
  -e DEEPL_API_KEY=a35ce617-15e4-46b2-8e99-a97bd1e6a853:fx \
  -v "$PROJECT_ROOT/data/test:/data" \
  localhost/seaser-rezept-tagebuch:test

echo -e "${GREEN}✅ TEST Container gestartet${NC}"
echo ""

# Step 3: Run Alembic Migration auf TEST DB
echo -e "${BLUE}🔄 Step 3/6: Running Alembic Migration auf TEST DB...${NC}"
echo "  📍 Database: rezepte_test"
echo "  📍 Config: alembic-test.ini"
echo ""

# Execute alembic upgrade inside the TEST container
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini upgrade head

echo ""
echo -e "${GREEN}✅ Migration auf TEST erfolgreich${NC}"
echo ""

# Step 4: Run Automated Tests
echo -e "${BLUE}🧪 Step 4/6: Running Automated Tests...${NC}"
echo ""

# Run pytest inside the TEST container
TEST_EXIT_CODE=0
podman exec seaser-rezept-tagebuch-test pytest -v || TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Alle Tests erfolgreich!${NC}"
else
    echo -e "${RED}❌ Tests fehlgeschlagen!${NC}"
    echo ""
    echo -e "${YELLOW}Migration auf TEST war erfolgreich, aber Tests sind fehlgeschlagen.${NC}"
    echo -e "${YELLOW}Bitte Fehler beheben bevor du auf DEV/PROD deployest.${NC}"
    echo ""
    echo "TEST Container läuft weiter für Debugging:"
    echo "  podman logs seaser-rezept-tagebuch-test"
    echo "  podman exec -it seaser-rezept-tagebuch-test bash"
    exit 1
fi

echo ""

# Step 5: Tag für PROD freigeben
echo -e "${BLUE}✅ Step 5/6: Freigabe für PROD Deployment...${NC}"
echo ""

# Freigabe-File erstellen/updaten
APPROVAL_FILE="$PROJECT_ROOT/.test-approvals"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_HASH=$(git rev-parse "$GIT_TAG")

echo "$GIT_TAG|$COMMIT_HASH|$TIMESTAMP|SUCCESS" >> "$APPROVAL_FILE"

echo -e "${GREEN}✅ Tag '$GIT_TAG' für PROD freigegeben${NC}"
echo "   Freigabe gespeichert in: .test-approvals"
echo ""

# Step 6: Update DEV Container
echo -e "${BLUE}🔄 Step 6/6: Update DEV Container mit neuer Migration...${NC}"
echo ""
echo "Möchtest du jetzt DEV Container aktualisieren? [y/N]"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔨 Building DEV Container..."
    "$SCRIPT_DIR/../deployment/build-dev.sh"
    echo ""
    echo -e "${GREEN}✅ DEV Container aktualisiert${NC}"
    echo "📍 URL: http://192.168.2.139:8001/rezept-tagebuch/"
else
    echo ""
    echo -e "${YELLOW}⏭️  DEV Update übersprungen${NC}"
    echo "Du kannst später manuell updaten:"
    echo "  ./scripts/deployment/build-dev.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ TEST MIGRATION ERFOLGREICH!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Migration auf TEST angewendet"
echo "✅ Alle Tests bestanden"
echo -e "${GREEN}✅ Tag '$GIT_TAG' für PROD freigegeben${NC}"
echo ""
echo "Nächste Schritte:"
echo "  1. Teste manuell in DEV: http://192.168.2.139:8001/rezept-tagebuch/"
echo "  2. Bei Erfolg: PROD Deployment"
echo "     ./scripts/deployment/deploy-prod.sh $GIT_TAG"
echo ""
echo -e "${YELLOW}⚠️  Dieser Tag kann jetzt auf PROD deployed werden!${NC}"
echo ""
echo "Test Container Status:"
podman ps | grep seaser-rezept-tagebuch-test
echo ""
