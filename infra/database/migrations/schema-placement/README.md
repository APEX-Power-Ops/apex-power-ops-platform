# schema-placement migration lane

Platform schema-placement changes - moving objects between schemas, and hardening `public` Data-API exposure -
that are NOT owned by a single app's Supabase migration lane.

Rules:
1. Apply via raw `psql -v ON_ERROR_STOP=1 -f <file>`, ONE action per invocation (each file is a self-contained
   `BEGIN ... <in-transaction asserts> ... COMMIT`). Do NOT route through the Supabase CLI runner or MCP
   apply_migration (they would nest the embedded transaction).
2. Every forward file has an executable, operator-gated `*.rollback.sql` companion (run as `postgres`).
3. Each change is proven on a disposable database (up/down/up) before apply; evidence lives under
   `docs/operations/<packet>/`.

Packet 01 (2026-07-10): relocate 2 inert scratch tables (`_009_rollback_snapshot`, `_phase3_load_manifest`) out of
anon-exposed `public` into the private `archive` schema. See `docs/operations/schema-placement-01/`.
