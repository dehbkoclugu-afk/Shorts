"""
adhd_main.py — ADHD Focus Music pipeline orkestratörü.

Kullanım:
  python adhd_main.py                    # Normal çalıştırma
  python adhd_main.py --dry-run          # Upload olmadan test
  python adhd_main.py --topic 2          # Topic pool'dan belirli index ile çalıştır

Pipeline:
  1) adhd_topic_pool.json'dan topic seç
  2) Gemini ile title/hook/tags üret (science-backed ADHD dili)
  3) 40Hz gamma binaural + brown noise sesi üret (55s, -14 LUFS)
  4) Video montajı: neon turkuaz overlay + science badge + ses uyarısı
  5) YouTube'a yükle (uploader.py)
  6) Telegram bildirimi
"""

import argparse
import json
import os
import random
import sys
import traceback

from adhd_script_gen import generate_adhd_script, generate_localizations, save_adhd_script
from adhd_audio_gen import generate_adhd_audio
from adhd_video_builder import build_adhd_video
from notifier import send_notification, send_error_notification

OUTPUT_DIR = "output"
TOPIC_POOL_PATH = "adhd_topic_pool.json"
USED_ADHD_PATH = "adhd_used_topics.json"
ADHD_AUDIO_PATH = os.path.join(OUTPUT_DIR, "adhd_audio.mp3")
ADHD_VIDEO_PATH = os.path.join(OUTPUT_DIR, "adhd_short.mp4")
ADHD_SCRIPT_PATH = os.path.join(OUTPUT_DIR, "adhd_script.json")


# ─── Seçim & durum ──────────────────────────────────────────────────────────

