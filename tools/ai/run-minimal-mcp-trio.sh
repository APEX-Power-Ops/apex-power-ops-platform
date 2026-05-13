#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../shell/common.sh"

repo_root="$(get_apex_repo_root)"
import_apex_env_file
repo_python="$(get_apex_preferred_python)"

action="${1:-status}"
packet_id="${2:-}"
packet_id_was_provided=true
if [[ -z "${packet_id}" ]]; then
  packet_id_was_provided=false
  packet_id="$(get_apex_default_packet_id minimal-mcp-trio)"
fi
require_apex_packet_id "${packet_id}"
fs_port="${APEX_DEV_MCP_FS_PORT:-8810}"
db_port="${APEX_DEV_MCP_DB_PORT:-8811}"
jobs_port="${APEX_DEV_MCP_JOBS_PORT:-8812}"
managed_ready_attempts="${APEX_MINIMAL_MCP_READY_ATTEMPTS:-50}"
managed_ready_interval_seconds="${APEX_MINIMAL_MCP_READY_INTERVAL_SECONDS:-0.2}"

state_dir="${repo_root}/.tmp/ai-workflow"
log_dir="${state_dir}/logs"
state_file="${state_dir}/minimal-mcp-trio.env"
ledger_path="${repo_root}/.apex-data/apex-jobs-ledger.json"
mcp_contract_actual_dir="${repo_root}/tests/canary/mcp-contract/actual"
verify_output="${mcp_contract_actual_dir}/verify-minimal-mcp-trio-${packet_id}.json"

fs_endpoint="http://127.0.0.1:${fs_port}/mcp"
db_endpoint="http://127.0.0.1:${db_port}/mcp"
jobs_endpoint="http://127.0.0.1:${jobs_port}/mcp"

mkdir -p "${log_dir}" "${mcp_contract_actual_dir}"

managed_entrypoints=(
  "services/mcp/apex-fs/build/http.js"
  "services/mcp/apex-db/build/http.js"
  "services/mcp/apex-jobs/build/http.js"
)

