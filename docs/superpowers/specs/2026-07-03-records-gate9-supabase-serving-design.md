# Records Gate 9 - Supabase Serving Design (Option B: server-side DSN)

> Design spec. After operator review, the next step is superpowers:writing-plans.
> Supersedes the "rebind" framing.
> Scope note: docs/superpowers/specs/2026-07-03-records-gate9-supabase-rebind-scope.md

Status: DESIGN rev 2. D1 ratified = Option B (2026-07-03). Grounded against prod
(read-only), Gate 5 migrations 045-048, and current Supabase docs.

Rev 2 folds the operator review (2026-07-03): P1 session_user-based startup
assertion (SET ROLE cannot false-green); contract v2 to end the Option-A
`supabase_target: authenticated` false-green; Supavisor qualified-user parser
form; records_api security-invoker view scope corrected.

**Goal:** Define how the Gate 5 records security boundary is SERVED from Supabase
without weakening it - by connecting server-side as the three custom
least-privilege LOGIN roles - and produce a validated design, a disposable
validation harness, a v2 serving contract, and a reviewed prod-variant apply
packet. No prod mutation in this lane.

**Architecture:** Server-side services connect to Supabase Postgres over direct or
Supavisor-session DSNs authenticated AS records_api / records_intake_writer /
records_auditor. current_user IS the role, so Gate 5's `TO records_*` policies
apply natively with zero rewrite. records is never exposed to the Data API and
never granted to anon/authenticated. No service_role / owner / superuser serving
path exists.

**Tech stack:** Supabase Postgres (15+), the existing records migration stack
001-049, the Gate 5 validation-harness substrate (run_validation.py pattern),
reference/records/SERVING_CONTRACT.{yaml,md} + test_serving_contract.py,
infra/secret-audit.sh Check 3, Vault (Padloc) for out-of-band password custody.

## Global constraints (bind every downstream task)

- Never target records_dev. Disposable validation DBs only (records_val_* pattern).
- No prod Supabase apply in this lane. Output = reviewed packet + operator checklist.
- No migration sets a password. Owners stay NOLOGIN; the 3 role passwords are set
  out-of-band, Vault-first, 0600 caches, at prod-landing time.
- ASCII-only added lines.
- Serving credentials = exactly {records_api, records_intake_writer,
  records_auditor}. Never service_role, postgres, records_owner, records_fn_owner,
  a BYPASSRLS role, or an sb_secret_* key.
- records is NOT added to Data API exposed-schemas and gets no anon/authenticated
  grant on any object.
- Honest scope: this closes the non-superuser-owner RLS bypass only.
  postgres-superuser and Supabase service_role bypass remain custody + detector +
  deferred startup assertion. Never "safe by enforcement" unqualified.
- Value-silent: never echo a DSN or password.

## 1. Context: greenfield, not a rebind

Read-only prod check (governed fxoyniqnrlkxfligbxmg, 2026-07-03): records schema
absent, 0 records_* roles, 0 of 198 migrations from the records lane, records not
in the Data API exposed-schemas. So Gate 9 is not a live-policy rebind; there are
no prod records objects to rebind. It is a serving strategy/design lane.

Gate 5 objects it serves (confirmed against migrations 045-048, no drift):

- 8 reference tables: SELECT-only for both records_api and records_intake_writer.
- 6 write-path tables: SELECT for both; column-scoped INSERT/UPDATE for
  records_intake_writer only; no DELETE anywhere.
- 2 security-invoker views (v_asset_test_history, v_pm_due): SELECT for
  records_api ONLY (not records_intake_writer). 045 grants these; they are part of
  records_api's exact read scope.
- neta_table_source_links and audit_log: owner-only (records_owner,
  records_fn_owner respectively). audit_log is append-only; records_auditor holds
  SELECT on audit_log only.
- All records tables carry FORCE ROW LEVEL SECURITY.

## 2. Decision record

