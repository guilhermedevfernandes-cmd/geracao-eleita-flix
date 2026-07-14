#!/bin/zsh
# Cria um episódio novo usando exclusivamente o pipeline de qualidade v2.
set -eu

SCRIPT_DIR="${0:A:h}"
PROJECT_ROOT="${SCRIPT_DIR:h}"
TEMPLATE_DIR="${PROJECT_ROOT}/templates/episode-v2"

if (( $# < 2 || $# > 3 )); then
  echo "Uso: $0 <slug> \"Título\" [diretório-de-saída]" >&2
  exit 2
fi

SLUG_INPUT="$1"
TITLE_INPUT="$2"
OUTPUT_ROOT="${3:-$PROJECT_ROOT}"

[[ "$SLUG_INPUT" =~ '^[a-z0-9]+([a-z0-9-]*[a-z0-9])?$' ]] || {
  echo "ERRO: slug deve usar apenas letras minúsculas, números e hífens" >&2
  exit 1
}
[[ -d "$TEMPLATE_DIR" ]] || {
  echo "ERRO: template v2 ausente: $TEMPLATE_DIR" >&2
  exit 1
}
[[ -d "$OUTPUT_ROOT" ]] || {
  echo "ERRO: diretório de saída não existe: $OUTPUT_ROOT" >&2
  exit 1
}

DEST="${OUTPUT_ROOT:A}/${SLUG_INPUT}"
[[ ! -e "$DEST" ]] || {
  echo "ERRO: destino já existe: $DEST" >&2
  exit 1
}

cp -R "$TEMPLATE_DIR" "$DEST"
mkdir -p "$DEST/assets" "$DEST/frames" "$DEST/clips" \
  "$DEST/audio/voice-tests" "$DEST/audio/sfx" "$DEST/build" \
  "$DEST/logs" "$DEST/approvals" "$DEST/_pipeline"
cp "$PROJECT_ROOT/scripts/episode_pipeline.py" "$DEST/_pipeline/"
cp "$PROJECT_ROOT/scripts/elevenlabs_audio.py" "$DEST/_pipeline/"
cp "$PROJECT_ROOT/scripts/artifact_cache.py" "$DEST/_pipeline/"
cp "$PROJECT_ROOT/scripts/audio_contract.py" "$DEST/_pipeline/"
cp "$PROJECT_ROOT/scripts/openart_batch.py" "$DEST/_pipeline/"
cp "$PROJECT_ROOT/PRODUCTION-BRIEF.md" "$DEST/"

python3 - "$DEST/meta.env" "$SLUG_INPUT" "$TITLE_INPUT" <<'PY'
from pathlib import Path
import shlex
import sys

path = Path(sys.argv[1])
slug = sys.argv[2]
title = sys.argv[3]
if any(ord(char) < 32 for char in title):
    raise SystemExit("ERRO: título contém caractere de controle")

lines = []
for line in path.read_text(encoding="utf-8").splitlines():
    if line.startswith("TITLE="):
        line = f"TITLE={shlex.quote(title)}"
    elif line.startswith("SLUG="):
        line = f"SLUG={shlex.quote(slug)}"
    lines.append(line)
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

chmod +x "$DEST"/*.sh "$DEST/_pipeline"/*.py

echo "EPISÓDIO CRIADO: $DEST"
echo
echo "Próximos passos:"
echo "1. Preencha characters.tsv com elenco e IDs candidatos."
echo "2. Escreva scenes.tsv seguindo PRODUCTION-BRIEF.md."
echo "3. Rode ./validate.sh script, ./make-roteiro.sh e ./approve-script.sh."
echo "4. Gere e aprove as vozes antes de qualquer narração."
echo "5. Gere referências, frames e clipes em lotes paralelos pelo MCP OpenArt."
echo "6. Registre cada lote com ./register-openart.sh e revise os gates visuais."
