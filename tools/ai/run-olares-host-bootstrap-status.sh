#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../shell/common.sh"

repo_root="$(get_apex_repo_root)"
import_apex_env_file
repo_python="$(get_apex_preferred_python)"

packet_id="${1:-}"
if [[ -z "${packet_id}" ]]; then
    packet_id="$(get_apex_default_packet_id host-bootstrap-status)"
fi
dsn_env="${2:-}"
host_container_root="$(cd "${repo_root}/.." && pwd)"
old_clone="/home/olares/src/apex-power-ops-platform"
pnpm_bin="/home/olares/apex-data/toolchains/pnpm-10.0.0/node_modules/.bin/pnpm"
calc_python="/home/olares/apex-data/toolchains/calc-engine-venv/bin/python"
state_dir="${repo_root}/.tmp/ai-workflow"
minimal_status_file="${state_dir}/host-bootstrap-minimal-status.json"
minimal_ownership_file="${state_dir}/host-bootstrap-minimal-ownership.json"
hold_status_file="${state_dir}/host-bootstrap-hold-status.json"
host_bootstrap_actual_dir="${repo_root}/tests/canary/host-bootstrap-status/actual"
host_bootstrap_output="${host_bootstrap_actual_dir}/host-bootstrap-status-${packet_id}.json"

mkdir -p "${state_dir}"
mkdir -p "${host_bootstrap_actual_dir}"

git_status_count() {
  local target="$1"
  git -C "${target}" status --porcelain | grep -c . || true
}

command_path_or_empty() {
  local command_name="$1"
  command -v "${command_name}" 2>/dev/null || true
}

bash "${repo_root}/tools/ai/run-minimal-mcp-trio.sh" status >"${minimal_status_file}"

minimal_mode="$({
    "${repo_python}" - <<'PY' "${minimal_status_file}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload.get("status") or "not-running")
PY
})"

rm -f "${minimal_ownership_file}"

if [[ "${minimal_mode}" == "unmanaged-running" ]]; then
    fs_endpoint="$({
        "${repo_python}" - <<'PY' "${minimal_status_file}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload.get("fs_endpoint") or "")
PY
    })"

    if [[ -n "${fs_endpoint}" ]]; then
        "${repo_python}" tools/ai/check_apex_fs_ownership.py \
            --fs-url "${fs_endpoint}" \
            --expected-workspace-root "${repo_root}" \
            --expected-readme-path "${repo_root}/README.md" >"${minimal_ownership_file}" || true

        "${repo_python}" - <<'PY' "${minimal_status_file}" "${minimal_ownership_file}"
import json
import sys
from pathlib import Path

minimal_path = Path(sys.argv[1])
ownership_path = Path(sys.argv[2])

minimal = json.loads(minimal_path.read_text(encoding="utf-8"))

if ownership_path.exists() and ownership_path.read_text(encoding="utf-8").strip():
    minimal["ownership_probe"] = json.loads(ownership_path.read_text(encoding="utf-8"))

minimal_path.write_text(json.dumps(minimal, indent=2) + "\n", encoding="utf-8")
PY
    fi
fi

minimal_ready="$({
    "${repo_python}" - <<'PY' "${minimal_status_file}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
status = payload.get("status")
mode = payload.get("mode")

ready_statuses = {"managed-running", "adopted-running"}
print("true" if status in ready_statuses or (status is None and mode in {"managed", "adopted"}) else "false")
PY
})"

if [[ "${minimal_ready}" == "true" ]]; then
  bash "${repo_root}/tools/ai/run-olares-hold-boundary-check.sh" "${packet_id}" "${dsn_env}" >"${hold_status_file}"
else
    hold_minimal_mcp="NOT_RUNNING"
    hold_decision="minimal_mcp_not_running"
    hold_minimal_mcp_detail="$({
        "${repo_python}" - <<'PY' "${minimal_status_file}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(json.dumps(payload, separators=(",", ":")))
PY
    })"

    if [[ "${minimal_mode}" == "unmanaged-running" ]]; then
        hold_minimal_mcp="UNMANAGED_RUNNING"
        hold_decision="minimal_mcp_unmanaged"
    fi

    cat >"${hold_status_file}" <<EOF
{
  "packet_id": "status-only",
    "minimal_mcp": "${hold_minimal_mcp}",
    "minimal_mcp_detail": ${hold_minimal_mcp_detail},
  "deferred_ops": "UNAVAILABLE",
    "deferred_ops_decision": "${hold_decision}",
  "outputs": {}
}
EOF
fi

"${repo_python}" - <<'PY' "${packet_id}" "${host_container_root}" "${repo_root}" "${old_clone}" "${pnpm_bin}" "${calc_python}" "${repo_python}" "${minimal_status_file}" "${hold_status_file}" "${host_bootstrap_output}"
import json
import shutil
import subprocess
import sys
from pathlib import Path

packet_id, host_container_root, repo_root, old_clone, pnpm_bin, calc_python, preferred_python, minimal_path, hold_path, output_path = sys.argv[1:]


def run_text(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def git_status_count(target: str) -> int:
    if not Path(target).exists():
        return 0
    output = subprocess.check_output(["git", "-C", target, "status", "--porcelain"], text=True)
    return 0 if not output else len(output.rstrip("\n").splitlines())


def git_head_or_none(target: str) -> str | None:
    if not Path(target).exists():
        return None
    try:
        return run_text("git", "-C", target, "rev-parse", "HEAD")
    except Exception:
        return None


def maybe_version(command: str) -> str | None:
    path = shutil.which(command)
    if not path:
        return None
    try:
        return subprocess.check_output([path, "--version"], text=True).splitlines()[0].strip()
    except Exception:
        return path


def file_version(path: str, args: list[str]) -> str | None:
    if not Path(path).exists():
        return None
    try:
        return subprocess.check_output([path, *args], text=True).splitlines()[0].strip()
    except Exception:
        return path


minimal = json.loads(Path(minimal_path).read_text(encoding="utf-8"))
hold = json.loads(Path(hold_path).read_text(encoding="utf-8"))

payload = {
    "packet_id": packet_id,
    "host_container_root": host_container_root,
    "implementation_root": repo_root,
    "git": {
        "head": run_text("git", "-C", repo_root, "rev-parse", "HEAD"),
        "status_count": git_status_count(repo_root),
        "old_clone": {
            "path": old_clone,
            "exists": Path(old_clone).exists(),
            "head": git_head_or_none(old_clone),
            "status_count": git_status_count(old_clone),
        },
    },
    "toolchains": {
        "preferred_python": {
            "path": preferred_python if Path(preferred_python).exists() else None,
            "version": file_version(preferred_python, ["--version"]),
        },
        "python3": {
            "path": shutil.which("python3"),
            "version": maybe_version("python3"),
        },
        "node": {
            "path": shutil.which("node"),
            "version": maybe_version("node"),
        },
        "pnpm_materialized": {
            "path": pnpm_bin if Path(pnpm_bin).exists() else None,
            "version": file_version(pnpm_bin, ["--version"]),
        },
        "calc_engine_python": {
            "path": calc_python if Path(calc_python).exists() else None,
            "version": file_version(calc_python, ["--version"]),
        },
    },
    "minimal_mcp": minimal,
    "hold_boundary": hold,
    "output_artifact": output_path,
}

output = Path(output_path)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
PY