**D1 = Option B (server-side DSN as the real roles).** Ratified 2026-07-03.
Rationale (grounded): Gate 5 policies already target the roles by name, so a
direct role DSN makes current_user = the role and the policies apply natively
(zero rewrite); records stays off the Data API (no exposed-schema entry, no
anon/authenticated grant); it honors the SERVING_CONTRACT ceiling invariant
(widening the Supabase mapping would re-open Gate 5); and no browser records
consumer exists yet (records serving runtime = deferred flagship), so a
JWT-claim provisioning model is speculative surface (YAGNI).

Mechanically verified SUPPORTED-WITH-CAVEATS against current Supabase docs: custom
LOGIN roles authenticate via direct connection or Supavisor session mode;
NOBYPASSRLS is the default; the PostgREST authenticator / db_pre_request path is
bypassed entirely. Caveats folded into sections 3.1, 3.4, 3.5, and 7.

**Contract is stale under B.** The Gate 5 SERVING_CONTRACT maps all three
connecting roles to `supabase_target: authenticated` - an Option-A-shaped
placeholder - and test_serving_contract.py passes against it, so the Option-B
drift is a false-green. Gate 9 revs the contract to v2 (section 4, deliverable 5)
with an explicit direct-role/DSN serving identity and a test that fails on the
drift.

**Option A (Data API + claims) is DEFERRED** as a future additive gate, designed
only when a real browser records consumer exists. If A is ever chosen, prefer a
Custom Access Token Hook + role/permission table + authorize() for auditability;
never use raw user_metadata for authorization. (Preferred, not the only, pattern.)

**D2** claim shape: moot under B (the DB role is the boundary; no JWT claims).
**D3/D4/D5** reader/writer/auditor authority: resolve to DSN custody - which
server component holds each DSN (section 3.4). **D6** source links: CLOSED.

## 3. Serving architecture (Option B)

### 3.1 Connection model

Each serving component connects with a DSN authenticated AS one of the three
roles. Recommended transports (Supabase guidance):

- Direct connection (port 5432) - recommended for persistent servers / long-lived
  containers.
- Supavisor session mode (port 5432) - fallback when IPv4-only networking is
  required or pooling/queuing is wanted; supports prepared statements. Supavisor
  qualifies the DSN username as [role].[project_ref] (e.g. records_api.<ref>); the
  base role is still records_api - Check 3 (section 6) normalizes this form.
- NOT Supavisor transaction mode (port 6543) for this pattern unless specifically
  needed; if used, prepared statements must be disabled (driver-specific).

No runtime SET ROLE is used - the connection authenticates AS the target role, so
current_user = session_user = the role for every statement.

### 3.2 Why the Gate 5 boundary binds natively

- Policies are written `TO records_api / records_intake_writer / records_auditor`;
  with current_user = the role, standard Postgres role-matching applies them.
- The three serving roles are created NOBYPASSRLS (default) - they cannot bypass
  RLS.
- The three serving roles are NOT table owners (owners are records_owner /
  records_fn_owner). Even so, Gate 5 sets FORCE ROW LEVEL SECURITY on every
  records table, so policies would bind even an owner - belt and suspenders.
- The two views are security_invoker = true, so RLS on their base tables binds
  through them with records_api as current_user (no view-owner privilege leak).

### 3.3 Data API exclusion (two independent gates)

- Platform config: records is NOT added to the Data API exposed-schemas list
  (apply-packet checklist item; not locally testable).
- Grants: no USAGE on schema records and no table grant to anon or authenticated
  (locally provable negative). This pair is AC2.

### 3.4 DSN custody

One DSN per role, each held by a named server component:

- records_api DSN -> the records read-serving service.
- records_intake_writer DSN -> the records intake / field-sync service.
- records_auditor DSN -> the compliance / audit-read service.

Passwords are set out-of-band (Vault-first, Padloc canonical), 0600 caches, at
prod-landing time; no migration sets a password. Custom-role passwords are NOT
auto-propagated by Supabase, so rotation is manual: the packet includes a rotation
runbook and a manual-reset step after project pause/restore or major-version
upgrade.

Open for operator: confirm which of these components exist today and whether any
DSN is withheld until its consumer is real (a DSN with no consumer should not be
minted).

