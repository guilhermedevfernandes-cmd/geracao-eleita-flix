#!/bin/zsh
# Dublagem multivoz. Falha fechado: sem fallback silencioso para o narrador.
source "${0:A:h}/_lib.sh"

require_command ffprobe
validate_stage audio

FORCE=0
DRY_RUN=0
ONLY=()
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    *) ONLY+=("$arg") ;;
  esac
done

typeset -A VOICE_ID
typeset -A VOICE_NAME
prepare_rows characters CHARACTER_ROWS
while IFS=$'\t' read -r key name voice_id locale approved sheet_prompt; do
  [[ -z "$key" ]] && continue
  VOICE_ID[$key]="$voice_id"
  VOICE_NAME[$key]="$name"
done < "$CHARACTER_ROWS"

mkdir -p audio build
prepare_rows scenes SCENE_ROWS
: > build/audio-durations.tsv
print -r -- $'scene\tvoice\tseconds\tfile' >> build/audio-durations.tsv

while IFS=$'\t' read -r id act shot refs voice text hold image_prompt motion_prompt vfx sfx transition; do
  [[ -z "$id" ]] && continue
  selected_scene "$id" "${ONLY[@]}" || continue
  [[ "$voice" == "-" ]] && {
    echo "= cena $id: beat sem fala"
    continue
  }

  voice_id="${VOICE_ID[$voice]:-}"
  [[ -n "$voice_id" ]] || {
    echo "ERRO: cena $id referencia voz inexistente '$voice'" >&2
    exit 1
  }

  out="audio/${id}.mp3"
  echo "=== cena $id · ${VOICE_NAME[$voice]} · PT-BR ==="
  args=(tts --text "$text" --voice-id "$voice_id" --out "$out")
  (( FORCE )) && args+=(--force)
  (( DRY_RUN )) && args+=(--dry-run)
  python3 "$AUDIO_HELPER" "${args[@]}"

  if (( ! DRY_RUN )); then
    duration=$(ffprobe -v error -show_entries format=duration \
      -of default=noprint_wrappers=1:nokey=1 "$out")
    printf "%s\t%s\t%.3f\t%s\n" "$id" "$voice" "$duration" "$out" \
      >> build/audio-durations.tsv
  fi
done < "$SCENE_ROWS"

if (( DRY_RUN )); then
  echo "DRY_RUN concluído; nenhum crédito foi usado."
elif (( ${#ONLY} == 0 )); then
  validate_stage produced-audio
  echo "DUBLAGEM APROVADA: duração real dentro da faixa de cinco minutos."
else
  echo "Dublagem parcial concluída. Rode sem IDs para validar a duração total."
fi
