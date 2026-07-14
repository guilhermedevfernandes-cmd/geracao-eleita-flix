#!/usr/bin/env python3
"""Small Kie.ai task runner for the Geração Eleita Flix shell pipeline."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import uuid
from pathlib import Path
from urllib import error, parse, request


API_BASE = os.environ.get("KIE_API_BASE", "https://api.kie.ai").rstrip("/")
UPLOAD_BASE = os.environ.get("KIE_UPLOAD_BASE", "https://kieai.redpandaai.co").rstrip("/")


def api_key() -> str:
    key = os.environ.get("KIE_API_KEY", "").strip()
    if not key:
        raise SystemExit("KIE_API_KEY não está configurada no ambiente.")
    return key


def read_json_response(response: request.addinfourl) -> dict:
    raw = response.read().decode("utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Resposta não é JSON: {raw[:300]}") from exc


def open_url(req: request.Request, timeout: int = 120) -> dict:
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return read_json_response(response)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def post_json(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{API_BASE}{path}",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": "application/json",
        },
    )
    return open_url(req)


def get_json(path: str, params: dict | None = None) -> dict:
    query = f"?{parse.urlencode(params)}" if params else ""
    req = request.Request(
        f"{API_BASE}{path}{query}",
        method="GET",
        headers={"Authorization": f"Bearer {api_key()}"},
    )
    return open_url(req)


def upload_file(path: Path, upload_path: str) -> str:
    if not path.exists():
        raise SystemExit(f"Arquivo não encontrado para upload: {path}")

    boundary = f"----kie-{uuid.uuid4().hex}"
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

    parts: list[bytes] = []
    fields = {"uploadPath": upload_path, "fileName": path.name}
    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(f"{value}\r\n".encode())

    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        (
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode()
    )
    parts.append(path.read_bytes())
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())

    req = request.Request(
        f"{UPLOAD_BASE}/api/file-stream-upload",
        data=b"".join(parts),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    response = open_url(req)
    data = response.get("data") or {}
    download_url = data.get("downloadUrl")
    if not download_url:
        raise RuntimeError(f"Upload não retornou downloadUrl: {response}")
    return download_url


def create_task(model: str, input_payload: dict, callback_url: str | None = None) -> str:
    payload: dict = {"model": model, "input": input_payload}
    if callback_url:
        payload["callBackUrl"] = callback_url

    response = post_json("/api/v1/jobs/createTask", payload)
    data = response.get("data") or {}
    task_id = data.get("taskId") or data.get("task_id")
    if not task_id:
        raise RuntimeError(f"createTask não retornou taskId: {response}")
    return task_id


def wait_task(task_id: str, timeout: int, interval: int) -> dict:
    started = time.time()
    while True:
        response = get_json("/api/v1/jobs/recordInfo", {"taskId": task_id})
        data = response.get("data") or {}
        state = data.get("state")
        if state == "success":
            return data
        if state == "fail":
            raise RuntimeError(f"Tarefa falhou: {data.get('failCode')} {data.get('failMsg')}")
        if time.time() - started > timeout:
            raise TimeoutError(f"Timeout aguardando tarefa {task_id}; último estado: {state}")
        print(f"  ... {task_id}: {state or 'waiting'}", file=sys.stderr)
        time.sleep(interval)


def result_url(task: dict) -> str:
    raw = task.get("resultJson") or "{}"
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"resultJson inválido: {raw}") from exc
    urls = result.get("resultUrls") or result.get("result_urls") or []
    if not urls:
        raise RuntimeError(f"Nenhuma URL de resultado em resultJson: {result}")
    return urls[0]


def download_file(url: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    req = request.Request(url, headers={"User-Agent": "gerecao-eleita-flix/1.0"})
    try:
        with request.urlopen(req, timeout=300) as response:
            out.write_bytes(response.read())
    except error.HTTPError:
        req = request.Request(url, headers={"Authorization": f"Bearer {api_key()}"})
        with request.urlopen(req, timeout=300) as response:
            out.write_bytes(response.read())


def append_usage(log_path: Path | None, kind: str, scene_id: str, model: str, task: dict, out: Path) -> None:
    if not log_path:
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text("kind\tid\tmodel\ttask_id\tcredits\toutput\n", encoding="utf-8")
    credits = task.get("creditsConsumed", "")
    row = "\t".join([kind, scene_id, model, task.get("taskId", ""), str(credits), str(out)])
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{row}\n")


def normalized_resolution(resolution: str) -> str:
    value = resolution.strip()
    upper = value.upper()
    return upper if upper in {"1K", "2K", "4K"} else value


def generate_image(args: argparse.Namespace) -> None:
    image_urls = [upload_file(Path(path), args.upload_path) for path in args.image]
    input_payload = {
        "prompt": args.prompt,
        "aspect_ratio": args.aspect_ratio,
        "resolution": normalized_resolution(args.resolution),
        "output_format": args.output_format,
    }
    if image_urls:
        input_payload["image_input"] = image_urls

    task_id = create_task(args.model, input_payload, args.callback_url)
    print(f"  task: {task_id}", file=sys.stderr)
    task = wait_task(task_id, args.timeout, args.interval)
    download_file(result_url(task), Path(args.out))
    append_usage(Path(args.usage_log) if args.usage_log else None, args.kind, args.id, args.model, task, Path(args.out))
    print(f"CREDITS_CONSUMED={task.get('creditsConsumed', '')}")


def generate_video(args: argparse.Namespace) -> None:
    image_url = upload_file(Path(args.image), args.upload_path)
    if args.model == "kling/v3-turbo-image-to-video":
        input_payload = {
            "prompt": args.prompt,
            "image_urls": [image_url],
            "duration": str(args.duration),
            "resolution": args.resolution,
        }
    else:
        input_payload = {
            "prompt": args.prompt,
            "image_urls": [image_url],
            "sound": args.sound,
            "duration": str(args.duration),
            "aspect_ratio": args.aspect_ratio,
            "mode": args.mode,
            "multi_shots": False,
            "multi_prompt": [],
        }

    task_id = create_task(args.model, input_payload, args.callback_url)
    print(f"  task: {task_id}", file=sys.stderr)
    task = wait_task(task_id, args.timeout, args.interval)
    download_file(result_url(task), Path(args.out))
    append_usage(Path(args.usage_log) if args.usage_log else None, "clip", args.id, args.model, task, Path(args.out))
    print(f"CREDITS_CONSUMED={task.get('creditsConsumed', '')}")


def balance(_: argparse.Namespace) -> None:
    response = get_json("/api/v1/chat/credit")
    print(response.get("data", ""))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--id", default="-")
    common.add_argument("--out", required=True)
    common.add_argument("--prompt", required=True)
    common.add_argument("--callback-url")
    common.add_argument("--usage-log")
    common.add_argument("--timeout", type=int, default=900)
    common.add_argument("--interval", type=int, default=5)
    common.add_argument("--upload-path", default="gerecao-eleita-flix")

    image = sub.add_parser("image", parents=[common])
    image.add_argument("--kind", default="frame", choices=["frame", "ref"])
    image.add_argument("--model", default=os.environ.get("KIE_IMAGE_MODEL", "google/nanobanana2"))
    image.add_argument("--aspect-ratio", default="16:9")
    image.add_argument("--resolution", default="2K")
    image.add_argument("--output-format", default="png", choices=["png", "jpg"])
    image.add_argument("--image", action="append", default=[])
    image.set_defaults(func=generate_image)

    video = sub.add_parser("video", parents=[common])
    video.add_argument("--model", default=os.environ.get("KIE_VIDEO_MODEL", "kling-3.0/video"))
    video.add_argument("--image", required=True)
    video.add_argument("--duration", default="5")
    video.add_argument("--aspect-ratio", default="16:9")
    video.add_argument("--resolution", default="1080p")
    video.add_argument("--mode", default="pro", choices=["std", "pro", "4K"])
    video.add_argument("--sound", action=argparse.BooleanOptionalAction, default=False)
    video.set_defaults(func=generate_video)

    credits = sub.add_parser("balance")
    credits.set_defaults(func=balance)
    return root


def main() -> None:
    args = parser().parse_args()
    try:
        args.func(args)
    except Exception as exc:
        print(f"✗ {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
