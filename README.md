# 🎬 YouTube to Facebook Reels Generator (Portrait 9:16)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/Flask-3.0%2B-black?logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/FFmpeg-Supported-green?logo=ffmpeg&logoColor=white" alt="FFmpeg" />
  <img src="https://img.shields.io/badge/yt--dlp-Latest-red?logo=youtube&logoColor=white" alt="yt-dlp" />
  <img src="https://img.shields.io/badge/Platform-Termux%20%7C%20Linux%20%7C%20Windows-brightgreen" alt="Platform Support" />
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" />
  <img src="https://img.shields.io/badge/Release-v1.0.0-orange" alt="Release v1.0.0" />
</p>

Aplikasi web lokal serba otomatis berbasis **Python**, **Flask**, **yt-dlp**, dan **FFmpeg** untuk mengunduh video YouTube (video panjang maupun Shorts), mengonversinya secara presisi ke rasio portrait **9:16 (1080×1920)** dengan berbagai mode visual (Cinematic Blur Background, Template Frame PNG, Center Crop, Fit to Portrait), memotong video secara berurutan menjadi klip-klip pendek siap unggah untuk **Facebook Reels / Instagram Reels / TikTok / YouTube Shorts**, serta membuat file metadata **`post_meta.json`**.

---

## 🏷️ Repository Tags & Topics

`youtube` • `facebook-reels` • `reels-generator` • `video-processing` • `ffmpeg` • `yt-dlp` • `flask` • `python` • `termux` • `video-editor` • `content-creator` • `automation`

---

## 🚀 Fitur Unggulan

### 1. 🖥️ Web UI Interaktif & Responsif
- **Akses Fleksibel**: Dapat dibuka langsung melalui browser desktop (`http://127.0.0.1:5000`) atau dari HP via Termux di jaringan lokal Wi-Fi.
- **Informasi Video Instan**: Menampilkan thumbnail, judul, channel, durasi asli, resolusi, serta estimasi jumlah part klip.
- **Pilihan Kualias Download**: *Best Quality*, 1080p, 720p, atau 480p.
- **Real-time Monitoring**: Server-Sent Events (SSE) menampilkan progres download, konversi per klip, persentase FFmpeg, ETA, dan log konsol secara langsung tanpa me-refresh halaman.
- **Kontrol Penuh**: Tersedia tombol pembatalan proses kapan saja dengan aman.

### 2. 🎞️ 4 Mode Layout Portrait 9:16 (1080×1920)
- **Mode B — Cinematic Blur Background (Default)**:
  - Latar belakang diperbesar memenuhi kanvas 9:16 dengan blur halus (*boxblur/gblur*), kecerahan redup, dan saturasi optimal.
  - Video utama di tengah kanvas tetap proporsional tanpa distorsi atau gepeng.
  - Opsi: *Blur Intensity*, *Background Dimming*, *Saturation*, *Contrast*, *Foreground Scale*, *Foreground Position (Center / Top / Bottom)*, dan *Vignette*.
- **Mode D — Template Frame PNG**:
  - Mendukung bingkai template transparan PNG kustom dari folder `Template/` (rasio 9:16 / 1080×1920).
  - Posisi slot video dan teks dihitung otomatis agar tidak bertumpuk dengan header template.
- **Mode A — Center Crop**:
  - Memotong video landscape dari bagian tengah secara proporsional mengisi kanvas 9:16.
- **Mode C — Fit to Portrait**:
  - Video asli diposisikan utuh di tengah dengan background solid hitam rapi.

### 3. ✂️ Pemotongan Klip Berurutan & Presisi
- **Pilihan Durasi Klip**: 30 detik, 45 detik, 60 detik, atau Custom (15s – 300s).
- **Penomoran Runtut**: Pemotongan video dari awal sampai akhir tanpa jeda yang hilang (`clip_001.mp4`, `clip_002.mp4`, dst.).
- **Segmentasi Terakhir**: Sisa durasi video di bagian akhir tetap tersimpan utuh meskipun kurang dari target durasi.
- **Sinkronisasi Presisi**: Audio dan video tetap *in-sync* dari detik pertama hingga akhir.

