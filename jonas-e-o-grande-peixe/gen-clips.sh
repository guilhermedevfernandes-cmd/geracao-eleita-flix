#!/bin/zsh
# Anima keyframes em planos de 10s; a montagem corta, nunca congela ou estica demais.
source "${0:A:h}/_lib.sh"

require_command curl
require_command ffprobe
validate_stage production

FORCE=0
ONLY=()
for arg in "$@"; do
  [[ "$arg" == "--force" ]] && { FORCE=1; continue; }
  ONLY+=("$arg")
done

model_args=(--aspect_ratio "$ASPECT" --duration "$VIDEO_DUR")
case "$VIDEO_MODEL" in
  kling3_0_turbo) model_args+=(--resolution "$VIDEO_RES") ;;
  kling3_0) model_args+=(--mode std --sound off) ;;
  kling2_6) model_args+=(--sound false) ;;
esac

mkdir -p clips build
prepare_rows scenes SCENE_ROWS

while IFS=$'\t' read -r id act shot refs voice text hold image_prompt motion_prompt vfx sfx transition; do
  [[ -z "$id" ]] && continue
  selected_scene "$id" "${ONLY[@]}" || continue

  frame="frames/${id}.png"
  out="clips/${id}.mp4"
  [[ -s "$frame" ]] || {
    echo "ERRO: frame ausente para cena $id: $frame" >&2
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
    echo "ERRO: frame $id está obsoleto; rode ./gen-frames.sh $id" >&2
    exit 1
  }
  python3 "$PIPELINE" verify-visual \
    --episode "$EPISODE_DIR" --kind frame --identifier "$id"

  prompt=$(python3 "$PIPELINE" prompt --episode "$EPISODE_DIR" \
    --scene "$id" --media clip)
  signature=$(python3 "$PIPELINE" signature --episode "$EPISODE_DIR" \
    --scene "$id" --media clip)
  cache_args=(
    --output "$out"
    --kind "episode-clip"
    --value "source_signature=$signature"
    --dependency "frame=$frame"
  )
  if (( ! FORCE )) && python3 "$CACHE_HELPER" check "${cache_args[@]}" >/dev/null; then
    echo "= cena $id: cache válido"
    continue
  fi

  tmp="build/.${id}.clip.$$.mp4"
  rm -f "$tmp"

  echo "=== clipe $id · $VIDEO_MODEL · ${VIDEO_DUR}s ==="
  if [[ "$GEN_PROVIDER" == "kie" ]]; then
    python3 "$KIE_HELPER" video \
      --id "$id" --out "$tmp" \
      --prompt "$prompt" \
      --image "$frame" \
      --duration "$VIDEO_DUR" \
      --resolution "$VIDEO_RES" \
      --aspect-ratio "$ASPECT" \
      --mode "$KIE_VIDEO_MODE" \
      --model "$KIE_VIDEO_MODEL" \
      --usage-log "$KIE_USAGE_LOG" \
      --upload-path "${SLUG}/clips"
  else
    attempt=1
    max_attempts=5
    response=""
    while (( attempt <= max_attempts )); do
      if response=$("$HIGGSFIELD_BIN" generate create "$VIDEO_MODEL" \
        --prompt "$prompt" \
        --image "$frame" \
        "${model_args[@]}" \
        --wait --wait-timeout 20m --json 2>&1); then
        break
      fi
      if (( attempt == max_attempts )); then
        echo "ERRO Higgsfield na cena $id (tentativa $attempt/$max_attempts): $response" >&2
        exit 1
      fi
      wait_s=$(( attempt * 20 ))
      echo "AVISO: falha na cena $id (tentativa $attempt/$max_attempts); nova tentativa em ${wait_s}s" >&2
      echo "AVISO: $response" >&2
      sleep "$wait_s"
      (( attempt++ ))
    done
    url=$(print -r -- "$response" | media_url_from_output) || {
      echo "ERRO: resposta sem URL na cena $id: $response" >&2
      exit 1
    }
    curl --fail --silent --show-error --location "$url" --output "$tmp"
  fi

  [[ -s "$tmp" ]] || {
    echo "ERRO: clipe vazio: $id" >&2
    exit 1
  }
  # Kling 3.0 Turbo pode devolver áudio e resolução off-by-a-few; normaliza para o gate.
  # -nostdin evita que o ffmpeg consuma o TSV do while-read.
  normalized="build/.${id}.clip.norm.$$.mp4"
  ffmpeg -nostdin -y -i "$tmp" \
    -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" \
    -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -an \
    -movflags +faststart "$normalized" >/dev/null 2>&1 || {
    echo "ERRO: falha ao normalizar clipe $id" >&2
    exit 1
  }
  mv "$normalized" "$tmp"
  python3 "$PIPELINE" media --path "$tmp" --kind clip
  mv "$tmp" "$out"
  python3 "$CACHE_HELPER" record "${cache_args[@]}" >/dev/null
  echo "✓ $out"
done < "$SCENE_ROWS"

echo "CLIPES concluídos. Revise identidade, mãos, física e ausência de morphing."
echo "Depois da revisão: ./approve-visual.sh clip all"
