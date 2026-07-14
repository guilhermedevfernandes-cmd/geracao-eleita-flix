#!/bin/zsh
# Gera a narração PT-BR de cada cena via ElevenLabs (text2speech_v2).
# A voz é definida na coluna "voice" de scenes.tsv:
#   - "narrator" (ou vazio) → NARRATOR_VOICE do meta.env
#   - uma <chave> de personagem → usa o voice_id daquela linha em characters.tsv
# Lê scenes.tsv. Salva em audio/NN.mp3. Pula os que já existem.
# Uso: ./gen-narr.sh [id1 id2 ...]  (sem args = todas)  |  --force
set -u
cd "${0:A:h}"
source ./meta.env

FORCE=0; ONLY=()
for a in "$@"; do
  [[ "$a" == "--force" ]] && { FORCE=1; continue; }
  ONLY+=("$a")
done

# mapa chave→voice_id dos personagens
typeset -A VOICEMAP
tail -n +2 characters.tsv | while IFS=$'\t' read -r key name voice_id prompt; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  [[ -n "$voice_id" ]] && print -r -- "$key=$voice_id"
done > /tmp/_goal_voices.$$
while IFS='=' read -r k v; do VOICEMAP[$k]="$v"; done < /tmp/_goal_voices.$$
rm -f /tmp/_goal_voices.$$

mkdir -p audio

tail -n +2 scenes.tsv | while IFS=$'\t' read -r id refs voice narration image_prompt motion_prompt; do
  [[ -z "$id" || "$id" == \#* ]] && continue
  [[ -z "$narration" ]] && { echo "= cena $id: sem narração — pulando"; continue; }
  if (( ${#ONLY} )) && [[ ! " ${ONLY[*]} " == *" $id "* ]]; then continue; fi

  out="audio/${id}.mp3"
  if [[ -f "$out" && $FORCE -eq 0 ]]; then
    echo "= cena $id: áudio já existe — pulando"; continue
  fi

  # resolve voz
  vid="$NARRATOR_VOICE"
  if [[ -n "$voice" && "$voice" != "narrator" ]]; then
    if [[ -n "${VOICEMAP[$voice]:-}" ]]; then vid="${VOICEMAP[$voice]}"
    else echo "  ⚠ voz '$voice' sem voice_id em characters.tsv — usando narrador"; fi
  fi

  echo "=== narr $id (voz: ${voice:-narrator}) ==="
  url=$(higgsfield generate create text2speech_v2 \
    --model elevenlabs --voice_id "$vid" --voice_type preset \
    --prompt "$narration" --wait --wait-timeout 5m 2>&1 | tail -1)
  if [[ "$url" == http* ]]; then
    curl -s -o "$out" "$url"
    d=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$out" 2>/dev/null)
    printf "  ✓ %s  %.1fs\n" "$out" "$d"
  else
    echo "  ✗ FALHOU: $url"
  fi
done
echo "=== narração concluída ==="
