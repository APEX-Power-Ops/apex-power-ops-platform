"""
PM Idempotency Expiry Sweep — CLI / cron entrypoint
====================================================
Packet: 2026-04-16-pm-schema-019g

Drives ``IdempotencyCache.sweep_expired()`` on demand against the
durable ``pm.idempotency_keys`` store.  Intended as the scheduled or
on-demand maintenance entrypoint that keeps the idempotency table
bounded between the packet-019f insert-time opportunistic prunes.

Usage:

    python -m scripts.sweep_pm_idempotency

    # or, via the file path:
    python apps/control-plane-api/scripts/sweep_pm_idempotency.py

Environment:
    DATABASE_URL — standard Supabase/Postgres URL used by ``config.py``
                   and the rest of the control-plane API.

Exit code:
    0 — sweep completed (even if 0 rows deleted).
    1 — sweep failed; the traceback is written to stderr.

What it does NOT do:
    * No DDL.  No changes to ``pm.idempotency_keys`` shape.
    * No writes to ``work.wbs_nodes`` or any other PM entity surface.
    * No new PM write endpoint — this is a process-local callable only.
"""

from __future__ import annotations

import logging
import os
import sys

# Prepend the control-plane-api root so `services.*` and `config`
# resolve when the script is invoked directly.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_API_ROOT = os.path.dirname(_THIS_DIR)
if _API_ROOT not in sys.path:
    sys.path.insert(0, _API_ROOT)


logger = logging.getLogger("apex.pm.idempotency.sweep")


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("APEX_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        from config import SessionLocal
        from services.work.idempotency import idempotency_cache
    except Exception as exc:
        logger.error("Import failed: %s", exc, exc_info=True)
        return 1

    # Pin the singleton to the durable backend so the sweep targets
    # pm.idempotency_keys rather than the process-local dict.
    try:
        idempotency_cache.use_durable_backend(SessionLocal)
    except Exception as exc:
        logger.error(
            "Could not bind durable backend: %s", exc, exc_info=True,
        )
        return 1

    try:
        deleted = idempotency_cache.sweep_expired()
    except Exception as exc:
        logger.error(
            "Sweep failed: %s", exc, exc_info=True,
        )
        return 1

    logger.info(
        "PM idempotency sweep complete: %s expired row(s) deleted "
        "from pm.idempotency_keys.",
        deleted,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
