import os
import re
import math
import shutil
import json
import subprocess
import threading
from typing import Dict, Any, List, Optional, Callable
from PIL import Image, ImageFont, ImageDraw

def check_ffmpeg() -> bool:
    """Check if ffmpeg is available in system PATH."""
    return shutil.which("ffmpeg") is not None

def check_ffprobe() -> bool:
    """Check if ffprobe is available in system PATH."""
    return shutil.which("ffprobe") is not None

def wrap_text(text: str, font: Any, max_width: int) -> List[str]:
    """Wraps text to fit within max_width using the specified font (from VideoTemplate)."""
    dummy_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy_img)

    words = text.split()
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        line_str = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), line_str, font=font)
        width = bbox[2] - bbox[0]

        if width > max_width:
            if len(current_line) == 1:
                lines.append(current_line[0])
                current_line = []
            else:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines

def preprocess_template(template_path: str, output_path: str, target_w: int = 1080, target_h: int = 1920) -> str:
    """Preprocess PNG template to prevent stretching on 1080x1920 (from VideoTemplate)."""
    try:
        with Image.open(template_path) as img:
            img = img.convert("RGBA")
            orig_tw, orig_th = img.size
            
            new_tw = target_w
            new_th = int(orig_th * (target_w / orig_tw))
            
            if new_th > target_h:
                new_th = target_h
                new_tw = int(orig_tw * (target_h / orig_th))
                
            resized_img = img.resize((new_tw, new_th), Image.LANCZOS)
            new_template = Image.new("RGBA", (target_w, target_h))
            
            y_offset = (target_h - new_th) // 2
            x_offset = (target_w - new_tw) // 2
            
            top_edge = resized_img.crop((0, 0, new_tw, 1))
            bottom_edge = resized_img.crop((0, new_th - 1, new_tw, new_th))
            left_edge = resized_img.crop((0, 0, 1, new_th))
            right_edge = resized_img.crop((new_tw - 1, 0, new_tw, new_th))
            
            if y_offset > 0 and x_offset > 0:
                new_template.paste(Image.new("RGBA", (x_offset, y_offset), resized_img.getpixel((0, 0))), (0, 0))
                new_template.paste(Image.new("RGBA", (target_w - x_offset - new_tw, y_offset), resized_img.getpixel((new_tw - 1, 0))), (x_offset + new_tw, 0))
                new_template.paste(Image.new("RGBA", (x_offset, target_h - y_offset - new_th), resized_img.getpixel((0, new_th - 1))), (0, y_offset + new_th))
                new_template.paste(Image.new("RGBA", (target_w - x_offset - new_tw, target_h - y_offset - new_th), resized_img.getpixel((new_tw - 1, new_th - 1))), (x_offset + new_tw, y_offset + new_th))
            
            if y_offset > 0:
                new_template.paste(top_edge.resize((new_tw, y_offset)), (x_offset, 0))
                if target_h - (y_offset + new_th) > 0:
                    new_template.paste(bottom_edge.resize((new_tw, target_h - (y_offset + new_th))), (x_offset, y_offset + new_th))
                    
            if x_offset > 0:
                new_template.paste(left_edge.resize((x_offset, new_th)), (0, y_offset))
                if target_w - (x_offset + new_tw) > 0:
                    new_template.paste(right_edge.resize((target_w - (x_offset + new_tw), new_th)), (x_offset + new_tw, y_offset))
            
            new_template.paste(resized_img, (x_offset, y_offset))
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            new_template.save(output_path)
            return output_path
    except Exception as e:
        print(f"Error preprocessing template {template_path}: {e}")
        return template_path

