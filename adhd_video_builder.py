"""
adhd_video_builder.py — ADHD focus music videoları için video montajı.

Format: 1080×1920 YouTube Shorts (55 saniye)
Renk: Koyu siyah (#0A0A0A) + neon turkuaz (#00E5CC) — meditation nişinden görsel ayrışma
Katmanlar:
  - Pexels footage (brain/coding/workspace temaları)
  - Hook overlay (merkez, büyük metin)
  - Science badge (sağ üst, "Nigg 2024 ✓" gibi)
  - 40Hz badge (sol üst)
  - "Turn Sound On" uyarısı (ilk 4s)
"""

import os
import json
import random
import math
import tempfile
import requests
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    ColorClip,
    concatenate_videoclips,
)
from freq_video_builder import (
    _load_font,
    _wrap_text,
    _make_gradient_bg,
    SOUND_WARNING_DURATION,
)

TARGET_W = 1080
TARGET_H = 1920
OUTPUT_PATH = os.path.join("output", "adhd_short.mp4")

# ADHD sabit paleti — tüm moodlar için aynı (rakiplerden görsel ayrışma)
ADHD_PALETTE = {
    "bg": (10, 10, 10),
    "accent": (0, 229, 204),    # neon turkuaz
    "text": (220, 255, 250),
}

ADHD_SEEN_PEXELS_PATH = os.path.join("output", "adhd_seen_pexels_ids.json")
MAX_SEEN_IDS = 500


def _load_adhd_seen_ids() -> set:
    try:
        with open(ADHD_SEEN_PEXELS_PATH, "r") as f:
            ids = json.load(f)
            if isinstance(ids, list):
                return set(ids)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return set()


def _save_adhd_seen_ids(seen: set) -> None:
    os.makedirs(os.path.dirname(ADHD_SEEN_PEXELS_PATH), exist_ok=True)
    id_list = list(seen)
    if len(id_list) > MAX_SEEN_IDS:
        id_list = id_list[-MAX_SEEN_IDS:]
    with open(ADHD_SEEN_PEXELS_PATH, "w") as f:
        json.dump(id_list, f)


def _fetch_pexels_clips(keywords: list, n: int = 1, seen_ids: set = None) -> tuple[list[str], set]:
    api_key = os.environ.get("PEXELS_API_KEY", "")
    if seen_ids is None:
        seen_ids = set()
    new_ids = set()

    if not api_key:
        print("[adhd_video] PEXELS_API_KEY eksik — renk arka plan kullanılacak")
        return [], new_ids

    downloaded = []
    session_seen = set()
    kw_pool = list(keywords)
    random.shuffle(kw_pool)

    for query in kw_pool[:5]:
        if len(downloaded) >= n:
            break
        try:
            page = random.randint(1, 3)
            resp = requests.get(
                "https://api.pexels.com/videos/search",
                params={"query": query, "per_page": 10, "orientation": "portrait", "page": page},
                headers={"Authorization": api_key},
                timeout=15,
            )
            if resp.status_code != 200:
                continue
            videos = resp.json().get("videos", [])
            random.shuffle(videos)
            for video in videos:
                if len(downloaded) >= n:
                    break
                vid_id = video["id"]
                vid_key = f"pexels_{vid_id}"
                if vid_key in session_seen or vid_id in seen_ids:
                    continue
                session_seen.add(vid_key)
                best = None
                for vf in video.get("video_files", []):
                    if vf.get("file_type") == "video/mp4" and vf.get("height", 0) >= 1080:
                        if best is None or vf.get("height", 0) > best.get("height", 0):
                            best = vf
                if not best:
                    continue
                try:
                    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, prefix="adhd_pexels_")
                    tmp.close()
                    r = requests.get(best["link"], timeout=60, stream=True)
                    r.raise_for_status()
                    with open(tmp.name, "wb") as f:
                        for chunk in r.iter_content(chunk_size=256 * 1024):
                            f.write(chunk)
                    downloaded.append(tmp.name)
                    new_ids.add(vid_id)
                    print(f"[adhd_video] Pexels klip indirildi: {query!r} (id={vid_id})")
                except Exception as e:
                    print(f"[adhd_video] Pexels indirme hatası: {e}")
        except Exception as e:
            print(f"[adhd_video] Pexels arama hatası ({query!r}): {e}")

    return downloaded, new_ids