get_db_connection_string() {
  if [[ -n "${APEX_OLARES_LIVE_DSN:-}" ]]; then
    printf '%s' "${APEX_OLARES_LIVE_DSN}"
    return
  fi

  if [[ -n "${SEAM_DATABASE_URL:-}" ]]; then
    printf '%s' "${SEAM_DATABASE_URL}"
    return
  fi

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

is_mcp_ready() {
  local endpoint="$1"
  local payload='{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"minimal-mcp-trio","version":"0.1.0"}}}'
  curl -fsS -X POST -H 'Content-Type: application/json' --data "${payload}" "${endpoint}" >/dev/null 2>&1
}

stop_managed_processes() {
  local pid
  for pid in "$@"; do
    if is_running "${pid}"; then
      kill "${pid}" >/dev/null 2>&1 || true
    fi
  done
}

wait_for_managed_readiness() {
  local fs_pid="$1"
  local db_pid="$2"
  local jobs_pid="$3"
  local attempt

  managed_fs_running=false
  managed_db_running=false
  managed_jobs_running=false
  managed_fs_ready=false
  managed_db_ready=false
  managed_jobs_ready=false

  for ((attempt = 1; attempt <= managed_ready_attempts; attempt++)); do
    if is_running "${fs_pid}"; then
      managed_fs_running=true
      if is_mcp_ready "${fs_endpoint}"; then
        managed_fs_ready=true
      else
        managed_fs_ready=false
      fi
    else
      managed_fs_running=false
      managed_fs_ready=false
    fi

    if is_running "${db_pid}"; then
      managed_db_running=true
      if is_mcp_ready "${db_endpoint}"; then
        managed_db_ready=true
      else
        managed_db_ready=false
      fi
    else
      managed_db_running=false
      managed_db_ready=false
    fi

    if is_running "${jobs_pid}"; then
      managed_jobs_running=true
      if is_mcp_ready "${jobs_endpoint}"; then
        managed_jobs_ready=true
      else
        managed_jobs_ready=false
      fi
    else
      managed_jobs_running=false
      managed_jobs_ready=false
    fi

    if [[ "${managed_fs_ready}" == true && "${managed_db_ready}" == true && "${managed_jobs_ready}" == true ]]; then
      return 0
    fi

    if [[ "${managed_fs_running}" == false || "${managed_db_running}" == false || "${managed_jobs_running}" == false ]]; then
      return 1
    fi

    if (( attempt < managed_ready_attempts )); then
      sleep "${managed_ready_interval_seconds}"
    fi
  done

  return 1
}

start_process() {
  local name="$1"
  shift
  nohup "$@" >"${log_dir}/${name}.log" 2>&1 &
  printf '%s' "$!"
}

emit_missing_managed_entrypoints() {
  local missing=("$@")
  printf '{"status":"start-refused","reason":"missing-service-entrypoints","missing_entrypoints":['
  local first=true
  local entry
  for entry in "${missing[@]}"; do
    if [[ "${first}" == true ]]; then
      first=false
    else
      printf ','
    fi
    printf '"%s"' "${entry}"
  done
  printf ']}'
}

emit_managed_readiness_failure() {
  printf '{"status":"start-refused","reason":"services-not-ready","fs_running":%s,"db_running":%s,"jobs_running":%s,"fs_ready":%s,"db_ready":%s,"jobs_ready":%s}' \
    "${managed_fs_running}" \
    "${managed_db_running}" \
    "${managed_jobs_running}" \
    "${managed_fs_ready}" \
    "${managed_db_ready}" \
    "${managed_jobs_ready}"
}

case "${action}" in
  up)
    if load_state && is_running "${FS_PID}" && is_running "${DB_PID}" && is_running "${JOBS_PID}"; then
      printf '{"status":"already-running"}\n'
      exit 0
    fi

    if is_mcp_ready "${fs_endpoint}" && is_mcp_ready "${db_endpoint}" && is_mcp_ready "${jobs_endpoint}"; then
      if ownership_probe="$(${repo_python} tools/ai/check_apex_fs_ownership.py --fs-url "${fs_endpoint}" --expected-workspace-root "${repo_root}" --expected-readme-path "${repo_root}/README.md")"; then
        :
      else
        printf '%s\n' "${ownership_probe}"
        exit 1
      fi

      write_state <<EOF
