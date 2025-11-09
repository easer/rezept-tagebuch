#!/bin/bash
# Test Migration auf TEST-Umgebung mit Commit-Hash-Freigabe
# Workflow:
# 1. TEST Container aus Working Dir (HEAD) bauen & starten
# 2. Alembic Migration auf TEST DB
# 3. Automatische Tests laufen lassen (inkl. Feature Tests)
# 4. Bei Erfolg: Commit-Hash wird für PROD freigegeben
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

# Prüfen ob Working Directory clean ist
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${YELLOW}⚠️  Warning: Working directory has uncommitted changes!${NC}"
    echo ""
    git status --short
    echo ""
    echo "Möchtest du trotzdem fortfahren? [y/N]"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Abgebrochen."
        exit 1
    fi
fi

# Get current commit hash
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_SHORT=$(git rev-parse --short HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B | head -1)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🧪 TEST MIGRATION WORKFLOW${NC}"
echo -e "${GREEN}📦 Commit: $COMMIT_SHORT${NC}"
echo -e "${GREEN}📝 Message: $COMMIT_MSG${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Checkout des HEAD in temporäres Verzeichnis
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "📦 Exporting HEAD to temporary directory..."
git archive HEAD | tar -x -C "$TEMP_DIR"
echo ""

# Step 1: Build TEST Container aus HEAD
echo -e "${BLUE}🔨 Step 1/6: Building TEST Container from HEAD...${NC}"
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

# Step 5: Commit für PROD freigeben
echo -e "${BLUE}✅ Step 5/6: Freigabe für PROD Deployment...${NC}"
echo ""

# Freigabe-File erstellen/updaten
APPROVAL_FILE="$PROJECT_ROOT/.test-approvals"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Format: COMMIT_HASH|TIMESTAMP|STATUS|COMMIT_MSG
echo "$COMMIT_HASH|$TIMESTAMP|SUCCESS|$COMMIT_MSG" >> "$APPROVAL_FILE"

echo -e "${GREEN}✅ Commit '$COMMIT_SHORT' für PROD freigegeben${NC}"
echo "   Freigabe gespeichert in: .test-approvals"
echo "   Full hash: $COMMIT_HASH"
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
echo -e "${GREEN}✅ Commit '$COMMIT_SHORT' für PROD freigegeben${NC}"
echo ""
echo "Nächste Schritte:"
echo "  1. Git Tag erstellen:"
echo "     git tag -a rezept_version_DD_MM_YYYY_NNN -m 'Release message'"
echo ""
echo "  2. PROD Deployment:"
echo "     ./scripts/deployment/deploy-prod.sh rezept_version_DD_MM_YYYY_NNN"
echo ""
echo -e "${YELLOW}⚠️  Nur Tags mit diesem Commit ($COMMIT_SHORT) können deployed werden!${NC}"
echo ""
echo "Test Container Status:"
podman ps | grep seaser-rezept-tagebuch-test
echo ""
