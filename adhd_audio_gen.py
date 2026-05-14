"""
adhd_audio_gen.py — ADHD focus music için 40Hz gamma binaural beats + brown noise üretir.

Özellikler:
  - 40Hz gamma binaural beat (carrier 200Hz sol / 240Hz sağ)
  - Brown noise arka plan katmanı (ADHD için beyaz gürültüden daha etkili)
  - Pink noise karışımı (Content ID bypass)
  - pyloudnorm ile -14 LUFS mastering (YouTube normalize etmez, biz ederiz)
  - 55 saniye (YouTube Shorts maks)
  - 44100 Hz stereo WAV → MP3 çıktı
"""

import os
import struct
import wave
import subprocess
import tempfile
import math
import random

SAMPLE_RATE = 44100
CHANNELS = 2
SAMPLE_WIDTH = 2  # 16-bit
DEFAULT_DURATION = 55.0  # Shorts maks
FADE_SEC = 3.0
TARGET_LUFS = -14.0

try:
    import numpy as np
    import pyloudnorm as pyln
    _PYLN_AVAILABLE = True
except ImportError:
    _PYLN_AVAILABLE = False


def _sine_wave(freq_hz: float, duration_sec: float, amplitude: float = 0.7) -> list[float]:
    n_samples = int(SAMPLE_RATE * duration_sec)
    return [
        amplitude * math.sin(2 * math.pi * freq_hz * i / SAMPLE_RATE)
        for i in range(n_samples)
    ]


def _apply_fade(samples: list[float], fade_sec: float) -> list[float]:
    fade_n = int(SAMPLE_RATE * fade_sec)
    result = list(samples)
    total = len(result)
    for i in range(min(fade_n, total)):
        factor = i / fade_n
        result[i] *= factor
        if total - 1 - i >= 0:
            result[total - 1 - i] *= factor
    return result


def _mix(a: list[float], b: list[float], ratio: float = 0.5) -> list[float]:
    n = max(len(a), len(b))
    out = []
    for i in range(n):
        va = a[i] if i < len(a) else 0.0
        vb = b[i] if i < len(b) else 0.0
        out.append(va * (1 - ratio) + vb * ratio)
    return out


def _pink_noise(n_samples: int, amplitude: float = 0.05) -> list[float]:
    """Voss-McCartney algoritması ile pink noise üretir."""
    rows = 16
    running_total = 0.0
    vals = [0.0] * rows
    out = []
    max_val = 0.0
    for i in range(n_samples):
        idx = 0
        n = i
        while n > 0 and idx < rows:
            if n & 1:
                new_val = random.uniform(-1, 1)
                running_total -= vals[idx]
                vals[idx] = new_val
                running_total += new_val
            n >>= 1
            idx += 1
        white = random.uniform(-1, 1)
        sample = (running_total + white) / (rows + 1)
        out.append(sample)
        max_val = max(max_val, abs(sample))
    if max_val > 0:
        out = [s / max_val * amplitude for s in out]
    return out


def _brown_noise(n_samples: int, amplitude: float = 0.35) -> list[float]:
    """
    Brown noise (Brownian noise / kırmızı gürültü) üretir.
    Random walk ile — her sample öncekinin birikimli toplamı.
    White noise'dan daha derin ve alçak tonlu; ADHD çalışmaları bu tip gürültüyü destekler.
    """
    out = []
    val = 0.0
    max_val = 1e-9
    for _ in range(n_samples):
        val += random.uniform(-1, 1)
        out.append(val)
        if abs(val) > max_val:
            max_val = abs(val)

    # Normalize et ve amplitude uygula
    return [s / max_val * amplitude for s in out]


def _normalize_lufs(
    left: list[float], right: list[float], target_lufs: float = TARGET_LUFS
) -> tuple[list[float], list[float]]:
    """
    pyloudnorm ile -14 LUFS'a normalize eder.
    YouTube sessiz track'leri yükseltmez, sadece yüksekleri kısar.
    -14 LUFS ile mix'te diğer kanallara eşit ses seviyesi sağlanır.
    pyloudnorm yoksa orijinal döner.
    """
    if not _PYLN_AVAILABLE:
        print("[adhd_audio] pyloudnorm bulunamadı — LUFS normalizasyonu atlandı")
        return left, right

    import numpy as np

    audio = np.array([left, right], dtype=np.float64).T  # [n_samples, 2]
    meter = pyln.Meter(SAMPLE_RATE)
    try:
        loudness = meter.integrated_loudness(audio)
        if math.isfinite(loudness):
            normalized = pyln.normalize.loudness(audio, loudness, target_lufs)
            print(f"[adhd_audio] LUFS: {loudness:.1f} → {target_lufs:.1f}")
            return normalized[:, 0].tolist(), normalized[:, 1].tolist()
    except Exception as e:
        print(f"[adhd_audio] LUFS normalizasyon hatası (kritik değil): {e}")
    return left, right


