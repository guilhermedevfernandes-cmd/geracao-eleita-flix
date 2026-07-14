#!/bin/zsh
# Execute somente depois de ouvir e comparar a amostra em audio/voice-tests/.
source "${0:A:h}/_lib.sh"

validate_stage production

if (( $# != 1 )); then
  echo "Uso: $0 <key-da-voz>" >&2
  exit 2
fi

python3 "$PIPELINE" approve-voice \
  --episode "$EPISODE_DIR" \
  --voice "$1"
