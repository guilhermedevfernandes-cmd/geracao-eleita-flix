from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import elevenlabs_audio as audio  # noqa: E402


class ElevenLabsAudioTests(unittest.TestCase):
    def test_missing_api_key_fails_closed(self) -> None:
        with mock.patch.dict("os.environ", {"ELEVENLABS_API_KEY": ""}, clear=False):
            with mock.patch.object(audio, "load_dotenv_files", lambda: None):
                with self.assertRaisesRegex(audio.AudioGenerationError, "ELEVENLABS_API_KEY"):
                    audio.api_key()

    def test_tts_dry_run_does_not_call_network(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "voice.mp3"
            args = mock.Mock(
                out=str(out),
                text="Oi, tudo bem?",
                voice_id="gkqqIm2zTUUewCkNIkTF",
                provider="elevenlabs",
                force=False,
                dry_run=True,
                retries=1,
            )
            with mock.patch.object(audio, "generate_tts") as generate:
                code = audio.command_tts(args)
            self.assertEqual(code, 0)
            generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
