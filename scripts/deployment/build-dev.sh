#!/bin/bash
# Build & Deploy Dev Version

set -e

echo "🔨 Building Dev Image..."
cd /home/gabor/easer_projekte/rezept-tagebuch
podman build -t seaser-rezept-tagebuch:dev -f Containerfile .

echo "🔄 Restarting Dev Container..."
podman stop seaser-rezept-tagebuch-dev 2>/dev/null || true
podman rm seaser-rezept-tagebuch-dev 2>/dev/null || true

podman run -d --name seaser-rezept-tagebuch-dev --network seaser-network -e DB_TYPE=postgresql -e DEV_MODE=true -e POSTGRES_HOST=seaser-postgres-dev -e POSTGRES_DB=rezepte_dev -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=seaser -e DEEPL_API_KEY=a35ce617-15e4-46b2-8e99-a97bd1e6a853:fx -v /home/gabor/easer_projekte/rezept-tagebuch/data/dev:/data localhost/seaser-rezept-tagebuch:dev

echo "✅ Dev Container läuft!"
echo "📍 URL: http://192.168.2.139:8000/rezept-tagebuch-dev/"
podman ps | grep seaser-rezept-tagebuch
