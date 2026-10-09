import os
import re
import math
from typing import Dict, Any, Optional, Callable
import yt_dlp

YOUTUBE_REGEX = re.compile(
    r'^(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/(watch\?v=|embed/|v/|shorts/)?([a-zA-Z0-9_-]{11})(\S*)?$'
)

def is_valid_youtube_url(url: str) -> bool:
    """Check if the given string is a valid YouTube URL."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    return bool(YOUTUBE_REGEX.match(url) or "youtube.com" in url or "youtu.be" in url)

def format_duration(seconds: Optional[float]) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds is None or seconds < 0:
        return "00:00"
    seconds = int(round(seconds))
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def extract_smart_summary(description: str, max_length: int = 150) -> str:
    """Extract a concise first sentence or paragraph from description for reels summary."""
    if not description:
        return ""
    lines = [line.strip() for line in description.splitlines() if line.strip()]
    if not lines:
        return ""
    first_paragraph = lines[0]
    # If first paragraph has multiple sentences, take up to 2 sentences
    sentences = re.split(r'(?<=[.!?])\s+', first_paragraph)
    if sentences:
        summary = " ".join(sentences[:2])
    else:
        summary = first_paragraph
    if len(summary) > max_length:
        summary = summary[:max_length].rstrip() + "..."
    return summary

def generate_default_hashtags(title: str, tags: list) -> list:
    """Generate up to 5 clean hashtags from video tags or title words."""
    result = []
    # Add from video tags first
    if tags:
        for tag in tags:
            clean = re.sub(r'[^a-zA-Z0-9_]', '', tag)
            if clean and len(clean) >= 3:
                tag_str = f"#{clean}"
                if tag_str not in result:
                    result.append(tag_str)
            if len(result) >= 4:
                break
    
    # Add generic/reels hashtags if needed
    generic = ["#ReelsID", "#VideoViral", "#EdukasiKreatif"]
    for g in generic:
        if len(result) < 5 and g not in result:
            result.append(g)
            
    return result[:5]

def get_video_info(url: str) -> Dict[str, Any]:
    """
    Extracts metadata from YouTube video without downloading media.
    Throws Exception with friendly Indonesian message on failure.
    """
    if not is_valid_youtube_url(url):
        raise ValueError("URL YouTube tidak valid. Mohon masukkan URL video YouTube yang benar.")
    
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False)
            
        if not info:
            raise ValueError("Gagal mengambil informasi video YouTube.")
            
        title = info.get("title", "Video YouTube")
        channel = info.get("uploader") or info.get("channel") or "Unknown Channel"
        duration = float(info.get("duration") or 0.0)
        thumbnail = info.get("thumbnail") or ""
        description = info.get("description") or ""
        tags = info.get("tags") or []
        
        # Determine available resolutions
        formats = info.get("formats", [])
        heights = set()
        for f in formats:
            h = f.get("height")
            if h and isinstance(h, int) and h >= 240:
                heights.add(h)
                
        sorted_heights = sorted(list(heights), reverse=True)
        res_options = []
        for h in sorted_heights:
            if h >= 1080:
                res_options.append(f"{h}p (FHD)")
            elif h >= 720:
                res_options.append(f"{h}p (HD)")
            else:
                res_options.append(f"{h}p (SD)")
        if not res_options:
            res_options = ["1080p (FHD)", "720p (HD)", "480p (SD)"]
            
        max_height = sorted_heights[0] if sorted_heights else 1080
        source_res = f"{max_height}p"
        
        from metadata_manager import sanitize_folder_name
        
        suggested_folder = sanitize_folder_name(title)
        suggested_summary = extract_smart_summary(description)
        if not suggested_summary:
            suggested_summary = f"Simak cuplikan video menarik dari {channel}: {title}."
        suggested_tags = generate_default_hashtags(title, tags)
        
        return {
            "id": info.get("id"),
            "url": url,
            "title": title,
            "channel": channel,
            "duration": duration,
            "duration_formatted": format_duration(duration),
            "thumbnail": thumbnail,
            "source_resolution": source_res,
            "available_resolutions": res_options,
            "description": description[:400],
            "suggested_post_title": title[:100],
            "suggested_summary": suggested_summary,
            "suggested_hashtags": suggested_tags,
            "suggested_cta": "Bagikan pendapatmu di kolom komentar!",
            "suggested_folder_name": suggested_folder,
        }
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "Private video" in msg:
            raise ValueError("Video ini bersifat pribadi (private) dan tidak dapat diakses.")
        elif "Video unavailable" in msg:
            raise ValueError("Video tidak tersedia atau telah dihapus dari YouTube.")
        elif "Sign in" in msg or "bot" in msg:
            raise ValueError("YouTube meminta verifikasi login atau bot protection.")
        else:
            raise ValueError(f"Gagal mengambil metadata YouTube: {msg}")
    except Exception as e:
        raise ValueError(f"Terjadi kesalahan saat memeriksa URL: {str(e)}")

def download_youtube_video(
    url: str,
    quality: str = "best",
    output_dir: str = "downloads",
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    cancel_event: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Downloads YouTube video to output_dir with specified quality.
    Calls progress_callback with percentage and download info.
    Does NOT remove source file.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Quality format selector - prioritize avc1 (H.264) for ultra-fast mobile decoding
    if "1080" in quality:
        fmt = "bestvideo[vcodec^=avc1][height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best"
    elif "720" in quality:
        fmt = "bestvideo[vcodec^=avc1][height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best"
    elif "480" in quality:
        fmt = "bestvideo[vcodec^=avc1][height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]/best"
    else:
        fmt = "bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        
    def hook(d):
        if cancel_event and cancel_event.is_set():
            raise Exception("Download dibatalkan oleh pengguna.")
            
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            percent = 0.0
            if total > 0:
                percent = round((downloaded / total) * 100, 1)
            
            speed = d.get("speed") or 0
            speed_str = f"{round(speed / 1024 / 1024, 2)} MB/s" if speed else "N/A"
            eta = d.get("eta") or 0
            eta_str = f"{eta}s" if eta else "N/A"
            
            if progress_callback:
                progress_callback({
                    "status": "downloading",
                    "percent": percent,
                    "downloaded_bytes": downloaded,
                    "total_bytes": total,
                    "speed": speed_str,
                    "eta": eta_str,
                    "filename": d.get("filename", "")
                })
        elif d.get("status") == "finished":
            if progress_callback:
                progress_callback({
                    "status": "finished",
                    "percent": 100.0,
                    "filename": d.get("filename", "")
                })

    out_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    
    ydl_opts = {
        'format': fmt,
        'outtmpl': out_template,
        'merge_output_format': 'mp4',
        'progress_hooks': [hook],
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get("id")
            title = info.get("title", "")
            duration = float(info.get("duration") or 0.0)
            channel = info.get("uploader") or info.get("channel") or ""
            
        # Determine actual file downloaded
        expected_mp4 = os.path.join(output_dir, f"{video_id}.mp4")
        if os.path.exists(expected_mp4):
            final_path = expected_mp4
        else:
            # Look for file starting with video_id
            candidates = [f for f in os.listdir(output_dir) if f.startswith(video_id)]
            if candidates:
                final_path = os.path.join(output_dir, candidates[0])
            else:
                raise FileNotFoundError("File hasil download tidak ditemukan di direktori tujuan.")
                
        return {
            "file_path": os.path.abspath(final_path),
            "id": video_id,
            "title": title,
            "duration": duration,
            "channel": channel
        }
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "Private video" in msg:
            raise RuntimeError("Video ini berstatus private dan tidak dapat diunduh.")
        elif "Video unavailable" in msg:
            raise RuntimeError("Video tidak tersedia di YouTube.")
        elif "HTTP Error 429" in msg:
            raise RuntimeError("Terlalu banyak permintaan ke YouTube (Rate Limit). Coba beberapa saat lagi.")
        else:
            raise RuntimeError(f"Gagal mengunduh video: {msg}")
    except Exception as e:
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Download dihentikan oleh pengguna.")
        raise RuntimeError(f"Terjadi kesalahan saat download: {str(e)}")
