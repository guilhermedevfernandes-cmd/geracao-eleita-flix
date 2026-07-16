#!/bin/zsh
# Gera a narração PT-BR de cada cena via ElevenLabs **v3 (API direta)** — NUNCA o
# TTS do HiggsField (regra do canal). Usa ../scripts/elevenlabs_audio.py (modelo
# eleven_v3 + voice_settings stability 1.0 "Robusto"). A expressão vem das AUDIO
# TAGS no próprio texto de scenes.tsv ([warm], [calm], [awe], [sad]...).
# Voz por cena (coluna "voice" de scenes.tsv):
#   - "narrator" (ou vazio) → NARRATOR_VOICE do meta.env (Lucas – Deep & Profound)
#   - <chave> de personagem  → voice_id daquela linha em characters.tsv
#     (daniel → Felipette · rei → Adam Borges)
# Salva em audio/NN.mp3. Pula os que já existem (use --force p/ refazer).
# Uso: ./gen-narr.sh [id1 id2 ...]  (sem args = todas)  |  --force
set -u
cd "${0:A:h}"
source ./meta.env
EL="../scripts/elevenlabs_audio.py"

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
rc=0

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

  echo "=== narr $id (voz: ${voice:-narrator} / $vid) ==="
  forceflag=(); [[ $FORCE -eq 1 ]] && forceflag=(--force)
  python3 "$EL" tts --text "$narration" --voice-id "$vid" --out "$out" "${forceflag[@]}"
  if [[ $? -ne 0 ]]; then echo "  ✗ FALHOU cena $id"; rc=1; fi
done
echo "=== narração concluída (rc=$rc) ==="
exit $rc
