import unittest

from fasttrack.src.video_validation import (
    VideoValidationError,
    validate_probe_payload,
)


class VideoValidationTests(unittest.TestCase):
    def setUp(self):
        self.valid_payload = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1080,
                    "height": 1920,
                    "avg_frame_rate": "30/1",
                },
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            "format": {"duration": "16.2"},
        }

    def test_accepts_valid_vertical_mp4(self):
        facts = validate_probe_payload(self.valid_payload)
        self.assertEqual((facts.width, facts.height), (1080, 1920))
        self.assertTrue(facts.has_audio)
        self.assertEqual(facts.duration, 16.2)

    def test_rejects_wrong_dimensions_and_missing_audio_together(self):
        invalid = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 720,
                    "height": 1280,
                    "avg_frame_rate": "30/1",
                }
            ],
            "format": {"duration": "16.0"},
        }
        with self.assertRaises(VideoValidationError) as raised:
            validate_probe_payload(invalid)
        self.assertIn("1080x1920", str(raised.exception))
        self.assertIn("audio stream", str(raised.exception))

    def test_rejects_duration_outside_launch_range(self):
        self.valid_payload["format"]["duration"] = "21.0"
        with self.assertRaisesRegex(VideoValidationError, "15.0 and 20.5"):
            validate_probe_payload(self.valid_payload)


if __name__ == "__main__":
    unittest.main()
