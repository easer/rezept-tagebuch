#!/bin/bash
# Rollback to previous version

set -e

# Version als Parameter
VERSION=$1

if [ -z "$VERSION" ]; then
    echo "❌ Fehler: Keine Version angegeben!"
    echo ""
    echo "Usage: ./rollback.sh <version>"
    echo ""
    echo "Verfügbare Versionen:"
    podman images | grep seaser-rezept-tagebuch | grep -v latest | grep -v dev
    exit 1
fi

# Prüfe ob Version existiert
if ! podman image exists seaser-rezept-tagebuch:$VERSION; then
    echo "❌ Version $VERSION existiert nicht!"
    echo ""
    echo "Verfügbare Versionen:"
    podman images | grep seaser-rezept-tagebuch
    exit 1
fi

echo "⏮️  Rollback zu Version: $VERSION"

# Tag alte Version als latest
echo "🏷️  Tagging v$VERSION as latest..."
podman tag seaser-rezept-tagebuch:$VERSION seaser-rezept-tagebuch:latest

# Prod Container neu starten
echo "🔄 Restarting Production Container..."
podman stop seaser-rezept-tagebuch
podman rm seaser-rezept-tagebuch

podman run -d \
  --name seaser-rezept-tagebuch \
  --network seaser-network \
  -v /home/gabor/data/rezept-tagebuch:/data:Z \
  localhost/seaser-rezept-tagebuch:latest

echo ""
echo "✅ Rollback zu v$VERSION erfolgreich!"
echo "📍 URL: http://192.168.2.139:8000/rezept-tagebuch/"
podman ps | grep seaser-rezept-tagebuch
