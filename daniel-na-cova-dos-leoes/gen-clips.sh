#!/bin/zsh
# Anima cada frame (frames/NN.png) em vídeo via KLING na CLI higgsfield.
# Usa o frame como primeiro quadro (--image) + o motion_prompt da cena.
# Lê scenes.tsv. Salva em clips/NN.mp4. Pula os que já existem.
# Modelo/resolução/duração vêm do meta.env (VIDEO_MODEL/VIDEO_RES/VIDEO_DUR).
# Uso: ./gen-clips.sh [id1 id2 ...]   (sem args = todas)  |  --force
set -u
cd "${0:A:h}"
source ./meta.env
KIE_HELPER="../scripts/kie_task.py"

FORCE=0
ONLY=()
for a in "$@"; do
  [[ "$a" == "--force" ]] && { FORCE=1; continue; }
  ONLY+=("$a")
done

mkdir -p clips

# Monta os flags específicos do modelo escolhido
modelargs=(--aspect_ratio "$ASPECT" --duration "$VIDEO_DUR")
case "$VIDEO_MODEL" in
  kling3_0_turbo) modelargs+=(--resolution "$VIDEO_RES") ;;
  kling3_0)       modelargs+=(--mode std --sound off) ;;
  kling2_6)       modelargs+=(--sound false) ;;
esac

tail -n +2 scenes.tsv | while IFS=$'\t' read -r id refs voice narration image_prompt motion_prompt; do
  [[ -z "$id" || "$id" == \#* ]] && continue
  if (( ${#ONLY} )) && [[ ! " ${ONLY[*]} " == *" $id "* ]]; then continue; fi

  out="clips/${id}.mp4"
  if [[ -f "$out" && $FORCE -eq 0 ]]; then
    echo "= cena $id: clipe já existe — pulando"; continue
  fi

  frame="frames/${id}.png"
  if [[ ! -f "$frame" ]]; then
    echo "  ⚠ cena $id: frame ausente ($frame) — gere com ./gen-frames.sh"; continue
  fi

  echo "=== cena $id  ($VIDEO_MODEL $VIDEO_RES ${VIDEO_DUR}s) ==="
  if [[ "${GEN_PROVIDER:-higgsfield}" == "kie" ]]; then
    "$KIE_HELPER" video \
      --id "$id" --out "$out" \
      --prompt "$motion_prompt, $STYLE" \
      --image "$frame" \
      --duration "$VIDEO_DUR" \
      --resolution "$VIDEO_RES" \
      --aspect-ratio "$ASPECT" \
      --mode "${KIE_VIDEO_MODE:-pro}" \
      --model "${KIE_VIDEO_MODEL:-kling-3.0/video}" \
      --usage-log "${KIE_USAGE_LOG:-build/kie-usage.tsv}" \
      --upload-path "${SLUG}/clips" && echo "  ✓ $out"
  else
    url=$(higgsfield generate create "$VIDEO_MODEL" \
      --prompt "$motion_prompt, $STYLE" \
      --image "$frame" \
      "${modelargs[@]}" \
      --wait --wait-timeout 15m 2>&1 | tail -1)
    if [[ "$url" == http* ]]; then
      curl -s -o "$out" "$url" && echo "  ✓ $out"
    else
      echo "  ✗ FALHOU: $url"
    fi
  fi
done
echo "=== clipes concluídos ==="
