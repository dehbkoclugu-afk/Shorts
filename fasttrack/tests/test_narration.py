import json
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import Mock

from fasttrack.src.narration import build_narration, probe_duration


class NarrationTests(unittest.TestCase):
    def test_builds_turkish_edge_tts_command(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "voice.mp3"

            def run(command, **_kwargs):
                destination.write_bytes(b"audio")
                return CompletedProcess(command, 0, "", "")

            runner = Mock(side_effect=run)
            output = build_narration("Merhaba", "tr", destination, runner=runner)

        self.assertEqual(output, destination)
        command = runner.call_args.args[0]
        self.assertEqual(command[:3], ["edge-tts", "--voice", "tr-TR-AhmetNeural"])
        self.assertIn("Merhaba", command)

    def test_probe_duration_parses_ffprobe_json(self):
        runner = Mock(
            return_value=CompletedProcess(
                [],
                0,
                json.dumps({"format": {"duration": "17.25"}}),
                "",
            )
        )
        self.assertEqual(probe_duration(Path("voice.mp3"), runner=runner), 17.25)

    def test_rejects_unknown_locale(self):
        with self.assertRaisesRegex(ValueError, "Unsupported narration locale"):
            build_narration("Hello", "xx", Path("voice.mp3"), runner=Mock())


if __name__ == "__main__":
    unittest.main()
