#!/bin/bash
# Install systemd timers for daily imports (PROD)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$SCRIPT_DIR"

echo "📅 Installing PROD daily import timers..."
echo ""

# Copy TheMealDB service and timer files
echo "📦 Installing TheMealDB import service..."
cp systemd/prod/rezept-daily-import.service ~/.config/systemd/user/
cp systemd/prod/rezept-daily-import.timer ~/.config/systemd/user/

# Copy Migusto service and timer files
echo "📦 Installing Migusto import service..."
cp systemd/prod/rezept-daily-migusto-import.service ~/.config/systemd/user/
cp systemd/prod/rezept-daily-migusto-import.timer ~/.config/systemd/user/

# Reload systemd
echo ""
echo "🔄 Reloading systemd..."
systemctl --user daemon-reload

# Enable and start timers
echo ""
echo "🚀 Enabling timers..."
systemctl --user enable rezept-daily-import.timer
systemctl --user enable rezept-daily-migusto-import.timer

echo ""
echo "🚀 Starting timers..."
systemctl --user start rezept-daily-import.timer
systemctl --user start rezept-daily-migusto-import.timer

# Show status
echo ""
echo "📊 Status:"
echo ""
systemctl --user list-timers | grep rezept

echo ""
echo "✅ Daily import timers installed!"
echo ""
echo "Services:"
echo "  • TheMealDB Import: Täglich um 06:00 UTC"
echo "  • Migusto Import:   Täglich um 07:00 UTC"
echo ""
echo "Commands:"
echo "  systemctl --user list-timers | grep rezept           # Show timers"
echo "  systemctl --user status rezept-daily-import.timer    # Check status"
echo "  journalctl --user -u rezept-daily-import.service     # View logs"
echo "  systemctl --user start rezept-daily-import.service   # Run manually"
echo ""
