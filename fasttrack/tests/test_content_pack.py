import json
import tempfile
import unittest
from pathlib import Path

from fasttrack.src.content_pack import UnsafeContentError, build_pack, write_pack


ROOT = Path(__file__).resolve().parents[1]


class ContentPackTests(unittest.TestCase):
    def setUp(self):
        self.topics = json.loads(
            (ROOT / "content" / "topics.json").read_text(encoding="utf-8")
        )["topics"]

    def test_builds_28_deterministic_localized_records(self):
        records = build_pack(self.topics)
        self.assertEqual(len(records), 28)
        self.assertEqual(records[0]["asset_id"], "FT-001-tr")
        self.assertEqual(records[1]["asset_id"], "FT-001-en")
        self.assertEqual(records[-1]["asset_id"], "FT-014-en")

    def test_records_have_complete_channel_links_and_copy(self):
        record = build_pack(self.topics, locales=["tr"], count=1)[0]
        self.assertEqual(record["master_id"], "FT-001")
        self.assertEqual(record["locale"], "tr")
        self.assertEqual(record["compliance"], "passed")
        self.assertIn("youtube", record["play_links"])
        self.assertIn("creator", record["play_links"])
        self.assertNotIn("{hook}", record["caption"])
        self.assertIn(record["hook"], record["caption"])

    def test_unsafe_topic_aborts_pack(self):
        unsafe = [
            {
                "id": "FT-999",
                "series": "test",
                "format": "test",
                "locales": {
                    "tr": {
                        "hook": "Kesin sonuç",
                        "script": "Bu yöntemle kesin kilo ver.",
                        "cta": "Dene",
                        "safety_note": ""
                    }
                }
            }
        ]
        with self.assertRaisesRegex(UnsafeContentError, "guaranteed_weight_loss"):
            build_pack(unsafe, locales=["tr"])

    def test_writes_reviewable_pack_files(self):
        records = build_pack(self.topics, locales=["en"], count=2)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_pack(records, output)
            self.assertTrue((output / "content-pack.json").exists())
            self.assertTrue((output / "content-calendar.csv").exists())
            self.assertTrue((output / "higgsfield-briefs.md").exists())
            review = (output / "review.md").read_text(encoding="utf-8")
            self.assertIn("FT-001-en", review)
            self.assertIn("FT-002-en", review)


if __name__ == "__main__":
    unittest.main()
