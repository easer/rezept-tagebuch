#!/bin/bash
# Daily Recipe Import with Retry Logic
# Retries up to 10 times if a recipe is rejected due to meat content
#
# Usage: daily-import.sh [strategy] [value]
# Examples:
#   daily-import.sh by_category Vegetarian
#   daily-import.sh by_area Italian
#   daily-import.sh random

set -e

# Configuration
MAX_ATTEMPTS=10
RETRY_DELAY=2
BASE_URL="http://localhost:8000/rezept-tagebuch/api/recipes/daily-import"
CLEANUP_URL="http://localhost:8000/rezept-tagebuch/api/recipes/cleanup-old-imports"

# Parse arguments
STRATEGY="${1:-by_category}"
VALUE="${2:-Vegetarian}"

# Build API URL
if [ -n "$VALUE" ] && [ "$VALUE" != "none" ]; then
    API_URL="${BASE_URL}?strategy=${STRATEGY}&value=${VALUE}"
else
    API_URL="${BASE_URL}?strategy=${STRATEGY}"
fi

echo "Starting daily recipe import (strategy: $STRATEGY, value: ${VALUE:-none}, max $MAX_ATTEMPTS attempts)..."

# Attempt import with retries
for attempt in $(seq 1 $MAX_ATTEMPTS); do
    echo "Attempt $attempt/$MAX_ATTEMPTS: Fetching recipe..."

    # Make request and capture HTTP status code
    http_code=$(curl -s -o /tmp/import-response.json -w "%{http_code}" -X POST "$API_URL")

    if [ "$http_code" = "200" ]; then
        echo "✅ Success! Meat-free recipe imported."
        recipe_title=$(cat /tmp/import-response.json | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4)
        echo "Imported: $recipe_title"

        # Cleanup old imports
        echo "Running cleanup of old imports..."
        curl -s -X POST "$CLEANUP_URL" > /dev/null
        echo "✅ Daily import completed successfully"
        exit 0
    elif [ "$http_code" = "400" ]; then
        rejected_category=$(cat /tmp/import-response.json | grep -o '"rejected_category":"[^"]*"' | cut -d'"' -f4)
        rejected_title=$(cat /tmp/import-response.json | grep -o '"rejected_title":"[^"]*"' | cut -d'"' -f4)
        echo "⚠️ Recipe rejected: '$rejected_title' (category: $rejected_category)"

        if [ $attempt -lt $MAX_ATTEMPTS ]; then
            echo "Retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
        fi
    else
        echo "❌ Error: HTTP $http_code"
        cat /tmp/import-response.json
        exit 1
    fi
done

echo "❌ Failed to import meat-free recipe after $MAX_ATTEMPTS attempts"
exit 1
