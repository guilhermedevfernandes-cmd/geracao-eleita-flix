#!/usr/bin/env python3
"""ElevenLabs audio generation for dialogue, SFX, and music."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib import error, request

from artifact_cache import CacheError, cache_valid, record_cache
from audio_contract import (
    MUSIC_JOB_TYPE,
    SFX_JOB_TYPE,
    TTS_JOB_TYPE,
    TTS_PROVIDER,
    music_values,
    sfx_values,
    tts_values,
)


API_BASE = os.environ.get("ELEVENLABS_API_BASE", "https://api.elevenlabs.io").rstrip("/")
TTS_MODEL = os.environ.get("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2")
TRANSIENT_MARKERS = (
    "http 429",
    "http 500",
    "http 502",
    "http 503",
    "http 504",
    "timeout",
    "temporarily unavailable",
    "connection reset",
)


class AudioGenerationError(RuntimeError):
    """Raised when an audio job cannot be completed safely."""


def load_dotenv_files() -> None:
    candidates = [
        Path.home() / ".config" / "gerecao-eleita-flix" / "elevenlabs.env",
        Path.cwd() / ".env",
        Path.cwd() / ".env.local",
    ]
    for path in candidates:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value


def api_key() -> str:
    load_dotenv_files()
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        raise AudioGenerationError(
            "ELEVENLABS_API_KEY não configurada. Exporte a variável ou grave em "
            "~/.config/gerecao-eleita-flix/elevenlabs.env"
        )
    return key


def is_transient(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in TRANSIENT_MARKERS)


def request_bytes(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    accept: str = "application/json",
    timeout: int = 300,
) -> bytes:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "xi-api-key": api_key(),
        "Accept": accept,
        "User-Agent": "gerecao-eleita-flix/2.2",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = request.Request(
        f"{API_BASE}{path}",
        data=data,
        method=method,
        headers=headers,
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AudioGenerationError(f"HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise AudioGenerationError(f"Falha de rede ElevenLabs: {exc}") from exc


def write_bytes_atomic(destination: Path, content: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=destination.parent,
        prefix=f".{destination.stem}.",
        suffix=destination.suffix,
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    try:
        if temporary.stat().st_size == 0:
            raise AudioGenerationError(f"Download vazio: {destination}")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def convert_to_target(source: Path, output: Path) -> None:
    if output.suffix.lower() == source.suffix.lower():
        if source.resolve() != output.resolve():
            output.write_bytes(source.read_bytes())
        return
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-y",
                "-i",
                str(source),
                "-vn",
                "-ar",
                "48000",
                "-ac",
                "2",
                str(output),
                "-loglevel",
                "error",
            ],
            check=True,
        )
    except FileNotFoundError as exc:
        raise AudioGenerationError("ffmpeg não está instalado") from exc
    except subprocess.CalledProcessError as exc:
        raise AudioGenerationError(
            f"Não foi possível converter áudio para {output}"
        ) from exc


def verify_audio(path: Path) -> None:
    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_type:format=duration",
                "-of",
                "json",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        data = json.loads(completed.stdout)
        streams = data.get("streams") or []
        duration = float((data.get("format") or {}).get("duration", 0))
        if not streams or duration <= 0.1:
            raise AudioGenerationError(f"Áudio inválido ou curto demais: {path}")
    except FileNotFoundError as exc:
        raise AudioGenerationError("ffprobe não está instalado") from exc
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as exc:
        raise AudioGenerationError(f"Áudio não decodificável: {path}") from exc


def with_retries(label: str, retries: int, fn) -> bytes:
    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except AudioGenerationError as exc:
            last_error = str(exc)
            if attempt == retries or not is_transient(last_error):
                raise
            delay = 2 ** (attempt - 1)
            print(
                f"{label}: tentativa {attempt} falhou; repetindo em {delay}s...",
                file=sys.stderr,
            )
            time.sleep(delay)
    raise AudioGenerationError(last_error or f"Falha em {label}")


def generate_tts(text: str, voice_id: str) -> bytes:
    return request_bytes(
        "POST",
        f"/v1/text-to-speech/{voice_id}",
        {
            "text": text,
            "model_id": TTS_MODEL,
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.8,
                "style": 0.15,
                "use_speaker_boost": True,
            },
        },
        accept="audio/mpeg",
    )


def generate_sfx(prompt: str, duration: float) -> bytes:
    clamped = max(0.5, min(float(duration), 22.0))
    return request_bytes(
        "POST",
        "/v1/sound-generation",
        {
            "text": prompt,
            "duration_seconds": clamped,
            "prompt_influence": 0.35,
        },
        accept="audio/mpeg",
    )


def generate_music(prompt: str, duration: float) -> bytes:
    # ElevenLabs music accepts length in milliseconds; keep a safe upper bound.
    length_ms = int(max(10.0, min(float(duration), 180.0)) * 1000)
    return request_bytes(
        "POST",
        "/v1/music",
        {
            "prompt": prompt,
            "music_length_ms": length_ms,
            "force_instrumental": True,
        },
        accept="audio/mpeg",
        timeout=600,
    )


def create_audio(
    args: argparse.Namespace,
    model: str,
    values: dict[str, str],
    producer,
) -> int:
    output = Path(args.out).expanduser().resolve()
    kind = f"elevenlabs-audio:{model}"
    if not args.force:
        valid, reason = cache_valid(output, kind, values, [])
        if valid:
            print(f"CACHE: {output}")
            return 0
        if output.exists():
            print(f"STALE: {output} ({reason}); regenerando.")

    if args.dry_run:
        print(f"DRY_RUN: elevenlabs {model} → {output}")
        return 0

    try:
        payload = with_retries(model, args.retries, producer)
        with tempfile.TemporaryDirectory(prefix="geflix-el-") as temporary:
            raw = Path(temporary) / "source.mp3"
            raw.write_bytes(payload)
            converted = Path(temporary) / f"converted{output.suffix}"
            convert_to_target(raw, converted)
            verify_audio(converted)
            write_bytes_atomic(output, converted.read_bytes())
        record_cache(output, kind, values, [])
        print(f"GERADO: {output}")
        return 0
    except (AudioGenerationError, CacheError, OSError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_tts(args: argparse.Namespace) -> int:
    if not args.text.strip():
        print("ERRO: texto de dublagem vazio", file=sys.stderr)
        return 1
    values = tts_values(args.text, args.voice_id, args.provider)
    return create_audio(
        args,
        TTS_JOB_TYPE,
        values,
        lambda: generate_tts(args.text, args.voice_id),
    )


def command_sfx(args: argparse.Namespace) -> int:
    values = sfx_values(args.prompt, args.duration)
    return create_audio(
        args,
        SFX_JOB_TYPE,
        values,
        lambda: generate_sfx(values["prompt"], args.duration),
    )


def command_music(args: argparse.Namespace) -> int:
    values = music_values(args.prompt, args.duration)
    return create_audio(
        args,
        MUSIC_JOB_TYPE,
        values,
        lambda: generate_music(values["prompt"], args.duration),
    )


def add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--out", required=True)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    tts = subparsers.add_parser("tts", help="gera uma fala")
    add_common_flags(tts)
    tts.add_argument("--text", required=True)
    tts.add_argument("--voice-id", required=True)
    tts.add_argument("--provider", default=TTS_PROVIDER)
    tts.set_defaults(func=command_tts)

    sfx = subparsers.add_parser("sfx", help="gera ambiência e efeitos")
    add_common_flags(sfx)
    sfx.add_argument("--prompt", required=True)
    sfx.add_argument("--duration", required=True, type=float)
    sfx.set_defaults(func=command_sfx)

    music = subparsers.add_parser("music", help="gera trilha instrumental")
    add_common_flags(music)
    music.add_argument("--prompt", required=True)
    music.add_argument("--duration", required=True, type=float)
    music.set_defaults(func=command_music)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
