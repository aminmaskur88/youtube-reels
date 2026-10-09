import os
import sys
import time
import uuid
import json
import queue
import shutil
import zipfile
import threading
import subprocess
from datetime import datetime
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify, Response, send_file, send_from_directory

from downloader import is_valid_youtube_url, get_video_info, download_youtube_video
from processor import split_and_process_video, check_ffmpeg, check_ffprobe, get_media_info
from metadata_manager import sanitize_folder_name, get_unique_folder_path, generate_post_meta, save_source_copyright_info

# Initialize Flask application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
POSTS_DIR = os.path.join(BASE_DIR, "Post")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
TEMPLATE_DIR = os.path.join(BASE_DIR, "Template")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(TEMPLATE_DIR, exist_ok=True)

TEMPLATE_DIRS = [
    TEMPLATE_DIR,
    "/data/data/com.termux/files/home/VideoTemplate/Template"
]

def get_available_templates():
    """Discover available PNG templates from local and VideoTemplate directories."""
    templates = []
    seen = set()
    for tdir in TEMPLATE_DIRS:
        if os.path.exists(tdir):
            for f in sorted(os.listdir(tdir)):
                if f.lower().endswith(".png") and f not in seen:
                    templates.append({
                        "name": os.path.splitext(f)[0],
                        "filename": f,
                        "path": os.path.join(tdir, f)
                    })
                    seen.add(f)
    return templates

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.config['JSON_AS_ASCII'] = False

# Active tasks repository
tasks_lock = threading.Lock()
tasks: Dict[str, Dict[str, Any]] = {}