### 4. ✍️ Sistem Teks & Part Overlay Dinamis
- **Font Kustom Berkualitas**: Menggunakan font `junction.bold.otf` dengan warna putih tajam dan border outline hitam tebal (`borderw=3`).
- **Dynamic Font Scaling**: Ukuran font otomatis menyesuaikan panjang teks agar selalu pas di layar.
- **Auto-Wrap Text**: Teks dibungkus rapi sesuai batas aman 90% lebar kanvas (`TEXT_WIDTH_SCALE = 0.90`).
- **Penempatan Aman**: Mengikuti standar margin aman 18% dari batas bawah kanvas dan batas atas header.
- **Label Template Part**: Template penomoran part fleksibel (misal: `PART {n}`, `BAGIAN {n}`, dsb.).

### 5. 🎛️ Modul Audio FFmpeg
- **Normalisasi Loudness (EBU R128)**: Menyamakan volume agar standar siaran media sosial tanpa distorsi pecah/cempreng.
- **Noise Reduction**: Filter `afftdn` untuk mengurangi dengung dan noise latar belakang.
- **Volume & Gain**: Penyesuaian desibel (dB) sesuai kebutuhan.
- **Equalizer**: Pilihan Bass Boost dan Treble Boost.
- **Efek Fade In & Fade Out**: Transisi audio halus di awal dan akhir klip.
- **Creative Pitch & Tempo Shift**: Penggeser pitch kreatif (0.85x – 1.15x) dengan kompensasi tempo otomatis.

### 6. 🎨 Modul Efek Visual Kreatif
- **Color Grading**: Penyesuaian Kecerahan (*brightness*), Kontras (*contrast*), dan Saturasi (*saturation*).
- **Filter Sharpen**: Menajamkan detail visual video.
- **Cinematic Film Look**: Nuansa warna film hangat dan kontras sinematik.
- **Subtle Slow Zoom In**: Gerakan kamera halus (Ken Burns effect).
- **Creative Glitch Effect**: Efek glitch berkala dengan intensitas yang dapat disesuaikan.

### 7. 📦 Struktur Output & Generator `post_meta.json`
Setiap video yang diproses disimpan rapi dalam sub-folder tersendiri:
```text
Post/
└── <nama-konten-sanitasi>/
    ├── clip_001.mp4
    ├── clip_002.mp4
    ├── clip_003.mp4
    ├── post_meta.json
    ├── source_info.json
    └── upload_status.json
```

Contoh isi file `post_meta.json`:
```json
{
  "post_title": "AI Cerdas Sortir Tomat Modern",
  "summary": "Teknologi AI ini memindai tomat dalam hitungan detik untuk mendeteksi kematangan dan kerusakan secara otomatis.",
  "hashtags": [
    "#AISortirTomat",
    "#PertanianModern",
    "#TeknologiAI"
  ],
  "cta": "Teknologi apa lagi yang bisa bantu petani Indonesia?",
  "image_count": 0,
  "generated_at": "2026-10-09 15:30:00"
}
```

