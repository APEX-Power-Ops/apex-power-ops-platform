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


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_name(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return PurePosixPath(value).name


def _validate_host_bootstrap_artifact(
    *,
    packet_id: str,
    artifact_path: Path,
    expected_head: str,
) -> dict[str, object]:
    payload = _read_json(artifact_path)

    if payload.get("packet_id") != packet_id:
        raise ValueError(
            f"host bootstrap artifact packet_id mismatch: expected {packet_id}, got {payload.get('packet_id')}"
        )

    git_payload = payload.get("git")
    if not isinstance(git_payload, dict):
        raise ValueError("host bootstrap artifact missing git payload")

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

    return {
        "verify_result": payload.get("result"),
        "verify_profile": profile,
        "verify_artifact_name": artifact_path.name,
    }


def _validate_promotion_artifact(*, packet_id: str, artifact_path: Path) -> dict[str, object]:
    payload = _read_json(artifact_path)

    if payload.get("packet_id") != packet_id:
        raise ValueError(
            f"promotion artifact packet_id mismatch: expected {packet_id}, got {payload.get('packet_id')}"
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
    host_success_run_ids: list[str] | None,
    supporting_run_ids: list[str] | None,
) -> dict[str, object]:
    payload = _read_json(artifact_path)

    if payload.get("packet_id") != packet_id:
        raise ValueError(
            f"coordinator summary artifact packet_id mismatch: expected {packet_id}, got {payload.get('packet_id')}"
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