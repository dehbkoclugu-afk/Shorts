"""Generate FastTrack narration with Edge TTS and inspect audio duration."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable


VOICES = {"tr": "tr-TR-AhmetNeural"}


class NarrationError(RuntimeError):
    """Raised when narration generation or inspection fails."""


def build_narration(
    text: str,
    locale: str,
    destination: Path,
    *,
    runner: Callable = subprocess.run,
) -> Path:
    voice = VOICES.get(locale)
    if voice is None:
        raise ValueError(f"Unsupported narration locale: {locale}")
    if not text.strip():
        raise ValueError("Narration text must not be empty")

    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "edge-tts",
        "--voice",
        voice,
        "--rate=+8%",
        "--text",
        text.strip(),
        "--write-media",
        str(destination),
    ]
    try:
        completed = runner(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        stderr = getattr(exc, "stderr", "")
        raise NarrationError(f"Edge TTS failed: {stderr or exc}") from exc
    if not destination.is_file() or destination.stat().st_size == 0:
        raise NarrationError(f"Edge TTS produced no audio: {completed.stderr}")
    return destination


def probe_duration(
    path: Path,
    *,
    runner: Callable = subprocess.run,
) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = runner(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        duration = float(json.loads(completed.stdout)["format"]["duration"])
    except (OSError, subprocess.CalledProcessError, KeyError, ValueError, json.JSONDecodeError) as exc:
        raise NarrationError(f"Could not inspect audio duration for {path}: {exc}") from exc
    if duration <= 0:
        raise NarrationError(f"Audio duration must be positive: {path}")
    return duration
