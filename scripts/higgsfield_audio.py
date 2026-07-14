#!/usr/bin/env python3
"""Reliable Higgsfield audio generation for dialogue, SFX, and music."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib import parse, request

from artifact_cache import CacheError, cache_valid, record_cache
from audio_contract import (
    MUSIC_JOB_TYPE,
    SFX_JOB_TYPE,
    TTS_JOB_TYPE,
    music_values,
    sfx_values,
    tts_values,
)


URL_RE = re.compile(r"https://[^\s\"']+")
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


def find_higgsfield() -> str:
    configured = os.environ.get("HIGGSFIELD_BIN")
    if configured:
        return configured
    found = shutil.which("higgsfield") or shutil.which("higgs")
    if found:
        return found
    homebrew = Path("/opt/homebrew/bin/higgsfield")
    if homebrew.exists():
        return str(homebrew)
    raise AudioGenerationError(
        "CLI Higgsfield não encontrada. Instale ou configure HIGGSFIELD_BIN."
    )


def nested_urls(value: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(value, dict):
        priority_keys = ("result_url", "url", "result_urls", "urls", "outputs")
        for key in priority_keys:
            if key in value:
                urls.extend(nested_urls(value[key]))
        for key, nested in value.items():
            if key not in priority_keys:
                urls.extend(nested_urls(nested))
    elif isinstance(value, list):
        for nested in value:
            urls.extend(nested_urls(nested))
    elif isinstance(value, str) and value.startswith("http"):
        urls.append(value)
    return urls


def parse_result_url(stdout: str) -> str:
    stripped = stdout.strip()
    candidates: list[Any] = []
    try:
        candidates.append(json.loads(stripped))
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(stripped):
            if char not in "[{":
                continue
            try:
                parsed, _ = decoder.raw_decode(stripped[index:])
                candidates.append(parsed)
                break
            except json.JSONDecodeError:
                continue

    for candidate in candidates:
        for url in nested_urls(candidate):
            if re.search(r"\.(mp3|wav|ogg|m4a)(?:\?|$)", url, re.IGNORECASE):
                return url

    for url in URL_RE.findall(stripped):
        cleaned = url.rstrip(".,)]}")
        if re.search(r"\.(mp3|wav|ogg|m4a)(?:\?|$)", cleaned, re.IGNORECASE):
            return cleaned

    raise AudioGenerationError(
        "A geração terminou sem URL de áudio reconhecível. "
        f"Saída final: {stripped[-500:]}"
    )


def is_transient(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in TRANSIENT_MARKERS)


def run_job(
    model: str,
    params: list[tuple[str, str]],
    timeout: str,
    retries: int,
    dry_run: bool,
) -> str:
    command = [find_higgsfield(), "generate", "create", model]
    for name, value in params:
        command.extend([f"--{name}", value])
    command.extend(["--wait", "--wait-timeout", timeout, "--json"])

    if dry_run:
        safe_command = [
            "<texto>" if token in {value for name, value in params if name == "prompt"} else token
            for token in command
        ]
        print("DRY_RUN:", shlex_join(safe_command))
        return "https://example.invalid/dry-run.mp3"

    for attempt in range(1, retries + 1):
        completed = subprocess.run(command, capture_output=True, text=True)
        combined = "\n".join(
            part for part in (completed.stdout, completed.stderr) if part
        ).strip()
        if completed.returncode == 0:
            return parse_result_url(combined)

        if attempt == retries or not is_transient(combined):
            raise AudioGenerationError(
                f"Higgsfield falhou após {attempt} tentativa(s): {combined[-1000:]}"
            )
        delay = 2 ** (attempt - 1)
        print(
            f"Tentativa {attempt} falhou temporariamente; repetindo em {delay}s...",
            file=sys.stderr,
        )
        time.sleep(delay)

    raise AudioGenerationError("Falha inesperada ao executar geração")


def shlex_join(parts: list[str]) -> str:
    import shlex

    return shlex.join(parts)


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    user_agent = {"User-Agent": "gerecao-eleita-flix/2.0"}
    with request.urlopen(request.Request(url, headers=user_agent), timeout=300) as response:
        with destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)
    if destination.stat().st_size == 0:
        raise AudioGenerationError(f"Download vazio: {url}")


def download_audio(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    url_suffix = Path(parse.urlparse(url).path).suffix.lower() or ".audio"
    with tempfile.TemporaryDirectory(prefix="geflix-audio-") as temporary:
        raw = Path(temporary) / f"source{url_suffix}"
        download(url, raw)

        if output.suffix.lower() == url_suffix:
            shutil.copy2(raw, output)
            return

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(raw),
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


def create_audio(
    args: argparse.Namespace, model: str, params: list[tuple[str, str]]
) -> int:
    output = Path(args.out).expanduser().resolve()
    values = {name: value for name, value in params}
    kind = f"higgsfield-audio:{model}"
    if not args.force:
        valid, reason = cache_valid(output, kind, values, [])
        if valid:
            print(f"CACHE: {output}")
            return 0
        if output.exists():
            print(f"STALE: {output} ({reason}); regenerando.")

    try:
        url = run_job(
            model=model,
            params=params,
            timeout=args.timeout,
            retries=args.retries,
            dry_run=args.dry_run,
        )
        if args.dry_run:
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=output.parent,
            prefix=f".{output.stem}.",
            suffix=output.suffix,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
        try:
            download_audio(url, temporary)
            verify_audio(temporary)
            os.replace(temporary, output)
        finally:
            temporary.unlink(missing_ok=True)
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
    return create_audio(
        args,
        TTS_JOB_TYPE,
        list(tts_values(args.text, args.voice_id, args.provider).items()),
    )


def command_sfx(args: argparse.Namespace) -> int:
    return create_audio(
        args,
        SFX_JOB_TYPE,
        list(sfx_values(args.prompt, args.duration).items()),
    )


def command_music(args: argparse.Namespace) -> int:
    return create_audio(
        args,
        MUSIC_JOB_TYPE,
        list(music_values(args.prompt, args.duration).items()),
    )


def add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--out", required=True)
    parser.add_argument("--timeout", default="10m")
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
    tts.add_argument("--provider", default="elevenlabs")
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
