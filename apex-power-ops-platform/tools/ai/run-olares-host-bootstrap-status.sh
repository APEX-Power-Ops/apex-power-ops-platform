#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../shell/common.sh"

repo_root="$(get_apex_repo_root)"
import_apex_env_file

packet_id="${1:-2026-05-06-olares-dev-residency-063}"
dsn_env="${2:-}"
host_root="$(cd "${repo_root}/.." && pwd)"
old_clone="/home/olares/src/apex-power-ops-platform"
pnpm_bin="/home/olares/apex-data/toolchains/pnpm-10.0.0/node_modules/.bin/pnpm"
calc_python="/home/olares/apex-data/toolchains/calc-engine-venv/bin/python"
state_dir="${repo_root}/.tmp/ai-workflow"
minimal_status_file="${state_dir}/host-bootstrap-minimal-status.json"
hold_status_file="${state_dir}/host-bootstrap-hold-status.json"

mkdir -p "${state_dir}"

git_status_count() {
  local target="$1"
  git -C "${target}" status --porcelain | grep -c . || true
}

command_path_or_empty() {
  local command_name="$1"
  command -v "${command_name}" 2>/dev/null || true
}

bash "${repo_root}/tools/ai/run-minimal-mcp-trio.sh" status >"${minimal_status_file}"

minimal_ready="$({
  python3 - <<'PY' "${minimal_status_file}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
status = payload.get("status")
print("true" if status != "not-running" else "false")
PY
})"

if [[ "${minimal_ready}" == "true" ]]; then
  bash "${repo_root}/tools/ai/run-olares-hold-boundary-check.sh" "${packet_id}" "${dsn_env}" >"${hold_status_file}"
else
  cat >"${hold_status_file}" <<'EOF'
{
  "packet_id": "status-only",
  "minimal_mcp": "NOT_RUNNING",
  "deferred_ops": "UNAVAILABLE",
  "deferred_ops_decision": "minimal_mcp_not_running",
  "outputs": {}
}
EOF
fi

python3 - <<'PY' "${packet_id}" "${host_root}" "${repo_root}" "${old_clone}" "${pnpm_bin}" "${calc_python}" "${minimal_status_file}" "${hold_status_file}"
import json
import shutil
import subprocess
import sys
from pathlib import Path

packet_id, host_root, repo_root, old_clone, pnpm_bin, calc_python, minimal_path, hold_path = sys.argv[1:]


def run_text(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def git_status_count(target: str) -> int:
    output = subprocess.check_output(["git", "-C", target, "status", "--porcelain"], text=True)
    return 0 if not output else len(output.rstrip("\n").splitlines())


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
    "host_root": host_root,
    "implementation_root": repo_root,
    "git": {
        "head": run_text("git", "-C", host_root, "rev-parse", "HEAD"),
        "status_count": git_status_count(host_root),
        "old_clone": {
            "path": old_clone,
            "head": run_text("git", "-C", old_clone, "rev-parse", "HEAD"),
            "status_count": git_status_count(old_clone),
        },
    },
    "toolchains": {
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
}

print(json.dumps(payload, indent=2))
PY