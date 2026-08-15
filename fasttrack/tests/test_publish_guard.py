import unittest

from fasttrack.src.publish_guard import validate_publish_request


class PublishGuardTests(unittest.TestCase):
    def test_allows_approved_dry_run(self):
        result = validate_publish_request(approved=True, dry_run=True, content_id="FT-001")
        self.assertEqual(result["status"], "dry-run-approved")

    def test_rejects_missing_approval(self):
        with self.assertRaisesRegex(ValueError, "approval"):
            validate_publish_request(approved=False, dry_run=True, content_id="FT-001")

    def test_blocks_live_publish_until_configured(self):
        with self.assertRaisesRegex(RuntimeError, "not configured"):
            validate_publish_request(approved=True, dry_run=False, content_id="FT-001")


if __name__ == "__main__":
    unittest.main()

