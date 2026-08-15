# FastTrack First Video Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce three review-ready Turkish 1080×1920 MP4 videos for FT-006, FT-011, and FT-013 from genuine FastTrack UI captures, narration, timed captions, and channel-specific metadata.

**Architecture:** Keep the existing content pack as the source of approved copy. Add a small batch manifest that maps each content ID to genuine UI captures and visual beats, a narration adapter around Edge TTS, a Pillow/FFmpeg renderer, and an FFprobe validator. The GitHub workflow builds each video independently, keeps successful outputs when one item fails, and fails the overall job when any requested asset is incomplete or invalid.

**Tech Stack:** Python 3.11, standard-library `unittest`, Pillow 10+, Edge TTS CLI, FFmpeg/FFprobe, GitHub Actions.

## Global Constraints

- Output language is Turkish only for this batch.
- Content IDs are exactly `FT-006`, `FT-011`, and `FT-013`.
- Master videos are 1080×1920, 9:16, H.264/AAC MP4, and 15–20 seconds long.
- Use genuine production FastTrack UI captures; missing captures are blocking.
- Do not add platform watermarks, body transformations, fake testimonials, medical promises, or quantified weight-loss outcomes.
- Privacy copy must match the production app and published privacy policy.
- Publishing remains manual and human-approved.
- Generated files remain under `fasttrack/output/` and are not committed.
- Do not add a HeyGen, Higgsfield, or other UGC provider dependency in this batch.

---

## File map

- Create `fasttrack/config/video_batch.json`: selected concepts, ordered visual beats, screen-capture keys, on-screen benefit, and CTA.
- Create `fasttrack/assets/screens/tr/README.md`: capture requirements, provenance, dimensions, and naming contract.
- Create `fasttrack/assets/screens/tr/*.png`: genuine production UI captures used by the approved manifest.
- Create `fasttrack/src/video_manifest.py`: typed manifest loading, content-record selection, capture resolution, and preflight validation.
- Create `fasttrack/src/narration.py`: Edge TTS invocation and FFprobe duration lookup.
- Create `fasttrack/src/video_renderer.py`: Pillow slide composition, FFmpeg video/audio assembly, per-item isolation, and CLI.
- Create `fasttrack/src/video_validation.py`: FFprobe-based media validation and structured results.
- Create `fasttrack/tests/test_video_manifest.py`: selection and missing-capture tests.
- Create `fasttrack/tests/test_narration.py`: command construction and duration parsing tests.
- Create `fasttrack/tests/test_video_renderer.py`: deterministic frame, caption-safe-area, isolation, and naming tests.
- Create `fasttrack/tests/test_video_validation.py`: stream, dimension, duration, and failure tests.
- Modify `.github/workflows/fasttrack-render.yml`: add selected-ID inputs, dependencies, MP4 rendering, validation, and artifact upload.
- Modify `fasttrack/README.md`: document local and Actions usage plus required human review.
- Modify `.gitignore`: keep generated narration, frames, and MP4 output out of git while allowing approved source captures.

### Task 1: Batch manifest and genuine capture preflight

**Files:**
- Create: `fasttrack/config/video_batch.json`
- Create: `fasttrack/assets/screens/tr/README.md`
- Create: `fasttrack/src/video_manifest.py`
- Test: `fasttrack/tests/test_video_manifest.py`

**Interfaces:**
- Consumes: content-pack records with `asset_id`, `master_id`, `locale`, `hook`, `script`, `cta`, and `safety_note`.
- Produces: `VideoSpec` and `VisualBeat` dataclasses; `load_video_specs(path: Path) -> dict[str, VideoSpec]`; `select_video_jobs(records: list[dict], specs: dict[str, VideoSpec], content_ids: list[str], assets_root: Path) -> list[VideoJob]`.

- [ ] **Step 1: Write the failing manifest tests**

