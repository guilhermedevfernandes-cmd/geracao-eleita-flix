#!/bin/zsh
# Trilha opcional. A montagem também aceita um audio/bgm.mp3 produzido externamente.
source "${0:A:h}/_lib.sh"

validate_stage produced-audio
mkdir -p audio

duration_report=$(mktemp "${TMPDIR:-/tmp}/geflix-duration.XXXXXX")
PIPELINE_TEMP_FILES+=("$duration_report")
python3 "$PIPELINE" validate --episode "$EPISODE_DIR" \
  --stage produced-audio --json > "$duration_report"
duration=$(python3 -c \
  'import json,sys; d=json.load(open(sys.argv[1])); print("{:.2f}".format(d["metrics"]["duration_seconds"]))' \
  "$duration_report")

args=(music --prompt "$SCORE_PROMPT" --duration "$duration" --out audio/bgm.mp3)
[[ "${1:-}" == "--force" ]] && args+=(--force)
[[ "${1:-}" == "--dry-run" || "${2:-}" == "--dry-run" ]] && args+=(--dry-run)

python3 "$AUDIO_HELPER" "${args[@]}"
echo "TRILHA: audio/bgm.mp3 (${duration}s)"
echo "Depois de ouvir a trilha: ./approve-music.sh"
