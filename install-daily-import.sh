#!/bin/bash
# Install systemd timer for daily TheMealDB import

echo "📅 Installing daily import timer..."

# Copy service and timer files
sudo cp rezept-daily-import.service /etc/systemd/system/
sudo cp rezept-daily-import.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start timer
sudo systemctl enable rezept-daily-import.timer
sudo systemctl start rezept-daily-import.timer

# Show status
sudo systemctl status rezept-daily-import.timer

echo ""
echo "✅ Daily import timer installed!"
echo "⏰ Runs every day at 06:00"
echo ""
echo "Commands:"
echo "  sudo systemctl status rezept-daily-import.timer  # Check timer status"
echo "  sudo journalctl -u rezept-daily-import.service   # View logs"
echo "  sudo systemctl start rezept-daily-import.service # Run manually"
