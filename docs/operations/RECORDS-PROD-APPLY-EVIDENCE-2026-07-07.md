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
