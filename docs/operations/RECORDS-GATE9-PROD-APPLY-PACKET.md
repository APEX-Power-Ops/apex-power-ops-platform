# Records Gate 9 - Prod-Variant Apply Packet (REVIEWED, NOT APPLIED)

Status: REVIEWED CHECKLIST. This document is produced and reviewed in the
`records/gate9-supabase-serving` lane. It is NOT executed here. No prod Supabase
apply happens as part of authoring or committing this file. A later, separate
operator-run apply consumes this packet against the governed prod Supabase
project.

Design basis: `docs/superpowers/specs/2026-07-03-records-gate9-supabase-serving-design.md`
(Option B: server-side DSN, three sanctioned serving roles connect AS
records_api / records_intake_writer / records_auditor).

Scope reminder (read-only prod check, 2026-07-03): records schema absent, 0
records_* roles, 0 of 198 migrations from the records lane landed, records not
in the Data API exposed-schemas. This is a greenfield first landing, not a
rebind of a live policy.

## 0. Hard gate

**NO STEP IN THIS PACKET IS APPLIED WITHOUT EXPLICIT OPERATOR SIGN-OFF.** This
lane (records/gate9-supabase-serving) only produces and reviews this packet.
The apply itself is a separate, later, operator-run action against the
governed prod Supabase project, gated on this checklist being followed in
order and each checkbox's evidence being captured before moving to the next.

Do not run any command in this packet against prod without a documented
operator GO. Any deviation from the sequence below (skipped check, reordered
step, partial completion) requires a fresh operator decision before continuing.

## 1. Pre-apply preconditions

- [ ] Confirm target project is the correct governed prod Supabase project
      (project ref only; never print a service-role key or DB password to
      confirm this - use `get_project` / dashboard identity, not a credential).
- [ ] Confirm the records migration stack range applied elsewhere for parity
      testing (`records_val_*` disposable harness) matches what will be
      applied to prod: 001-049, in order, no gaps, no local-only edits.
- [ ] Record pre-apply state (see Section 8, "pre-SHA / pre-state").
- [ ] Confirm no prior partial records apply exists in prod (expect: records
      schema absent, 0 records_* roles - re-verify empirically, do not assume
      the 2026-07-03 read-only check is still current).
