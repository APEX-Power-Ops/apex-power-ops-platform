from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_helper_module():
    helper_path = REPO_ROOT / "tools" / "ai" / "run_authoritative_host_packet.py"
    spec = importlib.util.spec_from_file_location("run_authoritative_host_packet", helper_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_remote_script_runs_host_chain_in_order() -> None:
    helper = _load_helper_module()

    script = helper.build_remote_script(
        packet_id="packet-799-lane-a",
        host_root="/home/olares/code/apex/apex-power-ops-platform",
        profile="strict-db-query",
        dsn_loader="/home/olares/apex-secrets/olares/ai-live-dsn.env",
    )

    expected_steps = [
        "bash tools/ai/run-minimal-mcp-trio.sh down packet-799-lane-a >/dev/null || true",
        "bash tools/ai/run-olares-host-bootstrap-status.sh packet-799-lane-a",
        "source /home/olares/apex-secrets/olares/ai-live-dsn.env",
        "bash tools/ai/run-minimal-mcp-trio.sh up packet-799-lane-a",
        "bash tools/ai/run-minimal-mcp-trio.sh verify packet-799-lane-a strict-db-query",
        '"${repo_python}" tools/ai/capture_apex_jobs_promotion.py --packet-id packet-799-lane-a --output /home/olares/code/apex/apex-power-ops-platform/tests/canary/mcp-contract/actual/apex-jobs-promotion-packet-799-lane-a.json',
        '"${repo_python}" tools/ai/build_ai_packet_evidence_summary.py --packet-id packet-799-lane-a --verify-artifact /home/olares/code/apex/apex-power-ops-platform/tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-packet-799-lane-a.json --promotion-artifact /home/olares/code/apex/apex-power-ops-platform/tests/canary/mcp-contract/actual/apex-jobs-promotion-packet-799-lane-a.json --output /home/olares/code/apex/apex-power-ops-platform/tests/canary/mcp-contract/actual/ai-packet-evidence-summary-packet-799-lane-a.json',
        "bash tools/ai/run-minimal-mcp-trio.sh down packet-799-lane-a",
        'final_status="$(bash tools/ai/run-minimal-mcp-trio.sh status packet-799-lane-a)"',
    ]

    positions: list[int] = []
    search_from = 0
    for step in expected_steps:
        position = script.index(step, search_from)
        positions.append(position)
        search_from = position + 1

    assert positions == sorted(positions)
    assert 'FINAL_STATUS_JSON="${final_status}" "${repo_python}" - <<\'"PY"' not in script
    assert 'FINAL_STATUS_JSON="${final_status}" "${repo_python}" - <<\'PY\'' in script


def test_plan_artifact_paths_matches_packet_conventions(tmp_path: Path) -> None:
    helper = _load_helper_module()

    paths = helper.plan_artifact_paths(
        packet_id="packet-799-lane-a",
        host_root="/home/olares/code/apex/apex-power-ops-platform",
        local_root=tmp_path,
    )

    assert paths["host_bootstrap"] == {
        "remote": "/home/olares/code/apex/apex-power-ops-platform/tests/canary/host-bootstrap-status/actual/host-bootstrap-status-packet-799-lane-a.json",
        "local": tmp_path / "tests" / "canary" / "host-bootstrap-status" / "actual" / "host-bootstrap-status-packet-799-lane-a.json",
    }
    assert paths["verify"] == {
        "remote": "/home/olares/code/apex/apex-power-ops-platform/tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-packet-799-lane-a.json",
        "local": tmp_path / "tests" / "canary" / "mcp-contract" / "actual" / "verify-minimal-mcp-trio-packet-799-lane-a.json",
    }
    assert paths["promotion"] == {
        "remote": "/home/olares/code/apex/apex-power-ops-platform/tests/canary/mcp-contract/actual/apex-jobs-promotion-packet-799-lane-a.json",
        "local": tmp_path / "tests" / "canary" / "mcp-contract" / "actual" / "apex-jobs-promotion-packet-799-lane-a.json",
    }
    assert paths["coordinator_summary"] == {
        "remote": "/home/olares/code/apex/apex-power-ops-platform/tests/canary/mcp-contract/actual/ai-packet-evidence-summary-packet-799-lane-a.json",
        "local": tmp_path / "tests" / "canary" / "mcp-contract" / "actual" / "ai-packet-evidence-summary-packet-799-lane-a.json",
    }


def test_orchestrate_packet_uses_stdin_fed_ssh_and_four_scp_imports(tmp_path: Path) -> None:
    helper = _load_helper_module()
    expected_head = helper._git_head(helper._repo_root())
    planned = helper.plan_artifact_paths(
        packet_id="packet-799-lane-a",
        host_root="/home/olares/code/apex/apex-power-ops-platform",
        local_root=tmp_path,
    )
    remote_contents = {
        planned["host_bootstrap"]["remote"]: {
            "packet_id": "packet-799-lane-a",
            "git": {"head": expected_head, "status_count": 0},
            "minimal_mcp": {"status": "not-running"},
        },
        planned["verify"]["remote"]: {
            "packet_id": "packet-799-lane-a",
            "profile": "strict-db-query",
            "result": "PASS",
        },
        planned["promotion"]["remote"]: {
            "packet_id": "packet-799-lane-a",
            "result": "PASS",
            "host_run": {
                "run_id": "host-run-123",
                "packet_id": "packet-799-lane-a",
                "status": "success",
            },
            "host_success_runs": [
                {"run_id": "host-run-123", "packet_id": "packet-799-lane-a", "status": "success"}
            ],
            "promotion": {"packet_id": "packet-799-lane-a", "supporting_run_ids": ["host-run-123"]},
        },
        planned["coordinator_summary"]["remote"]: {
            "packet_id": "packet-799-lane-a",
            "result": "PASS",
            "verify_artifact_path": planned["verify"]["remote"],
            "verification": {"result": "PASS", "profile": "strict-db-query"},
            "promotion_artifact_path": planned["promotion"]["remote"],
            "promotion": {
                "result": "PASS",
                "host_run": {"packet_id": "packet-799-lane-a", "run_id": "host-run-123"},
                "host_success_runs": [
                    {"run_id": "host-run-123", "packet_id": "packet-799-lane-a", "status": "success"}
                ],
                "promotion_record": {"packet_id": "packet-799-lane-a", "supporting_run_ids": ["host-run-123"]},
            },
        },
    }
    calls: list[tuple[list[str], str | None]] = []

    def fake_runner(command: list[str], input_text: str | None = None) -> None:
        calls.append((command, input_text))
        if command == ["ssh", "olares-mesh", "bash", "-s"]:
            assert input_text is not None
            assert "run-olares-host-bootstrap-status.sh packet-799-lane-a" in input_text
            return

        assert command[0] == "scp"
        assert input_text is None
        remote_spec = command[1]
        local_path = Path(command[2])
        assert remote_spec.startswith("olares-mesh:")
        remote_path = remote_spec.split(":", 1)[1]
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(json.dumps(remote_contents[remote_path]) + "\n", encoding="utf-8")

    summary = helper.orchestrate_packet(
        packet_id="packet-799-lane-a",
        host="olares-mesh",
        host_root="/home/olares/code/apex/apex-power-ops-platform",
        profile="strict-db-query",
        dsn_loader="/home/olares/apex-secrets/olares/ai-live-dsn.env",
        local_root=tmp_path,
        runner=fake_runner,
    )

    ssh_calls = [call for call in calls if call[0][0] == "ssh"]
    scp_calls = [call for call in calls if call[0][0] == "scp"]

    assert len(ssh_calls) == 1
    assert ssh_calls[0][0] == ["ssh", "olares-mesh", "bash", "-s"]
    assert ssh_calls[0][1] is not None

    assert len(scp_calls) == 4
    assert [call[0][1].split(":", 1)[1] for call in scp_calls] == [
        planned[name]["remote"] for name in helper.ARTIFACT_ORDER
    ]

    assert summary["packet_id"] == "packet-799-lane-a"
    assert summary["tool"] == "tools/ai/run_authoritative_host_packet.py"
    assert summary["host"] == "olares-mesh"
    assert summary["profile"] == "strict-db-query"
    assert summary["host_git_head"] == expected_head
    assert summary["host_status_count"] == 0
    assert summary["preflight_status"] == "not-running"
    assert summary["verify_result"] == "PASS"
    assert summary["verify_profile"] == "strict-db-query"
    assert summary["promotion_result"] == "PASS"
    assert summary["host_run_id"] == "host-run-123"
    assert summary["host_success_run_ids"] == ["host-run-123"]
    assert summary["promotion_supporting_run_ids"] == ["host-run-123"]
    assert summary["coordinator_summary_result"] == "PASS"
    assert summary["coordinator_verify_artifact_name"] == planned["verify"]["local"].name
    assert summary["coordinator_promotion_artifact_name"] == planned["promotion"]["local"].name
    assert summary["coordinator_host_success_run_ids"] == ["host-run-123"]
    assert summary["coordinator_supporting_run_ids"] == ["host-run-123"]
    assert summary["result"] == "PASS"
    assert summary["artifact_paths"] == {
        name: str(planned[name]["local"]).replace("\\", "/")
        for name in helper.ARTIFACT_ORDER
    }

    for name in helper.ARTIFACT_ORDER:
        local_path = Path(planned[name]["local"])
        assert local_path.exists()
        assert json.loads(local_path.read_text(encoding="utf-8")) == remote_contents[planned[name]["remote"]]


def test_run_subprocess_sends_remote_script_as_bytes(monkeypatch) -> None:
    helper = _load_helper_module()
    captured: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args[0], 0)

    monkeypatch.setattr(helper.subprocess, "run", fake_run)

    helper._run_subprocess(["ssh", "olares-mesh", "bash", "-s"], "set -euo pipefail\n")

    assert captured["args"] == (["ssh", "olares-mesh", "bash", "-s"],)
    assert captured["kwargs"]["check"] is True
    assert captured["kwargs"]["input"] == b"set -euo pipefail\n"
    assert "text" not in captured["kwargs"]


