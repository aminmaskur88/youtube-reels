#!/bin/bash
# ====================================================================
# Script Menjalankan YouTube Reels Generator (Linux / Termux)
# ====================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=================================================="
echo " Memulai YouTube to Facebook Reels Generator..."
echo " Web UI: http://127.0.0.1:5000"
echo " Tekan Ctrl+C untuk menghentikan server."
echo "=================================================="

# Jalankan server Flask
python3 app.py
