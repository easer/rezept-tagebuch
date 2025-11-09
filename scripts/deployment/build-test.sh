#!/bin/bash
# Build & Deploy Test Version

set -e

echo "🔨 Building Test Image..."
cd /home/gabor/easer_projekte/rezept-tagebuch
podman build -t seaser-rezept-tagebuch:test -f Containerfile .

echo "🔄 Restarting Test Container..."
podman stop seaser-rezept-tagebuch-test 2>/dev/null || true
podman rm seaser-rezept-tagebuch-test 2>/dev/null || true

podman run -d --name seaser-rezept-tagebuch-test --network seaser-network -e DB_TYPE=postgresql -e TESTING_MODE=true -e POSTGRES_HOST=seaser-postgres-test -e POSTGRES_DB=rezepte_test -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=test -e DEEPL_API_KEY=a35ce617-15e4-46b2-8e99-a97bd1e6a853:fx -v /home/gabor/easer_projekte/rezept-tagebuch/data/test:/data localhost/seaser-rezept-tagebuch:test

echo "✅ Test Container läuft!"
echo "📍 URL: http://192.168.2.139:8000/rezept-tagebuch-test/"
podman ps | grep seaser-rezept-tagebuch
