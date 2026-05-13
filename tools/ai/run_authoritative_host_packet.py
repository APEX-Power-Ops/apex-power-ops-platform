from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Callable


TOOL_PATH = "tools/ai/run_authoritative_host_packet.py"
DEFAULT_HOST = "olares-mesh"
DEFAULT_HOST_ROOT = "/home/olares/code/apex/apex-power-ops-platform"
DEFAULT_PROFILE = "strict-db-query"
DEFAULT_DSN_LOADER = "/home/olares/apex-secrets/olares/ai-live-dsn.env"
PACKET_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ARTIFACT_ORDER = (
    "host_bootstrap",
    "verify",
    "promotion",
    "coordinator_summary",
)

CommandRunner = Callable[[list[str], str | None], None]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _normalize_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _format_command(argv: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return shlex.join(argv)


def _validate_packet_id(packet_id: str) -> str:
    normalized = packet_id.strip()
    if not PACKET_ID_PATTERN.fullmatch(normalized):
        raise ValueError(
            f"Invalid packet id '{packet_id}'. Packet ids must match ^[A-Za-z0-9][A-Za-z0-9._-]*$."
        )
    return normalized


def plan_remote_artifact_paths(packet_id: str, host_root: str) -> dict[str, str]:
    normalized_packet_id = _validate_packet_id(packet_id)
    remote_root = PurePosixPath(host_root)
    remote_mcp_dir = remote_root / "tests" / "canary" / "mcp-contract" / "actual"
    remote_bootstrap_dir = remote_root / "tests" / "canary" / "host-bootstrap-status" / "actual"
    return {
        "host_bootstrap": str(remote_bootstrap_dir / f"host-bootstrap-status-{normalized_packet_id}.json"),
        "verify": str(remote_mcp_dir / f"verify-minimal-mcp-trio-{normalized_packet_id}.json"),
        "promotion": str(remote_mcp_dir / f"apex-jobs-promotion-{normalized_packet_id}.json"),
        "coordinator_summary": str(remote_mcp_dir / f"ai-packet-evidence-summary-{normalized_packet_id}.json"),
    }


def plan_local_artifact_paths(packet_id: str, local_root: Path) -> dict[str, Path]:
    normalized_packet_id = _validate_packet_id(packet_id)
    local_mcp_dir = local_root / "tests" / "canary" / "mcp-contract" / "actual"
    local_bootstrap_dir = local_root / "tests" / "canary" / "host-bootstrap-status" / "actual"
    return {
        "host_bootstrap": local_bootstrap_dir / f"host-bootstrap-status-{normalized_packet_id}.json",
        "verify": local_mcp_dir / f"verify-minimal-mcp-trio-{normalized_packet_id}.json",
        "promotion": local_mcp_dir / f"apex-jobs-promotion-{normalized_packet_id}.json",
        "coordinator_summary": local_mcp_dir / f"ai-packet-evidence-summary-{normalized_packet_id}.json",
    }


def plan_artifact_paths(packet_id: str, host_root: str, local_root: Path) -> dict[str, dict[str, str | Path]]:
    remote_paths = plan_remote_artifact_paths(packet_id, host_root)
    local_paths = plan_local_artifact_paths(packet_id, local_root)
    return {
        name: {"remote": remote_paths[name], "local": local_paths[name]}
        for name in ARTIFACT_ORDER
    }


def build_remote_script(packet_id: str, host_root: str, profile: str, dsn_loader: str) -> str:
    normalized_packet_id = _validate_packet_id(packet_id)
    remote_paths = plan_remote_artifact_paths(normalized_packet_id, host_root)
    quoted_host_root = shlex.quote(host_root)
    quoted_packet_id = shlex.quote(normalized_packet_id)
    quoted_profile = shlex.quote(profile)
    quoted_dsn_loader = shlex.quote(dsn_loader)
    quoted_verify = shlex.quote(remote_paths["verify"])
    quoted_promotion = shlex.quote(remote_paths["promotion"])
    quoted_summary = shlex.quote(remote_paths["coordinator_summary"])

    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            f"cd {quoted_host_root}",
            "source tools/shell/common.sh",
            'repo_root="$(get_apex_repo_root)"',
            'repo_python="$(get_apex_preferred_python)"',
            'cd "${repo_root}"',
            f"bash tools/ai/run-minimal-mcp-trio.sh down {quoted_packet_id} >/dev/null || true",
            f"bash tools/ai/run-olares-host-bootstrap-status.sh {quoted_packet_id}",
            "set -a",
            f"source {quoted_dsn_loader}",
            "set +a",
            f"bash tools/ai/run-minimal-mcp-trio.sh up {quoted_packet_id}",
            f"bash tools/ai/run-minimal-mcp-trio.sh verify {quoted_packet_id} {quoted_profile}",
            (
                f'"${{repo_python}}" tools/ai/capture_apex_jobs_promotion.py '
                f"--packet-id {quoted_packet_id} --output {quoted_promotion}"
            ),
            (
                f'"${{repo_python}}" tools/ai/build_ai_packet_evidence_summary.py '
                f"--packet-id {quoted_packet_id} --verify-artifact {quoted_verify} "
                f"--promotion-artifact {quoted_promotion} --output {quoted_summary}"
            ),
            f"bash tools/ai/run-minimal-mcp-trio.sh down {quoted_packet_id}",
            f'final_status="$(bash tools/ai/run-minimal-mcp-trio.sh status {quoted_packet_id})"',
            'FINAL_STATUS_JSON="${final_status}" "${repo_python}" - <<\'PY\'',
            "import json",
            "import os",
            "",
            'payload = json.loads(os.environ["FINAL_STATUS_JSON"])',
            'if payload.get("status") != "not-running":',
            '    raise SystemExit(f"expected final minimal-mcp status not-running, got {payload.get(\"status\")}")',
            "print(json.dumps(payload))",
            "PY",
            "",
        ]
    )


