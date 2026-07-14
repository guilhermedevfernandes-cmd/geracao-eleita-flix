from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTests(unittest.TestCase):
    def test_generated_episode_is_self_contained_and_title_is_not_executed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary)
            marker = output_root / "should-not-exist"
            title = f"Jonas $(touch {marker})"
            subprocess.run(
                [
                    str(ROOT / "scripts" / "new-episode.sh"),
                    "jonas-teste",
                    title,
                    str(output_root),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            episode = output_root / "jonas-teste"
            self.assertTrue((episode / "_pipeline" / "episode_pipeline.py").exists())
            self.assertTrue((episode / "_pipeline" / "artifact_cache.py").exists())
            self.assertTrue((episode / "_pipeline" / "audio_contract.py").exists())
            self.assertTrue((episode / "_pipeline" / "openart_batch.py").exists())
            self.assertTrue((episode / "approve-visual.sh").exists())
            self.assertTrue((episode / "approve-music.sh").exists())
            self.assertTrue((episode / "register-openart.sh").exists())
            self.assertTrue((episode / "approvals").is_dir())
            self.assertTrue((episode / "logs").is_dir())

            validation = subprocess.run(
                [str(episode / "validate.sh"), "script"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(validation.returncode, 1)
            self.assertFalse(marker.exists())

            env_output = subprocess.run(
                [
                    "python3",
                    str(episode / "_pipeline" / "episode_pipeline.py"),
                    "env",
                    "--episode",
                    str(episode),
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            self.assertIn(title, env_output)
            self.assertIn("GEN_PROVIDER\topenart", env_output)


if __name__ == "__main__":
    unittest.main()
