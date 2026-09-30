#!/usr/bin/env bash
# OmniGotchi Installation and Setup Script for Raspberry Pi OS
set -e

echo "=========================================================="
echo "          OmniGotchi Raspberry Pi Zero 2 W Setup         "
echo "=========================================================="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_NAME="$(whoami)"

echo "[1/5] Updating system packages & installing hardware dependencies..."
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv python3-pil python3-psutil git raspi-config

echo "[2/5] Enabling SPI interface on Raspberry Pi..."
if command -v raspi-config >/dev/null 2>&1; then
    sudo raspi-config nonint do_spi 0
    echo "-> SPI interface enabled successfully."
else
    echo "-> Note: raspi-config not found (skipping nonint SPI setup)."
fi

echo "[3/5] Setting up Python virtual environment..."
cd "$PROJECT_DIR"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv --system-site-packages
fi
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "[4/5] Installing Waveshare e-Paper Python library..."
if [ ! -d "e-Paper" ]; then
    git clone https://github.com/waveshare/e-Paper.git /tmp/waveshare-epaper
    cp -r /tmp/waveshare-epaper/RaspberryPi_JetsonNano/python/lib/waveshare_epd "$PROJECT_DIR/omnigotchi/display/" || true
    rm -rf /tmp/waveshare-epaper
fi

echo "[5/5] Creating and enabling systemd background service (omnigotchi.service)..."
SERVICE_FILE="/etc/systemd/system/omnigotchi.service"
sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=OmniGotchi Autonomous E-Ink Cyberpet
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/.venv/bin/python3 $PROJECT_DIR/main.py --hardware
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable omnigotchi.service

echo ""
echo "=========================================================="
echo "          OmniGotchi Installation Complete!              "
echo "=========================================================="
echo "To start OmniGotchi now:"
echo "  sudo systemctl start omnigotchi"
echo ""
echo "To check live logs:"
echo "  journalctl -u omnigotchi -f"
echo ""
echo "To run desktop simulator with live terminal/web mirror:"
echo "  ./run_simulator.py"
echo "=========================================================="
