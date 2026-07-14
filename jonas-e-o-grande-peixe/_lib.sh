#!/bin/zsh

set -eu
setopt pipefail

EPISODE_DIR="${0:A:h}"
PROJECT_ROOT="${EPISODE_DIR:h}"
if [[ -f "$EPISODE_DIR/_pipeline/episode_pipeline.py" ]]; then
  PIPELINE="${EPISODE_DIR}/_pipeline/episode_pipeline.py"
  AUDIO_HELPER="${EPISODE_DIR}/_pipeline/higgsfield_audio.py"
  CACHE_HELPER="${EPISODE_DIR}/_pipeline/artifact_cache.py"
  KIE_HELPER="${EPISODE_DIR}/_pipeline/kie_task.py"
else
  PIPELINE="${PROJECT_ROOT}/scripts/episode_pipeline.py"
  AUDIO_HELPER="${PROJECT_ROOT}/scripts/higgsfield_audio.py"
  CACHE_HELPER="${PROJECT_ROOT}/scripts/artifact_cache.py"
  KIE_HELPER="${PROJECT_ROOT}/scripts/kie_task.py"
fi

[[ -f "$PIPELINE" ]] || {
  echo "ERRO: pipeline compartilhado ausente: $PIPELINE" >&2
  exit 1
}
[[ -f "$EPISODE_DIR/meta.env" ]] || {
  echo "ERRO: meta.env ausente em $EPISODE_DIR" >&2
  exit 1
}

cd "$EPISODE_DIR"

typeset -a PIPELINE_TEMP_FILES
PIPELINE_TEMP_FILES=()

cleanup_pipeline_temp() {
  (( ${#PIPELINE_TEMP_FILES} )) && rm -f "${PIPELINE_TEMP_FILES[@]}"
}
trap cleanup_pipeline_temp EXIT

META_ROWS=$(mktemp "${TMPDIR:-/tmp}/geflix-meta.XXXXXX")
PIPELINE_TEMP_FILES+=("$META_ROWS")
python3 "$PIPELINE" env --episode "$EPISODE_DIR" > "$META_ROWS"
while IFS=$'\t' read -r key value || [[ -n "$key" ]]; do
  [[ -z "$key" ]] && continue
  typeset -g "$key=$value"
done < "$META_ROWS"

if [[ -z "${HIGGSFIELD_BIN:-}" ]]; then
  if (( $+commands[higgsfield] )); then
    HIGGSFIELD_BIN="${commands[higgsfield]}"
  elif (( $+commands[higgs] )); then
    HIGGSFIELD_BIN="${commands[higgs]}"
  else
    HIGGSFIELD_BIN="/opt/homebrew/bin/higgsfield"
  fi
fi

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERRO: comando obrigatório não encontrado: $1" >&2
    exit 1
  }
}

validate_stage() {
  python3 "$PIPELINE" validate --episode "$EPISODE_DIR" --stage "$1"
}

prepare_rows() {
  local table="$1"
  local target_variable="$2"
  local rows_file
  rows_file=$(mktemp "${TMPDIR:-/tmp}/geflix-${table}.XXXXXX")
  PIPELINE_TEMP_FILES+=("$rows_file")
  python3 "$PIPELINE" rows --episode "$EPISODE_DIR" \
    --table "$table" > "$rows_file"
  typeset -g "$target_variable=$rows_file"
}

selected_scene() {
  local scene_id="$1"
  shift
  (( $# == 0 )) && return 0
  local selected
  for selected in "$@"; do
    [[ "$selected" == "$scene_id" ]] && return 0
  done
  return 1
}

media_url_from_output() {
  python3 -c '
import json, re, sys
raw = sys.stdin.read().strip()
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    data = None

def urls(value):
    if isinstance(value, dict):
        for key in ("result_url", "url", "result_urls", "urls", "outputs"):
            if key in value:
                yield from urls(value[key])
        for key, nested in value.items():
            if key not in {"result_url", "url", "result_urls", "urls", "outputs"}:
                yield from urls(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from urls(nested)
    elif isinstance(value, str) and value.startswith("http"):
        yield value

if data is not None:
    for candidate in urls(data):
        print(candidate)
        raise SystemExit(0)

matches = re.findall(r"https://\S+", raw)
if matches:
    print(matches[-1].rstrip("\"'"'"',.)]}"))
    raise SystemExit(0)
raise SystemExit(1)
'
}
