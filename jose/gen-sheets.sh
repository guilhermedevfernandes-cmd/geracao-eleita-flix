#!/bin/zsh
# Gera a REFERÊNCIA de cada personagem a partir de characters.tsv.
# IMPORTANTE: a referência é UMA FIGURA ÚNICA e limpa (corpo inteiro, pose neutra,
# fundo liso). NUNCA um sheet com várias poses — isso faz o Nano Banana CLONAR o
# personagem (aparecem 2+ cópias) ao gerar os frames. Esta foi a lição do Noé.
# Salva em assets/<key>_ref.png. Pula os que já existem.
# Uso: ./gen-sheets.sh [--force]
set -u
cd "${0:A:h}"
source ./meta.env
KIE_HELPER="../scripts/kie_task.py"

# Enquadramento fixo que garante UMA figura só (a chave da consistência)
REFFRAME="ONE single character, solo, only one person in frame, full-body, standing in a neutral relaxed A-pose facing forward, plain solid light-gray studio background, no other people, no duplicates, clean character reference"

FORCE=0; [[ "${1:-}" == "--force" ]] && FORCE=1
mkdir -p assets

tail -n +2 characters.tsv | while IFS=$'\t' read -r key name voice_id prompt; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  [[ -z "$prompt" ]] && { echo "= $key: sem sheet_prompt (personagem só-voz) — pulando"; continue; }
  out="assets/${key}_ref.png"
  if [[ -f "$out" && $FORCE -eq 0 ]]; then
    echo "= $key: já existe ($out) — pulando (use --force p/ refazer)"; continue
  fi
  echo "=== ref: $name ($key) ==="
  if [[ "${GEN_PROVIDER:-higgsfield}" == "kie" ]]; then
    "$KIE_HELPER" image \
      --kind ref --id "$key" --out "$out" \
      --prompt "$prompt. $REFFRAME, $STYLE" \
      --aspect-ratio "$ASPECT" --resolution "$IMG_RES" \
      --model "${KIE_IMAGE_MODEL:-google/nanobanana2}" \
      --usage-log "${KIE_USAGE_LOG:-build/kie-usage.tsv}" \
      --upload-path "${SLUG}/assets" && echo "  ✓ $out"
  else
    url=$(higgsfield generate create nano_banana_2 \
      --prompt "$prompt. $REFFRAME, $STYLE" \
      --aspect_ratio "$ASPECT" --resolution "$IMG_RES" \
      --wait --wait-timeout 8m 2>&1 | tail -1)
    if [[ "$url" == http* ]]; then
      curl -s -o "$out" "$url" && echo "  ✓ $out"
    else
      echo "  ✗ FALHOU: $url"
    fi
  fi
done
echo "=== referências concluídas ==="
