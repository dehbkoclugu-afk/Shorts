"""Validate FastTrack MP4 deliverables with FFprobe."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class MediaFacts:
    width: int
    height: int
    duration: float
    frame_rate: float
    video_codec: str
    audio_codec: str | None
    has_audio: bool


class VideoValidationError(ValueError):
    """Raised when a video violates one or more launch invariants."""


def _frame_rate(value: str) -> float:
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return 0.0


def validate_probe_payload(payload: dict) -> MediaFacts:
    streams = payload.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    errors: list[str] = []
    if video is None:
        raise VideoValidationError("missing video stream; missing 1080x1920 dimensions")

    width = int(video.get("width", 0))
    height = int(video.get("height", 0))
    duration = float(payload.get("format", {}).get("duration", 0))
    frame_rate = _frame_rate(video.get("avg_frame_rate", "0/1"))
    video_codec = str(video.get("codec_name", ""))
    audio_codec = str(audio.get("codec_name")) if audio else None

    if (width, height) != (1080, 1920):
        errors.append(f"expected 1080x1920, got {width}x{height}")
    if audio is None:
        errors.append("missing audio stream")
    if not 15.0 <= duration <= 20.5:
        errors.append(f"duration must be between 15.0 and 20.5 seconds, got {duration:.3f}")
    if video_codec != "h264":
        errors.append(f"video codec must be h264, got {video_codec or 'none'}")
    if audio is not None and audio_codec != "aac":
        errors.append(f"audio codec must be aac, got {audio_codec}")
    if frame_rate < 24:
        errors.append(f"frame rate must be at least 24 fps, got {frame_rate:.3f}")
    if errors:
        raise VideoValidationError("; ".join(errors))

    return MediaFacts(
        width,
        height,
        duration,
        frame_rate,
        video_codec,
        audio_codec,
        audio is not None,
    )


def validate_video(
    path: Path,
    *,
    runner: Callable = subprocess.run,
) -> MediaFacts:
    if not path.is_file() or path.stat().st_size == 0:
        raise VideoValidationError(f"video is missing or empty: {path}")
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_streams",
        "-show_format",
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
        payload = json.loads(completed.stdout)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise VideoValidationError(f"FFprobe failed for {path}: {exc}") from exc
    return validate_probe_payload(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("videos", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.videos:
        try:
            facts = validate_video(path)
            print(json.dumps({"path": str(path), **asdict(facts)}, ensure_ascii=False))
        except VideoValidationError as exc:
            failed = True
            print(json.dumps({"path": str(path), "error": str(exc)}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
