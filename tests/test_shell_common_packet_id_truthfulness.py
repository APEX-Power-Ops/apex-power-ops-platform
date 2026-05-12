from __future__ import annotations

import os
import re
import shlex
import shutil
import socket
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _bash_path(path: Path) -> str:
    resolved = path.resolve().as_posix()
    if len(resolved) >= 3 and resolved[1:3] == ":/":
        return f"/mnt/{resolved[0].lower()}/{resolved[3:]}"
    return resolved


def _run_bash(function_call: str, *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    repo_root_bash = _bash_path(REPO_ROOT)
    command = " ; ".join(
        [
            f"cd {shlex.quote(repo_root_bash)}",
            "source tools/shell/common.sh",
            function_call,
        ]
    )
    return subprocess.run(
        ["bash", "-lc", command],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_powershell(function_call: str, *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    command = f". .\\tools\\shell\\common.ps1; {function_call}"
    return subprocess.run(
        ["pwsh", "-NoProfile", "-Command", command],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _contains_invalid_packet_id_message(text: str, packet_id: str) -> bool:
    normalized = _strip_ansi(text).replace("\r", "")
    return (
        f"Invalid packet id '{packet_id}'. Packet ids must match" in normalized
        and "^[A-Za-z0-9][A-Za-z0-9._-]*$." in normalized
    )


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash helper tests")
def test_common_bash_packet_id_uses_env_value() -> None:
    env = os.environ.copy()

    completed = _run_bash("export APEX_PACKET_ID=env-bash-packet-id ; get_apex_default_packet_id minimal-mcp-trio", env=env)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "env-bash-packet-id"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash helper tests")
def test_common_bash_packet_id_rejects_invalid_env_value() -> None:
    env = os.environ.copy()

    completed = _run_bash("export APEX_PACKET_ID='bad packet id' ; get_apex_default_packet_id minimal-mcp-trio", env=env)

    assert completed.returncode == 1
    assert completed.stdout == ""
    assert completed.stderr.strip() == "Invalid packet id 'bad packet id'. Packet ids must match ^[A-Za-z0-9][A-Za-z0-9._-]*$."


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash helper tests")
def test_common_bash_packet_id_generates_adhoc_label_when_env_missing() -> None:
    env = os.environ.copy()

    completed = _run_bash("unset APEX_PACKET_ID ; get_apex_default_packet_id hold-boundary", env=env)

    assert completed.returncode == 0, completed.stderr
    assert re.fullmatch(r"adhoc-hold-boundary-\d{4}-\d{2}-\d{2}-\d{6}", completed.stdout.strip())


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash helper tests")
def test_common_bash_packet_id_defaults_to_operator_label_when_argument_is_omitted() -> None:
    env = os.environ.copy()

    completed = _run_bash("unset APEX_PACKET_ID ; get_apex_default_packet_id", env=env)

    assert completed.returncode == 0, completed.stderr
    assert re.fullmatch(r"adhoc-operator-\d{4}-\d{2}-\d{2}-\d{6}", completed.stdout.strip())


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell helper tests")
def test_common_powershell_packet_id_uses_env_value() -> None:
    env = os.environ.copy()
    env["APEX_PACKET_ID"] = "env-powershell-packet-id"

    completed = _run_powershell("Get-ApexDefaultPacketId 'minimal-mcp-trio'", env=env)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "env-powershell-packet-id"


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell helper tests")
def test_common_powershell_packet_id_rejects_invalid_env_value() -> None:
    env = os.environ.copy()
    env["APEX_PACKET_ID"] = "bad packet id"

    completed = _run_powershell("Get-ApexDefaultPacketId 'minimal-mcp-trio'", env=env)

    assert completed.returncode == 1
    assert completed.stdout == ""
    assert _contains_invalid_packet_id_message(completed.stderr, "bad packet id")


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell helper tests")
def test_common_powershell_packet_id_generates_adhoc_label_when_env_missing() -> None:
    env = os.environ.copy()
    env.pop("APEX_PACKET_ID", None)

    completed = _run_powershell("Get-ApexDefaultPacketId 'host-bootstrap-status'", env=env)

    assert completed.returncode == 0, completed.stderr
    assert re.fullmatch(r"adhoc-host-bootstrap-status-\d{4}-\d{2}-\d{2}-\d{6}", completed.stdout.strip())


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell helper tests")
def test_common_powershell_packet_id_defaults_to_operator_label_when_argument_is_omitted() -> None:
    env = os.environ.copy()
    env.pop("APEX_PACKET_ID", None)

    completed = _run_powershell("Get-ApexDefaultPacketId", env=env)

    assert completed.returncode == 0, completed.stderr
    assert re.fullmatch(r"adhoc-operator-\d{4}-\d{2}-\d{2}-\d{6}", completed.stdout.strip())