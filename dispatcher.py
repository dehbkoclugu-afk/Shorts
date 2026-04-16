"""
dispatcher.py — Smart content system dispatcher.

Kullanım:
  python dispatcher.py Hz              # FREQ SHORTS günlük modunu etkinleştir
  python dispatcher.py Hz --count 7    # 7 video queue'ya ekle ve günlük başlat
  python dispatcher.py en              # WAR SHORTS ingilizce günlük modunu etkinleştir
  python dispatcher.py tr              # WAR SHORTS türkçe günlük modunu etkinleştir
  python dispatcher.py status          # Günlük görevlerin durumunu göster
  python dispatcher.py stop            # Günlük görevleri durdur

Sistem Yapısı:
  - "Hz" → FREQ SHORTS (Solfeggio/Binaural beat frequencies)
  - "en", "tr", vb. → WAR SHORTS (savaş/geopolitik haberleri)
  - Her sistem kendi daily posting queue'suna sahip
  - Otomatik planning ve scheduling
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta, datetime
import time
import subprocess

# ─── Sistem tipleri ve yapılandırma ──────────────────────────────────────────

SYSTEMS = {
    "Hz": {
        "name": "FREQ SHORTS",
        "mode": "freq",
        "queue_file": "freq_scheduled_queue.json",
        "used_file": "freq_used_topics.json",
        "batch_cmd": "freq_batch_producer.py",
        "main_cmd": "freq_main.py",
        "env_var": "USE_FREQ_QUEUE",
    },
    # Dil kodları War shorts için
    "en": {
        "name": "WAR SHORTS (English)",
        "mode": "war",
        "queue_file": "war_scheduled_queue.json",
        "batch_cmd": "batch_producer.py",
        "main_cmd": "main.py",
        "env_var": "USE_QUEUE",
        "language": "en",
    },
    "tr": {
        "name": "WAR SHORTS (Türkçe)",
        "mode": "war",
        "queue_file": "war_scheduled_queue_tr.json",
        "batch_cmd": "batch_producer.py",
        "main_cmd": "main.py",
        "env_var": "USE_QUEUE",
        "language": "tr",
    },
}

SCHEDULER_STATE_FILE = "dispatcher_scheduler.json"


def load_scheduler_state() -> dict:
    """Scheduler durumunu yükle."""
    if os.path.exists(SCHEDULER_STATE_FILE):
        with open(SCHEDULER_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "active_systems": [],
        "scheduled_tasks": {},
        "last_runs": {},
    }


def save_scheduler_state(state: dict) -> None:
    """Scheduler durumunu kaydet."""
    with open(SCHEDULER_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


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
    """Bir sistem için günlük modu etkinleştir (diğerleri otomatik devre dışı bırakılır)."""
    if system_key not in SYSTEMS:
        print(f"❌ Bilinmeyen sistem: {system_key}")
        return

    config = SYSTEMS[system_key]
    state = load_scheduler_state()

    # 1) DİĞER SİSTEMLERİ DEVRE DIŞI BIR (sadece biri active olabilir)
    print(f"\n🔄 Diğer sistemler devre dışı bırakılıyor...")
    for other_key in SYSTEMS.keys():
        if other_key != system_key and other_key in state["active_systems"]:
            state["active_systems"].remove(other_key)
            other_config = SYSTEMS[other_key]
            print(f"   ⚫ {other_config['name']} kapatıldı")

    print(f"\n🚀 {config['name']} — Günlük Modu Etkinleştiriliyor...")
    print(f"   {count} video kuyruğa eklenecek")
    print(f"   Queue: {config['queue_file']}")

    # 2) Queue'yu doldur
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

    # 3) Sistemi active etkinleştir
    if system_key not in state["active_systems"]:
        state["active_systems"].append(system_key)

    # 4) Scheduler durumunu güncelle
    state["scheduled_tasks"][system_key] = {
        "enabled": True,
        "enabled_at": datetime.now().isoformat(),
        "mode": "daily",
        "next_run": str(date.today()),
    }

    save_scheduler_state(state)

    # 5) Queue'yi göster
    queue = load_queue(system_key)
    if queue:
        print(f"\n✅ {config['name']} Günlük Modu Başarıyla Etkinleştirildi!")
        print(f"\n📅 Kuyruktaki videolar:")
        for item in queue[:5]:
            status = "✅ Yayınlandı" if item.get("published") else "⏳ Beklemede"
            scheduled = item.get("scheduled_date", "?")
            title = item.get("title", "?")[:50]
            print(f"   {scheduled} — {status} — {title}")

        if len(queue) > 5:
            print(f"   ... ve {len(queue) - 5} daha")
    else:
        print(f"⚠️  Queue boş — batch producer hata vermiş olabilir")


def disable_daily_mode(system_key: str) -> None:
    """Bir sistem için günlük modu devre dışı bırak."""
    if system_key not in SYSTEMS:
        print(f"❌ Bilinmeyen sistem: {system_key}")
        return

    config = SYSTEMS[system_key]
    state = load_scheduler_state()

    if system_key in state["active_systems"]:
        state["active_systems"].remove(system_key)

    state["scheduled_tasks"][system_key] = {
        "enabled": False,
        "disabled_at": datetime.now().isoformat(),
    }

    save_scheduler_state(state)
    print(f"✅ {config['name']} günlük modu devre dışı bırakıldı")


def show_status() -> None:
    """Tüm sistemlerin durumunu göster."""
    state = load_scheduler_state()

    active_count = len(state["active_systems"])
    active_sys = state["active_systems"][0] if state["active_systems"] else None

    print("\n" + "=" * 60)
    print("🎬 DISPATCHER STATUS")
    print("=" * 60)
    print(f"\n📡 Aktif Daily Sistem: {SYSTEMS[active_sys]['name'] if active_sys else '❌ NONE'}")
    print(f"   (Sadece BİR sistem aynı anda daily atabilir)\n")

    for system_key, config in SYSTEMS.items():
        is_active = system_key in state["active_systems"]
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

        task_info = state["scheduled_tasks"].get(system_key, {})
        if task_info.get("enabled_at"):
            print(f"  Etkinleştirildi: {task_info['enabled_at']}")

    print("\n" + "=" * 60)


def show_help() -> None:
    """Yardım bilgisini göster."""
    print("""
