#!/bin/zsh
# Gera o KIT-PRODUCAO.md: o passo a passo para VOCÊ animar cada frame
# manualmente no site (Seedance 2.0 Fast = grátis/ilimitado).
# Lê meta.env + scenes.tsv. Saída: KIT-PRODUCAO.md
set -u
cd "${0:A:h}"
source ./meta.env

KIT="KIT-PRODUCAO.md"
n=$(tail -n +2 scenes.tsv | grep -vc '^[[:space:]]*$')

{
  echo "# 🎬 KIT DE PRODUÇÃO — $TITLE"
  echo
  echo "> Anime cada frame no **site higgsfield.ai** com **Seedance 2.0 Fast** (grátis/ilimitado)."
  echo "> Regra: **Imagem = Nano Banana Pro** (já gerada em \`frames/\`) · **Vídeo = Seedance 2.0 Fast**."
  echo
  echo "## Para CADA cena (repete ${n}x)"
  echo "1. Abra o **Seedance 2.0 Fast** · modo **fast** · **$ASPECT** · 720p/1080p · duração **${CLIP_SECONDS}s**."
  echo "2. **Desligue \"generate audio\"** (a narração entra na montagem)."
  echo "3. Suba o frame correspondente da pasta \`frames/\` (\`NN.png\`)."
  echo "4. Cole o **PROMPT DE MOVIMENTO** abaixo. Gere. Baixe o MP4 → salve em \`clips/NN.mp4\`."
  echo
  echo "> ⚠️ A numeração (\`01.mp4\`, \`02.mp4\`, …) é o que permite montar na ordem certa."
  echo
  echo "---"
  echo

  tail -n +2 scenes.tsv | while IFS=$'\t' read -r id refs voice narration image_prompt motion_prompt; do
    [[ -z "$id" || "$id" == \#* ]] && continue
    echo "### Cena $id  ·  refs: ${refs}"
    [[ -n "$narration" ]] && echo "🗣️ **Narração (${voice:-narrator}):** \"$narration\""
    echo "🖼️ **Frame:** \`frames/${id}.png\`"
    echo "🎞️ **Movimento (cole no Seedance):** \`${motion_prompt}. ${STYLE}\`"
    echo
  done

  echo "---"
  echo
  echo "## Depois de animar todas"
  echo "Coloque os clipes em \`clips/\` (\`01.mp4\` … numerados). Daí rode:"
  echo '```'
  echo "./gen-narr.sh      # narração PT-BR"
  echo "# coloque uma música de fundo infantil suave em audio/bgm.mp3"
  echo "./assemble.sh      # MP4 final"
  echo '```'
} > "$KIT"

echo "✓ $KIT gerado ($n cenas)."
