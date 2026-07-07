# Records prod-apply evidence — greenfield 001-049 into `fxoyniqnrlkxfligbxmg`

Authoritative "applied" record per packet §11. Value-silent (no DSN / password / API key).
Governed by this transcript, NOT `supabase_migrations.schema_migrations` (packet §4).

- **Project:** `fxoyniqnrlkxfligbxmg` (authorized connector `bb4a07f4-...`; writes via session-pooler
  `SUPABASE_PROD_DSN` injected at runtime from Infisical `apex-platform/prod` — `infra/.env` NOT edited).
- **Applier tree (pinned):** `b8df9e3df012a3f0f8fcd81eb3d08165265faf8c` (== `origin/main`).
- **Server:** PostgreSQL 17.6. **Applier identity:** `postgres` (super=false, bypassrls, createrole).
- **Packet:** `.claude/PLATFORM/RECORDS-PROD-APPLY-PACKET-2026-07-07.md` (v2.1).

---

## GO #0 — SCRATCH_PROBE_GO  (2026-07-07, operator-gated)  — RESULT: PASS

### §2.1 Read-only prod re-probe (authorized connector, SELECT-only) — GO
- `records` schema absent; `records` table count = 0.
- App roles present = `[]`; any `records_*` role = `[]` (no name collision).
- `postgres` attrs: super=**false**, bypassrls=true, createrole=true, createdb=true, replication=true
  (== the branch-proof `LOCAL_APPLIER_ENVELOPE`).
- Extensions: `pgcrypto` present, `uuid-ossp` present (installed set: pg_stat_statements, pgcrypto,
  plpgsql, supabase_vault, uuid-ossp, vector). `fn_audit_capture` in `records` = false.
- Prereq scan of 49 up-files: **no `CREATE EXTENSION`**; `gen_random_uuid()` used (core PG17, 5 files);
  0 files use uuid-ossp / pgcrypto-specific / citext. **No prereq/capability/collision gap → GO.**

### §2.2 SHA pin + 49-file sha256 manifest — GO
- HEAD = `b8df9e3df012a3f0f8fcd81eb3d08165265faf8c` == `origin/main` (fetched).
- Applier bytes pristine: records-migration dir porcelain empty; `git diff b8df9e3d` for the dir = 0
  lines; probe diff = 0 lines; tracked-modified anywhere = 0. (Working tree shows exactly ONE
  untracked file — the known stray `docs/operations/CODEX-OVERSIGHT-RESUME-PLAYBOOK-2026-07-06.md` —
  left untouched, NOT in this apply.)
- sha256 (first 12) per up-file:
  001 cf97c1759f5f · 002 f90e480a87df · 003 5ed337c6360c · 004 4f12a38fb593 · 005 ee65f20c038b ·
  006 d32e9064d15b · 007 7c60e98c6af5 · 008 b93855e69988 · 009 95d3fd2b10e6 · 010 6b4da7a41d94 ·
  011 a0f51ef68a49 · 012 92cf483459f5 · 013 f3e7dcafffce · 014 8c169efdc2d8 · 015 b974f4278c64 ·
  016 c0e53d83a46a · 017 2f2936749fc3 · 018 ce1e80f45ed5 · 019 b111640567fb · 020 012d9074e768 ·
  021 7896601717fd · 022 2bbd10f3dfe4 · 023 c8b94b9b05bd · 024 da5232335faf · 025 d13a441b5faf ·
  026 7f6f3804cbcb · 027 90ad70df2f59 · 028 7d917cc55600 · 029 0d1c93b58c6a · 030 bb0a12204f90 ·
  031 48421b5f3969 · 032 3dcbd670b8a5 · 033 4ce92909df11 · 034 44e78ee0b271 · 035 23f8f6609acc ·
  036 edded840d510 · 037 b98ef2afbacf · 038 c4f6390c81f6 · 039 83ae485c4fed · 040 4aaa29cc2f59 ·
  041 af8dd9efbb4b · 042 9e9983f3e6ed · 043 7f5df69a896c · 044 ccb4545a2c0c · 045 24bd48b0263c ·
  046 495175852dfe · 047 4e1bdb85a457 · 048 3ca7506563ae · 049 e58fc60da3e6

### §2.3 Self-wrap audit — GO
- 49/49 up-files carry a top-level `BEGIN; ... COMMIT;` (atomic per `psql -f`).

### §2.4 DSN<->connector bind (fail-closed) — GO (after operator credential fix)
- Initial run FAIL-CLOSED: `infra/.env` `SUPABASE_PROD_DSN` targeted the right project (ref match) but
  **password authentication failed** — stale/rotated password. Structural diagnosis (value-silent):
  the value staged in Infisical prod was initially malformed (missing `@`, direct-host variant).
