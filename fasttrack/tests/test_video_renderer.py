import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from fasttrack.src.video_manifest import VideoJob, VideoSpec, VisualBeat
from fasttrack.src.video_renderer import (
    VideoBuildResult,
    build_batch,
    caption_box,
    render_slide,
    video_filename,
)


class VideoRendererTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)
        screen = self.output / "timer.png"
        Image.new("RGB", (360, 800), "white").save(screen)
        record = {
            "asset_id": "FT-006-tr",
            "master_id": "FT-006",
            "locale": "tr",
            "hook": "Bir oruç zamanlayıcısı sadece geri sayım olmamalı.",
            "cta": "FastTrack'i Google Play'den indir.",
            "safety_note": "FastTrack bir iyi yaşam takip uygulamasıdır.",
        }
        spec = VideoSpec(
            "FT-006",
            "tr",
            "Tüm oruç rutinin tek yerde.",
            (("timer.png", 3.5),),
        )
        self.job = VideoJob(record, spec, (VisualBeat(screen, 3.5),))

    def test_render_slide_is_vertical_and_keeps_caption_in_safe_area(self):
        path = render_slide(
            self.job,
            self.job.beats[0],
            0,
            self.output / "slide.png",
        )
        with Image.open(path) as image:
            self.assertEqual(image.size, (1080, 1920))
            self.assertEqual(image.mode, "RGB")
        self.assertLessEqual(caption_box(self.job.record["hook"])[3], 1680)

    def test_output_name_is_stable(self):
        self.assertEqual(video_filename(self.job), "FT-006-tr.mp4")

    def test_batch_keeps_success_when_another_video_fails(self):
        second = VideoJob(
            {**self.job.record, "asset_id": "FT-011-tr", "master_id": "FT-011"},
            VideoSpec("FT-011", "tr", "Kolay plan.", (("timer.png", 3.5),)),
            self.job.beats,
        )

        def build(job, output_dir):
            if job.record["master_id"] == "FT-011":
                raise RuntimeError("broken")
            video = output_dir / video_filename(job)
            video.touch()
            return VideoBuildResult(video, output_dir / "thumb.png", 16.0)

        with patch("fasttrack.src.video_renderer.build_video", side_effect=build):
            result = build_batch([self.job, second], self.output)

        self.assertEqual([path.name for path in result.succeeded], ["FT-006-tr.mp4"])
        self.assertEqual(result.failed[0].asset_id, "FT-011-tr")
        self.assertIn("broken", result.failed[0].reason)


if __name__ == "__main__":
    unittest.main()