def test_orchestrate_packet_rejects_dirty_host_bootstrap(tmp_path: Path) -> None:
    helper = _load_helper_module()
    planned = helper.plan_artifact_paths(
        packet_id="packet-800-lane-a",
        host_root="/home/olares/code/apex/apex-power-ops-platform",
        local_root=tmp_path,
    )

    def fake_runner(command: list[str], input_text: str | None = None) -> None:
        if command[0] == "ssh":
            return

        remote_path = command[1].split(":", 1)[1]
        local_path = Path(command[2])
        local_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"artifact": remote_path, "packet_id": "packet-800-lane-a"}
        if remote_path == planned["host_bootstrap"]["remote"]:
            payload = {
                "packet_id": "packet-800-lane-a",
                "git": {"head": helper._git_head(helper._repo_root()), "status_count": 2},
                "minimal_mcp": {"status": "not-running"},
            }
        local_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    try:
        helper.orchestrate_packet(
            packet_id="packet-800-lane-a",
            host="olares-mesh",
            host_root="/home/olares/code/apex/apex-power-ops-platform",
            profile="strict-db-query",
            dsn_loader="/home/olares/apex-secrets/olares/ai-live-dsn.env",
            local_root=tmp_path,
            runner=fake_runner,
        )
    except ValueError as error:
        assert str(error) == "host bootstrap artifact shows dirty host worktree: status_count=2"
        return

    raise AssertionError("expected orchestrate_packet to reject a dirty host bootstrap artifact")


