#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-config}"
ENV_FILE="${ENV_FILE:-$HOME/code/personal/.env.personal}"
WITH_DB="${WITH_DB:-0}"

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_ROOT/../.." && pwd)"
COMPOSE_FILE="$SCRIPT_ROOT/personal-stack.compose.yml"

ARGS=(compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

if [[ "$WITH_DB" == "1" ]]; then
  ARGS+=(--profile db)
fi

case "$ACTION" in
  up)
    ARGS+=(up -d)
    ;;
  down)
    ARGS+=(down)
    ;;
  config)
    ARGS+=(config)
    ;;
  *)
    echo "Unsupported action: $ACTION" >&2
    exit 2
    ;;
esac

cd "$REPO_ROOT"
docker "${ARGS[@]}"