from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any


def _command_string(argv: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return shlex.join(argv)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _extract_verify_summary(payload: dict[str, Any]) -> dict[str, Any]:
    checks = payload.get("checks", {})
    _require(payload.get("result") == "PASS", "verify artifact must report result=PASS")
    _require(checks.get("jobs_end_run", {}).get("status") == "pass", "verify artifact must include a passing jobs_end_run check")
    _require(checks.get("jobs_list_runs", {}).get("status") == "pass", "verify artifact must include a passing jobs_list_runs check")

    return {
        "profile": payload.get("profile"),
        "result": payload.get("result"),
        "guard_detail": checks.get("jobs_promote_guard", {}).get("detail"),
        "sandbox_run": checks.get("jobs_end_run", {}).get("run"),
        "listed_runs": checks.get("jobs_list_runs", {}).get("result", {}).get("runs", []),
    }


def _extract_promotion_summary(payload: dict[str, Any]) -> dict[str, Any]:
    checks = payload.get("checks", {})
    _require(payload.get("result") == "PASS", "promotion artifact must report result=PASS")

    host_run = payload.get("host_run")
    if host_run is None:
        host_run = checks.get("jobs_end_run", {}).get("run")

    host_success_runs = payload.get("host_success_runs")
    if host_success_runs is None:
        host_success_runs = checks.get("jobs_list_runs", {}).get("result", {}).get("runs", [])

    promotion_record = payload.get("promotion")
    if promotion_record is None:
        promotion_record = checks.get("jobs_promote_packet", {}).get("result")

    _require(host_run is not None, "promotion artifact must include a completed host run record")
    _require(bool(host_success_runs), "promotion artifact must include at least one host success run")
    _require(promotion_record is not None, "promotion artifact must include a promotion record")

    return {
        "env": payload.get("env"),
        "service": payload.get("service"),
        "result": payload.get("result"),
        "host_run": host_run,
        "host_success_runs": host_success_runs,
        "promotion_record": promotion_record,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose one packet-scoped AI evidence summary from verifier and promotion artifacts.")
    parser.add_argument("--packet-id")
    parser.add_argument("--verify-artifact", required=True)
    parser.add_argument("--promotion-artifact")
    parser.add_argument("--output")
    args = parser.parse_args()

    verify_path = Path(args.verify_artifact)
    promotion_path = Path(args.promotion_artifact) if args.promotion_artifact else None
    output_path = Path(args.output) if args.output else None

    verify_payload = _read_json(verify_path)
    promotion_payload = _read_json(promotion_path) if promotion_path is not None else None

    packet_id = args.packet_id or verify_payload.get("packet_id")
    _require(bool(packet_id), "packet_id must be provided directly or present in the verify artifact")
    _require(verify_payload.get("packet_id") == packet_id, "verify artifact packet_id does not match the requested packet_id")

    if promotion_payload is not None:
        _require(promotion_payload.get("packet_id") == packet_id, "promotion artifact packet_id does not match the requested packet_id")

    command = [sys.executable, "tools/ai/build_ai_packet_evidence_summary.py", "--verify-artifact", str(verify_path)]
    if args.packet_id:
        command[2:2] = ["--packet-id", args.packet_id]
    if promotion_path is not None:
        command.extend(["--promotion-artifact", str(promotion_path)])
    if output_path is not None:
        command.extend(["--output", str(output_path)])

    summary: dict[str, Any] = {
        "packet_id": packet_id,
        "tool": "tools/ai/build_ai_packet_evidence_summary.py",
        "command": _command_string(command),
        "verify_artifact_path": _normalize_path(verify_path),
        "verification": _extract_verify_summary(verify_payload),
        "result": "PASS",
    }

    if output_path is not None:
        summary["artifact_path"] = _normalize_path(output_path)

    if promotion_payload is not None:
        summary["promotion_artifact_path"] = _normalize_path(promotion_path)
        summary["promotion"] = _extract_promotion_summary(promotion_payload)

    rendered = json.dumps(summary, indent=2)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")

    print(rendered)
    return 0


if __name__ == "__main__":
    try:
        import subprocess

        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - exercised via CLI tests
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)