def test_orchestrate_packet_rejects_verify_packet_mismatch(tmp_path: Path) -> None:
    helper = _load_helper_module()
    expected_head = helper._git_head(helper._repo_root())
    planned = helper.plan_artifact_paths(
        packet_id="packet-801-lane-a",
        host_root="/home/olares/code/apex/apex-power-ops-platform",
        local_root=tmp_path,
    )

    remote_contents = {
        planned["host_bootstrap"]["remote"]: {
            "packet_id": "packet-801-lane-a",
            "git": {"head": expected_head, "status_count": 0},
            "minimal_mcp": {"status": "not-running"},
        },
        planned["verify"]["remote"]: {
            "packet_id": "packet-801-other",
            "profile": "strict-db-query",
            "result": "PASS",
        },
        planned["promotion"]["remote"]: {
            "packet_id": "packet-801-lane-a",
            "result": "PASS",
            "host_run": {"run_id": "host-run-123", "packet_id": "packet-801-lane-a", "status": "success"},
            "host_success_runs": [
                {"run_id": "host-run-123", "packet_id": "packet-801-lane-a", "status": "success"}
            ],
            "promotion": {"packet_id": "packet-801-lane-a", "supporting_run_ids": ["host-run-123"]},
        },
        planned["coordinator_summary"]["remote"]: {
            "packet_id": "packet-801-lane-a",
            "result": "PASS",
            "verify_artifact_path": planned["verify"]["remote"],
            "verification": {"result": "PASS", "profile": "strict-db-query"},
            "promotion_artifact_path": planned["promotion"]["remote"],
            "promotion": {
                "result": "PASS",
                "host_run": {"packet_id": "packet-801-lane-a", "run_id": "host-run-123"},
                "host_success_runs": [
                    {"run_id": "host-run-123", "packet_id": "packet-801-lane-a", "status": "success"}
                ],
                "promotion_record": {"packet_id": "packet-801-lane-a", "supporting_run_ids": ["host-run-123"]},
            },
        },
    }

    def fake_runner(command: list[str], input_text: str | None = None) -> None:
        if command[0] == "ssh":
            return

        remote_path = command[1].split(":", 1)[1]
        local_path = Path(command[2])
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(json.dumps(remote_contents[remote_path]) + "\n", encoding="utf-8")

    try:
        helper.orchestrate_packet(
            packet_id="packet-801-lane-a",
            host="olares-mesh",
            host_root="/home/olares/code/apex/apex-power-ops-platform",
            profile="strict-db-query",
            dsn_loader="/home/olares/apex-secrets/olares/ai-live-dsn.env",
            local_root=tmp_path,
            runner=fake_runner,
        )
    except ValueError as error:
        assert str(error) == "verify artifact packet_id mismatch: expected packet-801-lane-a, got packet-801-other"
        return

    raise AssertionError("expected orchestrate_packet to reject a mismatched verify artifact")


