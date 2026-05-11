#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/shell/common.sh"

repo_root="$(get_apex_repo_root)"
import_apex_env_file
repo_python="$(get_apex_preferred_python)"

forms_runtime_port="${APEX_DEV_FORMS_ENGINE_PORT:-8080}"
p6_runtime_port="${APEX_DEV_P6_INGEST_PORT:-8081}"
fs_mcp_port="${APEX_DEV_MCP_FS_PORT:-8810}"
db_mcp_port="${APEX_DEV_MCP_DB_PORT:-8811}"
jobs_mcp_port="${APEX_DEV_MCP_JOBS_PORT:-8812}"
p6_mcp_port="${APEX_DEV_MCP_P6_PORT:-8713}"
forms_mcp_port="${APEX_DEV_MCP_FORMS_PORT:-8714}"

wait_apex_endpoint() {
  local name="$1"
  local url="$2"
  local attempt

  for attempt in $(seq 1 30); do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      return 0
    fi

    sleep 0.5
  done

  printf '%s\n' "Timed out waiting for ${name} at ${url}" >&2
  return 1
}

cleanup() {
  for pid in "${pids[@]:-}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done
}

trap cleanup EXIT

pids=()
mkdir -p "${repo_root}/.tmp/forms-engine/templates" "${repo_root}/.tmp/forms-engine/artifacts" "${repo_root}/.tmp/p6-ingest/artifacts"

(
  cd "${repo_root}"
  export PYTHONPATH='packages/forms-engine/src'
  export FORMS_ENGINE_TEMPLATES_PATH="${repo_root}/.tmp/forms-engine/templates"
  export FORMS_ENGINE_ARTIFACTS_PATH="${repo_root}/.tmp/forms-engine/artifacts"
  export OIDC_ISSUER_URL="${APEX_DEV_OIDC_ISSUER_URL}"
  export OIDC_CLIENT_ID="${APEX_DEV_FORMS_ENGINE_OIDC_CLIENT_ID}"
  "${repo_python}" -m apex_forms_engine.runtime
) &
pids+=("$!")

(
  cd "${repo_root}"
  export PYTHONPATH='packages/p6-ingest/src'
  export P6_INGEST_ARTIFACTS_PATH="${repo_root}/.tmp/p6-ingest/artifacts"
  export APEX_P6_FIXTURE_PATH="${repo_root}/apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.xer"
  export OIDC_ISSUER_URL="${APEX_DEV_OIDC_ISSUER_URL}"
  export OIDC_CLIENT_ID="${APEX_DEV_P6_INGEST_OIDC_CLIENT_ID}"
  "${repo_python}" -m apex_p6_ingest.runtime
) &
pids+=("$!")

(
  cd "${repo_root}"
  export APEX_MCP_HTTP_PORT="${APEX_DEV_MCP_FS_PORT}"
  export APEX_MCP_WORKSPACE_ROOT="${repo_root}"
  export APEX_MCP_DATA_ROOT="${repo_root}/.apex-data"
  node services/mcp/apex-fs/build/http.js
) &
pids+=("$!")

(
  cd "${repo_root}"
  export APEX_MCP_HTTP_PORT="${APEX_DEV_MCP_DB_PORT}"
  node services/mcp/apex-db/build/http.js
) &
pids+=("$!")

(
  cd "${repo_root}"
  export APEX_MCP_HTTP_PORT="${APEX_DEV_MCP_JOBS_PORT}"
  export APEX_JOBS_LEDGER_PATH="${repo_root}/.apex-data/apex-jobs-ledger.json"
  node services/mcp/apex-jobs/build/http.js
) &
pids+=("$!")

(
  cd "${repo_root}"
  export APEX_MCP_HTTP_PORT="${APEX_DEV_MCP_FORMS_PORT}"
  export APEX_FORMS_RUNTIME_URL="http://127.0.0.1:${APEX_DEV_FORMS_ENGINE_PORT}"
  node services/mcp/apex-forms/build/http.js
) &
pids+=("$!")

(
  cd "${repo_root}"
  export APEX_MCP_HTTP_PORT="${APEX_DEV_MCP_P6_PORT}"
  export APEX_P6_RUNTIME_URL="http://127.0.0.1:${APEX_DEV_P6_INGEST_PORT}"
  node services/mcp/apex-p6/build/http.js
) &
pids+=("$!")

wait_apex_endpoint "forms runtime" "http://127.0.0.1:${forms_runtime_port}/health"
wait_apex_endpoint "p6 runtime" "http://127.0.0.1:${p6_runtime_port}/health"
wait_apex_endpoint "apex-fs MCP transport" "http://127.0.0.1:${fs_mcp_port}/mcp"
wait_apex_endpoint "apex-db MCP transport" "http://127.0.0.1:${db_mcp_port}/mcp"
wait_apex_endpoint "apex-jobs MCP transport" "http://127.0.0.1:${jobs_mcp_port}/mcp"
wait_apex_endpoint "apex-p6 MCP transport" "http://127.0.0.1:${p6_mcp_port}/mcp"
wait_apex_endpoint "apex-forms MCP transport" "http://127.0.0.1:${forms_mcp_port}/mcp"

cd "${repo_root}"
"${repo_python}" tools/canary/run_canary.py