STARTED_AT='$(date -u +%Y-%m-%dT%H:%M:%SZ)'
PACKET_ID='${packet_id}'
MODE='adopted'
FS_PID=''
DB_PID=''
JOBS_PID=''
LEDGER_PATH='${ledger_path}'
FS_ENDPOINT='${fs_endpoint}'
DB_ENDPOINT='${db_endpoint}'
JOBS_ENDPOINT='${jobs_endpoint}'
EOF
      printf '{"status":"adopted"}\n'
      exit 0
    fi

    missing_entrypoints=()
    for entrypoint in "${managed_entrypoints[@]}"; do
      if [[ ! -f "${repo_root}/${entrypoint}" ]]; then
        missing_entrypoints+=("${entrypoint}")
      fi
    done

    if (( ${#missing_entrypoints[@]} > 0 )); then
      emit_missing_managed_entrypoints "${missing_entrypoints[@]}"
      printf '\n'
      exit 1
    fi

    db_connection_string="$(get_db_connection_string)"
    fs_pid="$(start_process apex-fs env APEX_MCP_HTTP_PORT="${fs_port}" APEX_MCP_WORKSPACE_ROOT="${repo_root}" APEX_MCP_DATA_ROOT="${repo_root}/.apex-data" node services/mcp/apex-fs/build/http.js)"
    db_pid="$(start_process apex-db env APEX_MCP_HTTP_PORT="${db_port}" APEX_DB_CONNECTION_STRING="${db_connection_string}" node services/mcp/apex-db/build/http.js)"
    jobs_pid="$(start_process apex-jobs env APEX_MCP_HTTP_PORT="${jobs_port}" APEX_JOBS_LEDGER_PATH="${ledger_path}" node services/mcp/apex-jobs/build/http.js)"

    if ! wait_for_managed_readiness "${fs_pid}" "${db_pid}" "${jobs_pid}"; then
      stop_managed_processes "${fs_pid}" "${db_pid}" "${jobs_pid}"
      emit_managed_readiness_failure
      printf '\n'
      exit 1
    fi

    write_state <<EOF
STARTED_AT='$(date -u +%Y-%m-%dT%H:%M:%SZ)'
PACKET_ID='${packet_id}'
MODE='managed'
FS_PID='${fs_pid}'
DB_PID='${db_pid}'
JOBS_PID='${jobs_pid}'
LEDGER_PATH='${ledger_path}'
FS_ENDPOINT='${fs_endpoint}'
DB_ENDPOINT='${db_endpoint}'
JOBS_ENDPOINT='${jobs_endpoint}'
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
      if is_mcp_ready "${fs_endpoint}" && is_mcp_ready "${db_endpoint}" && is_mcp_ready "${jobs_endpoint}"; then
        cat <<EOF
{"status":"unmanaged-running","mode":"unmanaged","fs_running":true,"db_running":true,"jobs_running":true,"ledger_path":"${ledger_path}","fs_endpoint":"${fs_endpoint}","db_endpoint":"${db_endpoint}","jobs_endpoint":"${jobs_endpoint}"}
EOF
        exit 0
      fi

      printf '{"status":"not-running"}\n'
      exit 0
    fi

    fs_running=$(if [[ "${MODE:-managed}" == "adopted" ]]; then is_mcp_ready "${FS_ENDPOINT:-${fs_endpoint}}" && printf true || printf false; else is_running "${FS_PID:-}" && is_mcp_ready "${FS_ENDPOINT:-${fs_endpoint}}" && printf true || printf false; fi)
    db_running=$(if [[ "${MODE:-managed}" == "adopted" ]]; then is_mcp_ready "${DB_ENDPOINT:-${db_endpoint}}" && printf true || printf false; else is_running "${DB_PID:-}" && is_mcp_ready "${DB_ENDPOINT:-${db_endpoint}}" && printf true || printf false; fi)
    jobs_running=$(if [[ "${MODE:-managed}" == "adopted" ]]; then is_mcp_ready "${JOBS_ENDPOINT:-${jobs_endpoint}}" && printf true || printf false; else is_running "${JOBS_PID:-}" && is_mcp_ready "${JOBS_ENDPOINT:-${jobs_endpoint}}" && printf true || printf false; fi)

    status_value="not-running"
    if [[ "${fs_running}" == "true" && "${db_running}" == "true" && "${jobs_running}" == "true" ]]; then
      status_value="managed-running"
      if [[ "${MODE:-managed}" == "adopted" ]]; then
        status_value="adopted-running"
      fi
    fi

    cat <<EOF
{"status":"${status_value}","started_at":"${STARTED_AT}","packet_id":"${PACKET_ID}","mode":"${MODE:-managed}","fs_running":${fs_running},"db_running":${db_running},"jobs_running":${jobs_running},"ledger_path":"${LEDGER_PATH}","fs_endpoint":"${FS_ENDPOINT:-${fs_endpoint}}","db_endpoint":"${DB_ENDPOINT:-${db_endpoint}}","jobs_endpoint":"${JOBS_ENDPOINT:-${jobs_endpoint}}"}
EOF
    ;;
  verify)
    if [[ "${packet_id_was_provided}" == "false" ]] && load_state && [[ -n "${PACKET_ID:-}" ]]; then
      packet_id="${PACKET_ID}"
      verify_output="${mcp_contract_actual_dir}/verify-minimal-mcp-trio-${packet_id}.json"
    fi
    verify_args=(
      tools/ai/verify_minimal_mcp_trio.py
      --packet-id "${packet_id}"
      --output "${verify_output}"
    )

    if load_state && [[ -n "${FS_ENDPOINT:-}" && -n "${DB_ENDPOINT:-}" && -n "${JOBS_ENDPOINT:-}" ]]; then
      verify_args+=(
        --fs-url "${FS_ENDPOINT}"
        --db-url "${DB_ENDPOINT}"
        --jobs-url "${JOBS_ENDPOINT}"
      )
    fi

    "${repo_python}" "${verify_args[@]}"
    ;;
  *)
    printf 'Unknown action: %s\n' "${action}" >&2
    exit 1
    ;;
esac