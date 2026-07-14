#!/bin/zsh
# Vincula a aprovação humana à trilha exata, gerada ou externa.
source "${0:A:h}/_lib.sh"

validate_stage produced-audio
python3 "$PIPELINE" approve-music --episode "$EPISODE_DIR"
