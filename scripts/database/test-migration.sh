#!/bin/bash
# Test Migration auf TEST-Umgebung
# Workflow:
# 1. TEST Container bauen & starten
# 2. Alembic Migration auf TEST DB
# 3. Automatische Tests laufen lassen
# 4. Bei Erfolg: DEV Container aktualisieren

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

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🧪 TEST MIGRATION WORKFLOW${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Build TEST Container
echo -e "${BLUE}🔨 Step 1/5: Building TEST Container...${NC}"
podman build -t seaser-rezept-tagebuch:test -f Containerfile .
echo ""

# Step 2: Start TEST Container
echo -e "${BLUE}🚀 Step 2/5: Starting TEST Container...${NC}"
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
echo -e "${BLUE}🔄 Step 3/5: Running Alembic Migration auf TEST DB...${NC}"
echo "  📍 Database: rezepte_test"
echo "  📍 Config: alembic-test.ini"
echo ""

# Execute alembic upgrade inside the TEST container
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini upgrade head

echo ""
echo -e "${GREEN}✅ Migration auf TEST erfolgreich${NC}"
echo ""

# Step 4: Run Automated Tests
echo -e "${BLUE}🧪 Step 4/5: Running Automated Tests...${NC}"
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

# Step 5: Update DEV Container
echo -e "${BLUE}🔄 Step 5/5: Update DEV Container mit neuer Migration...${NC}"
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
echo ""
echo "Nächste Schritte:"
echo "  1. Teste manuell in DEV: http://192.168.2.139:8001/rezept-tagebuch/"
echo "  2. Bei Erfolg: Git Tag erstellen"
echo "     ./scripts/tools/tag-version.sh"
echo "  3. PROD Deployment:"
echo "     ./scripts/deployment/deploy-prod.sh rezept_version_DD_MM_YYYY_NNN"
echo ""
echo "Test Container Status:"
podman ps | grep seaser-rezept-tagebuch-test
echo ""
