#!/bin/zsh
# Produz o guia para animação manual no Higgsfield/Seedance.
source "${0:A:h}/_lib.sh"

validate_stage production
KIT="KIT-PRODUCAO.md"
prepare_rows scenes SCENE_ROWS
scene_count=$(wc -l < "$SCENE_ROWS" | tr -d ' ')

{
  echo "# KIT DE PRODUÇÃO — $TITLE"
  echo
  echo "> Pipeline v2 · ${scene_count} planos · ${VIDEO_DUR}s por clipe · $ASPECT."
  echo "> O áudio gerado pelo modelo de vídeo deve ficar DESLIGADO; vozes e SFX são mixados separadamente."
  echo
  echo "## Configuração por clipe"
  echo
  echo "1. Use Seedance/Kling em alta qualidade, $ASPECT, ${VIDEO_DUR}s."
  echo "2. Suba \`frames/NN.png\` pela aba de uploads."
  echo "3. Desligue geração de áudio e lip-sync."
  echo "4. Cole o prompt integral da cena."
  echo "5. Rejeite clipes com morphing, personagem duplicado, rosto/roupa alterados, mãos deformadas ou câmera sem intenção."
  echo "6. Salve o aprovado como \`clips/NN.mp4\`."
  echo "7. Depois de todos os downloads, rode \`./register-clips.sh\` para validar e vincular cada clipe ao frame/prompt usado."
  echo "8. Após assistir aos arquivos registrados, rode \`./approve-visual.sh clip all\`."
  echo
  echo "---"
  echo

  while IFS=$'\t' read -r id act shot refs voice text hold image_prompt motion_prompt vfx sfx transition; do
    [[ -z "$id" ]] && continue
    python3 "$PIPELINE" verify-visual \
      --episode "$EPISODE_DIR" --kind frame --identifier "$id" >/dev/null
    prompt=$(python3 "$PIPELINE" prompt --episode "$EPISODE_DIR" \
      --scene "$id" --media clip)

    echo "## Cena $id · $act"
    echo
    echo "- **Plano:** $shot"
    echo "- **Voz:** $voice"
    echo "- **Texto:** $text"
    echo "- **Respiro:** ${hold}s"
    echo "- **VFX:** $vfx"
    echo "- **SFX planejado:** $sfx"
    echo "- **Transição:** $transition"
    echo "- **Frame:** \`frames/${id}.png\`"
    echo "- **Saída:** \`clips/${id}.mp4\`"
    echo
    echo "**Prompt integral:**"
    echo
    echo '```text'
    echo "$prompt"
    echo '```'
    echo
    echo "**Checklist:** identidade estável · ação legível · câmera motivada · física natural · VFX integrado · sem áudio gerado."
    echo
    echo "---"
    echo
  done < "$SCENE_ROWS"
} > "$KIT"

echo "KIT: $EPISODE_DIR/$KIT"
