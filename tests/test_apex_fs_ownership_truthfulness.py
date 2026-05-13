from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
README_PREVIEW = README_PATH.read_bytes()[:120].decode("utf-8")


class _FakeFsHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        method = payload.get("method")

        if method == "initialize":
            if getattr(self.server, "initialize_error", None):
                result = {
                    "isError": True,
                    "content": [{"text": self.server.initialize_error}],
                }
            else:
                result = {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "serverInfo": {"name": "fake-apex-fs", "version": "0.1.0"},
                }
        elif method == "tools/call":
            tool_name = payload.get("params", {}).get("name")
            if tool_name == "list_roots":
                if getattr(self.server, "list_roots_error", None):
                    result = {
                        "isError": True,
                        "content": [{"text": self.server.list_roots_error}],
                    }
                else:
                    result = {
                        "structuredContent": {
                            "workspace": self.server.workspace_root,
                        }
                    }
            elif tool_name == "read_text_file":
                if getattr(self.server, "read_text_file_error", None):
                    result = {
                        "isError": True,
                        "content": [{"text": self.server.read_text_file_error}],
                    }
                else:
                    result = {
                        "structuredContent": {
                            "content": self.server.readme_preview,
                        }
                    }
            else:
                result = {
                    "isError": True,
                    "content": [{"text": f"unexpected tool {tool_name}"}],
                }
        else:
            result = {
                "isError": True,
                "content": [{"text": f"unexpected method {method}"}],
            }

        body = json.dumps({"jsonrpc": "2.0", "id": payload.get("id"), "result": result}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


@pytest.fixture
def fake_fs_server() -> threading.Thread:
    servers: list[ThreadingHTTPServer] = []

    def _start(
        workspace_root: str,
        readme_preview: str,
        *,
        initialize_error: str | None = None,
        list_roots_error: str | None = None,
        read_text_file_error: str | None = None,
    ) -> str:
        server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeFsHandler)
        server.workspace_root = workspace_root
        server.readme_preview = readme_preview
        server.initialize_error = initialize_error
        server.list_roots_error = list_roots_error
        server.read_text_file_error = read_text_file_error
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_address[1]}/mcp"

    yield _start

    for server in servers:
        server.shutdown()
        server.server_close()


def _run_helper(fs_url: str, *, include_readme_path: bool = True) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "tools/ai/check_apex_fs_ownership.py",
        "--fs-url",
        fs_url,
        "--expected-workspace-root",
        str(REPO_ROOT),
    ]
    if include_readme_path:
        command.extend(["--expected-readme-path", str(README_PATH)])

    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_helper_with_readme_path(fs_url: str, readme_path: Path) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "tools/ai/check_apex_fs_ownership.py",
        "--fs-url",
        fs_url,
        "--expected-workspace-root",
        str(REPO_ROOT),
        "--expected-readme-path",
        str(readme_path),
    ]

    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _expected_owned_payload(
    workspace_root: str,
    *,
    include_readme_preview: bool = True,
    readme_preview: str = README_PREVIEW,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": "owned",
        "workspace_root": workspace_root,
        "expected_workspace_root": str(REPO_ROOT),
    }
    if include_readme_preview:
        payload["readme_preview"] = readme_preview
        payload["expected_readme_preview"] = README_PREVIEW
    return payload


def _expected_refusal_payload(
    workspace_root: str,
    *,
    reason: str,
    readme_preview: str,
) -> dict[str, object]:
    return {
        "status": "adoption-refused",
        "workspace_root": workspace_root,
        "expected_workspace_root": str(REPO_ROOT),
        "readme_preview": readme_preview,
        "expected_readme_preview": README_PREVIEW,
        "reason": reason,
    }


def _expected_probe_failure_payload(error: str) -> dict[str, object]:
    return {
        "status": "adoption-refused",
        "reason": "fs-ownership-probe-failed",
        "expected_workspace_root": str(REPO_ROOT),
        "detail": error,
    }


