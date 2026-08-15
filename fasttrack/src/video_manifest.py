"""Load the approved FastTrack video batch and resolve genuine UI captures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VisualBeat:
    screen: Path
    seconds: float


@dataclass(frozen=True)
class VideoSpec:
    content_id: str
    locale: str
    benefit: str
    beats: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class VideoJob:
    record: dict
    spec: VideoSpec
    beats: tuple[VisualBeat, ...]


class MissingVideoAssetError(ValueError):
    """Raised when a requested video is missing an approved source capture."""


def load_video_specs(path: Path) -> dict[str, VideoSpec]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1:
        raise ValueError("Unsupported video batch version")
    locale = payload.get("locale")
    if locale != "tr":
        raise ValueError("The first video batch must use locale: tr")

    ordered_ids = payload.get("content_ids", [])
    if not ordered_ids or len(ordered_ids) != len(set(ordered_ids)):
        raise ValueError("Video content IDs must be non-empty and unique")
    videos = payload.get("videos", {})
    if set(ordered_ids) != set(videos):
        raise ValueError("Video manifest IDs and video definitions must match")

    specs: dict[str, VideoSpec] = {}
    for content_id in ordered_ids:
        item = videos[content_id]
        benefit = str(item.get("benefit", "")).strip()
        if not benefit:
            raise ValueError(f"{content_id} has an empty benefit")
        beats: list[tuple[str, float]] = []
        for beat in item.get("beats", []):
            screen = str(beat.get("screen", "")).strip()
            seconds = float(beat.get("seconds", 0))
            if not screen.endswith(".png"):
                raise ValueError(f"{content_id} has an invalid PNG capture: {screen}")
            if not 2 <= seconds <= 6:
                raise ValueError(f"{content_id} beat duration must be between 2 and 6 seconds")
            beats.append((screen, seconds))
        if not beats:
            raise ValueError(f"{content_id} has no visual beats")
        specs[content_id] = VideoSpec(content_id, locale, benefit, tuple(beats))
    return specs


def select_video_jobs(
    records: list[dict],
    specs: dict[str, VideoSpec],
    content_ids: list[str],
    assets_root: Path,
) -> list[VideoJob]:
    by_key = {(record["master_id"], record["locale"]): record for record in records}
    jobs: list[VideoJob] = []
    for content_id in content_ids:
        if content_id not in specs:
            raise ValueError(f"Unknown video content ID: {content_id}")
        spec = specs[content_id]
        record = by_key.get((content_id, spec.locale))
        if record is None:
            raise ValueError(f"Missing content-pack record: {content_id}-{spec.locale}")

        beats: list[VisualBeat] = []
        for screen_name, seconds in spec.beats:
            screen = assets_root / screen_name
            if not screen.is_file():
                raise MissingVideoAssetError(
                    f"{content_id} is missing required capture: {screen}"
                )
            beats.append(VisualBeat(screen, seconds))
        jobs.append(VideoJob(record, spec, tuple(beats)))
    return jobs