Format ini kompatibel langsung dengan bot auto-post media sosial (seperti [AutoPostFbSelenium](https://github.com/aminmaskur88/AutoPostFbSelenium)).

---

## 📁 Struktur Direktori

```text
youtube-reels/
├── app.py                  # Server web Flask, REST API, & Event Stream SSE
├── downloader.py           # yt-dlp metadata extractor & downloader
├── processor.py            # FFmpeg filter builder, splitter, & portrait engine
├── metadata_manager.py     # Generator post_meta.json & folder sanitization
├── test_suite.py           # Unit & integration test suite
├── requirements.txt        # Daftar dependensi Python
├── install.sh              # Script otomatis instalasi (Linux / Termux)
├── run.sh                  # Script eksekusi aplikasi (Linux / Termux)
├── install.bat             # Script otomatis instalasi (Windows)
├── run.bat                 # Script eksekusi aplikasi (Windows)
├── .gitignore              # Konfigurasi ignore file Git
├── LICENSE                 # Lisensi open-source (MIT)
├── README.md               # Dokumentasi lengkap proyek
├── Template/               # Folder template frame PNG kustom (didukung .gitkeep)
├── fonts/                  # Font yang digunakan untuk subtitle / part text
│   └── junction.bold.otf
├── templates/
│   └── index.html          # Antarmuka web pengguna (HTML5)
├── static/
│   ├── style.css           # Desain modern tema gelap (Dark Theme)
│   └── script.js           # Logika interaktif antarmuka & SSE listener
├── downloads/              # Arsip unduhan video mentah (didukung .gitkeep)
├── temp/                   # Cache pemrosesan sementara (didukung .gitkeep)
└── Post/                   # Folder hasil render klip Reels (didukung .gitkeep)
```

---

## 🛠️ Panduan Instalasi & Menjalankan

### A. Android (Termux)
1. **Perbarui paket dan instal paket yang dibutuhkan**:
   ```bash
   pkg update -y && pkg upgrade -y
   pkg install -y python ffmpeg git
   ```
2. **Kloning repository**:
   ```bash
   git clone https://github.com/aminmaskur88/youtube-reels.git
   cd youtube-reels
   ```
3. **Jalankan installer**:
   ```bash
   chmod +x install.sh run.sh
   ./install.sh
   ```
4. **Jalankan server aplikasi**:
   ```bash
   ./run.sh
   ```
5. Buka peramban (browser) di smartphone Anda:
   ```text
   http://127.0.0.1:5000
   ```

---

### B. Linux (Debian / Ubuntu / Kali / dsb.)
1. **Instal dependensi sistem**:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip ffmpeg git
   ```
2. **Kloning repository**:
   ```bash
   git clone https://github.com/aminmaskur88/youtube-reels.git
   cd youtube-reels
   ```
3. **Instal dependensi Python**:
   ```bash
   chmod +x install.sh run.sh
   ./install.sh
   ```
4. **Jalankan aplikasi**:
   ```bash
   ./run.sh
   ```
5. Buka browser di: `http://127.0.0.1:5000`

---

### C. Windows
1. Pastikan **Python 3.9+** telah terinstal (pastikan opsi *"Add Python to PATH"* dicentang saat instalasi).
2. Unduh **FFmpeg** (misal dari [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)) dan pastikan `ffmpeg.exe` serta `ffprobe.exe` terbaca pada Command Prompt (PATH).
3. Buka folder `youtube-reels`:
   - Klik dua kali **`install.bat`** (untuk mengunduh modul Python yang dibutuhkan).
   - Klik dua kali **`run.bat`** (untuk menjalankan server dan browser akan otomatis terbuka).

---

## 🌐 Dokumentasi REST API

| Endpoint | Method | Deskripsi |
| :--- | :---: | :--- |
| `/` | `GET` | Halaman Web UI utama generator reels |
| `/api/templates` | `GET` | Mengambil daftar file bingkai template PNG yang tersedia |
| `/api/system-status` | `GET` | Memeriksa ketersediaan Python, FFmpeg, dan memori sistem |
| `/api/video-info` | `POST` | Mengekstrak metadata video YouTube dari URL via yt-dlp |
| `/api/start-process` | `POST` | Memulai pipeline download, render portrait 9:16, split, dan metadata |
| `/api/latest-task` | `GET` | Mengambil ID task pemrosesan yang sedang berjalan |
| `/api/progress/<task_id>` | `GET` | Server-Sent Events (SSE) streaming data progress FFmpeg realtime |
| `/api/status/<task_id>` | `GET` | Memeriksa status akhir proses secara terperinci |
| `/api/cancel/<task_id>` | `POST` | Membatalkan task pemrosesan yang sedang berjalan |
| `/api/download-zip/<folder_name>` | `GET` | Mengunduh seluruh klip dan metadata dalam 1 file arsip `.zip` |
| `/api/open-folder` | `POST` | Membuka folder output pada file manager sistem lokal |

---

## ⚠️ Informasi Hak Cipta & Panduan Penggunaan

- **Hak Cipta Konten**: Keberadaan video di YouTube tidak secara otomatis menjadikannya materi bebas hak cipta (*public domain*). Pastikan Anda telah memiliki izin atau menggunakan video dengan lisensi Creative Commons sebelum mengunggah ulang ke media sosial.
- **Sistem Moderasi Platform**: Efek filter visual dan modifikasi audio yang disediakan bertujuan untuk estetika dan *creative editing*, bukan untuk melanggar Pedoman Komunitas atau menghindari sistem deteksi hak cipta Facebook, YouTube, atau platform lainnya.
- **Tanggung Jawab Pengguna**: Segala materi yang dihasilkan dan diunggah sepenuhnya menjadi tanggung jawab masing-masing pengguna.

---

## 👤 Pengembang & Kontributor

- **Amin Maskur**
  - GitHub: [@aminmaskur88](https://github.com/aminmaskur88)
  - Proyek Terkait: [AutoPostFbSelenium](https://github.com/aminmaskur88/AutoPostFbSelenium), [VideoTemplate](https://github.com/aminmaskur88/VideoTemplate)

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah lisensi open-source [MIT License](LICENSE). Anda bebas menggunakan, memodifikasi, dan mendistribusikan kode ini untuk keperluan pribadi maupun komersial.
