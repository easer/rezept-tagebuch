#!/bin/bash
# Build & Deploy Dev Version

set -e

echo "🔨 Building Dev Image..."
cd /home/gabor/easer_projekte/rezept-tagebuch
podman build -t seaser-rezept-tagebuch:dev -f Containerfile .

echo "🔄 Restarting Dev Container..."
podman stop seaser-rezept-tagebuch-dev 2>/dev/null || true
podman rm seaser-rezept-tagebuch-dev 2>/dev/null || true

podman run -d \
  --name seaser-rezept-tagebuch-dev \
  --network seaser-network \
  --env-file /home/gabor/easer_projekte/rezept-tagebuch/.env \
  -v /home/gabor/easer_projekte/rezept-tagebuch/data/dev:/data:Z \
  localhost/seaser-rezept-tagebuch:dev

echo "✅ Dev Container läuft!"
echo "📍 URL: http://192.168.2.139:8000/rezept-tagebuch-dev/"
podman ps | grep seaser-rezept-tagebuch
