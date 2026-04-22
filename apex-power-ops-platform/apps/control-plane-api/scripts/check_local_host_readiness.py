from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values


REPO_ROOT = Path(__file__).resolve().parents[3]
CONTROL_PLANE_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = CONTROL_PLANE_ROOT / ".env"
ENV_EXAMPLE_PATH = CONTROL_PLANE_ROOT / ".env.example"
CORE_RUNTIME_ENV = [
    "DATABASE_URL",
]
RECOMMENDED_LOCAL_ENV = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_JWKS_URL",
]


def _is_unresolved_value(raw: str | None, example_raw: str | None) -> bool:
    value = (raw or "").strip()
    example_value = (example_raw or "").strip()

    if not value:
        return True
    if "[" in value and "]" in value:
        return True
    if value.lower().startswith("change-me"):
        return True
    if example_value and value == example_value and ("[" in example_value and "]" in example_value):
        return True
    return False


def _collect_missing_values(values: dict[str, str | None], names: list[str]) -> list[str]:
    missing: list[str] = []
    for name in names:
        raw = values.get(name)
        if raw is None or not str(raw).strip():
            missing.append(name)
    return missing


def _collect_unresolved_values(
    values: dict[str, str | None],
    example_values: dict[str, str | None],
    names: list[str],
) -> list[str]:
    unresolved: list[str] = []
    for name in names:
        if _is_unresolved_value(values.get(name), example_values.get(name)):
            unresolved.append(name)
    return unresolved


def _run_import_probe() -> tuple[int, str]:
    python_executable = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    command = [
        str(python_executable),
        "-c",
        "import sys; sys.path.insert(0, r'apps/control-plane-api'); import main; print('IMPORT_OK')",
    ]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (completed.stdout or completed.stderr).strip()
    return completed.returncode, output


def main() -> int:
    print("LOCAL_HOST_READINESS")
    print(f"ENV_PATH {ENV_PATH}")
    print(f"ENV_EXISTS {'yes' if ENV_PATH.exists() else 'no'}")

    env_values = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    env_example_values = dotenv_values(ENV_EXAMPLE_PATH) if ENV_EXAMPLE_PATH.exists() else {}
    missing_core = _collect_missing_values(env_values, CORE_RUNTIME_ENV)
    missing_recommended = _collect_missing_values(env_values, RECOMMENDED_LOCAL_ENV)
    unresolved_core = _collect_unresolved_values(env_values, env_example_values, CORE_RUNTIME_ENV)
    unresolved_recommended = _collect_unresolved_values(env_values, env_example_values, RECOMMENDED_LOCAL_ENV)

    print(f"MISSING_CORE_RUNTIME_ENV {json.dumps(missing_core)}")
    print(f"MISSING_RECOMMENDED_LOCAL_ENV {json.dumps(missing_recommended)}")
    print(f"UNRESOLVED_CORE_RUNTIME_ENV {json.dumps(unresolved_core)}")
    print(f"UNRESOLVED_RECOMMENDED_LOCAL_ENV {json.dumps(unresolved_recommended)}")

    return_code, output = _run_import_probe()
    if return_code == 0:
        print("IMPORT_PROBE_STATUS ok")
    else:
        print("IMPORT_PROBE_STATUS fail")
    if output:
        print("IMPORT_PROBE_OUTPUT")
        print(output)

    if return_code == 0 and not unresolved_core:
        print("DECISION host-ready")
        print("RESULT PASS")
        return 0

    print("DECISION host-readiness-blocked")
    print("RESULT FAIL")
    if not ENV_PATH.exists():
        print("- apps/control-plane-api/.env does not exist on the current workstation")
    if missing_core:
        print(f"- missing core runtime env values: {', '.join(missing_core)}")
    if missing_recommended:
        print(f"- missing recommended local auth/runtime env values: {', '.join(missing_recommended)}")
    unresolved_core_without_missing = [name for name in unresolved_core if name not in missing_core]
    unresolved_recommended_without_missing = [
        name for name in unresolved_recommended if name not in missing_recommended
    ]
    if unresolved_core_without_missing:
        print(
            "- unresolved core runtime env values still match template placeholders: "
            + ", ".join(unresolved_core_without_missing)
        )
    if unresolved_recommended_without_missing:
        print(
            "- unresolved recommended local auth/runtime env values still match template placeholders: "
            + ", ".join(unresolved_recommended_without_missing)
        )
    if return_code != 0:
        print("- control-plane import probe failed before local host validation could begin")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())