### 3.5 Startup identity assertion (session_user-based)

A serving process asserts, at startup or first request, that:

- session_user = current_user (no SET ROLE is masking a privileged login), and
- that role is one of the three sanctioned roles, and
- the role is NOT rolsuper, NOT rolbypassrls, and not an owner role
  (records_owner / records_fn_owner).

Fail-closed if any check fails. Checking current_user alone is insufficient: a
postgres/privileged connection can SET ROLE records_api so current_user looks
sanctioned while session_user stays privileged (the Gate 5 actor_role =
session_user lesson). This assertion proves THIS process holds a sanctioned,
non-bypassing, non-owner login - not the absence of a privileged credential
elsewhere (that stays a custody + detector concern).

## 4. Deliverables (this lane)

1. This design + the implementation plan (writing-plans).
2. A disposable Supabase-like validation harness (section 5).
3. secret-audit Check 3 arming + startup identity assertion (section 6).
4. A reviewed prod-variant apply packet - produced and reviewed here, NOT applied
   (section 7).
5. SERVING_CONTRACT v2 (Option B): replace `supabase_target: authenticated` per
   connecting role with `serving_transport: direct_role_dsn` + `connect_as:
   <role>`; add `data_api_exposed: false`; add `supavisor_qualified_user` to
   `dsn_form_inventory`. Update the .md companion (Gate-9 recipe now = direct-role
   DSN, not JWT/pooler-role binding) and test_serving_contract.py so it FAILS if
   any connecting role's serving identity is authenticated, service_role, or an
   owner role.

## 5. Disposable validation harness

Extends the Gate 5 run_validation.py substrate. In a disposable records_val_* DB
(never records_dev): apply the records migration stack 001-049 (which creates the
records_* roles); add anon / authenticated / service_role stubs (Supabase
built-ins absent from plain Postgres). Prove the serving red/green matrix via SET
SESSION AUTHORIZATION per role (consistent with Gate 5's writer proofs; LOGIN and
passwords are irrelevant to SET SESSION AUTHORIZATION):

- records_api: can SELECT all 14 app-served tables AND the 2 security-invoker
  views (v_asset_test_history, v_pm_due), proven with join-satisfying positive
  controls so the views actually return rows under records_api RLS; cannot
  INSERT/UPDATE/DELETE any records table; cannot read neta_table_source_links or
  audit_log.
- records_intake_writer: can SELECT the 14; can INSERT/UPDATE only the column-
  scoped writer matrix on the 6 write-path tables; no DELETE; cannot read
  source_links or audit_log; cannot read the 2 views (records_api-only).
- records_auditor: can SELECT audit_log only; cannot read the 14, the 2 views, or
  source_links; cannot INSERT/UPDATE/DELETE audit_log.
- anon and authenticated: reach NOTHING in records - no schema USAGE, no table or
  view grant (the Data-API-exclusion negative, AC2).
- audit_log stays append-only: no role can UPDATE or DELETE it.
- Role cleanup: drop all created stub roles AFTER the DB drop (Gate 5 [drop-role]
  discipline) so the shared cluster stays clean.

The harness proves the grant + RLS boundary (the security-critical surface). The
actual login/pooler path is a connection-string concern proven by the startup
assertion (3.5) and at apply time, not by the local harness.

## 6. secret-audit Check 3 arming + startup assertion

Update infra/secret-audit.sh Check 3: allow exactly {records_api,
records_intake_writer, records_auditor}; reject postgres, records_owner,
records_fn_owner, service_role, any BYPASSRLS role, and sb_secret_* keys. Parse
all DSN forms in dsn_form_inventory (keyword_user, url_userinfo,
url_driver_qualified, pg_env_vars) PLUS a new supavisor_qualified_user form for
Supabase pooler DSNs whose username is [role].[project_ref]. For the Supavisor
form, Check 3 splits the base role from the project-ref suffix and requires the
base role to be exactly one sanctioned role and the suffix to be a project-ref -
arbitrary dotted usernames (postgres.<ref>, an unsanctioned base, or a
multi-dotted user) are rejected. Armed only when RECORDS_SERVING_GLOBS points at
real serving config, introduced in the same change. Value-silent. Add a red/green
unit per rejected credential shape and per DSN form, including a sanctioned
records_api.<ref> (pass) and postgres.<ref> / evil.<ref> (fail).

