#!/bin/zsh
# Registra a aprovação humana do arquivo visual exato revisado.
source "${0:A:h}/_lib.sh"

validate_stage production

kind="${1:-}"
if [[ "$kind" != "reference" && "$kind" != "frame" && "$kind" != "clip" ]]; then
  echo "Uso: ./approve-visual.sh reference|frame|clip ID...|all" >&2
  exit 2
fi
shift

identifiers=("$@")
if (( ${#identifiers[@]} == 0 )); then
  echo "ERRO: informe um ou mais IDs, ou 'all' depois da revisão humana." >&2
  exit 2
fi

if [[ "${identifiers[1]}" == "all" ]]; then
  if (( ${#identifiers[@]} != 1 )); then
    echo "ERRO: use 'all' sozinho." >&2
    exit 2
  fi
  identifiers=()
  if [[ "$kind" == "reference" ]]; then
    prepare_rows characters APPROVAL_ROWS
    while IFS=$'\t' read -r key name voice_id locale approved sheet_prompt; do
      [[ -z "$key" || "$sheet_prompt" == "-" ]] && continue
      identifiers+=("$key")
    done < "$APPROVAL_ROWS"
  else
    prepare_rows scenes APPROVAL_ROWS
    while IFS=$'\t' read -r id rest; do
      [[ -z "$id" ]] && continue
      identifiers+=("$id")
    done < "$APPROVAL_ROWS"
  fi
fi

for identifier in "${identifiers[@]}"; do
  python3 "$PIPELINE" approve-visual \
    --episode "$EPISODE_DIR" \
    --kind "$kind" \
    --identifier "$identifier"
done

echo "APROVAÇÃO VISUAL concluída para ${#identifiers[@]} arquivo(s)."
