#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../shell/common.sh"

repo_root="$(get_apex_repo_root)"
import_apex_env_file

action="${1:-status}"
packet_id="${2:-2026-05-06-olares-dev-residency-037}"
fs_port="${APEX_DEV_MCP_FS_PORT:-8710}"
db_port="${APEX_DEV_MCP_DB_PORT:-8711}"
jobs_port="${APEX_DEV_MCP_JOBS_PORT:-8712}"

state_dir="${repo_root}/.tmp/ai-workflow"
log_dir="${state_dir}/logs"
state_file="${state_dir}/minimal-mcp-trio.env"
ledger_path="${repo_root}/.apex-data/apex-jobs-ledger.json"

mkdir -p "${log_dir}"

get_db_connection_string() {
  if [[ -n "${APEX_DB_CONNECTION_STRING:-}" ]]; then
    printf '%s' "${APEX_DB_CONNECTION_STRING}"
    return
  fi

  if [[ -n "${DATABASE_URL:-}" ]]; then
    printf '%s' "${DATABASE_URL}"
    return
  fi

  if [[ -n "${APEX_DEV_POSTGRES_USER:-}" && -n "${APEX_DEV_POSTGRES_PASSWORD:-}" && -n "${APEX_DEV_POSTGRES_DB:-}" && -n "${APEX_DEV_POSTGRES_PORT:-}" ]]; then
    printf 'postgresql://%s:%s@127.0.0.1:%s/%s' "${APEX_DEV_POSTGRES_USER}" "${APEX_DEV_POSTGRES_PASSWORD}" "${APEX_DEV_POSTGRES_PORT}" "${APEX_DEV_POSTGRES_DB}"
    return
  fi

  printf ''
}

write_state() {
  cat > "${state_file}"
}

load_state() {
  if [[ -f "${state_file}" ]]; then
    # shellcheck disable=SC1090
    source "${state_file}"
    return 0
  fi
  return 1
}

is_running() {
  local pid="$1"
  if [[ -z "${pid}" ]]; then
    return 1
  fi
  kill -0 "${pid}" >/dev/null 2>&1
}

is_healthy() {
  local port="$1"
  curl -fsS "http://127.0.0.1:${port}/health" >/dev/null 2>&1
}

start_process() {
  local name="$1"
  shift
  nohup "$@" >"${log_dir}/${name}.log" 2>&1 &
  printf '%s' "$!"
}

case "${action}" in
  up)
    if load_state && is_running "${FS_PID}" && is_running "${DB_PID}" && is_running "${JOBS_PID}"; then
      printf '{"status":"already-running"}\n'
      exit 0
    fi

    if is_healthy "${fs_port}" && is_healthy "${db_port}" && is_healthy "${jobs_port}"; then
      write_state <<EOF
STARTED_AT='$(date -u +%Y-%m-%dT%H:%M:%SZ)'
PACKET_ID='${packet_id}'
MODE='adopted'
FS_PID=''
DB_PID=''
JOBS_PID=''
LEDGER_PATH='${ledger_path}'
FS_ENDPOINT='http://127.0.0.1:${fs_port}/mcp'
DB_ENDPOINT='http://127.0.0.1:${db_port}/mcp'
JOBS_ENDPOINT='http://127.0.0.1:${jobs_port}/mcp'
EOF
      printf '{"status":"adopted"}\n'
      exit 0
    fi

    db_connection_string="$(get_db_connection_string)"
    fs_pid="$(start_process apex-fs env APEX_MCP_HTTP_PORT="${fs_port}" APEX_MCP_WORKSPACE_ROOT="${repo_root}" APEX_MCP_DATA_ROOT="${repo_root}/.apex-data" node services/mcp/apex-fs/build/http.js)"
    db_pid="$(start_process apex-db env APEX_MCP_HTTP_PORT="${db_port}" APEX_DB_CONNECTION_STRING="${db_connection_string}" node services/mcp/apex-db/build/http.js)"
    jobs_pid="$(start_process apex-jobs env APEX_MCP_HTTP_PORT="${jobs_port}" APEX_JOBS_LEDGER_PATH="${ledger_path}" node services/mcp/apex-jobs/build/http.js)"

    write_state <<EOF
STARTED_AT='$(date -u +%Y-%m-%dT%H:%M:%SZ)'
PACKET_ID='${packet_id}'
MODE='managed'
FS_PID='${fs_pid}'
DB_PID='${db_pid}'
JOBS_PID='${jobs_pid}'
LEDGER_PATH='${ledger_path}'
FS_ENDPOINT='http://127.0.0.1:${fs_port}/mcp'
DB_ENDPOINT='http://127.0.0.1:${db_port}/mcp'
JOBS_ENDPOINT='http://127.0.0.1:${jobs_port}/mcp'
EOF
    printf '{"status":"started"}\n'
    ;;
  down)
    if ! load_state; then
      printf '{"status":"not-running"}\n'
      exit 0
    fi
    if [[ "${MODE:-managed}" != "adopted" ]]; then
      for pid in "${FS_PID:-}" "${DB_PID:-}" "${JOBS_PID:-}"; do
        if is_running "${pid}"; then
          kill "${pid}"
        fi
      done
    fi
    rm -f "${state_file}"
    printf '{"status":"stopped"}\n'
    ;;
  status)
    if ! load_state; then
      printf '{"status":"not-running"}\n'
      exit 0
    fi
    cat <<EOF
{"started_at":"${STARTED_AT}","packet_id":"${PACKET_ID}","mode":"${MODE:-managed}","fs_running":$(if [[ "${MODE:-managed}" == "adopted" ]]; then is_healthy "${fs_port}" && printf true || printf false; else is_running "${FS_PID:-}" && printf true || printf false; fi),"db_running":$(if [[ "${MODE:-managed}" == "adopted" ]]; then is_healthy "${db_port}" && printf true || printf false; else is_running "${DB_PID:-}" && printf true || printf false; fi),"jobs_running":$(if [[ "${MODE:-managed}" == "adopted" ]]; then is_healthy "${jobs_port}" && printf true || printf false; else is_running "${JOBS_PID:-}" && printf true || printf false; fi),"ledger_path":"${LEDGER_PATH}","fs_endpoint":"${FS_ENDPOINT:-http://127.0.0.1:${fs_port}/mcp}","db_endpoint":"${DB_ENDPOINT:-http://127.0.0.1:${db_port}/mcp}","jobs_endpoint":"${JOBS_ENDPOINT:-http://127.0.0.1:${jobs_port}/mcp}"}
EOF
    ;;
  verify)
    python tools/ai/verify_minimal_mcp_trio.py --packet-id "${packet_id}" --output "${state_dir}/verify-minimal-mcp-trio.json"
    ;;
  *)
    printf 'Unknown action: %s\n' "${action}" >&2
    exit 1
    ;;
esac