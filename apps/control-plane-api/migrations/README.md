# Legacy Migration Utilities

This directory is not the canonical forward migration lane.

Use it only for historical loaders, diagnostics, controlled replay, or recovery support.

Rules:

1. place new Supabase schema changes in `../supabase/migrations/`
2. do not treat the scripts here as the source of truth for forward schema state
3. do not introduce new schema changes by editing or extending these utilities
4. keep `.env`-backed connection details local and out of tracked files when running anything here

Related files:

1. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\migrations\LEGACY-UTILITY-BOUNDARY.md`
2. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\supabase\migrations\README.md`
3. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\README.md`
4. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\migrations\_archive\README.md`
