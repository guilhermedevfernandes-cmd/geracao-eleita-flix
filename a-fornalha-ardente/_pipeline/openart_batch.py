#!/usr/bin/env python3
"""Bridge between episode manifests and Cursor's OAuth-authenticated OpenArt MCP."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request

from artifact_cache import cache_valid, record_cache, sha256_file
from episode_pipeline import (
    Episode,
    PipelineError,
    clip_prompt,
    configured_image_model,
    configured_video_model,
    frame_prompt,
    load_episode,
    meta_int,
    reference_prompt,
    validate_clip_story_capacity,
    validate_visual_media,
    verify_visual_approval,
    visual_artifact_contract,
)


MANIFEST_SCHEMA = 1
RESULT_SCHEMA = 1
VALID_KINDS = {"reference", "frame", "clip"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
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


def canonical_hash(data: Any) -> str:
    payload = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def manifest_path(episode: Episode, kind: str) -> Path:
    return episode.root / "build" / "openart" / f"{kind}-batch.json"


def results_path(episode: Episode, kind: str) -> Path:
    return episode.root / "build" / "openart" / f"{kind}-results.json"


def require_openart(episode: Episode) -> None:
    if episode.meta.get("GEN_PROVIDER") != "openart":
        raise PipelineError(
            "Este comando exige GEN_PROVIDER=openart; providers antigos são "
            "aceitos apenas para reproduzir episódios legados."
        )


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


def relative_to_episode(episode: Episode, path: Path) -> str:
    return str(path.resolve().relative_to(episode.root))


def input_record(episode: Episode, role: str, path: Path) -> dict[str, str]:
    if not path.exists() or not path.is_file():
        raise PipelineError(f"Entrada OpenArt ausente: {path}")
    return {
        "role": role,
        "path": str(path.resolve()),
        "relative_path": relative_to_episode(episode, path),
        "sha256": sha256_file(path),
    }


def verify_upstream(episode: Episode, kind: str, identifier: str) -> None:
    if kind == "frame":
        scene = next(row for row in episode.scenes if row["id"] == identifier)
        if scene["refs"] != "-":
            for key in scene["refs"].split(","):
                verify_visual_approval(episode, "reference", key)
    elif kind == "clip":
        verify_visual_approval(episode, "frame", identifier)


def build_task(
    episode: Episode, kind: str, identifier: str
) -> tuple[dict[str, Any], bool, str]:
    verify_upstream(episode, kind, identifier)
    output, cache_kind, values, dependencies = visual_artifact_contract(
        episode, kind, identifier
    )
    valid, cache_reason = cache_valid(output, cache_kind, values, dependencies)

    if kind == "reference":
        character = episode.cast[identifier]
        prompt = reference_prompt(episode, character)
        model = configured_image_model(episode)
        operation = "text_to_image"
        parameters: dict[str, Any] = {
            "aspect_ratio": episode.meta["REF_ASPECT"],
            "resolution": episode.meta["IMG_RES"].upper(),
            "variations": 1,
        }
        inputs: list[dict[str, str]] = []
    else:
        scene = next(row for row in episode.scenes if row["id"] == identifier)
        if kind == "frame":
            prompt = frame_prompt(episode, scene)
            model = configured_image_model(episode)
            parameters = {
                "aspect_ratio": episode.meta["ASPECT"],
                "resolution": episode.meta["IMG_RES"].upper(),
                "variations": 1,
            }
            inputs = []
            if scene["refs"] != "-":
                inputs = [
                    input_record(
                        episode,
                        f"character_reference:{key}",
                        episode.root / "assets" / f"{key}_ref.png",
                    )
                    for key in scene["refs"].split(",")
                ]
            operation = (
                "reference_image_generation" if inputs else "text_to_image"
            )
        else:
            prompt = clip_prompt(episode, scene)
            model = configured_video_model(episode)
            operation = "image_to_video"
            # OpenArt Kling Omni: 720p→std, 1080p→pro
            openart_resolution = {
                "720p": "std",
                "1080p": "pro",
            }.get(episode.meta.get("VIDEO_RES", "1080p"), "pro")
            parameters = {
                "aspect_ratio": episode.meta["ASPECT"],
                "resolution": openart_resolution,
                "duration_seconds": int(episode.meta["VIDEO_DUR"]),
                "generate_audio": False,
                "variations": 1,
            }
            inputs = [
                input_record(
                    episode,
                    "start_frame",
                    episode.root / "frames" / f"{identifier}.png",
                )
            ]

    task = {
        "task_id": f"{kind}:{identifier}",
        "identifier": identifier,
        "media_kind": kind,
        "operation": operation,
        "model": model,
        "prompt": prompt,
        "parameters": parameters,
        "inputs": inputs,
        "output": {
            "path": str(output.resolve()),
            "relative_path": relative_to_episode(episode, output),
        },
        "source_signature": values["source_signature"],
        "cache": {
            "kind": cache_kind,
            "dependencies": [
                {
                    "label": label,
                    "path": str(path.resolve()),
                    "sha256": sha256_file(path),
                }
                for label, path in dependencies
            ],
        },
    }
    return task, valid, cache_reason


def build_manifest(
    episode: Episode,
    kind: str,
    requested: list[str],
    force: bool,
) -> dict[str, Any]:
    require_openart(episode)
    tasks: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for identifier in select_identifiers(episode, kind, requested):
        task, valid, reason = build_task(episode, kind, identifier)
        if valid and not force:
            skipped.append({"identifier": identifier, "reason": reason})
        else:
            tasks.append(task)

    stable = {
        "schema": MANIFEST_SCHEMA,
        "provider": "openart-mcp",
        "server": episode.meta["OPENART_MCP_SERVER"],
        "episode": {
            "slug": episode.meta["SLUG"],
            "title": episode.meta["TITLE"],
            "root": str(episode.root),
            "project": episode.meta["SLUG"],
            "project_id": episode.meta.get("OPENART_PROJECT_ID", ""),
        },
        "media_kind": kind,
        "max_concurrency": meta_int(
            episode.meta, "OPENART_CONCURRENCY", 8
        ),
        "tasks": tasks,
        "skipped": skipped,
    }
    stable["batch_id"] = canonical_hash(stable)
    stable["created_at"] = utc_now()
    stable["agent_contract"] = {
        "execution": "parallel_mcp_tool_calls",
        "instructions": [
            "Use exclusivamente o MCP OpenArt autenticado via OAuth no Cursor.",
            "Descubra os modelos disponíveis e resolva os nomes do manifesto.",
            "Crie ou selecione o projeto OpenArt com o slug do episódio.",
            "Envie tarefas independentes em paralelo até max_concurrency.",
            "Use todos os inputs como referências; clip usa start_frame.",
            "Não gere áudio nos vídeos.",
            "Salve cada resultado no output.path correspondente.",
            f"Depois rode ./register-openart.sh {kind} all.",
        ],
        "normalized_results_path": str(results_path(episode, kind)),
    }
    return stable


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise PipelineError(f"{label} ausente: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"{label} inválido: {path}") from exc
    if not isinstance(data, dict):
        raise PipelineError(f"{label} precisa ser um objeto JSON: {path}")
    return data


def load_manifest(path: Path) -> dict[str, Any]:
    data = load_json_object(path, "Manifesto OpenArt")
    if (
        data.get("schema") != MANIFEST_SCHEMA
        or data.get("provider") != "openart-mcp"
        or not isinstance(data.get("tasks"), list)
    ):
        raise PipelineError(f"Manifesto OpenArt incompatível: {path}")
    return data


def load_results(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = load_json_object(path, "Resultados OpenArt")
    if data.get("schema") != RESULT_SCHEMA:
        raise PipelineError(f"Resultados OpenArt incompatíveis: {path}")
    rows = data.get("results")
    if not isinstance(rows, list):
        raise PipelineError(f"Resultados OpenArt sem lista 'results': {path}")
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("task_id"), str):
            raise PipelineError(f"Resultado OpenArt malformado: {path}")
        indexed[row["task_id"]] = row
    return indexed


def safe_download(url: str, target: Path) -> None:
    parsed = parse.urlparse(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise PipelineError(f"URL de resultado OpenArt inválida: {url}")
    req = request.Request(url, headers={"User-Agent": "gerecao-eleita-flix/2.2"})
    try:
        with request.urlopen(req, timeout=600) as response:
            with target.open("wb") as handle:
                shutil.copyfileobj(response, handle)
    except (error.URLError, TimeoutError) as exc:
        raise PipelineError(f"Falha ao baixar resultado OpenArt: {url}") from exc


def materialize_source(
    episode: Episode,
    task: dict[str, Any],
    result: dict[str, Any] | None,
) -> Path:
    scratch = episode.root / "build" / "openart" / "downloads"
    scratch.mkdir(parents=True, exist_ok=True)
    suffix = ".mp4" if task["media_kind"] == "clip" else ".img"
    raw = scratch / f"{task['task_id'].replace(':', '-')}{suffix}"
    raw.unlink(missing_ok=True)

    if result:
        if result.get("status") not in {None, "success", "succeeded", "completed"}:
            raise PipelineError(
                f"OpenArt não concluiu {task['task_id']}: "
                f"{result.get('status')}"
            )
        local_path = result.get("path")
        url = (
            result.get("url")
            or result.get("download_url")
            or (
                result.get("urls", [None])[0]
                if isinstance(result.get("urls"), list)
                and result.get("urls")
                else None
            )
        )
        if local_path:
            source = Path(str(local_path)).expanduser().resolve()
            if not source.exists() or not source.is_file():
                raise PipelineError(
                    f"Arquivo retornado pelo OpenArt está ausente: {source}"
                )
            shutil.copy2(source, raw)
        elif url:
            safe_download(str(url), raw)
        else:
            raise PipelineError(
                f"Resultado de {task['task_id']} não contém path nem URL"
            )
    else:
        source = Path(task["output"]["path"])
        if not source.exists() or not source.is_file():
            raise PipelineError(
                f"Resultado OpenArt ausente para {task['task_id']}: {source}"
            )
        shutil.copy2(source, raw)

    if not raw.exists() or raw.stat().st_size == 0:
        raise PipelineError(f"Resultado OpenArt vazio para {task['task_id']}")
    return raw


def run_ffmpeg(arguments: list[str], identifier: str) -> None:
    try:
        subprocess.run(
            ["ffmpeg", "-nostdin", "-y", *arguments],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise PipelineError("ffmpeg não está instalado") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()[-800:]
        raise PipelineError(
            f"Falha ao normalizar resultado OpenArt {identifier}: {detail}"
        ) from exc


def normalize_output(
    episode: Episode, task: dict[str, Any], raw: Path
) -> Path:
    output = Path(task["output"]["path"])
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(
        f".{output.stem}.openart.tmp{output.suffix}"
    )
    temporary.unlink(missing_ok=True)
    kind = task["media_kind"]

    if kind == "reference":
        width, height = 1440, 1920
    else:
        width, height = 1920, 1080
    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1"
    )

    if kind in {"reference", "frame"}:
        run_ffmpeg(
            [
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
            task["task_id"],
        )
    else:
        run_ffmpeg(
            [
                "-i",
                str(raw),
                "-vf",
                video_filter,
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-an",
                "-movflags",
                "+faststart",
                str(temporary),
            ],
            task["task_id"],
        )
    os.replace(temporary, output)
    return output


def sanitized_result(result: dict[str, Any] | None) -> dict[str, Any]:
    if not result:
        return {}
    sanitized = {
        key: value
        for key, value in result.items()
        if key not in {"url", "download_url", "urls"}
    }
    url = result.get("url") or result.get("download_url")
    if isinstance(url, str):
        parsed = parse.urlsplit(url)
        sanitized["source_url"] = parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, "", "")
        )
    return sanitized


def register_task(
    episode: Episode,
    manifest: dict[str, Any],
    task: dict[str, Any],
    result: dict[str, Any] | None,
) -> None:
    current_task, valid, _ = build_task(
        episode, task["media_kind"], task["identifier"]
    )
    if current_task["source_signature"] != task.get("source_signature"):
        raise PipelineError(
            f"Manifesto obsoleto para {task['task_id']}; rode o gen-* novamente"
        )
    if valid and result is None:
        print(f"= {task['task_id']}: cache válido")
        return

    raw = materialize_source(episode, task, result)
    output = normalize_output(episode, task, raw)
    kind = task["media_kind"]
    metrics = validate_visual_media(
        output, "reference" if kind == "reference" else kind
    )
    if kind == "clip":
        validate_clip_story_capacity(
            episode, task["identifier"], metrics["duration_seconds"]
        )

    _, cache_kind, values, dependencies = visual_artifact_contract(
        episode, kind, task["identifier"]
    )
    cache_data = record_cache(output, cache_kind, values, dependencies)
    provenance = {
        "schema": 1,
        "provider": "openart-mcp",
        "server": manifest["server"],
        "batch_id": manifest["batch_id"],
        "task_id": task["task_id"],
        "model": task["model"],
        "registered_at": utc_now(),
        "source_signature": task["source_signature"],
        "output_sha256": cache_data["output_sha256"],
        "result": sanitized_result(result),
    }
    write_json_atomic(Path(f"{output}.openart.json"), provenance)
    raw.unlink(missing_ok=True)
    print(f"✓ {task['task_id']} → {relative_to_episode(episode, output)}")


def command_plan(args: argparse.Namespace) -> int:
    episode = load_episode(Path(args.episode))
    manifest = build_manifest(episode, args.kind, args.identifiers, args.force)
    path = (
        Path(args.manifest).expanduser().resolve()
        if args.manifest
        else manifest_path(episode, args.kind)
    )
    write_json_atomic(path, manifest)
    print(f"OPENART_MCP_BATCH={path}")
    print(f"OPENART_MCP_TASKS={len(manifest['tasks'])}")
    print(f"OPENART_MCP_CONCURRENCY={manifest['max_concurrency']}")
    if manifest["tasks"]:
        print(
            "LOTE PRONTO: peça ao agente Cursor para executar este manifesto "
            "com o MCP OpenArt em paralelo."
        )
    else:
        print("LOTE VAZIO: todos os artefatos selecionados estão em cache.")
    return 0


def command_register(args: argparse.Namespace) -> int:
    episode = load_episode(Path(args.episode))
    require_openart(episode)
    path = (
        Path(args.manifest).expanduser().resolve()
        if args.manifest
        else manifest_path(episode, args.kind)
    )
    manifest = load_manifest(path)
    if manifest.get("media_kind") != args.kind:
        raise PipelineError(
            f"Manifesto é de {manifest.get('media_kind')}, não {args.kind}"
        )
    selected = set(
        select_identifiers(episode, args.kind, args.identifiers)
    )
    result_file = (
        Path(args.results).expanduser().resolve()
        if args.results
        else results_path(episode, args.kind)
    )
    results = load_results(result_file)
    tasks = [
        task
        for task in manifest["tasks"]
        if task.get("identifier") in selected
    ]
    if not tasks:
        print("Nenhuma tarefa pendente no manifesto selecionado.")
        return 0
    for task in tasks:
        register_task(episode, manifest, task, results.get(task["task_id"]))
    print(
        f"REGISTRO OPENART concluído. Revise e rode "
        f"./approve-visual.sh {args.kind} all"
    )
    return 0


def command_result(args: argparse.Namespace) -> int:
    episode = load_episode(Path(args.episode))
    require_openart(episode)
    path = (
        Path(args.results).expanduser().resolve()
        if args.results
        else results_path(episode, args.kind)
    )
    data: dict[str, Any]
    if path.exists():
        data = load_json_object(path, "Resultados OpenArt")
    else:
        data = {
            "schema": RESULT_SCHEMA,
            "provider": "openart-mcp",
            "media_kind": args.kind,
            "results": [],
        }
    rows = data.setdefault("results", [])
    if not isinstance(rows, list):
        raise PipelineError(f"Resultados OpenArt inválidos: {path}")
    task_id = f"{args.kind}:{args.identifier}"
    row = {
        "task_id": task_id,
        "status": args.status,
        "model": args.model or "",
        "asset_id": args.asset_id or "",
    }
    if args.url:
        row["url"] = args.url
    if args.path:
        row["path"] = str(Path(args.path).expanduser().resolve())
    rows[:] = [
        existing
        for existing in rows
        if not isinstance(existing, dict)
        or existing.get("task_id") != task_id
    ]
    rows.append(row)
    data["updated_at"] = utc_now()
    write_json_atomic(path, data)
    print(f"RESULTADO OPENART: {task_id} → {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan")
    plan.add_argument("--episode", required=True)
    plan.add_argument("--kind", choices=sorted(VALID_KINDS), required=True)
    plan.add_argument("--force", action="store_true")
    plan.add_argument("--manifest")
    plan.add_argument("identifiers", nargs="*")
    plan.set_defaults(func=command_plan)

    register = subparsers.add_parser("register")
    register.add_argument("--episode", required=True)
    register.add_argument("--kind", choices=sorted(VALID_KINDS), required=True)
    register.add_argument("--manifest")
    register.add_argument("--results")
    register.add_argument("identifiers", nargs="*")
    register.set_defaults(func=command_register)

    result = subparsers.add_parser("result")
    result.add_argument("--episode", required=True)
    result.add_argument("--kind", choices=sorted(VALID_KINDS), required=True)
    result.add_argument("--id", dest="identifier", required=True)
    source = result.add_mutually_exclusive_group(required=True)
    source.add_argument("--url")
    source.add_argument("--path")
    result.add_argument("--status", default="succeeded")
    result.add_argument("--model")
    result.add_argument("--asset-id")
    result.add_argument("--results")
    result.set_defaults(func=command_result)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        raise SystemExit(args.func(args))
    except PipelineError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
