#!/usr/bin/env python3
"""Quality gates and production documents for Geração Eleita Flix episodes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import secrets
import shlex
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from artifact_cache import (
    CacheError,
    cache_valid,
    fingerprint_payload,
    metadata_path,
    record_cache,
    sha256_file,
    verify_recorded_output,
)
from audio_contract import (
    MUSIC_JOB_TYPE,
    NARRATION_TTS_MODEL,
    SFX_JOB_TYPE,
    TTS_JOB_TYPE,
    VOICE_TEST_TEXT,
    music_values,
    narration_tts_values,
    sfx_values,
    tts_values,
)


CHARACTER_FIELDS = [
    "key",
    "name",
    "voice_id",
    "locale",
    "voice_approved",
    "sheet_prompt",
]

SCENE_FIELDS = [
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

ALLOWED_TRANSITIONS = {
    "cut",
    "match-cut",
    "smash-cut",
    "whip-pan",
    "dip-to-black",
    "light-flash",
    "water-wipe",
}

PIPELINE_VERSION = "2.2"

POLICY_STRINGS = {
    "LANGUAGE": "pt-BR",
    "ASPECT": "16:9",
    "IMG_RES": "2k",
    "REF_ASPECT": "3:4",
    "VIDEO_RES": "1080p",
}

POLICY_INTEGERS = {
    "TARGET_DURATION": 300,
    "MIN_DURATION": 285,
    "MAX_DURATION": 315,
    "WORDS_PER_MINUTE": 138,
    "MIN_SCENES": 34,
    "MAX_SCENES": 46,
    "MIN_VOICES": 4,
    "MIN_ACTS": 6,
    "MIN_SHOT_VARIETY": 8,
    "MIN_IMAGE_PROMPT_CHARS": 100,
    "MIN_MOTION_PROMPT_CHARS": 60,
    "VIDEO_DUR": 10,
    "FPS": 24,
}

POLICY_FLOATS = {
    "MIN_BEAT_SECONDS": 2.0,
    "MAX_BEAT_SECONDS": 11.2,
    "MIN_DIALOGUE_RATIO": 0.25,
    "MIN_VFX_RATIO": 0.25,
    "MIN_SFX_RATIO": 0.70,
    "MAX_STRETCH": 1.12,
}

REQUIRED_RUNTIME_META = {
    "TITLE",
    "SLUG",
    "STYLE",
    "IMAGE_QUALITY",
    "IMAGE_NEGATIVE",
    "MOTION_QUALITY",
    "GEN_PROVIDER",
    "BGMVOL",
    "SFXVOL",
    "MASTER_LIMIT",
    "SCORE_PROMPT",
}

PROVIDER_META_KEYS = {
    "OPENART_MCP_SERVER",
    "OPENART_PROJECT_ID",
    "OPENART_IMAGE_MODEL",
    "OPENART_VIDEO_MODEL",
    "OPENART_CONCURRENCY",
    "KIE_IMAGE_MODEL",
    "KIE_VIDEO_MODEL",
    "KIE_VIDEO_MODE",
    "KIE_USAGE_LOG",
    "VIDEO_MODEL",
}

ALLOWED_META_KEYS = (
    set(POLICY_STRINGS)
    | set(POLICY_INTEGERS)
    | set(POLICY_FLOATS)
    | REQUIRED_RUNTIME_META
    | PROVIDER_META_KEYS
)

REFERENCE_DIRECTION = (
    "ONE single character only, solo full-body production reference, relaxed "
    "neutral A-pose, facing camera with a slight three-quarter turn, both hands "
    "and both feet fully visible, precise face wardrobe color palette materials "
    "age and proportions, clean seamless warm-gray studio background, soft "
    "three-point studio lighting, no props unless identity-critical, no extra "
    "people, no multiple poses, no turnaround grid, no labels"
)

DIVINE_VISUAL_POLICY = (
    "GOD VISUAL POLICY (mandatory): never depict God as a person, humanoid, "
    "face, body, hand, shadow, silhouette, statue or figure in the clouds. "
    "When God's presence is visually implied, show only soft warm golden-white "
    "light, volumetric rays, luminous atmosphere, wind or environmental reaction"
)

BIBLICAL_WORLD_POLICY = (
    "BIBLICAL WORLD LOCK (mandatory): use only the subjects, period and objects "
    "explicitly requested by the scene. Never add modern clothing, explorers, "
    "tourists, astronauts, spacecraft, phones, cameras, technology, science-fiction "
    "props or unrelated fantasy heroes"
)

PORTUGUESE_MARKERS = {
    "a",
    "ao",
    "aos",
    "as",
    "cada",
    "cê",
    "com",
    "criança",
    "crianças",
    "da",
    "das",
    "de",
    "deus",
    "do",
    "dos",
    "e",
    "ele",
    "ela",
    "em",
    "então",
    "era",
    "estava",
    "está",
    "foi",
    "mas",
    "na",
    "não",
    "nas",
    "no",
    "nos",
    "nós",
    "o",
    "os",
    "para",
    "pela",
    "pelas",
    "pelo",
    "pelos",
    "por",
    "que",
    "quando",
    "se",
    "seu",
    "sim",
    "sob",
    "sua",
    "um",
    "uma",
    "você",
    "vocês",
    "viu",
}

PORTUGUESE_SUFFIXES = (
    "ções",
    "ção",
    "dade",
    "eiro",
    "eiros",
    "eira",
    "eiras",
    "mente",
    "nhas",
    "nhos",
)

ENGLISH_MARKERS = {
    "and",
    "are",
    "at",
    "but",
    "for",
    "from",
    "god",
    "he",
    "her",
    "his",
    "in",
    "is",
    "of",
    "on",
    "she",
    "that",
    "the",
    "then",
    "they",
    "to",
    "was",
    "when",
    "with",
    "you",
}

ENGLISH_STRONG_MARKERS = {
    "children",
    "everyone",
    "every",
    "hello",
    "loves",
    "lord",
    "please",
    "thank",
    "today",
    "tomorrow",
    "we",
    "will",
    "your",
}

SPANISH_MARKERS = {
    "ahora",
    "con",
    "dios",
    "el",
    "ella",
    "ellos",
    "en",
    "es",
    "hola",
    "la",
    "las",
    "los",
    "niños",
    "para",
    "pero",
    "por",
    "que",
    "señor",
    "una",
    "uno",
    "ustedes",
    "y",
}

SPANISH_STRONG_MARKERS = {
    "ahora",
    "dios",
    "ellos",
    "hola",
    "niños",
    "señor",
    "ustedes",
}

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
VOICE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,64}$")
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
ENV_DEFAULT_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*):-([^}]*)\}")
WORD_RE = re.compile(r"\b[\wÀ-ÿ'-]+\b", re.UNICODE)


class PipelineError(RuntimeError):
    """Raised when an episode file cannot be parsed."""


@dataclass
class Episode:
    root: Path
    meta: dict[str, str]
    characters: list[dict[str, str]]
    scenes: list[dict[str, str]]

    @property
    def cast(self) -> dict[str, dict[str, str]]:
        return {row["key"]: row for row in self.characters}


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]
    metrics: dict[str, Any]

    @property
    def ok(self) -> bool:
        return not self.errors


def _expand_env_defaults(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name, default = match.groups()
        return os.environ.get(name) or default

    return ENV_DEFAULT_RE.sub(replace, value)


def load_meta(path: Path) -> dict[str, str]:
    if not path.exists():
        raise PipelineError(f"Arquivo ausente: {path}")

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise PipelineError(f"{path}:{line_number}: configuração sem '='")

        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise PipelineError(f"{path}:{line_number}: chave inválida '{key}'")

        try:
            parsed = shlex.split(raw_value, comments=True, posix=True)
        except ValueError as exc:
            raise PipelineError(f"{path}:{line_number}: {exc}") from exc

        value = " ".join(parsed) if parsed else ""
        values[key] = _expand_env_defaults(value)

    unknown = sorted(set(values) - ALLOWED_META_KEYS)
    if unknown:
        raise PipelineError(
            f"{path}: chaves não permitidas: {', '.join(unknown)}"
        )
    return values


def read_tsv(path: Path, expected_fields: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise PipelineError(f"Arquivo ausente: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        actual = reader.fieldnames or []
        if actual != expected_fields:
            raise PipelineError(
                f"{path}: cabeçalho inválido.\n"
                f"  esperado: {' | '.join(expected_fields)}\n"
                f"  recebido: {' | '.join(actual)}"
            )

        rows: list[dict[str, str]] = []
        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise PipelineError(
                    f"{path}:{line_number}: colunas extras; evite TAB dentro dos campos"
                )
            normalized = {
                field: (row.get(field) or "").strip() for field in expected_fields
            }
            for field, value in normalized.items():
                if "\t" in value or "\n" in value or "\r" in value:
                    raise PipelineError(
                        f"{path}:{line_number}: '{field}' contém TAB/quebra de linha; "
                        "cada cena precisa ocupar uma única linha física"
                    )
            if not any(normalized.values()) or normalized[expected_fields[0]].startswith("#"):
                continue
            for field, value in normalized.items():
                if value == "":
                    raise PipelineError(
                        f"{path}:{line_number}: campo '{field}' vazio; "
                        "use '-' explicitamente quando não houver conteúdo"
                    )
            normalized["_line"] = str(line_number)
            rows.append(normalized)
    return rows


def load_episode(root: Path) -> Episode:
    root = root.expanduser().resolve()
    episode = Episode(
        root=root,
        meta=load_meta(root / "meta.env"),
        characters=read_tsv(root / "characters.tsv", CHARACTER_FIELDS),
        scenes=read_tsv(root / "scenes.tsv", SCENE_FIELDS),
    )
    for scene in episode.scenes:
        if scene["refs"] != "-":
            raw_refs = scene["refs"].split(",")
            refs = [value.strip() for value in raw_refs]
            if any(not value for value in refs):
                raise PipelineError(
                    f"{root / 'scenes.tsv'}:{scene['_line']}: refs contém "
                    "item vazio; use '-' quando não houver referência"
                )
            if len(refs) != len(set(refs)):
                raise PipelineError(
                    f"{root / 'scenes.tsv'}:{scene['_line']}: refs contém "
                    "personagem duplicado"
                )
            scene["refs"] = ",".join(refs)
    return episode


def meta_float(meta: dict[str, str], key: str, default: float) -> float:
    raw = meta.get(key, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise PipelineError(f"meta.env: {key} precisa ser número; recebido '{raw}'") from exc
    if not math.isfinite(value):
        raise PipelineError(f"meta.env: {key} precisa ser finito; recebido '{raw}'")
    return value


def meta_int(meta: dict[str, str], key: str, default: int) -> int:
    raw = meta.get(key, str(default))
    try:
        return int(raw)
    except ValueError as exc:
        raise PipelineError(f"meta.env: {key} precisa ser inteiro; recebido '{raw}'") from exc


def validate_policy_meta(meta: dict[str, str], errors: list[str]) -> None:
    required = (
        set(POLICY_STRINGS)
        | set(POLICY_INTEGERS)
        | set(POLICY_FLOATS)
        | REQUIRED_RUNTIME_META
    )
    for key in sorted(required):
        if not meta.get(key):
            errors.append(f"meta.env: configuração obrigatória ausente: {key}")

    for key, expected in POLICY_STRINGS.items():
        if meta.get(key) != expected:
            errors.append(
                f"meta.env: política fixa {key}={expected}; "
                f"recebido '{meta.get(key, '')}'"
            )

    for key, expected in POLICY_INTEGERS.items():
        if meta_int(meta, key, expected) != expected:
            errors.append(
                f"meta.env: política fixa {key}={expected}; "
                f"recebido '{meta.get(key, '')}'"
            )

    for key, expected in POLICY_FLOATS.items():
        if not math.isclose(
            meta_float(meta, key, expected), expected, rel_tol=0, abs_tol=1e-9
        ):
            errors.append(
                f"meta.env: política fixa {key}={expected}; "
                f"recebido '{meta.get(key, '')}'"
            )

    provider = meta.get("GEN_PROVIDER")
    provider_requirements = {
        "openart": {
            "OPENART_MCP_SERVER",
            "OPENART_PROJECT_ID",
            "OPENART_IMAGE_MODEL",
            "OPENART_VIDEO_MODEL",
            "OPENART_CONCURRENCY",
        },
        "higgsfield": {"VIDEO_MODEL"},
        "kie": {
            "KIE_IMAGE_MODEL",
            "KIE_VIDEO_MODEL",
            "KIE_VIDEO_MODE",
            "KIE_USAGE_LOG",
        },
    }
    if provider not in provider_requirements:
        errors.append(
            "meta.env: GEN_PROVIDER deve ser 'openart' "
            "(ou 'higgsfield'/'kie' somente para episódios legados)"
        )
    else:
        for key in sorted(provider_requirements[provider]):
            if not meta.get(key):
                errors.append(
                    f"meta.env: configuração obrigatória para {provider}: {key}"
                )
    if provider == "openart" and meta.get("OPENART_CONCURRENCY"):
        concurrency = meta_int(meta, "OPENART_CONCURRENCY", 8)
        if not 1 <= concurrency <= 16:
            errors.append(
                "meta.env: OPENART_CONCURRENCY deve ficar entre 1 e 16"
            )
    if provider == "kie" and meta.get("KIE_VIDEO_MODE") != "pro":
        errors.append(
            "meta.env: episódios Kie legados exigem KIE_VIDEO_MODE=pro"
        )
    slug = meta.get("SLUG", "")
    if not SLUG_RE.fullmatch(slug):
        errors.append(
            "meta.env: SLUG deve conter apenas letras minúsculas, números e "
            "hífens, sem começar ou terminar com hífen"
        )

    for key, lower, upper in (
        ("BGMVOL", 0.0, 0.35),
        ("SFXVOL", 0.0, 0.65),
        ("MASTER_LIMIT", 0.8, 1.0),
    ):
        value = meta_float(meta, key, -1)
        if not lower <= value <= upper:
            errors.append(
                f"meta.env: {key}={value} fora da faixa segura {lower}–{upper}"
            )


def word_count(text: str) -> int:
    if not text or text == "-":
        return 0
    return len(WORD_RE.findall(text))


def validate_portuguese_text(
    scenes: list[dict[str, str]], errors: list[str], warnings: list[str]
) -> list[str]:
    all_tokens: list[str] = []
    ambiguous_lines: list[str] = []
    english_tokens = ENGLISH_MARKERS | ENGLISH_STRONG_MARKERS
    for scene in scenes:
        if scene["text"] == "-":
            continue
        tokens = [token.casefold() for token in WORD_RE.findall(scene["text"])]
        all_tokens.extend(tokens)
        pt_hits = sum(token in PORTUGUESE_MARKERS for token in tokens)
        pt_morphology = sum(
            token.endswith(PORTUGUESE_SUFFIXES) for token in tokens
        )
        pt_diacritics = sum(
            any(character in token for character in "ãõçêôáéíóúà")
            for token in tokens
        )
        pt_evidence = pt_hits + pt_morphology + pt_diacritics
        en_hits = sum(token in english_tokens for token in tokens)
        en_strong = sum(token in ENGLISH_STRONG_MARKERS for token in tokens)
        es_hits = sum(token in SPANISH_MARKERS for token in tokens)
        es_strong = sum(token in SPANISH_STRONG_MARKERS for token in tokens)
        english_detected = (
            (len(tokens) <= 3 and en_strong >= 1)
            or (en_strong >= 1 and pt_evidence < 2)
            or (
                len(tokens) >= 4
                and en_hits >= 2
                and en_hits > max(pt_hits * 1.5, 1)
            )
        )
        spanish_detected = (
            (len(tokens) <= 3 and es_strong >= 1)
            or (es_strong >= 1 and pt_evidence < 2)
            or (
                len(tokens) >= 4
                and es_strong >= 1
                and es_hits >= 2
                and es_hits > max(pt_hits * 1.5, 1)
            )
        )
        language_unknown = len(tokens) >= 4 and pt_evidence < 2
        if english_detected:
            errors.append(
                f"scenes.tsv:{scene['_line']}: texto parece estar em inglês; "
                "toda fala deve ser português brasileiro"
            )
        if spanish_detected:
            errors.append(
                f"scenes.tsv:{scene['_line']}: texto parece estar em espanhol; "
                "toda fala deve ser português brasileiro"
            )
        if language_unknown and not english_detected and not spanish_detected:
            ambiguous_lines.append(scene["_line"])
            warnings.append(
                f"scenes.tsv:{scene['_line']}: idioma ambíguo; exige confirmação "
                "humana explícita de português brasileiro"
            )

    if not all_tokens:
        return ambiguous_lines
    pt_hits = sum(token in PORTUGUESE_MARKERS for token in all_tokens)
    en_hits = sum(token in english_tokens for token in all_tokens)
    pt_ratio = pt_hits / len(all_tokens)
    if (
        pt_hits < 10
        or pt_ratio < 0.08
        or en_hits > pt_hits
    ):
        errors.append(
            "O conjunto das falas não apresenta sinais suficientes de português "
            "brasileiro; revise o conteúdo de text em scenes.tsv"
        )
    return ambiguous_lines


def reference_prompt(episode: Episode, character: dict[str, str]) -> str:
    return (
        f"{character['sheet_prompt']}. {REFERENCE_DIRECTION}. "
        f"{episode.meta.get('STYLE', '')}. {episode.meta.get('IMAGE_QUALITY', '')}. "
        f"Negative constraints: {episode.meta.get('IMAGE_NEGATIVE', '')}"
    )


def environment_safe_style(style: str) -> str:
    """Remove character-oriented style cues from shots with no character refs."""
    cleaned = re.sub(
        r"\bexpressive\s+(?:appealing\s+)?characters\b,?\s*",
        "",
        style,
        flags=re.IGNORECASE,
    )
    return cleaned.strip(" ,")


def frame_subject_policy(episode: Episode, scene: dict[str, str]) -> str:
    if scene["refs"] == "-":
        return (
            "ENVIRONMENT-ONLY FRAME (hard constraint): there are zero people and "
            "zero humanoid characters in this image. No child, adult, observer, "
            "traveler, adventurer, astronaut, silhouette, human statue, human face "
            "or human body part may appear. Do not anthropomorphize animals, clouds, "
            "light, stars or landscapes. Animals are allowed only when the scene "
            "explicitly requests them"
        )

    keys = scene["refs"].split(",")
    names = [
        episode.cast[key]["name"] if key in episode.cast else key
        for key in keys
    ]
    return (
        "CHARACTER CAST LOCK (hard constraint): the only human or humanoid "
        f"subjects allowed are the supplied references for {', '.join(names)}. "
        "Show every requested referenced character exactly once, preserving the "
        "exact face, age, body proportions, skin tone, hair, costume and colors. "
        "Do not invent extras, crowds, children, relatives, observers or any "
        "unreferenced character"
    )


def frame_prompt(episode: Episode, scene: dict[str, str]) -> str:
    vfx_direction = (
        f"Practical and magical VFX visible in-frame: {scene['vfx']}."
        if scene["vfx"] != "-"
        else ""
    )
    style = episode.meta.get("STYLE", "")
    if scene["refs"] == "-":
        style = environment_safe_style(style)
    return (
        f"{frame_subject_policy(episode, scene)}. {DIVINE_VISUAL_POLICY}. "
        f"{BIBLICAL_WORLD_POLICY}. The following scene description is exhaustive; "
        "do not invent additional story subjects or props. "
        f"Story beat: {scene['act']}. Camera and lens: {scene['shot']}. "
        f"Required scene content: {scene['image_prompt']}. {vfx_direction} "
        f"{style}. "
        f"{episode.meta.get('IMAGE_QUALITY', '')}. Negative constraints: "
        f"{episode.meta.get('IMAGE_NEGATIVE', '')}"
    )


def clip_prompt(episode: Episode, scene: dict[str, str]) -> str:
    performance_direction = ""
    if scene["voice"] not in {"-", "narrator", "deus"}:
        performance_direction = (
            "The speaking character gives a natural facial performance with "
            "restrained mouth movement and expressive eyes; generate no audio."
        )
    vfx_direction = (
        f"Layered cinematic VFX: {scene['vfx']}."
        if scene["vfx"] != "-"
        else ""
    )
    transition_direction = (
        "End with a composition that supports a clean "
        f"{scene['transition']} into the next shot; do not insert an edit "
        "inside this clip."
    )
    return (
        f"{scene['motion_prompt']}. {performance_direction} {vfx_direction} "
        f"{transition_direction} {episode.meta.get('MOTION_QUALITY', '')}. "
        f"Visual finish: {episode.meta.get('STYLE', '')}"
    )


def configured_image_model(episode: Episode) -> str:
    provider = episode.meta.get("GEN_PROVIDER")
    if provider == "openart":
        return episode.meta.get("OPENART_IMAGE_MODEL", "")
    if provider == "kie":
        return episode.meta.get("KIE_IMAGE_MODEL", "")
    return "nano_banana_2"


def configured_video_model(episode: Episode) -> str:
    provider = episode.meta.get("GEN_PROVIDER")
    if provider == "openart":
        return episode.meta.get("OPENART_VIDEO_MODEL", "")
    if provider == "kie":
        return episode.meta.get("KIE_VIDEO_MODEL", "")
    return episode.meta.get("VIDEO_MODEL", "")


def reference_source_signature(
    episode: Episode, character: dict[str, str]
) -> str:
    payload = {
        "pipeline_version": PIPELINE_VERSION,
        "key": character["key"],
        "prompt": reference_prompt(episode, character),
        "provider": episode.meta.get("GEN_PROVIDER", ""),
        "model": configured_image_model(episode),
        "aspect": episode.meta.get("REF_ASPECT", ""),
        "resolution": episode.meta.get("IMG_RES", ""),
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def media_source_signature(
    episode: Episode, scene: dict[str, str], media: str
) -> str:
    if media == "frame":
        payload = {
            "pipeline_version": PIPELINE_VERSION,
            "scene_id": scene["id"],
            "refs": scene["refs"],
            "prompt": frame_prompt(episode, scene),
            "provider": episode.meta.get("GEN_PROVIDER", ""),
            "model": configured_image_model(episode),
            "aspect": episode.meta.get("ASPECT", ""),
            "resolution": episode.meta.get("IMG_RES", ""),
        }
    elif media == "clip":
        payload = {
            "pipeline_version": PIPELINE_VERSION,
            "scene_id": scene["id"],
            "prompt": clip_prompt(episode, scene),
            "provider": episode.meta.get("GEN_PROVIDER", ""),
            "model": configured_video_model(episode),
            "mode": (
                "mcp"
                if episode.meta.get("GEN_PROVIDER") == "openart"
                else episode.meta.get("KIE_VIDEO_MODE", "")
            ),
            "aspect": episode.meta.get("ASPECT", ""),
            "resolution": episode.meta.get("VIDEO_RES", ""),
            "duration": episode.meta.get("VIDEO_DUR", ""),
            "audio_disabled": True,
        }
    else:
        raise PipelineError(f"Tipo de assinatura desconhecido: {media}")

    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def parse_hold(scene: dict[str, str]) -> float:
    try:
        return float(scene["hold"])
    except ValueError as exc:
        raise PipelineError(
            f"scenes.tsv:{scene['_line']}: hold inválido '{scene['hold']}'"
        ) from exc


def estimated_scene_seconds(scene: dict[str, str], words_per_minute: float) -> float:
    spoken = word_count(scene["text"]) / words_per_minute * 60
    return spoken + parse_hold(scene)


def ffprobe_duration(path: Path) -> float:
    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return float(completed.stdout.strip())
    except FileNotFoundError as exc:
        raise PipelineError("ffprobe não está instalado") from exc
    except (subprocess.CalledProcessError, ValueError) as exc:
        raise PipelineError(f"Não foi possível medir a duração de {path}") from exc


def ffprobe_info(path: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                (
                    "format=duration,format_name:format_tags=comment:"
                    "stream=index,codec_type,codec_name,width,height,"
                    "r_frame_rate,avg_frame_rate,nb_frames,duration,"
                    "sample_rate,channels"
                ),
                "-of",
                "json",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)
    except FileNotFoundError as exc:
        raise PipelineError("ffprobe não está instalado") from exc
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise PipelineError(f"Mídia não decodificável: {path}") from exc


def validate_visual_media(path: Path, kind: str) -> dict[str, Any]:
    if not path.exists() or not path.is_file() or path.stat().st_size == 0:
        raise PipelineError(f"Mídia visual ausente ou vazia: {path}")
    info = ffprobe_info(path)
    streams = info.get("streams") or []
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
    others = [
        stream
        for stream in streams
        if stream.get("codec_type") not in {"video", "audio"}
    ]
    if len(videos) != 1:
        raise PipelineError(
            f"{kind} precisa ter exatamente um stream visual: {path}"
        )
    if audios:
        raise PipelineError(f"{kind} não pode conter áudio: {path}")
    if others:
        raise PipelineError(f"{kind} contém streams extras não permitidos: {path}")

    video = videos[0]
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    codec = str(video.get("codec_name") or "")
    format_name = str((info.get("format") or {}).get("format_name", ""))
    if width <= 0 or height <= 0:
        raise PipelineError(f"{kind} possui dimensões inválidas: {path}")

    if kind == "reference":
        minimum = (1440, 1920)
        expected_ratio = 3 / 4
    elif kind in {"frame", "clip"}:
        minimum = (1920, 1080)
        expected_ratio = 16 / 9
    else:
        raise PipelineError(f"Tipo de mídia visual desconhecido: {kind}")

    if width < minimum[0] or height < minimum[1]:
        raise PipelineError(
            f"{kind} em baixa resolução: {width}x{height}; mínimo "
            f"{minimum[0]}x{minimum[1]}"
        )
    ratio = width / height
    if not math.isclose(ratio, expected_ratio, rel_tol=0, abs_tol=0.025):
        raise PipelineError(
            f"{kind} com proporção incorreta: {width}x{height}; "
            f"esperado {'3:4' if kind == 'reference' else '16:9'}"
        )

    metrics: dict[str, Any] = {
        "width": width,
        "height": height,
        "codec": codec,
        "format": format_name,
    }
    if kind in {"reference", "frame"}:
        if codec not in {"png", "mjpeg", "webp", "jpeg2000"}:
            raise PipelineError(
                f"{kind} precisa ser uma imagem estática real; codec '{codec}'"
            )
        if any(
            container in format_name.split(",")
            for container in {"mov", "mp4", "matroska", "webm"}
        ):
            raise PipelineError(
                f"{kind} não pode ser um vídeo renomeado como imagem: {path}"
            )
    if kind == "clip":
        duration = stream_duration(path, "video")
        expected = float(POLICY_INTEGERS["VIDEO_DUR"])
        if not expected - 0.6 <= duration <= expected + 0.6:
            raise PipelineError(
                f"clipe dura {duration:.2f}s; esperado {expected:.0f}s "
                "(tolerância ±0.6s)"
            )
        if codec not in {"h264", "hevc", "av1"}:
            raise PipelineError(
                f"clipe precisa usar codec temporal de alta qualidade; recebido '{codec}'"
            )
        if not {"mov", "mp4"}.intersection(format_name.split(",")):
            raise PipelineError(
                f"clipe precisa ser um container MP4/MOV real; recebido '{format_name}'"
            )
        raw_fps = video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1"
        try:
            fps = float(Fraction(str(raw_fps)))
        except (ValueError, ZeroDivisionError):
            fps = 0.0
        if not 23.5 <= fps <= 60.5:
            raise PipelineError(
                f"clipe com cadência inadequada: {fps:.3f} fps; esperado 24–60 fps"
            )
        raw_frames = video.get("nb_frames")
        if raw_frames not in {None, "", "N/A"}:
            try:
                frame_count = int(raw_frames)
            except (TypeError, ValueError):
                frame_count = 0
            if frame_count < duration * 20:
                raise PipelineError(
                    f"clipe possui apenas {frame_count} frames em {duration:.2f}s"
                )
        metrics["duration_seconds"] = duration
        metrics["fps"] = fps
    return metrics


def visual_artifact_contract(
    episode: Episode, kind: str, identifier: str
) -> tuple[Path, str, dict[str, str], list[tuple[str, Path]]]:
    if kind == "reference":
        character = episode.cast.get(identifier)
        if character is None or character["sheet_prompt"] == "-":
            raise PipelineError(f"Referência visual desconhecida: {identifier}")
        return (
            episode.root / "assets" / f"{identifier}_ref.png",
            "episode-reference",
            {"source_signature": reference_source_signature(episode, character)},
            [],
        )

    scene = next(
        (row for row in episode.scenes if row["id"] == identifier), None
    )
    if scene is None:
        raise PipelineError(f"Cena desconhecida: {identifier}")
    if kind == "frame":
        dependencies = []
        if scene["refs"] != "-":
            dependencies = [
                (f"ref-{key}", episode.root / "assets" / f"{key}_ref.png")
                for key in scene["refs"].split(",")
            ]
        return (
            episode.root / "frames" / f"{identifier}.png",
            "episode-frame",
            {"source_signature": media_source_signature(episode, scene, "frame")},
            dependencies,
        )
    if kind == "clip":
        return (
            episode.root / "clips" / f"{identifier}.mp4",
            "episode-clip",
            {"source_signature": media_source_signature(episode, scene, "clip")},
            [("frame", episode.root / "frames" / f"{identifier}.png")],
        )
    raise PipelineError(f"Tipo de aprovação visual desconhecido: {kind}")


def validate_clip_story_capacity(
    episode: Episode, identifier: str, clip_seconds: float
) -> None:
    scene = next(
        (row for row in episode.scenes if row["id"] == identifier), None
    )
    if scene is None:
        raise PipelineError(f"Cena desconhecida: {identifier}")
    estimated = estimated_scene_seconds(
        scene, meta_float(episode.meta, "WORDS_PER_MINUTE", 138)
    )
    required = estimated
    basis = "estimado"
    audio = episode.root / "audio" / f"{identifier}.mp3"
    if scene["text"] != "-" and audio.exists():
        required = actual_scene_seconds(episode, scene)
        basis = "real"
    max_stretch = meta_float(episode.meta, "MAX_STRETCH", 1.12)
    if required > clip_seconds * max_stretch:
        raise PipelineError(
            f"clipe '{identifier}' tem {clip_seconds:.2f}s, mas o beat {basis} "
            f"precisa {required:.2f}s; excede stretch de {max_stretch:.2f}x"
        )


def stream_duration(path: Path, stream_type: str) -> float:
    info = ffprobe_info(path)
    for stream in info.get("streams") or []:
        if stream.get("codec_type") != stream_type:
            continue
        raw = stream.get("duration")
        if raw not in {None, "", "N/A"}:
            try:
                value = float(raw)
                if math.isfinite(value) and value > 0:
                    return value
            except ValueError:
                pass
    try:
        fallback = float((info.get("format") or {}).get("duration", 0))
    except ValueError as exc:
        raise PipelineError(f"Duração inválida: {path}") from exc
    if not math.isfinite(fallback) or fallback <= 0:
        raise PipelineError(f"Duração inválida: {path}")
    return fallback


def expected_tts_cache_values(
    episode: Episode, scene: dict[str, str]
) -> dict[str, str]:
    character = episode.cast.get(scene["voice"])
    if character is None:
        raise PipelineError(f"Voz desconhecida: {scene['voice']}")
    return narration_tts_values(
        scene["id"],
        scene["act"],
        scene["voice"],
        scene["text"],
        character["voice_id"],
    )


def verify_cached_audio(
    path: Path, kind: str, expected_values: dict[str, str]
) -> dict[str, Any]:
    try:
        data = verify_recorded_output(path)
    except CacheError as exc:
        raise PipelineError(str(exc)) from exc
    if data.get("kind") != kind:
        raise PipelineError(f"Tipo de cache incorreto para {path}")
    if data.get("values") != expected_values:
        raise PipelineError(
            f"Entradas mudaram desde a geração de {path}; regenere o arquivo"
        )
    if stream_duration(path, "audio") <= 0.1:
        raise PipelineError(f"Áudio inválido ou curto demais: {path}")
    return data


def approvals_path(episode: Episode) -> Path:
    return episode.root / "audio" / "voice-tests" / "approvals.json"


def load_voice_approvals(episode: Episode) -> dict[str, dict[str, str]]:
    path = approvals_path(episode)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"Manifesto de aprovação inválido: {path}") from exc
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise PipelineError(f"Manifesto de aprovação inválido: {path}")
    approvals = data.get("approvals")
    if not isinstance(approvals, dict):
        raise PipelineError(f"Manifesto de aprovação inválido: {path}")
    normalized: dict[str, dict[str, str]] = {}
    required = {"voice_id", "fingerprint", "output_sha256", "approved_at"}
    for voice, approval in approvals.items():
        if (
            not isinstance(voice, str)
            or not isinstance(approval, dict)
            or not required.issubset(approval)
            or any(not isinstance(approval[key], str) for key in required)
        ):
            raise PipelineError(f"Manifesto de aprovação inválido: {path}")
        normalized[voice] = approval
    return normalized


def verify_voice_approval(
    episode: Episode, voice: str, character: dict[str, str]
) -> dict[str, str]:
    sample = episode.root / "audio" / "voice-tests" / f"{voice}.mp3"
    expected_values = tts_values(VOICE_TEST_TEXT, character["voice_id"])
    data = verify_cached_audio(
        sample,
        f"elevenlabs-audio:{TTS_JOB_TYPE}",
        expected_values,
    )
    approval = load_voice_approvals(episode).get(voice)
    if not approval:
        raise PipelineError(
            f"Voz '{voice}' não possui aprovação vinculada; "
            f"ouça a amostra e rode ./approve-voice.sh {voice}"
        )
    if (
        approval.get("fingerprint") != data.get("fingerprint")
        or approval.get("output_sha256") != data.get("output_sha256")
        or approval.get("voice_id") != character["voice_id"]
    ):
        raise PipelineError(
            f"A aprovação de '{voice}' pertence a outra amostra/voice_id; "
            f"ouça novamente e rode ./approve-voice.sh {voice}"
        )
    return approval


def actual_scene_seconds(episode: Episode, scene: dict[str, str]) -> float:
    if scene["text"] == "-":
        return parse_hold(scene)
    audio = episode.root / "audio" / f"{scene['id']}.mp3"
    verify_cached_audio(
        audio,
        f"elevenlabs-audio:{NARRATION_TTS_MODEL}",
        expected_tts_cache_values(episode, scene),
    )
    return stream_duration(audio, "audio") + parse_hold(scene)


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def validate_episode(episode: Episode, stage: str = "script") -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    meta = episode.meta

    validate_policy_meta(meta, errors)

    cast: dict[str, dict[str, str]] = {}
    for character in episode.characters:
        line = character["_line"]
        key = character["key"]
        if not KEY_RE.fullmatch(key):
            errors.append(f"characters.tsv:{line}: key inválida '{key}'")
        if key in cast:
            errors.append(f"characters.tsv:{line}: key duplicada '{key}'")
        cast[key] = character

        if not character["name"]:
            errors.append(f"characters.tsv:{line}: personagem sem name")
        if character["locale"] not in {"pt-BR", "-"}:
            errors.append(
                f"characters.tsv:{line}: locale '{character['locale']}' inválido; "
                "vozes faladas devem usar pt-BR"
            )
        if character["voice_approved"] not in {"yes", "no", "n/a"}:
            errors.append(
                f"characters.tsv:{line}: voice_approved deve ser yes, no ou n/a"
            )

    if "narrator" not in cast:
        errors.append("characters.tsv: elenco precisa conter a key 'narrator'")

    scene_ids: set[str] = set()
    referenced_voices: Counter[str] = Counter()
    referenced_voice_words: Counter[str] = Counter()
    acts: Counter[str] = Counter()
    shots: Counter[str] = Counter()
    total_words = 0
    dialogue_words = 0
    vfx_scenes = 0
    sfx_scenes = 0
    estimated_seconds = 0.0

    words_per_minute = meta_float(meta, "WORDS_PER_MINUTE", 138)
    if words_per_minute <= 0:
        errors.append("meta.env: WORDS_PER_MINUTE precisa ser maior que zero")
        words_per_minute = 138

    for index, scene in enumerate(episode.scenes, start=1):
        line = scene["_line"]
        scene_id = scene["id"]
        expected_id = f"{index:02d}"
        if scene_id != expected_id:
            errors.append(
                f"scenes.tsv:{line}: id deve ser sequencial; "
                f"esperado '{expected_id}', recebido '{scene_id}'"
            )
        if scene_id in scene_ids:
            errors.append(f"scenes.tsv:{line}: id duplicado '{scene_id}'")
        scene_ids.add(scene_id)

        if not scene["act"]:
            errors.append(f"scenes.tsv:{line}: act obrigatório")
        else:
            acts[scene["act"]] += 1
        if not scene["shot"]:
            errors.append(f"scenes.tsv:{line}: shot obrigatório")
        else:
            shots[scene["shot"]] += 1

        refs = [] if scene["refs"] == "-" else [
            value.strip() for value in scene["refs"].split(",") if value.strip()
        ]
        for ref in refs:
            if ref not in cast:
                errors.append(
                    f"scenes.tsv:{line}: referência visual desconhecida '{ref}'"
                )
            elif cast[ref]["sheet_prompt"] == "-":
                errors.append(
                    f"scenes.tsv:{line}: '{ref}' é somente voz e não pode aparecer em refs"
                )

        voice = scene["voice"]
        text = scene["text"]
        if (voice == "-") != (text == "-"):
            errors.append(
                f"scenes.tsv:{line}: voice e text devem ser ambos '-' em beat sem fala"
            )
        elif voice != "-":
            if voice not in cast:
                errors.append(f"scenes.tsv:{line}: voz desconhecida '{voice}'")
            else:
                character = cast[voice]
                if character["locale"] != "pt-BR":
                    errors.append(
                        f"scenes.tsv:{line}: voz '{voice}' não está marcada como pt-BR"
                    )
                if stage in {"audio", "produced-audio", "assembly"}:
                    if not VOICE_ID_RE.fullmatch(character["voice_id"]):
                        errors.append(
                            f"characters.tsv:{character['_line']}: voice_id de "
                            f"'{voice}' inválido para ElevenLabs"
                        )
                    if character["voice_approved"] != "yes":
                        errors.append(
                            f"characters.tsv:{character['_line']}: voz '{voice}' "
                            "ainda não foi aprovada em audição PT-BR"
                        )
                elif character["voice_approved"] != "yes":
                    warnings.append(
                        f"voz '{voice}' está pendente de audição PT-BR; "
                        "a geração de áudio ficará bloqueada"
                    )

            scene_words = word_count(text)
            referenced_voices[voice] += 1
            referenced_voice_words[voice] += scene_words
            total_words += scene_words
            if voice != "narrator":
                dialogue_words += scene_words

        try:
            hold = parse_hold(scene)
            if not 0.0 <= hold <= 10.0:
                errors.append(
                    f"scenes.tsv:{line}: hold deve ficar entre 0 e 10 segundos"
                )
        except PipelineError as exc:
            errors.append(str(exc))
            hold = 0.0

        if len(scene["image_prompt"]) < meta_int(meta, "MIN_IMAGE_PROMPT_CHARS", 100):
            errors.append(
                f"scenes.tsv:{line}: image_prompt curto demais para direção cinematográfica"
            )
        if len(scene["motion_prompt"]) < meta_int(meta, "MIN_MOTION_PROMPT_CHARS", 60):
            errors.append(
                f"scenes.tsv:{line}: motion_prompt curto demais para movimento de alta qualidade"
            )

        if scene["vfx"] != "-":
            vfx_scenes += 1
        if scene["sfx"] != "-":
            sfx_scenes += 1
        if scene["transition"] not in ALLOWED_TRANSITIONS:
            errors.append(
                f"scenes.tsv:{line}: transition '{scene['transition']}' inválida"
            )

        try:
            scene_seconds = estimated_scene_seconds(scene, words_per_minute)
            estimated_seconds += scene_seconds
            min_beat = meta_float(meta, "MIN_BEAT_SECONDS", 2.0)
            max_beat = meta_float(meta, "MAX_BEAT_SECONDS", 11.5)
            if scene_seconds < min_beat:
                errors.append(
                    f"scenes.tsv:{line}: beat estimado em {scene_seconds:.1f}s; "
                    f"mínimo {min_beat:.1f}s"
                )
            if scene_seconds > max_beat:
                errors.append(
                    f"scenes.tsv:{line}: beat estimado em {scene_seconds:.1f}s; "
                    f"máximo {max_beat:.1f}s. Divida a fala em mais planos."
                )
        except PipelineError as exc:
            errors.append(str(exc))

    ambiguous_language_lines = validate_portuguese_text(
        episode.scenes, errors, warnings
    )

    scene_count = len(episode.scenes)
    voiced_scene_count = sum(referenced_voices.values())
    distinct_voices = len(referenced_voices)
    voice_ids_seen: dict[str, str] = {}
    for voice in referenced_voices:
        character = cast.get(voice)
        if not character or not VOICE_ID_RE.fullmatch(character["voice_id"]):
            continue
        voice_id = character["voice_id"].lower()
        previous = voice_ids_seen.get(voice_id)
        if previous:
            errors.append(
                f"As vozes '{previous}' e '{voice}' usam o mesmo voice_id; "
                "cada papel falado precisa de uma voz realmente distinta"
            )
        else:
            voice_ids_seen[voice_id] = voice

    if stage in {"audio", "produced-audio", "assembly"}:
        approved_audio_hashes: dict[str, str] = {}
        for voice in referenced_voices:
            character = cast.get(voice)
            if (
                not character
                or not VOICE_ID_RE.fullmatch(character["voice_id"])
                or character["voice_approved"] != "yes"
            ):
                continue
            try:
                approval = verify_voice_approval(episode, voice, character)
                audio_hash = approval["output_sha256"]
                previous = approved_audio_hashes.get(audio_hash)
                if previous:
                    errors.append(
                        f"As vozes '{previous}' e '{voice}' possuem a mesma "
                        "amostra de áudio; escolha vozes perceptivelmente distintas"
                    )
                else:
                    approved_audio_hashes[audio_hash] = voice
            except PipelineError as exc:
                errors.append(str(exc))

    dialogue_ratio = _ratio(dialogue_words, total_words)
    vfx_ratio = _ratio(vfx_scenes, scene_count)
    sfx_ratio = _ratio(sfx_scenes, scene_count)

    min_scenes = meta_int(meta, "MIN_SCENES", 34)
    max_scenes = meta_int(meta, "MAX_SCENES", 46)
    if not min_scenes <= scene_count <= max_scenes:
        errors.append(
            f"Quantidade de cenas: {scene_count}; esperado entre "
            f"{min_scenes} e {max_scenes}"
        )

    min_voices = meta_int(meta, "MIN_VOICES", 4)
    if distinct_voices < min_voices:
        errors.append(
            f"Elenco falado insuficiente: {distinct_voices} vozes; mínimo {min_voices}"
        )

    min_dialogue_ratio = meta_float(meta, "MIN_DIALOGUE_RATIO", 0.25)
    if dialogue_ratio < min_dialogue_ratio:
        errors.append(
            f"Diálogo direto insuficiente: {dialogue_ratio:.0%}; "
            f"mínimo {min_dialogue_ratio:.0%}. Reduza a dependência do narrador."
        )

    min_vfx_ratio = meta_float(meta, "MIN_VFX_RATIO", 0.25)
    if vfx_ratio < min_vfx_ratio:
        errors.append(
            f"Cobertura de VFX insuficiente: {vfx_ratio:.0%}; mínimo {min_vfx_ratio:.0%}"
        )

    min_sfx_ratio = meta_float(meta, "MIN_SFX_RATIO", 0.70)
    if sfx_ratio < min_sfx_ratio:
        errors.append(
            f"Cobertura de desenho de som insuficiente: {sfx_ratio:.0%}; "
            f"mínimo {min_sfx_ratio:.0%}"
        )

    min_acts = meta_int(meta, "MIN_ACTS", 6)
    if len(acts) < min_acts:
        errors.append(
            f"Arco narrativo simples demais: {len(acts)} atos/beats; mínimo {min_acts}"
        )

    min_shot_variety = meta_int(meta, "MIN_SHOT_VARIETY", 8)
    if len(shots) < min_shot_variety:
        errors.append(
            f"Pouca variedade de câmera: {len(shots)} tipos de plano; "
            f"mínimo {min_shot_variety}"
        )

    min_duration = meta_float(meta, "MIN_DURATION", 285)
    max_duration = meta_float(meta, "MAX_DURATION", 315)
    duration_for_gate = estimated_seconds

    if stage in {"produced-audio", "assembly"} and not errors:
        actual_total = 0.0
        for scene in episode.scenes:
            try:
                actual_seconds = actual_scene_seconds(episode, scene)
                actual_total += actual_seconds
                if actual_seconds < POLICY_FLOATS["MIN_BEAT_SECONDS"]:
                    errors.append(
                        f"Cena {scene['id']} dura {actual_seconds:.1f}s; "
                        f"mínimo real {POLICY_FLOATS['MIN_BEAT_SECONDS']:.1f}s"
                    )
                if actual_seconds > POLICY_FLOATS["MAX_BEAT_SECONDS"]:
                    errors.append(
                        f"Cena {scene['id']} dura {actual_seconds:.1f}s; "
                        f"máximo real {POLICY_FLOATS['MAX_BEAT_SECONDS']:.1f}s. "
                        "Divida a fala em mais planos."
                    )
            except PipelineError as exc:
                errors.append(str(exc))
        duration_for_gate = actual_total

    if not min_duration <= duration_for_gate <= max_duration:
        label = "real" if stage in {"produced-audio", "assembly"} else "estimada"
        errors.append(
            f"Duração {label}: {duration_for_gate:.1f}s; "
            f"faixa obrigatória {min_duration:.0f}–{max_duration:.0f}s"
        )

    if stage == "produced-audio" and not errors:
        try:
            visual_approvals = load_visual_approvals(episode)
        except PipelineError as exc:
            errors.append(str(exc))
            visual_approvals = {}
        max_stretch = meta_float(meta, "MAX_STRETCH", 1.12)
        for scene in episode.scenes:
            scene_id = scene["id"]
            if visual_approval_key("clip", scene_id) not in visual_approvals:
                continue
            try:
                verify_visual_approval(episode, "clip", scene_id)
                clip_seconds = stream_duration(
                    episode.root / "clips" / f"{scene_id}.mp4", "video"
                )
                required_seconds = actual_scene_seconds(episode, scene)
                if required_seconds > clip_seconds * max_stretch:
                    errors.append(
                        f"Cena {scene_id}: áudio real precisa {required_seconds:.1f}s, "
                        f"mas o clipe aprovado tem {clip_seconds:.1f}s; excede "
                        f"stretch de {max_stretch:.2f}x"
                    )
            except PipelineError as exc:
                errors.append(str(exc))

    if stage == "assembly" and not errors:
        max_stretch = meta_float(meta, "MAX_STRETCH", 1.12)
        for scene in episode.scenes:
            scene_id = scene["id"]
            clip = episode.root / "clips" / f"{scene_id}.mp4"
            if not clip.exists():
                errors.append(f"Clipe ausente: {clip}")
                continue

            frame = episode.root / "frames" / f"{scene_id}.png"
            if not frame.exists():
                errors.append(f"Frame-fonte ausente: {frame}")
                continue
            try:
                verify_visual_approval(episode, "clip", scene_id)
            except PipelineError as exc:
                errors.append(str(exc))
                continue
            clip_seconds = stream_duration(clip, "video")
            required_seconds = actual_scene_seconds(episode, scene)
            if required_seconds > clip_seconds * max_stretch:
                errors.append(
                    f"Cena {scene_id}: precisa {required_seconds:.1f}s, "
                    f"clipe tem {clip_seconds:.1f}s; excede stretch máximo "
                    f"de {max_stretch:.2f}x. Divida a cena ou gere clipe maior."
                )
            if scene["sfx"] != "-":
                sfx = episode.root / "audio" / "sfx" / f"{scene_id}.wav"
                sfx_base_prompt = (
                    f"{scene['sfx']}. Scene context: {scene['act']}. "
                    "Build clear foreground action, environmental ambience, "
                    "and subtle spatial depth."
                )
                try:
                    verify_cached_audio(
                        sfx,
                        f"elevenlabs-audio:{SFX_JOB_TYPE}",
                        sfx_values(sfx_base_prompt, required_seconds),
                    )
                    sfx_seconds = stream_duration(sfx, "audio")
                    if sfx_seconds < required_seconds - 0.25:
                        errors.append(
                            f"SFX {scene_id} dura {sfx_seconds:.2f}s, mas a cena "
                            f"precisa {required_seconds:.2f}s"
                        )
                except PipelineError as exc:
                    errors.append(str(exc))

    if stage == "assembly" and (episode.root / "audio" / "bgm.mp3").exists():
        try:
            verify_music_approval(episode)
        except PipelineError as exc:
            errors.append(str(exc))

    if stage in {"production", "audio", "produced-audio", "assembly"}:
        try:
            verify_script_approval(episode)
        except PipelineError as exc:
            errors.append(str(exc))

    metrics: dict[str, Any] = {
        "title": meta.get("TITLE", episode.root.name),
        "scene_count": scene_count,
        "voiced_scene_count": voiced_scene_count,
        "word_count": total_words,
        "dialogue_words": dialogue_words,
        "dialogue_ratio": dialogue_ratio,
        "distinct_voices": distinct_voices,
        "distinct_voice_ids": len(voice_ids_seen),
        "voices": dict(referenced_voice_words),
        "act_count": len(acts),
        "acts": dict(acts),
        "shot_variety": len(shots),
        "shots": dict(shots),
        "vfx_ratio": vfx_ratio,
        "sfx_ratio": sfx_ratio,
        "estimated_seconds": estimated_seconds,
        "duration_seconds": duration_for_gate,
        "target_seconds": meta_float(meta, "TARGET_DURATION", 300),
        "ambiguous_language_lines": ambiguous_language_lines,
    }
    return ValidationResult(
        errors=list(dict.fromkeys(errors)),
        warnings=sorted(set(warnings)),
        metrics=metrics,
    )


def render_script(episode: Episode, result: ValidationResult) -> str:
    metrics = result.metrics
    meta = episode.meta
    cast = episode.cast
    minutes, seconds = divmod(round(metrics["estimated_seconds"]), 60)

    lines = [
        f"# {meta['TITLE']} — Roteiro de Produção",
        "",
        (
            f"**Formato:** filme infantil 3D cinematográfico · {meta.get('ASPECT', '16:9')} "
            f"· estimativa {minutes}min{seconds:02d}s"
        ),
        (
            f"**Qualidade:** {metrics['scene_count']} planos · "
            f"{metrics['distinct_voices']} vozes · "
            f"{metrics['dialogue_ratio']:.0%} de diálogo direto · "
            f"{metrics['vfx_ratio']:.0%} com VFX · "
            f"{metrics['sfx_ratio']:.0%} com desenho de som"
        ),
        "**Idioma obrigatório:** português brasileiro (pt-BR), sem sotaque de Portugal.",
        (
            "**Revisão linguística obrigatória:** as linhas "
            + ", ".join(metrics["ambiguous_language_lines"])
            + " são ambíguas para o detector e exigem confirmação humana explícita."
            if metrics["ambiguous_language_lines"]
            else "**Revisão linguística:** nenhum trecho ambíguo detectado."
        ),
        "",
        "## Elenco de voz",
        "",
    ]

    used_voices = set(metrics["voices"])
    for character in episode.characters:
        if character["key"] not in used_voices:
            continue
        status = (
            "aprovada em PT-BR"
            if character["voice_approved"] == "yes"
            else "PENDENTE de audição"
        )
        lines.append(
            f"- **{character['name']}** (`{character['key']}`): "
            f"{character['locale']} · {status}"
        )

    current_act: str | None = None
    for scene in episode.scenes:
        if scene["act"] != current_act:
            current_act = scene["act"]
            lines.extend(["", "---", "", f"## Ato/beat — {current_act}", ""])

        speaker = (
            "Beat sem fala"
            if scene["voice"] == "-"
            else f"{cast[scene['voice']]['name']} ({scene['voice']})"
        )
        lines.extend(
            [
                f"### Cena {scene['id']} · {scene['shot']} · {scene['transition']}",
                f"**Voz:** {speaker}",
                (
                    f"**Texto:** “{scene['text']}”"
                    if scene["text"] != "-"
                    else "**Texto:** —"
                ),
                f"**Respiro dramático:** {float(scene['hold']):.1f}s",
                f"**Visual:** {scene['image_prompt']}",
                f"**Movimento de câmera/personagens:** {scene['motion_prompt']}",
                f"**VFX:** {scene['vfx'] if scene['vfx'] != '-' else 'sem efeito especial dedicado'}",
                f"**SFX/ambiência:** {scene['sfx'] if scene['sfx'] != '-' else 'silêncio intencional'}",
                f"**Referências:** {scene['refs']}",
                "",
            ]
        )

    lines.extend(
        [
            "---",
            "",
            "## Gates antes de gerar mídia",
            "",
            "- Aprovar história, fidelidade bíblica, ritmo e adequação infantil.",
            "- Ouvir cada amostra em `audio/voice-tests/` e aprovar somente sotaque brasileiro.",
            "- Confirmar continuidade visual dos personagens e geografia entre cenas.",
            "- Não gerar narração enquanto qualquer voz usada estiver pendente.",
            "",
        ]
    )
    return "\n".join(lines)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def visual_approvals_path(episode: Episode) -> Path:
    return episode.root / "approvals" / "visual.json"


def load_visual_approvals(episode: Episode) -> dict[str, dict[str, str]]:
    path = visual_approvals_path(episode)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"Manifesto de aprovação visual inválido: {path}") from exc
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise PipelineError(f"Manifesto de aprovação visual inválido: {path}")
    approvals = data.get("approvals")
    if not isinstance(approvals, dict):
        raise PipelineError(f"Manifesto de aprovação visual inválido: {path}")
    normalized: dict[str, dict[str, str]] = {}
    required = {
        "kind",
        "identifier",
        "fingerprint",
        "output_sha256",
        "approved_at",
    }
    for key, approval in approvals.items():
        if (
            not isinstance(key, str)
            or not isinstance(approval, dict)
            or not required.issubset(approval)
            or any(not isinstance(approval[field], str) for field in required)
        ):
            raise PipelineError(f"Manifesto de aprovação visual inválido: {path}")
        normalized[key] = approval
    return normalized


def visual_approval_key(kind: str, identifier: str) -> str:
    return f"{kind}:{identifier}"


def verify_visual_upstream(
    episode: Episode, kind: str, identifier: str
) -> None:
    if kind == "frame":
        scene = next(
            (row for row in episode.scenes if row["id"] == identifier), None
        )
        if scene is None:
            raise PipelineError(f"Cena desconhecida: {identifier}")
        if scene["refs"] != "-":
            for key in scene["refs"].split(","):
                verify_visual_approval(episode, "reference", key)
    elif kind == "clip":
        verify_visual_approval(episode, "frame", identifier)


def verify_visual_approval(
    episode: Episode, kind: str, identifier: str
) -> dict[str, str]:
    path, cache_kind, values, dependencies = visual_artifact_contract(
        episode, kind, identifier
    )
    visual_kind = "reference" if kind == "reference" else kind
    media_metrics = validate_visual_media(path, visual_kind)
    if kind == "clip":
        validate_clip_story_capacity(
            episode, identifier, media_metrics["duration_seconds"]
        )
    valid, reason = cache_valid(path, cache_kind, values, dependencies)
    if not valid:
        raise PipelineError(f"{kind} '{identifier}' está obsoleto: {reason}")
    verify_visual_upstream(episode, kind, identifier)
    try:
        cache_data = verify_recorded_output(path)
    except CacheError as exc:
        raise PipelineError(str(exc)) from exc
    approval = load_visual_approvals(episode).get(
        visual_approval_key(kind, identifier)
    )
    if not approval:
        raise PipelineError(
            f"{kind} '{identifier}' ainda não possui aprovação visual vinculada"
        )
    if (
        approval.get("kind") != kind
        or approval.get("identifier") != identifier
        or approval.get("fingerprint") != cache_data.get("fingerprint")
        or approval.get("output_sha256") != cache_data.get("output_sha256")
    ):
        raise PipelineError(
            f"A aprovação visual de {kind} '{identifier}' pertence a outro arquivo "
            "ou outra versão do prompt"
        )
    return approval


def approve_visual(
    episode: Episode, kind: str, identifier: str
) -> dict[str, str]:
    path, cache_kind, values, dependencies = visual_artifact_contract(
        episode, kind, identifier
    )
    media_metrics = validate_visual_media(
        path, "reference" if kind == "reference" else kind
    )
    if kind == "clip":
        validate_clip_story_capacity(
            episode, identifier, media_metrics["duration_seconds"]
        )
    valid, reason = cache_valid(path, cache_kind, values, dependencies)
    if not valid:
        raise PipelineError(
            f"Não é possível aprovar {kind} '{identifier}': {reason}"
        )
    verify_visual_upstream(episode, kind, identifier)
    try:
        cache_data = verify_recorded_output(path)
    except CacheError as exc:
        raise PipelineError(str(exc)) from exc
    approval = {
        "kind": kind,
        "identifier": identifier,
        "fingerprint": str(cache_data["fingerprint"]),
        "output_sha256": str(cache_data["output_sha256"]),
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }
    approvals = load_visual_approvals(episode)
    approvals[visual_approval_key(kind, identifier)] = approval
    atomic_write_json(
        visual_approvals_path(episode),
        {"schema": 1, "approvals": approvals},
    )
    return approval


def music_approval_path(episode: Episode) -> Path:
    return episode.root / "approvals" / "music.json"


def expected_music_values(episode: Episode) -> dict[str, str]:
    duration = sum(actual_scene_seconds(episode, scene) for scene in episode.scenes)
    return music_values(episode.meta["SCORE_PROMPT"], duration)


def load_music_approval(episode: Episode) -> dict[str, Any]:
    path = music_approval_path(episode)
    if not path.exists():
        raise PipelineError(
            "Trilha ainda não foi aprovada; ouça e rode ./approve-music.sh"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"Aprovação de trilha inválida: {path}") from exc
    required = {"source", "fingerprint", "output_sha256", "approved_at"}
    if (
        not isinstance(data, dict)
        or data.get("schema") != 1
        or not required.issubset(data)
        or any(not isinstance(data[key], str) for key in required)
        or data["source"] not in {"generated", "external"}
    ):
        raise PipelineError(f"Aprovação de trilha inválida: {path}")
    return data


def music_artifact_data(
    episode: Episode,
) -> tuple[str, str, str]:
    bgm = episode.root / "audio" / "bgm.mp3"
    if not bgm.exists() or bgm.stat().st_size == 0:
        raise PipelineError(f"Trilha ausente ou vazia: {bgm}")
    if stream_duration(bgm, "audio") <= 1.0:
        raise PipelineError(f"Trilha curta ou inválida: {bgm}")
    sidecar = Path(f"{bgm}.meta.json")
    if sidecar.exists():
        data = verify_cached_audio(
            bgm,
            f"elevenlabs-audio:{MUSIC_JOB_TYPE}",
            expected_music_values(episode),
        )
        return (
            "generated",
            str(data["fingerprint"]),
            str(data["output_sha256"]),
        )
    output_hash = sha256_file(bgm)
    return ("external", f"external:{output_hash}", output_hash)


def approve_music(episode: Episode) -> dict[str, Any]:
    source, fingerprint, output_sha256 = music_artifact_data(episode)
    approval = {
        "schema": 1,
        "source": source,
        "fingerprint": fingerprint,
        "output_sha256": output_sha256,
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_json(music_approval_path(episode), approval)
    return approval


def verify_music_approval(episode: Episode) -> dict[str, Any]:
    source, fingerprint, output_sha256 = music_artifact_data(episode)
    approval = load_music_approval(episode)
    if (
        approval["source"] != source
        or approval["fingerprint"] != fingerprint
        or approval["output_sha256"] != output_sha256
    ):
        raise PipelineError(
            "A trilha ou seu prompt mudou após a aprovação; ouça e aprove novamente"
        )
    return approval


def script_source_fingerprint(episode: Episode) -> str:
    characters = [
        {
            "key": row["key"],
            "name": row["name"],
            "locale": row["locale"],
            "sheet_prompt": row["sheet_prompt"],
        }
        for row in episode.characters
    ]
    scenes = [
        {field: row[field] for field in SCENE_FIELDS} for row in episode.scenes
    ]
    meta_keys = (
        "TITLE",
        "SLUG",
        "LANGUAGE",
        "TARGET_DURATION",
        "MIN_DURATION",
        "MAX_DURATION",
        "WORDS_PER_MINUTE",
        "STYLE",
        "IMAGE_QUALITY",
        "IMAGE_NEGATIVE",
        "MOTION_QUALITY",
        "ASPECT",
    )
    brief = episode.root / "PRODUCTION-BRIEF.md"
    payload = {
        "schema": 1,
        "pipeline_version": PIPELINE_VERSION,
        "meta": {key: episode.meta.get(key, "") for key in meta_keys},
        "characters": characters,
        "scenes": scenes,
        "brief_sha256": (
            hashlib.sha256(brief.read_bytes()).hexdigest() if brief.exists() else ""
        ),
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def script_approval_path(episode: Episode) -> Path:
    return episode.root / "approvals" / "script.json"


def approve_script(
    episode: Episode, confirm_ambiguous_pt_br: bool = False
) -> dict[str, Any]:
    result = validate_episode(episode, "script")
    if not result.ok:
        raise PipelineError(
            "Roteiro não pode ser aprovado enquanto houver gates reprovados"
        )
    ambiguous_lines = list(result.metrics["ambiguous_language_lines"])
    if ambiguous_lines and not confirm_ambiguous_pt_br:
        raise PipelineError(
            "Há falas com idioma ambíguo nas linhas "
            + ", ".join(ambiguous_lines)
            + "; revise-as e rode ./approve-script.sh --confirm-ambiguous-pt-br"
        )
    roteiro = episode.root / "roteiro.md"
    if not roteiro.exists():
        raise PipelineError("roteiro.md ausente; rode ./make-roteiro.sh")
    expected = render_script(episode, result)
    actual = roteiro.read_text(encoding="utf-8")
    if actual != expected:
        raise PipelineError(
            "roteiro.md não corresponde às fontes atuais; rode ./make-roteiro.sh novamente"
        )
    approval = {
        "schema": 1,
        "source_fingerprint": script_source_fingerprint(episode),
        "document_sha256": hashlib.sha256(actual.encode("utf-8")).hexdigest(),
        "ambiguous_pt_br_lines": ambiguous_lines,
        "ambiguous_language_confirmed": bool(ambiguous_lines),
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_json(script_approval_path(episode), approval)
    return approval


def verify_script_approval(episode: Episode) -> None:
    path = script_approval_path(episode)
    if not path.exists():
        raise PipelineError(
            "Roteiro ainda não foi aprovado; leia roteiro.md e rode ./approve-script.sh"
        )
    try:
        approval = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"Aprovação de roteiro inválida: {path}") from exc
    required_strings = {"source_fingerprint", "document_sha256", "approved_at"}
    if (
        not isinstance(approval, dict)
        or approval.get("schema") != 1
        or not required_strings.issubset(approval)
        or any(not isinstance(approval[key], str) for key in required_strings)
        or not isinstance(approval.get("ambiguous_pt_br_lines"), list)
        or any(
            not isinstance(line, str)
            for line in approval.get("ambiguous_pt_br_lines", [])
        )
        or not isinstance(approval.get("ambiguous_language_confirmed"), bool)
    ):
        raise PipelineError(f"Aprovação de roteiro inválida: {path}")
    expected = script_source_fingerprint(episode)
    if approval.get("source_fingerprint") != expected:
        raise PipelineError(
            "O roteiro, personagens ou briefing mudaram após a aprovação; "
            "gere roteiro.md e aprove novamente"
        )
    current_result = validate_episode(episode, "script")
    if not current_result.ok:
        raise PipelineError("O roteiro aprovado não passa mais nos gates atuais")
    current_ambiguous = current_result.metrics["ambiguous_language_lines"]
    if approval["ambiguous_pt_br_lines"] != current_ambiguous or (
        current_ambiguous and not approval["ambiguous_language_confirmed"]
    ):
        raise PipelineError(
            "A confirmação de idioma ambíguo não corresponde ao roteiro atual"
        )
    roteiro = episode.root / "roteiro.md"
    if not roteiro.exists():
        raise PipelineError(
            "roteiro.md aprovado não existe mais; gere e aprove novamente"
        )
    document_sha256 = hashlib.sha256(roteiro.read_bytes()).hexdigest()
    if approval.get("document_sha256") != document_sha256:
        raise PipelineError(
            "roteiro.md mudou após a aprovação; gere e aprove novamente"
        )


def approve_voice(episode: Episode, voice: str) -> dict[str, str]:
    character = episode.cast.get(voice)
    if character is None:
        raise PipelineError(f"Voz desconhecida: {voice}")
    if character["locale"] != "pt-BR":
        raise PipelineError(f"Voz '{voice}' não está marcada como pt-BR")
    if not VOICE_ID_RE.fullmatch(character["voice_id"]):
        raise PipelineError(f"voice_id inválido para '{voice}'")

    sample = episode.root / "audio" / "voice-tests" / f"{voice}.mp3"
    data = verify_cached_audio(
        sample,
        f"elevenlabs-audio:{TTS_JOB_TYPE}",
        tts_values(VOICE_TEST_TEXT, character["voice_id"]),
    )
    approval = {
        "voice_id": character["voice_id"],
        "fingerprint": str(data["fingerprint"]),
        "output_sha256": str(data["output_sha256"]),
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }

    path = approvals_path(episode)
    existing = load_voice_approvals(episode) if path.exists() else {}
    existing[voice] = approval
    atomic_write_json(path, {"schema": 1, "approvals": existing})

    characters_path = episode.root / "characters.tsv"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        dir=episode.root,
        prefix=".characters.",
        suffix=".tsv.tmp",
        delete=False,
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=CHARACTER_FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in episode.characters:
            clean = {field: row[field] for field in CHARACTER_FIELDS}
            if clean["key"] == voice:
                clean["voice_approved"] = "yes"
            writer.writerow(clean)
        temporary = Path(handle.name)
    os.replace(temporary, characters_path)
    return approval


def analyze_loudness(path: Path) -> tuple[float, float]:
    try:
        completed = subprocess.run(
            [
                "ffmpeg",
                "-nostats",
                "-i",
                str(path),
                "-filter_complex",
                "ebur128=peak=true",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise PipelineError("ffmpeg não está instalado") from exc
    if completed.returncode != 0:
        raise PipelineError(f"Falha ao analisar loudness de {path}")

    output = completed.stderr
    integrated_matches = re.findall(
        r"Integrated loudness:\s+I:\s+(-?(?:\d+(?:\.\d+)?|inf))\s+LUFS",
        output,
        re.IGNORECASE,
    )
    peak_matches = re.findall(
        r"True peak:\s+Peak:\s+(-?(?:\d+(?:\.\d+)?|inf))\s+dBFS",
        output,
        re.IGNORECASE,
    )
    if not integrated_matches or not peak_matches:
        raise PipelineError(f"Não foi possível ler loudness/true peak de {path}")
    try:
        integrated = float(integrated_matches[-1])
        peak = float(peak_matches[-1])
    except ValueError as exc:
        raise PipelineError(f"Loudness inválido em {path}") from exc
    if not math.isfinite(integrated) or not math.isfinite(peak):
        raise PipelineError(f"Loudness não finito em {path}")
    return integrated, peak


def master_cache_values(
    episode: Episode, session_fingerprint: str, expected_duration: float
) -> dict[str, str]:
    return {
        "pipeline_version": PIPELINE_VERSION,
        "source_fingerprint": script_source_fingerprint(episode),
        "assembly_session": session_fingerprint,
        "expected_duration": f"{expected_duration:.3f}",
        "fps": episode.meta.get("FPS", ""),
        "bgm_volume": episode.meta.get("BGMVOL", ""),
        "sfx_volume": episode.meta.get("SFXVOL", ""),
        "master_limit": episode.meta.get("MASTER_LIMIT", ""),
        "video_codec": "libx264-crf17-slow-yuv420p",
        "audio_codec": "aac-256k-48000-stereo",
        "loudness": "I=-14:TP=-1.5:LRA=9",
    }


def master_dependencies(episode: Episode) -> list[tuple[str, Path]]:
    dependencies: list[tuple[str, Path]] = [
        ("meta", episode.root / "meta.env"),
        ("characters", episode.root / "characters.tsv"),
        ("scenes", episode.root / "scenes.tsv"),
        ("brief", episode.root / "PRODUCTION-BRIEF.md"),
        ("roteiro", episode.root / "roteiro.md"),
        ("script-approval", script_approval_path(episode)),
        ("voice-approvals", approvals_path(episode)),
        ("visual-approvals", visual_approvals_path(episode)),
    ]
    referenced_assets = sorted(
        {
            key
            for scene in episode.scenes
            if scene["refs"] != "-"
            for key in scene["refs"].split(",")
        }
    )
    for key in referenced_assets:
        dependencies.append(
            (f"reference-{key}", episode.root / "assets" / f"{key}_ref.png")
        )
    for scene in episode.scenes:
        scene_id = scene["id"]
        dependencies.extend(
            [
                (f"frame-{scene_id}", episode.root / "frames" / f"{scene_id}.png"),
                (f"clip-{scene_id}", episode.root / "clips" / f"{scene_id}.mp4"),
            ]
        )
        if scene["text"] != "-":
            dependencies.append(
                (f"dialogue-{scene_id}", episode.root / "audio" / f"{scene_id}.mp3")
            )
        if scene["sfx"] != "-":
            dependencies.append(
                (
                    f"sfx-{scene_id}",
                    episode.root / "audio" / "sfx" / f"{scene_id}.wav",
                )
            )
    bgm = episode.root / "audio" / "bgm.mp3"
    if bgm.exists():
        dependencies.extend(
            [
                ("bgm", bgm),
                ("music-approval", music_approval_path(episode)),
            ]
        )
    return dependencies


def _canonical_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def timeline_duration(path: Path, episode: Episode) -> float:
    if not path.exists():
        raise PipelineError(f"Timeline de montagem ausente: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["scene", "seconds", "voice", "transition"]:
            raise PipelineError(f"Timeline de montagem com cabeçalho inválido: {path}")
        rows = list(reader)
    expected_ids = [scene["id"] for scene in episode.scenes]
    if [row.get("scene") for row in rows] != expected_ids:
        raise PipelineError("Timeline de montagem não corresponde às cenas atuais")
    try:
        values = [float(row["seconds"]) for row in rows]
    except (TypeError, ValueError, KeyError) as exc:
        raise PipelineError(f"Timeline de montagem inválida: {path}") from exc
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise PipelineError(f"Timeline de montagem possui duração inválida: {path}")
    return sum(values)


def _master_inputs_fingerprint(episode: Episode) -> str:
    fingerprint, _ = fingerprint_payload(
        "episode-master-inputs",
        {
            "pipeline_version": PIPELINE_VERSION,
            "source_fingerprint": script_source_fingerprint(episode),
        },
        master_dependencies(episode),
    )
    return fingerprint


def create_assembly_lock(
    episode: Episode, lock_path: Path
) -> dict[str, Any]:
    build_root = (episode.root / "build").resolve()
    lock_path = lock_path.resolve()
    if lock_path.parent != build_root or lock_path.name != "source-lock.json":
        raise PipelineError("Lock da montagem precisa ser build/source-lock.json")
    assembly = validate_episode(episode, "assembly")
    if not assembly.ok:
        raise PipelineError(
            "Não é possível bloquear fontes da montagem: "
            + "; ".join(assembly.errors[:5])
        )
    payload: dict[str, Any] = {
        "schema": 1,
        "pipeline_version": PIPELINE_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "nonce": secrets.token_hex(16),
        "episode_slug": episode.meta["SLUG"],
        "source_fingerprint": script_source_fingerprint(episode),
        "master_inputs_fingerprint": _master_inputs_fingerprint(episode),
        "expected_duration": round(
            float(assembly.metrics["duration_seconds"]), 3
        ),
    }
    payload["lock_fingerprint"] = _canonical_sha256(payload)
    atomic_write_json(lock_path, payload)
    return payload


def verify_assembly_lock(
    episode: Episode, lock_path: Path
) -> tuple[dict[str, Any], ValidationResult]:
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"Lock da montagem inválido: {lock_path}") from exc
    required = {
        "schema",
        "pipeline_version",
        "created_at",
        "nonce",
        "episode_slug",
        "source_fingerprint",
        "master_inputs_fingerprint",
        "expected_duration",
        "lock_fingerprint",
    }
    if (
        not isinstance(data, dict)
        or not required.issubset(data)
        or data["schema"] != 1
        or data["pipeline_version"] != PIPELINE_VERSION
    ):
        raise PipelineError(f"Lock da montagem inválido: {lock_path}")
    fingerprint = data.pop("lock_fingerprint")
    expected_fingerprint = _canonical_sha256(data)
    data["lock_fingerprint"] = fingerprint
    if (
        not isinstance(fingerprint, str)
        or fingerprint != expected_fingerprint
    ):
        raise PipelineError("Fingerprint do lock da montagem é inválido")
    try:
        created = datetime.fromisoformat(str(data["created_at"]))
        if created.tzinfo is None:
            raise ValueError("timezone ausente")
        age_seconds = (datetime.now(timezone.utc) - created).total_seconds()
    except (TypeError, ValueError) as exc:
        raise PipelineError("Data do lock da montagem é inválida") from exc
    if not 0 <= age_seconds <= 6 * 60 * 60:
        raise PipelineError("Lock da montagem expirou; inicie a montagem novamente")

    assembly = validate_episode(episode, "assembly")
    if not assembly.ok:
        raise PipelineError(
            "Fontes mudaram após o lock: " + "; ".join(assembly.errors[:5])
        )
    try:
        locked_duration = float(data["expected_duration"])
        current_duration = float(assembly.metrics["duration_seconds"])
    except (TypeError, ValueError) as exc:
        raise PipelineError("Duração do lock da montagem é inválida") from exc
    if (
        data["episode_slug"] != episode.meta["SLUG"]
        or data["source_fingerprint"] != script_source_fingerprint(episode)
        or data["master_inputs_fingerprint"] != _master_inputs_fingerprint(episode)
        or not math.isclose(
            locked_duration,
            current_duration,
            rel_tol=0,
            abs_tol=0.001,
        )
    ):
        raise PipelineError("Fontes mudaram após o lock da montagem")
    return data, assembly


def create_assembly_session(
    episode: Episode,
    source_lock: Path,
    session_path: Path,
    timeline: Path,
    video_stem: Path,
    audio_stem: Path,
    expected_output: Path,
) -> dict[str, Any]:
    lock, assembly = verify_assembly_lock(episode, source_lock)
    build_root = (episode.root / "build").resolve()
    session_path = session_path.resolve()
    if (
        session_path.parent != build_root
        or session_path.name != "assembly-session.json"
    ):
        raise PipelineError("Manifesto da sessão precisa ser build/assembly-session.json")
    for source in (timeline, video_stem, audio_stem):
        if not source.resolve().is_relative_to(build_root):
            raise PipelineError(f"Entrada da montagem fora de build/: {source}")
        if not source.exists() or source.stat().st_size == 0:
            raise PipelineError(f"Entrada da montagem ausente ou vazia: {source}")
    expected_output = expected_output.resolve()
    if (
        expected_output.parent != episode.root
        or expected_output.suffix.lower() != ".mp4"
        or not expected_output.name.startswith(f".{episode.meta['SLUG']}_final.")
    ):
        raise PipelineError("Saída temporária do master possui caminho inválido")

    expected_duration = float(assembly.metrics["duration_seconds"])
    timeline_seconds = timeline_duration(timeline, episode)
    if not math.isclose(
        timeline_seconds, expected_duration, rel_tol=0, abs_tol=0.05
    ):
        raise PipelineError(
            f"Timeline soma {timeline_seconds:.3f}s, mas as fontes atuais "
            f"exigem {expected_duration:.3f}s"
        )
    for label, stem in (("vídeo", video_stem), ("áudio", audio_stem)):
        stem_seconds = stream_duration(
            stem, "video" if label == "vídeo" else "audio"
        )
        if not math.isclose(
            stem_seconds, timeline_seconds, rel_tol=0, abs_tol=1.5
        ):
            raise PipelineError(
                f"Stem de {label} dura {stem_seconds:.3f}s; "
                f"timeline possui {timeline_seconds:.3f}s"
            )

    payload: dict[str, Any] = {
        "schema": 1,
        "pipeline_version": PIPELINE_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "nonce": secrets.token_hex(16),
        "episode_slug": episode.meta["SLUG"],
        "source_fingerprint": script_source_fingerprint(episode),
        "master_inputs_fingerprint": _master_inputs_fingerprint(episode),
        "source_lock_fingerprint": lock["lock_fingerprint"],
        "expected_duration": round(expected_duration, 3),
        "expected_output": str(expected_output),
        "assembly_inputs": [
            {
                "label": label,
                "filename": source.name,
                "sha256": sha256_file(source),
            }
            for label, source in (
                ("timeline", timeline),
                ("video-stem", video_stem),
                ("audio-stem", audio_stem),
            )
        ],
    }
    payload["session_fingerprint"] = _canonical_sha256(payload)
    atomic_write_json(session_path, payload)
    return payload


def verify_assembly_session(
    episode: Episode, session_path: Path, output_path: Path
) -> tuple[dict[str, Any], ValidationResult]:
    session_path = session_path.resolve()
    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"Sessão de montagem inválida: {session_path}") from exc
    required = {
        "schema",
        "pipeline_version",
        "created_at",
        "nonce",
        "episode_slug",
        "source_fingerprint",
        "master_inputs_fingerprint",
        "source_lock_fingerprint",
        "expected_duration",
        "expected_output",
        "assembly_inputs",
        "session_fingerprint",
    }
    if not isinstance(data, dict) or not required.issubset(data):
        raise PipelineError(f"Sessão de montagem inválida: {session_path}")
    if data["schema"] != 1 or data["pipeline_version"] != PIPELINE_VERSION:
        raise PipelineError("Sessão de montagem usa schema/versão incompatível")
    try:
        created = datetime.fromisoformat(str(data["created_at"]))
        if created.tzinfo is None:
            raise ValueError("timezone ausente")
        age_seconds = (datetime.now(timezone.utc) - created).total_seconds()
    except (TypeError, ValueError) as exc:
        raise PipelineError("Data da sessão de montagem é inválida") from exc
    if not 0 <= age_seconds <= 6 * 60 * 60:
        raise PipelineError("Sessão de montagem expirou; monte o episódio novamente")
    if Path(str(data["expected_output"])).resolve() != output_path.resolve():
        raise PipelineError("Sessão de montagem pertence a outro arquivo de saída")
    if (
        data["episode_slug"] != episode.meta["SLUG"]
        or data["source_fingerprint"] != script_source_fingerprint(episode)
    ):
        raise PipelineError("Roteiro mudou depois que a sessão de montagem começou")
    source_lock, assembly = verify_assembly_lock(
        episode, session_path.parent / "source-lock.json"
    )
    if data["source_lock_fingerprint"] != source_lock["lock_fingerprint"]:
        raise PipelineError("Sessão de montagem pertence a outro lock de fontes")

    inputs = data["assembly_inputs"]
    if not isinstance(inputs, list) or len(inputs) != 3:
        raise PipelineError("Entradas da sessão de montagem são inválidas")
    for record in inputs:
        if (
            not isinstance(record, dict)
            or set(record) != {"label", "filename", "sha256"}
            or not all(isinstance(value, str) for value in record.values())
            or Path(record["filename"]).name != record["filename"]
        ):
            raise PipelineError("Entrada inválida no manifesto de montagem")
        source = session_path.parent / record["filename"]
        if not source.exists() or sha256_file(source) != record["sha256"]:
            raise PipelineError(
                f"Entrada da montagem mudou durante o render: {record['label']}"
            )

    expected_duration = float(assembly.metrics["duration_seconds"])
    try:
        stored_duration = float(data["expected_duration"])
    except (TypeError, ValueError) as exc:
        raise PipelineError("Duração da sessão de montagem é inválida") from exc
    if not math.isclose(
        stored_duration,
        expected_duration,
        rel_tol=0,
        abs_tol=0.001,
    ):
        raise PipelineError("Duração esperada mudou durante o render")
    if data["master_inputs_fingerprint"] != _master_inputs_fingerprint(episode):
        raise PipelineError("Dependências do episódio mudaram durante o render")

    fingerprint = data.pop("session_fingerprint")
    expected_fingerprint = _canonical_sha256(data)
    data["session_fingerprint"] = fingerprint
    if (
        not isinstance(fingerprint, str)
        or fingerprint != expected_fingerprint
    ):
        raise PipelineError("Fingerprint da sessão de montagem é inválido")
    return data, assembly


def master_session_fingerprint(info: dict[str, Any]) -> str:
    tags = (info.get("format") or {}).get("tags") or {}
    comment = tags.get("comment") if isinstance(tags, dict) else None
    match = re.fullmatch(r"geflix-session:([0-9a-f]{64})", str(comment or ""))
    return match.group(1) if match else ""


def commit_master_artifact(
    episode: Episode, source: Path, destination: Path
) -> None:
    source = source.resolve()
    destination = destination.resolve()
    expected_destination = (
        episode.root / f"{episode.meta['SLUG']}_final.mp4"
    ).resolve()
    if (
        source.parent != episode.root
        or not source.name.startswith(f".{episode.meta['SLUG']}_final.")
        or source.suffix.lower() != ".mp4"
        or destination != expected_destination
    ):
        raise PipelineError("Caminho inválido para commit do master")
    source_sidecar = metadata_path(source)
    destination_sidecar = metadata_path(destination)
    try:
        data = verify_recorded_output(source)
    except CacheError as exc:
        raise PipelineError(str(exc)) from exc
    if data.get("kind") != "episode-master" or not source_sidecar.exists():
        raise PipelineError("Master temporário não possui proveniência registrada")
    validation = validate_master(episode, source, require_provenance=True)
    if not validation.ok:
        raise PipelineError(
            "Master temporário reprovado antes do commit: "
            + "; ".join(validation.errors[:5])
        )

    token = secrets.token_hex(8)
    output_backup = episode.root / f".{destination.name}.{token}.bak"
    sidecar_backup = episode.root / f".{destination_sidecar.name}.{token}.bak"
    backed_output = False
    backed_sidecar = False
    moved_output = False
    moved_sidecar = False
    committed = False
    try:
        if destination.exists():
            os.replace(destination, output_backup)
            backed_output = True
        if destination_sidecar.exists():
            os.replace(destination_sidecar, sidecar_backup)
            backed_sidecar = True
        os.replace(source, destination)
        moved_output = True
        os.replace(source_sidecar, destination_sidecar)
        moved_sidecar = True
        verify_recorded_output(destination)
        committed = True
    except (OSError, CacheError) as exc:
        try:
            if moved_sidecar and destination_sidecar.exists():
                os.replace(destination_sidecar, source_sidecar)
            if moved_output and destination.exists():
                os.replace(destination, source)
            if backed_output and output_backup.exists():
                os.replace(output_backup, destination)
            if backed_sidecar and sidecar_backup.exists():
                os.replace(sidecar_backup, destination_sidecar)
        except OSError:
            pass
        raise PipelineError(f"Falha ao efetivar master; versão anterior restaurada: {exc}") from exc
    finally:
        if committed:
            output_backup.unlink(missing_ok=True)
            sidecar_backup.unlink(missing_ok=True)


def validate_master(
    episode: Episode, path: Path, require_provenance: bool = True
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.exists() or path.stat().st_size == 0:
        return ValidationResult(
            errors=[f"Master ausente ou vazio: {path}"],
            warnings=[],
            metrics={},
        )

    info = ffprobe_info(path)
    session_fingerprint = master_session_fingerprint(info)
    format_name = str((info.get("format") or {}).get("format_name", ""))
    if path.suffix.lower() != ".mp4" or "mp4" not in format_name.split(","):
        errors.append(
            f"Master precisa ser container MP4 real; formato recebido '{format_name}'"
        )
    streams = info.get("streams") or []
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
    others = [
        stream
        for stream in streams
        if stream.get("codec_type") not in {"video", "audio"}
    ]
    if len(videos) != 1:
        errors.append("Master precisa ter exatamente um stream de vídeo")
    if len(audios) != 1:
        errors.append("Master precisa ter exatamente um stream de áudio")
    if others:
        errors.append("Master contém streams extras não permitidos")

    try:
        duration = float((info.get("format") or {}).get("duration", 0))
    except ValueError:
        duration = 0.0
    if not 285 <= duration <= 315:
        errors.append(
            f"Master dura {duration:.2f}s; obrigatório ficar entre 285 e 315s"
        )

    if videos:
        video = videos[0]
        expected_size = (1920, 1080)
        if (video.get("width"), video.get("height")) != expected_size:
            errors.append(
                f"Master deve ser 1920x1080; recebido "
                f"{video.get('width')}x{video.get('height')}"
            )
        if video.get("codec_name") != "h264":
            errors.append("Master deve usar vídeo H.264")
        try:
            fps = float(Fraction(video.get("r_frame_rate", "0/1")))
        except (ValueError, ZeroDivisionError):
            fps = 0.0
        if not math.isclose(fps, 24.0, rel_tol=0, abs_tol=0.02):
            errors.append(f"Master deve usar 24 fps; recebido {fps:.3f}")

    if audios:
        audio = audios[0]
        if audio.get("codec_name") != "aac":
            errors.append("Master deve usar áudio AAC")
        if str(audio.get("sample_rate")) != "48000":
            errors.append("Master deve usar áudio em 48 kHz")
        if int(audio.get("channels") or 0) != 2:
            errors.append("Master deve usar áudio estéreo")

    integrated = 0.0
    true_peak = 0.0
    if audios:
        try:
            integrated, true_peak = analyze_loudness(path)
            if not -15.5 <= integrated <= -12.5:
                errors.append(
                    f"Loudness integrado {integrated:.1f} LUFS; esperado -15.5 a -12.5"
                )
            if true_peak > -1.0:
                errors.append(
                    f"True peak {true_peak:.1f} dBFS; precisa ser no máximo -1.0"
                )
        except PipelineError as exc:
            errors.append(str(exc))

    if require_provenance:
        assembly = validate_episode(episode, "assembly")
        errors.extend(
            f"Fontes do master: {error}" for error in assembly.errors
        )
        if assembly.ok:
            expected_duration = float(assembly.metrics["duration_seconds"])
            if not math.isclose(
                duration, expected_duration, rel_tol=0, abs_tol=1.5
            ):
                errors.append(
                    f"Master dura {duration:.3f}s, mas a timeline atual exige "
                    f"{expected_duration:.3f}s (tolerância 1.5s)"
                )
            if not session_fingerprint:
                errors.append("Master não contém uma sessão de montagem válida")
            else:
                valid, reason = cache_valid(
                    path,
                    "episode-master",
                    master_cache_values(
                        episode, session_fingerprint, expected_duration
                    ),
                    master_dependencies(episode),
                )
                if not valid:
                    errors.append(
                        f"Proveniência do master ausente ou obsoleta: {reason}"
                    )
    else:
        warnings.append(
            "Validação somente técnica; proveniência da montagem não foi verificada"
        )

    return ValidationResult(
        errors=list(dict.fromkeys(errors)),
        warnings=warnings,
        metrics={
            "path": str(path),
            "duration_seconds": duration,
            "width": videos[0].get("width") if videos else None,
            "height": videos[0].get("height") if videos else None,
            "loudness_lufs": integrated,
            "true_peak_dbfs": true_peak,
            "session_fingerprint": session_fingerprint or None,
            "validation_scope": (
                "technical-and-provenance" if require_provenance else "technical-only"
            ),
        },
    )


def print_validation(result: ValidationResult, as_json: bool = False) -> None:
    payload = {
        "ok": result.ok,
        "errors": result.errors,
        "warnings": result.warnings,
        "metrics": result.metrics,
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    metrics = result.metrics
    print(
        "QUALIDADE: "
        f"{metrics['scene_count']} cenas · "
        f"{metrics['duration_seconds']:.1f}s · "
        f"{metrics['distinct_voices']} vozes · "
        f"{metrics['dialogue_ratio']:.0%} diálogo · "
        f"{metrics['vfx_ratio']:.0%} VFX · "
        f"{metrics['sfx_ratio']:.0%} SFX"
    )
    for warning in result.warnings:
        print(f"AVISO: {warning}")
    for error in result.errors:
        print(f"ERRO: {error}", file=sys.stderr)
    print("APROVADO" if result.ok else "REPROVADO")


def command_validate(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        result = validate_episode(episode, args.stage)
    except PipelineError as exc:
        if args.json:
            print(
                json.dumps(
                    {"ok": False, "errors": [str(exc)], "warnings": [], "metrics": {}},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    print_validation(result, args.json)
    return 0 if result.ok else 1


def command_script(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        result = validate_episode(episode, "script")
        print_validation(result)
        if not result.ok:
            return 1
        output = Path(args.output) if args.output else episode.root / "roteiro.md"
        output.write_text(render_script(episode, result), encoding="utf-8")
        print(f"ROTEIRO: {output}")
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_duration(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        scene = next(
            (row for row in episode.scenes if row["id"] == args.scene), None
        )
        if scene is None:
            raise PipelineError(f"Cena desconhecida: {args.scene}")
        if args.actual:
            seconds = actual_scene_seconds(episode, scene)
        else:
            seconds = estimated_scene_seconds(
                scene, meta_float(episode.meta, "WORDS_PER_MINUTE", 138)
            )
        # Seis casas evitam que o shell transforme valores como 6.675188 em
        # 6.675 e altere o arredondamento do fingerprint de SFX.
        print(f"{seconds:.6f}")
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_env(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        for key, value in episode.meta.items():
            if "\t" in value or "\n" in value or "\r" in value:
                raise PipelineError(f"meta.env: valor inseguro em {key}")
            print(f"{key}\t{value}")
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_rows(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        structural = validate_episode(episode, "script")
        if not structural.ok:
            raise PipelineError(
                "TSV reprovado; corrija ./validate.sh script antes de gerar mídia"
            )
        if args.table == "scenes":
            fields = SCENE_FIELDS
            rows = episode.scenes
        else:
            fields = CHARACTER_FIELDS
            rows = episode.characters
        for row in rows:
            print("\t".join(row[field] for field in fields))
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_signature(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        scene = next(
            (row for row in episode.scenes if row["id"] == args.scene), None
        )
        if scene is None:
            raise PipelineError(f"Cena desconhecida: {args.scene}")
        print(media_source_signature(episode, scene, args.media))
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_prompt(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        scene = next(
            (row for row in episode.scenes if row["id"] == args.scene), None
        )
        if scene is None:
            raise PipelineError(f"Cena desconhecida: {args.scene}")
        print(frame_prompt(episode, scene) if args.media == "frame" else clip_prompt(episode, scene))
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_media(args: argparse.Namespace) -> int:
    try:
        metrics = validate_visual_media(
            Path(args.path).expanduser().resolve(), args.kind
        )
        if args.json:
            print(json.dumps(metrics, ensure_ascii=False, indent=2))
        else:
            print(
                f"OK: {args.kind} {metrics['width']}x{metrics['height']}"
                + (
                    f" · {metrics['duration_seconds']:.2f}s"
                    if "duration_seconds" in metrics
                    else ""
                )
            )
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_reference(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        character = episode.cast.get(args.key)
        if character is None:
            raise PipelineError(f"Personagem desconhecido: {args.key}")
        if character["sheet_prompt"] == "-":
            raise PipelineError(f"Personagem '{args.key}' não possui referência visual")
        if args.field == "prompt":
            print(reference_prompt(episode, character))
        else:
            print(reference_source_signature(episode, character))
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_voice_test_text(_: argparse.Namespace) -> int:
    print(VOICE_TEST_TEXT)
    return 0


def command_approve_voice(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        approval = approve_voice(episode, args.voice)
        print(
            f"APROVADA: {args.voice} · voice_id {approval['voice_id']} · "
            f"fingerprint {approval['fingerprint']}"
        )
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_approve_script(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        approval = approve_script(
            episode,
            confirm_ambiguous_pt_br=args.confirm_ambiguous_pt_br,
        )
        print(
            "ROTEIRO APROVADO: "
            f"fingerprint {approval['source_fingerprint']}"
        )
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_approve_visual(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        approval = approve_visual(episode, args.kind, args.identifier)
        print(
            f"VISUAL APROVADO: {args.kind} {args.identifier} · "
            f"fingerprint {approval['fingerprint']}"
        )
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_verify_visual(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        verify_visual_approval(episode, args.kind, args.identifier)
        print(f"APROVAÇÃO VÁLIDA: {args.kind} {args.identifier}")
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_approve_music(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        approval = approve_music(episode)
        print(
            f"TRILHA APROVADA: {approval['source']} · "
            f"fingerprint {approval['fingerprint']}"
        )
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_verify_music(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        verify_music_approval(episode)
        print("APROVAÇÃO VÁLIDA: trilha")
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_assembly_session(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        session = create_assembly_session(
            episode,
            Path(args.source_lock).expanduser().resolve(),
            Path(args.session).expanduser().resolve(),
            Path(args.timeline).expanduser().resolve(),
            Path(args.video).expanduser().resolve(),
            Path(args.audio).expanduser().resolve(),
            Path(args.output).expanduser().resolve(),
        )
        print(session["session_fingerprint"])
        return 0
    except (PipelineError, CacheError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_assembly_lock(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        lock = create_assembly_lock(
            episode, Path(args.path).expanduser().resolve()
        )
        print(lock["lock_fingerprint"])
        return 0
    except (PipelineError, CacheError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_commit_master(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        commit_master_artifact(
            episode,
            Path(args.source).expanduser().resolve(),
            Path(args.destination).expanduser().resolve(),
        )
        print(f"MASTER EFETIVADO: {Path(args.destination).expanduser().resolve()}")
        return 0
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_master(args: argparse.Namespace) -> int:
    try:
        episode = load_episode(Path(args.episode))
        path = Path(args.path).expanduser().resolve()
        result = validate_master(
            episode, path, require_provenance=not args.technical_only and not args.record
        )
        if args.record and result.ok:
            if not args.session:
                raise PipelineError(
                    "--record exige --session criada pelo assemble.sh"
                )
            session, assembly = verify_assembly_session(
                episode, Path(args.session).expanduser().resolve(), path
            )
            session_fingerprint = str(session["session_fingerprint"])
            if result.metrics.get("session_fingerprint") != session_fingerprint:
                raise PipelineError(
                    "Master não contém o fingerprint da sessão de montagem"
                )
            expected_duration = float(assembly.metrics["duration_seconds"])
            if not math.isclose(
                float(result.metrics["duration_seconds"]),
                expected_duration,
                rel_tol=0,
                abs_tol=1.5,
            ):
                raise PipelineError(
                    "Duração do master diverge da timeline da sessão"
                )
            cache_data = record_cache(
                path,
                "episode-master",
                master_cache_values(
                    episode, session_fingerprint, expected_duration
                ),
                master_dependencies(episode),
            )
            result.metrics["provenance_fingerprint"] = cache_data["fingerprint"]
            result.metrics["validation_scope"] = "technical-and-provenance"
            result.warnings = []
    except (PipelineError, CacheError) as exc:
        result = ValidationResult(errors=[str(exc)], warnings=[], metrics={})

    payload = {
        "ok": result.ok,
        "errors": result.errors,
        "warnings": result.warnings,
        "metrics": result.metrics,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for error in result.errors:
            print(f"ERRO: {error}", file=sys.stderr)
        if result.ok:
            metrics = result.metrics
            print(
                f"MASTER APROVADO: {metrics['duration_seconds']:.2f}s · "
                f"{metrics['width']}x{metrics['height']} · "
                f"{metrics['loudness_lufs']:.1f} LUFS · "
                f"{metrics['true_peak_dbfs']:.1f} dBFS"
            )
        else:
            print("MASTER REPROVADO", file=sys.stderr)
    return 0 if result.ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="executa gates de qualidade")
    validate.add_argument("--episode", required=True)
    validate.add_argument(
        "--stage",
        choices=["script", "production", "audio", "produced-audio", "assembly"],
        default="script",
    )
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(func=command_validate)

    script = subparsers.add_parser("script", help="gera roteiro.md após validação")
    script.add_argument("--episode", required=True)
    script.add_argument("--output")
    script.set_defaults(func=command_script)

    duration = subparsers.add_parser("duration", help="retorna duração de uma cena")
    duration.add_argument("--episode", required=True)
    duration.add_argument("--scene", required=True)
    duration.add_argument("--actual", action="store_true")
    duration.set_defaults(func=command_duration)

    env = subparsers.add_parser("env", help="emite meta.env parseado com segurança")
    env.add_argument("--episode", required=True)
    env.set_defaults(func=command_env)

    rows = subparsers.add_parser("rows", help="emite linhas TSV normalizadas")
    rows.add_argument("--episode", required=True)
    rows.add_argument("--table", choices=["characters", "scenes"], required=True)
    rows.set_defaults(func=command_rows)

    signature = subparsers.add_parser(
        "signature", help="calcula assinatura da fonte visual"
    )
    signature.add_argument("--episode", required=True)
    signature.add_argument("--scene", required=True)
    signature.add_argument("--media", choices=["frame", "clip"], required=True)
    signature.set_defaults(func=command_signature)

    prompt = subparsers.add_parser(
        "prompt", help="emite o prompt visual canônico"
    )
    prompt.add_argument("--episode", required=True)
    prompt.add_argument("--scene", required=True)
    prompt.add_argument("--media", choices=["frame", "clip"], required=True)
    prompt.set_defaults(func=command_prompt)

    media = subparsers.add_parser(
        "media", help="valida resolução, proporção e streams visuais"
    )
    media.add_argument("--path", required=True)
    media.add_argument(
        "--kind", choices=["reference", "frame", "clip"], required=True
    )
    media.add_argument("--json", action="store_true")
    media.set_defaults(func=command_media)

    reference = subparsers.add_parser(
        "reference", help="emite prompt ou assinatura de personagem"
    )
    reference.add_argument("--episode", required=True)
    reference.add_argument("--key", required=True)
    reference.add_argument("--field", choices=["prompt", "signature"], required=True)
    reference.set_defaults(func=command_reference)

    voice_text = subparsers.add_parser(
        "voice-test-text", help="emite frase canônica de audição"
    )
    voice_text.set_defaults(func=command_voice_test_text)

    approve = subparsers.add_parser(
        "approve-voice", help="vincula aprovação à amostra ouvida"
    )
    approve.add_argument("--episode", required=True)
    approve.add_argument("--voice", required=True)
    approve.set_defaults(func=command_approve_voice)

    approve_story = subparsers.add_parser(
        "approve-script", help="vincula aprovação às fontes do roteiro"
    )
    approve_story.add_argument("--episode", required=True)
    approve_story.add_argument(
        "--confirm-ambiguous-pt-br",
        action="store_true",
        help="confirma manualmente as falas marcadas como linguisticamente ambíguas",
    )
    approve_story.set_defaults(func=command_approve_script)

    approve_visual_parser = subparsers.add_parser(
        "approve-visual", help="vincula aprovação a um artefato visual"
    )
    approve_visual_parser.add_argument("--episode", required=True)
    approve_visual_parser.add_argument(
        "--kind", choices=["reference", "frame", "clip"], required=True
    )
    approve_visual_parser.add_argument("--identifier", required=True)
    approve_visual_parser.set_defaults(func=command_approve_visual)

    verify_visual_parser = subparsers.add_parser(
        "verify-visual", help="verifica aprovação visual vinculada"
    )
    verify_visual_parser.add_argument("--episode", required=True)
    verify_visual_parser.add_argument(
        "--kind", choices=["reference", "frame", "clip"], required=True
    )
    verify_visual_parser.add_argument("--identifier", required=True)
    verify_visual_parser.set_defaults(func=command_verify_visual)

    approve_music_parser = subparsers.add_parser(
        "approve-music", help="vincula aprovação à trilha ouvida"
    )
    approve_music_parser.add_argument("--episode", required=True)
    approve_music_parser.set_defaults(func=command_approve_music)

    verify_music_parser = subparsers.add_parser(
        "verify-music", help="verifica a aprovação vinculada da trilha"
    )
    verify_music_parser.add_argument("--episode", required=True)
    verify_music_parser.set_defaults(func=command_verify_music)

    assembly_lock = subparsers.add_parser(
        "assembly-lock", help="bloqueia as fontes antes de criar stems"
    )
    assembly_lock.add_argument("--episode", required=True)
    assembly_lock.add_argument("--path", required=True)
    assembly_lock.set_defaults(func=command_assembly_lock)

    assembly_session = subparsers.add_parser(
        "assembly-session", help="abre uma sessão vinculada aos stems da montagem"
    )
    assembly_session.add_argument("--episode", required=True)
    assembly_session.add_argument("--source-lock", required=True)
    assembly_session.add_argument("--session", required=True)
    assembly_session.add_argument("--timeline", required=True)
    assembly_session.add_argument("--video", required=True)
    assembly_session.add_argument("--audio", required=True)
    assembly_session.add_argument("--output", required=True)
    assembly_session.set_defaults(func=command_assembly_session)

    commit_master = subparsers.add_parser(
        "commit-master", help="efetiva master e proveniência com rollback"
    )
    commit_master.add_argument("--episode", required=True)
    commit_master.add_argument("--source", required=True)
    commit_master.add_argument("--destination", required=True)
    commit_master.set_defaults(func=command_commit_master)

    master = subparsers.add_parser("master", help="valida o MP4 final")
    master.add_argument("--episode", required=True)
    master.add_argument("--path", required=True)
    master.add_argument("--json", action="store_true")
    master.add_argument("--session")
    master_mode = master.add_mutually_exclusive_group()
    master_mode.add_argument("--technical-only", action="store_true")
    master_mode.add_argument("--record", action="store_true")
    master.set_defaults(func=command_master)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
