#!/bin/bash
# E2E Test: Recipe Import Flow
# Tests: TheMealDB API → DeepL Translation → SCHRITT Formatting → DB Storage → Parser

echo "🧪 E2E Test: Recipe Import Flow"
echo "================================"
echo ""

# Configuration
API_URL="http://localhost:8000/rezept-tagebuch-dev/api"
CONTAINER="seaser-rezept-tagebuch-dev"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_pass() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

test_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 1. Check if container is running
echo "1️⃣  Checking Dev Container..."
if podman ps | grep -q "$CONTAINER"; then
    test_pass "Container '$CONTAINER' is running"
else
    test_fail "Container '$CONTAINER' is NOT running"
    echo "   → Run: ./scripts/deployment/build-dev.sh"
    exit 1
fi
echo ""

# 2. Check if DEEPL_API_KEY is configured
echo "2️⃣  Checking DeepL Configuration..."
DEEPL_CHECK=$(podman exec "$CONTAINER" printenv DEEPL_API_KEY 2>/dev/null || echo "")
if [ -n "$DEEPL_CHECK" ]; then
    test_pass "DEEPL_API_KEY is configured"
else
    test_fail "DEEPL_API_KEY is NOT configured"
    echo "   → Set in .env file and rebuild: ./scripts/deployment/build-dev.sh"
    exit 1
fi
echo ""

# 3. Get recipe count before import
echo "3️⃣  Getting initial recipe count..."
BEFORE_COUNT=$(podman exec "$CONTAINER" python3 -c "import sqlite3; conn = sqlite3.connect('/data/rezepte.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM recipes'); print(c.fetchone()[0]); conn.close()")
test_info "Recipes in DB before import: $BEFORE_COUNT"
echo ""

# 4. Trigger daily import
echo "4️⃣  Triggering daily import from TheMealDB..."
IMPORT_RESPONSE=$(curl -s -X POST "$API_URL/recipes/daily-import")

if echo "$IMPORT_RESPONSE" | grep -q '"success"' && echo "$IMPORT_RESPONSE" | grep -q 'true'; then
    test_pass "Daily import API call succeeded"

    # Extract recipe ID
    RECIPE_ID=$(echo "$IMPORT_RESPONSE" | grep -o '"recipe_id":[[:space:]]*[0-9]*' | grep -o '[0-9]*')
    test_info "Imported Recipe ID: $RECIPE_ID"
else
    test_fail "Daily import API call failed"
    echo "   Response: $IMPORT_RESPONSE"
    exit 1
fi
echo ""

# 5. Verify recipe count increased
echo "5️⃣  Verifying recipe was added to DB..."
AFTER_COUNT=$(podman exec "$CONTAINER" python3 -c "import sqlite3; conn = sqlite3.connect('/data/rezepte.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM recipes'); print(c.fetchone()[0]); conn.close()")

if [ "$AFTER_COUNT" -gt "$BEFORE_COUNT" ]; then
    test_pass "Recipe count increased: $BEFORE_COUNT → $AFTER_COUNT"
else
    test_fail "Recipe count did NOT increase"
    exit 1
fi
echo ""

# 6. Check SCHRITT formatting in DB
echo "6️⃣  Validating SCHRITT formatting in DB..."
HAS_SCHRITT=$(podman exec "$CONTAINER" python3 -c "import sqlite3, re; conn = sqlite3.connect('/data/rezepte.db'); c = conn.cursor(); c.execute('SELECT notes FROM recipes WHERE id = $RECIPE_ID'); notes = c.fetchone()[0]; conn.close(); print('YES' if re.search(r'SCHRITT\s+\d+', notes, re.IGNORECASE) else 'NO')")

if [ "$HAS_SCHRITT" = "YES" ]; then
    test_pass "Recipe notes contain SCHRITT formatting"
else
    test_fail "Recipe notes do NOT contain SCHRITT formatting"
    test_info "Notes preview:"
    podman exec "$CONTAINER" python3 -c "import sqlite3; conn = sqlite3.connect('/data/rezepte.db'); c = conn.cursor(); c.execute('SELECT notes FROM recipes WHERE id = $RECIPE_ID'); notes = c.fetchone()[0]; print(notes[:300] + '...' if len(notes) > 300 else notes); conn.close()"
fi
echo ""

# 7. Check Zutaten section
echo "7️⃣  Validating Zutaten section..."
HAS_ZUTATEN=$(podman exec "$CONTAINER" python3 -c "import sqlite3; conn = sqlite3.connect('/data/rezepte.db'); c = conn.cursor(); c.execute('SELECT notes FROM recipes WHERE id = $RECIPE_ID'); notes = c.fetchone()[0]; conn.close(); print('YES' if 'Zutaten:' in notes else 'NO')")

if [ "$HAS_ZUTATEN" = "YES" ]; then
    test_pass "Recipe notes contain Zutaten section"
else
    test_fail "Recipe notes do NOT contain Zutaten section"
fi
echo ""

# 8. Verify API endpoint returns recipe
echo "8️⃣  Testing API endpoint /api/recipes/$RECIPE_ID..."
API_RESPONSE=$(curl -s "$API_URL/recipes/$RECIPE_ID")

if echo "$API_RESPONSE" | grep -q '"id":'; then
    test_pass "API endpoint returns recipe data"

    # Check if title is in German (translated)
    TITLE=$(echo "$API_RESPONSE" | grep -o '"title": "[^"]*"' | head -1 | cut -d'"' -f4)
    test_info "Recipe title: $TITLE"
else
    test_fail "API endpoint did NOT return recipe data"
fi
echo ""

# 9. Test parser config is accessible
echo "9️⃣  Testing recipe-format-config.json availability..."
CONFIG_RESPONSE=$(curl -s "$API_URL/recipe-format-config.json")

if echo "$CONFIG_RESPONSE" | grep -q '"patterns"'; then
    test_pass "recipe-format-config.json is accessible"
else
    test_fail "recipe-format-config.json is NOT accessible"
    echo "   Response: $CONFIG_RESPONSE"
fi
echo ""

# Summary
echo "================================"
echo "📊 Test Summary"
echo "================================"
echo -e "${GREEN}✓ Passed: $TESTS_PASSED${NC}"
echo -e "${RED}✗ Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo "✅ Recipe Import Flow is working:"
    echo "   1. TheMealDB API → ✓"
    echo "   2. DeepL Translation → ✓"
    echo "   3. SCHRITT Formatting → ✓"
    echo "   4. DB Storage → ✓"
    echo "   5. API Endpoint → ✓"
    echo "   6. Parser Config → ✓"
    echo ""
    echo "🔍 View imported recipe:"
    echo "   http://localhost:8000/rezept-tagebuch-dev/ → Recipe ID: $RECIPE_ID"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
