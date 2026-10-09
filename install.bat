@echo off
REM ====================================================================
REM Script Instalasi YouTube Reels Generator (Windows)
REM ====================================================================
echo ==================================================
echo  Memulai Instalasi YouTube to Facebook Reels (Windows)
echo ==================================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak terdeteksi!
    echo Silakan install Python dari https://www.python.org/
    echo Pastikan mencentang "Add Python to PATH" saat instalasi.
    pause
    exit /b 1
)

REM Check FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [PERINGATAN] FFmpeg belum terdeteksi di PATH!
    echo Aplikasi memerlukan FFmpeg untuk memotong dan mengonversi video.
    echo Silakan unduh FFmpeg dari https://gyan.dev/ffmpeg/builds/ dan tambahkan ke PATH.
)

REM Install dependencies
echo Menginstal dependensi Python dari requirements.txt...
pip install -r requirements.txt

echo ==================================================
echo  Instalasi selesai!
echo  Jalankan aplikasi dengan klik dua kali "run.bat"
echo ==================================================
pause
