from __future__ import annotations

import contextlib
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_DEV_FILE = REPO_ROOT / ".env.dev"
ENV_DEV_TEMPLATE_FILE = REPO_ROOT / ".env.dev.template"


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


def _template_value(name: str) -> str:
    for line in ENV_DEV_TEMPLATE_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        assert line == stripped
        key, value = line.split("=", 1)
        assert key == key.strip()
        assert value == value.strip()
        if key == name:
            return value

    raise AssertionError(f"Template variable not found: {name}")


@contextlib.contextmanager
def _hide_repo_env_files(tmp_path: Path, *, hide_template: bool = False):
    backup_path = tmp_path / ".env.dev.backup"
    template_backup_path = tmp_path / ".env.dev.template.backup"
    had_env_dev = ENV_DEV_FILE.exists()
    had_template = ENV_DEV_TEMPLATE_FILE.exists()

    if had_env_dev:
        ENV_DEV_FILE.replace(backup_path)
    if hide_template and had_template:
        ENV_DEV_TEMPLATE_FILE.replace(template_backup_path)

    try:
        yield
    finally:
        if ENV_DEV_FILE.exists() and not had_env_dev:
            ENV_DEV_FILE.unlink()
        if had_env_dev:
            if ENV_DEV_FILE.exists():
                ENV_DEV_FILE.unlink()
            backup_path.replace(ENV_DEV_FILE)
        if ENV_DEV_TEMPLATE_FILE.exists() and not had_template:
            ENV_DEV_TEMPLATE_FILE.unlink()
        if hide_template and had_template:
            if ENV_DEV_TEMPLATE_FILE.exists():
                ENV_DEV_TEMPLATE_FILE.unlink()
            template_backup_path.replace(ENV_DEV_TEMPLATE_FILE)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash helper tests")
def test_common_bash_import_env_file_imports_values_from_explicit_crlf_file(tmp_path: Path) -> None:
    env_file = tmp_path / "bash.env"
    env_file.write_text(
        "# ignored comment\r\n\r\nAPEX_TEST_ALPHA=bash-alpha\r\nAPEX_TEST_BETA=bash-beta\r\n",
        encoding="utf-8",
        newline="",
    )

    env = os.environ.copy()
    env.pop("APEX_TEST_ALPHA", None)
    env.pop("APEX_TEST_BETA", None)
    env_file_bash = _bash_path(env_file)
    repo_root_bash = _bash_path(REPO_ROOT)
    script_path = tmp_path / "check-bash-import.sh"
    script_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"cd {shlex.quote(repo_root_bash)}\n"
        "source tools/shell/common.sh\n"
        "unset APEX_TEST_ALPHA APEX_TEST_BETA\n"
        f"import_apex_env_file {shlex.quote(env_file_bash)}\n"
        "printf '%s|%s' \"${APEX_TEST_ALPHA-}\" \"${APEX_TEST_BETA-}\"\n",
        encoding="utf-8",
        newline="\n",
    )
    script_path.chmod(0o755)
    script_path_bash = _bash_path(script_path)

    completed = _run_bash(f"bash {shlex.quote(script_path_bash)}", env=env)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "bash-alpha|bash-beta"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash helper tests")
def test_common_bash_import_env_file_falls_back_to_repo_template_when_env_dev_is_missing(tmp_path: Path) -> None:
    env = os.environ.copy()
    env.pop("APEX_DEV_MCP_FS_PORT", None)
    env.pop("APEX_DEV_MCP_JOBS_PORT", None)
    expected_fs_port = _template_value("APEX_DEV_MCP_FS_PORT")
    expected_jobs_port = _template_value("APEX_DEV_MCP_JOBS_PORT")
    repo_root_bash = _bash_path(REPO_ROOT)
    script_path = tmp_path / "check-bash-template-fallback.sh"
    script_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"cd {shlex.quote(repo_root_bash)}\n"
        "source tools/shell/common.sh\n"
        "unset APEX_DEV_MCP_FS_PORT APEX_DEV_MCP_JOBS_PORT\n"
        "import_apex_env_file\n"
        "printf '%s|%s' \"${APEX_DEV_MCP_FS_PORT-}\" \"${APEX_DEV_MCP_JOBS_PORT-}\"\n",
        encoding="utf-8",
        newline="\n",
    )
    script_path.chmod(0o755)
    script_path_bash = _bash_path(script_path)

    with _hide_repo_env_files(tmp_path):
        completed = _run_bash(f"bash {shlex.quote(script_path_bash)}", env=env)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == f"{expected_fs_port}|{expected_jobs_port}"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash helper tests")
