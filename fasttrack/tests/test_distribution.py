import json
import tempfile
import unittest
from pathlib import Path

from fasttrack.src.content_pack import build_pack
from fasttrack.src.distribution import build_distribution, write_distribution_exports


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CHANNELS = {
    "youtube",
    "instagram",
    "tiktok",
    "facebook",
    "pinterest",
    "threads",
    "x",
    "reddit",
    "creator",
    "seo",
}


class DistributionTests(unittest.TestCase):
    def setUp(self):
        topics = json.loads(
            (ROOT / "content" / "topics.json").read_text(encoding="utf-8")
        )["topics"]
        self.records = build_pack(topics, locales=["tr"], count=1)

    def test_builds_every_supported_channel(self):
        exports = build_distribution(self.records)
        self.assertEqual(set(exports), EXPECTED_CHANNELS)
        self.assertEqual(len(exports["youtube"]), 1)
        self.assertEqual(len(exports["instagram"]), 1)

    def test_channel_rules_are_explicit(self):
        exports = build_distribution(self.records)
        self.assertEqual(exports["tiktok"][0]["publishing_mode"], "draft_only")
        self.assertEqual(exports["reddit"][0]["publishing_mode"], "human_only")
        self.assertIn("reel", exports["instagram"][0]["content_types"])
        self.assertIn("pin", exports["pinterest"][0]["content_types"])
        self.assertLessEqual(len(exports["youtube"][0]["title"]), 100)
        self.assertLessEqual(len(exports["x"][0]["post_text"]), 280)

    def test_writes_one_export_per_channel(self):
        exports = build_distribution(self.records)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            paths = write_distribution_exports(exports, output)
            self.assertEqual(len(paths), 11)
            for channel in EXPECTED_CHANNELS:
                self.assertTrue((output / f"{channel}.json").exists())
            self.assertTrue((output / "distribution-summary.md").exists())


if __name__ == "__main__":
    unittest.main()

