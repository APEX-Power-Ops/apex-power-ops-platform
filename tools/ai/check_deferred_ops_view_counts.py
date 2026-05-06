from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def import_env_file() -> None:
    root = repo_root()
    env_file = root / ".env.dev"
    if not env_file.exists():
        env_file = root / ".env.dev.template"
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip())


def get_db_connection_string() -> str:
    import_env_file()

    if os.getenv("SEAM_DATABASE_URL"):
        return os.environ["SEAM_DATABASE_URL"]

    if os.getenv("APEX_DB_CONNECTION_STRING"):
        return os.environ["APEX_DB_CONNECTION_STRING"]

    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    user = os.getenv("APEX_DEV_POSTGRES_USER")
    password = os.getenv("APEX_DEV_POSTGRES_PASSWORD")
    database = os.getenv("APEX_DEV_POSTGRES_DB")
    port = os.getenv("APEX_DEV_POSTGRES_PORT")
    if user and password and database and port:
        return f"postgresql://{user}:{password}@127.0.0.1:{port}/{database}"

    raise RuntimeError("No database connection string is available for deferred ops view checks.")


def looks_local_connection(dsn: str) -> bool:
    lowered = dsn.lower()
    return "127.0.0.1" in lowered or "localhost" in lowered or "apex_dev" in lowered


def resolve_db_connection_string(args: argparse.Namespace) -> tuple[str, str]:
    import_env_file()

    if args.dsn:
        return args.dsn, "argument:dsn"

    if args.dsn_env:
        value = str(os.getenv(args.dsn_env) or "").strip()
        if value:
            return value, f"env:{args.dsn_env}"
        raise RuntimeError(f"{args.dsn_env} is not set; cannot run deferred ops view checks.")

    if os.getenv("SEAM_DATABASE_URL"):
        return os.environ["SEAM_DATABASE_URL"], "env:SEAM_DATABASE_URL"

    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"], "env:DATABASE_URL"

    if os.getenv("APEX_DB_CONNECTION_STRING"):
        return os.environ["APEX_DB_CONNECTION_STRING"], "env:APEX_DB_CONNECTION_STRING"

    return get_db_connection_string(), "env-file:apex-dev-fallback"


def write_output(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether deferred Operations Visibility views have live rows.")
    parser.add_argument("--packet-id", default="2026-05-06-olares-dev-residency-056")
    parser.add_argument("--dsn")
    parser.add_argument("--dsn-env")
    parser.add_argument("--output")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else None
    summary: dict[str, Any] = {
        "packet_id": args.packet_id,
        "repo_root": str(repo_root()),
        "checks": {},
    }

    try:
        dsn, dsn_source = resolve_db_connection_string(args)
        summary["checks"]["db_connection"] = {
            "status": "pass",
            "source": dsn_source,
            "looks_local": looks_local_connection(dsn),
        }

        engine = create_engine(dsn)
        try:
            with engine.connect() as connection:
                rows = connection.execute(
                    text(
                        """
                        select 'v_resource_allocation' as view_name, count(*) as row_count
                        from public.v_resource_allocation
                        union all
                        select 'v_equipment_needs' as view_name, count(*) as row_count
                        from public.v_equipment_needs
                        order by view_name
                        """
                    )
                ).mappings().all()
        except ProgrammingError as error:
            if "relation \"public.v_resource_allocation\" does not exist" not in str(error):
                raise
            if not looks_local_connection(dsn):
                raise
            summary["checks"]["deferred_view_counts"] = {
                "status": "unavailable",
                "reason": "Local development database does not expose the authoritative deferred operations views.",
            }
            summary["result"] = "UNAVAILABLE"
            summary["decision"] = (
                "Authoritative deferred view counts require a live DSN such as SEAM_DATABASE_URL; "
                "the local development database is not sufficient for this hold check."
            )
            write_output(output_path, summary)
            print(json.dumps(summary, indent=2))
            return 0

        counts = {row["view_name"]: int(row["row_count"]) for row in rows}
        reopen = [name for name, row_count in counts.items() if row_count > 0]

        summary["checks"]["deferred_view_counts"] = {
            "status": "pass",
            "counts": counts,
        }
        summary["result"] = "REOPEN" if reopen else "HOLD"
        summary["reopen_candidates"] = reopen
        summary["decision"] = (
            "One or more deferred Operations Visibility seams now have live rows."
            if reopen
            else "Deferred Operations Visibility seams remain empty and should stay on hold."
        )
        write_output(output_path, summary)
        print(json.dumps(summary, indent=2))
        return 0
    except Exception as error:  # noqa: BLE001
        summary["result"] = "FAIL"
        summary["error"] = str(error)
        write_output(output_path, summary)
        print(json.dumps(summary, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())