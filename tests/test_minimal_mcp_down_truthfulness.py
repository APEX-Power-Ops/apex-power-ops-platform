from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = REPO_ROOT / ".tmp" / "ai-workflow"
PS_STATE_FILE = STATE_DIR / "minimal-mcp-trio.json"
BASH_STATE_FILE = STATE_DIR / "minimal-mcp-trio.env"


def _run_json(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _expected_not_running_result() -> dict[str, object]:
    return {"status": "not-running"}


def _expected_stopped_result() -> dict[str, object]:
    return {"status": "stopped"}


def _start_bash_shell_process() -> tuple[subprocess.Popen[str], str]:
    process = subprocess.Popen(
        ["bash", "-lc", "printf '%s\n' \"$$\"; sleep 30"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    pid = process.stdout.readline().strip()
    if not pid:
        stderr = ""
        if process.stderr is not None:
            stderr = process.stderr.read()
        process.terminate()
        process.wait(timeout=5)
        raise RuntimeError(f"Failed to start Bash shell process: {stderr}")
    return process, pid


def _start_powershell_sleep_process() -> subprocess.Popen[str]:
    return subprocess.Popen(
        ["pwsh", "-NoProfile", "-Command", "Start-Sleep -Seconds 30"],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def _write_powershell_managed_state(pid: int) -> None:
    payload = {
        "started_at": "2026-05-11T00:00:00Z",
        "packet_id": "powershell-down-test",
        "mode": "managed",
        "processes": [
            {"name": "apex-fs", "pid": pid, "log": "fs.log"},
            {"name": "apex-db", "pid": pid, "log": "db.log"},
            {"name": "apex-jobs", "pid": pid, "log": "jobs.log"},
        ],
        "endpoints": {
            "fs": "http://127.0.0.1:59110/mcp",
            "db": "http://127.0.0.1:59111/mcp",
            "jobs": "http://127.0.0.1:59112/mcp",
        },
        "ledger_path": str(REPO_ROOT / ".apex-data" / "apex-jobs-ledger.json"),
    }
    PS_STATE_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_bash_managed_state(pid: str) -> None:
    BASH_STATE_FILE.write_text(
        "\n".join(
            [
                "STARTED_AT='2026-05-11T00:00:00Z'",
                "PACKET_ID='bash-down-test'",
                "MODE='managed'",
                f"FS_PID='{pid}'",
                f"DB_PID='{pid}'",
                f"JOBS_PID='{pid}'",
                f"LEDGER_PATH='{REPO_ROOT / '.apex-data' / 'apex-jobs-ledger.json'}'",
                "FS_ENDPOINT='http://127.0.0.1:59110/mcp'",
                "DB_ENDPOINT='http://127.0.0.1:59111/mcp'",
                "JOBS_ENDPOINT='http://127.0.0.1:59112/mcp'",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


@pytest.fixture(autouse=True)
def _clean_state_files() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    for path in (PS_STATE_FILE, BASH_STATE_FILE):
        if path.exists():
            path.unlink()
    yield
    for path in (PS_STATE_FILE, BASH_STATE_FILE):
        if path.exists():
            path.unlink()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_down_reports_not_running_without_state() -> None:
    result = _run_json(
        ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "down"],
    )

    assert result == _expected_not_running_result()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_down_reports_not_running_without_state() -> None:
    result = _run_json(
        ["bash", "tools/ai/run-minimal-mcp-trio.sh", "down"],
    )

    assert result == _expected_not_running_result()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_down_stops_managed_processes_and_removes_state() -> None:
    process = _start_powershell_sleep_process()
    try:
        _write_powershell_managed_state(process.pid)

        result = _run_json(
            ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "down"],
        )

        process.wait(timeout=5)
        assert result == _expected_stopped_result()
        assert not PS_STATE_FILE.exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_down_stops_managed_processes_and_removes_state() -> None:
    process, pid = _start_bash_shell_process()
    try:
        _write_bash_managed_state(pid)

        result = _run_json(
            ["bash", "tools/ai/run-minimal-mcp-trio.sh", "down"],
        )

        process.wait(timeout=5)
        assert result == _expected_stopped_result()
        assert not BASH_STATE_FILE.exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)