#!/bin/bash
# Rollback to previous version (Git-Tag-basiert)

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Git-Tag als Parameter
GIT_TAG=$1

if [ -z "$GIT_TAG" ]; then
    echo -e "${RED}❌ Fehler: Kein Git-Tag angegeben!${NC}"
    echo ""
    echo "Usage: ./rollback.sh <GIT_TAG>"
    echo ""
    echo "Verfügbare Git-Tags:"
    git tag | grep "^rezept_version_" || echo "  (keine Tags gefunden)"
    echo ""
    echo "Verfügbare Container-Images:"
    podman images | grep seaser-rezept-tagebuch | grep -v latest | grep -v dev
    exit 1
fi

# Prüfe ob Container-Image existiert
if ! podman image exists seaser-rezept-tagebuch:$GIT_TAG; then
    echo -e "${RED}❌ Container-Image für '$GIT_TAG' existiert nicht!${NC}"
    echo ""
    echo "Das Image muss erst gebaut werden. Nutze:"
    echo "  ./deploy-prod.sh $GIT_TAG"
    echo ""
    echo "Verfügbare Images:"
    podman images | grep seaser-rezept-tagebuch
    exit 1
fi

echo "⏮️  Rollback zu Git-Tag: $GIT_TAG"
echo ""

# Warnung anzeigen
echo -e "${YELLOW}⚠️  WARNUNG: Rollback wird durchgeführt!${NC}"
echo "   Stelle sicher, dass die Datenbank kompatibel ist."
echo "   Bei Schema-Änderungen ggf. erst DB-Backup wiederherstellen."
echo ""
read -p "Fortfahren? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Abgebrochen."
    exit 1
fi
echo ""

# Tag alte Version als latest
echo "🏷️  Tagging $GIT_TAG as latest..."
podman tag seaser-rezept-tagebuch:$GIT_TAG seaser-rezept-tagebuch:latest

# Prod Container neu starten
echo "🔄 Restarting Production Container..."
podman stop seaser-rezept-tagebuch
podman rm seaser-rezept-tagebuch

podman run -d \
  --name seaser-rezept-tagebuch \
  --network seaser-network \
  --env-file /home/gabor/easer_projekte/rezept-tagebuch/.env \
  -v /home/gabor/data/rezept-tagebuch:/data:Z \
  localhost/seaser-rezept-tagebuch:latest

echo ""
echo -e "${GREEN}✅ Rollback zu $GIT_TAG erfolgreich!${NC}"
echo "📍 URL: http://192.168.2.139:8000/rezept-tagebuch/"
podman ps | grep seaser-rezept-tagebuch