```python
def test_selects_the_three_turkish_jobs_in_requested_order(self):
    jobs = select_video_jobs(
        self.records,
        self.specs,
        ["FT-006", "FT-011", "FT-013"],
        self.assets_root,
    )
    self.assertEqual([job.record["asset_id"] for job in jobs], [
        "FT-006-tr", "FT-011-tr", "FT-013-tr",
    ])

def test_missing_capture_names_the_content_id_and_file(self):
    with self.assertRaisesRegex(
        MissingVideoAssetError,
        r"FT-006.*timer\.png",
    ):
        select_video_jobs(
            self.records, self.specs, ["FT-006"], self.assets_root
        )
```

- [ ] **Step 2: Run the focused test and verify failure**

Run: `python -m unittest fasttrack.tests.test_video_manifest -v`

Expected: FAIL because `fasttrack.src.video_manifest` does not exist.

- [ ] **Step 3: Add the explicit three-video manifest**

Use this schema in `video_batch.json`:

```json
{
  "version": 1,
  "locale": "tr",
  "content_ids": ["FT-006", "FT-011", "FT-013"],
  "videos": {
    "FT-006": {
      "benefit": "Tüm oruç rutinin tek yerde.",
      "beats": [
        {"screen": "timer.png", "seconds": 3.5},
        {"screen": "hydration.png", "seconds": 3.5},
        {"screen": "progress.png", "seconds": 3.5}
      ]
    },
    "FT-011": {
      "benefit": "İlk sürdürülebilir planını kolayca kur.",
      "beats": [
        {"screen": "plans.png", "seconds": 4.0},
        {"screen": "schedule.png", "seconds": 4.0},
        {"screen": "timer.png", "seconds": 3.0}
      ]
    },
    "FT-013": {
      "benefit": "Hesap açmadan sade takip.",
      "beats": [
        {"screen": "launch.png", "seconds": 3.5},
        {"screen": "timer.png", "seconds": 3.5},
        {"screen": "privacy.png", "seconds": 4.0}
      ]
    }
  }
}
```

- [ ] **Step 4: Implement strict manifest loading and capture preflight**

```python
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
    pass
```

Reject unknown IDs, duplicate IDs, non-Turkish records, beat durations outside 2–6 seconds, empty benefits, and missing PNGs. Error messages must include the content ID and exact missing path.

- [ ] **Step 5: Document and add the capture contract**

`README.md` must state that files are captured from the production Android build or current Play listing, must contain no notification/identifier, and must be visually reviewed before commit. Record the source date `2026-08-15` and package `com.dehbkoclugu.fasttrack`.

- [ ] **Step 6: Run the focused tests**

Run: `python -m unittest fasttrack.tests.test_video_manifest -v`

Expected: PASS.

- [ ] **Step 7: Commit the manifest unit**

```bash
git add fasttrack/config/video_batch.json fasttrack/assets/screens/tr/README.md \
  fasttrack/src/video_manifest.py fasttrack/tests/test_video_manifest.py
git commit -m "feat: define FastTrack video batch"
```

### Task 2: Narration adapter and duration inspection

**Files:**
- Create: `fasttrack/src/narration.py`
- Test: `fasttrack/tests/test_narration.py`

**Interfaces:**
- Consumes: `text: str`, `locale: str`, and destination `Path`.
- Produces: `build_narration(text: str, locale: str, destination: Path, runner=subprocess.run) -> Path`; `probe_duration(path: Path, runner=subprocess.run) -> float`.

- [ ] **Step 1: Write failing command-construction tests**

```python
def test_builds_turkish_edge_tts_command(self):
    runner = Mock(return_value=CompletedProcess([], 0, "", ""))
    output = build_narration("Merhaba", "tr", Path("voice.mp3"), runner=runner)
    self.assertEqual(output, Path("voice.mp3"))
    command = runner.call_args.args[0]
    self.assertEqual(command[:3], ["edge-tts", "--voice", "tr-TR-AhmetNeural"])
    self.assertIn("Merhaba", command)

def test_probe_duration_parses_ffprobe_json(self):
    runner = Mock(return_value=CompletedProcess(
        [], 0, '{"format":{"duration":"17.25"}}', ""
    ))
    self.assertEqual(probe_duration(Path("voice.mp3"), runner=runner), 17.25)
```

