#!/bin/bash
# Run tests with isolated test database
# This script starts the dev container in TESTING_MODE

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🧪 Starting isolated test environment${NC}"
echo ""

# Stop and remove existing dev container
echo "Stopping existing dev container..."
podman rm -f seaser-rezept-tagebuch-dev 2>/dev/null || true

# Wait for port to be released
sleep 2

# Clean test database
TEST_DB="./data/test/rezepte.db"
if [ -f "$TEST_DB" ]; then
    rm "$TEST_DB"
    echo -e "${GREEN}✅ Cleaned test database${NC}"
fi

# Start container with TESTING_MODE
echo "Starting container with TESTING_MODE..."
podman run -d --rm \
    --name seaser-rezept-tagebuch-dev \
    -p 8000:80 \
    -v "$SCRIPT_DIR/data:/data:Z" \
    -e TESTING_MODE=true \
    seaser-rezept-tagebuch:dev

# Wait for container to be ready
sleep 3

echo -e "${GREEN}✅ Test container ready${NC}"
echo ""

# Run tests
echo -e "${BLUE}Running pytest...${NC}"
echo ""

pytest "$@"

TEST_RESULT=$?

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Some tests failed${NC}"
fi

echo ""
echo "Restarting dev container in normal mode..."
./build-dev.sh > /dev/null 2>&1

echo -e "${GREEN}✅ Dev container restored${NC}"

exit $TEST_RESULT
