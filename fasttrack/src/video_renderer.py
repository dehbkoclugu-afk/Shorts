"""Render approved FastTrack records into clean vertical review videos."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageOps

from fasttrack.src.compliance import check_text
from fasttrack.src.narration import build_narration, probe_duration
from fasttrack.src.storyboards import _draw_wrapped, _font, _gradient, _hex
from fasttrack.src.video_manifest import (
    VideoJob,
    VisualBeat,
    load_video_specs,
    select_video_jobs,
)


ROOT = Path(__file__).resolve().parents[1]
WIDTH = 1080
HEIGHT = 1920


@dataclass(frozen=True)
class VideoBuildResult:
    video: Path
    thumbnail: Path
    duration: float


@dataclass(frozen=True)
class VideoFailure:
    asset_id: str
    reason: str


@dataclass(frozen=True)
class BatchBuildResult:
    succeeded: tuple[Path, ...]
    failed: tuple[VideoFailure, ...]


def video_filename(job: VideoJob) -> str:
    return f"{job.record['asset_id']}.mp4"


def caption_box(_text: str) -> tuple[int, int, int, int]:
    """Return the fixed caption safe area used by every rendered slide."""
    return (84, 1370, 996, 1680)


def _brand() -> dict:
    return json.loads((ROOT / "config" / "brand.json").read_text(encoding="utf-8"))


def render_slide(
    job: VideoJob,
    beat: VisualBeat,
    index: int,
    destination: Path,
) -> Path:
    palette = _brand()["palette"]
    background = _gradient(
        _hex(palette["dark_background"]),
        _hex(palette["dark_card"]),
    )
    draw = ImageDraw.Draw(background)
    white = (248, 248, 252)
    muted = (178, 181, 199)
    primary = _hex(palette["primary"])

    draw.rounded_rectangle((64, 56, 1016, 144), radius=40, fill=(26, 26, 46))
    draw.text((104, 80), "FASTTRACK", font=_font(31, bold=True), fill=white)
    draw.text(
        (820, 84),
        job.record["asset_id"],
        font=_font(23),
        fill=muted,
    )

    draw.rounded_rectangle((112, 204, 968, 1330), radius=64, fill=(8, 8, 14))
    draw.rounded_rectangle((132, 224, 948, 1310), radius=48, fill=(28, 29, 45))
    with Image.open(beat.screen) as source:
        capture = ImageOps.contain(source.convert("RGB"), (760, 1040))
    x = (WIDTH - capture.width) // 2
    y = 246 + (1040 - capture.height) // 2
    background.paste(capture, (x, y))

    if index == 0:
        caption = job.record["hook"]
    elif index < len(job.beats):
        caption = job.spec.benefit
    else:
        caption = job.record["cta"]
        draw.rounded_rectangle((84, 1710, 996, 1838), radius=48, fill=primary)
        _draw_wrapped(
            draw,
            "GOOGLE PLAY'DE FASTTRACK",
            xy=(150, 1745),
            font=_font(34, bold=True),
            fill=white,
            width=780,
            spacing=8,
            max_lines=1,
        )

    _draw_wrapped(
        draw,
        caption,
        xy=(84, 1390),
        font=_font(58, bold=True),
        fill=white,
        width=912,
        spacing=14,
        max_lines=3,
    )
    _draw_wrapped(
        draw,
        job.record["safety_note"],
        xy=(84, 1630),
        font=_font(22),
        fill=muted,
        width=912,
        spacing=6,
        max_lines=2,
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    background.save(destination, format="PNG", optimize=True)
    return destination


def _narration_text(job: VideoJob) -> str:
    return " ".join(
        [
            job.record["hook"],
            job.spec.benefit,
            job.record["cta"],
            job.record["safety_note"],
        ]
    )


def _concat_path(path: Path) -> str:
    return str(path.resolve()).replace("'", "'\\''")


def build_video(
    job: VideoJob,
    output_dir: Path,
    *,
    runner: Callable = subprocess.run,
) -> VideoBuildResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = output_dir / ".work" / job.record["asset_id"]
    work_dir.mkdir(parents=True, exist_ok=True)

    narration_text = _narration_text(job)
    findings = check_text(narration_text)
    if findings:
        rules = ", ".join(sorted({finding.rule_id for finding in findings}))
        raise ValueError(f"{job.record['asset_id']} narration failed compliance: {rules}")

    narration = build_narration(
        narration_text,
        job.record["locale"],
        work_dir / "narration.mp3",
        runner=runner,
    )
    narration_seconds = probe_duration(narration, runner=runner)
    if narration_seconds > 20:
        raise ValueError(
            f"{job.record['asset_id']} narration is too long: {narration_seconds:.2f}s"
        )
    total_duration = max(15.0, narration_seconds + 0.4)

    slide_paths: list[Path] = []
    durations = [beat.seconds for beat in job.beats]
    cta_duration = max(2.5, total_duration - sum(durations))
    durations.append(cta_duration)
    total_duration = sum(durations)
    if total_duration > 20.5:
        overflow = total_duration - 20.5
        durations[-1] -= overflow
        total_duration = 20.5

    for index, beat in enumerate((*job.beats, job.beats[-1])):
        slide_paths.append(
            render_slide(job, beat, index, work_dir / f"slide-{index:02d}.png")
        )

    concat_file = work_dir / "slides.txt"
    concat_lines: list[str] = []
    for slide, duration in zip(slide_paths, durations):
        concat_lines.extend(
            [f"file '{_concat_path(slide)}'", f"duration {duration:.3f}"]
        )
    concat_lines.append(f"file '{_concat_path(slide_paths[-1])}'")
    concat_file.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

    destination = output_dir / video_filename(job)
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-i",
        str(narration),
        "-vf",
        "fps=30,format=yuv420p",
        "-af",
        "apad",
        "-t",
        f"{total_duration:.3f}",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(destination),
    ]
    try:
        runner(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        stderr = getattr(exc, "stderr", "")
        raise RuntimeError(f"FFmpeg failed for {job.record['asset_id']}: {stderr or exc}") from exc
    if not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError(f"FFmpeg produced no video: {destination}")

    thumbnail = output_dir / f"{job.record['asset_id']}-thumbnail.png"
    shutil.copyfile(slide_paths[0], thumbnail)
    return VideoBuildResult(destination, thumbnail, total_duration)


def build_batch(jobs: list[VideoJob], output_dir: Path) -> BatchBuildResult:
    succeeded: list[Path] = []
    failed: list[VideoFailure] = []
    for job in jobs:
        try:
            succeeded.append(build_video(job, output_dir).video)
        except Exception as exc:  # batch boundary: preserve independent successes
            failed.append(VideoFailure(job.record["asset_id"], str(exc)))
    return BatchBuildResult(tuple(succeeded), tuple(failed))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument(
        "--manifest", type=Path, default=ROOT / "config" / "video_batch.json"
    )
    parser.add_argument(
        "--assets", type=Path, default=ROOT / "assets" / "screens" / "tr"
    )
    parser.add_argument("--content-id", action="append", dest="content_ids")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.pack.read_text(encoding="utf-8"))
    specs = load_video_specs(args.manifest)
    content_ids = args.content_ids or list(specs)
    jobs = select_video_jobs(payload["records"], specs, content_ids, args.assets)
    result = build_batch(jobs, args.output)
    report = {
        "succeeded": [str(path) for path in result.succeeded],
        "failed": [asdict(item) for item in result.failed],
    }
    (args.output / "video-build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
