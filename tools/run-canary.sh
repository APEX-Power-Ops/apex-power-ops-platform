#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/shell/common.sh"

repo_root="$(get_apex_repo_root)"
import_apex_env_file
repo_python="$(get_apex_preferred_python)"

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

sleep 3

cd "${repo_root}"
"${repo_python}" tools/canary/run_canary.py