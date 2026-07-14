from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import episode_pipeline as pipeline  # noqa: E402
from artifact_cache import record_cache  # noqa: E402
from audio_contract import TTS_JOB_TYPE, VOICE_TEST_TEXT, tts_values  # noqa: E402


class EpisodePipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.episode = Path(self.temporary.name)
        self.write_meta()
        self.write_characters()
        self.write_scenes()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_meta(self) -> None:
        (self.episode / "meta.env").write_text(
            "\n".join(
                [
                    'TITLE="Episódio de teste"',
                    'SLUG="episodio-teste"',
                    'LANGUAGE="pt-BR"',
                    "TARGET_DURATION=300",
                    "MIN_DURATION=285",
                    "MAX_DURATION=315",
                    "WORDS_PER_MINUTE=138",
                    "MIN_SCENES=34",
                    "MAX_SCENES=46",
                    "MIN_BEAT_SECONDS=2.0",
                    "MAX_BEAT_SECONDS=11.2",
                    "MIN_VOICES=4",
                    "MIN_DIALOGUE_RATIO=0.25",
                    "MIN_ACTS=6",
                    "MIN_SHOT_VARIETY=8",
                    "MIN_VFX_RATIO=0.25",
                    "MIN_SFX_RATIO=0.70",
                    "MIN_IMAGE_PROMPT_CHARS=100",
                    "MIN_MOTION_PROMPT_CHARS=60",
                    "VIDEO_DUR=10",
                    "MAX_STRETCH=1.12",
                    'ASPECT="16:9"',
                    'IMG_RES="2k"',
                    'REF_ASPECT="3:4"',
                    "FPS=24",
                    'STYLE="premium style"',
                    'IMAGE_QUALITY="cinematic quality"',
                    'IMAGE_NEGATIVE="defects"',
                    'MOTION_QUALITY="stable motion"',
                    'GEN_PROVIDER="${GEN_PROVIDER:-openart}"',
                    'OPENART_MCP_SERVER="openart"',
                    'OPENART_PROJECT_ID="test-project"',
                    'OPENART_IMAGE_MODEL="nano-banana-2"',
                    'OPENART_VIDEO_MODEL="kling-3-omni"',
                    'OPENART_CONCURRENCY="8"',
                    'VIDEO_RES="1080p"',
                    "BGMVOL=0.12",
                    "SFXVOL=0.38",
                    "MASTER_LIMIT=0.95",
                    'SCORE_PROMPT="warm score"',
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def write_characters(
        self,
        hero_locale: str = "pt-BR",
        approved: str = "yes",
        hero_voice_id: str = "22222222-2222-4222-8222-222222222222",
    ) -> None:
        rows = [
            [
                "narrator",
                "Narrador",
                "11111111-1111-4111-8111-111111111111",
                "pt-BR",
                "yes",
                "-",
            ],
            [
                "hero",
                "Herói",
                hero_voice_id,
                hero_locale,
                approved,
                "A consistent kind biblical hero in a detailed robe",
            ],
            [
                "deus",
                "Voz de Deus",
                "33333333-3333-4333-8333-333333333333",
                "pt-BR",
                "yes",
                "-",
            ],
            [
                "captain",
                "Capitão",
                "44444444-4444-4444-8444-444444444444",
                "pt-BR",
                "yes",
                "A weathered but kind ancient ship captain in layered nautical robes",
            ],
        ]
        with (self.episode / "characters.tsv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(pipeline.CHARACTER_FIELDS)
            writer.writerows(rows)

    def write_scenes(self, long_first_beat: bool = False) -> None:
        voices = ["narrator", "hero", "deus", "captain"]
        acts = [f"beat-{index}" for index in range(1, 9)]
        shots = [
            "extreme-wide",
            "wide",
            "medium",
            "close-up",
            "extreme-close-up",
            "aerial",
            "low-angle",
            "over-shoulder",
        ]
        image_prompt = (
            "A carefully staged cinematic biblical environment with layered foreground, "
            "midground and background, expressive acting, motivated lighting and rich detail."
        )
        motion_prompt = (
            "The character performs a clear emotional action while the camera moves with "
            "purpose and the environment responds with natural secondary motion."
        )

        rows = []
        portuguese_words = (
            "Quando o povo ouviu a voz de Deus ele abriu o coração e caminhou "
            "com fé para um novo começo"
        ).split()
        for index in range(34):
            count = 40 if long_first_beat and index == 0 else 20
            repeated = (portuguese_words * ((count // len(portuguese_words)) + 1))[
                :count
            ]
            rows.append(
                [
                    f"{index + 1:02d}",
                    acts[index % len(acts)],
                    shots[index % len(shots)],
                    "hero",
                    voices[index % len(voices)],
                    " ".join(repeated),
                    "0.5",
                    image_prompt,
                    motion_prompt,
                    "volumetric rain and glowing particles" if index % 3 == 0 else "-",
                    "wind, cloth movement, footsteps and distant ambience"
                    if index % 5 != 0
                    else "-",
                    "cut",
                ]
            )

        with (self.episode / "scenes.tsv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(pipeline.SCENE_FIELDS)
            writer.writerows(rows)

    def result(self, stage: str = "script") -> pipeline.ValidationResult:
        episode = pipeline.load_episode(self.episode)
        return pipeline.validate_episode(episode, stage)

    def test_environment_frame_prompt_forbids_invented_people(self) -> None:
        episode = pipeline.load_episode(self.episode)
        episode.meta["STYLE"] = (
            "premium stylized 3D, expressive appealing characters, cinematic"
        )
        scene = dict(episode.scenes[0])
        scene["refs"] = "-"
        scene["voice"] = "deus"

        prompt = pipeline.frame_prompt(episode, scene)

        self.assertTrue(prompt.startswith("ENVIRONMENT-ONLY FRAME"))
        self.assertIn("zero people and zero humanoid characters", prompt)
        self.assertIn("never depict God as a person", prompt)
        self.assertIn("Never add modern clothing", prompt)
        self.assertNotIn("expressive appealing characters", prompt)

    def test_referenced_frame_prompt_uses_cast_as_strict_whitelist(self) -> None:
        episode = pipeline.load_episode(self.episode)
        scene = dict(episode.scenes[0])
        scene["refs"] = "hero,captain"

        prompt = pipeline.frame_prompt(episode, scene)

        self.assertTrue(prompt.startswith("CHARACTER CAST LOCK"))
        self.assertIn("supplied references for Herói, Capitão", prompt)
        self.assertIn("Do not invent extras, crowds, children", prompt)
        self.assertIn("never depict God as a person", prompt)

    def create_voice_sample(self, key: str) -> pipeline.Episode:
        episode = pipeline.load_episode(self.episode)
        character = episode.cast[key]
        output = self.episode / "audio" / "voice-tests" / f"{key}.mp3"
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=0.3",
                "-c:a",
                "libmp3lame",
                str(output),
                "-loglevel",
                "error",
            ],
            check=True,
        )
        record_cache(
            output,
            f"elevenlabs-audio:{TTS_JOB_TYPE}",
            tts_values(VOICE_TEST_TEXT, character["voice_id"]),
            [],
        )
        return episode

    def replace_scene_text(self, scene_index: int, text: str) -> None:
        path = self.episode / "scenes.tsv"
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle, delimiter="\t"))
        rows[scene_index + 1][5] = text
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerows(rows)

    def create_image(self, path: Path, size: str, color: str = "blue") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s={size}",
                "-frames:v",
                "1",
                str(path),
                "-loglevel",
                "error",
            ],
            check=True,
        )

    def create_video(
        self, path: Path, size: str, fps: int, duration: float
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c=blue:s={size}:r={fps}:d={duration}",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                str(path),
                "-loglevel",
                "error",
            ],
            check=True,
        )

    def test_high_quality_fixture_passes_script_gate(self) -> None:
        result = self.result()
        self.assertTrue(result.ok, result.errors)
        self.assertGreaterEqual(result.metrics["duration_seconds"], 285)
        self.assertGreaterEqual(result.metrics["distinct_voices"], 4)
        self.assertGreaterEqual(result.metrics["vfx_ratio"], 0.25)
        self.assertGreaterEqual(result.metrics["sfx_ratio"], 0.70)

    def test_portuguese_from_portugal_is_rejected(self) -> None:
        self.write_characters(hero_locale="pt-PT")
        result = self.result()
        self.assertFalse(result.ok)
        self.assertTrue(
            any("locale 'pt-PT' inválido" in error for error in result.errors)
        )

    def test_unapproved_voice_blocks_audio_generation(self) -> None:
        self.write_characters(approved="no")
        result = self.result("audio")
        self.assertFalse(result.ok)
        self.assertTrue(
            any("ainda não foi aprovada" in error for error in result.errors)
        )

    def test_two_roles_cannot_reuse_the_same_voice(self) -> None:
        self.write_characters(
            hero_voice_id="11111111-1111-4111-8111-111111111111"
        )
        result = self.result()
        self.assertFalse(result.ok)
        self.assertTrue(
            any("usam o mesmo voice_id" in error for error in result.errors)
        )

    def test_editorial_policy_cannot_be_weakened_in_meta(self) -> None:
        path = self.episode / "meta.env"
        content = path.read_text(encoding="utf-8").replace(
            "MIN_VOICES=4", "MIN_VOICES=1"
        )
        path.write_text(content, encoding="utf-8")
        result = self.result()
        self.assertFalse(result.ok)
        self.assertTrue(
            any("política fixa MIN_VOICES=4" in error for error in result.errors)
        )

    def test_english_script_is_rejected_even_when_locale_label_says_pt_br(self) -> None:
        path = self.episode / "scenes.tsv"
        content = path.read_text(encoding="utf-8")
        portuguese = (
            "Quando o povo ouviu a voz de Deus ele abriu o coração e caminhou "
            "com fé para um novo começo"
        )
        english = (
            "When the people heard the voice of God they opened the heart and "
            "walked with faith to a new beginning"
        )
        path.write_text(content.replace(portuguese, english), encoding="utf-8")
        result = self.result()
        self.assertFalse(result.ok)
        self.assertTrue(
            any("parece estar em inglês" in error for error in result.errors)
        )

    def test_single_mixed_english_scene_is_rejected(self) -> None:
        self.replace_scene_text(
            0, "Hello children, God loves every one of you today"
        )
        result = self.result()
        self.assertFalse(result.ok)
        self.assertTrue(
            any("parece estar em inglês" in error for error in result.errors)
        )

    def test_single_spanish_scene_is_rejected(self) -> None:
        self.replace_scene_text(
            0, "Hola niños, Dios ama a cada uno de ustedes"
        )
        result = self.result()
        self.assertFalse(result.ok)
        self.assertTrue(
            any("parece estar em espanhol" in error for error in result.errors)
        )

    def test_english_content_words_without_stopwords_are_rejected(self) -> None:
        self.replace_scene_text(
            0,
            "Tomorrow brave sailors discover mysterious islands beyond distant horizons",
        )
        result = self.result()
        self.assertFalse(result.ok)
        self.assertTrue(
            any("parece estar em inglês" in error for error in result.errors)
        )

    def test_shared_spanish_words_do_not_reject_portuguese(self) -> None:
        self.replace_scene_text(
            0,
            "Cada criança está pronta para caminhar com coragem e esperança",
        )
        result = self.result()
        self.assertTrue(
            not any("espanhol" in error for error in result.errors),
            result.errors,
        )

    def test_ambiguous_short_language_requires_explicit_human_confirmation(self) -> None:
        self.replace_scene_text(
            0, "Brave sailors discover mysterious islands"
        )
        episode = pipeline.load_episode(self.episode)
        result = pipeline.validate_episode(episode)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.metrics["ambiguous_language_lines"], ["2"])
        (self.episode / "roteiro.md").write_text(
            pipeline.render_script(episode, result), encoding="utf-8"
        )
        with self.assertRaisesRegex(pipeline.PipelineError, "idioma ambíguo"):
            pipeline.approve_script(episode)
        pipeline.approve_script(episode, confirm_ambiguous_pt_br=True)
        pipeline.verify_script_approval(episode)

    def test_portuguese_content_sentence_is_not_marked_ambiguous(self) -> None:
        self.replace_scene_text(
            0, "Pedro viu Jonas correr pelo barco sob forte chuva"
        )
        result = self.result()
        self.assertNotIn("2", result.metrics["ambiguous_language_lines"])

    def test_slug_cannot_escape_episode_directory(self) -> None:
        path = self.episode / "meta.env"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                'SLUG="episodio-teste"', 'SLUG="../episodio-antigo"'
            ),
            encoding="utf-8",
        )
        result = self.result()
        self.assertFalse(result.ok)
        self.assertTrue(any("SLUG deve conter" in error for error in result.errors))

    def test_empty_environment_variable_uses_colon_dash_default(self) -> None:
        with mock.patch.dict(os.environ, {"GEN_PROVIDER": ""}):
            meta = pipeline.load_meta(self.episode / "meta.env")
        self.assertEqual(meta["GEN_PROVIDER"], "openart")

    def test_empty_reference_item_is_rejected_before_shell_parsing(self) -> None:
        path = self.episode / "scenes.tsv"
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle, delimiter="\t"))
        rows[1][3] = ","
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle, delimiter="\t", lineterminator="\n").writerows(rows)
        with self.assertRaisesRegex(pipeline.PipelineError, "item vazio"):
            pipeline.load_episode(self.episode)

    def test_voice_approval_is_bound_to_exact_voice_id_and_sample(self) -> None:
        episode = self.create_voice_sample("hero")
        pipeline.approve_voice(episode, "hero")
        approved_episode = pipeline.load_episode(self.episode)
        pipeline.verify_voice_approval(
            approved_episode, "hero", approved_episode.cast["hero"]
        )

        self.write_characters(
            hero_voice_id="55555555-5555-4555-8555-555555555555"
        )
        changed_episode = pipeline.load_episode(self.episode)
        with self.assertRaises(pipeline.PipelineError):
            pipeline.verify_voice_approval(
                changed_episode, "hero", changed_episode.cast["hero"]
            )

    def test_corrupt_voice_approval_manifest_fails_closed(self) -> None:
        episode = self.create_voice_sample("hero")
        path = pipeline.approvals_path(episode)
        path.write_text("{corrompido", encoding="utf-8")
        with self.assertRaises(pipeline.PipelineError):
            pipeline.approve_voice(episode, "hero")
        self.assertEqual(path.read_text(encoding="utf-8"), "{corrompido")

    def test_script_approval_is_bound_to_rendered_document(self) -> None:
        episode = pipeline.load_episode(self.episode)
        result = pipeline.validate_episode(episode)
        roteiro = self.episode / "roteiro.md"
        roteiro.write_text(
            pipeline.render_script(episode, result), encoding="utf-8"
        )
        pipeline.approve_script(episode)
        pipeline.verify_script_approval(episode)
        roteiro.write_text(
            roteiro.read_text(encoding="utf-8") + "\nTexto alterado.\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(pipeline.PipelineError, "mudou"):
            pipeline.verify_script_approval(episode)

    def test_malformed_script_approval_is_reported_without_crash(self) -> None:
        episode = pipeline.load_episode(self.episode)
        path = pipeline.script_approval_path(episode)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(["estrutura", "inválida"]), encoding="utf-8")
        with self.assertRaises(pipeline.PipelineError):
            pipeline.verify_script_approval(episode)

    def test_low_resolution_visual_media_is_rejected(self) -> None:
        path = self.episode / "frames" / "01.png"
        self.create_image(path, "320x180")
        with self.assertRaisesRegex(pipeline.PipelineError, "baixa resolução"):
            pipeline.validate_visual_media(path, "frame")

    def test_video_renamed_as_frame_is_rejected(self) -> None:
        source = self.episode / "build" / "fake-frame.mp4"
        self.create_video(source, "1920x1080", 24, 0.2)
        frame = self.episode / "frames" / "01.png"
        frame.parent.mkdir(parents=True, exist_ok=True)
        source.replace(frame)
        with self.assertRaisesRegex(pipeline.PipelineError, "imagem estática"):
            pipeline.validate_visual_media(frame, "frame")

    def test_one_fps_clip_is_rejected(self) -> None:
        clip = self.episode / "clips" / "01.mp4"
        self.create_video(clip, "1920x1080", 1, 10)
        with self.assertRaisesRegex(pipeline.PipelineError, "cadência inadequada"):
            pipeline.validate_visual_media(clip, "clip")

    def test_master_session_fingerprint_is_read_from_mp4_metadata(self) -> None:
        source = self.episode / "build" / "source.mp4"
        tagged = self.episode / "build" / "tagged.mp4"
        self.create_video(source, "320x180", 24, 0.2)
        fingerprint = "a" * 64
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(source),
                "-c",
                "copy",
                "-metadata",
                f"comment=geflix-session:{fingerprint}",
                str(tagged),
                "-loglevel",
                "error",
            ],
            check=True,
        )
        self.assertEqual(
            pipeline.master_session_fingerprint(pipeline.ffprobe_info(tagged)),
            fingerprint,
        )

    def test_assembly_session_detects_stem_changed_during_render(self) -> None:
        episode = pipeline.load_episode(self.episode)
        build = self.episode / "build"
        build.mkdir(parents=True, exist_ok=True)
        timeline = build / "timeline.tsv"
        per_scene = 300 / len(episode.scenes)
        with timeline.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(["scene", "seconds", "voice", "transition"])
            for scene in episode.scenes:
                writer.writerow(
                    [scene["id"], f"{per_scene:.12f}", scene["voice"], "cut"]
                )
        video = build / "video-only.mp4"
        audio = build / "master-audio.wav"
        video.write_bytes(b"video-stem")
        audio.write_bytes(b"audio-stem")
        lock_path = build / "source-lock.json"
        session_path = build / "assembly-session.json"
        output = self.episode / ".episodio-teste_final.123.mp4"
        validation = pipeline.ValidationResult(
            errors=[], warnings=[], metrics={"duration_seconds": 300.0}
        )
        with (
            mock.patch.object(pipeline, "validate_episode", return_value=validation),
            mock.patch.object(pipeline, "stream_duration", return_value=300.0),
            mock.patch.object(
                pipeline, "_master_inputs_fingerprint", return_value="inputs"
            ),
        ):
            pipeline.create_assembly_lock(episode, lock_path)
            pipeline.create_assembly_session(
                episode,
                lock_path,
                session_path,
                timeline,
                video,
                audio,
                output,
            )
            pipeline.verify_assembly_session(episode, session_path, output)
            video.write_bytes(b"video-stem-alterado")
            with self.assertRaisesRegex(pipeline.PipelineError, "mudou"):
                pipeline.verify_assembly_session(episode, session_path, output)

    def test_assembly_lock_detects_source_changed_before_stems_finish(self) -> None:
        episode = pipeline.load_episode(self.episode)
        build = self.episode / "build"
        build.mkdir(parents=True, exist_ok=True)
        lock_path = build / "source-lock.json"
        validation = pipeline.ValidationResult(
            errors=[], warnings=[], metrics={"duration_seconds": 300.0}
        )
        with (
            mock.patch.object(pipeline, "validate_episode", return_value=validation),
            mock.patch.object(
                pipeline, "_master_inputs_fingerprint", return_value="antes"
            ),
        ):
            pipeline.create_assembly_lock(episode, lock_path)
        with (
            mock.patch.object(pipeline, "validate_episode", return_value=validation),
            mock.patch.object(
                pipeline, "_master_inputs_fingerprint", return_value="depois"
            ),
        ):
            with self.assertRaisesRegex(pipeline.PipelineError, "mudaram"):
                pipeline.verify_assembly_lock(episode, lock_path)

    def test_master_commit_replaces_output_only_after_recording(self) -> None:
        episode = pipeline.load_episode(self.episode)
        source = self.episode / ".episodio-teste_final.123.mp4"
        destination = self.episode / "episodio-teste_final.mp4"
        source.write_bytes(b"novo-master")
        destination.write_bytes(b"master-anterior")
        record_cache(source, "episode-master", {"session": "ok"}, [])
        approved = pipeline.ValidationResult(
            errors=[], warnings=[], metrics={"duration_seconds": 300.0}
        )
        with mock.patch.object(pipeline, "validate_master", return_value=approved):
            pipeline.commit_master_artifact(episode, source, destination)
        self.assertEqual(destination.read_bytes(), b"novo-master")
        self.assertFalse(source.exists())
        self.assertTrue(pipeline.metadata_path(destination).exists())

    def test_short_valid_clip_cannot_hide_excessive_stretch(self) -> None:
        episode = pipeline.load_episode(self.episode)
        scene = episode.scenes[0]
        scene["text"] = " ".join(["coragem"] * 24)
        with self.assertRaisesRegex(pipeline.PipelineError, "excede stretch"):
            pipeline.validate_clip_story_capacity(episode, "01", 9.4)

    def test_clip_approval_prefers_real_audio_duration_when_available(self) -> None:
        episode = pipeline.load_episode(self.episode)
        audio = self.episode / "audio" / "01.mp3"
        audio.parent.mkdir(parents=True, exist_ok=True)
        audio.write_bytes(b"audio-presente")
        with mock.patch.object(
            pipeline, "actual_scene_seconds", return_value=11.0
        ):
            with self.assertRaisesRegex(pipeline.PipelineError, "beat real"):
                pipeline.validate_clip_story_capacity(episode, "01", 9.4)

    def test_visual_approval_is_bound_to_exact_reference(self) -> None:
        episode = pipeline.load_episode(self.episode)
        path, kind, values, dependencies = pipeline.visual_artifact_contract(
            episode, "reference", "hero"
        )
        self.create_image(path, "1440x1920", "blue")
        record_cache(path, kind, values, dependencies)
        pipeline.approve_visual(episode, "reference", "hero")
        pipeline.verify_visual_approval(episode, "reference", "hero")

        self.create_image(path, "1440x1920", "red")
        with self.assertRaises(pipeline.PipelineError):
            pipeline.verify_visual_approval(episode, "reference", "hero")

    def test_external_music_approval_is_bound_to_exact_audio(self) -> None:
        episode = pipeline.load_episode(self.episode)
        bgm = self.episode / "audio" / "bgm.mp3"
        bgm.parent.mkdir(parents=True, exist_ok=True)
        for frequency in (220, 330):
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"sine=frequency={frequency}:duration=2",
                    "-c:a",
                    "libmp3lame",
                    str(bgm),
                    "-loglevel",
                    "error",
                ],
                check=True,
            )
            if frequency == 220:
                pipeline.approve_music(episode)
                pipeline.verify_music_approval(episode)
        with self.assertRaisesRegex(pipeline.PipelineError, "mudou"):
            pipeline.verify_music_approval(episode)

    def test_generated_music_with_old_prompt_cannot_be_approved(self) -> None:
        episode = pipeline.load_episode(self.episode)
        bgm = self.episode / "audio" / "bgm.mp3"
        bgm.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=220:duration=2",
                "-c:a",
                "libmp3lame",
                str(bgm),
                "-loglevel",
                "error",
            ],
            check=True,
        )
        old_values = pipeline.music_values("old score prompt", 300)
        record_cache(
            bgm,
            f"elevenlabs-audio:{pipeline.MUSIC_JOB_TYPE}",
            old_values,
            [],
        )
        current_values = pipeline.music_values("new score prompt", 300)
        with mock.patch.object(
            pipeline, "expected_music_values", return_value=current_values
        ):
            with self.assertRaisesRegex(pipeline.PipelineError, "Entradas mudaram"):
                pipeline.approve_music(episode)

    def test_last_scene_without_trailing_newline_is_not_lost(self) -> None:
        path = self.episode / "scenes.tsv"
        path.write_text(path.read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8")
        episode = pipeline.load_episode(self.episode)
        self.assertEqual(len(episode.scenes), 34)
        self.assertEqual(episode.scenes[-1]["id"], "34")

    def test_reference_whitespace_is_normalized_once(self) -> None:
        path = self.episode / "scenes.tsv"
        content = path.read_text(encoding="utf-8").replace(
            "\thero\tnarrator\t", "\thero, captain\tnarrator\t", 1
        )
        path.write_text(content, encoding="utf-8")
        episode = pipeline.load_episode(self.episode)
        self.assertEqual(episode.scenes[0]["refs"], "hero,captain")

    def test_long_voiceover_beat_must_be_split(self) -> None:
        self.write_scenes(long_first_beat=True)
        result = self.result()
        self.assertFalse(result.ok)
        self.assertTrue(
            any("Divida a fala em mais planos" in error for error in result.errors)
        )

    def test_rendered_script_surfaces_brazilian_language_gate(self) -> None:
        episode = pipeline.load_episode(self.episode)
        result = pipeline.validate_episode(episode)
        document = pipeline.render_script(episode, result)
        self.assertIn("português brasileiro", document)
        self.assertIn("sem sotaque de Portugal", document)


if __name__ == "__main__":
    unittest.main()
