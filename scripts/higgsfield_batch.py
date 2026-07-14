#!/usr/bin/env python3
"""Parallel Higgsfield image generation with a bounded in-flight window.

Submits up to N jobs at once via the `higgsfield` CLI (no --wait), polls
job status, downloads and normalizes results, and records cache metadata.
Logs in-flight counts to prove real parallelism.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from artifact_cache import cache_valid, record_cache
from episode_pipeline import (
    Episode,
    PipelineError,
    load_episode,
    meta_int,
    validate_visual_media,
    verify_visual_approval,
    visual_artifact_contract,
)

POLL_INTERVAL_SECONDS = 5.0
JOB_TIMEOUT_SECONDS = 12 * 60
MAX_ATTEMPTS = 3
VALID_KINDS = {"reference", "frame"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    raise PipelineError(
        "CLI Higgsfield não encontrada. Instale ou configure HIGGSFIELD_BIN."
    )


def require_higgsfield(episode: Episode) -> None:
    if episode.meta.get("GEN_PROVIDER") != "higgsfield":
        raise PipelineError(
            "Este comando exige GEN_PROVIDER=higgsfield em meta.env."
        )


def run_cli(binary: str, arguments: list[str]) -> str:
    completed = subprocess.run(
        [binary, *arguments, "--json"],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[-500:]
        raise PipelineError(f"CLI Higgsfield falhou: {detail}")
    return completed.stdout.strip()


def parse_json(raw: str, context: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PipelineError(
            f"Resposta Higgsfield não é JSON ({context}): {raw[:300]}"
        ) from exc


class BatchLogger:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.max_in_flight = 0

    def log(self, event: str, identifier: str, in_flight: int, extra: str = "") -> None:
        self.max_in_flight = max(self.max_in_flight, in_flight)
        line = (
            f"{utc_now()}\t{event}\t{identifier}\tin_flight={in_flight}"
            + (f"\t{extra}" if extra else "")
        )
        print(line, flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


class Task:
    def __init__(
        self,
        identifier: str,
        prompt: str,
        images: list[Path],
        aspect: str,
        resolution: str,
        output: Path,
        cache_kind: str,
        cache_values: dict[str, str],
        cache_dependencies: list[tuple[str, Path]],
        media_kind: str,
    ) -> None:
        self.identifier = identifier
        self.prompt = prompt
        self.images = images
        self.aspect = aspect
        self.resolution = resolution
        self.output = output
        self.cache_kind = cache_kind
        self.cache_values = cache_values
        self.cache_dependencies = cache_dependencies
        self.media_kind = media_kind
        self.attempts = 0
        self.job_id: str | None = None
        self.submitted_at: float | None = None


def available_identifiers(episode: Episode, kind: str) -> list[str]:
    if kind == "reference":
        return [
            character["key"]
            for character in episode.characters
            if character["sheet_prompt"] != "-"
        ]
    return [scene["id"] for scene in episode.scenes]


def select_identifiers(
    episode: Episode, kind: str, requested: list[str]
) -> list[str]:
    available = available_identifiers(episode, kind)
    if not requested or "all" in requested:
        return available
    unknown = sorted(set(requested) - set(available))
    if unknown:
        raise PipelineError(
            f"Identificadores desconhecidos para {kind}: {', '.join(unknown)}"
        )
    requested_set = set(requested)
    return [identifier for identifier in available if identifier in requested_set]


def build_task(episode: Episode, kind: str, identifier: str) -> Task:
    # Prompt construction reuses the shared pipeline (policies included).
    from episode_pipeline import frame_prompt, reference_prompt

    output, cache_kind, values, dependencies = visual_artifact_contract(
        episode, kind, identifier
    )
    if kind == "reference":
        character = episode.cast[identifier]
        prompt = reference_prompt(episode, character)
        aspect = episode.meta["REF_ASPECT"]
        images: list[Path] = []
    else:
        scene = next(row for row in episode.scenes if row["id"] == identifier)
        prompt = frame_prompt(episode, scene)
        aspect = episode.meta["ASPECT"]
        images = []
        if scene["refs"] != "-":
            for key in scene["refs"].split(","):
                verify_visual_approval(episode, "reference", key)
                ref = episode.root / "assets" / f"{key}_ref.png"
                if not ref.exists():
                    raise PipelineError(
                        f"Cena {identifier} precisa da referência ausente {ref}"
                    )
                images.append(ref)
    return Task(
        identifier=identifier,
        prompt=prompt,
        images=images,
        aspect=aspect,
        resolution=episode.meta["IMG_RES"],
        output=output,
        cache_kind=cache_kind,
        cache_values=values,
        cache_dependencies=dependencies,
        media_kind=kind,
    )


def submit(binary: str, task: Task) -> str:
    arguments = ["generate", "create", "nano_banana_2", "--prompt", task.prompt]
    for image in task.images:
        arguments.extend(["--image", str(image)])
    arguments.extend(
        ["--aspect_ratio", task.aspect, "--resolution", task.resolution]
    )
    raw = run_cli(binary, arguments)
    data = parse_json(raw, f"submit {task.identifier}")
    if isinstance(data, list) and data and isinstance(data[0], str):
        return data[0]
    if isinstance(data, dict) and isinstance(data.get("id"), str):
        return data["id"]
    raise PipelineError(
        f"Resposta de submissão sem job id para {task.identifier}: {raw[:300]}"
    )


def job_status(binary: str, job_id: str) -> dict[str, Any]:
    raw = run_cli(binary, ["generate", "get", job_id])
    data = parse_json(raw, f"get {job_id}")
    if not isinstance(data, dict):
        raise PipelineError(f"Status inesperado para job {job_id}: {raw[:300]}")
    return data


def result_url(data: dict[str, Any]) -> str:
    url = data.get("result_url")
    if isinstance(url, str) and url.startswith("http"):
        return url
    raise PipelineError(
        f"Job {data.get('id')} concluído sem result_url utilizável"
    )


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "curl",
            "--fail",
            "--silent",
            "--show-error",
            "--location",
            url,
            "--output",
            str(target),
        ],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or not target.exists() or target.stat().st_size == 0:
        raise PipelineError(
            f"Falha ao baixar resultado Higgsfield: {completed.stderr.strip()[:300]}"
        )


def normalize(task: Task, raw: Path) -> None:
    if task.media_kind == "reference":
        width, height = 1440, 1920
    else:
        width, height = 1920, 1080
    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1"
    )
    task.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = task.output.with_name(
        f".{task.output.stem}.higgs.tmp{task.output.suffix}"
    )
    temporary.unlink(missing_ok=True)
    completed = subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-i",
            str(raw),
            "-vf",
            video_filter,
            "-frames:v",
            "1",
            "-c:v",
            "png",
            str(temporary),
        ],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise PipelineError(
            f"Falha ao normalizar {task.identifier}: "
            f"{completed.stderr.strip()[-400:]}"
        )
    os.replace(temporary, task.output)


def finalize(episode: Episode, task: Task, status: dict[str, Any]) -> None:
    scratch = episode.root / "build" / "higgsfield"
    scratch.mkdir(parents=True, exist_ok=True)
    raw = scratch / f"{task.media_kind}-{task.identifier}.img"
    raw.unlink(missing_ok=True)
    download(result_url(status), raw)
    normalize(task, raw)
    validate_visual_media(task.output, task.media_kind)
    cache_data = record_cache(
        task.output, task.cache_kind, task.cache_values, task.cache_dependencies
    )
    provenance = {
        "schema": 1,
        "provider": "higgsfield-cli",
        "model": "nano_banana_2",
        "job_id": status.get("id", ""),
        "registered_at": utc_now(),
        "source_signature": task.cache_values.get("source_signature", ""),
        "output_sha256": cache_data["output_sha256"],
    }
    sidecar = Path(f"{task.output}.higgsfield.json")
    sidecar.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    raw.unlink(missing_ok=True)


def run_batch(
    episode: Episode,
    kind: str,
    identifiers: list[str],
    concurrency: int,
    force: bool,
    skip_blocked: bool,
) -> int:
    binary = find_higgsfield()
    logger = BatchLogger(
        episode.root / "logs" / f"higgsfield-batch-{kind}.log"
    )

    pending: list[Task] = []
    blocked: list[str] = []
    for identifier in select_identifiers(episode, kind, identifiers):
        try:
            task = build_task(episode, kind, identifier)
        except PipelineError as exc:
            if skip_blocked:
                blocked.append(f"{identifier}: {exc}")
                continue
            raise
        valid, reason = cache_valid(
            task.output,
            task.cache_kind,
            task.cache_values,
            task.cache_dependencies,
        )
        if valid and not force:
            print(f"= {kind} {identifier}: cache válido ({reason})")
            continue
        pending.append(task)

    for message in blocked:
        print(f"BLOQUEADO (pulado): {message}", file=sys.stderr)

    if not pending:
        print("Nada a gerar: todos os artefatos selecionados estão prontos.")
        return 0

    print(
        f"LOTE HIGGSFIELD: {len(pending)} {kind}(s), "
        f"concorrência máxima {concurrency}"
    )

    queue = list(pending)
    in_flight: dict[str, Task] = {}
    failures: list[str] = []
    completed_count = 0

    while queue or in_flight:
        while queue and len(in_flight) < concurrency:
            task = queue.pop(0)
            task.attempts += 1
            try:
                task.job_id = submit(binary, task)
            except PipelineError as exc:
                if task.attempts < MAX_ATTEMPTS:
                    queue.append(task)
                    logger.log(
                        "retry-submit",
                        task.identifier,
                        len(in_flight),
                        str(exc)[:200],
                    )
                    time.sleep(5 * task.attempts)
                else:
                    failures.append(f"{task.identifier}: {exc}")
                    logger.log(
                        "failed-submit",
                        task.identifier,
                        len(in_flight),
                        str(exc)[:200],
                    )
                continue
            task.submitted_at = time.monotonic()
            in_flight[task.job_id] = task
            logger.log("submitted", task.identifier, len(in_flight), task.job_id)

        if not in_flight:
            continue

        time.sleep(POLL_INTERVAL_SECONDS)
        for job_id in list(in_flight):
            task = in_flight[job_id]
            try:
                status = job_status(binary, job_id)
            except PipelineError as exc:
                logger.log("poll-error", task.identifier, len(in_flight), str(exc)[:160])
                continue
            state = str(status.get("status", ""))
            if state in {"queued", "in_progress", "pending", ""}:
                elapsed = time.monotonic() - (task.submitted_at or 0)
                if elapsed > JOB_TIMEOUT_SECONDS:
                    del in_flight[job_id]
                    if task.attempts < MAX_ATTEMPTS:
                        queue.append(task)
                        logger.log("timeout-retry", task.identifier, len(in_flight))
                    else:
                        failures.append(f"{task.identifier}: timeout")
                        logger.log("failed-timeout", task.identifier, len(in_flight))
                continue
            del in_flight[job_id]
            if state == "completed":
                try:
                    finalize(episode, task, status)
                except PipelineError as exc:
                    if task.attempts < MAX_ATTEMPTS:
                        queue.append(task)
                        logger.log(
                            "retry-finalize",
                            task.identifier,
                            len(in_flight),
                            str(exc)[:200],
                        )
                    else:
                        failures.append(f"{task.identifier}: {exc}")
                        logger.log(
                            "failed-finalize",
                            task.identifier,
                            len(in_flight),
                            str(exc)[:200],
                        )
                    continue
                completed_count += 1
                logger.log(
                    "completed",
                    task.identifier,
                    len(in_flight),
                    f"restam={len(queue)}",
                )
            else:
                if task.attempts < MAX_ATTEMPTS:
                    queue.append(task)
                    logger.log(
                        "retry-status",
                        task.identifier,
                        len(in_flight),
                        f"status={state}",
                    )
                else:
                    failures.append(f"{task.identifier}: status {state}")
                    logger.log(
                        "failed-status",
                        task.identifier,
                        len(in_flight),
                        f"status={state}",
                    )

    print(
        f"RESUMO: {completed_count} concluído(s), {len(failures)} falha(s), "
        f"pico de paralelismo observado: {logger.max_in_flight}"
    )
    for failure in failures:
        print(f"FALHA: {failure}", file=sys.stderr)
    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--kind", choices=sorted(VALID_KINDS), required=True)
    parser.add_argument("--concurrency", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--skip-blocked",
        action="store_true",
        help="pula tarefas bloqueadas por aprovações pendentes em vez de abortar",
    )
    parser.add_argument("identifiers", nargs="*")
    args = parser.parse_args()

    try:
        episode = load_episode(Path(args.episode))
        require_higgsfield(episode)
        concurrency = args.concurrency or meta_int(
            episode.meta, "HIGGS_CONCURRENCY", 8
        )
        if not 1 <= concurrency <= 16:
            raise PipelineError("Concorrência deve ficar entre 1 e 16")
        raise SystemExit(
            run_batch(
                episode,
                args.kind,
                args.identifiers,
                concurrency,
                args.force,
                args.skip_blocked,
            )
        )
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