def _make_adhd_hook_overlay(hook_line: str, hook_subtext: str, duration: float) -> ImageClip:
    """Hook metni — neon turkuaz accent ile."""
    palette = ADHD_PALETTE
    img = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    accent = palette["accent"]
    text_color = palette["text"]

    hook_font_size = 64
    font_hook = _load_font(hook_font_size)
    max_w = TARGET_W - 100
    lines = _wrap_text(hook_line, font_hook, max_w)

    line_h = hook_font_size + 14
    total_h = len(lines) * line_h
    y_start = int(TARGET_H * 0.30) - total_h // 2

    pad = 24
    box_y1 = y_start - pad
    box_y2 = y_start + total_h + pad
    draw.rectangle([(40, box_y1), (TARGET_W - 40, box_y2)], fill=(0, 0, 0, 160))

    # Sol kenar accent çizgisi
    draw.rectangle([(40, box_y1), (46, box_y2)], fill=(*accent, 255))

    for i, line in enumerate(lines):
        y = y_start + i * line_h
        try:
            lw = draw.textlength(line, font=font_hook)
        except AttributeError:
            bbox = font_hook.getbbox(line)
            lw = bbox[2] - bbox[0]
        x = (TARGET_W - lw) // 2
        draw.text((x + 2, y + 2), line, font=font_hook, fill=(0, 0, 0, 180))
        draw.text((x, y), line, font=font_hook, fill=(*text_color, 245))

    # Accent alt çizgi
    line_y = box_y2 + 8
    draw.rectangle(
        [(TARGET_W // 2 - 100, line_y), (TARGET_W // 2 + 100, line_y + 3)],
        fill=(*accent, 220),
    )

    if hook_subtext:
        font_sub = _load_font(38)
        sub_y = line_y + 16
        try:
            sw = draw.textlength(hook_subtext, font=font_sub)
        except AttributeError:
            bbox = font_sub.getbbox(hook_subtext)
            sw = bbox[2] - bbox[0]
        sx = (TARGET_W - sw) // 2
        draw.text((sx + 1, sub_y + 1), hook_subtext, font=font_sub, fill=(0, 0, 0, 150))
        draw.text((sx, sub_y), hook_subtext, font=font_sub, fill=(*accent, 220))

    arr = np.array(img)
    return ImageClip(arr, ismask=False).set_duration(duration)


def _make_science_badge(science_ref: str, duration: float) -> ImageClip:
    """
    Sağ üst köşede küçük bilimsel referans pill'i.
    "Nigg 2024 ✓" veya "MIT Research ✓" — rakiplerden ayrıştırıcı dürüstlük sinyali.
    """
    img = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    accent = ADHD_PALETTE["accent"]

    text = f"{science_ref} ✓"
    font = _load_font(30)

    try:
        tw = draw.textlength(text, font=font)
    except AttributeError:
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]

    pad_x, pad_y = 20, 10
    box_w = int(tw) + pad_x * 2
    box_h = 30 + pad_y * 2
    x1 = TARGET_W - box_w - 20
    y1 = 140
    x2 = TARGET_W - 20
    y2 = y1 + box_h

    try:
        draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=box_h // 2, fill=(0, 0, 0, 180))
        draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=box_h // 2, outline=(*accent, 200), width=2)
    except AttributeError:
        draw.rectangle([(x1, y1), (x2, y2)], fill=(0, 0, 0, 180))

    tx = x1 + pad_x
    ty = y1 + pad_y
    draw.text((tx, ty), text, font=font, fill=(*accent, 230))

    arr = np.array(img)
    return ImageClip(arr, ismask=False).set_duration(duration)


def _make_40hz_badge(duration: float) -> ImageClip:
    """Sol üst: '40Hz GAMMA' sabit etiketi."""
    img = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    accent = ADHD_PALETTE["accent"]

    text = "40Hz GAMMA"
    font = _load_font(30)

    try:
        tw = draw.textlength(text, font=font)
    except AttributeError:
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]

    pad_x, pad_y = 20, 10
    box_h = 30 + pad_y * 2
    x1, y1 = 20, 140
    x2 = x1 + int(tw) + pad_x * 2
    y2 = y1 + box_h

    try:
        draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=box_h // 2, fill=(*accent, 200))
    except AttributeError:
        draw.rectangle([(x1, y1), (x2, y2)], fill=(*accent, 200))

    draw.text((x1 + pad_x, y1 + pad_y), text, font=font, fill=(10, 10, 10, 245))

    arr = np.array(img)
    return ImageClip(arr, ismask=False).set_duration(duration)


def _make_sound_warning(palette: dict, duration: float = SOUND_WARNING_DURATION) -> ImageClip:
    """'TURN SOUND ON' — freq_video_builder'dakiyle aynı mantık, ADHD paleti ile."""
    img = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    accent = palette["accent"]

    text = "TURN SOUND ON"
    font = _load_font(46)

    try:
        tw = draw.textlength(text, font=font)
    except AttributeError:
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]

    pad_x, pad_y = 52, 22
    box_w = int(tw) + pad_x * 2
    box_h = 46 + pad_y * 2
    cx = TARGET_W // 2
    cy = int(TARGET_H * 0.62)
    x1 = cx - box_w // 2
    y1 = cy - box_h // 2
    x2 = cx + box_w // 2
    y2 = cy + box_h // 2

    try:
        draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=box_h // 2, fill=(*accent, 220))
    except AttributeError:
        draw.rectangle([(x1, y1), (x2, y2)], fill=(*accent, 220))

    tx = cx - int(tw) // 2
    ty = y1 + pad_y
    draw.text((tx + 1, ty + 1), text, font=font, fill=(0, 0, 0, 100))
    draw.text((tx, ty), text, font=font, fill=(10, 10, 10, 245))

    arr = np.array(img)
    return ImageClip(arr, ismask=False).set_duration(duration)