def calculate_video_and_text_layout(
    src_w: int = 1920,
    src_h: int = 1080,
    text_content: Optional[str] = None,
    font_path: Optional[str] = None,
    base_font_size: Optional[int] = None,
    canvas_w: int = 1080,
    canvas_h: int = 1920
) -> Dict[str, Any]:
    """
    Calculates video location and text position identical to VideoTemplate/main.py:
    - canvas_w, canvas_h = 1080, 1920
    - TEXT_WIDTH_SCALE, DESC_FONT_BASE, DESC_FONT_MIN = 0.90, int(canvas_w * 0.055), int(canvas_w * 0.027)
    - MARGIN_BOTTOM_SCALE, final_line_spacing, max_text_area_height = 0.18, 5, int(canvas_h * 0.25)
    - Dynamic font scaling loop down to DESC_FONT_MIN
    - text_y = canvas_h - total_text_height - int(canvas_h * MARGIN_BOTTOM_SCALE) (even)
    - header_limit, video_bottom_limit = int(canvas_h * 0.28), text_y - int(canvas_h * 0.02)
    - avail_w, avail_h = int(canvas_w * 0.90), video_bottom_limit - header_limit
    - scale = min(avail_w / w, avail_h / h)
    - new_w, new_h = int(w * scale), int(h * scale) (even)
    - off_x, off_y = (canvas_w - new_w) // 2, header_limit + (avail_h - new_h) // 2 (even)
    """
    if src_w <= 0:
        src_w = 1920
    if src_h <= 0:
        src_h = 1080

    TEXT_WIDTH_SCALE = 0.90
    DESC_FONT_BASE = base_font_size if (base_font_size and base_font_size > 0) else int(canvas_w * 0.055)
    DESC_FONT_MIN = int(canvas_w * 0.027)
    MARGIN_BOTTOM_SCALE = 0.18
    final_line_spacing = 5
    max_text_area_height = int(canvas_h * 0.25)

    font_size = DESC_FONT_BASE
    final_font_size = DESC_FONT_BASE
    wrapped_lines = []

    text_str = (text_content or "").strip()
    
    # Resolve font path
    chosen_font_path = None
    default_candidates = [
        font_path,
        "/data/data/com.termux/files/home/VideoTemplate/junction.bold.otf",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "junction.bold.otf")
    ]
    for cand in default_candidates:
        if cand and os.path.exists(cand):
            chosen_font_path = cand
            break

    if text_str:
        font_loaded = False
        if chosen_font_path:
            try:
                curr_size = font_size
                while curr_size >= DESC_FONT_MIN:
                    font = ImageFont.truetype(chosen_font_path, curr_size)
                    current_wrapped = wrap_text(text_str, font, int(canvas_w * TEXT_WIDTH_SCALE))
                    if len(current_wrapped) * (curr_size + final_line_spacing) <= max_text_area_height:
                        wrapped_lines = current_wrapped
                        final_font_size = curr_size
                        font_loaded = True
                        break
                    curr_size -= 2
                if not wrapped_lines:
                    wrapped_lines = wrap_text(text_str, ImageFont.truetype(chosen_font_path, DESC_FONT_MIN), int(canvas_w * TEXT_WIDTH_SCALE))
                    final_font_size = DESC_FONT_MIN
                    font_loaded = True
            except Exception:
                font_loaded = False

        if not font_loaded:
            wrapped_lines = [text_str]
            final_font_size = DESC_FONT_BASE

    total_text_height = len(wrapped_lines) * (final_font_size + final_line_spacing)
    text_y = canvas_h - total_text_height - int(canvas_h * MARGIN_BOTTOM_SCALE)
    if text_y % 2 != 0:
        text_y -= 1

    header_limit = int(canvas_h * 0.28)
    video_bottom_limit = text_y - int(canvas_h * 0.02)
    avail_w = int(canvas_w * 0.90)
    avail_h = max(100, video_bottom_limit - header_limit)

    scale = min(avail_w / src_w, avail_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    if new_w % 2 != 0:
        new_w -= 1
    if new_h % 2 != 0:
        new_h -= 1
    new_w = max(2, new_w)
    new_h = max(2, new_h)

    off_x = (canvas_w - new_w) // 2
    off_y = header_limit + (avail_h - new_h) // 2
    if off_x % 2 != 0:
        off_x -= 1
    if off_y % 2 != 0:
        off_y -= 1

    return {
        "canvas_w": canvas_w,
        "canvas_h": canvas_h,
        "header_limit": header_limit,
        "video_bottom_limit": video_bottom_limit,
        "avail_w": avail_w,
        "avail_h": avail_h,
        "new_w": new_w,
        "new_h": new_h,
        "off_x": off_x,
        "off_y": off_y,
        "text_y": text_y,
        "final_font_size": final_font_size,
        "final_line_spacing": final_line_spacing,
        "wrapped_lines": wrapped_lines,
        "font_path": chosen_font_path,
        "text_str": text_str
    }

def calculate_header_layout(
    text_content: Optional[str] = None,
    font_path: Optional[str] = None,
    base_font_size: Optional[int] = None,
    canvas_w: int = 1080,
    canvas_h: int = 1920,
    off_y: int = 537,
    position_mode: str = "above_video",
    style: str = "default"
) -> Dict[str, Any]:
    """
    Calculates typography and vertical placement for title/header text above the video.
    Matches typography and scaling logic from VideoTemplate/main.py:
    - canvas_w: 1080, canvas_h: 1920
    - Text auto-wrapped with PIL ImageDraw.textbbox
    - Dynamic font scaling down to DESC_FONT_MIN
    - Multi-position support: 'above_video', 'top_center', 'top_margin'
    """
    TEXT_WIDTH_SCALE = 0.90
    DESC_FONT_BASE = base_font_size if (base_font_size and base_font_size > 0) else int(canvas_w * 0.055)
    DESC_FONT_MIN = int(canvas_w * 0.027)
    final_line_spacing = 5
    max_text_area_height = max(80, int(off_y * 0.70))

    font_size = DESC_FONT_BASE
    final_font_size = DESC_FONT_BASE
    wrapped_lines = []

    text_str = (text_content or "").strip()

    # Resolve font path
    chosen_font_path = None
    default_candidates = [
        font_path,
        "/data/data/com.termux/files/home/VideoTemplate/junction.bold.otf",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "junction.bold.otf")
    ]
    for cand in default_candidates:
        if cand and os.path.exists(cand):
            chosen_font_path = cand
            break

    if text_str:
        font_loaded = False
        if chosen_font_path:
            try:
                curr_size = font_size
                while curr_size >= DESC_FONT_MIN:
                    font = ImageFont.truetype(chosen_font_path, curr_size)
                    current_wrapped = wrap_text(text_str, font, int(canvas_w * TEXT_WIDTH_SCALE))
                    if len(current_wrapped) * (curr_size + final_line_spacing) <= max_text_area_height:
                        wrapped_lines = current_wrapped
                        final_font_size = curr_size
                        font_loaded = True
                        break
                    curr_size -= 2
                if not wrapped_lines:
                    wrapped_lines = wrap_text(text_str, ImageFont.truetype(chosen_font_path, DESC_FONT_MIN), int(canvas_w * TEXT_WIDTH_SCALE))
                    final_font_size = DESC_FONT_MIN
                    font_loaded = True
            except Exception:
                font_loaded = False

        if not font_loaded:
            wrapped_lines = [text_str]
            final_font_size = DESC_FONT_BASE

    total_title_height = len(wrapped_lines) * (final_font_size + final_line_spacing)
    
    if position_mode == "top_center":
        # Centered vertically between top safe margin (~80px) and off_y
        title_y = 80 + max(0, (off_y - 80 - total_title_height) // 2)
    elif position_mode == "top_margin":
        # Near top safe area
        title_y = int(canvas_h * 0.06)
    else:
        # Default: "above_video", positioned just above the video with safety gap
        title_y = off_y - total_title_height - int(canvas_h * 0.02)
        if title_y < 60:
            title_y = 60

    if title_y % 2 != 0:
        title_y -= 1

    return {
        "wrapped_lines": wrapped_lines,
        "final_font_size": final_font_size,
        "final_line_spacing": final_line_spacing,
        "title_y": title_y,
        "font_path": chosen_font_path,
        "style": style,
        "text_str": text_str,
        "position_mode": position_mode
    }

def get_media_info(filepath: str) -> Dict[str, Any]:
    """
    Inspect media file using ffprobe to obtain accurate duration,
    resolution, and audio stream presence.
    """
    if not check_ffprobe():
        return {"duration": 0.0, "has_audio": True, "has_video": True, "width": 1920, "height": 1080}
        
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "stream=codec_type,width,height,duration",
        "-show_entries", "format=duration",
        "-of", "json",
        filepath
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(res.stdout)
        
        duration = 0.0
        fmt = data.get("format", {})
        if fmt.get("duration"):
            duration = float(fmt["duration"])
            
        streams = data.get("streams", [])
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        has_video = any(s.get("codec_type") == "video" for s in streams)
        
        width = 0
        height = 0
        for s in streams:
            if s.get("codec_type") == "video":
                w_val = s.get("width")
                h_val = s.get("height")
                if w_val and h_val:
                    width = int(w_val)
                    height = int(h_val)
                    break
                    
        # If format duration was missing, check stream duration
        if duration <= 0:
            for s in streams:
                if s.get("duration"):
                    duration = max(duration, float(s["duration"]))
                    
        return {
            "duration": duration,
            "has_audio": has_audio,
            "has_video": has_video,
            "width": width if width > 0 else 1920,
            "height": height if height > 0 else 1080
        }
    except Exception as e:
        return {"duration": 0.0, "has_audio": True, "has_video": True, "width": 1920, "height": 1080, "error": str(e)}

def build_filter_complex(
    mode: str,
    cinematic_opts: Dict[str, Any],
    visual_opts: Dict[str, Any],
    clip_len: float,
    part_opts: Optional[Dict[str, Any]] = None,
    part_num: int = 1,
    total_clips: int = 1,
    src_w: int = 1920,
    src_h: int = 1080,
    caption_path: Optional[str] = None,
    meta_info: Optional[Dict[str, Any]] = None,
    template_active: bool = False,
    header_opts: Optional[Dict[str, Any]] = None,
    header_path: Optional[str] = None
) -> str:
    """
    Builds the FFmpeg video filter complex string for 9:16 portrait output,
    with video location and text position matching VideoTemplate/main.py.
    """
    mode = mode.lower()
    part_opts = part_opts or {}
    cinematic_opts = cinematic_opts or {}
    visual_opts = visual_opts or {}

    # Determine text to render
    text_content = ""
    if part_opts.get("enabled", True):
        tmpl = part_opts.get("template", "PART {n}")
        title_str = (meta_info.get("post_title") if meta_info else "") or ""
        caption_str = (part_opts.get("caption") or (meta_info.get("caption") if meta_info else "") or "").strip()
        
        text_val = tmpl.replace("{n}", str(part_num)).replace("{total}", str(total_clips))
        text_val = text_val.replace("{title}", title_str).replace("{caption}", caption_str)
        if not text_val.strip() and caption_str:
            text_val = caption_str
        text_content = text_val

    # Layout calculation matching VideoTemplate/main.py
    font_path_opt = (part_opts.get("font_path") or "").strip()
    font_size_opt = int(part_opts.get("font_size", 0)) if part_opts.get("font_size") else None
    layout = calculate_video_and_text_layout(
        src_w=src_w,
        src_h=src_h,
        text_content=text_content,
        font_path=font_path_opt,
        base_font_size=font_size_opt
    )
    
    # 1. Base portrait layout
    filter_parts = []
    
    if mode == "center_crop":
        # Mode A: Center crop 9:16
        layout_filter = (
            "[0:v]scale='if(gt(a,9/16),-2,1080)':'if(gt(a,9/16),1920,-2)',"
            "crop=1080:1920,setsar=1[v_base]"
        )
        filter_parts.append(layout_filter)
        
    elif mode in ["template", "template_frame"] and template_active:
        # Mode D: Template Frame PNG from VideoTemplate
        # Input 0: template PNG, Input 1: video
        bg_chain = f"[0:v]scale=w=1080:h=1920,setsar=1[bg]"
        fg_chain = f"[1:v]scale={layout['new_w']}:{layout['new_h']},setsar=1[fg]"
        comp_chain = f"[bg][fg]overlay=x={layout['off_x']}:y={layout['off_y']},setsar=1[v_base]"
        filter_parts.extend([bg_chain, fg_chain, comp_chain])

    elif mode == "fit_portrait":
        # Mode C: Fit to Portrait with solid black background
        bg_chain = f"color=c=black:s=1080x1920:d={clip_len}[bg]"
        fg_chain = f"[0:v]scale={layout['new_w']}:{layout['new_h']},setsar=1[fg]"
        comp_chain = f"[bg][fg]overlay=x={layout['off_x']}:y={layout['off_y']},setsar=1[v_base]"
        filter_parts.extend([bg_chain, fg_chain, comp_chain])
        
    else:
        # Mode B: Cinematic Blur Background (Default)
        blur_radius = int(cinematic_opts.get("blur_intensity", 20))
        bg_brightness = float(cinematic_opts.get("bg_brightness", -0.15))
        bg_contrast = float(cinematic_opts.get("bg_contrast", 1.1))
        bg_saturation = float(cinematic_opts.get("bg_saturation", 1.2))
        use_bg_vignette = bool(cinematic_opts.get("bg_vignette", True))
        vignette_str = ",vignette=angle=PI/4" if use_bg_vignette else ""
        
        # Optimized background: scale down to 540x960, blur, scale up to 1080x1920
        bg_chain = (
            f"[0:v]scale='if(gt(a,9/16),-2,540)':'if(gt(a,9/16),960,-2)',"
            f"crop=540:960,"
            f"boxblur={blur_radius}:1,"
            f"scale=1080:1920,"
            f"eq=brightness={bg_brightness}:contrast={bg_contrast}:saturation={bg_saturation}"
            f"{vignette_str}[bg]"
        )
        fg_chain = f"[0:v]scale={layout['new_w']}:{layout['new_h']},setsar=1[fg]"
        comp_chain = f"[bg][fg]overlay=x={layout['off_x']}:y={layout['off_y']},setsar=1[v_base]"
        
        filter_parts.extend([bg_chain, fg_chain, comp_chain])
        
    # 2. Visual Effects chain on [v_base] -> [outv]
    vf_sub = []
    
    if visual_opts.get("enabled", False):
        v_bright = float(visual_opts.get("brightness", 0.0))
        v_cont = float(visual_opts.get("contrast", 1.0))
        v_sat = float(visual_opts.get("saturation", 1.0))
        if v_bright != 0.0 or v_cont != 1.0 or v_sat != 1.0:
            vf_sub.append(f"eq=brightness={v_bright}:contrast={v_cont}:saturation={v_sat}")
            
        if visual_opts.get("sharpen", False):
            vf_sub.append("unsharp=5:5:0.8:5:5:0.0")
            
        if visual_opts.get("vignette", False):
            vf_sub.append("vignette=angle=PI/4")
            
        if visual_opts.get("film_look", False):
            # Cinematic color grade: gentle warm tint and soft contrast
            vf_sub.append("colorbalance=rs=0.07:gs=0.02:bs=-0.07:rm=0.03:bm=-0.04")
            
        if visual_opts.get("glitch", False):
            freq = float(visual_opts.get("glitch_frequency", 3.5))
            intensity = float(visual_opts.get("glitch_intensity", 30))
            vf_sub.append(
                f"hue=h='if(between(mod(t,{freq}),0,0.12),sin(t*50)*{intensity},0)':"
                f"s='if(between(mod(t,{freq}),0,0.12),1.8,1.0)'"
            )
            
    if visual_opts.get("subtle_zoom", False):
        vf_sub.append("scale=eval=frame:w='trunc(iw*(1+0.0002*n)/2)*2':h='trunc(ih*(1+0.0002*n)/2)*2',crop=1080:1920")

    # 3. Header / Title Text above the video (matching 'part' typography & styling)
    header_opts = header_opts or {}
    if header_opts.get("enabled", False):
        h_tmpl = header_opts.get("template", "{title}")
        if h_tmpl == "custom":
            h_tmpl = header_opts.get("custom_template") or "{title}"
        h_title_raw = (header_opts.get("custom_title") or (meta_info.get("post_title") if meta_info else "") or (meta_info.get("title") if meta_info else "") or "").strip()
        h_text_val = h_tmpl.replace("{title}", h_title_raw).replace("{n}", str(part_num)).replace("{total}", str(total_clips))
        if not h_text_val.strip() and h_title_raw:
            h_text_val = h_title_raw

        if h_text_val.strip():
            h_font_path = (header_opts.get("font_path") or part_opts.get("font_path") or "").strip()
            h_font_size = int(header_opts.get("font_size", 0)) if header_opts.get("font_size") else None
            h_pos = header_opts.get("position", "above_video")
            h_style = header_opts.get("style", "default")

            h_layout = calculate_header_layout(
                text_content=h_text_val,
                font_path=h_font_path,
                base_font_size=h_font_size,
                canvas_w=layout["canvas_w"],
                canvas_h=layout["canvas_h"],
                off_y=layout["off_y"],
                position_mode=h_pos,
                style=h_style
            )

            if h_layout["wrapped_lines"]:
                chosen_h_font = h_layout["font_path"] or layout["font_path"]
                if chosen_h_font:
                    safe_h_font = chosen_h_font.replace("'", "\\'").replace(":", "\\:")
                    if h_style == "outline":
                        h_style_params = "fontcolor=white:borderw=5:bordercolor=black"
                    elif h_style == "box":
                        h_style_params = "fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=16"
                    elif h_style == "box_border":
                        h_style_params = "fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=16:borderw=3:bordercolor=black"
                    else:
                        h_style_params = "fontcolor=white:borderw=3:bordercolor=black"

                    h_text_y = h_layout["title_y"]
                    h_size = h_layout["final_font_size"]
                    h_spacing = h_layout["final_line_spacing"]

                    if header_path and os.path.exists(header_path):
                        hp_ff = header_path.replace('\\', '/').replace(':', '\\:')
                        draw_h_filter = (
                            f"drawtext=fontfile='{safe_h_font}':textfile='{hp_ff}':"
                            f"x=(w-text_w)/2:y={h_text_y}:fontsize={h_size}:{h_style_params}:"
                            f"line_spacing={h_spacing}:text_align=center"
                        )
                    else:
                        single_h_text = " ".join(h_layout["wrapped_lines"]) if len(h_layout["wrapped_lines"]) == 1 else h_layout["text_str"]
                        safe_h_text = single_h_text.replace("'", "\\'")
                        draw_h_filter = (
                            f"drawtext=fontfile='{safe_h_font}':text='{safe_h_text}':"
                            f"fontsize={h_size}:{h_style_params}:"
                            f"x=(w-text_w)/2:y={h_text_y}:line_spacing={h_spacing}:text_align=center"
                        )
                    vf_sub.append(draw_h_filter)

    # 4. Text at the bottom of the video positioned identically to VideoTemplate/main.py
    if part_opts.get("enabled", True) and layout["wrapped_lines"]:
        chosen_font = layout["font_path"]
        if chosen_font:
            safe_font = chosen_font.replace("'", "\\'").replace(":", "\\:")
            
            style = part_opts.get("style", "default")
            if style == "outline":
                style_params = "fontcolor=white:borderw=5:bordercolor=black"
            elif style == "box":
                style_params = "fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=16"
            elif style == "box_border":
                style_params = "fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=16:borderw=3:bordercolor=black"
            else:
                # VideoTemplate standard: clean white text with 3px black border
                style_params = "fontcolor=white:borderw=3:bordercolor=black"
                
            text_y = layout["text_y"]
            font_size = layout["final_font_size"]
            spacing = layout["final_line_spacing"]

            if caption_path and os.path.exists(caption_path):
                cp_ff = caption_path.replace('\\', '/').replace(':', '\\:')
                draw_filter = (
                    f"drawtext=fontfile='{safe_font}':textfile='{cp_ff}':"
                    f"x=(w-text_w)/2:y={text_y}:fontsize={font_size}:{style_params}:"
                    f"line_spacing={spacing}:text_align=center"
                )
            else:
                single_text = " ".join(layout["wrapped_lines"]) if len(layout["wrapped_lines"]) == 1 else layout["text_str"]
                safe_text = single_text.replace("'", "\\'")
                draw_filter = (
                    f"drawtext=fontfile='{safe_font}':text='{safe_text}':"
                    f"fontsize={font_size}:{style_params}:"
                    f"x=(w-text_w)/2:y={text_y}:text='{safe_text}'"
                )
                # Ensure line_spacing and text='...' format matches test_suite
                draw_filter = (
                    f"drawtext=fontfile='{safe_font}':text='{safe_text}':"
                    f"fontsize={font_size}:{style_params}:"
                    f"x=(w-text_w)/2:y={text_y}:line_spacing={spacing}:text_align=center"
                )
            vf_sub.append(draw_filter)

    if vf_sub:
        effects_str = ",".join(vf_sub)
        filter_parts.append(f"[v_base]{effects_str}[outv]")
    else:
        filter_parts.append("[v_base]copy[outv]")
        
    return ";".join(filter_parts)

def build_audio_filter_chain(
    audio_opts: Dict[str, Any],
    clip_len: float
) -> Optional[str]:
    """
    Builds the FFmpeg audio filter string.
    """
    if not audio_opts.get("enabled", True):
        return None
        
    af_list = []
    
    # 1. Volume
    vol = float(audio_opts.get("volume", 0.0))
    if vol != 0.0:
        af_list.append(f"volume={vol:+.1f}dB")
        
    # 2. Equalizer
    bass = float(audio_opts.get("bass_gain", 0.0))
    treble = float(audio_opts.get("treble_gain", 0.0))
    if bass != 0.0:
        af_list.append(f"equalizer=f=100:width_type=h:width=200:g={bass:+.1f}")
    if treble != 0.0:
        af_list.append(f"equalizer=f=8000:width_type=h:width=1000:g={treble:+.1f}")
        
    # 3. Creative pitch adjustment
    pitch = float(audio_opts.get("pitch", 1.0))
    if abs(pitch - 1.0) > 0.01:
        # Creative pitch shift while preserving sync
        sample_rate = int(round(44100 * pitch))
        tempo_inv = 1.0 / pitch
        af_list.append(f"asetrate={sample_rate},atempo={tempo_inv:.4f}")
        
    # 4. Noise reduction
    if audio_opts.get("noise_reduction", False):
        af_list.append("afftdn=nf=-25")
        
    # 5. Fade In & Fade Out
    fade_in = float(audio_opts.get("fade_in", 0.0))
    fade_out = float(audio_opts.get("fade_out", 0.0))
    if fade_in > 0 and fade_in < clip_len:
        af_list.append(f"afade=t=in:ss=0:d={fade_in:.2f}")
    if fade_out > 0 and fade_out < clip_len:
        start_out = max(0.0, clip_len - fade_out)
        af_list.append(f"afade=t=out:st={start_out:.2f}:d={fade_out:.2f}")
        
    # 6. Loudness normalization (EBU R128 standard)
    if audio_opts.get("loudnorm", False):
        af_list.append("loudnorm=I=-16:TP=-1.5:LRA=11")
        
    return ",".join(af_list) if af_list else None

def split_and_process_video(
    input_path: str,
    output_dir: str,
    clip_duration: float,
    mode: str = "cinematic_blur",
    cinematic_opts: Optional[Dict[str, Any]] = None,
    visual_opts: Optional[Dict[str, Any]] = None,
    audio_opts: Optional[Dict[str, Any]] = None,
    part_opts: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    cancel_event: Optional[Any] = None,
    template_path: Optional[str] = None,
    meta_info: Optional[Dict[str, Any]] = None,
    header_opts: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Splits video into consecutive 9:16 clips without dropping any part.
    Saves outputs as clip_001.mp4, clip_002.mp4, etc. inside output_dir.
    Reports real-time progress.
    """
    if not check_ffmpeg():
        raise RuntimeError("FFmpeg tidak ditemukan di sistem. Silakan install FFmpeg terlebih dahulu.")
        
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File video sumber tidak ditemukan: {input_path}")
        
    os.makedirs(output_dir, exist_ok=True)
    
    media_info = get_media_info(input_path)
    total_duration = media_info.get("duration", 0.0)
    has_audio = media_info.get("has_audio", True)
    src_w = media_info.get("width", 1920) or 1920
    src_h = media_info.get("height", 1080) or 1080
    
    if total_duration <= 0:
        raise ValueError("Tidak dapat membaca durasi video sumber.")
        
    if clip_duration <= 0:
        clip_duration = 30.0
        
    # Calculate clip boundaries
    # Segments: [0, clip_duration), [clip_duration, 2*clip_duration), ...
    total_clips = int(math.ceil(total_duration / clip_duration))
    if total_clips < 1:
        total_clips = 1
        
    cinematic_opts = cinematic_opts or {}
    visual_opts = visual_opts or {}
    audio_opts = audio_opts or {}
    part_opts = part_opts or {}
    meta_info = meta_info or {}
    header_opts = header_opts or {}
    
    # Handle template PNG if template_frame mode is used
    is_template_mode = (mode.lower() in ["template", "template_frame"]) and bool(template_path and os.path.exists(template_path))
    processed_template_file = None
    if is_template_mode and template_path:
        processed_template_file = os.path.join(output_dir, f"_active_template_{os.path.basename(template_path)}")
        try:
            preprocess_template(template_path, processed_template_file, target_w=1080, target_h=1920)
        except Exception as e:
            print(f"Error preparing template: {e}")
            processed_template_file = template_path

    created_clips = []
    
    if progress_callback:
        progress_callback({
            "step": "Mempersiapkan pembagian video...",
            "percent": 0.0,
            "clip_current": 0,
            "clip_total": total_clips,
            "total_duration": total_duration,
            "status": "preparing"
        })
        
    active_process = None
    
    try:
        for i in range(total_clips):
            if cancel_event and cancel_event.is_set():
                raise RuntimeError("Proses dihentikan oleh pengguna.")
                
            start_time = i * clip_duration
            current_len = min(clip_duration, total_duration - start_time)
            if current_len <= 0.2:
                # Skip sub-second artifact at very end if zero length
                continue
                
            clip_name = f"clip_{i+1:03d}.mp4"
            out_clip_path = os.path.join(output_dir, clip_name)
            
            # Check if this clip was already rendered completely and is valid
            if os.path.exists(out_clip_path) and os.path.getsize(out_clip_path) > 10000:
                existing_info = get_media_info(out_clip_path)
                if existing_info.get("has_video") and abs(existing_info.get("duration", 0) - current_len) < 1.0:
                    created_clips.append(out_clip_path)
                    overall_percent = round(((i + 1) / total_clips) * 100, 1)
                    if progress_callback:
                        progress_callback({
                            "step": f"Klip {i+1:02d}/{total_clips:02d} sudah siap (melanjutkan...)",
                            "percent": overall_percent,
                            "clip_current": i + 1,
                            "clip_total": total_clips,
                            "status": "processing"
                        })
                    continue

            # Determine bottom text and write caption file if present
            caption_file = None
            text_val = ""
            if part_opts.get("enabled", True):
                tmpl = part_opts.get("template", "PART {n}")
                title_str = meta_info.get("post_title", "")
                caption_str = (part_opts.get("caption") or meta_info.get("caption") or "").strip()
                text_val = tmpl.replace("{n}", str(i + 1)).replace("{total}", str(total_clips))
                text_val = text_val.replace("{title}", title_str).replace("{caption}", caption_str)
                if not text_val.strip() and caption_str:
                    text_val = caption_str

            font_path_opt = (part_opts.get("font_path") or "").strip()
            font_size_opt = int(part_opts.get("font_size", 0)) if part_opts.get("font_size") else None
            
            layout_calc = calculate_video_and_text_layout(
                src_w=src_w,
                src_h=src_h,
                text_content=text_val,
                font_path=font_path_opt,
                base_font_size=font_size_opt
            )
            if part_opts.get("enabled", True) and layout_calc["wrapped_lines"]:
                caption_file = os.path.join(output_dir, f"{clip_name}.caption.txt")
                with open(caption_file, "w", encoding="utf-8") as cf:
                    cf.write("\n".join(layout_calc["wrapped_lines"]))

            # Determine header title text and write title file if present
            title_file = None
            if header_opts.get("enabled", False):
                h_tmpl = header_opts.get("template", "{title}")
                if h_tmpl == "custom":
                    h_tmpl = header_opts.get("custom_template") or "{title}"
                h_title_raw = (header_opts.get("custom_title") or meta_info.get("post_title") or meta_info.get("title") or "").strip()
                h_text_val = h_tmpl.replace("{title}", h_title_raw).replace("{n}", str(i + 1)).replace("{total}", str(total_clips))
                if not h_text_val.strip() and h_title_raw:
                    h_text_val = h_title_raw

                if h_text_val.strip():
                    h_font_path = (header_opts.get("font_path") or part_opts.get("font_path") or "").strip()
                    h_font_size = int(header_opts.get("font_size", 0)) if header_opts.get("font_size") else None
                    h_pos = header_opts.get("position", "above_video")
                    h_style = header_opts.get("style", "default")

                    h_layout = calculate_header_layout(
                        text_content=h_text_val,
                        font_path=h_font_path,
                        base_font_size=h_font_size,
                        canvas_w=1080,
                        canvas_h=1920,
                        off_y=layout_calc["off_y"],
                        position_mode=h_pos,
                        style=h_style
                    )
                    if h_layout["wrapped_lines"]:
                        title_file = os.path.join(output_dir, f"{clip_name}.title.txt")
                        with open(title_file, "w", encoding="utf-8") as tf:
                            tf.write("\n".join(h_layout["wrapped_lines"]))
            
            # Build filter complex for this clip with video & text position matching VideoTemplate
            filter_complex = build_filter_complex(
                mode=mode,
                cinematic_opts=cinematic_opts,
                visual_opts=visual_opts,
                clip_len=current_len,
                part_opts=part_opts,
                part_num=i + 1,
                total_clips=total_clips,
                src_w=src_w,
                src_h=src_h,
                caption_path=caption_file,
                meta_info=meta_info,
                template_active=is_template_mode,
                header_opts=header_opts,
                header_path=title_file
            )
            af_filter = build_audio_filter_chain(audio_opts, current_len) if has_audio else None
            
            # Build FFmpeg command safely using arguments list
            if is_template_mode and processed_template_file and os.path.exists(processed_template_file):
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-loop", "1",
                    "-i", processed_template_file,
                    "-ss", f"{start_time:.3f}",
                    "-t", f"{current_len:.3f}",
                    "-i", input_path,
                    "-filter_complex", filter_complex,
                    "-map", "[outv]",
                ]
                if has_audio:
                    cmd.extend(["-map", "1:a?"])
                    if af_filter:
                        cmd.extend(["-af", af_filter])
                    cmd.extend(["-c:a", "aac", "-b:a", "192k", "-ar", "44100"])
                else:
                    cmd.extend([
                        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                        "-c:a", "aac", "-b:a", "128k", "-shortest"
                    ])
            else:
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-ss", f"{start_time:.3f}",
                    "-t", f"{current_len:.3f}",
                    "-i", input_path,
                    "-filter_complex", filter_complex,
                    "-map", "[outv]",
                ]
                if has_audio:
                    cmd.extend(["-map", "0:a?"])
                    if af_filter:
                        cmd.extend(["-af", af_filter])
                    cmd.extend(["-c:a", "aac", "-b:a", "192k", "-ar", "44100"])
                else:
                    cmd.extend([
                        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                        "-c:a", "aac", "-b:a", "128k", "-shortest"
                    ])
                
            cmd.extend([
                "-r", "30",
                "-threads", "0",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                "-crf", "23",
                "-movflags", "+faststart",
                "-loglevel", "error",
                "-progress", "pipe:1",
                out_clip_path
            ])
            
            # Run FFmpeg and stream progress
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Dedicated thread to consume stderr continuously, preventing pipe buffer deadlock
            stderr_output = []
            def consume_stderr():
                try:
                    for err_line in proc.stderr:
                        stderr_output.append(err_line)
                except Exception:
                    pass
                finally:
                    try:
                        proc.stderr.close()
                    except Exception:
                        pass
                    
            err_thread = threading.Thread(target=consume_stderr, daemon=True)
            err_thread.start()
            
            step_label = f"Processing clip {i+1:02d}/{total_clips:02d}"
            clip_percent = 0.0
            current_speed = "1.0x"
            current_fps = "0"
            
            try:
                for line in proc.stdout:
                    if cancel_event and cancel_event.is_set():
                        proc.kill()
                        if os.path.exists(out_clip_path):
                            os.remove(out_clip_path)
                        raise RuntimeError("Proses dihentikan oleh pengguna.")
                        
                    line = line.strip()
                    if line.startswith("fps="):
                        try:
                            current_fps = line.split("=")[1].strip()
                        except Exception:
                            pass
                    elif line.startswith("speed="):
                        try:
                            current_speed = line.split("=")[1].strip()
                        except Exception:
                            pass
                    elif line.startswith("out_time_us="):
                        try:
                            us = int(line.split("=")[1])
                            curr_sec = us / 1_000_000.0
                            clip_frac = max(0.0, min(1.0, curr_sec / current_len))
                            clip_percent = round(clip_frac * 100, 1)
                            overall_percent = round(((i + clip_frac) / total_clips) * 100, 1)
                            
                            speed_info = f" • Speed: {current_speed}" if current_speed else ""
                            fps_info = f" • {current_fps} fps" if current_fps and current_fps != "0" else ""
                            
                            if progress_callback:
                                progress_callback({
                                    "step": f"{step_label} ({clip_percent}%{speed_info}{fps_info})",
                                    "percent": overall_percent,
                                    "clip_current": i + 1,
                                    "clip_total": total_clips,
                                    "speed": current_speed,
                                    "fps": current_fps,
                                    "status": "processing"
                                })
                        except Exception:
                            pass
                            
                proc.stdout.close()
                proc.wait()
                err_thread.join(timeout=1.0)
                
                if proc.returncode != 0:
                    err_text = "".join(stderr_output)
                    raise RuntimeError(f"FFmpeg encoding gagal pada klip {clip_name}: {err_text[-300:]}")
                    
                created_clips.append(out_clip_path)
                
                # Cleanup caption & title files
                if caption_file and os.path.exists(caption_file):
                    try:
                        os.remove(caption_file)
                    except Exception:
                        pass
                if title_file and os.path.exists(title_file):
                    try:
                        os.remove(title_file)
                    except Exception:
                        pass
                
                # Post-clip progress update
                overall_percent = round(((i + 1) / total_clips) * 100, 1)
                if progress_callback:
                    progress_callback({
                        "step": f"Klip {i+1:02d}/{total_clips:02d} selesai",
                        "percent": overall_percent,
                        "clip_current": i + 1,
                        "clip_total": total_clips,
                        "status": "processing"
                    })
                    
            except Exception as e:
                if proc.poll() is None:
                    proc.kill()
                if proc.stdout and not proc.stdout.closed:
                    proc.stdout.close()
                if proc.stderr and not proc.stderr.closed:
                    proc.stderr.close()
                if os.path.exists(out_clip_path):
                    try:
                        os.remove(out_clip_path)
                    except Exception:
                        pass
                if caption_file and os.path.exists(caption_file):
                    try:
                        os.remove(caption_file)
                    except Exception:
                        pass
                if title_file and os.path.exists(title_file):
                    try:
                        os.remove(title_file)
                    except Exception:
                        pass
                raise e
    finally:
        if processed_template_file and os.path.exists(processed_template_file) and processed_template_file != template_path:
            try:
                os.remove(processed_template_file)
            except Exception:
                pass
            
    return created_clips
