# Breaker Sandbox — Snapshot Manifest

- **Source:** prod `fxoyniqnrlkxfligbxmg` schema `tcc` @ 2026-06-25 (operator-side `pg_dump`, direct/session connection; prod credential never touched the host).
- **Baseline DB:** `tcc_breaker_baseline_20260625` (frozen — PUBLIC connect revoked)
- **Snapshot timestamp (UTC):** 2026-06-25T20:26:40Z
- **Dump command shape:** `pg_dump --no-owner --no-privileges --schema=tcc -Fc <PROD_RO_DSN>` (74,643,372 bytes)
- **Dump sha256:** `7c5ee61457471f4a324de80ad7dbb309e0a8c4f62805d2b6b6650ab277ac3166`
- **Object counts (tcc):** tables=91, views=2, sequences=30, indexes=190 — matches `check_baseline_exact` (PASS).
- **RLS:** 60 tables RLS-enabled; 120 policies (all `to public`; 60 reference `auth.*` — `auth.role()`/`auth.jwt()`, NOT `auth.uid()`; 0 `vault.*`).

## Restore preflight (what the real `--schema=tcc` dump required beyond the template)
- **auth.* stubs** (`10_auth_stubs.sql`): `auth.uid/role/jwt` created before restore (60 policies reference them; a missing stub fails CREATE POLICY).
- **work.* enum stubs** (`11_work_enums.sql`): `work.provenance_source_enum`, `work.provenance_status_enum`, `work.relay_range_parent_kind_enum`, `work.relay_voltage_restraint_kind_enum` — the `relay_*` table columns are typed from the `work` schema, which `--schema=tcc` excludes. Complete prod value lists used (a missing label fails the data COPY).
- **FK CONSTRAINTS OMITTED (by design):** the restore uses a TOC that drops `FK CONSTRAINT` entries. Prod carries data-quality orphans under FKs it marks valid but does NOT enforce — e.g. **484 `tcc.tmt_curves` rows whose `frame_id` has no `tcc.tmt_frames` row** (FK `tcc_tmt_curves_frame_id_fkey` is `convalidated=true` yet violated; classic bulk-migration artifact — `work.provenance_source_enum` even has `migration`/`bulk_upload`). Re-validating those FKs on restore fails. The sandbox is an analytical/audit copy; FK enforcement is not what Codex audits, and the orphan rows are PRESERVED as real prod data (a finding the #79 audit should surface). `--exit-on-error` still guards everything else (fail-closed).
- No login-role stubs needed; column defaults core-only (no contrib extension).

## Clones (verified live)
- **`tcc_breaker_viewer_20260625`** — read-only clone; RLS disabled clone-locally on all 60 tables; `tcc_breaker_ro` reads 17,877 `tcc.etu_sensors` rows (RLS off, SELECT-only — no write). `check_viewer` PASS.
- **`tcc_breaker_codex_79audit_20260625`** — disposable writable clone; `tcc_breaker_codex_79audit` owns all tcc r/S/v (linked identity/serial sequences follow their table's owner; standalone sequences + tables + views explicitly transferred). Write+DDL proven (CREATE/INSERT/SELECT in a rolled-back txn). `check_codex_clone` PASS.

## Privilege matrix (acceptance — all PASS)
- `check_role_zero_reach`: codex role has NO CREATE on any non-codex DB.
- Per sibling DB (`ops_dev`, `records_dev`, `learning_dev`, `orchestration_dev`): `check_sibling_no_table_priv` leaked=0 AND `check_schema_create` (no CREATE on `public`).
- Neither role has any cluster attribute (no SUPERUSER/CREATEDB/CREATEROLE/BYPASSRLS).
- **Residual postgres-owned in codex clone:** 1 function, 0 types (the r/S/v ownership-loop does not cover functions; codex can still EXECUTE it — harmless for the audit). `check_residual_owner` recorded.

## Dump-file deletion proof
Dump deleted from `/home/olares/dev-pg-backups/tcc/` at **2026-06-25T20:27:06Z** — 0 remaining matches; directory empty (mode 700). Prod data now exists on the host ONLY inside the restored baseline/clone DBs.

## Notes / findings for follow-up
- **Doc drift:** repo docs say ~60 tcc tables; prod has 91 — reconcile separately.
- **Prod data-quality (for #79 audit):** 484 orphan `tmt_curves` under a valid-but-unenforced FK.
- The 4 synthetic fixture DBs (`tcc_breaker_*_fixture`) are dropped in the T7 cleanup step.
