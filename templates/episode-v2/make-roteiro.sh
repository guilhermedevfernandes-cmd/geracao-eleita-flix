#!/bin/zsh
source "${0:A:h}/_lib.sh"

python3 "$PIPELINE" script --episode "$EPISODE_DIR" --output "$EPISODE_DIR/roteiro.md"