- Operator re-stored a well-formed **session-pooler** DSN in Infisical `apex-platform/prod`.
- Re-run UNDER injection (`infra/infisical/inject.sh prod -- ...`): `INJECTED_DSN=yes`, `HAS_AT=yes`,
  `POOLER_5432=yes`, `PSQL_RC=0`. Facts match the §2.1 connector probe exactly: current_user=postgres,
  server_version=17.6, `records` absent, 0 tables, 0 `records_*` roles, postgres super=f/bypassrls=t/
  createrole=t. **Bind confirmed → GO.** Mechanism = runtime injection; `infra/.env` untouched.
- Incident: during the malformed-DSN attempt, psql echoed a password fragment to stderr (transcript-
  exposed). Harness hardened afterward (psql stderr captured + classified, never dumped). Re-rotation
  is the operator's call.

### §2.6 Advisor baseline (read-only, pre-write) — captured
- `get_advisors(security)` + `(performance)` captured project-wide before any write. Records-scope is
  empty by construction (`records` schema absent). To be diffed by finding IDENTITY post-T2 (§9).

### §2.5 GO #0 scratch-WRITE probe (`supabase_probe.py`, trusted-applier) — PASS
- Run suffix `r52f1dd5099`; gate-a-policy `trusted-applier`; exit 0.
- 8/8 PASS: role_attr_A2 · gate_a_creator_edge · gate_a_escalation (escalation POSSIBLE → ACCEPTED
  under trusted-applier; postgres exempt from invariant 8) · gate_b_policy_binding ·
  ownership_choreography · ddl_envelope · trigger_set_role · rls_enforcement.
- The non-super `postgres` write identity exercises every privilege class 045-049 need; matches the
  Phase-3B branch-proof envelope.

### Zero-residue re-probe (independent; authorized connector, SELECT-only) — CLEAN
- `scratch_roles=[]`, `scratch_schemas=[]`, `any sp_*-prefixed object=0`.
- Greenfield intact: `records` absent, 0 tables, 0 `records_*` roles.

**GO #0 verdict: PASS, zero residue, greenfield intact. Next gate: GO #1 (T1 apply 001-044) —
operator-gated; not yet authorized.**

---

## GO #1 — T1 apply (migrations 001-044)  (2026-07-07, operator-gated)  — RESULT: PASS

### Credential re-verify (post second rotation)
- Operator re-rotated the prod password (leaked-fragment remediation) + updated Infisical. Bind
  re-verified UNDER injection: after ~20s Supavisor pooler propagation, `PSQL_RC=0`, FACTS match §2.1
  (current_user=postgres, 17.6, envelope super=f/bypassrls=t/createrole=t). Fresh password
  authenticates; no leak (stderr captured + classified).

### Apply mechanism + result
- Exact T1 manifest = 44 up-files `001..044` (belt-and-suspenders guard rejects 045-049; halts after
  044). Each applied via `psql -v ON_ERROR_STOP=1 -q -f <file>` over the injected session-pooler DSN,
  numeric order, STOP-on-first-nonzero. **Result: 44/44 OK, zero failures** (incl. the 4051-line
  `006` NETA seed streamed by `psql -f`). `T1_COMPLETE: applied 44/44 (001-044)`.

### T1 structural fingerprint (authorized connector, read-only)
- tables=15, views=2, functions=1, indexes=64, enums=14, triggers=10.
- `records_*` app roles = `[]` (T2 not run - roles minted in 045/047).
- table_owners = `{postgres: 15}` (all base tables owned by the applier; 046 transfers to
  records_owner under T2).

### Reference row counts (exact, read-only) - total 4316 rows / 15 tables
- Seed/reference (non-empty): neta_test_items=3920, neta_tables=88, neta_procedures=72,
  neta_procedure_xref=70, asset_classes=69, asset_class_neta_procedure=62, form_templates=35.
- Operational (empty, expected greenfield): assets, persons, pm_events, pm_programs, pm_schedules,
  form_submissions, form_field_values, neta_table_source_links = 0.

**GO #1 verdict: PASS. Schema stood up, seed loaded, no records role/ownership yet. Next gate: GO #2
(T2 apply 045-049 + §5 acceptance) - operator-gated; not yet authorized.**

---

## GO #2 — T2 apply (045-049) + adapted acceptance  (2026-07-07, operator-gated)  — RESULT: PASS

### DEVIATION + operator-ratified adaptation (§5 acceptance)
- The literal §5 tiers (run_validation tier5/6/7) impersonate via `SET SESSION AUTHORIZATION`
  (superuser-only). Prod `postgres` is non-super -> 42501 false-RED. VERIFIED on prod:
  `SET SESSION AUTHORIZATION` FAIL(42501); `SET ROLE` OK. Stopped before T2, surfaced the deviation.