def test_common_bash_import_env_file_noops_when_repo_env_and_template_are_missing(tmp_path: Path) -> None:
    env = os.environ.copy()
    env.pop("APEX_DEV_MCP_FS_PORT", None)
    env.pop("APEX_DEV_MCP_JOBS_PORT", None)
    repo_root_bash = _bash_path(REPO_ROOT)
    script_path = tmp_path / "check-bash-missing-env-files.sh"
    script_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"cd {shlex.quote(repo_root_bash)}\n"
        "source tools/shell/common.sh\n"
        "unset APEX_DEV_MCP_FS_PORT APEX_DEV_MCP_JOBS_PORT\n"
        "import_apex_env_file\n"
        "printf '%s|%s' \"${APEX_DEV_MCP_FS_PORT-}\" \"${APEX_DEV_MCP_JOBS_PORT-}\"\n",
        encoding="utf-8",
        newline="\n",
    )
    script_path.chmod(0o755)
    script_path_bash = _bash_path(script_path)

    with _hide_repo_env_files(tmp_path, hide_template=True):
        completed = _run_bash(f"bash {shlex.quote(script_path_bash)}", env=env)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "|"


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell helper tests")
def test_common_powershell_import_env_file_imports_values_from_explicit_crlf_file(tmp_path: Path) -> None:
    env_file = tmp_path / "powershell.env"
    env_file.write_text(
        "# ignored comment\r\n\r\nAPEX_TEST_ALPHA = powershell-alpha\r\nAPEX_TEST_BETA=powershell-beta\r\n",
        encoding="utf-8",
        newline="",
    )

    env = os.environ.copy()
    env.pop("APEX_TEST_ALPHA", None)
    env.pop("APEX_TEST_BETA", None)

    completed = _run_powershell(
        f"Remove-Item Env:APEX_TEST_ALPHA -ErrorAction SilentlyContinue; Remove-Item Env:APEX_TEST_BETA -ErrorAction SilentlyContinue; Import-ApexEnvFile -EnvFile '{env_file}'; Write-Output \"$env:APEX_TEST_ALPHA|$env:APEX_TEST_BETA\"",
        env=env,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "powershell-alpha|powershell-beta"


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell helper tests")
def test_common_powershell_import_env_file_falls_back_to_repo_template_when_env_dev_is_missing(tmp_path: Path) -> None:
    env = os.environ.copy()
    env.pop("APEX_DEV_MCP_FS_PORT", None)
    env.pop("APEX_DEV_MCP_JOBS_PORT", None)
    expected_fs_port = _template_value("APEX_DEV_MCP_FS_PORT")
    expected_jobs_port = _template_value("APEX_DEV_MCP_JOBS_PORT")

    with _hide_repo_env_files(tmp_path):
        completed = _run_powershell(
            "Remove-Item Env:APEX_DEV_MCP_FS_PORT -ErrorAction SilentlyContinue; Remove-Item Env:APEX_DEV_MCP_JOBS_PORT -ErrorAction SilentlyContinue; Import-ApexEnvFile; Write-Output \"$env:APEX_DEV_MCP_FS_PORT|$env:APEX_DEV_MCP_JOBS_PORT\"",
            env=env,
        )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == f"{expected_fs_port}|{expected_jobs_port}"


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell helper tests")
def test_common_powershell_import_env_file_noops_when_repo_env_and_template_are_missing(tmp_path: Path) -> None:
    env = os.environ.copy()
    env.pop("APEX_DEV_MCP_FS_PORT", None)
    env.pop("APEX_DEV_MCP_JOBS_PORT", None)

    with _hide_repo_env_files(tmp_path, hide_template=True):
        completed = _run_powershell(
            "Remove-Item Env:APEX_DEV_MCP_FS_PORT -ErrorAction SilentlyContinue; Remove-Item Env:APEX_DEV_MCP_JOBS_PORT -ErrorAction SilentlyContinue; Import-ApexEnvFile; Write-Output \"$env:APEX_DEV_MCP_FS_PORT|$env:APEX_DEV_MCP_JOBS_PORT\"",
            env=env,
        )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "|"