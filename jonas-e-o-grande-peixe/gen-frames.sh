#!/bin/zsh
# Gera keyframes cinematográficos com continuidade de personagem e geografia.
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

mkdir -p frames build
prepare_rows scenes SCENE_ROWS

while IFS=$'\t' read -r id act shot refs voice text hold image_prompt motion_prompt vfx sfx transition; do
  [[ -z "$id" ]] && continue
  selected_scene "$id" "${ONLY[@]}" || continue

  out="frames/${id}.png"

  ref_args=()
  cache_dependencies=()
  if [[ "$refs" != "-" ]]; then
    for key in ${(s:,:)refs}; do
      ref="assets/${key}_ref.png"
      [[ -s "$ref" ]] || {
        echo "ERRO: cena $id precisa da referência ausente $ref" >&2
        exit 1
      }
      ref_signature=$(python3 "$PIPELINE" reference --episode "$EPISODE_DIR" \
        --key "$key" --field signature)
      python3 "$CACHE_HELPER" check \
        --output "$ref" \
        --kind "episode-reference" \
        --value "source_signature=$ref_signature" >/dev/null || {
        echo "ERRO: referência '$key' está obsoleta; rode ./gen-sheets.sh $key" >&2
        exit 1
      }
      python3 "$PIPELINE" verify-visual \
        --episode "$EPISODE_DIR" --kind reference --identifier "$key"
      ref_args+=(--image "$ref")
      cache_dependencies+=(--dependency "ref-${key}=$ref")
    done
  fi

  prompt=$(python3 "$PIPELINE" prompt --episode "$EPISODE_DIR" \
    --scene "$id" --media frame)
  signature=$(python3 "$PIPELINE" signature --episode "$EPISODE_DIR" \
    --scene "$id" --media frame)
  cache_args=(
    --output "$out"
    --kind "episode-frame"
    --value "source_signature=$signature"
    "${cache_dependencies[@]}"
  )
  if (( ! FORCE )) && python3 "$CACHE_HELPER" check "${cache_args[@]}" >/dev/null; then
    echo "= cena $id: cache válido"
    continue
  fi

  tmp="build/.${id}.frame.$$.png"
  rm -f "$tmp"

  echo "=== frame $id · $act · $shot ==="
  if [[ "$GEN_PROVIDER" == "kie" ]]; then
    python3 "$KIE_HELPER" image \
      --kind frame --id "$id" --out "$tmp" \
      --prompt "$prompt" \
      "${ref_args[@]}" \
      --aspect-ratio "$ASPECT" --resolution "$IMG_RES" \
      --model "$KIE_IMAGE_MODEL" \
      --usage-log "$KIE_USAGE_LOG" \
      --upload-path "${SLUG}/frames"
  else
    if ! response=$("$HIGGSFIELD_BIN" generate create nano_banana_2 \
      --prompt "$prompt" \
      "${ref_args[@]}" \
      --aspect_ratio "$ASPECT" --resolution "$IMG_RES" \
      --wait --wait-timeout 8m --json 2>&1); then
      echo "ERRO Higgsfield na cena $id: $response" >&2
      exit 1
    fi
    url=$(print -r -- "$response" | media_url_from_output) || {
      echo "ERRO: resposta sem URL na cena $id: $response" >&2
      exit 1
    }
    curl --fail --silent --show-error --location "$url" --output "$tmp"
  fi

  [[ -s "$tmp" ]] || {
    echo "ERRO: frame vazio: $id" >&2
    exit 1
  }
  python3 "$PIPELINE" media --path "$tmp" --kind frame
  mv "$tmp" "$out"
  python3 "$CACHE_HELPER" record "${cache_args[@]}" >/dev/null
  echo "✓ $out"
done < "$SCENE_ROWS"

echo "FRAMES concluídos. Revise composição, identidade e continuidade."
echo "Depois da revisão: ./approve-visual.sh frame all"
