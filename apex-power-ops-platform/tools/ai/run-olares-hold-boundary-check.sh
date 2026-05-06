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

mkdir -p "${state_dir}"

bash "${repo_root}/tools/ai/run-minimal-mcp-trio.sh" verify "${packet_id}" >/dev/null

hold_args=(
  "${repo_root}/tools/ai/check_deferred_ops_view_counts.py"
  --packet-id "${packet_id}"
  --output "${hold_output}"
)

if [[ -n "${dsn_env}" ]]; then
  hold_args+=(--dsn-env "${dsn_env}")
fi

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