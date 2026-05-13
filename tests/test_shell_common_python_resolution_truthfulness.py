from __future__ import annotations

import os
import re
import shlex
import shutil
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


def _last_nonempty_line(text: str) -> str:
    lines = [line for line in text.replace("\r\n", "\n").split("\n") if line]
    assert lines
    assert all(line == line.strip() for line in lines)
    return lines[-1]


def _normalized_powershell_throw_message(stderr: str) -> str:
    stripped_stderr = re.sub(r"\x1b\[[0-9;]*m", "", stderr)
    return " ".join(
        content[1:]
        for line in stripped_stderr.splitlines()
        if "|" in line
        for _, separator, content in [line.partition("|")]
        if separator
        if content.startswith(" ")
        if content == f" {content[1:].strip()}"
        if content[1:] and not content[1:].startswith("throw") and not set(content[1:]) <= {"~"}
    )


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash helper tests")
def test_common_bash_repo_python_materializes_bare_command_override(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_python = bin_dir / "fake-python"
    fake_python.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8", newline="\n")
    fake_python.chmod(0o755)

    env = os.environ.copy()
    bin_dir_bash = _bash_path(bin_dir)

    completed = _run_bash(
        f"export PATH={shlex.quote(bin_dir_bash)}:\"$PATH\" ; export APEX_PLATFORM_PYTHON=fake-python ; get_apex_repo_python",
        env=env,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == _bash_path(fake_python)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash helper tests")
def test_common_bash_repo_python_fails_for_missing_command_override() -> None:
    env = os.environ.copy()

    completed = _run_bash(
        "export APEX_PLATFORM_PYTHON=missing-bash-python-command ; get_apex_repo_python",
        env=env,
    )

    assert completed.returncode == 1
    assert _last_nonempty_line(completed.stderr) == (
        "Configured APEX_PLATFORM_PYTHON command not found: missing-bash-python-command"
    )


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash helper tests")
def test_common_bash_repo_python_fails_for_missing_path_override(tmp_path: Path) -> None:
    env = os.environ.copy()
    missing_python = _bash_path(tmp_path / "missing-python")

    completed = _run_bash(
        f"export APEX_PLATFORM_PYTHON={shlex.quote(missing_python)} ; get_apex_repo_python",
        env=env,
    )

    assert completed.returncode == 1
    assert _last_nonempty_line(completed.stderr) == (
        f"Configured APEX_PLATFORM_PYTHON path not found: {missing_python}"
    )


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell helper tests")
def test_common_powershell_repo_python_materializes_bare_command_override(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_python = bin_dir / "fake-python.ps1"
    fake_python.write_text("exit 0\n", encoding="utf-8")

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["APEX_PLATFORM_PYTHON"] = "fake-python.ps1"

    completed = _run_powershell("Get-ApexRepoPython", env=env)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == str(fake_python.resolve())


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell helper tests")
def test_common_powershell_repo_python_fails_for_missing_command_override() -> None:
    env = os.environ.copy()
    env["APEX_PLATFORM_PYTHON"] = "missing-powershell-python-command"

    completed = _run_powershell("Get-ApexRepoPython", env=env)

    assert completed.returncode == 1
    assert _normalized_powershell_throw_message(completed.stderr) == (
        "Configured APEX_PLATFORM_PYTHON command not found: missing-powershell-python-command"
    )


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell helper tests")
def test_common_powershell_repo_python_fails_for_missing_path_override(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["APEX_PLATFORM_PYTHON"] = str(tmp_path / "missing-python.ps1")

    completed = _run_powershell("Get-ApexRepoPython", env=env)

    assert completed.returncode == 1
    assert _normalized_powershell_throw_message(completed.stderr) == (
        f"Configured APEX_PLATFORM_PYTHON path not found: {tmp_path / 'missing-python.ps1'}"
    )