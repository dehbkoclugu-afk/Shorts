"""
dispatcher.py — Simple system selector based on environment variables.

Kullanım (Local):
  python dispatcher.py Hz --count 7     # FREQ SHORTS başlat (7 video queue'ya ekle)
  python dispatcher.py en --count 10    # WAR SHORTS en başlat (10 video)
  python dispatcher.py tr --count 10    # WAR SHORTS tr başlat (10 video)
  python dispatcher.py status           # Hangi sistem aktif?

GitHub Kullanımı:
  Settings → Variables → ACTIVE_SYSTEM = "Hz" | "en" | "tr"

  Workflow'lar otomatik olarak kontrol eder:
  - daily.yml → ACTIVE_SYSTEM != "en/tr" ise skip
  - freq_daily.yml → ACTIVE_SYSTEM != "Hz" ise skip
  - Sadece aktif sistem çalışır!

Sistem Yapısı:
  - "Hz" → FREQ SHORTS (Solfeggio frequencies)
  - "en" → WAR SHORTS (English)
  - "tr" → WAR SHORTS (Turkish)
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta, datetime
import subprocess

# ─── Sistem tipleri ──────────────────────────────────────────────────────────

SYSTEMS = {
    "Hz": {
        "name": "FREQ SHORTS",
        "queue_file": "freq_scheduled_queue.json",
        "batch_cmd": "freq_batch_producer.py",
        "env_var": "USE_FREQ_QUEUE",
    },
    "en": {
        "name": "WAR SHORTS (English)",
        "queue_file": "war_scheduled_queue.json",
        "batch_cmd": "batch_producer.py",
        "language": "en",
        "env_var": "USE_QUEUE",
    },
    "tr": {
        "name": "WAR SHORTS (Türkçe)",
        "queue_file": "war_scheduled_queue_tr.json",
        "batch_cmd": "batch_producer.py",
        "language": "tr",
        "env_var": "USE_QUEUE",
    },
    "ar": {
        "name": "WAR SHORTS (العربية)",
        "queue_file": "war_scheduled_queue_ar.json",
        "batch_cmd": "batch_producer.py",
        "language": "ar",
        "env_var": "USE_QUEUE",
    },
}


def get_active_system() -> str | None:
    """GitHub environment variable'dan aktif sistemi oku."""
    # Local'da var mı kontrol et
    if os.path.exists(".env.local"):
        try:
            from dotenv import load_dotenv
            load_dotenv(".env.local")
        except:
            pass

    return os.environ.get("ACTIVE_SYSTEM", "").strip() or None


