import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from fasttrack.src.content_pack import build_pack
from fasttrack.src.video_manifest import (
    MissingVideoAssetError,
    load_video_specs,
    select_video_jobs,
)


ROOT = Path(__file__).resolve().parents[1]


class VideoManifestTests(unittest.TestCase):
    def setUp(self):
        topics = json.loads(
            (ROOT / "content" / "topics.json").read_text(encoding="utf-8")
        )["topics"]
        self.records = build_pack(
            topics,
            locales=["tr"],
            content_ids={"FT-006", "FT-011", "FT-013"},
        )
        self.specs = load_video_specs(ROOT / "config" / "video_batch.json")

    def _create_assets(self, root: Path) -> None:
        names = {
            screen
            for spec in self.specs.values()
            for screen, _seconds in spec.beats
        }
        for name in names:
            Image.new("RGB", (360, 800), "white").save(root / name)

    def test_selects_the_three_turkish_jobs_in_requested_order(self):
        with tempfile.TemporaryDirectory() as directory:
            assets = Path(directory)
            self._create_assets(assets)
            jobs = select_video_jobs(
                self.records,
                self.specs,
                ["FT-006", "FT-011", "FT-013"],
                assets,
            )

        self.assertEqual(
            [job.record["asset_id"] for job in jobs],
            ["FT-006-tr", "FT-011-tr", "FT-013-tr"],
        )

    def test_missing_capture_names_the_content_id_and_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                MissingVideoAssetError,
                r"FT-006.*timer\.png",
            ):
                select_video_jobs(
                    self.records,
                    self.specs,
                    ["FT-006"],
                    Path(directory),
                )

    def test_rejects_unknown_content_id(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Unknown video content ID: FT-999"):
                select_video_jobs(
                    self.records,
                    self.specs,
                    ["FT-999"],
                    Path(directory),
                )


if __name__ == "__main__":
    unittest.main()
