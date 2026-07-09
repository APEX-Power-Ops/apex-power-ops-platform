# OPS prod-apply evidence -- G3 Step 1 (ops 001-012)

Target project: `fxoyniqnrlkxfligbxmg` (governed prod). Date: 2026-07-09.
Gate lineage: packet `docs/operations/OPS-PROD-APPLY-PACKET-G2-G3-2026-07-08.md` @ main `6ca1d4a2`;
G3 Step 0 drift gate PASS (2026-07-08); G3 Step 1 applied under a separate operator write GO.

This artifact is the durable record for Step 1 only. Steps 2-5 (role arming, login round-trip,
boundary/advisors, final reconciliation) remain separately operator-gated and are NOT covered here.

## 1. Mechanism (and a deliberate deviation)

Applied via host-side `psql --single-transaction -f` per file, ordered 001-011 (008 =
`008_core_equipment_models`; the ops_dev-only `008_apply_preflight` is excluded) then 012. This
deviates from the packet-default MCP `execute_sql`. Rationale, taken under the packet's pre-authorized
"file-atomic execution surface" clause:

- Byte fidelity. Five of the twelve files are 19-58 KB. Reproducing that DDL through a tool-argument
  round-trip cannot guarantee byte-identical submission; `psql -f` reads the exact file bytes.
  The migration bodies were therefore applied verbatim ("do not rewrite migration bodies").
- Transactionally identical. `--single-transaction` wraps each file in one transaction with
  `ON_ERROR_STOP=1` -- the same all-or-nothing behavior as the MCP one-request-per-file path (a
  multi-statement simple query is one implicit transaction). A failed statement or in-body assert
  rolls back the whole file.
- Same applier. The connection is the managed non-super `postgres` (confirmed below), identical to
  the applier the packet specifies.

Credential source: the current admin DSN is `SUPABASE_PROD_DSN` in **Infisical prod**
(`infra/infisical/inject.sh prod`), session-pooler host `aws-0-us-west-2.pooler.supabase.com:5432`,
user `postgres.fxoyniqnrlkxfligbxmg`, db `postgres`. The copy in host `infra/.env` is STALE (password
authentication fails); Infisical prod is the source of truth. Value-silent throughout: the password
travels only in `PGPASSWORD`, never on argv; the psql conninfo carries only non-secret host/port/user/db.

Verification below was run through the INDEPENDENT MCP channel (`bb4a07f4` governed connection), i.e.
apply = psql, verify = MCP -- two independent channels agreeing.

## 2. Pre-write guard (read-only, zero writes)

Immediately before the apply, over the same prod DSN:

- `current_database() = postgres`, `current_user = postgres`, `rolsuper = false`,
  `rolcreaterole = true`, `rolbypassrls = true` (expected managed admin).
- `to_regnamespace('ops') IS NULL` and `to_regnamespace('core') IS NULL` (both target schemas absent).
- `records_*` = 6 roles, all NOLOGIN (target-guard marker intact).

## 3. Pinned SHA manifest @ main 6ca1d4a2 (re-derived at write time)

All 12 applied files matched their Step-0 pin (012 and 012_down are byte-identical to the G1-proven
canonical):

```
39c82d6d56f07a2b23154500a80445d8be18aacf2b6c3af3b91108208de4edb0  001_identity_skeleton.sql
4368f16b947b48b05ccefb2f7311691cadfeac3c8401a77d93f4906cb59107dc  002_quote_model.sql
71e0ca27c8a968797be91297524093efdd11b141a39cd69d5ae14aa1ac0b0afa  003_intake_unique_keys.sql
7c00bd5f753cd193cdfc3e2b4dca95fc10421c4d4d060b3774cf72fc07484d33  004_person_anchor.sql
7b5643193641d3a49e63f860510f8ba397667288ed401660bd5af57d2026fd21  005_recognition_ledger.sql
c2d4fbef23e3745af08118eaed10f5db4d0cd904a7c5a0679778c2725722f477  006_progress_billing.sql
c44401b0387c9a22ecd145f82713bce4da00f17d45a4a01e4971b80a03ba9cfb  007_intake_envelope.sql
63064718d02dbac524145038088cae8a9633e412d14c4ff9670e0fdd83dac4e0  008_core_equipment_models.sql
a8c807206a2d47630568070ae4d6a84ed0fd9939c3bac1104bc0d8bc1fb6506a  009_recognition_bridge.sql
595bdfe7e447cfd4179c0c824cc5219e3dae7d80dae11f893b58336eb62f05ec  010_native_envelope_intake.sql
d1c160d88b06331a1640029d51618f673f34735edbe5403587bb7611d68084e9  011_scope_quote_line_description.sql
a31a65be3efd1aa56443834af0fd270c028f341023a03d68710ed8ef7854c436  012_ops_app_role_boundary.sql
```

