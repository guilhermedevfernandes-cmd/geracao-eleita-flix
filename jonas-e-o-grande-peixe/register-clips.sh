#!/bin/zsh
# Registra clipes produzidos manualmente no Seedance depois de validar sua integridade.
source "${0:A:h}/_lib.sh"

require_command ffprobe
validate_stage production
ONLY=("$@")
prepare_rows scenes SCENE_ROWS

while IFS=$'\t' read -r id act shot refs voice text hold image_prompt motion_prompt vfx sfx transition; do
  [[ -z "$id" ]] && continue
  selected_scene "$id" "${ONLY[@]}" || continue

  frame="frames/${id}.png"
  clip="clips/${id}.mp4"
  [[ -s "$frame" ]] || {
    echo "ERRO: frame ausente: $frame" >&2
    exit 1
  }
  [[ -s "$clip" ]] || {
    echo "ERRO: clipe manual ausente: $clip" >&2
    exit 1
  }

  frame_signature=$(python3 "$PIPELINE" signature --episode "$EPISODE_DIR" \
    --scene "$id" --media frame)
  frame_cache_args=(
    --output "$frame"
    --kind "episode-frame"
    --value "source_signature=$frame_signature"
  )
  if [[ "$refs" != "-" ]]; then
    for key in ${(s:,:)refs}; do
      frame_cache_args+=(--dependency "ref-${key}=assets/${key}_ref.png")
    done
  fi
  python3 "$CACHE_HELPER" check "${frame_cache_args[@]}" >/dev/null || {
    echo "ERRO: frame $id está obsoleto; regenere antes de registrar o clipe" >&2
    exit 1
  }
  python3 "$PIPELINE" verify-visual \
    --episode "$EPISODE_DIR" --kind frame --identifier "$id"

  python3 "$PIPELINE" media --path "$clip" --kind clip

  signature=$(python3 "$PIPELINE" signature --episode "$EPISODE_DIR" \
    --scene "$id" --media clip)
  python3 "$CACHE_HELPER" record \
    --output "$clip" \
    --kind "episode-clip" \
    --value "source_signature=$signature" \
    --dependency "frame=$frame" >/dev/null
  echo "✓ clipe manual $id registrado"
done < "$SCENE_ROWS"

echo "REGISTRO concluído. Alterar clipe, frame ou prompt invalidará o manifesto."
echo "Depois de assistir aos clipes: ./approve-visual.sh clip all"
