#!/bin/bash
# Run pytest test suite for Rezept-Tagebuch

set -e

echo "🧪 Rezept-Tagebuch Test Suite"
echo "============================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest is not installed"
    echo "   Installing pytest..."
    pip3 install -r requirements.txt
fi

# Check if dev container is running
if ! podman ps | grep -q "seaser-rezept-tagebuch-dev"; then
    echo "❌ Dev container is not running"
    echo "   Run: ./build-dev.sh"
    exit 1
fi

echo "✅ Dev container is running"
echo ""

# Run tests
echo "Running pytest..."
echo ""

# Default: run all tests
if [ $# -eq 0 ]; then
    pytest
else
    # Run with arguments (e.g., ./run-tests.sh -k test_create)
    pytest "$@"
fi