- [ ] **Step 2: Verify the tests fail**

Run: `python -m unittest fasttrack.tests.test_narration -v`

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement safe subprocess wrappers**

Use argument arrays, `check=True`, `capture_output=True`, and `text=True`; never invoke a shell. Support `tr` with `tr-TR-AhmetNeural` and reject unknown locales. Raise `NarrationError` with stderr when Edge TTS fails or output is missing/empty.

- [ ] **Step 4: Run narration tests**

Run: `python -m unittest fasttrack.tests.test_narration -v`

Expected: PASS.

- [ ] **Step 5: Commit narration support**

```bash
git add fasttrack/src/narration.py fasttrack/tests/test_narration.py
git commit -m "feat: add FastTrack narration adapter"
```

### Task 3: Deterministic vertical frame composition

**Files:**
- Create: `fasttrack/src/video_renderer.py`
- Test: `fasttrack/tests/test_video_renderer.py`

**Interfaces:**
- Consumes: `VideoJob`, approved brand palette, and narration duration.
- Produces: `render_slide(job: VideoJob, beat: VisualBeat, index: int, destination: Path) -> Path`; `build_video(job: VideoJob, output_dir: Path, runner=subprocess.run) -> VideoBuildResult`; `build_batch(jobs: list[VideoJob], output_dir: Path) -> BatchBuildResult`.

- [ ] **Step 1: Write failing frame and naming tests**

```python
def test_render_slide_is_vertical_and_keeps_caption_in_safe_area(self):
    path = render_slide(self.job, self.job.beats[0], 0, self.output / "slide.png")
    with Image.open(path) as image:
        self.assertEqual(image.size, (1080, 1920))
    self.assertEqual(caption_box(self.job.record["hook"]).bottom <= 1680, True)

def test_output_name_is_stable(self):
    self.assertEqual(video_filename(self.job), "FT-006-tr.mp4")
```

- [ ] **Step 2: Verify focused failure**

Run: `python -m unittest fasttrack.tests.test_video_renderer -v`

Expected: FAIL because renderer interfaces do not exist.

- [ ] **Step 3: Implement Pillow slide composition**

Render a dark navy gradient, FastTrack label, a centered rounded phone frame containing the genuine capture, a two-line maximum hook/benefit caption, and a final coral CTA slide. Use DejaVu/Liberation fonts as in `storyboards.py`; keep all important text between y=180 and y=1680. Scale captures with `ImageOps.contain` and never crop product controls.

- [ ] **Step 4: Implement FFmpeg assembly**

Write a concat list with absolute escaped slide paths and beat durations. Invoke FFmpeg without a shell:

```python
command = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
    "-i", str(narration), "-vf", "fps=30,format=yuv420p",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "192k", "-shortest", str(destination),
]
```

Build narration text from `hook`, a shortened product benefit, `cta`, and `safety_note`. Adjust the final CTA slide so the total requested visual duration remains within 15–20 seconds and is not shorter than narration.

- [ ] **Step 5: Preserve successful outputs when one item fails**

```python
@dataclass(frozen=True)
class BatchBuildResult:
    succeeded: tuple[Path, ...]
    failed: tuple[VideoFailure, ...]

def build_batch(jobs, output_dir):
    succeeded, failed = [], []
    for job in jobs:
        try:
            succeeded.append(build_video(job, output_dir).video)
        except Exception as exc:
            failed.append(VideoFailure(job.record["asset_id"], str(exc)))
    return BatchBuildResult(tuple(succeeded), tuple(failed))
```

- [ ] **Step 6: Run renderer tests**

Run: `python -m unittest fasttrack.tests.test_video_renderer -v`

Expected: PASS.

- [ ] **Step 7: Commit rendering unit**

