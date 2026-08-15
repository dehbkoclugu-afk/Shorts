import tempfile
import unittest
from pathlib import Path

from fasttrack.src.report import build_report


class ReportTests(unittest.TestCase):
    def test_builds_baseline_summary(self):
        rows = [
            {"asset_id": "FT-001-tr", "locale": "tr", "series": "beginner", "format": "faceless"},
            {"asset_id": "FT-001-en", "locale": "en", "series": "beginner", "format": "faceless"},
            {"asset_id": "FT-002-tr", "locale": "tr", "series": "recovery", "format": "ugc"},
        ]
        report = build_report(rows)
        self.assertIn("Localized assets: **3**", report)
        self.assertIn("tr: 2", report)
        self.assertIn("beginner: 2", report)


if __name__ == "__main__":
    unittest.main()

