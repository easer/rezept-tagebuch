#!/bin/bash
# Deploy to Production with Version Tag, Auto-Backup & Migrations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Version aus Parameter oder aktuelles Datum
VERSION=${1:-$(date +%y.%m.%d)}

echo "🚀 Deploying Version: v$VERSION"
echo ""

# 1. Create automatic backup BEFORE deployment
echo "📦 Step 1/5: Creating automatic backup..."
./backup-db.sh prod "before-v$VERSION"
echo ""

# 2. Build mit Version-Tag
echo "🔨 Step 2/5: Building Image v$VERSION..."
podman build -t seaser-rezept-tagebuch:v$VERSION -f Containerfile .

# Tag als latest
echo ""
echo "🏷️  Step 3/5: Tagging as latest..."
podman tag seaser-rezept-tagebuch:v$VERSION seaser-rezept-tagebuch:latest

# 3. Run migrations BEFORE starting new container
echo ""
echo "🔄 Step 4/5: Running database migrations..."
export DB_PATH="/home/gabor/data/rezept-tagebuch/rezepte.db"
python3 -m pip install --quiet alembic==1.13.1 2>/dev/null || true
alembic upgrade head
echo "  ✅ Migrations completed"

# 4. Prod Container neu starten
echo ""
echo "🔄 Step 5/5: Restarting Production Container..."
podman stop seaser-rezept-tagebuch 2>/dev/null || true
podman rm seaser-rezept-tagebuch 2>/dev/null || true

podman run -d \
  --name seaser-rezept-tagebuch \
  --network seaser-network \
  -v /home/gabor/data/rezept-tagebuch:/data:Z \
  localhost/seaser-rezept-tagebuch:latest

# Systemd Service aktualisieren
echo ""
echo "⚙️  Updating systemd service..."
podman generate systemd --new --name seaser-rezept-tagebuch > /home/gabor/.config/systemd/user/container-seaser-rezept-tagebuch.service
systemctl --user daemon-reload
systemctl --user enable container-seaser-rezept-tagebuch.service

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Production Deployment erfolgreich!"
echo "📦 Version: v$VERSION"
echo "📍 URL: http://192.168.2.139:8000/rezept-tagebuch/"
echo "🗄️  Database: Migrated to latest schema"
echo ""
echo "Container Status:"
podman ps | grep seaser-rezept-tagebuch
echo ""
echo "Available versions:"
podman images | grep seaser-rezept-tagebuch
echo ""
echo "💡 Rollback available via: ./rollback.sh v$VERSION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