def load_queue(system_key: str) -> list:
    """Sistemin kuyruğunu yükle."""
    config = SYSTEMS.get(system_key)
    if not config:
        return []

    queue_file = config["queue_file"]
    if os.path.exists(queue_file):
        with open(queue_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_queue(system_key: str, queue: list) -> None:
    """Sistemin kuyruğunu kaydet."""
    config = SYSTEMS.get(system_key)
    if not config:
        return

    queue_file = config["queue_file"]
    with open(queue_file, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


def get_next_scheduled(system_key: str) -> dict | None:
    """Bugün yayınlanacak ilk kuyruğu döndür."""
    queue = load_queue(system_key)
    today = str(date.today())
    for item in queue:
        if not item.get("published") and item.get("scheduled_date", "") <= today:
            return item
    return None


def enable_daily_mode(system_key: str, count: int = 7) -> None:
    """Sistem için queue oluştur ve GitHub variable'da belirt."""
    if system_key not in SYSTEMS:
        print(f"❌ Bilinmeyen sistem: {system_key}")
        return

    config = SYSTEMS[system_key]

    print(f"\n🚀 {config['name']} — Queue Oluşturuluyor...")
    print(f"   {count} video kuyruğa eklenecek")
    print(f"   Queue: {config['queue_file']}")

    # 1) Queue'yu oluştur (batch producer çalıştır)
    if system_key == "Hz":
        cmd = f"python {config['batch_cmd']} --count {count}"
    else:
        lang = config.get("language", "en")
        cmd = f"python {config['batch_cmd']} --count {count} --language {lang}"

    print(f"\n   Çalıştırılıyor: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Queue doldurma başarısız:")
        print(result.stderr)
        return

    print(result.stdout)

    # 2) .env.local'a ACTIVE_SYSTEM yaz (local testing için)
    with open(".env.local", "w", encoding="utf-8") as f:
        f.write(f"ACTIVE_SYSTEM={system_key}\n")

    # 3) Queue'yi göster
    queue = load_queue(system_key)
    if queue:
        print(f"\n✅ {config['name']} Queue Başarıyla Oluşturuldu!")
        print(f"\n📅 Kuyruktaki videolar:")
        for item in queue[:5]:
            status = "✅ Yayınlandı" if item.get("published") else "⏳ Beklemede"
            scheduled = item.get("scheduled_date", "?")
            title = item.get("title", "?")[:50]
            print(f"   {scheduled} — {status} — {title}")

        if len(queue) > 5:
            print(f"   ... ve {len(queue) - 5} daha")

        print(f"\n⚙️  GitHub Settings → Variables:")
        print(f"   ACTIVE_SYSTEM = \"{system_key}\"")
        print(f"   (Workflow'lar bunu kontrol eder)")
    else:
        print(f"⚠️  Queue boş — batch producer hata vermiş olabilir")


def disable_daily_mode(system_key: str) -> None:
    """Sistemi devre dışı bırak."""
    if system_key not in SYSTEMS:
        print(f"❌ Bilinmeyen sistem: {system_key}")
        return

    config = SYSTEMS[system_key]

    # .env.local'ı kaldır
    if os.path.exists(".env.local"):
        os.remove(".env.local")

    print(f"✅ {config['name']} devre dışı bırakıldı")
    print(f"   GitHub Settings → Variables:")
    print(f"   ACTIVE_SYSTEM = \"\" (boş)")
    print(f"   (Tüm workflow'lar skip edilecek)")


def show_status() -> None:
    """Tüm sistemlerin durumunu göster."""
    active_sys = get_active_system()

    print("\n" + "=" * 60)
    print("🎬 DISPATCHER STATUS")
    print("=" * 60)
    print(f"\n📡 Aktif Daily Sistem: {SYSTEMS[active_sys]['name'] if active_sys else '❌ NONE (Tüm workflow skip)'}")
    print(f"   (Sadece BİR sistem aynı anda daily atabilir)\n")

    for system_key, config in SYSTEMS.items():
        is_active = active_sys == system_key
        status = "🟢 ACTIVE" if is_active else "⚫ INACTIVE"

        queue = load_queue(system_key)
        next_item = get_next_scheduled(system_key)

        print(f"\n{config['name']}")
        print(f"  Status: {status}")
        print(f"  Queue: {len(queue)} video")

        if next_item:
            next_date = next_item.get("scheduled_date", "?")
            next_title = next_item.get("title", "?")[:50]
            print(f"  Sonraki: {next_date} — {next_title}")
        else:
            print(f"  Sonraki: Queue boş")

    print("\n" + "=" * 60)


def show_help() -> None:
    """Yardım bilgisini göster."""
    print("""
╔════════════════════════════════════════════════════════════╗
║           🎬 DISPATCHER — Simple System Selector          ║
╚════════════════════════════════════════════════════════════╝

KULLANIM:
  python dispatcher.py Hz                # FREQ queue oluştur
  python dispatcher.py Hz --count 7      # 7 video ekle
  python dispatcher.py en                # WAR queue (English) oluştur
  python dispatcher.py tr                # WAR queue (Turkish) oluştur
  python dispatcher.py ar                # WAR queue (Arabic) oluştur
  python dispatcher.py status            # Hangi sistem aktif?
  python dispatcher.py Hz stop           # Sistemi kapat
  python dispatcher.py help              # Bu yardım

SİSTEMLER:
  Hz    → FREQ SHORTS (Solfeggio/Binaural Beats)
  en    → WAR SHORTS (English)
  tr    → WAR SHORTS (Türkçe)
  ar    → WAR SHORTS (العربية)

NASIL ÇALIŞIR:
  1. python dispatcher.py Hz --count 7
     ↓ Queue dosyası oluşturulur: freq_scheduled_queue.json
     ↓ .env.local'a ACTIVE_SYSTEM=Hz yazılır

  2. GitHub Settings → Variables → ACTIVE_SYSTEM="Hz" ayarla
     ↓ (ya da otomatik GitHub Actions'dan kontrol et)

  3. daily.yml / freq_daily.yml bunu kontrol eder:
     ↓ if ACTIVE_SYSTEM == "Hz" → freq_main.py çalış
     ↓ if ACTIVE_SYSTEM == "en" → main.py çalış

  4. Otomatik yayın her gün belirlenen saatte!

ÖRNEKLER:
  # Freq Shorts başlat (7 video)
  python dispatcher.py Hz --count 7

  # War Shorts English başlat (10 video)
  python dispatcher.py en --count 10

  # War Shorts Arapça başlat (10 video)
  python dispatcher.py ar --count 10

  # Durumu kontrol et
  python dispatcher.py status

  # Sistemi kapat
  python dispatcher.py Hz stop

ÖNEMLI:
  • SADECE BİR sistem aktif olabilir
  • GitHub Settings → Variables → ACTIVE_SYSTEM = "Hz"|"en"|"tr"
  • Workflow'lar otomatik olarak kontrol eder ve çalıştırır
  • Queue boşaldığında dispatcher.py ile yeniden dolduabilirsin
""")


def main():
    parser = argparse.ArgumentParser(
        description="Dispatcher — Smart content system router",
        add_help=False,
    )
    parser.add_argument("system", nargs="?", default="help",
                       help="System key (Hz, en, tr, status, help)")
    parser.add_argument("--count", type=int, default=7,
                       help="Videos to queue (default: 7)")
    parser.add_argument("action", nargs="?", default="enable",
                       help="enable (default) or stop")

    args = parser.parse_args()

    system_key = args.system.lower()
    action = args.action.lower() if args.action else "enable"

    # ─── Özel komutlar ──────────────────────────────────────────────────────

    if system_key == "help":
        show_help()
        return

    if system_key == "status":
        show_status()
        return

    # ─── Sistem komutları ───────────────────────────────────────────────────

    if system_key not in SYSTEMS:
        print(f"❌ Bilinmeyen sistem: {system_key}")
        print(f"   Kullanılabilir sistemler: {', '.join(SYSTEMS.keys())}, status, help")
        sys.exit(1)

    if action == "stop":
        disable_daily_mode(system_key)
    else:  # default: enable
        enable_daily_mode(system_key, args.count)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Dispatcher durduruldu")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
