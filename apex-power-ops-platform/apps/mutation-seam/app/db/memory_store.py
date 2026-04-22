"""
Store shim — delegates to the Supabase-backed store.
Packet UI-001e migrated persistence from in-memory dicts to Postgres.

All existing imports of `from app.db.memory_store import store` continue
to work unchanged; the singleton `store` is now a SupabaseStore instance
backed by the `seam` schema in Postgres.

To fall back to the original in-memory store, set env var:
    SEAM_STORE_BACKEND=memory
"""
import os

if os.getenv("SEAM_STORE_BACKEND") == "memory":
    # Fallback: use the original in-memory store for offline/disconnected dev
    from app.db.memory_store_original import MemoryStore, store  # noqa: F401
else:
    from app.db.supabase_store import SupabaseStore as MemoryStore, store  # noqa: F401
