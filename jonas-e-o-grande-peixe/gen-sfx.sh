#!/bin/zsh
# Cria uma camada de ambiência/efeitos por cena com Mirelo.
source "${0:A:h}/_lib.sh"

validate_stage produced-audio

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

mkdir -p audio/sfx
prepare_rows scenes SCENE_ROWS

while IFS=$'\t' read -r id act shot refs voice text hold image_prompt motion_prompt vfx sfx transition; do
  [[ -z "$id" ]] && continue
  selected_scene "$id" "${ONLY[@]}" || continue
  [[ "$sfx" == "-" ]] && {
    echo "= cena $id: silêncio intencional"
    continue
  }

  duration=$(python3 "$PIPELINE" duration \
    --episode "$EPISODE_DIR" --scene "$id" --actual)
  out="audio/sfx/${id}.wav"
  prompt="$sfx. Scene context: $act. Build clear foreground action, environmental ambience, and subtle spatial depth."

  echo "=== SFX $id · ${duration}s ==="
  args=(sfx --prompt "$prompt" --duration "$duration" --out "$out")
  (( FORCE )) && args+=(--force)
  (( DRY_RUN )) && args+=(--dry-run)
  python3 "$AUDIO_HELPER" "${args[@]}"
done < "$SCENE_ROWS"

echo "DESENHO DE SOM concluído."
