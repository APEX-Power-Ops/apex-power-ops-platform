# Archived Legacy Migration Utilities

This folder holds superseded historical utilities that are no longer part of the active legacy utility set.

Rules:

1. do not use files here for current replay or repair work unless a specific historical reconstruction requires them
2. prefer the active legacy utility set in the parent `migrations/` folder when replay or diagnostics are still needed
3. prefer `../supabase/migrations/` for all new forward schema changes

Current contents:

1. `002_transfer_data.py` — archived because the env-driven `002_data_transfer.py` path superseded it for current replay work