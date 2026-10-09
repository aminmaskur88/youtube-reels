import os
import sys
import json
import tempfile
import shutil
import unittest
import subprocess

from metadata_manager import sanitize_folder_name, get_unique_folder_path, generate_post_meta, save_source_copyright_info
from downloader import is_valid_youtube_url, format_duration, extract_smart_summary
from processor import (
    check_ffmpeg, check_ffprobe, get_media_info, split_and_process_video,
    build_filter_complex, build_audio_filter_chain, calculate_video_and_text_layout,
    calculate_header_layout, preprocess_template, wrap_text
)
from app import app

class TestYouTubeReels(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.app_client = app.test_client()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_downloader_helpers(self):
        self.assertTrue(is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertTrue(is_valid_youtube_url("https://youtu.be/dQw4w9WgXcQ"))
        self.assertTrue(is_valid_youtube_url("https://youtube.com/shorts/dQw4w9WgXcQ"))
        self.assertFalse(is_valid_youtube_url("not_a_url"))
        
        self.assertEqual(format_duration(65), "01:05")
        self.assertEqual(format_duration(3665), "01:01:05")

        summary = extract_smart_summary("Ini adalah kalimat pertama. Ini kalimat kedua. Ini ketiga.")
        self.assertIn("Ini adalah kalimat pertama.", summary)

    def test_metadata_manager(self):
        # Folder Sanitizer
        name = "Cara Buat Kopi Enak: Tips & Trik 100% Berhasil?!"
        sanitized = sanitize_folder_name(name)
        self.assertNotIn(":", sanitized)
        self.assertNotIn("?", sanitized)
        self.assertNotIn("%", sanitized)
        self.assertTrue(len(sanitized) > 0)
        
        # Unique Folder Deduplication
        f1 = get_unique_folder_path(self.test_dir, "reels-kopi")
        os.makedirs(f1)
        f2 = get_unique_folder_path(self.test_dir, "reels-kopi")
        self.assertTrue(f2.endswith("reels-kopi_02"))
        os.makedirs(f2)
        f3 = get_unique_folder_path(self.test_dir, "reels-kopi")
        self.assertTrue(f3.endswith("reels-kopi_03"))

        # Post Meta Schema
        meta = generate_post_meta(
            output_dir=f1,
            post_title="Judul Reels Kopi",
            summary="Ringkasan kopi sedap.",
            hashtags=["kopi", "#barista"],
            cta="Komentar di bawah!",
            image_count=0,
            generated_at="2026-10-08 12:00:00"
        )
        self.assertEqual(meta["post_title"], "Judul Reels Kopi")
        self.assertEqual(meta["summary"], "Ringkasan kopi sedap.")
        self.assertIn("#kopi", meta["hashtags"])
        self.assertIn("#barista", meta["hashtags"])
        self.assertEqual(meta["image_count"], 0)
        self.assertEqual(meta["cta"], "Komentar di bawah!")
        self.assertEqual(meta["generated_at"], "2026-10-08 12:00:00")
        
        # Verify saved file
        json_path = os.path.join(f1, "post_meta.json")
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["post_title"], "Judul Reels Kopi")

    def test_filter_complex_builder(self):
        fc_blur = build_filter_complex(
            mode="cinematic_blur",
            cinematic_opts={"blur_intensity": 25, "bg_brightness": -0.15, "fg_scale": 1.0, "bg_vignette": True},
            visual_opts={"enabled": True, "sharpen": True, "film_look": True},
            clip_len=30.0
        )
        self.assertIn("boxblur=25:1", fc_blur)
        self.assertIn("overlay", fc_blur)
        self.assertIn("setsar=1", fc_blur)
        self.assertIn("unsharp", fc_blur)

        fc_crop = build_filter_complex(
            mode="center_crop",
            cinematic_opts={},
            visual_opts={},
            clip_len=30.0
        )
        self.assertIn("crop=1080:1920", fc_crop)

        fc_part = build_filter_complex(
            mode="cinematic_blur",
            cinematic_opts={},
            visual_opts={},
            clip_len=30.0,
            part_opts={
                "enabled": True,
                "template": "PART {n}",
                "font_path": "/data/data/com.termux/files/home/VideoTemplate/junction.bold.otf",
                "font_size": 68,
                "bottom_offset": 220
            },
            part_num=2,
            total_clips=5
        )
        self.assertIn("drawtext=", fc_part)
        self.assertIn("text='PART 2'", fc_part)
        self.assertIn("junction.bold.otf", fc_part)

        # Header Title above video test
        fc_header = build_filter_complex(
            mode="cinematic_blur",
            cinematic_opts={},
            visual_opts={},
            clip_len=30.0,
            part_opts={"enabled": False},
            header_opts={
                "enabled": True,
                "template": "{title} - PART {n}",
                "custom_title": "FAKTA UNIK",
                "font_path": "/data/data/com.termux/files/home/VideoTemplate/junction.bold.otf",
                "position": "above_video"
            },
            part_num=1,
            total_clips=3
        )
        self.assertIn("drawtext=", fc_header)
        self.assertIn("text='FAKTA UNIK - PART 1'", fc_header)

    def test_audio_filter_chain(self):
        af = build_audio_filter_chain(
            audio_opts={
                "enabled": True,
                "volume": 3.0,
                "loudnorm": True,
                "pitch": 1.05,
                "fade_in": 1.0,
                "fade_out": 1.0
            },
            clip_len=10.0
        )
        self.assertIn("volume=+3.0dB", af)
        self.assertIn("loudnorm", af)
        self.assertIn("asetrate=46305", af)
        self.assertIn("afade=t=in", af)
        self.assertIn("afade=t=out", af)

    def test_video_processing_pipeline(self):
        # Generate 4-second test video
        src_video = os.path.join(self.test_dir, "test_input.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=4:size=640x360:rate=25",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
            "-c:v", "libx264", "-c:a", "aac", src_video
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        out_folder = os.path.join(self.test_dir, "clips")
        clips = split_and_process_video(
            input_path=src_video,
            output_dir=out_folder,
            clip_duration=2.5,  # Should generate 2 clips: 2.5s and 1.5s
            mode="cinematic_blur",
            cinematic_opts={"blur_intensity": 10, "bg_brightness": -0.1},
            visual_opts={"enabled": False},
            audio_opts={"enabled": True}
        )

        self.assertEqual(len(clips), 2)
        self.assertTrue(os.path.exists(os.path.join(out_folder, "clip_001.mp4")))
        self.assertTrue(os.path.exists(os.path.join(out_folder, "clip_002.mp4")))

        # Check media info of produced clip
        info = get_media_info(clips[0])
        self.assertTrue(info["has_video"])
        self.assertTrue(info["has_audio"])
        self.assertAlmostEqual(info["duration"], 2.5, delta=0.5)

        # Test Mode A: Center Crop
        out_crop = os.path.join(self.test_dir, "crop")
        clips_crop = split_and_process_video(
            input_path=src_video,
            output_dir=out_crop,
            clip_duration=4.0,
            mode="center_crop"
        )
        self.assertEqual(len(clips_crop), 1)
        info_crop = get_media_info(clips_crop[0])
        self.assertTrue(info_crop["has_video"])

        # Test Mode C: Fit to Portrait
        out_fit = os.path.join(self.test_dir, "fit")
        clips_fit = split_and_process_video(
            input_path=src_video,
            output_dir=out_fit,
            clip_duration=4.0,
            mode="fit_portrait"
        )
        self.assertEqual(len(clips_fit), 1)
        info_fit = get_media_info(clips_fit[0])
        self.assertTrue(info_fit["has_video"])

    def test_flask_routes(self):
        # GET /
        resp = self.app_client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"YouTube to Reels 9:16", resp.data)

        # GET /api/system-status
        resp = self.app_client.get("/api/system-status")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data["ffmpeg"])

        # GET /api/latest-task
        resp = self.app_client.get("/api/latest-task")
        self.assertEqual(resp.status_code, 200)

        # POST /api/video-info with invalid url
        resp = self.app_client.post("/api/video-info", json={"url": "invalid"})
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertFalse(data["success"])

        # GET /api/templates
        resp_tpl = self.app_client.get("/api/templates")
        self.assertEqual(resp_tpl.status_code, 200)
        tpl_data = json.loads(resp_tpl.data)
        self.assertTrue(tpl_data["success"])
        self.assertIsInstance(tpl_data["templates"], list)

    def test_videotemplate_layout_matching(self):
        """
        Tests that calculate_video_and_text_layout strictly matches
        the positioning rules in VideoTemplate/main.py:
        - header_limit = int(canvas_h * 0.28) = 537
        - text_y = canvas_h - total_text_height - int(canvas_h * 0.18)
        - video_bottom_limit = text_y - int(canvas_h * 0.02)
        - scale = min(avail_w / w, avail_h / h)
        """
        # 1. Test short text (e.g. 'PART 1')
        layout = calculate_video_and_text_layout(src_w=1920, src_h=1080, text_content="PART 1")
        self.assertEqual(layout["canvas_w"], 1080)
        self.assertEqual(layout["canvas_h"], 1920)
        self.assertEqual(layout["header_limit"], int(1920 * 0.28))  # 537
        self.assertEqual(layout["avail_w"], int(1080 * 0.90))       # 972
        
        # text_y calculation
        expected_text_y = 1920 - (1 * (layout["final_font_size"] + 5)) - int(1920 * 0.18)
        if expected_text_y % 2 != 0:
            expected_text_y -= 1
        self.assertEqual(layout["text_y"], expected_text_y)
        
        # video bounds
        expected_vbl = layout["text_y"] - int(1920 * 0.02)
        self.assertEqual(layout["video_bottom_limit"], expected_vbl)
        expected_avail_h = expected_vbl - layout["header_limit"]
        self.assertEqual(layout["avail_h"], expected_avail_h)
        
        # video dimensions & centering
        expected_scale = min(972 / 1920, expected_avail_h / 1080)
        expected_w = int(1920 * expected_scale)
        if expected_w % 2 != 0:
            expected_w -= 1
        expected_h = int(1080 * expected_scale)
        if expected_h % 2 != 0:
            expected_h -= 1
        self.assertEqual(layout["new_w"], expected_w)
        self.assertEqual(layout["new_h"], expected_h)
        
        expected_off_x = (1080 - expected_w) // 2
        if expected_off_x % 2 != 0:
            expected_off_x -= 1
        expected_off_y = layout["header_limit"] + (expected_avail_h - expected_h) // 2
        if expected_off_y % 2 != 0:
            expected_off_y -= 1
        self.assertEqual(layout["off_x"], expected_off_x)
        self.assertEqual(layout["off_y"], expected_off_y)

        # 2. Test template preprocessing
        test_png = os.path.join(self.test_dir, "test_template.png")
        from PIL import Image
        im = Image.new("RGBA", (1080, 1440), color=(20, 30, 40, 255))
        im.save(test_png)
        
        out_png = os.path.join(self.test_dir, "out_template.png")
        preprocess_template(test_png, out_png, target_w=1080, target_h=1920)
        self.assertTrue(os.path.exists(out_png))
        with Image.open(out_png) as p_img:
            self.assertEqual(p_img.size, (1080, 1920))

    def test_header_layout_calculation(self):
        h_layout = calculate_header_layout(
            text_content="JUDUL BESAR VIRAL DI ATAS VIDEO",
            off_y=600,
            position_mode="above_video"
        )
        self.assertTrue(len(h_layout["wrapped_lines"]) >= 1)
        self.assertLess(h_layout["title_y"], 600)
        self.assertGreaterEqual(h_layout["title_y"], 60)
        self.assertEqual(h_layout["title_y"] % 2, 0)

        # Test top_center
        h_center = calculate_header_layout(
            text_content="CENTER HEADER",
            off_y=600,
            position_mode="top_center"
        )
        self.assertEqual(h_center["title_y"] % 2, 0)
        self.assertLess(h_center["title_y"], 600)

if __name__ == "__main__":
    unittest.main()