The startup identity assertion (3.5) ships as a small reusable check the serving
process runs before serving.

## 7. Prod-variant apply packet (reviewed, NOT applied here)

Scope of the packet a later, separate operator apply consumes:

- Records migration stack 001-049 - first-ever prod landing.
- Ensure the three serving roles have LOGIN and out-of-band passwords (Vault),
  altering any the migrations created NOLOGIN; no password appears in any migration.
- Confirm FORCE RLS on all records tables and that the three roles are non-owners.
- Confirm records is NOT added to exposed-schemas and holds no anon/authenticated
  grant.
- SCRAM-SHA-256 prefix check on the freshly created roles (docs-ambiguous; verify
  empirically that fresh roles are SCRAM, not md5).
- Run Supabase security advisors; review before accept (AC11).
- Value-silent apply-evidence transcript (pre-SHA / post-counts / advisors),
  per the established apply-evidence standard.

This lane only produces and reviews the packet; the operator applies later.

## 8. Honest scope

Gate 9 closes the non-superuser-owner RLS bypass for records serving only. The
postgres superuser and the Supabase service_role can still bypass RLS; those
remain custody-controlled (never minted as records serving credentials), covered
by the secret-audit detector, and by the deferred startup assertion. Do not
describe records serving as "safe by enforcement" without this qualification.

## 9. Acceptance criteria

- AC1: Serving credentials are exactly the three contract roles; no
  owner/superuser/service_role/BYPASSRLS/sb_secret_* credential appears in any
  serving config.
- AC2: records is not exposed to the Data API; no anon or authenticated grant on
  any records object (proven negative in the harness + apply-packet checklist).
- AC3: Only the sanctioned role DSNs reach the allowed objects; each role reaches
  exactly its contract scope and no more.
- AC4: records_api reads exactly the 14 app-served tables and the 2 security-
  invoker views (v_asset_test_history, v_pm_due), and writes nothing.
- AC5: records_intake_writer reads the 14 (not the 2 views) and inserts/updates
  only the column-scoped writer matrix on the 6 write-path tables; no DELETE.
- AC6: records_auditor reads audit_log only; cannot read operational / reference /
  view / source-link tables.
- AC7: audit_log stays append-only; no serving grant or policy opens UPDATE/DELETE.
- AC8: neta_table_source_links remains closed to all three serving roles.
- AC9: secret-audit Check 3, once armed, allows exactly the three roles and fails
  on postgres/owner/service_role/sb_secret_*/BYPASSRLS across all DSN forms
  including the Supavisor [role].[project_ref] form; value-silent.
- AC10: The startup identity assertion proves session_user = current_user, both
  equal one sanctioned records role, and that role is NOT rolsuper, NOT
  rolbypassrls, and not an owner role - so a privileged login that did SET ROLE
  cannot false-green as sanctioned.
- AC11: Supabase security advisors run and are reviewed before any prod apply
  packet is accepted.
- AC12: SERVING_CONTRACT is revised to v2 with a direct-role/DSN serving identity
  (not supabase_target: authenticated); test_serving_contract.py fails if any
  connecting role's serving identity is authenticated, service_role, or an owner
  role.

## 10. Out of scope

- Option A (Data API + claims / browser consumer) - deferred future gate.
- The actual records prod landing apply (operator-run, separate from this lane).
- Widening source_links or adding any new serving capability - that would be a new
  migration + a SERVING_CONTRACT update, never a wider Supabase role mapping.

## 11. Verify-at-apply caveats

- SCRAM-SHA-256 vs md5 for freshly created roles (empirical check at apply time).
- Any project-tier cap on custom roles or connections-per-role (empirical).
- Final Supavisor-session vs direct choice per deployment networking (IPv4
  add-on availability).
