#!/bin/bash
# Build & Deploy Dev Version

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
cd "$PROJECT_ROOT"

echo "🔨 Building Dev Image..."
podman build -t seaser-rezept-tagebuch:dev -f Containerfile .

echo "🔄 Restarting Dev Container..."
podman stop seaser-rezept-tagebuch-dev 2>/dev/null || true
podman rm seaser-rezept-tagebuch-dev 2>/dev/null || true

echo "🚀 Starting Dev Container..."

# Load DeepL API Key from .env if available
DEEPL_KEY=""
if [ -f "$PROJECT_ROOT/.env" ]; then
  DEEPL_KEY=$(grep "^DEEPL_API_KEY=" "$PROJECT_ROOT/.env" | cut -d'=' -f2)
fi

podman run -d \
  --name seaser-rezept-tagebuch-dev \
  --network seaser-network \
  -e DEV_MODE=true \
  -e DEEPL_API_KEY="$DEEPL_KEY" \
  -v "$PROJECT_ROOT/data/dev/uploads:/data/dev/uploads:Z" \
  seaser-rezept-tagebuch:dev

echo ""
echo "✅ Dev Container läuft!"
echo "📍 URL: http://192.168.2.139:8000/rezept-tagebuch-dev/"
echo ""
echo "📊 Status:"
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep rezept-tagebuch-dev
