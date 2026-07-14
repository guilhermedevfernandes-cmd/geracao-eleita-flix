#!/bin/zsh
# Gera o roteiro.md: o documento LEGÍVEL do episódio (para você ler e aprovar
# ANTES de gerar referências/frames). É derivado do scenes.tsv + characters.tsv,
# então roteiro.md e a produção nunca divergem.
# Lê meta.env + scenes.tsv + characters.tsv. Saída: roteiro.md
set -u
cd "${0:A:h}"
source ./meta.env

OUT="roteiro.md"
n=$(tail -n +2 scenes.tsv | grep -vc '^[[:space:]]*$')
# duração estimada: ~0,4s por palavra de narração + respiro
secs=$(tail -n +2 scenes.tsv | awk -F'\t' 'NF{nw=split($4,a," "); t+=nw*0.4+0.6} END{printf "%d", t}')
mins=$(( secs / 60 )); rest=$(( secs % 60 ))

{
  echo "# $TITLE — Roteiro (Disney/Pixar 3D · $ASPECT · ~${mins}min${rest}s)"
  echo
  echo "**Narração:** voz masculina calorosa, PT-BR, tom de \"vovô contador de histórias\"."
  echo "**Estrutura:** ${n} cenas (estimativa ~${secs}s no total)."
  echo "**Estilo visual (constante em todo prompt):** \`${STYLE}\`"
  echo
  echo "**Personagens (consistência via referência única):**"
  tail -n +2 characters.tsv | while IFS=$'\t' read -r key name voice_id prompt; do
    [[ -z "$key" || "$key" == \#* ]] && continue
    if [[ -n "$prompt" ]]; then
      echo "- **$name** (\`$key\`) — ${prompt}."
    else
      echo "- **$name** (\`$key\`) — apenas voz (não aparece em cena)."
    fi
  done
  echo
  echo "---"
  echo

  tail -n +2 scenes.tsv | while IFS=$'\t' read -r id refs voice narration image_prompt motion_prompt; do
    [[ -z "$id" || "$id" == \#* ]] && continue
    echo "## Cena $id"
    if [[ -n "$voice" && "$voice" != "narrator" ]]; then
      echo "**Voz:** $voice (fala em 1ª pessoa — NÃO o narrador)."
      echo "**Fala:** \"$narration\""
    else
      echo "**Narração:** \"$narration\""
    fi
    echo "**Visual:** $image_prompt."
    echo "**Movimento:** $motion_prompt."
    [[ "$refs" != "-" && -n "$refs" ]] && echo "**Refs:** $refs."
    echo
  done

  echo "---"
  echo
  echo "### Notas de produção"
  echo "- Cada cena vira: 1 frame (Nano Banana Pro) → 1 clipe de ${CLIP_SECONDS}s (Seedance 2.0 Fast, manual) → narração sincronizada."
  echo "- Vilões/perigo sempre \"ameaçador-fofo\", nunca aterrorizante (público infantil)."
  echo "- Clímax sem violência gráfica."
  echo "- Fonte única de verdade: \`scenes.tsv\`. Editou o roteiro? edite o TSV e rode \`./make-roteiro.sh\` de novo."
} > "$OUT"

echo "✓ $OUT gerado (${n} cenas, ~${mins}min${rest}s)."