- [ ] Operator GO recorded (name/date, out of this packet's scope to capture
      the mechanism - use whatever the operator's standard sign-off record is).

## 2. Land the records migration stack (first-ever prod landing)

- [ ] Apply migrations 001-049 as reviewable SQL, in numeric order, each in
      its own transaction (or a single transaction if the migration runner
      guarantees atomic all-or-nothing across the range - match whatever
      transactional discipline the harness already validated).
- [ ] This is the first-ever prod landing of this stack - there is no existing
      prod records data or schema to preserve or migrate; treat every
      migration as a clean create, not an alter-in-place against live rows.
- [ ] Confirm each migration's `_down` counterpart exists and was exercised in
      the disposable-DB harness (reversibility already proven pre-apply; this
      step is a re-confirmation, not a new proof).
- [ ] After the full range lands, capture post-apply object counts (see
      Section 8).
- [ ] Do NOT run this step, or any step below, until Section 1's operator GO
      is recorded.

## 3. Roles and credentials - mint only for a real consumer

- [ ] Enumerate the serving roles the migrations created: records_api,
      records_intake_writer, records_auditor (owners records_owner /
      records_fn_owner are separate and stay non-login per Section 4).
- [ ] For EACH of the three serving roles, confirm whether a real consumer
      exists today (a named server component that will actually connect as
      that role - see the design spec section 3.4 for the intended DSN
      custody: records_api -> read-serving service, records_intake_writer ->
      intake/field-sync service, records_auditor -> compliance/audit-read
      service).
- [ ] **Mint a DSN/password ONLY for a role with a real consumer.** Do not
      pre-mint a dormant DSN/password for a role that has no consumer yet,
      unless the operator explicitly opts in to pre-minting (record that
      choice explicitly if made - it is a deviation from the default, not the
      default).
- [ ] A role with no real consumer at apply time stays exactly as the
      migrations left it (NOLOGIN, no password) - do not "get ahead" of the
      real consumer.
- [ ] For each role that DOES get a credential: set the password out-of-band
      (Vault/Padloc canonical custody, per the platform's secret custody
      model), never in-band in this packet, a migration, a chat transcript,
      or any command's visible argument list.
- [ ] Cache the password only in a 0600-permission file/secret store on the
      consuming component's host; never in shell history, never in a
      world/group-readable location.
- [ ] **ALTER any role the migrations created to NOLOGIN if it is not being
      given a real, minted credential in this apply.** Only the roles with a
      confirmed real consumer AND a minted credential become LOGIN.
- [ ] Confirm NO migration file sets a password (grep the applied migration
      SQL for password-setting clauses; expect zero matches - the migrations
      only create roles, they do not assign credentials).
- [ ] Confirm the owner roles (records_owner, records_fn_owner) remain NOLOGIN
      - they are never serving credentials and never get a DSN.

## 4. RLS and ownership posture

- [ ] Confirm FORCE ROW LEVEL SECURITY is set on every records table (not just
      RLS enabled - FORCE, so even the table owner is bound by policy).
- [ ] Confirm the three serving roles (records_api, records_intake_writer,
      records_auditor) are NOT owners of any records object - ownership sits
      with records_owner / records_fn_owner only.
- [ ] Confirm the three serving roles are NOBYPASSRLS (the Postgres default
      for newly created roles; verify empirically, do not assume default
      wasn't overridden anywhere in the migration stack).
- [ ] Confirm the two security-invoker views (v_asset_test_history, v_pm_due)
      are security_invoker = true, so RLS on their base tables binds through
      them with the querying serving role as current_user.

## 5. Data API exclusion (two independent gates - both required)

- [ ] **Platform config gate:** confirm records is NOT added to the Supabase
      Data API's exposed-schemas list (this is a project-settings check, not
      locally testable from SQL alone - verify directly against the target
      project's API settings).
- [ ] **Grants gate:** confirm there is no USAGE grant on schema records, and
      no table/view grant of any privilege on any records object, to any of:
      anon, authenticated, service_role, or PUBLIC.
- [ ] Because grants are checked before RLS, absence of a grant blocks even a
      BYPASSRLS role (service_role) at the grant layer - confirm this is true
      empirically for service_role against at least one records table (expect
      permission-denied, not an RLS-filtered empty result).
- [ ] Treat both gates as required together - passing one without the other is
      not sufficient (a missing exposed-schemas entry does not by itself
      guarantee no grant exists, and vice versa).

## 6. Fresh-role password encoding check

- [ ] For each freshly created LOGIN role (the serving roles that received a
      minted password in Section 3), confirm empirically that
      `rolpassword LIKE 'SCRAM-SHA-256%'` in pg_authid (or the project's
      equivalent inspection path) - NOT an md5-prefixed hash.
- [ ] This is documented as project/version-dependent (docs-ambiguous per the
      design spec) - verify per-project at apply time, do not assume from a
      prior project's behavior.
- [ ] If any fresh role encodes as md5, stop and resolve before proceeding
      (do not silently accept a weaker encoding).

## 7. Supabase security advisors

- [ ] Run the Supabase security advisors against the target project after the
      migration stack and role/credential steps above are complete.
- [ ] Review every advisor finding before accepting the apply as done (AC11).
      A finding is not automatically a blocker, but it must be explicitly
      reviewed and either resolved or consciously accepted with a documented
      reason - never silently ignored.
- [ ] Pay particular attention to any advisor finding touching: RLS
      enablement/force status, exposed-schema membership, anon/authenticated
      grants, or use of service_role-equivalent privilege - these overlap
      directly with Sections 4 and 5 above and should corroborate, not
      contradict, the manual checks.
- [ ] Capture the advisor run's summary in the apply-evidence transcript
      (Section 8) - value-silent (finding categories/counts, not raw
      credentials or connection strings).

## 8. Apply-evidence transcript (value-silent, committed)

Produce and commit a transcript recording, at minimum:

- [ ] **Pre-SHA:** the exact commit SHA of the branch/tag being applied
      (the reviewed migration stack's source commit), captured before the
      apply begins.
- [ ] **Pre-state:** empirical confirmation of prod's state immediately before
      apply (records schema absent/present, records_* role count, records
      Data-API exposure status) - re-verified at apply time, not assumed from
      an earlier read-only check.
- [ ] **Post-counts:** object counts after the migration stack lands (table
      count, view count, role count, policy count per table where
      practical) - enough to demonstrate the applied state matches the
      reviewed migration stack's expected shape.
- [ ] **Advisors:** the Section 7 security-advisor run summary and review
      disposition (accepted / resolved / deferred-with-reason per finding).
- [ ] **Value-silence discipline:** the transcript NEVER contains a real DSN,
      a real password, a real connection string, or any other live secret -
      use placeholders (e.g. `<REDACTED>`, `<ROLE_DSN>`) throughout, exactly
      as this packet does. If a command's output could contain a credential,
      the transcript records that the command was run and its outcome, not
      its raw output.
- [ ] Commit the completed transcript to the repository (docs/operations/,
      following the naming convention of prior gate evidence records, e.g.
      `RECORDS-GATE9-PROD-APPLY-EVIDENCE-<date>.md`) as part of the apply,
      not as part of this lane.

## 9. Rotation and recovery notes (carried from the design spec)

- [ ] Custom-role passwords are not auto-propagated by Supabase across
      project pause/restore or major-version upgrade - a manual password
      reset is required after either event. Note this in the runbook that
      accompanies the minted credentials so it is not rediscovered under
      pressure.
- [ ] Confirm which serving components hold which DSN (one DSN per role, per
      the design spec's custody model) before the apply is considered
      complete - a role with a minted credential but no confirmed holder is
      an open custody gap, not a finished step.

## 10. Honest scope (read before signing off)

Completing every step in this packet closes the non-superuser-owner RLS
bypass for records serving ONLY. It does this by ensuring the three serving
roles are non-owners, NOBYPASSRLS, and bound by FORCE RLS, and by keeping
records off the Data API surface entirely.

It does NOT make records serving "safe by enforcement" in an unqualified
sense. After this apply:

- The Postgres superuser (e.g. `postgres`) can still bypass RLS. This risk is
  not closed by this packet - it remains controlled by custody (superuser
  credentials are never minted or distributed as a records serving
  credential), by the secret-audit detector (Check 3, once armed, flags a
  superuser/owner/bypass-shaped credential in serving config), and by the
  startup identity assertion (a serving process, at startup, asserts
  session_user = current_user, both equal one of the three sanctioned roles,
  and that role is not rolsuper/rolbypassrls/an owner role).
- Supabase's `service_role` can still bypass RLS at the platform level. This
  packet's Section 5 keeps records out of `service_role`'s reachable surface
  (no grant, no Data API exposure) but does not and cannot revoke
  `service_role`'s inherent bypass capability - that is a platform-level
  property, not a records-schema property.
- Both of the above remain custody + detector + startup-assertion controlled,
  never enforcement-eliminated. Do not describe records serving as "safe by
  enforcement" without this qualification in any downstream summary,
  announcement, or status report.

## 11. Explicit non-goals of this packet

- This packet does not itself apply anything to prod. Authoring and
  committing it in the `records/gate9-supabase-serving` lane performs no
  mutation against any Supabase project.
- This packet does not cover Option A (Data API + JWT claims / browser
  consumer) - that remains a deferred future gate, designed only when a real
  browser records consumer exists.
- This packet does not widen `neta_table_source_links` access or add any new
  serving capability beyond the three sanctioned roles' existing Gate 5
  scope - any such widening is a new migration plus a SERVING_CONTRACT
  update, never a wider ad hoc Supabase role mapping applied under cover of
  this packet.
