#!/bin/bash
# Erstellt einen neuen Git-Tag im Format: rezept_version_DD_MM_YYYY_NNN
# Prüft vorher ob Working Directory clean ist

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🏷️  Git-Tag Creator für Rezept-Tagebuch"
echo ""

# Prüfen ob Working Directory clean ist
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}❌ Working Directory ist nicht clean!${NC}"
    echo ""
    git status --short
    echo ""
    echo -e "${YELLOW}Bitte erst alle Änderungen committen:${NC}"
    echo "  git add <files>"
    echo "  git commit -m 'deine message'"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Working Directory ist clean${NC}"
echo ""

# Tests ausführen vor Tag-Erstellung (kann übersprungen werden mit TAG_SKIP_TESTS=1)
if [[ "$TAG_SKIP_TESTS" == "1" ]]; then
    echo -e "${YELLOW}⚠️  Tests werden übersprungen (TAG_SKIP_TESTS=1)${NC}"
    echo ""
else
    echo "🧪 Running tests before creating tag..."
    echo ""

# Check if dev container is running
if ! podman ps | grep -q "seaser-rezept-tagebuch-dev"; then
    echo -e "${YELLOW}⚠️  Dev container is not running${NC}"
    echo "   Starte Container..."
    ./build-dev.sh
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "   Installing pytest..."
    pip3 install pytest pytest-timeout --break-system-packages --quiet
fi

# Run pytest tests
echo "   Running pytest test suite..."
if ! pytest -x -q; then
    echo ""
    echo -e "${RED}❌ Tests failed!${NC}"
    echo "   Tag creation aborted."
    echo ""
    echo "Options:"
    echo "  1. Fix failing tests"
    echo "  2. Skip tests: TAG_SKIP_TESTS=1 ./tag-version.sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ All pytest tests passed${NC}"
echo ""

# Run E2E test
echo "   Running E2E test (recipe import)..."
if ! ./test-recipe-import-e2e.sh > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  E2E test failed (non-blocking)${NC}"
else
    echo -e "${GREEN}✅ E2E test passed${NC}"
fi

echo ""
echo -e "${GREEN}✅ All tests completed successfully!${NC}"
echo ""
fi

# Custom Tag oder Auto-Increment?
if [[ -n "$1" ]]; then
    # Custom Tag aus Parameter (muss im richtigen Format sein)
    CUSTOM_TAG=$1
    if [[ ! "$CUSTOM_TAG" =~ ^rezept_version_[0-9]{2}_[0-9]{2}_[0-9]{4}_[0-9]{3}$ ]]; then
        echo -e "${RED}❌ Ungültiges Tag-Format!${NC}"
        echo "   Erwartet: rezept_version_DD_MM_YYYY_NNN"
        echo "   Beispiel: rezept_version_05_11_2025_001"
        exit 1
    fi
    GIT_TAG=$CUSTOM_TAG
else
    # Auto-Increment: Finde höchste Nummer für heutiges Datum
    TODAY="rezept_version_$(date +%d_%m_%Y)"
    EXISTING_TAGS=$(git tag | grep "^${TODAY}_" 2>/dev/null || true)

    if [[ -z "$EXISTING_TAGS" ]]; then
        # Erster Tag für heute
        BUILD_NUM="001"
    else
        # Finde höchste Nummer und inkrementiere
        HIGHEST=$(echo "$EXISTING_TAGS" | sed "s/^${TODAY}_//" | sort -n | tail -1)
        BUILD_NUM=$(printf "%03d" $((10#$HIGHEST + 1)))
    fi

    GIT_TAG="${TODAY}_${BUILD_NUM}"

    echo -e "${BLUE}Auto-generierter Tag:${NC} $GIT_TAG"
    echo ""
fi

# Prüfen ob Tag bereits existiert
if git rev-parse "$GIT_TAG" >/dev/null 2>&1; then
    echo -e "${RED}❌ Tag '$GIT_TAG' existiert bereits!${NC}"
    echo ""
    echo "Möchtest du einen anderen Tag-Namen verwenden?"
    echo "Usage: ./tag-version.sh rezept_version_DD_MM_YYYY_NNN"
    echo ""
    echo "Existierende Tags:"
    git tag | grep "^rezept_version_"
    exit 1
fi

# Commit-Info anzeigen
echo -e "${BLUE}Aktueller Commit:${NC}"
git log -1 --oneline
echo ""

# Tag-Message eingeben
echo -e "${YELLOW}Tag-Message (optional, Enter für Standard-Message):${NC}"
read -r TAG_MESSAGE

if [[ -z "$TAG_MESSAGE" ]]; then
    TAG_MESSAGE="Release $GIT_TAG"
fi

# Tag erstellen
echo ""
echo "Erstelle Git-Tag: $GIT_TAG"
git tag -a "$GIT_TAG" -m "$TAG_MESSAGE"

echo ""
echo -e "${GREEN}✅ Tag erfolgreich erstellt!${NC}"
echo ""
echo "📦 Tag: $GIT_TAG"
echo "💬 Message: $TAG_MESSAGE"
echo ""
echo "Nächste Schritte:"
echo "  1. Tag zum Remote pushen:"
echo "     ${BLUE}git push origin $GIT_TAG${NC}"
echo ""
echo "  2. Auf Prod deployen:"
echo "     ${BLUE}./deploy-prod.sh $GIT_TAG${NC}"
echo ""
echo "Alle Tags anzeigen:"
echo "  git tag | grep rezept_version"
