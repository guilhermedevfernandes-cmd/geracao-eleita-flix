#!/bin/zsh
# Execute somente depois de ler e aprovar roteiro.md.
source "${0:A:h}/_lib.sh"

python3 "$PIPELINE" approve-script --episode "$EPISODE_DIR" "$@"