def _load_pool() -> list:
    with open(TOPIC_POOL_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_used() -> list:
    if os.path.exists(USED_ADHD_PATH):
        with open(USED_ADHD_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_used(used: list) -> None:
    with open(USED_ADHD_PATH, "w", encoding="utf-8") as f:
        json.dump(used, f, indent=2)


def pick_topic(topic_index: int = None) -> dict:
    """
    Topic seçer. topic_index verilmişse pool'dan o index'i döner.
    Aksi halde kullanılmamış topic'lerden rastgele seçer.
    Tüm topic'ler kullanıldıysa listeyi sıfırlar.
    """
    pool = _load_pool()

    if topic_index is not None:
        if 0 <= topic_index < len(pool):
            return pool[topic_index]
        raise ValueError(f"Topic index {topic_index} geçersiz (pool boyutu: {len(pool)})")

    used = _load_used()
    used_set = set(used)
    available = [t for t in pool if t["name"] not in used_set]

    if not available:
        print("[adhd_main] Tüm topic'ler kullanıldı — liste sıfırlanıyor.")
        used = []
        _save_used(used)
        available = pool

    topic = random.choice(available)
    used.append(topic["name"])
    _save_used(used)
    return topic


# ─── Adım çalıştırıcı ────────────────────────────────────────────────────────

def _step(name: str, fn, topic_name: str = ""):
    try:
        return fn()
    except Exception as e:
        print(f"\n[adhd_main] HATA — {name}: {e}", file=sys.stderr)
        traceback.print_exc()
        try:
            send_error_notification(name, e, topic_name)
        except Exception:
            pass
        raise


# ─── Pipeline ────────────────────────────────────────────────────────────────

def run(dry_run: bool = False, topic_index: int = None) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for p in [ADHD_AUDIO_PATH, ADHD_VIDEO_PATH, ADHD_SCRIPT_PATH]:
        if os.path.exists(p):
            os.remove(p)

    print("=" * 52)
    print("🧠  ADHD FOCUS — Pipeline Başlatıldı")
    print("=" * 52)

    # 1) Topic seç
    topic = pick_topic(topic_index)
    print(f"\n[adhd_main] Seçilen topic: {topic['name']}")
    print(f"[adhd_main] Bilim referansı: {topic.get('science_ref', 'Nigg 2024')}")

    # 2) Script/metadata üret
    print("\n[adhd_main] Metadata üretiliyor...")
    script = _step(
        "Script üretimi",
        lambda: generate_adhd_script(topic),
        topic["name"],
    )
    save_adhd_script(script, ADHD_SCRIPT_PATH)
    print(f"[adhd_main] Başlık: {script['title']}")

    # 2.5) Lokalizasyon — başarısız olursa video lokalizasyonsuz yüklenir
    print("\n[adhd_main] Çoklu dil çevirileri üretiliyor...")
    localizations = None
    try:
        localizations = generate_localizations(script)
    except Exception as _loc_err:
        print(f"[adhd_main] Localization üretilemedi (kritik değil): {_loc_err}")

    # 3) Audio üret (40Hz gamma + brown noise + -14 LUFS)
    print(f"\n[adhd_main] 40Hz gamma sesi üretiliyor...")
    audio_path = _step(
        "Ses üretimi",
        lambda: generate_adhd_audio(
            carrier_hz=float(topic.get("carrier_hz", 200)),
            beat_hz=float(topic.get("beat_hz", 40)),
            noise_type=topic.get("noise_type", "brown"),
            output_mp3=ADHD_AUDIO_PATH,
        ),
        topic["name"],
    )

    # 4) Video üret
    print("\n[adhd_main] Video montajı yapılıyor...")
    video_path = _step(
        "Video montajı",
        lambda: build_adhd_video(script, audio_path, ADHD_VIDEO_PATH),
        topic["name"],
    )

    if dry_run:
        if localizations:
            script["localizations"] = localizations
            save_adhd_script(script, ADHD_SCRIPT_PATH)

        print("\n" + "=" * 52)
        print("✅  DRY RUN TAMAMLANDI (upload atlandı)")
        print(f"   Script → {ADHD_SCRIPT_PATH}")
        print(f"   Ses    → {audio_path}")
        print(f"   Video  → {video_path}")
        print("=" * 52)
        return

    # 5) YouTube'a yükle
    print("\n[adhd_main] YouTube'a yükleniyor...")
    from uploader import upload_video

    base_tags = [
        "ADHD", "ADHD Focus", "40Hz Gamma", "Brown Noise", "Gamma Waves",
        "Binaural Beats", "Neuroscience", "Focus Music", "Deep Work",
        "ADHD Brain", "Science-Backed", "Shorts",
    ]
    upload_tags = list(dict.fromkeys(script["tags"] + base_tags))

    description = script.get("description", "")
    if not description:
        from adhd_script_gen import MEDICAL_DISCLAIMER
        description = (
            f"{script['title']}\n\n"
            f"{topic['short_benefit']} — 40Hz gamma binaural beats + brown noise.\n\n"
            f"🎧 Use headphones — binaural beats require stereo.\n\n"
            f"Follow for science-backed ADHD focus music.\n\n"
            f"{MEDICAL_DISCLAIMER}\n\n"
            f"#ADHDFocus #40HzGamma #BrownNoise #GammaWaves #BinauralBeats #ADHD #Shorts"
        )

    video_id = _step(
        "YouTube upload",
        lambda: upload_video(
            video_path=video_path,
            title=script["title"],
            description=description,
            tags=upload_tags,
            thumbnail_path=None,
            localizations=localizations,
            category_id="10",  # Music
        ),
        topic["name"],
    )

    print(f"\n[adhd_main] Video yüklendi: https://youtube.com/shorts/{video_id}")

    # 6) Telegram bildirimi
    print("\n[adhd_main] Bildirim gönderiliyor...")
    try:
        send_notification(
            title=script["title"],
            video_id=video_id,
            duration_sec=55,
            tags=script["tags"],
        )
    except Exception as e:
        print(f"[adhd_main] Telegram bildirimi gönderilemedi (kritik değil): {e}")

    print("\n" + "=" * 52)
    print(f"✅  TAMAMLANDI! (ADHD FOCUS SHORTS)")
    print(f"   https://youtube.com/shorts/{video_id}")
    print("=" * 52)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ADHD Focus Music Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Upload olmadan test et")
    parser.add_argument("--topic", type=int, default=None, help="Topic pool index (0-9)")
    args = parser.parse_args()

    try:
        run(dry_run=args.dry_run, topic_index=args.topic)
    except Exception as e:
        print(f"\n❌ Pipeline başarısız: {e}", file=sys.stderr)
        sys.exit(1)
