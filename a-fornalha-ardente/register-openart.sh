#!/bin/zsh
# Normaliza, valida e registra resultados produzidos pelo lote OpenArt MCP.
source "${0:A:h}/_lib.sh"

if (( $# < 1 )); then
  echo "Uso: $0 <reference|frame|clip> [all|id ...]" >&2
  exit 2
fi

KIND="$1"
shift

case "$KIND" in
  reference|frame|clip) ;;
  *)
    echo "ERRO: tipo inválido: $KIND" >&2
    exit 2
    ;;
esac

validate_stage production
require_command ffmpeg
require_command ffprobe

python3 "$OPENART_HELPER" register \
  --episode "$EPISODE_DIR" \
  --kind "$KIND" \
  "$@"
