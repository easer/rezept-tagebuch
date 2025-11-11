#!/bin/bash
# Run pytest tests in parallel using pytest-xdist
# This script runs tests inside the test container which has pytest-xdist installed

set -e

CONTAINER_NAME="seaser-rezept-tagebuch-test"

# Check if container is running
if ! podman ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Error: Container $CONTAINER_NAME is not running"
    echo "Please start the test container first"
    exit 1
fi

echo "🧪 Running parallel tests in container..."
echo ""

# Create tests directory and copy test files to container
podman exec "$CONTAINER_NAME" mkdir -p /app/tests
podman cp tests/. "$CONTAINER_NAME:/app/tests/"

# Run tests in parallel
echo "=== PARALLEL TEST (pytest-xdist) ==="
podman exec "$CONTAINER_NAME" pytest tests/ -n auto -v

echo ""
echo "✅ Tests completed!"
