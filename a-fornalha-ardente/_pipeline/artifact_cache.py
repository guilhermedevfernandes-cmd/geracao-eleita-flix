#!/usr/bin/env python3
"""Content-addressed cache metadata for generated episode media."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


CACHE_SCHEMA = 1


class CacheError(RuntimeError):
    """Raised when cache metadata is missing or inconsistent."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metadata_path(output: Path) -> Path:
    return Path(f"{output}.meta.json")


def dependency_records(
    dependencies: Iterable[tuple[str, Path]],
) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for label, path in dependencies:
        if not path.exists() or not path.is_file():
            raise CacheError(f"Dependência ausente: {label}={path}")
        records.append(
            {
                "label": label,
                "filename": path.name,
                "sha256": sha256_file(path),
            }
        )
    return records


def fingerprint_payload(
    kind: str,
    values: dict[str, str],
    dependencies: Iterable[tuple[str, Path]],
) -> tuple[str, list[dict[str, str]]]:
    records = dependency_records(dependencies)
    payload = {
        "schema": CACHE_SCHEMA,
        "kind": kind,
        "values": values,
        "dependencies": records,
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest(), records


def load_metadata(output: Path) -> dict[str, Any]:
    sidecar = metadata_path(output)
    if not sidecar.exists():
        raise CacheError(f"Metadado de cache ausente: {sidecar}")
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CacheError(f"Metadado inválido: {sidecar}") from exc
    if not isinstance(data, dict) or data.get("schema") != CACHE_SCHEMA:
        raise CacheError(f"Schema de cache inválido: {sidecar}")
    return data


def verify_recorded_output(output: Path) -> dict[str, Any]:
    if not output.exists() or not output.is_file() or output.stat().st_size == 0:
        raise CacheError(f"Artefato ausente ou vazio: {output}")
    data = load_metadata(output)
    if data.get("output_size") != output.stat().st_size:
        raise CacheError(f"Tamanho do artefato diverge do manifesto: {output}")
    if data.get("output_sha256") != sha256_file(output):
        raise CacheError(f"Hash do artefato diverge do manifesto: {output}")
    return data


def cache_valid(
    output: Path,
    kind: str,
    values: dict[str, str],
    dependencies: Iterable[tuple[str, Path]],
) -> tuple[bool, str]:
    try:
        expected, _ = fingerprint_payload(kind, values, dependencies)
        data = verify_recorded_output(output)
        if data.get("kind") != kind:
            return False, "tipo mudou"
        if data.get("fingerprint") != expected:
            return False, "entradas mudaram"
        return True, "cache válido"
    except CacheError as exc:
        return False, str(exc)


def record_cache(
    output: Path,
    kind: str,
    values: dict[str, str],
    dependencies: Iterable[tuple[str, Path]],
) -> dict[str, Any]:
    if not output.exists() or not output.is_file() or output.stat().st_size == 0:
        raise CacheError(f"Não é possível registrar artefato ausente/vazio: {output}")
    fingerprint, records = fingerprint_payload(kind, values, dependencies)
    data: dict[str, Any] = {
        "schema": CACHE_SCHEMA,
        "kind": kind,
        "fingerprint": fingerprint,
        "values": values,
        "dependencies": records,
        "output_sha256": sha256_file(output),
        "output_size": output.stat().st_size,
    }

    sidecar = metadata_path(output)
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=sidecar.parent,
        prefix=f".{sidecar.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, sidecar)
    return data


def parse_pairs(items: list[str], label: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise CacheError(f"{label} precisa usar chave=valor: {item}")
        key, value = item.split("=", 1)
        if not key:
            raise CacheError(f"{label} com chave vazia: {item}")
        if key in parsed:
            raise CacheError(f"{label} duplicado: {key}")
        parsed[key] = value
    return parsed


def parse_dependencies(items: list[str]) -> list[tuple[str, Path]]:
    parsed: list[tuple[str, Path]] = []
    for item in items:
        if "=" not in item:
            raise CacheError(f"dependency precisa usar rótulo=caminho: {item}")
        label, raw_path = item.split("=", 1)
        parsed.append((label, Path(raw_path).expanduser().resolve()))
    return parsed


def common_inputs(
    args: argparse.Namespace,
) -> tuple[Path, str, dict[str, str], list[tuple[str, Path]]]:
    return (
        Path(args.output).expanduser().resolve(),
        args.kind,
        parse_pairs(args.value, "value"),
        parse_dependencies(args.dependency),
    )


def command_check(args: argparse.Namespace) -> int:
    try:
        output, kind, values, dependencies = common_inputs(args)
        valid, reason = cache_valid(output, kind, values, dependencies)
        print(("HIT" if valid else "MISS") + f": {reason}")
        return 0 if valid else 1
    except CacheError as exc:
        print(f"MISS: {exc}")
        return 1


def command_record(args: argparse.Namespace) -> int:
    try:
        output, kind, values, dependencies = common_inputs(args)
        data = record_cache(output, kind, values, dependencies)
        print(data["fingerprint"])
        return 0
    except CacheError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_fingerprint(args: argparse.Namespace) -> int:
    try:
        _, kind, values, dependencies = common_inputs(args)
        fingerprint, _ = fingerprint_payload(kind, values, dependencies)
        print(fingerprint)
        return 0
    except CacheError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def command_verify(args: argparse.Namespace) -> int:
    try:
        data = verify_recorded_output(Path(args.output).expanduser().resolve())
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(data["fingerprint"])
        return 0
    except CacheError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


def add_cache_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output", required=True)
    parser.add_argument("--kind", required=True)
    parser.add_argument("--value", action="append", default=[])
    parser.add_argument("--dependency", action="append", default=[])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check")
    add_cache_inputs(check)
    check.set_defaults(func=command_check)

    record = subparsers.add_parser("record")
    add_cache_inputs(record)
    record.set_defaults(func=command_record)

    fingerprint = subparsers.add_parser("fingerprint")
    add_cache_inputs(fingerprint)
    fingerprint.set_defaults(func=command_fingerprint)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--output", required=True)
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(func=command_verify)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
