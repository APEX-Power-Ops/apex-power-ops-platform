# Records Gate 9 - Supabase Serving Design (scope)

Status: SCOPE note, revised 2026-07-03 after read-only grounding + operator
ratification. Transport decision D1 RATIFIED = Option B (server-side DSN as the
real least-privilege roles). No database mutated. No prod Supabase apply
authorized in this lane. Supersedes the earlier "rebind" draft.

AUTHORITATIVE ARTIFACT: the design spec
(docs/superpowers/specs/2026-07-03-records-gate9-supabase-serving-design.md) is the
source of truth for the decision record and Acceptance Criteria. This note is kept
for provenance; where they differ, the spec (AC1-AC12) governs.

Repo state grounded: main @ 3a167a89. Lane branch: records/gate9-supabase-serving.
Primary input: reference/records/SERVING_CONTRACT.yaml (Gate 5).

## Reframe: greenfield, not a rebind

A read-only catalog check of governed prod (fxoyniqnrlkxfligbxmg) on 2026-07-03
found records is ABSENT from prod:

- records schema: absent (0)
- records_* roles: 0
- records-lane migrations applied: 0 of 198 total prod migrations
- Data API exposed-schemas is platform-config-gated; records is not exposed.

So Gate 9 is NOT a live-policy rebind - there are no prod records objects to
rebind. It is a Supabase-SERVING strategy/design lane whose output is:

1. a reviewed design + spec,
2. a disposable Supabase-like validation harness proving the serving posture,
3. a prod-variant APPLY PACKET (records migration stack 001-049 + role/password
   custody) that a later, separate operator apply consumes.

No prod mutation happens in this lane.

## Ratified decision D1 = Option B (server-side DSN)

Serving connects SERVER-SIDE to Supabase Postgres as the three custom
least-privilege LOGIN roles from the Gate 5 contract:

- records_api (read-only), records_intake_writer (column-scoped writes),
  records_auditor (audit-log read only).

Why B (grounded):

- Gate 5 policies already target these roles by name (TO records_api, ...).
  A direct role DSN makes current_user = the role, so the existing policies
  apply NATIVELY - zero policy rewrite.
- records stays OFF the Data API entirely (never added to exposed schemas; no
  anon/authenticated grant). Stronger posture than collapsing to authenticated.
- Honors the contract ceiling invariant (SERVING_CONTRACT rebind recipe step 3):
  widening the Supabase role mapping is a design smell that would re-open Gate 5.
  Option A's collapse-to-authenticated is exactly that widening.
- No browser records consumer exists yet (records serving runtime = deferred
  flagship), so a JWT-claim provisioning model is speculative surface (YAGNI).

Option A (Data API / Supabase Auth + claims) is DEFERRED as a future additive
gate, to be designed only when a real browser records consumer exists. If A is
ever chosen, PREFER a Custom Access Token Hook + role/permission table +
authorize() for auditability; never use raw user_metadata for authorization.
(Softened per review finding 5: reading app_metadata via auth.jwt() in RLS is
also documented; hook/table/authorize is the preferred, not the only, pattern.)

RESOLVED spec-grounding item: confirmed via Supabase docs that a custom LOGIN role
authenticates through Supavisor (session) + direct connection and RLS applies as
that role (NOBYPASSRLS default). Verdict SUPPORTED-WITH-CAVEATS; see design spec
sections 3.1 / 3.5 / 7.

## Remaining decisions

- D2 claim shape: MOOT under B (no JWT claims; the DB role is the boundary).
- D3 reader baseline: under B, automatic - only the records_api DSN reads;
  no end-user is authenticated into records.
- D4 writer authority: under B, whichever server component holds the
  records_intake_writer DSN (a service, not end-users).
- D5 auditor authority: under B, the records_auditor DSN holder (a compliance/
  audit read service).
  -> D3/D4/D5 collapse to DSN CUSTODY assignments; name the holding component
     per DSN in the spec. Flag for operator if any DSN should be withheld.
- D6 source links: CLOSED. neta_table_source_links stays owner-only; opening it
  needs a separate source-review capability + red proofs - out of scope until a
  real source-review UI exists.

## Serving posture (Option B)

- No serving path uses service_role, postgres, an owner role (records_owner,
  records_fn_owner), a BYPASSRLS role, or an sb_secret_* key.
- The 3 role DSNs are the only records serving credentials. Passwords are set
  out-of-band (Vault-first custody, 0600 caches) at prod-landing time; no
  migration sets a password.
- records schema is NOT added to Data API exposed-schemas; no anon/authenticated
  grant on any records object.
- Honest scope: this closes the non-superuser-owner RLS bypass only. postgres
  superuser and Supabase service_role bypass remain custody-controlled + detector
  + deferred startup assertion, not provable inside Postgres. Never "safe by
  enforcement" unqualified.

## Sequence (finding 3)

1. Gate 9 design/spec (this lane) - server-side DSN custody, Supavisor/direct
   role behavior, secret-audit Check 3 arming, startup identity assertion.
2. Disposable Supabase-like validation harness: role stubs, prove the B
   red/green matrix. Not records_dev.
3. Prod-variant apply packet: records migration stack (001-049) + role creation
   + out-of-band password custody. Reviewed, NOT applied here.
4. Operator apply later (separate, gated). Run Supabase advisors before accept.

## Acceptance criteria - SUPERSEDED

The acceptance criteria in this scope note are SUPERSEDED by the design spec
(2026-07-03-records-gate9-supabase-serving-design.md), AC1-AC12. Consume the
spec's ACs, not this note's. The spec corrects this draft in three places that a
downstream plan/harness must NOT regress:

- AC4: records_api reads the 14 app-served tables AND the 2 security-invoker views
  (v_asset_test_history, v_pm_due) - not "exactly 14 tables".
- AC2: the Data-API negative covers anon, authenticated, AND service_role at the
  grant layer (grants precede RLS; a BYPASSRLS stub with no grant is still blocked).
- AC10: the startup assertion is session_user-based (session_user = current_user,
  both a sanctioned non-super / non-bypassrls / non-owner role) - not current_user
  only.

See the design spec for the full, authoritative AC1-AC12.

## Check 3 update (finding 4)

infra/secret-audit.sh Check 3 currently sanctions only records_api and
records_intake_writer (Gate 3-era). Gate 9 adds records_auditor as a connecting
role. Update Check 3 - when real serving config exists (RECORDS_SERVING_GLOBS
armed in the same change) - to allow exactly the 3 B roles and reject postgres,
owner roles, service_role, sb_secret_*, and BYPASSRLS, parsing all DSN forms in
dsn_form_inventory.

## Grounding provenance

- Prod catalog read-only check: records absent, 0 records_* roles, 0 of 198
  migrations (governed fxoyniqnrlkxfligbxmg, 2026-07-03).
- Gate 5 object matrix confirmed against migrations 045-048 (no contract drift):
  8 ref SELECT-only both roles; 6 wp column-scoped writer; no DELETE; source_links
  + audit_log owner-only; audit_log append-only.
- Supabase current mechanics (2026): custom-schema Data API = two gates (exposed
  schemas list + explicit per-role grants); the 2026 explicit-grant breaking
  change is public-schema-scoped (custom schemas never auto-exposed); UPDATE needs
  a SELECT policy; user_metadata is unsafe for authorization; new sb_publishable_*/
  sb_secret_* keys and asymmetric JWT signing are orthogonal to the DB-role model.
