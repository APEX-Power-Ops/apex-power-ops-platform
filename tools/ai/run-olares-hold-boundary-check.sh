#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../shell/common.sh"

repo_root="$(get_apex_repo_root)"
import_apex_env_file
repo_python="$(get_apex_preferred_python)"

packet_id="${1:-}"
if [[ -z "${packet_id}" ]]; then
  packet_id="$(get_apex_default_packet_id hold-boundary)"
fi
require_apex_packet_id "${packet_id}"
dsn_env="${2:-}"
state_dir="${repo_root}/.tmp/ai-workflow"
mcp_contract_actual_dir="${repo_root}/tests/canary/mcp-contract/actual"
deferred_ops_actual_dir="${repo_root}/tests/canary/deferred-ops-view-counts/actual"
minimal_state_file="${state_dir}/minimal-mcp-trio.env"
minimal_output="${mcp_contract_actual_dir}/verify-minimal-mcp-trio-${packet_id}.json"
hold_output="${deferred_ops_actual_dir}/deferred-ops-view-counts-${packet_id}.json"
live_db_port="${APEX_HOLD_BOUNDARY_DB_PORT:-8721}"
live_db_url="http://127.0.0.1:${live_db_port}/mcp"
live_db_pid=""
live_db_root="${repo_root}/services/mcp/apex-db"

mkdir -p "${state_dir}"
mkdir -p "${state_dir}/logs"
mkdir -p "${mcp_contract_actual_dir}"
mkdir -p "${deferred_ops_actual_dir}"

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
hold_helper_output="${state_dir}/hold-boundary-helper-output.json"

if [[ -z "${dsn_env}" && -f "${minimal_state_file}" ]]; then
  # shellcheck disable=SC1090
  source "${minimal_state_file}"
  if [[ -n "${DB_ENDPOINT:-}" ]]; then
    hold_args+=(--db-url "${DB_ENDPOINT}")
  fi
fi

if [[ -n "${dsn_env}" ]]; then
  if "${repo_python}" -c 'import sqlalchemy' >/dev/null 2>&1; then
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
  rm -f "${hold_helper_output}"
}

trap cleanup EXIT

hold_source="${hold_output}"
if "${repo_python}" "${hold_args[@]}" >"${hold_helper_output}"; then
  hold_exit_code=0
else
  hold_exit_code=$?
  if [[ ! -f "${hold_output}" ]]; then
    if [[ -s "${hold_helper_output}" ]]; then
      hold_source="${hold_helper_output}"
    else
      exit "${hold_exit_code}"
    fi
  fi
fi

"${repo_python}" - <<'PY' "${packet_id}" "${minimal_output}" "${hold_output}" "${hold_source}"
import json
import sys
from pathlib import Path

packet_id = sys.argv[1]
minimal = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
hold = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
if hold.get("result") == "FAIL":
  decision = hold.get("error") or hold.get("output_error") or hold.get("decision")
else:
  decision = hold.get("decision") or hold.get("error") or hold.get("output_error")

print(json.dumps({
    "packet_id": packet_id,
    "minimal_mcp": minimal.get("result"),
    "deferred_ops": hold.get("result"),
    "deferred_ops_decision": decision,
    "outputs": {
        "minimal_mcp": sys.argv[2],
        "deferred_ops": sys.argv[3],
    },
}, indent=2))
PY

exit "${hold_exit_code}"