class TaskWorker:
    def __init__(self, task_id: str, payload: Dict[str, Any]):
        self.task_id = task_id
        self.payload = payload
        self.cancel_event = threading.Event()
        self.log_queue = queue.Queue()
        self.state = {
            "task_id": task_id,
            "status": "pending",  # pending, downloading, processing, completed, error, cancelled
            "step": "Menyiapkan antrian proses...",
            "percent": 0.0,
            "clip_current": 0,
            "clip_total": 0,
            "logs": [],
            "error": None,
            "result": None
        }

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        self.state["logs"].append(formatted)
        self.log_queue.put({"type": "log", "message": formatted})
        print(f"[{self.task_id}] {formatted}")

    def update_progress(self, step: str, percent: float, **kwargs):
        self.state["step"] = step
        self.state["percent"] = round(percent, 1)
        for k, v in kwargs.items():
            self.state[k] = v
        self.log_queue.put({
            "type": "progress",
            "step": self.state["step"],
            "percent": self.state["percent"],
            "clip_current": self.state.get("clip_current", 0),
            "clip_total": self.state.get("clip_total", 0),
            "status": self.state["status"]
        })

    def run(self):
        try:
            self.state["status"] = "downloading"
            self.log("Memulai alur kerja pembuatan Reels...")
            
            # Step 0: Check FFmpeg
            if not check_ffmpeg():
                raise RuntimeError("FFmpeg tidak ditemukan di sistem. Silakan install FFmpeg terlebih dahulu.")

            url = self.payload.get("url", "").strip()
            if not is_valid_youtube_url(url):
                raise ValueError("URL YouTube tidak valid.")
                
            quality = self.payload.get("quality", "best")
            clip_dur = float(self.payload.get("clip_duration", 60.0))
            mode = self.payload.get("mode", "cinematic_blur")
            cinematic_opts = self.payload.get("cinematic_opts", {})
            visual_opts = self.payload.get("visual_opts", {})
            audio_opts = self.payload.get("audio_opts", {})
            part_opts = self.payload.get("part_opts", {})
            header_opts = self.payload.get("header_opts", {})
            user_meta = self.payload.get("metadata", {})
            user_source = self.payload.get("source_info", {})

            # Step 1: Downloading
            self.update_progress("Mengambil informasi video...", 5.0)
            self.log(f"Menghubungi YouTube untuk URL: {url}")
            
            def dl_hook(d):
                if self.cancel_event.is_set():
                    raise RuntimeError("Download dihentikan oleh pengguna.")
                if d.get("status") == "downloading":
                    pct = 5.0 + (d.get("percent", 0.0) * 0.35)  # 5% to 40%
                    speed = d.get("speed", "N/A")
                    eta = d.get("eta", "N/A")
                    step_txt = f"Download: {d.get('percent', 0.0):.1f}% ({speed}, ETA: {eta})"
                    self.update_progress(step_txt, pct)
                elif d.get("status") == "finished":
                    self.update_progress("Download selesai. Mempersiapkan media...", 40.0)
                    self.log("File video berhasil diunduh.")

            dl_res = download_youtube_video(
                url=url,
                quality=quality,
                output_dir=DOWNLOADS_DIR,
                progress_callback=dl_hook,
                cancel_event=self.cancel_event
            )
            
            src_file = dl_res["file_path"]
            src_title = dl_res.get("title", "Video YouTube")
            src_channel = dl_res.get("channel", "Unknown Channel")
            self.log(f"Video tersimpan di: {src_file}")

            # Step 2: Preparing Output Folder in Post/
            self.state["status"] = "processing"
            self.update_progress("Mempersiapkan folder hasil...", 42.0)
            
            req_folder_name = user_meta.get("folder_name", "")
            if not req_folder_name:
                req_folder_name = sanitize_folder_name(src_title)
            else:
                req_folder_name = sanitize_folder_name(req_folder_name)
                
            unique_post_dir = get_unique_folder_path(POSTS_DIR, req_folder_name)
            folder_basename = os.path.basename(unique_post_dir)
            os.makedirs(unique_post_dir, exist_ok=True)
            self.log(f"Folder tujuan klip: Post/{folder_basename}")

            # Step 3: Splitting and Portrait Conversion
            self.update_progress("Mempersiapkan video...", 45.0)
            
            def proc_hook(p):
                if self.cancel_event.is_set():
                    raise RuntimeError("Pemrosesan dihentikan oleh pengguna.")
                # Map 45% - 95%
                overall_proc_pct = 45.0 + (p.get("percent", 0.0) * 0.50)
                step_msg = p.get("step", "Memproses klip...")
                self.update_progress(
                    step_msg,
                    overall_proc_pct,
                    clip_current=p.get("clip_current", 0),
                    clip_total=p.get("clip_total", 0)
                )

            template_choice = self.payload.get("template_choice") or cinematic_opts.get("template_choice")
            template_path = None
            if template_choice:
                for t in get_available_templates():
                    if t["filename"] == template_choice or t["name"] == template_choice or t["path"] == template_choice:
                        template_path = t["path"]
                        break

            self.log(f"Memotong video menjadi segmen per {clip_dur:.0f} detik dengan Mode: {mode.upper()}...")
            generated_clips = split_and_process_video(
                input_path=src_file,
                output_dir=unique_post_dir,
                clip_duration=clip_dur,
                mode=mode,
                cinematic_opts=cinematic_opts,
                visual_opts=visual_opts,
                audio_opts=audio_opts,
                part_opts=part_opts,
                progress_callback=proc_hook,
                cancel_event=self.cancel_event,
                template_path=template_path,
                meta_info=user_meta,
                header_opts=header_opts
            )
            
            self.log(f"Berhasil menghasilkan {len(generated_clips)} klip portrait 9:16.")

            # Step 4: Metadata Generation
            self.update_progress("Membuat metadata...", 96.0)
            self.log("Menyimpan metadata post_meta.json...")
            
            meta_json = generate_post_meta(
                output_dir=unique_post_dir,
                post_title=user_meta.get("post_title") or src_title,
                summary=user_meta.get("summary") or f"Cuplikan video {src_title}.",
                hashtags=user_meta.get("hashtags") or ["#ReelsID", "#VideoViral"],
                cta=user_meta.get("cta") or "Bagikan pendapatmu di komentar!",
                image_count=int(user_meta.get("image_count", 0)),
                generated_at=user_meta.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Step 5: Save Audit Copyright Info
            source_info_data = {
                "original_url": url,
                "original_title": src_title,
                "original_channel": src_channel,
                "source_duration": dl_res.get("duration", 0),
                "license_status": user_source.get("license_status", "Belum diketahui")
            }
            save_source_copyright_info(unique_post_dir, source_info_data)
            self.log("Informasi lisensi dan sumber tersimpan.")

            # Step 6: Completion
            clip_relative_urls = []
            for c in generated_clips:
                c_name = os.path.basename(c)
                clip_relative_urls.append({
                    "filename": c_name,
                    "url": f"/Post/{folder_basename}/{c_name}",
                    "size_mb": round(os.path.getsize(c) / (1024 * 1024), 2)
                })

            result_data = {
                "folder_name": folder_basename,
                "folder_path": unique_post_dir,
                "clip_count": len(generated_clips),
                "clips": clip_relative_urls,
                "metadata": meta_json
            }

            self.state["status"] = "completed"
            self.state["result"] = result_data
            self.update_progress("Selesai.", 100.0)
            self.log("Seluruh proses berhasil diselesaikan!")
            self.log_queue.put({"type": "completed", "result": result_data})

        except Exception as e:
            if self.cancel_event.is_set():
                self.state["status"] = "cancelled"
                self.state["error"] = "Proses dibatalkan oleh pengguna."
                self.log("Proses telah dibatalkan.")
                self.log_queue.put({"type": "cancelled"})
            else:
                self.state["status"] = "error"
                self.state["error"] = str(e)
                self.log(f"ERROR: {str(e)}")
                self.log_queue.put({"type": "error", "error": str(e)})

# Routes
@app.route("/")
def index():
    return render_template(
        "index.html",
        ffmpeg_available=check_ffmpeg(),
        ffprobe_available=check_ffprobe(),
        templates=get_available_templates()
    )

@app.route("/api/templates")
def api_templates():
    return jsonify({
        "success": True,
        "templates": get_available_templates()
    })

@app.route("/api/system-status")
def system_status():
    return jsonify({
        "ffmpeg": check_ffmpeg(),
        "ffprobe": check_ffprobe(),
        "downloads_dir": DOWNLOADS_DIR,
        "posts_dir": POSTS_DIR
    })

@app.route("/api/video-info", methods=["POST"])
def video_info_route():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"success": False, "error": "URL YouTube tidak boleh kosong."}), 400
        
    try:
        info = get_video_info(url)
        return jsonify({"success": True, "data": info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/start-process", methods=["POST"])
def start_process_route():
    payload = request.get_json() or {}
    url = payload.get("url", "").strip()
    if not url:
        return jsonify({"success": False, "error": "URL YouTube harus diisi."}), 400

    task_id = uuid.uuid4().hex[:12]
    worker = TaskWorker(task_id, payload)
    
    with tasks_lock:
        tasks[task_id] = worker
        
    thread = threading.Thread(target=worker.run, daemon=True)
    thread.start()
    
    return jsonify({"success": True, "task_id": task_id})

@app.route("/api/latest-task")
def latest_task_route():
    with tasks_lock:
        if not tasks:
            return jsonify({"has_task": False})
        
        # Check if there is an active running task first
        for tid, worker in reversed(list(tasks.items())):
            if worker.state["status"] in ["downloading", "processing", "pending"]:
                return jsonify({
                    "has_task": True,
                    "task_id": tid,
                    "state": worker.state,
                    "is_active": True
                })
        
        # Otherwise get the last task
        tid, worker = list(tasks.items())[-1]
        return jsonify({
            "has_task": True,
            "task_id": tid,
            "state": worker.state,
            "is_active": False
        })

@app.route("/api/progress/<task_id>")
def progress_stream(task_id: str):
    with tasks_lock:
        worker = tasks.get(task_id)
        
    if not worker:
        return jsonify({"error": "Task tidak ditemukan"}), 404

    def generate_events():
        # First send current snapshot
        init_data = json.dumps({
            "type": "progress",
            "step": worker.state["step"],
            "percent": worker.state["percent"],
            "clip_current": worker.state.get("clip_current", 0),
            "clip_total": worker.state.get("clip_total", 0),
            "status": worker.state["status"],
            "result": worker.state.get("result"),
            "error": worker.state.get("error")
        })
        yield f"data: {init_data}\n\n"
        
        # Re-send all historical logs so refreshing browser restores full terminal history
        for hist_log in worker.state.get("logs", []):
            yield f"data: {json.dumps({'type': 'log', 'message': hist_log})}\n\n"
        
        while True:
            try:
                msg = worker.log_queue.get(timeout=2.0)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("type") in ["completed", "error", "cancelled"]:
                    break
            except queue.Empty:
                # Keep-alive heartbeat
                if worker.state["status"] in ["completed", "error", "cancelled"]:
                    break
                yield ": keep-alive\n\n"

    return Response(
        generate_events(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )

@app.route("/api/status/<task_id>")
def task_status(task_id: str):
    with tasks_lock:
        worker = tasks.get(task_id)
    if not worker:
        return jsonify({"success": False, "error": "Task tidak ditemukan"}), 404
        
    return jsonify({"success": True, "state": worker.state})

@app.route("/api/cancel/<task_id>", methods=["POST"])
def cancel_task(task_id: str):
    with tasks_lock:
        worker = tasks.get(task_id)
    if not worker:
        return jsonify({"success": False, "error": "Task tidak ditemukan"}), 404
        
    worker.cancel_event.set()
    return jsonify({"success": True, "message": "Permintaan pembatalan diterima."})

@app.route("/Post/<path:filepath>")
def serve_post_files(filepath: str):
    """Serve files in Post directory with partial range support for smooth video streaming."""
    return send_from_directory(POSTS_DIR, filepath, conditional=True)

@app.route("/api/download-zip/<folder_name>")
def download_zip(folder_name: str):
    """Download the whole content folder as a zip package."""
    clean_name = sanitize_folder_name(folder_name)
    target_dir = os.path.join(POSTS_DIR, clean_name)
    if not os.path.exists(target_dir):
        return jsonify({"error": "Folder tidak ditemukan"}), 404
        
    zip_filename = f"{clean_name}.zip"
    zip_path = os.path.join(TEMP_DIR, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(target_dir):
            for file in files:
                file_full = os.path.join(root, file)
                rel_path = os.path.relpath(file_full, target_dir)
                zipf.write(file_full, rel_path)
                
    return send_file(zip_path, as_attachment=True, download_name=zip_filename)

@app.route("/api/open-folder", methods=["POST"])
def open_folder_route():
    """Attempt to open folder in system file browser if possible."""
    data = request.get_json() or {}
    folder_name = data.get("folder_name", "")
    target_path = os.path.join(POSTS_DIR, sanitize_folder_name(folder_name))
    
    if not os.path.exists(target_path):
        target_path = POSTS_DIR
        
    abs_path = os.path.abspath(target_path)
    opened = False
    
    try:
        if sys.platform == "win32":
            os.startfile(abs_path)
            opened = True
        elif sys.platform == "darwin":
            subprocess.run(["open", abs_path], check=False)
            opened = True
        else:
            # Linux / Termux
            if shutil.which("termux-open"):
                subprocess.run(["termux-open", abs_path], check=False)
                opened = True
            elif shutil.which("xdg-open"):
                subprocess.run(["xdg-open", abs_path], check=False)
                opened = True
    except Exception:
        opened = False
        
    return jsonify({
        "success": True,
        "opened": opened,
        "path": abs_path,
        "message": f"Folder tersimpan di: {abs_path}"
    })

if __name__ == "__main__":
    # Host on 0.0.0.0 so user can access from phone browser via localhost or local network
    port = int(os.environ.get("PORT", 5000))
    print(f"\n==================================================")
    print(f" YouTube Reels Generator berjalan di:")
    print(f" -> http://127.0.0.1:{port}")
    print(f" -> http://localhost:{port}")
    print(f"==================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
