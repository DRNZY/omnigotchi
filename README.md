# OmniGotchi

OmniGotchi is an autonomous e-ink cyberpet and desk companion built for the Raspberry Pi Zero 2 W and Waveshare 2.13-inch e-Paper display (250x122 monochrome).

Instead of capturing Wi-Fi handshakes, OmniGotchi combines coding activity, lossless music playback, and network telemetry into an evolving Tamagotchi with mood expressions, XP progression, and speech bubbles.

## Hardware requirements

- Raspberry Pi Zero 2 W (or Raspberry Pi 3/4/5)
- Waveshare 2.13" or 2.14" E-Paper HAT (250x122 resolution, V2/V3/V4)
- MicroSD card (8GB or larger)
- Micro-USB power supply

### Waveshare E-Paper GPIO Pinout

| Pin | Function | Raspberry Pi Physical Pin |
|---|---|---|
| VCC | 3.3V Power | Pin 1 (3V3) |
| GND | Ground | Pin 6 (GND) |
| DIN | SPI MOSI | Pin 19 (GPIO 10) |
| CLK | SPI SCLK | Pin 23 (GPIO 11) |
| CS | Chip Select | Pin 24 (GPIO 8) |
| DC | Data/Command | Pin 22 (GPIO 25) |
| RST | Reset | Pin 11 (GPIO 17) |
| BUSY | Busy Status | Pin 18 (GPIO 24) |

## Features

- **Dev and GitHub Sentinel:** Tracks your GitHub followers, stars, public repos, and local git commits across your projects.
- **Cadence and Audio Sync:** Detects playback from Cadence or MPRIS players, showing the track title, artist, and dancing animations.
- **Network Sentinel:** Measures live ping latency to 1.1.1.1, Wi-Fi signal strength, and host CPU temperature.
- **Tamagotchi RPG Engine:** Gains XP, levels up, and unlocks titles as you code and listen to music.
- **Ghosting-Resistant E-Ink Engine:** Fast partial screen refreshes with automatic full refresh cycles every 25 updates.
- **Desktop Simulator and Web Companion:** Includes a terminal ANSI mirror and web dashboard on port 8000 for development without hardware.

## Quick start (Desktop Simulator)

To preview and test OmniGotchi on your Linux desktop:

```bash
git clone https://github.com/DRNZY/omnigotchi.git
cd omnigotchi
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
./run_simulator.py
```

Open `http://localhost:8000` in your browser to view the live e-ink screen mirror and interact with your Gotchi.

## Installation on Raspberry Pi

1. Flash Raspberry Pi OS Lite (64-bit) onto your MicroSD card.
2. Boot your Raspberry Pi and clone the repository:
   ```bash
   git clone https://github.com/DRNZY/omnigotchi.git
   cd omnigotchi
   chmod +x setup.sh
   ./setup.sh
   ```
3. Start the background service:
   ```bash
   sudo systemctl start omnigotchi
   ```

Check logs at any time:
```bash
journalctl -u omnigotchi -f
```

## Configuration

Settings are saved in `~/.config/omnigotchi/state.json`. You can also configure environment variables:

- `GITHUB_TOKEN`: GitHub personal access token for higher API rate limits.
- `CADENCE_URL`: URL to your local Cadence player (default: `http://127.0.0.1:3001`).

## License

MIT License. Copyright (c) 2026 Darnell Dijksteel.
