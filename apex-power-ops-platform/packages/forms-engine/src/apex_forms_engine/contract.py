"""Bounded forms-engine runtime contract for Olares canary and MCP proof."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


DEFAULT_TEMPLATES_PATH = Path("/var/lib/forms-engine/templates")
DEFAULT_ARTIFACTS_PATH = Path("/usr/local/lib/python3.11/site-packages/apex_forms_engine/artifacts")


def _resolve_path(env_name: str, default: Path) -> Path:
    raw_path = os.getenv(env_name)
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    return default


def _runtime_port() -> int:
    raw_port = os.getenv("APEX_FORMS_RUNTIME_PORT") or os.getenv("PORT") or "8080"
    return int(raw_port)


def get_runtime_status() -> dict[str, Any]:
    templates_path = _resolve_path("FORMS_ENGINE_TEMPLATES_PATH", DEFAULT_TEMPLATES_PATH)
    artifacts_path = _resolve_path("FORMS_ENGINE_ARTIFACTS_PATH", DEFAULT_ARTIFACTS_PATH)

    return {
        "service": "forms-engine",
        "status": "ok",
        "env": os.getenv("APEX_RUN_ENV", "sandbox"),
        "port": _runtime_port(),
        "templatesPath": str(templates_path).replace("\\", "/"),
        "templatesPathExists": templates_path.exists(),
        "artifactsPath": str(artifacts_path).replace("\\", "/"),
        "expectedArtifacts": [],
        "oidc": {
            "issuerUrl": os.getenv("OIDC_ISSUER_URL", "https://auth.olares.local"),
            "clientId": os.getenv("OIDC_CLIENT_ID", "forms-engine-placeholder"),
        },
    }