def _samples_to_bytes(left: list[float], right: list[float]) -> bytes:
    n = min(len(left), len(right))
    frames = bytearray()
    for i in range(n):
        l_val = max(-1.0, min(1.0, left[i]))
        r_val = max(-1.0, min(1.0, right[i]))
        frames += struct.pack("<hh", int(l_val * 32767), int(r_val * 32767))
    return bytes(frames)


def generate_adhd_audio(
    carrier_hz: float = 200.0,
    beat_hz: float = 40.0,
    noise_type: str = "brown",
    output_mp3: str = "output/adhd_audio.mp3",
    duration_sec: float = DEFAULT_DURATION,
) -> str:
    """
    ADHD odak müziği üretir: 40Hz gamma binaural beat + brown/pink noise.

    Args:
        carrier_hz: Sol kulak carrier frekansı (sağ = carrier + beat_hz)
        beat_hz: Binaural beat frekansı (40Hz = gamma, dikkat ağları)
        noise_type: "brown" | "pink" | "none"
        output_mp3: Çıktı MP3 yolu
        duration_sec: Ses süresi saniye cinsinden

    Returns:
        output_mp3 yolu
    """
    right_carrier = carrier_hz + beat_hz
    n_samples = int(SAMPLE_RATE * duration_sec)

    # Küçük randomizasyon (Content ID benzersizliği)
    main_amp = round(random.uniform(0.32, 0.42), 3)
    noise_amp = round(random.uniform(0.30, 0.40), 3)
    pink_amp = round(random.uniform(0.03, 0.07), 3)

    print(
        f"[adhd_audio] {carrier_hz}Hz/{right_carrier}Hz binaural ({beat_hz}Hz beat) "
        f"+ {noise_type} noise, {duration_sec:.0f}s, amp={main_amp}"
    )

    # ─── 1) Binaural beat dalgaları ───────────────────────────────────────────
    left_tone = _sine_wave(carrier_hz, duration_sec, amplitude=main_amp)
    right_tone = _sine_wave(right_carrier, duration_sec, amplitude=main_amp)

    # ─── 2) Gürültü katmanı ───────────────────────────────────────────────────
    if noise_type == "brown":
        noise_l = _brown_noise(n_samples, amplitude=noise_amp)
        noise_r = _brown_noise(n_samples, amplitude=noise_amp)
    elif noise_type == "pink":
        noise_l = _pink_noise(n_samples, amplitude=noise_amp)
        noise_r = _pink_noise(n_samples, amplitude=noise_amp)
    else:
        noise_l = [0.0] * n_samples
        noise_r = [0.0] * n_samples

    # Gürültü dominant arka plan (ADHD için)
    left_final = _mix(left_tone, noise_l, ratio=0.55)
    right_final = _mix(right_tone, noise_r, ratio=0.55)

    # ─── 3) Pink noise (Content ID fingerprint kırıcı) ────────────────────────
    pk_l = _pink_noise(n_samples, amplitude=pink_amp)
    pk_r = _pink_noise(n_samples, amplitude=pink_amp)
    left_final = _mix(left_final, pk_l, ratio=0.08)
    right_final = _mix(right_final, pk_r, ratio=0.08)

    # ─── 4) Fade-in / fade-out ────────────────────────────────────────────────
    left_final = _apply_fade(left_final, FADE_SEC)
    right_final = _apply_fade(right_final, FADE_SEC)

    # ─── 5) -14 LUFS mastering ────────────────────────────────────────────────
    left_final, right_final = _normalize_lufs(left_final, right_final, TARGET_LUFS)

    # ─── 6) WAV yaz ──────────────────────────────────────────────────────────
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False, prefix="adhd_")
    tmp_wav.close()

    pcm_data = _samples_to_bytes(left_final, right_final)
    with wave.open(tmp_wav.name, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)

    print(f"[adhd_audio] WAV yazıldı: {tmp_wav.name} ({os.path.getsize(tmp_wav.name) // 1024} KB)")

    # ─── 7) WAV → MP3 (ffmpeg) ───────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_mp3) if os.path.dirname(output_mp3) else ".", exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", tmp_wav.name,
        "-codec:a", "libmp3lame",
        "-b:a", "192k",
        "-ar", str(SAMPLE_RATE),
        output_mp3,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(tmp_wav.name)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg WAV→MP3 başarısız:\n{result.stderr}")

    print(f"[adhd_audio] MP3 kaydedildi: {output_mp3} ({os.path.getsize(output_mp3) // 1024} KB)")
    return output_mp3


if __name__ == "__main__":
    out = generate_adhd_audio(output_mp3="/tmp/test_adhd_40hz.mp3")
    print(f"Test çıktısı: {out}")