def build_adhd_video(script: dict, audio_path: str, output_path: str = OUTPUT_PATH) -> str:
    """
    ADHD focus music videosu üretir.

    Args:
        script: adhd_script_gen.py çıktısı
        audio_path: 40Hz + brown noise MP3
        output_path: Çıktı MP4 yolu

    Returns:
        output_path
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    hook_line = script["hook_line"]
    hook_subtext = script.get("hook_subtext", "")
    science_ref = script.get("science_ref", "Nigg 2024")
    pexels_keywords = script.get("pexels_keywords", [
        "brain network neurons", "dark minimal desk", "focused person laptop"
    ])

    palette = ADHD_PALETTE

    # ─── Ses ──────────────────────────────────────────────────────────────────
    audio_clip = AudioFileClip(audio_path)
    total_duration = min(audio_clip.duration, 55.0)
    print(f"[adhd_video] Toplam süre: {total_duration:.1f}s")

    # ─── Pexels footage (dedup) ───────────────────────────────────────────────
    seen_ids = _load_adhd_seen_ids()
    clip_paths, new_ids = _fetch_pexels_clips(pexels_keywords, n=1, seen_ids=seen_ids)
    seen_ids.update(new_ids)
    _save_adhd_seen_ids(seen_ids)
    tmp_files = list(clip_paths)

    # ─── Arka plan ────────────────────────────────────────────────────────────
    def _prepare_bg(path: str, duration: float) -> VideoFileClip:
        clip = VideoFileClip(path, audio=False)
        tr = TARGET_W / TARGET_H
        cr = clip.w / clip.h
        if cr > tr:
            new_h, new_w = TARGET_H, int(clip.w * (TARGET_H / clip.h))
        else:
            new_w, new_h = TARGET_W, int(clip.h * (TARGET_W / clip.w))
        clip = clip.resize((new_w, new_h))
        x1 = (new_w - TARGET_W) // 2
        y1 = (new_h - TARGET_H) // 2
        clip = clip.crop(x1=x1, y1=y1, x2=x1 + TARGET_W, y2=y1 + TARGET_H)
        if clip.duration < duration:
            n = int(math.ceil(duration / clip.duration))
            clip = concatenate_videoclips([clip] * n).subclip(0, duration)
        else:
            clip = clip.subclip(0, duration)
        darken = ColorClip(size=(TARGET_W, TARGET_H), color=[0, 0, 0]).set_opacity(0.55).set_duration(duration)
        return CompositeVideoClip([clip, darken])

    print("[adhd_video] Arka plan hazırlanıyor...")
    if clip_paths:
        bg_clips = []
        per = total_duration / max(len(clip_paths), 1)
        for p in clip_paths:
            try:
                bg_clips.append(_prepare_bg(p, per))
            except Exception as e:
                print(f"[adhd_video] Klip yüklenemedi ({p}): {e}")
        if bg_clips:
            bg_video = concatenate_videoclips(bg_clips)
            if bg_video.duration < total_duration:
                fill = _make_gradient_bg(palette, total_duration - bg_video.duration)
                bg_video = concatenate_videoclips([bg_video, fill])
        else:
            bg_video = _make_gradient_bg(palette, total_duration)
    else:
        bg_video = _make_gradient_bg(palette, total_duration)

    # ─── Overlay katmanları ───────────────────────────────────────────────────
    print("[adhd_video] Overlay'ler oluşturuluyor...")
    hook_overlay = _make_adhd_hook_overlay(hook_line, hook_subtext, total_duration)
    science_badge = _make_science_badge(science_ref, total_duration)
    hz_badge = _make_40hz_badge(total_duration)
    sound_warning = _make_sound_warning(palette)

    # ─── Birleştir ────────────────────────────────────────────────────────────
    print("[adhd_video] Katmanlar birleştiriliyor...")
    final_video = CompositeVideoClip(
        [bg_video, hook_overlay, hz_badge, science_badge, sound_warning],
        size=(TARGET_W, TARGET_H),
    ).set_duration(total_duration)
    final_video = final_video.set_audio(audio_clip.subclip(0, total_duration))

    # ─── Export ───────────────────────────────────────────────────────────────
    print(f"[adhd_video] Export ediliyor: {output_path}")
    final_video.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="4000k",
        audio_bitrate="192k",
        threads=4,
        preset="fast",
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        logger=None,
    )

    audio_clip.close()
    final_video.close()
    for p in tmp_files:
        try:
            os.unlink(p)
        except OSError:
            pass

    print(f"[adhd_video] Video tamamlandı: {output_path}")
    return output_path