def test_orchestrate_packet_rejects_summary_verify_artifact_path_mismatch(tmp_path: Path) -> None:
    helper = _load_helper_module()
    expected_head = helper._git_head(helper._repo_root())
    planned = helper.plan_artifact_paths(
        packet_id="packet-802-lane-a",
        host_root="/home/olares/code/apex/apex-power-ops-platform",
        local_root=tmp_path,
    )

    remote_contents = {
        planned["host_bootstrap"]["remote"]: {
            "packet_id": "packet-802-lane-a",
            "git": {"head": expected_head, "status_count": 0},
            "minimal_mcp": {"status": "not-running"},
        },
        planned["verify"]["remote"]: {
            "packet_id": "packet-802-lane-a",
            "profile": "strict-db-query",
            "result": "PASS",
        },
        planned["promotion"]["remote"]: {
            "packet_id": "packet-802-lane-a",
            "result": "PASS",
            "host_run": {"run_id": "host-run-802", "packet_id": "packet-802-lane-a", "status": "success"},
            "host_success_runs": [
                {"run_id": "host-run-802", "packet_id": "packet-802-lane-a", "status": "success"}
            ],
            "promotion": {"packet_id": "packet-802-lane-a", "supporting_run_ids": ["host-run-802"]},
        },
        planned["coordinator_summary"]["remote"]: {
            "packet_id": "packet-802-lane-a",
            "result": "PASS",
            "verify_artifact_path": "/remote/wrong-verify.json",
            "verification": {"result": "PASS", "profile": "strict-db-query"},
            "promotion_artifact_path": planned["promotion"]["remote"],
            "promotion": {
                "result": "PASS",
                "host_run": {"packet_id": "packet-802-lane-a", "run_id": "host-run-802"},
                "host_success_runs": [
                    {"run_id": "host-run-802", "packet_id": "packet-802-lane-a", "status": "success"}
                ],
                "promotion_record": {"packet_id": "packet-802-lane-a", "supporting_run_ids": ["host-run-802"]},
            },
        },
    }

    def fake_runner(command: list[str], input_text: str | None = None) -> None:
        if command[0] == "ssh":
            return

        remote_path = command[1].split(":", 1)[1]
        local_path = Path(command[2])
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(json.dumps(remote_contents[remote_path]) + "\n", encoding="utf-8")

    try:
        helper.orchestrate_packet(
            packet_id="packet-802-lane-a",
            host="olares-mesh",
            host_root="/home/olares/code/apex/apex-power-ops-platform",
            profile="strict-db-query",
            dsn_loader="/home/olares/apex-secrets/olares/ai-live-dsn.env",
            local_root=tmp_path,
            runner=fake_runner,
        )
    except ValueError as error:
        assert str(error) == (
            "coordinator summary verify artifact path mismatch: expected "
            "verify-minimal-mcp-trio-packet-802-lane-a.json, got wrong-verify.json"
        )
        return

    raise AssertionError("expected orchestrate_packet to reject a mismatched coordinator summary verify artifact path")


