import unittest
from urllib.parse import parse_qs, unquote, urlparse

from fasttrack.src.campaign_links import build_play_url


class CampaignLinkTests(unittest.TestCase):
    def test_builds_encoded_play_referrer(self):
        url = build_play_url("youtube", "tr", "FT-001")
        query = parse_qs(urlparse(url).query)

        self.assertEqual(query["id"], ["com.dehbkoclugu.fasttrack"])
        referrer = parse_qs(unquote(query["referrer"][0]))
        self.assertEqual(referrer["utm_source"], ["youtube"])
        self.assertEqual(referrer["utm_medium"], ["organic_video"])
        self.assertEqual(referrer["utm_campaign"], ["launch_2026_tr"])
        self.assertEqual(referrer["utm_content"], ["ft-001"])

    def test_rejects_unknown_channel(self):
        with self.assertRaisesRegex(ValueError, "Unknown channel"):
            build_play_url("unknown", "tr", "FT-001")

    def test_rejects_malformed_content_id(self):
        with self.assertRaisesRegex(ValueError, "content ID"):
            build_play_url("youtube", "tr", "first-video")

    def test_rejects_unsupported_locale(self):
        with self.assertRaisesRegex(ValueError, "locale"):
            build_play_url("youtube", "jp", "FT-001")


if __name__ == "__main__":
    unittest.main()

