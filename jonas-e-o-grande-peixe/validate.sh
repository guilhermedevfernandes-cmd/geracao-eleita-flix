#!/bin/zsh
source "${0:A:h}/_lib.sh"

STAGE="${1:-script}"
validate_stage "$STAGE"
