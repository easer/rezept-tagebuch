#!/bin/bash
# Daily Migusto Recipe Import
# Imports 1 random recipe from Migusto using a random preset from config
#
# Usage: daily-migusto-import.sh [preset_name]
# Examples:
#   daily-migusto-import.sh vegetarische_pasta_familie
#   daily-migusto-import.sh (random preset)

set -e

# Configuration
BASE_URL="http://localhost:8000/rezept-tagebuch/api/recipes/import-migusto-batch"
CLEANUP_URL="http://localhost:8000/rezept-tagebuch/api/recipes/cleanup-old-imports"
CONFIG_FILE="/home/gabor/easer_projekte/rezept-tagebuch/config/migusto-import-config.json"

# Available presets (from config)
PRESETS=("vegetarische_pasta_familie" "vegane_hauptgerichte" "schnelle_familiengerichte")

# Parse arguments
if [ -n "$1" ]; then
    PRESET="$1"
else
    # Select random preset
    PRESET=${PRESETS[$RANDOM % ${#PRESETS[@]}]}
fi

echo "Starting daily Migusto import (preset: $PRESET)..."

# Build API request body
REQUEST_BODY="{\"preset_name\": \"${PRESET}\", \"max_recipes\": 1}"

# Make request
echo "Fetching recipe with preset: $PRESET..."
http_code=$(curl -s -o /tmp/migusto-import-response.json -w "%{http_code}" \
    -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_BODY")

if [ "$http_code" = "200" ]; then
    success_count=$(cat /tmp/migusto-import-response.json | grep -o '"success_count":[0-9]*' | cut -d':' -f2)

    if [ "$success_count" -gt 0 ]; then
        echo "✅ Success! $success_count Migusto recipe imported."

        # Extract recipe title if available
        recipe_title=$(cat /tmp/migusto-import-response.json | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [ -n "$recipe_title" ]; then
            echo "Imported: $recipe_title"
        fi

        # Cleanup old imports
        echo "Running cleanup of old imports..."
        curl -s -X POST "$CLEANUP_URL" > /dev/null
        echo "✅ Daily Migusto import completed successfully"
        exit 0
    else
        echo "⚠️ No recipes imported (0 success)"
        cat /tmp/migusto-import-response.json
        exit 1
    fi
else
    echo "❌ Error: HTTP $http_code"
    cat /tmp/migusto-import-response.json
    exit 1
fi