def test_check_apex_fs_ownership_reports_owned_for_matching_workspace_and_readme(fake_fs_server) -> None:
    fs_url = fake_fs_server(str(REPO_ROOT), README_PREVIEW)

    result = _run_helper(fs_url)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_owned_payload(str(REPO_ROOT))


def test_check_apex_fs_ownership_reports_owned_without_readme_probe_when_path_is_omitted(fake_fs_server) -> None:
    fs_url = fake_fs_server(
        str(REPO_ROOT),
        README_PREVIEW,
        read_text_file_error="read_text_file should not be called when readme proof is omitted",
    )

    result = _run_helper(fs_url, include_readme_path=False)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_owned_payload(str(REPO_ROOT), include_readme_preview=False)


def test_check_apex_fs_ownership_accepts_equivalent_noncanonical_workspace_root(fake_fs_server) -> None:
    fs_url = fake_fs_server(str(REPO_ROOT / "infra" / ".."), README_PREVIEW)

    result = _run_helper(fs_url)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_owned_payload(str(REPO_ROOT / "infra" / ".."))


def test_check_apex_fs_ownership_refuses_workspace_root_mismatch(fake_fs_server) -> None:
    fs_url = fake_fs_server(str(REPO_ROOT.parent / "foreign-root"), README_PREVIEW)

    result = _run_helper(fs_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_refusal_payload(
        str(REPO_ROOT.parent / "foreign-root"),
        reason="workspace-root-mismatch",
        readme_preview=README_PREVIEW,
    )


def test_check_apex_fs_ownership_refuses_readme_preview_mismatch(fake_fs_server) -> None:
    fs_url = fake_fs_server(str(REPO_ROOT), "not-the-current-readme-preview")

    result = _run_helper(fs_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_refusal_payload(
        str(REPO_ROOT),
        reason="readme-preview-mismatch",
        readme_preview="not-the-current-readme-preview",
    )


def test_check_apex_fs_ownership_reports_probe_failure_when_list_roots_errors(fake_fs_server) -> None:
    fs_url = fake_fs_server(
        str(REPO_ROOT),
        README_PREVIEW,
        list_roots_error="temporary list_roots failure",
    )

    result = _run_helper(fs_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_probe_failure_payload("temporary list_roots failure")


def test_check_apex_fs_ownership_reports_probe_failure_when_initialize_errors(fake_fs_server) -> None:
    fs_url = fake_fs_server(
        str(REPO_ROOT),
        README_PREVIEW,
        initialize_error="temporary initialize failure",
    )

    result = _run_helper(fs_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_probe_failure_payload("temporary initialize failure")


def test_check_apex_fs_ownership_reports_probe_failure_when_readme_probe_errors(fake_fs_server) -> None:
    fs_url = fake_fs_server(
        str(REPO_ROOT),
        README_PREVIEW,
        read_text_file_error="temporary read_text_file failure",
    )

    result = _run_helper(fs_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_probe_failure_payload("temporary read_text_file failure")


def test_check_apex_fs_ownership_reports_probe_failure_when_expected_readme_path_is_missing(
    fake_fs_server, tmp_path: Path
) -> None:
    fs_url = fake_fs_server(str(REPO_ROOT), README_PREVIEW)
    missing_readme_path = tmp_path / "missing-README.md"

    result = _run_helper_with_readme_path(fs_url, missing_readme_path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    payload_without_detail = {key: value for key, value in payload.items() if key != "detail"}
    expected_without_detail = {
        key: value for key, value in _expected_probe_failure_payload("<os-shaped-missing-readme-detail>").items() if key != "detail"
    }
    assert payload_without_detail == expected_without_detail
    detail = str(payload.get("detail") or "").lower()
    normalized_detail = detail.replace("\\\\", "\\")
    assert str(missing_readme_path).lower() in normalized_detail
    assert detail.startswith("[errno 2]")
    assert "no such file or directory" in detail