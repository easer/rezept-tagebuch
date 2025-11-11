#!/bin/bash
# Run Performance Tests on TEST Container
#
# Tests that recipe imports complete within acceptable time:
# - TheMealDB Import: < 3 seconds
# - Migusto Import: < 3 seconds

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}⚡ PERFORMANCE TESTS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if TEST container is running
echo "📍 Checking TEST container status..."
if ! podman ps --format "{{.Names}}" | grep -q "seaser-rezept-tagebuch-test"; then
    echo -e "${RED}❌ TEST container is not running!${NC}"
    echo ""
    echo "Start TEST container first:"
    echo "  ./scripts/test/build.sh"
    echo ""
    echo "Or run full test workflow:"
    echo "  ./scripts/test/test-and-approve-for-prod.sh"
    exit 1
fi

echo -e "${GREEN}✅ TEST container is running${NC}"
echo ""

# Check if TEST container is accessible
echo "📍 Checking TEST API accessibility..."
if curl -s --max-time 5 http://localhost:8001/ > /dev/null; then
    echo -e "${GREEN}✅ TEST API is accessible${NC}"
else
    echo -e "${RED}❌ TEST API is not accessible at http://localhost:8001/${NC}"
    echo ""
    echo "Container may not be fully started yet. Wait a moment and try again."
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Running Performance Tests${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Target: http://localhost:8001"
echo "Threshold: < 3 seconds per import"
echo ""

# Run performance tests
podman exec seaser-rezept-tagebuch-test pytest \
    -v \
    -s \
    --tb=short \
    -m performance \
    tests/test_performance_imports.py

TEST_EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ PERFORMANCE TESTS PASSED!${NC}"
    echo ""
    echo "All imports completed within 3 seconds threshold."
    echo ""
    echo "📊 Results:"
    echo "  ✅ TheMealDB Import: < 3s"
    echo "  ✅ Migusto Import: < 3s"
else
    echo -e "${RED}❌ PERFORMANCE TESTS FAILED!${NC}"
    echo ""
    echo "Some imports exceeded the 3 second threshold."
    echo ""
    echo "Possible causes:"
    echo "  - Network latency"
    echo "  - DeepL API slow"
    echo "  - TheMealDB API slow"
    echo "  - Container resource constraints"
    echo ""
    echo "Check logs:"
    echo "  podman logs seaser-rezept-tagebuch-test"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit $TEST_EXIT_CODE
