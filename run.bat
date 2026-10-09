@echo off
REM ====================================================================
REM Script Menjalankan YouTube Reels Generator (Windows)
REM ====================================================================
cd /d "%~dp0"

echo ==================================================
echo  Menjalankan YouTube to Facebook Reels Generator...
echo  Membuka Web UI: http://127.0.0.1:5000
echo  Tekan Ctrl+C untuk keluar dari server.
echo ==================================================

REM Otomatis buka browser lokal
start http://127.0.0.1:5000

REM Jalankan Flask
python app.py
pause
