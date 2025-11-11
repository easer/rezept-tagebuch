#!/bin/bash
# Install Quadlets to ~/.config/containers/systemd/
# This script installs Pod + Container Quadlets for Rezept-Tagebuch

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="$HOME/.config/containers/systemd"

echo "=== Quadlets Installation ==="
echo ""

# Create systemd directory
mkdir -p "$SYSTEMD_DIR"

# Function to install environment
install_env() {
    local env=$1
    echo "Installing ${env^^} Quadlets..."

    if [ -d "$SCRIPT_DIR/$env" ]; then
        cp "$SCRIPT_DIR/$env"/*.{pod,container,service,timer} "$SYSTEMD_DIR/" 2>/dev/null || true
        echo "  ✓ ${env^^} Quadlets copied"
    else
        echo "  ✗ ${env^^} directory not found"
        return 1
    fi
}

# Install based on argument or all
if [ $# -eq 0 ]; then
    echo "Installing ALL environments (prod, dev, test)..."
    echo ""
    install_env "prod"
    install_env "dev"
    install_env "test"
elif [ "$1" == "prod" ] || [ "$1" == "dev" ] || [ "$1" == "test" ]; then
    install_env "$1"
else
    echo "Usage: $0 [prod|dev|test]"
    echo "  No argument: Install all environments"
    echo "  prod:        Install PROD only"
    echo "  dev:         Install DEV only"
    echo "  test:        Install TEST only"
    exit 1
fi

echo ""
echo "Reloading systemd daemon..."
systemctl --user daemon-reload

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Installed to: $SYSTEMD_DIR"
echo ""
echo "Next steps:"
echo "  1. Enable services:"
echo "     systemctl --user enable rezept-prod-app.container"
echo "     systemctl --user enable rezept-dev-app.container"
echo ""
echo "  2. Start services:"
echo "     systemctl --user start rezept-prod-app.container"
echo "     systemctl --user start rezept-dev-app.container"
echo ""
echo "  3. Check status:"
echo "     podman pod ps"
echo "     systemctl --user list-units 'rezept-*'"
echo ""