```bash
git add fasttrack/src/video_renderer.py fasttrack/tests/test_video_renderer.py
git commit -m "feat: render FastTrack vertical videos"
```

### Task 4: Media validation and truthful failure status

**Files:**
- Create: `fasttrack/src/video_validation.py`
- Test: `fasttrack/tests/test_video_validation.py`

**Interfaces:**
- Consumes: rendered MP4 `Path` and FFprobe JSON.
- Produces: `MediaFacts`; `validate_video(path: Path, runner=subprocess.run) -> MediaFacts`; raises `VideoValidationError` containing every failed invariant.

- [ ] **Step 1: Write failing validator tests**

```python
def test_accepts_valid_vertical_mp4(self):
    facts = validate_probe_payload(self.valid_payload)
    self.assertEqual((facts.width, facts.height), (1080, 1920))
    self.assertTrue(facts.has_audio)

def test_rejects_wrong_dimensions_and_missing_audio_together(self):
    with self.assertRaisesRegex(
        VideoValidationError,
        "1080x1920.*audio stream",
    ):
        validate_probe_payload(self.invalid_payload)
```

- [ ] **Step 2: Verify failure**

Run: `python -m unittest fasttrack.tests.test_video_validation -v`

Expected: FAIL because validator interfaces do not exist.

- [ ] **Step 3: Implement FFprobe parsing and invariants**

Validate: file exists and is non-empty; video stream exists; width=1080; height=1920; audio stream exists; duration is between 15.0 and 20.5 seconds; video codec is H.264; audio codec is AAC; frame rate is at least 24 fps.

- [ ] **Step 4: Run validator tests**

Run: `python -m unittest fasttrack.tests.test_video_validation -v`

Expected: PASS.

- [ ] **Step 5: Commit validation unit**

```bash
git add fasttrack/src/video_validation.py fasttrack/tests/test_video_validation.py
git commit -m "test: validate FastTrack video artifacts"
```

### Task 5: CLI, real captures, and end-to-end local build

**Files:**
- Modify: `fasttrack/src/video_renderer.py`
- Create: `fasttrack/assets/screens/tr/timer.png`
- Create: `fasttrack/assets/screens/tr/hydration.png`
- Create: `fasttrack/assets/screens/tr/progress.png`
- Create: `fasttrack/assets/screens/tr/plans.png`
- Create: `fasttrack/assets/screens/tr/schedule.png`
- Create: `fasttrack/assets/screens/tr/launch.png`
- Create: `fasttrack/assets/screens/tr/privacy.png`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `--pack`, `--manifest`, `--assets`, `--content-id` (repeatable), and `--output` CLI arguments.
- Produces: three MP4s, three thumbnails, `video-build-report.json`, and non-zero exit when any requested item fails.

- [ ] **Step 1: Import and verify current production captures**

Obtain captures from the production package/current Play listing, remove no UI elements, and place them under the exact manifest filenames. Open every image and verify it belongs to FastTrack, contains no personal notification/identifier, and accurately supports its assigned beat.

- [ ] **Step 2: Add CLI parsing and report output**

```python
parser.add_argument("--pack", type=Path, required=True)
parser.add_argument("--manifest", type=Path, default=ROOT / "config" / "video_batch.json")
parser.add_argument("--assets", type=Path, default=ROOT / "assets" / "screens" / "tr")
parser.add_argument("--content-id", action="append", dest="content_ids")
parser.add_argument("--output", type=Path, required=True)
```

Default IDs come from the manifest. Write JSON with `succeeded`, `failed`, media facts, asset IDs, and output paths. Return exit code 1 if `failed` is non-empty.

- [ ] **Step 3: Generate the selected content pack**

Run:

```bash
python -m fasttrack.src.planner --locales tr \
  --content-id FT-006 --content-id FT-011 --content-id FT-013 \
  --output fasttrack/output
```

Expected: three records in `fasttrack/output/content-pack.json`.

