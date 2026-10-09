#!/bin/bash
# ====================================================================
# Script Instalasi YouTube Reels Generator (Linux / Termux / Ubuntu)
# ====================================================================

set -e

echo "=================================================="
echo " Memulai Instalasi YouTube to Facebook Reels"
echo "=================================================="

# Detect Termux or Standard Linux
if [ -d "/data/data/com.termux/files" ]; then
    echo "[1/3] Mendeteksi lingkungan Termux..."
    pkg update -y || true
    pkg install -y python ffmpeg || true
else
    echo "[1/3] Mendeteksi lingkungan Linux / Debian / Ubuntu..."
    if command -v apt-get &> /dev/null; then
        echo "Memeriksa paket sistem (python3, ffmpeg)..."
        sudo apt-get update -y || true
        sudo apt-get install -y python3 python3-pip ffmpeg || true
    fi
fi

# Install Python requirements
echo "[2/3] Menginstal dependensi Python dari requirements.txt..."
python3 -m pip install -r "$(dirname "$0")/requirements.txt"

# Make scripts executable
chmod +x "$(dirname "$0")/run.sh" 2>/dev/null || true

echo "[3/3] Memeriksa instalasi FFmpeg dan Python..."
python3 --version
ffmpeg -version | head -n 1

echo ""
echo "=================================================="
echo " Instalasi Berhasil!"
echo " Jalankan aplikasi dengan: ./run.sh"
echo "=================================================="
