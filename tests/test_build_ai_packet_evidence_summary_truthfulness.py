from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_helper(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/ai/build_ai_packet_evidence_summary.py", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _expected_command(argv: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return shlex.join(argv)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_builds_summary_from_verify_and_legacy_promotion_artifacts(tmp_path: Path) -> None:
    packet_id = "2026-05-13-olares-dev-residency-797"
    verify_path = tmp_path / f"verify-minimal-mcp-trio-{packet_id}.json"
    promotion_path = tmp_path / f"apex-jobs-promotion-{packet_id}.json"
    output_path = tmp_path / f"packet-evidence-summary-{packet_id}.json"

    verify_payload = {
        "packet_id": packet_id,
        "profile": "strict-db-query",
        "result": "PASS",
        "checks": {
            "jobs_promote_guard": {"status": "pass", "detail": "guard refused without host evidence"},
            "jobs_end_run": {"status": "pass", "run": {"run_id": "sandbox-run-1", "env": "sandbox", "status": "success"}},
            "jobs_list_runs": {"status": "pass", "result": {"runs": [{"run_id": "sandbox-run-1", "env": "sandbox", "status": "success"}]}},
        },
    }
    promotion_payload = {
        "packet_id": packet_id,
        "command": "python tools/ai/capture_apex_jobs_promotion.py",
        "env": "host",
        "service": "ai-workflow",
        "result": "PASS",
        "checks": {
            "jobs_end_run": {"status": "pass", "run": {"run_id": "host-run-1", "env": "host", "status": "success"}},
            "jobs_list_runs": {"status": "pass", "result": {"runs": [{"run_id": "host-run-1", "env": "host", "status": "success"}]}},
            "jobs_promote_packet": {"status": "pass", "result": {"packet_id": packet_id, "supporting_run_ids": ["host-run-1"]}},
        },
    }

    _write_json(verify_path, verify_payload)
    _write_json(promotion_path, promotion_payload)

    result = _run_helper(
        "--packet-id",
        packet_id,
        "--verify-artifact",
        str(verify_path),
        "--promotion-artifact",
        str(promotion_path),
        "--output",
        str(output_path),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    expected_command = _expected_command(
        [
            sys.executable,
            "tools/ai/build_ai_packet_evidence_summary.py",
            "--packet-id",
            packet_id,
            "--verify-artifact",
            str(verify_path),
            "--promotion-artifact",
            str(promotion_path),
            "--output",
            str(output_path),
        ]
    )
    assert payload == {
        "packet_id": packet_id,
        "tool": "tools/ai/build_ai_packet_evidence_summary.py",
        "command": expected_command,
        "verify_artifact_path": str(verify_path).replace("\\", "/"),
        "artifact_path": str(output_path).replace("\\", "/"),
        "promotion_artifact_path": str(promotion_path).replace("\\", "/"),
        "verification": {
            "profile": "strict-db-query",
            "result": "PASS",
            "guard_detail": "guard refused without host evidence",
            "sandbox_run": {"run_id": "sandbox-run-1", "env": "sandbox", "status": "success"},
            "listed_runs": [{"run_id": "sandbox-run-1", "env": "sandbox", "status": "success"}],
        },
        "promotion": {
            "env": "host",
            "service": "ai-workflow",
            "result": "PASS",
            "host_run": {"run_id": "host-run-1", "env": "host", "status": "success"},
            "host_success_runs": [{"run_id": "host-run-1", "env": "host", "status": "success"}],
            "promotion_record": {"packet_id": packet_id, "supporting_run_ids": ["host-run-1"]},
        },
        "result": "PASS",
    }
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_prefers_top_level_promotion_provenance_when_present(tmp_path: Path) -> None:
    packet_id = "packet-797-top-level"
    verify_path = tmp_path / "verify.json"
    promotion_path = tmp_path / "promotion.json"

    _write_json(
        verify_path,
        {
            "packet_id": packet_id,
            "profile": "baseline",
            "result": "PASS",
            "checks": {
                "jobs_end_run": {"status": "pass", "run": {"run_id": "sandbox-run-2", "env": "sandbox", "status": "success"}},
                "jobs_list_runs": {"status": "pass", "result": {"runs": [{"run_id": "sandbox-run-2", "env": "sandbox", "status": "success"}]}},
            },
        },
    )
    _write_json(
        promotion_path,
        {
            "packet_id": packet_id,
            "env": "host",
            "service": "ai-workflow",
            "result": "PASS",
            "host_run": {"run_id": "host-top-level", "env": "host", "status": "success"},
            "host_success_runs": [{"run_id": "host-top-level", "env": "host", "status": "success"}],
            "promotion": {"packet_id": packet_id, "supporting_run_ids": ["host-top-level"]},
            "checks": {
                "jobs_end_run": {"status": "pass", "run": {"run_id": "nested-host-run", "env": "host", "status": "success"}},
                "jobs_list_runs": {"status": "pass", "result": {"runs": [{"run_id": "nested-host-run", "env": "host", "status": "success"}]}},
                "jobs_promote_packet": {"status": "pass", "result": {"packet_id": packet_id, "supporting_run_ids": ["nested-host-run"]}},
            },
        },
    )

    result = _run_helper("--verify-artifact", str(verify_path), "--promotion-artifact", str(promotion_path))

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["promotion"]["host_run"]["run_id"] == "host-top-level"
    assert payload["promotion"]["host_success_runs"][0]["run_id"] == "host-top-level"
    assert payload["promotion"]["promotion_record"]["supporting_run_ids"] == ["host-top-level"]


def test_fails_when_packet_ids_do_not_match(tmp_path: Path) -> None:
    verify_path = tmp_path / "verify.json"
    promotion_path = tmp_path / "promotion.json"

    _write_json(
        verify_path,
        {
            "packet_id": "packet-a",
            "result": "PASS",
            "checks": {
                "jobs_end_run": {"status": "pass", "run": {"run_id": "sandbox-run-a"}},
                "jobs_list_runs": {"status": "pass", "result": {"runs": [{"run_id": "sandbox-run-a"}]}},
            },
        },
    )
    _write_json(
        promotion_path,
        {
            "packet_id": "packet-b",
            "env": "host",
            "service": "ai-workflow",
            "result": "PASS",
            "host_run": {"run_id": "host-run-b"},
            "host_success_runs": [{"run_id": "host-run-b"}],
            "promotion": {"packet_id": "packet-b"},
        },
    )

    result = _run_helper("--verify-artifact", str(verify_path), "--promotion-artifact", str(promotion_path))

    assert result.returncode == 1
    assert "promotion artifact packet_id does not match" in result.stderr


def test_fails_when_verify_artifact_is_not_pass(tmp_path: Path) -> None:
    verify_path = tmp_path / "verify.json"

    _write_json(
        verify_path,
        {
            "packet_id": "packet-fail",
            "result": "FAIL",
            "checks": {},
        },
    )

    result = _run_helper("--verify-artifact", str(verify_path))

    assert result.returncode == 1
    assert "verify artifact must report result=PASS" in result.stderr