╔════════════════════════════════════════════════════════════╗
║           🎬 DISPATCHER — Smart Content System            ║
╚════════════════════════════════════════════════════════════╝

KULLANIM:
  python dispatcher.py Hz                # Freq Shorts günlük modunu etkinleştir
  python dispatcher.py Hz --count 7      # 7 video ekle ve başlat
  python dispatcher.py en                # War Shorts (İngilizce) etkinleştir
  python dispatcher.py tr                # War Shorts (Türkçe) etkinleştir
  python dispatcher.py status            # Tüm sistemlerin durumunu göster
  python dispatcher.py Hz stop           # Freq Shorts günlük modunu durdur
  python dispatcher.py help              # Bu yardım mesajını göster

SİSTEMLER:
  Hz    → FREQ SHORTS (Solfeggio/Binaural Beats)
  en    → WAR SHORTS (English)
  tr    → WAR SHORTS (Türkçe)

GÜNLÜK MOD:
  • Otomatik video queue'su oluşturur
  • Belirtilen tarihten itibaren günde 1 video yayınlar
  • Queue'yu isteğe bağlı olarak yeniden doldurabilirsiniz
  • SADECE BİR sistem aynı anda daily atabilir
  • Yeni sistem etkinleştirirseniz önceki otomatik kapatılır

ÖRNEKLER:
  # Freq Shorts'u 7 video ile başlat
  python dispatcher.py Hz --count 7

  # War Shorts İngilizce'yi 10 video ile başlat
  python dispatcher.py en --count 10

  # Durumu kontrol et
  python dispatcher.py status

  # Freq Shorts'u durdur
  python dispatcher.py Hz stop
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
