#!/usr/bin/env bash
set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${1:-$HOME/code/personal/.env.personal}"
NOTE_FILE="${2:-$HOME/code/personal/personal-stack-operator-note.md}"
DATA_ROOT_DEFAULT="$HOME/apex-data/personal"
SECRETS_ROOT_DEFAULT="$HOME/apex-secrets/personal"
TEMPLATE_ENV="$SCRIPT_ROOT/.env.personal.template"
TEMPLATE_NOTE="$SCRIPT_ROOT/personal-stack-operator-note.template.md"

mkdir -p "$(dirname "$ENV_FILE")"
mkdir -p "$(dirname "$NOTE_FILE")"
mkdir -p "$DATA_ROOT_DEFAULT/memos"
mkdir -p "$SECRETS_ROOT_DEFAULT"

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$TEMPLATE_ENV" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
fi

if [[ ! -f "$NOTE_FILE" ]]; then
  sed \
    -e "s|{{ENV_FILE}}|$ENV_FILE|g" \
    -e "s|{{DATA_ROOT}}|$DATA_ROOT_DEFAULT|g" \
    -e "s|{{SECRETS_ROOT}}|$SECRETS_ROOT_DEFAULT|g" \
    "$TEMPLATE_NOTE" > "$NOTE_FILE"
  chmod 600 "$NOTE_FILE"
fi

echo "Prepared personal stack host paths:"
echo "  env file: $ENV_FILE"
echo "  note file: $NOTE_FILE"
echo "  data root: $DATA_ROOT_DEFAULT"
echo "  secrets root: $SECRETS_ROOT_DEFAULT"
echo ""
echo "Next steps:"
echo "  1. Review the env file and keep PERSONAL_NOTES_PORT host-only."
echo "  2. Use bash infra/private/run-personal-stack.sh config"
echo "  3. Use bash infra/private/run-personal-stack.sh up"
