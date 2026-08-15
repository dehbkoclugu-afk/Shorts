import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from fasttrack.src.content_pack import build_pack
from fasttrack.src.storyboards import render_storyboards


ROOT = Path(__file__).resolve().parents[1]


class StoryboardTests(unittest.TestCase):
    def test_renders_one_vertical_png_per_record(self):
        topics = json.loads(
            (ROOT / "content" / "topics.json").read_text(encoding="utf-8")
        )["topics"]
        records = build_pack(topics, locales=["tr"], count=2)

        with tempfile.TemporaryDirectory() as directory:
            paths = render_storyboards(records, Path(directory))
            self.assertEqual([path.name for path in paths], ["FT-001-tr.png", "FT-002-tr.png"])
            with Image.open(paths[0]) as image:
                self.assertEqual(image.size, (1080, 1920))
                self.assertEqual(image.mode, "RGB")


if __name__ == "__main__":
    unittest.main()

