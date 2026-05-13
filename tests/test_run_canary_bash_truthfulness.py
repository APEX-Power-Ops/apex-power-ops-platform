from __future__ import annotations

import json
import os
import shlex
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


def _bash_path(path: Path) -> str:
    resolved = path.resolve().as_posix()
    if len(resolved) >= 3 and resolved[1:3] == ":/":
        return f"/mnt/{resolved[0].lower()}/{resolved[3:]}"
    return resolved


def _expected_node_call(target: str, *, env: dict[str, object]) -> dict[str, object]:
    return {
        "argv": [target],
        "env": {
            "APEX_MCP_HTTP_PORT": env.get("APEX_MCP_HTTP_PORT"),
            "APEX_MCP_WORKSPACE_ROOT": env.get("APEX_MCP_WORKSPACE_ROOT"),
            "APEX_MCP_DATA_ROOT": env.get("APEX_MCP_DATA_ROOT"),
            "APEX_JOBS_LEDGER_PATH": env.get("APEX_JOBS_LEDGER_PATH"),
            "APEX_FORMS_RUNTIME_URL": env.get("APEX_FORMS_RUNTIME_URL"),
            "APEX_P6_RUNTIME_URL": env.get("APEX_P6_RUNTIME_URL"),
        },
    }


def _expected_python_call(argv: tuple[str, ...], *, env: dict[str, object]) -> dict[str, object]:
    return {
        "argv": list(argv),
        "env": {
            "PORT": env.get("PORT"),
            "PYTHONPATH": env.get("PYTHONPATH"),
            "FORMS_ENGINE_TEMPLATES_PATH": env.get("FORMS_ENGINE_TEMPLATES_PATH"),
            "FORMS_ENGINE_ARTIFACTS_PATH": env.get("FORMS_ENGINE_ARTIFACTS_PATH"),
            "P6_INGEST_ARTIFACTS_PATH": env.get("P6_INGEST_ARTIFACTS_PATH"),
            "APEX_P6_FIXTURE_PATH": env.get("APEX_P6_FIXTURE_PATH"),
            "OIDC_ISSUER_URL": env.get("OIDC_ISSUER_URL"),
            "OIDC_CLIENT_ID": env.get("OIDC_CLIENT_ID"),
        },
    }


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_run_canary_bash_uses_fallback_ports_for_waits_and_child_envs(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    python_log = tmp_path / "python-log.jsonl"
    node_log = tmp_path / "node-log.jsonl"
    curl_log = tmp_path / "curl-log.jsonl"
    python_log_bash = _bash_path(python_log)
    node_log_bash = _bash_path(node_log)
    curl_log_bash = _bash_path(curl_log)

    fake_python = bin_dir / "fake-python"
    fake_python.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"python_log={json.dumps(python_log_bash)}\n"
        "python3 - <<'PY' \"$python_log\" \"$@\"\n"
        "import json\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)\n"
        "payload = {\n"
        "    'argv': sys.argv[2:],\n"
        "    'env': {\n"
        "        'PORT': os.getenv('PORT'),\n"
        "        'PYTHONPATH': os.getenv('PYTHONPATH'),\n"
        "        'FORMS_ENGINE_TEMPLATES_PATH': os.getenv('FORMS_ENGINE_TEMPLATES_PATH'),\n"
        "        'FORMS_ENGINE_ARTIFACTS_PATH': os.getenv('FORMS_ENGINE_ARTIFACTS_PATH'),\n"
        "        'P6_INGEST_ARTIFACTS_PATH': os.getenv('P6_INGEST_ARTIFACTS_PATH'),\n"
        "        'APEX_P6_FIXTURE_PATH': os.getenv('APEX_P6_FIXTURE_PATH'),\n"
        "        'OIDC_ISSUER_URL': os.getenv('OIDC_ISSUER_URL'),\n"
        "        'OIDC_CLIENT_ID': os.getenv('OIDC_CLIENT_ID'),\n"
        "    },\n"
        "}\n"
        "with Path(sys.argv[1]).open('a', encoding='utf-8') as handle:\n"
        "    handle.write(json.dumps(payload) + '\\n')\n"
        "PY\n",
        encoding="utf-8",
        newline="\n",
    )
    fake_python.chmod(0o755)

    fake_node = bin_dir / "node"
    fake_node.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"node_log={json.dumps(node_log_bash)}\n"
        "python3 - <<'PY' \"$node_log\" \"$@\"\n"
        "import json\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)\n"
        "payload = {\n"
        "    'argv': sys.argv[2:],\n"
        "    'env': {\n"
        "        'APEX_MCP_HTTP_PORT': os.getenv('APEX_MCP_HTTP_PORT'),\n"
        "        'APEX_MCP_WORKSPACE_ROOT': os.getenv('APEX_MCP_WORKSPACE_ROOT'),\n"
        "        'APEX_MCP_DATA_ROOT': os.getenv('APEX_MCP_DATA_ROOT'),\n"
        "        'APEX_JOBS_LEDGER_PATH': os.getenv('APEX_JOBS_LEDGER_PATH'),\n"
        "        'APEX_FORMS_RUNTIME_URL': os.getenv('APEX_FORMS_RUNTIME_URL'),\n"
        "        'APEX_P6_RUNTIME_URL': os.getenv('APEX_P6_RUNTIME_URL'),\n"
        "    },\n"
        "}\n"
        "with Path(sys.argv[1]).open('a', encoding='utf-8') as handle:\n"
        "    handle.write(json.dumps(payload) + '\\n')\n"
        "PY\n",
        encoding="utf-8",
        newline="\n",
    )
    fake_node.chmod(0o755)

    fake_curl = bin_dir / "curl"
    fake_curl.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"curl_log={json.dumps(curl_log_bash)}\n"
        "url=\"${*: -1}\"\n"
        "python3 - <<'PY' \"$curl_log\" \"$url\"\n"
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)\n"
        "with Path(sys.argv[1]).open('a', encoding='utf-8') as handle:\n"
        "    handle.write(json.dumps({'url': sys.argv[2]}) + '\\n')\n"
        "PY\n",
        encoding="utf-8",
        newline="\n",
    )
    fake_curl.chmod(0o755)

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

    repo_root_bash = _bash_path(REPO_ROOT)
    bin_dir_bash = _bash_path(bin_dir)
    fake_python_bash = _bash_path(fake_python)
    command = " ; ".join(
        [
            f"cd {shlex.quote(repo_root_bash)}",
            f"export PATH={shlex.quote(bin_dir_bash)}:\"$PATH\"",
            f"export APEX_PLATFORM_PYTHON={shlex.quote(fake_python_bash)}",
            "unset APEX_DEV_FORMS_ENGINE_PORT",
            "unset APEX_DEV_P6_INGEST_PORT",
            "unset APEX_DEV_MCP_FS_PORT",
            "unset APEX_DEV_MCP_DB_PORT",
            "unset APEX_DEV_MCP_JOBS_PORT",
            "unset APEX_DEV_MCP_P6_PORT",
            "unset APEX_DEV_MCP_FORMS_PORT",
            "unset APEX_FORMS_RUNTIME_URL",
            "unset APEX_P6_RUNTIME_URL",
            "bash tools/run-canary.sh",
        ]
    )

    original_env_dev = ENV_DEV_FILE.read_text(encoding="utf-8") if ENV_DEV_FILE.exists() else None
    if ENV_DEV_FILE.exists():
        ENV_DEV_FILE.unlink()
    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
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

    curl_calls = [entry["url"] for entry in _read_json_lines(curl_log)]
    assert curl_calls == [
        "http://127.0.0.1:8080/health",
        "http://127.0.0.1:8081/health",
        "http://127.0.0.1:8810/mcp",
        "http://127.0.0.1:8811/mcp",
        "http://127.0.0.1:8812/mcp",
        "http://127.0.0.1:8713/mcp",
        "http://127.0.0.1:8714/mcp",
    ]

    node_calls = _read_json_lines(node_log)
    node_by_target = {str(entry["argv"][0]): entry for entry in node_calls}
    assert set(node_by_target) == {
        "services/mcp/apex-fs/build/http.js",
        "services/mcp/apex-db/build/http.js",
        "services/mcp/apex-jobs/build/http.js",
        "services/mcp/apex-p6/build/http.js",
        "services/mcp/apex-forms/build/http.js",
    }
    assert node_by_target["services/mcp/apex-fs/build/http.js"] == _expected_node_call(
        "services/mcp/apex-fs/build/http.js",
        env={
            "APEX_MCP_HTTP_PORT": "8810",
            "APEX_MCP_WORKSPACE_ROOT": repo_root_bash,
            "APEX_MCP_DATA_ROOT": f"{repo_root_bash}/.apex-data",
        },
    )
    assert node_by_target["services/mcp/apex-db/build/http.js"] == _expected_node_call(
        "services/mcp/apex-db/build/http.js",
        env={
            "APEX_MCP_HTTP_PORT": "8811",
        },
    )
    assert node_by_target["services/mcp/apex-jobs/build/http.js"] == _expected_node_call(
        "services/mcp/apex-jobs/build/http.js",
        env={
            "APEX_MCP_HTTP_PORT": "8812",
            "APEX_JOBS_LEDGER_PATH": f"{repo_root_bash}/.apex-data/apex-jobs-ledger.json",
        },
    )
    assert node_by_target["services/mcp/apex-p6/build/http.js"] == _expected_node_call(
        "services/mcp/apex-p6/build/http.js",
        env={
            "APEX_MCP_HTTP_PORT": "8713",
            "APEX_P6_RUNTIME_URL": "http://127.0.0.1:8081",
        },
    )
    assert node_by_target["services/mcp/apex-forms/build/http.js"] == _expected_node_call(
        "services/mcp/apex-forms/build/http.js",
        env={
            "APEX_MCP_HTTP_PORT": "8714",
            "APEX_FORMS_RUNTIME_URL": "http://127.0.0.1:8080",
        },
    )

    python_calls = _read_json_lines(python_log)
    python_by_invocation = {tuple(entry["argv"]): entry for entry in python_calls}
    assert python_by_invocation[("-m", "apex_forms_engine.runtime")] == _expected_python_call(
        ("-m", "apex_forms_engine.runtime"),
        env={
            "PORT": "8080",
            "PYTHONPATH": "packages/forms-engine/src",
            "FORMS_ENGINE_TEMPLATES_PATH": f"{repo_root_bash}/.tmp/forms-engine/templates",
            "FORMS_ENGINE_ARTIFACTS_PATH": f"{repo_root_bash}/.tmp/forms-engine/artifacts",
            "OIDC_ISSUER_URL": "https://auth.olares.local",
            "OIDC_CLIENT_ID": "forms-engine-placeholder",
        },
    )
    assert python_by_invocation[("-m", "apex_p6_ingest.runtime")] == _expected_python_call(
        ("-m", "apex_p6_ingest.runtime"),
        env={
            "PORT": "8081",
            "PYTHONPATH": "packages/p6-ingest/src",
            "P6_INGEST_ARTIFACTS_PATH": f"{repo_root_bash}/.tmp/p6-ingest/artifacts",
            "APEX_P6_FIXTURE_PATH": f"{repo_root_bash}/apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.xer",
            "OIDC_ISSUER_URL": "https://auth.olares.local",
            "OIDC_CLIENT_ID": "p6-ingest-placeholder",
        },
    )
    assert set(python_by_invocation) == {
        ("-m", "apex_forms_engine.runtime"),
        ("-m", "apex_p6_ingest.runtime"),
        ("tools/canary/run_canary.py",),
    }
