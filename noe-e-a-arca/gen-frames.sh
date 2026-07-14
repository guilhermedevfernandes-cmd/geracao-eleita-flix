#!/bin/zsh
# Gera o frame (imagem) de cada cena via Nano Banana Pro, usando as REFERÊNCIAS
# (assets/<key>_ref.png — uma figura única cada) indicadas na coluna "refs".
# Lê scenes.tsv. Salva em frames/NN.png. Pula os que já existem.
# Uso: ./gen-frames.sh [id1 id2 ...]   (sem args = todas)  |  --force
set -u
cd "${0:A:h}"
source ./meta.env
KIE_HELPER="../scripts/kie_task.py"

# Guarda anti-clonagem: o Nano Banana tende a duplicar personagens. Reforçamos
# que devem aparecer SÓ os personagens descritos, sem cópias.
ANTICLONE="show only the characters described, no duplicated or cloned characters, natural single composition"

FORCE=0
ONLY=()
for a in "$@"; do
  [[ "$a" == "--force" ]] && { FORCE=1; continue; }
  ONLY+=("$a")
done

mkdir -p frames

tail -n +2 scenes.tsv | while IFS=$'\t' read -r id refs voice narration image_prompt motion_prompt; do
  [[ -z "$id" || "$id" == \#* ]] && continue
  if (( ${#ONLY} )) && [[ ! " ${ONLY[*]} " == *" $id "* ]]; then continue; fi

  out="frames/${id}.png"
  if [[ -f "$out" && $FORCE -eq 0 ]]; then
    echo "= cena $id: frame já existe — pulando"; continue
  fi

  # refs = chaves de personagem separadas por vírgula (ou "-" p/ nenhuma)
  imgargs=()
  if [[ "$refs" != "-" && -n "$refs" ]]; then
    for k in ${(s:,:)refs}; do
      ref="assets/${k}_ref.png"
      if [[ -f "$ref" ]]; then imgargs+=(--image "$ref")
      else echo "  ⚠ ref '$k' sem referência ($ref) — gere com ./gen-sheets.sh"; fi
    done
  fi

  echo "=== cena $id (refs: ${refs}) ==="
  if [[ "${GEN_PROVIDER:-higgsfield}" == "kie" ]]; then
    kie_imgargs=()
    for pair in "${imgargs[@]}"; do
      [[ "$pair" == "--image" ]] && continue
      kie_imgargs+=(--image "$pair")
    done
    "$KIE_HELPER" image \
      --kind frame --id "$id" --out "$out" \
      --prompt "$image_prompt, $ANTICLONE, $STYLE" \
      "${kie_imgargs[@]}" \
      --aspect-ratio "$ASPECT" --resolution "$IMG_RES" \
      --model "${KIE_IMAGE_MODEL:-google/nanobanana2}" \
      --usage-log "${KIE_USAGE_LOG:-build/kie-usage.tsv}" \
      --upload-path "${SLUG}/frames" && echo "  ✓ $out"
  else
    url=$(higgsfield generate create nano_banana_2 \
      --prompt "$image_prompt, $ANTICLONE, $STYLE" \
      "${imgargs[@]}" \
      --aspect_ratio "$ASPECT" --resolution "$IMG_RES" \
      --wait --wait-timeout 8m 2>&1 | tail -1)
    if [[ "$url" == http* ]]; then
      curl -s -o "$out" "$url" && echo "  ✓ $out"
    else
      echo "  ✗ FALHOU: $url"
    fi
  fi
done
echo "=== frames concluídos ==="