## 4. Apply transcript (summary)

Each file applied with `rc=0`, terminating in `ALL_APPLIED`. Two benign, expected messages:

- `004`: `NOTICE: schema "ops" already exists, skipping` (001 created it; 004 uses `if not exists`).
- `012`: two `WARNING: role "ops_intake_writer"/"ops_api" has not been granted membership in role
  "ops_fn_owner" by role "postgres"` -- the defensive membership-revoke posture step revoking a
  membership that was never granted. 012's own in-body posture asserts did not raise, and the
  end-state (zero serving-role membership) is confirmed in section 5.

## 5. Verification (independent MCP channel)

### Structural fingerprint

| schema | views | tables | functions | SECDEF |
|--------|-------|--------|-----------|--------|
| ops    | 11    | 16     | 28        | 9      |
| core   | 1     | 1      | 0         | 0      |

Operator fingerprint (11 views / 28 functions / 9 SECDEF) matches the ops schema exactly. The 12th
view across ops+core is core's supporting `v_equipment_models_resolved`. `supabase_migrations` count
= 198, UNCHANGED (psql apply writes no migration-history rows; acceptance is evidence/MANIFEST-governed
by design).

### SECURITY DEFINER functions (9, all owned by ops_fn_owner, search_path = ops, pg_temp)

```
ops.approve_and_recognize
ops.attest_apparatus_complete
ops.discard_draft_billing_application
ops.issue_billing_application            (two overloads)
ops.record_billing_application
ops.reverse_recognition
ops.revoke_completion_attestation
ops.void_billing_application
```

### Roles

| role               | login | super | bypassrls | passwordless |
|--------------------|-------|-------|-----------|--------------|
| ops_api            | true  | false | false     | true         |
| ops_intake_writer  | true  | false | false     | true         |
| ops_fn_owner       | false | false | false     | n/a (NOLOGIN)|

Passwordless confirmed via `pg_shadow.passwd IS NULL` for both serving roles -- they are created LOGIN
but unusable until Step 2 arming. No login was attempted.

### ops_fn_owner membership (trusted-applier edge)

Members of `ops_fn_owner` = `postgres` ONLY, via two grant records:

- creation-membership, `granted_by = supabase_admin`, `set_option = false`, `inherit_option = false`
  (automatic when a non-super role creates a role in PG16+);
- A2 self-grant, `granted_by = postgres`, `set_option = true`, `inherit_option = true` (the managed
  ownership-transfer path; SET-capable).

`ops_api` and `ops_intake_writer` hold ZERO membership in `ops_fn_owner` (no SET ROLE path for serving
roles). The retained `postgres -> ops_fn_owner` edge is the ratified trusted-applier edge (012 `[1a]`
posture assert exempts `current_user`); it grants no privilege beyond what admin `postgres` already
holds and is not a serving path. "No memberships" means no serving-role memberships.

### Boundary spot-check

Writer can insert `ops.intake_runs` but cannot execute `attest_apparatus_complete`. API can read the
recognition worklist and execute recognition SECDEF but cannot insert `apparatus`/`scopes` or execute
billing. `apparatus.status` is denied to the writer; API provenance update is denied. ops/core PUBLIC
EXECUTE count = 0.

### Advisors

Zero ERROR-level advisors touch ops or core in either report. Security: 173 lints / 62 ERROR, all in
OTHER schemas (chiefly `public`) and pre-existing, not introduced by this apply; ops exposure = 19
`function_search_path_mutable` WARN on base (non-SECDEF) functions (tracked follow-up). Performance:
0 ERROR; ops/core exposure is INFO-level index hygiene only (unindexed FKs, unused indexes).

### Records dormancy intact

`records_*` = 6 total / 0 LOGIN / 6 NOLOGIN, unchanged. Ops migrations touch no records migration and
no `records_*` role; ops Step 1 did not disturb the records substrate's GO#3 dormant posture.

## 6. Cross-engine confirmation

Two independent post-apply reviews (one repo-evidence-only, one live read-only prod) agreed with this
record on every count: the ops/core fingerprint, migration-history = 198, role posture, the boundary
spot-check, the trusted-applier edge, the stale `infra/.env` note, and records dormancy intact.

## 7. State after Step 1

- Prod `fxoyniqnrlkxfligbxmg` now holds `ops` and `core` (ops 001-012 LIVE).
- Serving roles `ops_api` / `ops_intake_writer` exist LOGIN but passwordless -- NOT armed.
- No login as a serving role was attempted. No serving secret was armed. No records role was altered.
- Next: G3 Step 2 (value-silent psql role arming) under a separate explicit operator write GO.