- Operator RATIFIED a **prod-compatible dormant acceptance shim** (`prod_acceptance_managed.py`,
  sha256 `c8bf670c6c7eb4f3e307519dea4f0c2c15d32df033fad7666aa3830b826aa56f`): (1) static invariants
  full-strength (reuses run_validation SQL constants); (2) behavioral via SET ROLE + transient
  self-grant (NO bare-postgres records access) + EXACT row-PK audit sentinel + Phase A/B/C residue;
  (3) session_user semantics CARRIED from Phase-3B, disclosed. Cross-engine reviewed (Claude + 4 Codex
  passes; all findings folded incl. bare-postgres load-bearing, reachability-false-green,
  sequence-residue honesty). Final Codex verdict: SAFE TO RUN. Not literally zero-residue: only
  `audit_log.audit_id` identity advances + normal aborted-write WAL churn (packet-Sec-5 ratified,
  benign on dormant substrate).

### Pre-write gates (all GREEN before 045)
- **Pre-state drift:** records present, 15 tables/2 views, 0 records roles, owner=postgres, RLS/FORCE
  0/0, policies 0, audit_log absent (== exactly T1-only, no drift).
- **Artifact identity:** shim `c8bf670c...b826aa56f`; T2 script `t2_apply.sh`
  `bfe3ddddfa53e4911b27b8b8057ba3363ee626f7b3ebb7d6920cd7712eb0b9c5`.
- **§2.4 bind** re-verified under injection: `PSQL_RC=0`, envelope f/t/t.

### T2 apply (045-049)
- `psql -v ON_ERROR_STOP=1 -q -f` per self-wrapped file under injection: **5/5 OK**
  (045_records_security_rls, 046_records_ownership, 047_records_audit_roles, 048_records_audit_log,
  049_records_audit_triggers). `T2_COMPLETE: applied 5/5 (045-049)`.

### Post-T2 posture (connector, read-only) - matches Phase-3B branch-proof Phase C
- 6 roles: records_api/intake_writer/auditor LOGIN; records_owner/fn_owner/reclaim_owner NOLOGIN;
  none super/bypass. base_tables=16, RLS 16/16, FORCE 16/16, policies=28. schema_owner=records_owner
  (046 transferred), audit_log owner=records_fn_owner, fn_audit_capture owner=records_fn_owner,
  trg_audit=6, owned-by-super/bypass=0, non-owner tab/view=0.

### §5 adapted acceptance (shim under injection) - PASS
- `ADAPTED_ACCEPTANCE_OVERALL: PASS`: [PASS] bucket1-static-invariants, [PASS] bucket2-behavioral-set-role,
  [INFO] bucket3 session_user semantics carried-from-Phase-3B (not re-proved on prod; deferred to a
  real direct-login consumer).
- Residue (connector, pg_catalog corroboration): non-exempt membership edges=0, exempt creator
  edges=6, scratch/sentinel roles=[]. Shim Phase-B verified records-row sentinels via the app roles.

### §7 Data-API exclusion (3 gates)
- **Grant gate:** shim bucket 1 - anon/authenticated/service_role hold NO schema USAGE + NO object
  grant on records; PUBLIC=0 (exhaustive aclexplode).
- **Config + live gate:** `GET /rest/v1/assets` with `Accept-Profile: records` (active publishable
  key) -> **HTTP 406 PGRST106** `"Invalid schema: records"`, hint `"Only the following schemas are
  exposed: public, graphql_public"`. Specific schema-not-exposed failure (not 200/401/404). Pre-auth
  schema-exposure rejection == records config-excluded from the Data API.

### §9 advisor diff (by finding identity)
- Security: baseline 152 (ERROR 62/WARN 71/INFO 19), **0 records-scoped** -> post-T2 154 (ERROR 62/
  WARN 72/INFO 20), **2 records-scoped**, delta = exactly these two, both BY-DESIGN:
  `[INFO] rls_enabled_no_policy` on records.neta_table_source_links (deny-all D10) +
  `[WARN] function_search_path_mutable` on records.fn_set_updated_at (base trigger fn). **No records
  ERROR.** (All 62 ERROR / 72 WARN are inherited public/tcc/... schemas, pre-existing, out of scope.)

**GO #2 verdict: PASS.** Secured records substrate live on prod: RLS/FORCE/policies/ownership/audit
all as designed; Data-API-excluded; acceptance green on the managed substrate. **Transient window:**
3 LOGIN-but-passwordless roles (records_api/intake_writer/auditor) exist between T2 and the GO #3
toggle - no credential minted. **Next gate: GO #3 (dormant NOLOGIN toggle of all three + all-6-NOLOGIN
assert) - operator-gated; not yet authorized.**
