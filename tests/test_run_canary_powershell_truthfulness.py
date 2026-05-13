from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_DEV_FILE = REPO_ROOT / ".env.dev"


def _read_json_lines(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    assert all(line.strip() for line in lines)
    return [json.loads(line) for line in lines]


def _powershell_literal(value: str) -> str:
    return value.replace("'", "''")


def _normalize_start_process_entry(entry: dict[str, object]) -> dict[str, object]:
    argument_list = entry["argument_list"]
    assert isinstance(argument_list, list)
    assert len(argument_list) == 3
    assert argument_list[:2] == ["-NoProfile", "-Command"]

    command = str(argument_list[2])
    parts = command.split("; ")
    assert len(parts) >= 2

    env_assignments: dict[str, str] = {}
    for part in parts[:-2]:
        match = re.fullmatch(r"\$env:([^ ]+) = '([^']*)'", part)
        assert match is not None
        env_assignments[match.group(1)] = match.group(2)
    assert len(env_assignments) == len(parts[:-2])

    location_match = re.fullmatch(r"Set-Location '([^']*)'", parts[-2])
    assert location_match is not None

    invoke_match = re.fullmatch(r"& '([^']*)'(?: (.*))?", parts[-1])
    assert invoke_match is not None
    invoke_args_text = str(invoke_match.group(2) or "")
    invoke_args = re.findall(r"'([^']*)'", invoke_args_text)
    assert invoke_args_text == " ".join(f"'{argument}'" for argument in invoke_args)

    return {
        "file_path": entry["file_path"],
        "env": env_assignments,
        "cwd": location_match.group(1),
        "invoke_file": invoke_match.group(1),
        "invoke_args": invoke_args,
    }


def _expected_start_process_entry(
    *,
    env: dict[str, str],
    cwd: str,
    invoke_file: str,
    invoke_args: list[str],
) -> dict[str, object]:
    return {
        "file_path": "pwsh",
        "env": env,
        "cwd": cwd,
        "invoke_file": invoke_file,
        "invoke_args": invoke_args,
    }


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_run_canary_powershell_uses_fallback_ports_for_waits_and_child_envs(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    python_log = tmp_path / "python-log.jsonl"
    start_process_log = tmp_path / "start-process-log.jsonl"
    webrequest_log = tmp_path / "webrequest-log.jsonl"

    fake_python = bin_dir / "fake-python.ps1"
    fake_python.write_text(
        "$payload = [ordered]@{ argv = $args; env = [ordered]@{ PORT = $env:PORT; PYTHONPATH = $env:PYTHONPATH; FORMS_ENGINE_TEMPLATES_PATH = $env:FORMS_ENGINE_TEMPLATES_PATH; FORMS_ENGINE_ARTIFACTS_PATH = $env:FORMS_ENGINE_ARTIFACTS_PATH; P6_INGEST_ARTIFACTS_PATH = $env:P6_INGEST_ARTIFACTS_PATH; APEX_P6_FIXTURE_PATH = $env:APEX_P6_FIXTURE_PATH; OIDC_ISSUER_URL = $env:OIDC_ISSUER_URL; OIDC_CLIENT_ID = $env:OIDC_CLIENT_ID } }\n"
        "Add-Content -Encoding utf8 -Path $env:FAKE_PYTHON_LOG -Value ($payload | ConvertTo-Json -Compress)\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    for variable in (
        "APEX_DEV_FORMS_ENGINE_PORT",
        "APEX_DEV_P6_INGEST_PORT",
        "APEX_DEV_MCP_FS_PORT",
        "APEX_DEV_MCP_DB_PORT",
        "APEX_DEV_MCP_JOBS_PORT",
        "APEX_DEV_MCP_P6_PORT",
        "APEX_DEV_MCP_FORMS_PORT",
        "APEX_FORMS_RUNTIME_URL",
        "APEX_P6_RUNTIME_URL",
    ):
        env.pop(variable, None)

    command = " ; ".join(
        [
            f"$env:APEX_PLATFORM_PYTHON = '{_powershell_literal(str(fake_python))}'",
            f"$env:FAKE_PYTHON_LOG = '{_powershell_literal(str(python_log))}'",
            f"$env:FAKE_START_PROCESS_LOG = '{_powershell_literal(str(start_process_log))}'",
            f"$env:FAKE_WEBREQUEST_LOG = '{_powershell_literal(str(webrequest_log))}'",
            "Remove-Item Env:APEX_DEV_FORMS_ENGINE_PORT -ErrorAction SilentlyContinue",
            "Remove-Item Env:APEX_DEV_P6_INGEST_PORT -ErrorAction SilentlyContinue",
            "Remove-Item Env:APEX_DEV_MCP_FS_PORT -ErrorAction SilentlyContinue",
            "Remove-Item Env:APEX_DEV_MCP_DB_PORT -ErrorAction SilentlyContinue",
            "Remove-Item Env:APEX_DEV_MCP_JOBS_PORT -ErrorAction SilentlyContinue",
            "Remove-Item Env:APEX_DEV_MCP_P6_PORT -ErrorAction SilentlyContinue",
            "Remove-Item Env:APEX_DEV_MCP_FORMS_PORT -ErrorAction SilentlyContinue",
            "Remove-Item Env:APEX_FORMS_RUNTIME_URL -ErrorAction SilentlyContinue",
            "Remove-Item Env:APEX_P6_RUNTIME_URL -ErrorAction SilentlyContinue",
            "function Invoke-WebRequest { param([string]$Uri, [switch]$UseBasicParsing) $payload = [ordered]@{ url = $Uri }; Add-Content -Encoding utf8 -Path $env:FAKE_WEBREQUEST_LOG -Value ($payload | ConvertTo-Json -Compress); return [pscustomobject]@{ StatusCode = 200 } }",
            "function Start-Process { param([string]$FilePath, [object[]]$ArgumentList, [switch]$PassThru) $payload = [ordered]@{ file_path = $FilePath; argument_list = @($ArgumentList) }; Add-Content -Encoding utf8 -Path $env:FAKE_START_PROCESS_LOG -Value ($payload | ConvertTo-Json -Compress -Depth 5); return [pscustomobject]@{ Id = 1; HasExited = $true } }",
            "& 'tools/run-canary.ps1'",
        ]
    )

    original_env_dev = ENV_DEV_FILE.read_text(encoding="utf-8") if ENV_DEV_FILE.exists() else None
    if ENV_DEV_FILE.exists():
        ENV_DEV_FILE.unlink()

    try:
        completed = subprocess.run(
            ["pwsh", "-NoProfile", "-Command", command],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        if original_env_dev is None:
            if ENV_DEV_FILE.exists():
                ENV_DEV_FILE.unlink()
        else:
            ENV_DEV_FILE.write_text(original_env_dev, encoding="utf-8")

    assert completed.returncode == 0, completed.stderr

    webrequest_urls = [entry["url"] for entry in _read_json_lines(webrequest_log)]
    assert webrequest_urls == [
        "http://127.0.0.1:8080/health",
        "http://127.0.0.1:8081/health",
        "http://127.0.0.1:8810/mcp",
        "http://127.0.0.1:8811/mcp",
        "http://127.0.0.1:8812/mcp",
        "http://127.0.0.1:8713/mcp",
        "http://127.0.0.1:8714/mcp",
    ]

    start_process_calls = _read_json_lines(start_process_log)
    normalized_calls = [_normalize_start_process_entry(entry) for entry in start_process_calls]
    normalized_by_invoke = {tuple(str(value) for value in entry["invoke_args"]): entry for entry in normalized_calls}
    assert len(normalized_calls) == 7
    assert set(normalized_by_invoke) == {
        ("-m", "apex_forms_engine.runtime"),
        ("services/mcp/apex-db/build/http.js",),
        ("services/mcp/apex-fs/build/http.js",),
        ("services/mcp/apex-jobs/build/http.js",),
        ("services/mcp/apex-forms/build/http.js",),
        ("services/mcp/apex-p6/build/http.js",),
        ("-m", "apex_p6_ingest.runtime"),
    }

    repo_root = str(REPO_ROOT)
    assert normalized_by_invoke[("-m", "apex_forms_engine.runtime")] == _expected_start_process_entry(
        env={
            "PORT": "8080",
            "PYTHONPATH": "packages/forms-engine/src",
            "FORMS_ENGINE_TEMPLATES_PATH": str(REPO_ROOT / ".tmp" / "forms-engine" / "templates"),
            "FORMS_ENGINE_ARTIFACTS_PATH": str(REPO_ROOT / ".tmp" / "forms-engine" / "artifacts"),
            "OIDC_ISSUER_URL": "https://auth.olares.local",
            "OIDC_CLIENT_ID": "forms-engine-placeholder",
        },
        cwd=repo_root,
        invoke_file=str(fake_python),
        invoke_args=["-m", "apex_forms_engine.runtime"],
    )
    assert normalized_by_invoke[("services/mcp/apex-db/build/http.js",)] == _expected_start_process_entry(
        env={
            "APEX_MCP_HTTP_PORT": "8811",
        },
        cwd=repo_root,
        invoke_file="node",
        invoke_args=["services/mcp/apex-db/build/http.js"],
    )
    assert normalized_by_invoke[("services/mcp/apex-fs/build/http.js",)] == _expected_start_process_entry(
        env={
            "APEX_MCP_HTTP_PORT": "8810",
            "APEX_MCP_WORKSPACE_ROOT": repo_root,
            "APEX_MCP_DATA_ROOT": str(REPO_ROOT / ".apex-data"),
        },
        cwd=repo_root,
        invoke_file="node",
        invoke_args=["services/mcp/apex-fs/build/http.js"],
    )
    assert normalized_by_invoke[("services/mcp/apex-jobs/build/http.js",)] == _expected_start_process_entry(
        env={
            "APEX_MCP_HTTP_PORT": "8812",
            "APEX_JOBS_LEDGER_PATH": str(REPO_ROOT / ".apex-data" / "apex-jobs-ledger.json"),
        },
        cwd=repo_root,
        invoke_file="node",
        invoke_args=["services/mcp/apex-jobs/build/http.js"],
    )
    assert normalized_by_invoke[("services/mcp/apex-forms/build/http.js",)] == _expected_start_process_entry(
        env={
            "APEX_MCP_HTTP_PORT": "8714",
            "APEX_FORMS_RUNTIME_URL": "http://127.0.0.1:8080",
        },
        cwd=repo_root,
        invoke_file="node",
        invoke_args=["services/mcp/apex-forms/build/http.js"],
    )
    assert normalized_by_invoke[("services/mcp/apex-p6/build/http.js",)] == _expected_start_process_entry(
        env={
            "APEX_MCP_HTTP_PORT": "8713",
            "APEX_P6_RUNTIME_URL": "http://127.0.0.1:8081",
        },
        cwd=repo_root,
        invoke_file="node",
        invoke_args=["services/mcp/apex-p6/build/http.js"],
    )
    assert normalized_by_invoke[("-m", "apex_p6_ingest.runtime")] == _expected_start_process_entry(
        env={
            "PORT": "8081",
            "PYTHONPATH": "packages/p6-ingest/src",
            "P6_INGEST_ARTIFACTS_PATH": str(REPO_ROOT / ".tmp" / "p6-ingest" / "artifacts"),
            "APEX_P6_FIXTURE_PATH": str(REPO_ROOT / "apps" / "mutation-seam" / "app" / "schedule" / "fixtures" / "stack_data_center_baseline_sanitized.xer"),
            "OIDC_ISSUER_URL": "https://auth.olares.local",
            "OIDC_CLIENT_ID": "p6-ingest-placeholder",
        },
        cwd=repo_root,
        invoke_file=str(fake_python),
        invoke_args=["-m", "apex_p6_ingest.runtime"],
    )

    python_calls = _read_json_lines(python_log)
    assert python_calls == [
        {
            "argv": ["tools/canary/run_canary.py"],
            "env": {
                "PORT": None,
                "PYTHONPATH": None,
                "FORMS_ENGINE_TEMPLATES_PATH": None,
                "FORMS_ENGINE_ARTIFACTS_PATH": None,
                "P6_INGEST_ARTIFACTS_PATH": None,
                "APEX_P6_FIXTURE_PATH": None,
                "OIDC_ISSUER_URL": None,
                "OIDC_CLIENT_ID": None,
            },
        }
    ]
