import os
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

def sanitize_folder_name(name: str) -> str:
    """
    Sanitize folder name to be safe on Windows, Linux, and Android (Termux).
    Replaces illegal characters, spaces, and limits length.
    """
    if not name or not name.strip():
        return "reels_video"
    
    # Remove emojis or characters outside standard alphanum and common symbols
    # Keep indonesian/latin letters, digits, and hyphens/underscores
    cleaned = name.strip()
    # Replace illegal filesystem chars <>:"/\|?*
    cleaned = re.sub(r'[<>:"/\\|?*#~`!@$%^&+=;]', '', cleaned)
    # Replace spaces and multiple symbols with single hyphen
    cleaned = re.sub(r'[\s_]+', '-', cleaned)
    cleaned = re.sub(r'-+', '-', cleaned)
    cleaned = cleaned.strip('-').lower()
    
    # Restrict length to safe filesystem limit
    if len(cleaned) > 60:
        cleaned = cleaned[:60].rstrip('-')
    
    return cleaned if cleaned else "reels_video"

def get_unique_folder_path(base_dir: str, folder_name: str) -> str:
    """
    Returns an unused folder path inside base_dir.
    If 'folder_name' exists, creates 'folder_name_02', 'folder_name_03', etc.
    """
    os.makedirs(base_dir, exist_ok=True)
    target_path = os.path.join(base_dir, folder_name)
    if not os.path.exists(target_path):
        return target_path
    
    index = 2
    while True:
        candidate = os.path.join(base_dir, f"{folder_name}_{index:02d}")
        if not os.path.exists(candidate):
            return candidate
        index += 1

def generate_post_meta(
    output_dir: str,
    post_title: str,
    summary: str,
    hashtags: Any,
    cta: str,
    image_count: int = 0,
    generated_at: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates and saves post_meta.json following the exact required schema:
    {
      "post_title": "...",
      "summary": "...",
      "hashtags": ["#tag1", ...],
      "cta": "...",
      "image_count": 0,
      "generated_at": "YYYY-MM-DD HH:MM:SS"
    }
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Process hashtags to list with # prefix
    tag_list: List[str] = []
    if isinstance(hashtags, list):
        for tag in hashtags:
            t = str(tag).strip()
            if t:
                if not t.startswith('#'):
                    t = f"#{t}"
                tag_list.append(t)
    elif isinstance(hashtags, str):
        # Can be space or comma separated
        raw_tags = re.split(r'[, \n]+', hashtags.strip())
        for raw in raw_tags:
            t = raw.strip()
            if t:
                if not t.startswith('#'):
                    t = f"#{t}"
                tag_list.append(t)
                
    if not generated_at:
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    meta_content = {
        "post_title": post_title.strip() if post_title else "Reels Video",
        "summary": summary.strip() if summary else "",
        "hashtags": tag_list,
        "cta": cta.strip() if cta else "Simak video lengkapnya!",
        "image_count": int(image_count) if image_count is not None else 0,
        "generated_at": generated_at
    }
    
    meta_path = os.path.join(output_dir, "post_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_content, f, ensure_ascii=False, indent=2)
        
    return meta_content

def save_source_copyright_info(output_dir: str, source_info: Dict[str, Any]) -> str:
    """
    Saves content source and copyright audit log in source_info.json
    without breaking post_meta.json standard fields.
    """
    os.makedirs(output_dir, exist_ok=True)
    data = {
        "original_url": source_info.get("original_url", ""),
        "original_title": source_info.get("original_title", ""),
        "original_channel": source_info.get("original_channel", ""),
        "download_timestamp": source_info.get("download_timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "source_duration": source_info.get("source_duration", 0),
        "license_status": source_info.get("license_status", "Belum diketahui"),
        "disclaimer": "Penggunaan ulang video YouTube untuk Facebook Reels tunduk pada kebijakan hak cipta masing-masing platform. Aplikasi ini tidak menjamin lolos Content ID secara otomatis."
    }
    path = os.path.join(output_dir, "source_info.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path