def build_ssh_command(host: str) -> list[str]:
    return ["ssh", host, "bash", "-s"]


def build_scp_command(host: str, remote_path: str, local_path: Path) -> list[str]:
    return ["scp", f"{host}:{remote_path}", str(local_path)]


def _run_subprocess(command: list[str], input_text: str | None = None) -> None:
    if input_text is None:
        subprocess.run(command, check=True, text=True)
        return

    subprocess.run(command, input=input_text.encode("utf-8"), check=True)


def orchestrate_packet(
    *,
    packet_id: str,
    host: str,
    host_root: str,
    profile: str,
    dsn_loader: str,
    local_root: Path,
    runner: CommandRunner = _run_subprocess,
) -> dict[str, object]:
    normalized_packet_id = _validate_packet_id(packet_id)
    artifacts = plan_artifact_paths(normalized_packet_id, host_root, local_root)
    remote_script = build_remote_script(normalized_packet_id, host_root, profile, dsn_loader)

    runner(build_ssh_command(host), remote_script)

    for name in ARTIFACT_ORDER:
        local_path = Path(artifacts[name]["local"])
        local_path.parent.mkdir(parents=True, exist_ok=True)
        runner(build_scp_command(host, str(artifacts[name]["remote"]), local_path), None)

    return {
        "packet_id": normalized_packet_id,
        "tool": TOOL_PATH,
        "command": _format_command([sys.executable, *sys.argv]),
        "host": host,
        "host_root": host_root,
        "profile": profile,
        "artifact_paths": {
            name: _normalize_path(Path(artifacts[name]["local"]))
            for name in ARTIFACT_ORDER
        },
        "result": "PASS",
    }


def _write_output(path: Path | None, payload: dict[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _emit_summary(path: Path | None, payload: dict[str, object], exit_code: int) -> int:
    try:
        _write_output(path, payload)
    except Exception as error:  # noqa: BLE001
        payload = dict(payload)
        payload["result"] = "FAIL"
        payload["error"] = str(error)
        exit_code = 1

    print(json.dumps(payload, indent=2))
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the authoritative-host AI packet chain through stdin-fed ssh and import the packet artifacts locally."
    )
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--host-root", default=DEFAULT_HOST_ROOT)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--dsn-loader", default=DEFAULT_DSN_LOADER)
    parser.add_argument("--output")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else None
    local_root = _repo_root()

    base_summary: dict[str, object] = {
        "packet_id": args.packet_id,
        "tool": TOOL_PATH,
        "host": args.host,
        "host_root": args.host_root,
        "profile": args.profile,
    }

    try:
        summary = orchestrate_packet(
            packet_id=args.packet_id,
            host=args.host,
            host_root=args.host_root,
            profile=args.profile,
            dsn_loader=args.dsn_loader,
            local_root=local_root,
        )
        if output_path is not None:
            summary["output_path"] = _normalize_path(output_path)
        return _emit_summary(output_path, summary, 0)
    except Exception as error:  # noqa: BLE001
        failure = dict(base_summary)
        failure["result"] = "FAIL"
        failure["error"] = str(error)
        return _emit_summary(output_path, failure, 1)


if __name__ == "__main__":
    raise SystemExit(main())