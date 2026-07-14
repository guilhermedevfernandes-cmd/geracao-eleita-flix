#!/bin/zsh

set -eu
setopt pipefail

EPISODE_DIR="${0:A:h}"
PROJECT_ROOT="${EPISODE_DIR:h}"
if [[ -f "$EPISODE_DIR/_pipeline/episode_pipeline.py" ]]; then
  PIPELINE="${EPISODE_DIR}/_pipeline/episode_pipeline.py"
  AUDIO_HELPER="${EPISODE_DIR}/_pipeline/elevenlabs_audio.py"
  CACHE_HELPER="${EPISODE_DIR}/_pipeline/artifact_cache.py"
  OPENART_HELPER="${EPISODE_DIR}/_pipeline/openart_batch.py"
else
  PIPELINE="${PROJECT_ROOT}/scripts/episode_pipeline.py"
  AUDIO_HELPER="${PROJECT_ROOT}/scripts/elevenlabs_audio.py"
  CACHE_HELPER="${PROJECT_ROOT}/scripts/artifact_cache.py"
  OPENART_HELPER="${PROJECT_ROOT}/scripts/openart_batch.py"
fi

[[ -f "$PIPELINE" ]] || {
  echo "ERRO: pipeline compartilhado ausente: $PIPELINE" >&2
  exit 1
}
[[ -f "$OPENART_HELPER" ]] || {
  echo "ERRO: helper OpenArt ausente: $OPENART_HELPER" >&2
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
