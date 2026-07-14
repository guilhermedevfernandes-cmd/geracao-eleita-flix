from __future__ import annotations

import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import openart_batch as openart  # noqa: E402
from artifact_cache import record_cache  # noqa: E402
from episode_pipeline import (  # noqa: E402
    PipelineError,
    load_episode,
    validate_visual_media,
    visual_artifact_contract,
)


class OpenArtBatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.episode_root = Path(self.temporary.name)
        (self.episode_root / "meta.env").write_text(
            "\n".join(
                [
                    'TITLE="Teste OpenArt"',
                    'SLUG="teste-openart"',
                    'STYLE="premium animated style"',
                    'IMAGE_QUALITY="cinematic"',
                    'IMAGE_NEGATIVE="defects"',
                    'MOTION_QUALITY="stable"',
                    'GEN_PROVIDER="openart"',
                    'OPENART_MCP_SERVER="openart"',
                    'OPENART_PROJECT_ID="test-project"',
                    'OPENART_IMAGE_MODEL="nano-banana-2"',
                    'OPENART_VIDEO_MODEL="kling-3-omni"',
                    'OPENART_CONCURRENCY="8"',
                    'REF_ASPECT="3:4"',
                    'ASPECT="16:9"',
                    'IMG_RES="2k"',
                    'VIDEO_RES="1080p"',
                    "VIDEO_DUR=10",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        with (self.episode_root / "characters.tsv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            csv.writer(handle, delimiter="\t", lineterminator="\n").writerows(
                [
                    [
                        "key",
                        "name",
                        "voice_id",
                        "locale",
                        "voice_approved",
                        "sheet_prompt",
                    ],
                    [
                        "hero",
                        "Herói",
                        "-",
                        "pt-BR",
                        "yes",
                        "A kind biblical hero wearing a blue robe",
                    ],
                    ["narrator", "Narrador", "-", "pt-BR", "yes", "-"],
                ]
            )
        (self.episode_root / "scenes.tsv").write_text(
            "\t".join(
                [
                    "id",
                    "act",
                    "shot",
                    "refs",
                    "voice",
                    "text",
                    "hold",
                    "image_prompt",
                    "motion_prompt",
                    "vfx",
                    "sfx",
                    "transition",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_reference_manifest_contains_parallel_mcp_contract(self) -> None:
        episode = load_episode(self.episode_root)
        manifest = openart.build_manifest(episode, "reference", [], False)

        self.assertEqual(manifest["provider"], "openart-mcp")
        self.assertEqual(manifest["max_concurrency"], 8)
        self.assertEqual(len(manifest["tasks"]), 1)
        task = manifest["tasks"][0]
        self.assertEqual(task["task_id"], "reference:hero")
        self.assertEqual(task["model"], "nano-banana-2")
        self.assertEqual(task["operation"], "text_to_image")
        self.assertEqual(task["parameters"]["aspect_ratio"], "3:4")
        self.assertEqual(task["output"]["relative_path"], "assets/hero_ref.png")

    def test_valid_cache_is_skipped_unless_forced(self) -> None:
        episode = load_episode(self.episode_root)
        output, cache_kind, values, dependencies = visual_artifact_contract(
            episode, "reference", "hero"
        )
        output.parent.mkdir(parents=True)
        output.write_bytes(b"existing-reference")
        record_cache(output, cache_kind, values, dependencies)

        cached = openart.build_manifest(
            episode, "reference", ["hero"], False
        )
        forced = openart.build_manifest(
            episode, "reference", ["hero"], True
        )

        self.assertEqual(cached["tasks"], [])
        self.assertEqual(cached["skipped"][0]["identifier"], "hero")
        self.assertEqual(len(forced["tasks"]), 1)

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe"),
        "ffmpeg/ffprobe não disponíveis",
    )
    def test_register_normalizes_and_records_openart_image(self) -> None:
        episode = load_episode(self.episode_root)
        manifest = openart.build_manifest(
            episode, "reference", ["hero"], True
        )
        task = manifest["tasks"][0]
        output = Path(task["output"]["path"])
        output.parent.mkdir(parents=True)
        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:s=768x1024",
                "-frames:v",
                "1",
                str(output),
            ],
            check=True,
            capture_output=True,
        )

        openart.register_task(episode, manifest, task, None)

        metrics = validate_visual_media(output, "reference")
        self.assertEqual(metrics["width"], 1440)
        self.assertEqual(metrics["height"], 1920)
        self.assertTrue(Path(f"{output}.meta.json").exists())
        self.assertTrue(Path(f"{output}.openart.json").exists())

    def test_legacy_provider_cannot_create_openart_batch(self) -> None:
        path = self.episode_root / "meta.env"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                'GEN_PROVIDER="openart"', 'GEN_PROVIDER="higgsfield"'
            ),
            encoding="utf-8",
        )
        episode = load_episode(self.episode_root)
        with self.assertRaisesRegex(PipelineError, "GEN_PROVIDER=openart"):
            openart.build_manifest(episode, "reference", [], False)


if __name__ == "__main__":
    unittest.main()
