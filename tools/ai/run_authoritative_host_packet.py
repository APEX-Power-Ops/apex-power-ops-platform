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
HOST_BOOTSTRAP_TOOL_PATH = "tools/ai/run-olares-host-bootstrap-status.sh"
VERIFY_TOOL_PATH = "tools/ai/verify_minimal_mcp_trio.py"
PROMOTION_TOOL_PATH = "tools/ai/capture_apex_jobs_promotion.py"
COORDINATOR_SUMMARY_TOOL_PATH = "tools/ai/build_ai_packet_evidence_summary.py"
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


def _git_head(repo_root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
    ).strip()


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
    quoted_bootstrap = shlex.quote(remote_paths["host_bootstrap"])
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
            (
                f"bash tools/ai/run-olares-host-bootstrap-status.sh "
                f"--packet-id {quoted_packet_id} --output {quoted_bootstrap}"
            ),
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


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_name(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return PurePosixPath(value).name


def _parse_command(command: object, artifact_label: str) -> list[str]:
    if not isinstance(command, str) or not command.strip():
        raise ValueError(f"{artifact_label} missing command")

    try:
        argv = shlex.split(command)
    except ValueError as error:
        raise ValueError(f"{artifact_label} command is not parseable: {error}") from error

    if len(argv) < 2:
        raise ValueError(f"{artifact_label} command missing tool invocation")

    return argv


def _command_flag_value(argv: list[str], flag: str, artifact_label: str) -> str:
    try:
        index = argv.index(flag)
    except ValueError as error:
        raise ValueError(f"{artifact_label} command missing {flag}") from error

    if index + 1 >= len(argv):
        raise ValueError(f"{artifact_label} command missing value for {flag}")

    return argv[index + 1]


def _validate_command_surface(
    *,
    artifact_label: str,
    command: object,
    expected_tool_path: str,
    expected_packet_id: str,
    expected_output_name: str,
    expected_input_names: dict[str, str] | None = None,
) -> list[str]:
    argv = _parse_command(command, artifact_label)
    actual_tool_path = argv[1]
    if actual_tool_path != expected_tool_path:
        raise ValueError(
            f"{artifact_label} command tool mismatch: expected {expected_tool_path}, got {actual_tool_path}"
        )

    actual_packet_id = _command_flag_value(argv, "--packet-id", artifact_label)
    if actual_packet_id != expected_packet_id:
        raise ValueError(
            f"{artifact_label} command packet_id mismatch: expected {expected_packet_id}, got {actual_packet_id}"
        )

    actual_output_name = _path_name(_command_flag_value(argv, "--output", artifact_label))
    if actual_output_name != expected_output_name:
        raise ValueError(
            f"{artifact_label} command output mismatch: expected {expected_output_name}, got {actual_output_name}"
        )

    for flag, expected_name in (expected_input_names or {}).items():
        actual_name = _path_name(_command_flag_value(argv, flag, artifact_label))
        if actual_name != expected_name:
            raise ValueError(
                f"{artifact_label} command {flag} mismatch: expected {expected_name}, got {actual_name}"
            )

    return argv


def _validate_host_bootstrap_artifact(
    *,
    packet_id: str,
    artifact_path: Path,
    expected_old_clone_path: str,
    expected_host_container_root: str,
    expected_host_root: str,
    expected_head: str,
) -> dict[str, object]:
    payload = _read_json(artifact_path)

    payload_output_artifact = payload.get("output_artifact")
    if _path_name(payload_output_artifact) != artifact_path.name:
        raise ValueError(
            "host bootstrap artifact output path mismatch: "
            f"expected {artifact_path.name}, got {_path_name(payload_output_artifact)}"
        )

    if payload.get("tool") != HOST_BOOTSTRAP_TOOL_PATH:
        raise ValueError(
            f"host bootstrap artifact tool mismatch: expected {HOST_BOOTSTRAP_TOOL_PATH}, got {payload.get('tool')}"
        )

    _validate_command_surface(
        artifact_label="host bootstrap artifact",
        command=payload.get("command"),
        expected_tool_path=HOST_BOOTSTRAP_TOOL_PATH,
        expected_packet_id=packet_id,
        expected_output_name=artifact_path.name,
    )

    if payload.get("packet_id") != packet_id:
        raise ValueError(
            f"host bootstrap artifact packet_id mismatch: expected {packet_id}, got {payload.get('packet_id')}"
        )

    host_container_root = payload.get("host_container_root")
    if host_container_root != expected_host_container_root:
        raise ValueError(
            "host bootstrap artifact host_container_root mismatch: "
            f"expected {expected_host_container_root}, got {host_container_root}"
        )

    implementation_root = payload.get("implementation_root")
    if implementation_root != expected_host_root:
        raise ValueError(
            f"host bootstrap artifact implementation_root mismatch: expected {expected_host_root}, got {implementation_root}"
        )

    git_payload = payload.get("git")
    if not isinstance(git_payload, dict):
        raise ValueError("host bootstrap artifact missing git payload")

    old_clone_payload = git_payload.get("old_clone")
    if not isinstance(old_clone_payload, dict):
        raise ValueError("host bootstrap artifact missing git.old_clone payload")

    old_clone_path = old_clone_payload.get("path")
    if old_clone_path != expected_old_clone_path:
        raise ValueError(
            f"host bootstrap artifact old_clone path mismatch: expected {expected_old_clone_path}, got {old_clone_path}"
        )

    status_count = git_payload.get("status_count")
    if status_count != 0:
        raise ValueError(f"host bootstrap artifact shows dirty host worktree: status_count={status_count}")

    host_head = git_payload.get("head")
    if host_head != expected_head:
        raise ValueError(
            f"host bootstrap artifact head mismatch: expected {expected_head}, got {host_head}"
        )

    minimal_mcp = payload.get("minimal_mcp")
    if not isinstance(minimal_mcp, dict):
        raise ValueError("host bootstrap artifact missing minimal_mcp payload")

    preflight_status = minimal_mcp.get("status")
    if preflight_status != "not-running":
        raise ValueError(
            f"host bootstrap artifact preflight status must be not-running, got {preflight_status}"
        )

    return {
        "host_git_head": host_head,
        "host_status_count": status_count,
        "preflight_status": preflight_status,
    }


def _validate_verify_artifact(*, packet_id: str, artifact_path: Path, expected_profile: str) -> dict[str, object]:
    payload = _read_json(artifact_path)

    if payload.get("packet_id") != packet_id:
        raise ValueError(
            f"verify artifact packet_id mismatch: expected {packet_id}, got {payload.get('packet_id')}"
        )

    if payload.get("result") != "PASS":
        raise ValueError(f"verify artifact result must be PASS, got {payload.get('result')}")

    profile = payload.get("profile")
    if profile != expected_profile:
        raise ValueError(f"verify artifact profile mismatch: expected {expected_profile}, got {profile}")

    argv = _validate_command_surface(
        artifact_label="verify artifact",
        command=payload.get("command"),
        expected_tool_path=VERIFY_TOOL_PATH,
        expected_packet_id=packet_id,
        expected_output_name=artifact_path.name,
    )

    command_profile = _command_flag_value(argv, "--profile", "verify artifact")
    if command_profile != expected_profile:
        raise ValueError(
            f"verify artifact command profile mismatch: expected {expected_profile}, got {command_profile}"
        )

    return {
        "verify_result": payload.get("result"),
        "verify_profile": profile,
        "verify_artifact_name": artifact_path.name,
    }


def _validate_promotion_artifact(*, packet_id: str, artifact_path: Path) -> dict[str, object]:
    payload = _read_json(artifact_path)

    payload_artifact_path = payload.get("artifact_path")
    if _path_name(payload_artifact_path) != artifact_path.name:
        raise ValueError(
            "promotion artifact self path mismatch: "
            f"expected {artifact_path.name}, got {_path_name(payload_artifact_path)}"
        )

    if payload.get("packet_id") != packet_id:
        raise ValueError(
            f"promotion artifact packet_id mismatch: expected {packet_id}, got {payload.get('packet_id')}"
        )

    if payload.get("tool") != PROMOTION_TOOL_PATH:
        raise ValueError(
            f"promotion artifact tool mismatch: expected {PROMOTION_TOOL_PATH}, got {payload.get('tool')}"
        )

    _validate_command_surface(
        artifact_label="promotion artifact",
        command=payload.get("command"),
        expected_tool_path=PROMOTION_TOOL_PATH,
        expected_packet_id=packet_id,
        expected_output_name=artifact_path.name,
    )

    if payload.get("result") != "PASS":
        raise ValueError(f"promotion artifact result must be PASS, got {payload.get('result')}")

    host_run = payload.get("host_run")
    if not isinstance(host_run, dict):
        raise ValueError("promotion artifact missing host_run payload")

    if host_run.get("packet_id") != packet_id:
        raise ValueError(
            f"promotion artifact host_run packet_id mismatch: expected {packet_id}, got {host_run.get('packet_id')}"
        )

    if host_run.get("status") != "success":
        raise ValueError(f"promotion artifact host_run status must be success, got {host_run.get('status')}")

    host_run_env = host_run.get("env")
    if host_run_env != "host":
        raise ValueError(f"promotion artifact host_run env must be host, got {host_run_env}")

    host_service = host_run.get("service")
    if not isinstance(host_service, str) or not host_service:
        raise ValueError("promotion artifact host_run missing service")

    if payload.get("env") != host_run_env:
        raise ValueError(
            f"promotion artifact env mismatch: expected {host_run_env}, got {payload.get('env')}"
        )

    if payload.get("service") != host_service:
        raise ValueError(
            f"promotion artifact service mismatch: expected {host_service}, got {payload.get('service')}"
        )

    promotion = payload.get("promotion")
    if not isinstance(promotion, dict):
        raise ValueError("promotion artifact missing promotion payload")

    if promotion.get("packet_id") != packet_id:
        raise ValueError(
            f"promotion record packet_id mismatch: expected {packet_id}, got {promotion.get('packet_id')}"
        )

    promotion_promoted_at = promotion.get("promoted_at")
    if not isinstance(promotion_promoted_at, str) or not promotion_promoted_at:
        raise ValueError("promotion record missing promoted_at")

    host_success_runs = payload.get("host_success_runs")
    if not isinstance(host_success_runs, list) or not host_success_runs:
        raise ValueError("promotion artifact missing host_success_runs payload")

    incompatible_host_success_run_ids = [
        run.get("run_id")
        for run in host_success_runs
        if isinstance(run, dict)
        and run.get("packet_id") == packet_id
        and run.get("status") == "success"
        and (run.get("env") != host_run_env or run.get("service") != host_service)
    ]
    if incompatible_host_success_run_ids:
        raise ValueError(
            "promotion artifact host_success_runs contain runs outside accepted host env/service: "
            f"{incompatible_host_success_run_ids}"
        )

    host_run_id = host_run.get("run_id")
    host_success_run_ids = [
        run.get("run_id")
        for run in host_success_runs
        if isinstance(run, dict)
        and run.get("packet_id") == packet_id
        and run.get("status") == "success"
        and run.get("env") == host_run_env
        and run.get("service") == host_service
    ]
    if host_run_id not in host_success_run_ids:
        raise ValueError(
            f"promotion artifact host_success_runs missing accepted host_run id {host_run_id}"
        )

    supporting_run_ids = promotion.get("supporting_run_ids")
    if not isinstance(supporting_run_ids, list) or host_run_id not in supporting_run_ids:
        raise ValueError(
            f"promotion artifact supporting_run_ids missing accepted host_run id {host_run_id}"
        )

    unsupported_supporting_run_ids = [run_id for run_id in supporting_run_ids if run_id not in host_success_run_ids]
    if unsupported_supporting_run_ids:
        raise ValueError(
            "promotion artifact supporting_run_ids are not backed by host_success_runs: "
            f"{unsupported_supporting_run_ids}"
        )

    return {
        "promotion_result": payload.get("result"),
        "host_run_id": host_run_id,
        "host_run_env": host_run_env,
        "host_service": host_service,
        "promotion_promoted_at": promotion_promoted_at,
        "promotion_artifact_name": artifact_path.name,
        "host_success_run_ids": host_success_run_ids,
        "promotion_supporting_run_ids": supporting_run_ids,
    }


def _validate_coordinator_summary_artifact(
    *,
    packet_id: str,
    artifact_path: Path,
    verify_artifact_name: str,
    verify_profile: str,
    promotion_artifact_name: str,
    host_run_id: str | None,
    host_run_env: str | None,
    host_service: str | None,
    promotion_promoted_at: str | None,
    host_success_run_ids: list[str] | None,
    supporting_run_ids: list[str] | None,
) -> dict[str, object]:
    payload = _read_json(artifact_path)

    payload_artifact_path = payload.get("artifact_path")
    if _path_name(payload_artifact_path) != artifact_path.name:
        raise ValueError(
            "coordinator summary artifact self path mismatch: "
            f"expected {artifact_path.name}, got {_path_name(payload_artifact_path)}"
        )

    if payload.get("packet_id") != packet_id:
        raise ValueError(
            f"coordinator summary artifact packet_id mismatch: expected {packet_id}, got {payload.get('packet_id')}"
        )

    if payload.get("tool") != COORDINATOR_SUMMARY_TOOL_PATH:
        raise ValueError(
            "coordinator summary artifact tool mismatch: "
            f"expected {COORDINATOR_SUMMARY_TOOL_PATH}, got {payload.get('tool')}"
        )

    _validate_command_surface(
        artifact_label="coordinator summary artifact",
        command=payload.get("command"),
        expected_tool_path=COORDINATOR_SUMMARY_TOOL_PATH,
        expected_packet_id=packet_id,
        expected_output_name=artifact_path.name,
        expected_input_names={
            "--verify-artifact": verify_artifact_name,
            "--promotion-artifact": promotion_artifact_name,
        },
    )

    if payload.get("result") != "PASS":
        raise ValueError(
            f"coordinator summary artifact result must be PASS, got {payload.get('result')}"
        )

    verification = payload.get("verification")
    if not isinstance(verification, dict):
        raise ValueError("coordinator summary artifact missing verification payload")

    if verification.get("result") != "PASS":
        raise ValueError(
            f"coordinator summary verification result must be PASS, got {verification.get('result')}"
        )

    if verification.get("profile") != verify_profile:
        raise ValueError(
            f"coordinator summary verification profile mismatch: expected {verify_profile}, got {verification.get('profile')}"
        )

    verify_artifact_path = payload.get("verify_artifact_path")
    if _path_name(verify_artifact_path) != verify_artifact_name:
        raise ValueError(
            "coordinator summary verify artifact path mismatch: "
            f"expected {verify_artifact_name}, got {_path_name(verify_artifact_path)}"
        )

    promotion = payload.get("promotion")
    if not isinstance(promotion, dict):
        raise ValueError("coordinator summary artifact missing promotion payload")

    if promotion.get("result") != "PASS":
        raise ValueError(
            f"coordinator summary promotion result must be PASS, got {promotion.get('result')}"
        )

    if host_run_env is not None and promotion.get("env") != host_run_env:
        raise ValueError(
            f"coordinator summary promotion env mismatch: expected {host_run_env}, got {promotion.get('env')}"
        )

    if host_service is not None and promotion.get("service") != host_service:
        raise ValueError(
            f"coordinator summary promotion service mismatch: expected {host_service}, got {promotion.get('service')}"
        )

    promotion_artifact_path = payload.get("promotion_artifact_path")
    if _path_name(promotion_artifact_path) != promotion_artifact_name:
        raise ValueError(
            "coordinator summary promotion artifact path mismatch: "
            f"expected {promotion_artifact_name}, got {_path_name(promotion_artifact_path)}"
        )

    host_run = promotion.get("host_run")
    if not isinstance(host_run, dict):
        raise ValueError("coordinator summary promotion payload missing host_run")

    if host_run.get("packet_id") != packet_id:
        raise ValueError(
            f"coordinator summary host_run packet_id mismatch: expected {packet_id}, got {host_run.get('packet_id')}"
        )

    if host_run_id is not None and host_run.get("run_id") != host_run_id:
        raise ValueError(
            f"coordinator summary host_run id mismatch: expected {host_run_id}, got {host_run.get('run_id')}"
        )

    if host_run_env is not None and host_run.get("env") != host_run_env:
        raise ValueError(
            f"coordinator summary host_run env mismatch: expected {host_run_env}, got {host_run.get('env')}"
        )

    if host_service is not None and host_run.get("service") != host_service:
        raise ValueError(
            f"coordinator summary host_run service mismatch: expected {host_service}, got {host_run.get('service')}"
        )

    host_success_runs = promotion.get("host_success_runs")
    if not isinstance(host_success_runs, list) or not host_success_runs:
        raise ValueError("coordinator summary promotion payload missing host_success_runs")

    incompatible_host_success_run_ids = [
        run.get("run_id")
        for run in host_success_runs
        if isinstance(run, dict)
        and run.get("packet_id") == packet_id
        and run.get("status") == "success"
        and ((host_run_env is not None and run.get("env") != host_run_env) or (host_service is not None and run.get("service") != host_service))
    ]
    if incompatible_host_success_run_ids:
        raise ValueError(
            "coordinator summary host_success_runs contain runs outside accepted host env/service: "
            f"{incompatible_host_success_run_ids}"
        )

    coordinator_host_success_run_ids = [
        run.get("run_id")
        for run in host_success_runs
        if isinstance(run, dict)
        and run.get("packet_id") == packet_id
        and run.get("status") == "success"
        and (host_run_env is None or run.get("env") == host_run_env)
        and (host_service is None or run.get("service") == host_service)
    ]
    if host_run_id is not None and host_run_id not in coordinator_host_success_run_ids:
        raise ValueError(
            f"coordinator summary host_success_runs missing accepted host_run id {host_run_id}"
        )

    if host_success_run_ids is not None and coordinator_host_success_run_ids != host_success_run_ids:
        raise ValueError(
            "coordinator summary host_success_runs mismatch: "
            f"expected {host_success_run_ids}, got {coordinator_host_success_run_ids}"
        )

    promotion_record = promotion.get("promotion_record")
    if not isinstance(promotion_record, dict):
        raise ValueError("coordinator summary promotion payload missing promotion_record")

    if promotion_record.get("packet_id") != packet_id:
        raise ValueError(
            f"coordinator summary promotion_record packet_id mismatch: expected {packet_id}, got {promotion_record.get('packet_id')}"
        )

    if promotion_promoted_at is not None and promotion_record.get("promoted_at") != promotion_promoted_at:
        raise ValueError(
            "coordinator summary promotion_record promoted_at mismatch: "
            f"expected {promotion_promoted_at}, got {promotion_record.get('promoted_at')}"
        )

    summary_supporting_run_ids = promotion_record.get("supporting_run_ids")
    if not isinstance(summary_supporting_run_ids, list) or (
        host_run_id is not None and host_run_id not in summary_supporting_run_ids
    ):
        raise ValueError(
            f"coordinator summary supporting_run_ids missing accepted host_run id {host_run_id}"
        )

    if supporting_run_ids is not None and summary_supporting_run_ids != supporting_run_ids:
        raise ValueError(
            "coordinator summary supporting_run_ids mismatch: "
            f"expected {supporting_run_ids}, got {summary_supporting_run_ids}"
        )

    return {
        "coordinator_summary_result": payload.get("result"),
        "coordinator_verify_artifact_name": verify_artifact_name,
        "coordinator_promotion_artifact_name": promotion_artifact_name,
        "coordinator_promotion_promoted_at": promotion_record.get("promoted_at"),
        "coordinator_host_success_run_ids": coordinator_host_success_run_ids,
        "coordinator_supporting_run_ids": summary_supporting_run_ids,
    }


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
    expected_head = _git_head(_repo_root())

    runner(build_ssh_command(host), remote_script)

    for name in ARTIFACT_ORDER:
        local_path = Path(artifacts[name]["local"])
        local_path.parent.mkdir(parents=True, exist_ok=True)
        runner(build_scp_command(host, str(artifacts[name]["remote"]), local_path), None)

    bootstrap_validation = _validate_host_bootstrap_artifact(
        packet_id=normalized_packet_id,
        artifact_path=Path(artifacts["host_bootstrap"]["local"]),
        expected_old_clone_path=str(PurePosixPath("/home/olares/src") / PurePosixPath(host_root).name),
        expected_host_container_root=str(PurePosixPath(host_root).parent),
        expected_host_root=host_root,
        expected_head=expected_head,
    )
    verify_validation = _validate_verify_artifact(
        packet_id=normalized_packet_id,
        artifact_path=Path(artifacts["verify"]["local"]),
        expected_profile=profile,
    )
    promotion_validation = _validate_promotion_artifact(
        packet_id=normalized_packet_id,
        artifact_path=Path(artifacts["promotion"]["local"]),
    )
    coordinator_summary_validation = _validate_coordinator_summary_artifact(
        packet_id=normalized_packet_id,
        artifact_path=Path(artifacts["coordinator_summary"]["local"]),
        verify_artifact_name=str(verify_validation["verify_artifact_name"]),
        verify_profile=str(verify_validation["verify_profile"]),
        promotion_artifact_name=str(promotion_validation["promotion_artifact_name"]),
        host_run_id=promotion_validation["host_run_id"] if isinstance(promotion_validation["host_run_id"], str) else None,
        host_run_env=promotion_validation["host_run_env"] if isinstance(promotion_validation["host_run_env"], str) else None,
        host_service=promotion_validation["host_service"] if isinstance(promotion_validation["host_service"], str) else None,
        promotion_promoted_at=promotion_validation["promotion_promoted_at"] if isinstance(promotion_validation["promotion_promoted_at"], str) else None,
        host_success_run_ids=promotion_validation["host_success_run_ids"] if isinstance(promotion_validation["host_success_run_ids"], list) else None,
        supporting_run_ids=promotion_validation["promotion_supporting_run_ids"] if isinstance(promotion_validation["promotion_supporting_run_ids"], list) else None,
    )

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
        **bootstrap_validation,
        **verify_validation,
        **promotion_validation,
        **coordinator_summary_validation,
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