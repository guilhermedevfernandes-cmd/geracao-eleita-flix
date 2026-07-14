#!/bin/zsh
# Prepara todos os planos pendentes para animação paralela via OpenArt MCP.
source "${0:A:h}/_lib.sh"

validate_stage production

python3 "$OPENART_HELPER" plan \
  --episode "$EPISODE_DIR" \
  --kind clip \
  "$@"
