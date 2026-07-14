#!/bin/zsh
# Gera uma referência visual limpa por personagem; nunca um mosaico de poses.
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

mkdir -p assets build
prepare_rows characters CHARACTER_ROWS

while IFS=$'\t' read -r key name voice_id locale approved sheet_prompt; do
  [[ -z "$key" ]] && continue
  selected_scene "$key" "${ONLY[@]}" || continue
  [[ "$sheet_prompt" == "-" ]] && {
    echo "= $key: personagem somente voz"
    continue
  }

  out="assets/${key}_ref.png"
  prompt=$(python3 "$PIPELINE" reference --episode "$EPISODE_DIR" \
    --key "$key" --field prompt)
  signature=$(python3 "$PIPELINE" reference --episode "$EPISODE_DIR" \
    --key "$key" --field signature)
  cache_args=(
    --output "$out"
    --kind "episode-reference"
    --value "source_signature=$signature"
  )
  if (( ! FORCE )) && python3 "$CACHE_HELPER" check "${cache_args[@]}" >/dev/null; then
    echo "= $key: cache válido"
    continue
  fi

  tmp="build/.${key}.ref.$$.png"
  rm -f "$tmp"
  echo "=== referência · $name ($key) ==="

  if [[ "$GEN_PROVIDER" == "kie" ]]; then
    python3 "$KIE_HELPER" image \
      --kind ref --id "$key" --out "$tmp" \
      --prompt "$prompt" \
      --aspect-ratio "$REF_ASPECT" --resolution "$IMG_RES" \
      --model "$KIE_IMAGE_MODEL" \
      --usage-log "$KIE_USAGE_LOG" \
      --upload-path "${SLUG}/assets"
  else
    if ! response=$("$HIGGSFIELD_BIN" generate create nano_banana_2 \
      --prompt "$prompt" \
      --aspect_ratio "$REF_ASPECT" --resolution "$IMG_RES" \
      --wait --wait-timeout 8m --json 2>&1); then
      echo "ERRO Higgsfield: $response" >&2
      exit 1
    fi
    url=$(print -r -- "$response" | media_url_from_output) || {
      echo "ERRO: resposta sem URL para $key: $response" >&2
      exit 1
    }
    curl --fail --silent --show-error --location "$url" --output "$tmp"
  fi

  [[ -s "$tmp" ]] || {
    echo "ERRO: referência vazia para $key" >&2
    exit 1
  }
  python3 "$PIPELINE" media --path "$tmp" --kind reference
  mv "$tmp" "$out"
  python3 "$CACHE_HELPER" record "${cache_args[@]}" >/dev/null
  echo "✓ $out"
done < "$CHARACTER_ROWS"

echo "REFERÊNCIAS concluídas. Revise rosto, roupa, cores e silhueta."
echo "Depois da revisão: ./approve-visual.sh reference all"