def test_orchestrate_packet_rejects_promotion_supporting_run_drift(tmp_path: Path) -> None:
    helper = _load_helper_module()
    expected_head = helper._git_head(helper._repo_root())
    planned = helper.plan_artifact_paths(
        packet_id="packet-803-lane-a",
        host_root="/home/olares/code/apex/apex-power-ops-platform",
        local_root=tmp_path,
    )

    remote_contents = {
        planned["host_bootstrap"]["remote"]: {
            "packet_id": "packet-803-lane-a",
            "git": {"head": expected_head, "status_count": 0},
            "minimal_mcp": {"status": "not-running"},
        },
        planned["verify"]["remote"]: {
            "packet_id": "packet-803-lane-a",
            "profile": "strict-db-query",
            "result": "PASS",
        },
        planned["promotion"]["remote"]: {
            "packet_id": "packet-803-lane-a",
            "result": "PASS",
            "host_run": {"run_id": "host-run-803", "packet_id": "packet-803-lane-a", "status": "success"},
            "host_success_runs": [
                {"run_id": "host-run-803", "packet_id": "packet-803-lane-a", "status": "success"}
            ],
            "promotion": {"packet_id": "packet-803-lane-a", "supporting_run_ids": ["other-run"]},
        },
        planned["coordinator_summary"]["remote"]: {
            "packet_id": "packet-803-lane-a",
            "result": "PASS",
            "verify_artifact_path": planned["verify"]["remote"],
            "verification": {"result": "PASS", "profile": "strict-db-query"},
            "promotion_artifact_path": planned["promotion"]["remote"],
            "promotion": {
                "result": "PASS",
                "host_run": {"packet_id": "packet-803-lane-a", "run_id": "host-run-803"},
                "host_success_runs": [
                    {"run_id": "host-run-803", "packet_id": "packet-803-lane-a", "status": "success"}
                ],
                "promotion_record": {"packet_id": "packet-803-lane-a", "supporting_run_ids": ["other-run"]},
            },
        },
    }

    def fake_runner(command: list[str], input_text: str | None = None) -> None:
        if command[0] == "ssh":
            return

        remote_path = command[1].split(":", 1)[1]
        local_path = Path(command[2])
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(json.dumps(remote_contents[remote_path]) + "\n", encoding="utf-8")

    try:
        helper.orchestrate_packet(
            packet_id="packet-803-lane-a",
            host="olares-mesh",
            host_root="/home/olares/code/apex/apex-power-ops-platform",
            profile="strict-db-query",
            dsn_loader="/home/olares/apex-secrets/olares/ai-live-dsn.env",
            local_root=tmp_path,
            runner=fake_runner,
        )
    except ValueError as error:
        assert str(error) == "promotion artifact supporting_run_ids missing accepted host_run id host-run-803"
        return

    raise AssertionError("expected orchestrate_packet to reject promotion supporting_run_ids drift")


def test_orchestrate_packet_rejects_summary_host_success_run_drift(tmp_path: Path) -> None:
    helper = _load_helper_module()
    expected_head = helper._git_head(helper._repo_root())
    planned = helper.plan_artifact_paths(
        packet_id="packet-804-lane-a",
        host_root="/home/olares/code/apex/apex-power-ops-platform",
        local_root=tmp_path,
    )

    remote_contents = {
        planned["host_bootstrap"]["remote"]: {
            "packet_id": "packet-804-lane-a",
            "git": {"head": expected_head, "status_count": 0},
            "minimal_mcp": {"status": "not-running"},
        },
        planned["verify"]["remote"]: {
            "packet_id": "packet-804-lane-a",
            "profile": "strict-db-query",
            "result": "PASS",
        },
        planned["promotion"]["remote"]: {
            "packet_id": "packet-804-lane-a",
            "result": "PASS",
            "host_run": {"run_id": "host-run-804", "packet_id": "packet-804-lane-a", "status": "success"},
            "host_success_runs": [
                {"run_id": "host-run-804", "packet_id": "packet-804-lane-a", "status": "success"}
            ],
            "promotion": {"packet_id": "packet-804-lane-a", "supporting_run_ids": ["host-run-804"]},
        },
        planned["coordinator_summary"]["remote"]: {
            "packet_id": "packet-804-lane-a",
            "result": "PASS",
            "verify_artifact_path": planned["verify"]["remote"],
            "verification": {"result": "PASS", "profile": "strict-db-query"},
            "promotion_artifact_path": planned["promotion"]["remote"],
            "promotion": {
                "result": "PASS",
                "host_run": {"packet_id": "packet-804-lane-a", "run_id": "host-run-804"},
                "host_success_runs": [
                    {"run_id": "host-run-804", "packet_id": "packet-804-lane-a", "status": "success"},
                    {"run_id": "extra-run", "packet_id": "packet-804-lane-a", "status": "success"}
                ],
                "promotion_record": {"packet_id": "packet-804-lane-a", "supporting_run_ids": ["host-run-804"]},
            },
        },
    }

    def fake_runner(command: list[str], input_text: str | None = None) -> None:
        if command[0] == "ssh":
            return

        remote_path = command[1].split(":", 1)[1]
        local_path = Path(command[2])
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(json.dumps(remote_contents[remote_path]) + "\n", encoding="utf-8")

    try:
        helper.orchestrate_packet(
            packet_id="packet-804-lane-a",
            host="olares-mesh",
            host_root="/home/olares/code/apex/apex-power-ops-platform",
            profile="strict-db-query",
            dsn_loader="/home/olares/apex-secrets/olares/ai-live-dsn.env",
            local_root=tmp_path,
            runner=fake_runner,
        )
    except ValueError as error:
        assert str(error) == (
            "coordinator summary host_success_runs mismatch: "
            "expected ['host-run-804'], got ['host-run-804', 'extra-run']"
        )
        return

    raise AssertionError("expected orchestrate_packet to reject coordinator summary host_success_runs drift")


