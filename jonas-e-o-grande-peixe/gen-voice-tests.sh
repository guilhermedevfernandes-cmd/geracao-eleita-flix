#!/bin/zsh
# Gera amostras curtas. A aprovação humana do sotaque PT-BR é obrigatória.
source "${0:A:h}/_lib.sh"

validate_stage production

FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1
mkdir -p audio/voice-tests

TEST_LINE=$(python3 "$PIPELINE" voice-test-text)
prepare_rows characters CHARACTER_ROWS

{
  echo "# Audição obrigatória de vozes — $TITLE"
  echo
  echo "Escute cada arquivo com fones. Aprove somente pronúncia e sotaque naturais do português brasileiro."
  echo "Se soar português de Portugal, robótico ou inconsistente, troque o voice_id e gere novamente."
  echo
} > audio/voice-tests/README.md

while IFS=$'\t' read -r key name voice_id locale approved sheet_prompt; do
  [[ -z "$key" || "$voice_id" == "-" ]] && continue

  if [[ "$locale" != "pt-BR" ]]; then
    echo "ERRO: $key está com locale '$locale'; esperado pt-BR" >&2
    exit 1
  fi
  if [[ ! "$voice_id" =~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$' ]]; then
    echo "ERRO: defina um voice_id candidato válido para '$key' antes da audição" >&2
    exit 1
  fi

  out="audio/voice-tests/${key}.mp3"
  args=(tts --text "$TEST_LINE" --voice-id "$voice_id" --out "$out")
  (( FORCE )) && args+=(--force)
  python3 "$AUDIO_HELPER" "${args[@]}"
  fingerprint=$(python3 "$CACHE_HELPER" verify --output "$out")
  echo "- [ ] **$name** (\`$key\`) — \`${key}.mp3\` — voice_id \`$voice_id\` — amostra \`${fingerprint}\`" >> audio/voice-tests/README.md
done < "$CHARACTER_ROWS"

cat >> audio/voice-tests/README.md <<'EOF'

Depois de ouvir:

1. Troque qualquer voz inadequada em `characters.tsv` e gere novamente.
2. Para cada amostra aprovada, rode `./approve-voice.sh <key>`.
3. A aprovação fica vinculada ao voice_id, texto de teste e hash do áudio ouvido.
4. Se qualquer um deles mudar, `./gen-narr.sh` bloqueará automaticamente.
EOF

echo "AMOSTRAS: $EPISODE_DIR/audio/voice-tests/"
echo "AÇÃO HUMANA: ouvir e aprovar cada voz antes da narração."
