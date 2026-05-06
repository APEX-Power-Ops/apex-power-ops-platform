#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../shell/common.sh"

repo_root="$(get_apex_repo_root)"
import_apex_env_file

packet_id="${1:-2026-05-06-olares-dev-residency-056}"
dsn_env="${2:-}"
state_dir="${repo_root}/.tmp/ai-workflow"
minimal_output="${state_dir}/verify-minimal-mcp-trio.json"
hold_output="${state_dir}/deferred-ops-view-counts.json"
live_db_port="${APEX_HOLD_BOUNDARY_DB_PORT:-8721}"
live_db_url="http://127.0.0.1:${live_db_port}/mcp"
live_db_pid=""
live_db_root="${repo_root}/services/mcp/apex-db"

mkdir -p "${state_dir}"
mkdir -p "${state_dir}/logs"

if [[ -n "${dsn_env}" ]]; then
  dsn_value="${!dsn_env:-}"
  if [[ -z "${dsn_value}" ]]; then
    printf '%s\n' "${dsn_env} is not set; cannot run the hold-boundary cadence check against a live DSN." >&2
    exit 1
  fi
  export SEAM_DATABASE_URL="${dsn_value}"
fi

bash "${repo_root}/tools/ai/run-minimal-mcp-trio.sh" verify "${packet_id}" >/dev/null

hold_args=(
  "${repo_root}/tools/ai/check_deferred_ops_view_counts.py"
  --packet-id "${packet_id}"
  --output "${hold_output}"
)

if [[ -n "${dsn_env}" ]]; then
  if python3 -c 'import sqlalchemy' >/dev/null 2>&1; then
    hold_args+=(--db-connection-string-env "SEAM_DATABASE_URL")
  elif [[ -f "${live_db_root}/build/http.js" ]]; then
    live_db_pid="$({
      cd "${live_db_root}"
      nohup env APEX_MCP_HTTP_PORT="${live_db_port}" APEX_DB_CONNECTION_STRING="${SEAM_DATABASE_URL}" node build/http.js >"${state_dir}/logs/live-hold-boundary-db.log" 2>&1 &
      printf '%s' "$!"
    })"

    deadline=$((SECONDS + 15))
    until curl -fsS "http://127.0.0.1:${live_db_port}/health" >/dev/null 2>&1; do
      if (( SECONDS >= deadline )); then
        printf '%s\n' "Timed out waiting for live hold-boundary apex-db on port ${live_db_port}." >&2
        exit 1
      fi
    done

    hold_args+=(--db-url "${live_db_url}")
  fi
fi

cleanup() {
  if [[ -n "${live_db_pid}" ]]; then
    kill "${live_db_pid}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

python3 "${hold_args[@]}" >/dev/null

python3 - <<'PY' "${packet_id}" "${minimal_output}" "${hold_output}"
import json
import sys
from pathlib import Path

packet_id = sys.argv[1]
minimal = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
hold = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))

print(json.dumps({
    "packet_id": packet_id,
    "minimal_mcp": minimal.get("result"),
    "deferred_ops": hold.get("result"),
    "deferred_ops_decision": hold.get("decision"),
    "outputs": {
        "minimal_mcp": sys.argv[2],
        "deferred_ops": sys.argv[3],
    },
}, indent=2))
PY