- [ ] **Step 4: Render the three MP4s**

Run:

```bash
python -m fasttrack.src.video_renderer \
  --pack fasttrack/output/content-pack.json \
  --output fasttrack/output/videos
```

Expected: `FT-006-tr.mp4`, `FT-011-tr.mp4`, `FT-013-tr.mp4`, three thumbnails, and a build report.

- [ ] **Step 5: Validate all MP4s**

Run:

```bash
python -m fasttrack.src.video_validation fasttrack/output/videos/*.mp4
```

Expected: exit 0 and one valid-media summary per file.

- [ ] **Step 6: Commit source captures and CLI**

```bash
git add .gitignore fasttrack/assets/screens/tr fasttrack/src/video_renderer.py
git commit -m "feat: build first FastTrack video batch"
```

### Task 6: GitHub Actions artifact and operator documentation

**Files:**
- Modify: `.github/workflows/fasttrack-render.yml`
- Modify: `fasttrack/README.md`

**Interfaces:**
- Consumes: workflow inputs `content_ids` and `locale`.
- Produces: `fasttrack-videos-<run_id>` artifact containing videos, thumbnails, content pack, platform metadata, review checklist, and build report.

- [ ] **Step 1: Extend workflow inputs and dependencies**

Set defaults to `FT-006,FT-011,FT-013` and `tr`. Install `Pillow>=10`, `edge-tts>=7,<8`; verify `ffmpeg -version` and `ffprobe -version` before rendering.

- [ ] **Step 2: Build explicit planner arguments safely**

Use Bash to split only comma-separated IDs matching `^FT-[0-9]{3}$`; append each as a separate `--content-id` argument. Reject empty or malformed input before running Python.

- [ ] **Step 3: Add render, validate, and artifact steps**

The workflow must run the full unit suite, create the selected pack, render videos, run validation, build the baseline report, and upload `fasttrack/output/` with `if-no-files-found: error`. Do not use `continue-on-error` for compliance, render, or validation.

- [ ] **Step 4: Document local and workflow operation**

Add exact commands, source-capture provenance rules, artifact contents, human review checklist, and the explicit statement that publishing remains manual.

- [ ] **Step 5: Run complete local validation**

Run:

```bash
python -m unittest discover -s fasttrack/tests -v
python -m compileall -q fasttrack
git diff --check
```

Expected: all tests pass, compilation succeeds, and diff check is clean.

- [ ] **Step 6: Commit workflow and documentation**

```bash
git add .github/workflows/fasttrack-render.yml fasttrack/README.md
git commit -m "ci: publish FastTrack video review artifacts"
```

### Task 7: Final review package

**Files:**
- Verify: `fasttrack/output/videos/*`
- Verify: `fasttrack/output/platforms/*`
- Verify: `fasttrack/output/review.md`

**Interfaces:**
- Consumes: the completed build output.
- Produces: a human-approved three-day distribution package; no live social mutation.

- [ ] **Step 1: Inspect all three videos at representative frames**

Extract frames at 1, 8, and 16 seconds with FFmpeg. Confirm correct UI, readable captions, no crop of product controls, no personal data, and correct CTA.

- [ ] **Step 2: Confirm channel metadata and links**

Verify YouTube, Instagram, TikTok, Facebook, and Pinterest records reference the matching asset ID and channel-coded Play Store URL.

- [ ] **Step 3: Confirm health and privacy copy**

Run `check_text` on narration and visible text. Compare FT-013 privacy wording with the current production privacy policy and app behavior.

- [ ] **Step 4: Run final repository checks**

Run:

```bash
python -m unittest discover -s fasttrack/tests -v
python -m compileall -q fasttrack
git status -sb
git log --oneline --max-count=8
```

Expected: clean tests/compilation and only intentional commits on `agent/fasttrack-growth`.

- [ ] **Step 5: Push the completed branch once**

```bash
git push origin agent/fasttrack-growth
```

PR #98 updates in place; do not create a second PR.
