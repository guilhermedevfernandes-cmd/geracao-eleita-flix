from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import artifact_cache as cache  # noqa: E402


class ArtifactCacheTests(unittest.TestCase):
    def test_cache_invalidates_changed_inputs_and_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "frame.png"
            dependency = root / "reference.png"
            output.write_bytes(b"generated-frame")
            dependency.write_bytes(b"reference-v1")

            cache.record_cache(
                output,
                "episode-frame",
                {"source_signature": "scene-v1"},
                [("hero", dependency)],
            )
            valid, _ = cache.cache_valid(
                output,
                "episode-frame",
                {"source_signature": "scene-v1"},
                [("hero", dependency)],
            )
            self.assertTrue(valid)

            changed_input, _ = cache.cache_valid(
                output,
                "episode-frame",
                {"source_signature": "scene-v2"},
                [("hero", dependency)],
            )
            self.assertFalse(changed_input)

            dependency.write_bytes(b"reference-v2")
            changed_dependency, _ = cache.cache_valid(
                output,
                "episode-frame",
                {"source_signature": "scene-v1"},
                [("hero", dependency)],
            )
            self.assertFalse(changed_dependency)

    def test_modified_output_fails_integrity_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "voice.mp3"
            output.write_bytes(b"first")
            cache.record_cache(output, "audio", {"voice": "one"}, [])
            output.write_bytes(b"tampered")
            with self.assertRaises(cache.CacheError):
                cache.verify_recorded_output(output)


if __name__ == "__main__":
    unittest.main()