def test_orchestrate_packet_rejects_unbacked_promotion_supporting_run(tmp_path: Path) -> None:
    helper = _load_helper_module()
    expected_head = helper._git_head(helper._repo_root())
    planned = helper.plan_artifact_paths(
        packet_id="packet-805-lane-a",
        host_root="/home/olares/code/apex/apex-power-ops-platform",
        local_root=tmp_path,
    )

    remote_contents = {
        planned["host_bootstrap"]["remote"]: {
            "packet_id": "packet-805-lane-a",
            "git": {"head": expected_head, "status_count": 0},
            "minimal_mcp": {"status": "not-running"},
        },
        planned["verify"]["remote"]: {
            "packet_id": "packet-805-lane-a",
            "profile": "strict-db-query",
            "result": "PASS",
        },
        planned["promotion"]["remote"]: {
            "packet_id": "packet-805-lane-a",
            "result": "PASS",
            "host_run": {"run_id": "host-run-805", "packet_id": "packet-805-lane-a", "status": "success"},
            "host_success_runs": [
                {"run_id": "host-run-805", "packet_id": "packet-805-lane-a", "status": "success"}
            ],
            "promotion": {"packet_id": "packet-805-lane-a", "supporting_run_ids": ["host-run-805", "ghost-run"]},
        },
        planned["coordinator_summary"]["remote"]: {
            "packet_id": "packet-805-lane-a",
            "result": "PASS",
            "verify_artifact_path": planned["verify"]["remote"],
            "verification": {"result": "PASS", "profile": "strict-db-query"},
            "promotion_artifact_path": planned["promotion"]["remote"],
            "promotion": {
                "result": "PASS",
                "host_run": {"packet_id": "packet-805-lane-a", "run_id": "host-run-805"},
                "host_success_runs": [
                    {"run_id": "host-run-805", "packet_id": "packet-805-lane-a", "status": "success"}
                ],
                "promotion_record": {"packet_id": "packet-805-lane-a", "supporting_run_ids": ["host-run-805", "ghost-run"]},
            },
        },
    }

    def fake_runner(command: list[str], input_text: str | None = None) -> None:
        if command[0] == "ssh":
            return

        remote_path = command[1].split(":", 1)[1]
        local_path = Path(command[2])
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(json.dumps(remote_contents[remote_path]) + "\n", encoding="utf-8")

    try:
        helper.orchestrate_packet(
            packet_id="packet-805-lane-a",
            host="olares-mesh",
            host_root="/home/olares/code/apex/apex-power-ops-platform",
            profile="strict-db-query",
            dsn_loader="/home/olares/apex-secrets/olares/ai-live-dsn.env",
            local_root=tmp_path,
            runner=fake_runner,
        )
    except ValueError as error:
        assert str(error) == "promotion artifact supporting_run_ids are not backed by host_success_runs: ['ghost-run']"
        return

    raise AssertionError("expected orchestrate_packet to reject unsupported promotion supporting_run_ids")