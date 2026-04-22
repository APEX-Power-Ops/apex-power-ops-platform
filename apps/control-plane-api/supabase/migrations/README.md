# Supabase Migration Lane

This directory is the canonical forward migration lane for new Supabase schema changes.

Rules:

1. new schema changes for the active LV breaker completion path should be captured here first
2. dashboard-only schema edits are not authoritative unless immediately reflected in a tracked migration artifact
3. historical scripts under `migrations/` remain legacy loaders, diagnostics, or transitional utilities until archived
4. live schema inspection should be rerun before any new migration is accepted as the next baseline

Current baseline reference:

1. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\README.md`
2. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\supabase\migrations\20260322_000001_live_baseline_marker.sql`

Current inspection utility:

1. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\scripts\inspect_live_schema.py`
2. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\scripts\check_schema_drift.py`

Current execution utility:

1. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\scripts\apply_supabase_migration.py`