#!/bin/bash
# Build & Start Test Container (Manual Debugging Only)
#
# ⚠️  HINWEIS: Für normale Test-Workflows verwende stattdessen:
#     ./scripts/database/test-migration.sh
#
# Dieses Script ist NUR für manuelles Debugging gedacht.
# Es startet den TEST-Container permanent (nicht on-demand).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
cd "$PROJECT_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  MANUAL TEST CONTAINER START"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  Dies ist NUR für manuelles Debugging!"
echo ""
echo "Für normale Test-Workflows verwende:"
echo "  ./scripts/database/test-migration.sh"
echo ""
echo "Fortfahren? [y/N]"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""
echo "🔨 Building Test Image from Working Directory..."
podman build -t seaser-rezept-tagebuch:test -f Containerfile .

echo ""
echo "🔄 Stopping existing Test Container..."
podman stop seaser-rezept-tagebuch-test 2>/dev/null || true
podman rm seaser-rezept-tagebuch-test 2>/dev/null || true

echo ""
echo "🚀 Starting Test Container..."
podman run -d \
  --name seaser-rezept-tagebuch-test \
  --network seaser-network \
  -e TESTING_MODE=true \
  -v "$PROJECT_ROOT/data/test/uploads:/data/test/uploads:Z" \
  seaser-rezept-tagebuch:test

echo ""
echo "✅ Test Container läuft (manuell gestartet)!"
echo "📍 URL: http://192.168.2.139:8000/rezept-tagebuch-test/"
echo ""
echo "⚠️  Vergiss nicht den Container zu stoppen:"
echo "   podman stop seaser-rezept-tagebuch-test"
echo "   podman rm seaser-rezept-tagebuch-test"
echo ""
echo "📊 Status:"
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep rezept-tagebuch-test
