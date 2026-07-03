# Records Gate 9 - Supabase Serving (Option B) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Option-B serving posture for records - server-side DSN as the
real least-privilege roles - as a validated, disposable-DB-proven package plus a
reviewed prod-variant apply packet, with zero prod mutation.

**Architecture:** Extend the existing Gate 5 validation substrate
(`run_validation.py` + `_dbtest.py`) with a serving-proof tier; rev the serving
contract to v2 (direct-role identity, killing the `supabase_target: authenticated`
false-green); widen + harden `secret-audit.sh` Check 3; add a session_user-based
startup identity assertion; and author a reviewed prod-variant apply packet. No
runtime code is added (no records browser/serving consumer exists yet).

**Tech Stack:** Python 3.11+ (system 3.12 on host), psycopg, pytest, bash, Postgres
15+ (local disposable `records_val_*` cluster via `RECORDS_PG_ADMIN_DSN`), the
`power-test-converters` + `records-import` editable installs.

Design spec (authoritative): `docs/superpowers/specs/2026-07-03-records-gate9-supabase-serving-design.md`
(rev 4). Scope note (superseded, provenance only):
`docs/superpowers/specs/2026-07-03-records-gate9-supabase-rebind-scope.md`.

## Global Constraints

- Never target `records_dev`. Disposable `records_val_*` DBs only; `_dbtest.guard_target`
  + `assert_val_name` enforce this - do not weaken them.
- No prod Supabase apply in this lane. The apply packet is produced + reviewed, NOT run.
- No migration or test sets a password. Owners stay NOLOGIN; serving-role passwords
  are out-of-band (Vault) at apply time.
- ASCII-only added lines (every added file line must be pure ASCII).
- Serving credentials = exactly {records_api, records_intake_writer, records_auditor}.
  Never service_role, postgres, records_owner, records_fn_owner, a BYPASSRLS role, or
  an sb_secret_* key.
- records is NOT exposed to the Data API; no effective records privilege via anon,
  authenticated, service_role, or PUBLIC (no schema USAGE, no table/view grant).
- Value-silent: never echo a DSN or a password in test output or logs.
- Every disposable-DB run must leave the shared cluster clean: extend `snapshot_roles`
  so the `[drop-role]` finally-block drops every stub role this run creates.
- Honest scope: this closes the non-superuser-owner RLS bypass only. Never describe
  records serving as "safe by enforcement" unqualified.

## File Structure

Created:
- `docs/operations/RECORDS-GATE9-EVIDENCE-2026-07.md` - AC1-AC12 evidence map (Task 6).
- `docs/operations/RECORDS-GATE9-PROD-APPLY-PACKET.md` - reviewed prod-variant apply
  checklist, NOT executed (Task 5).
- `infra/database/migrations/records/serving_identity.py` - `assert_serving_identity(conn)`
  reusable startup check (Task 3).
- `infra/database/migrations/records/test_serving_identity.py` - its proof (Task 3).

Modified:
- `reference/records/SERVING_CONTRACT.yaml` - v1 -> v2 direct-role identity (Task 1).
- `reference/records/SERVING_CONTRACT.md` - Gate-9 recipe rewrite for Option B (Task 1).
- `reference/records/test_serving_contract.py` - kill the false-green; assert v2 (Task 1).
- `infra/secret-audit.sh` - Check 3: 3-role allowlist + Supavisor form + uppercase
  PGUSER (Task 2).
- `infra/database/migrations/records/test_secret_audit_ac8.sh` - extend fixtures (Task 2).
- `infra/database/migrations/records/run_validation.py` - `snapshot_roles` +8 stub roles;
  new `tier7_serving`; wire into `main()` + `parse_tiers` (Task 4).

Provisioned (not committed):
- `apex-records-gate9/.venv` + `.env.dev` (Task 0).

---

### Task 0: Lane prep - venv, env, clean baseline

**Files:**
- Provision: `.venv` (worktree root), `.env.dev` (worktree root, 0600)
- No source changes; establishes the green baseline every later task builds on.

**Interfaces:**
- Produces: a runnable harness in this worktree - `python infra/database/migrations/records/run_validation.py --require-db` green (tiers 0-6), `test_serving_contract.py` green (v1), `test_secret_audit_ac8.sh` green.

- [ ] **Step 1: Provision the venv (do NOT copy gate5's .venv - it is path-bound).**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  python3 -m venv .venv && \
  ./.venv/bin/python -m pip install --upgrade pip && \
  ./.venv/bin/pip install -e packages/power-test-converters && \
  ./.venv/bin/pip install -e "packages/records-import[test]"'
```

- [ ] **Step 2: Provision `.env.dev` (value-silent copy from the gate5 worktree; operator-approved pattern).**

```bash
ssh olares-mesh 'install -m 600 /home/olares/code/apex/apex-records-gate5/.env.dev \
  /home/olares/code/apex/apex-records-gate9/.env.dev && \
  echo ".env.dev in place (0600)"'
```

- [ ] **Step 3: Baseline the harness unit tests + gate (must be green BEFORE any Gate 9 change).**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python -m pytest infra/database/migrations/records/test__dbtest_helper.py \
     infra/database/migrations/records/test_run_validation_unit.py -q && \
  ./.venv/bin/python -m pytest reference/records/test_serving_contract.py -q && \
  bash infra/database/migrations/records/test_secret_audit_ac8.sh && \
  ./.venv/bin/python infra/database/migrations/records/run_validation.py --require-db'
```
Expected: unit tests pass; contract test passes (v1); ac8 passes; validation gate tiers 0-6 PASS (0 SKIP under --require-db). If any tier SKIPs, stop and resolve env before proceeding.

- [ ] **Step 4: Record the baseline commit point.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && git rev-parse HEAD'
```
Note this SHA - it is the review-package BASE for Task 1.

---

### Task 1: Serving contract v2 (kill the `supabase_target: authenticated` false-green)

**Files:**
- Modify: `reference/records/test_serving_contract.py`
- Modify: `reference/records/SERVING_CONTRACT.yaml`
- Modify: `reference/records/SERVING_CONTRACT.md`

**Interfaces:**
- Consumes: the v1 contract + test (Task 0 baseline).
- Produces: contract v2 shape used by Task 2 (Supavisor form) and Task 6 (evidence):
  each `connects: true` role has `serving_transport: direct_role_dsn` and
  `connect_as: <role-name>`, no `supabase_target`; top-level `data_api_exposed: false`;
  `dsn_form_inventory` includes `supavisor_qualified_user`; new `api_views:
  [v_asset_test_history, v_pm_due]`.

- [ ] **Step 1: Write the failing test changes (TDD - test the v2 shape first).**

In `reference/records/test_serving_contract.py`, REPLACE `test_every_connecting_role_has_supabase_target`
with the v2 guard, and ADD a drift-rejection test:

```python
def test_every_connecting_role_has_direct_role_identity():
    # Gate 9 (Option B): connecting roles serve via a direct DSN authenticated AS
    # the role, NOT via a Supabase JWT/pooler role. Each must declare
    # serving_transport: direct_role_dsn and connect_as: <its own name>, and must
    # NOT declare supabase_target at all (that was the Option-A-shaped placeholder).
    doc = load_simple_yaml(YAML_PATH)
    roles = doc["roles"]
    assert roles, "roles map must not be empty"
    for name, spec in roles.items():
        if spec.get("connects") is True:
            assert spec.get("serving_transport") == "direct_role_dsn", (
                "connecting role %s must serve via direct_role_dsn" % name
            )
            assert spec.get("connect_as") == name, (
                "connecting role %s must connect_as itself, got %r"
                % (name, spec.get("connect_as"))
            )
            assert "supabase_target" not in spec, (
                "connecting role %s still declares supabase_target (Option-A drift)" % name
            )


def test_no_role_serves_via_authenticated_service_role_or_owner():
    # The drift guard: fail loudly if any role's serving identity regresses to a
    # Supabase built-in (authenticated/anon/service_role) or an owner role.
    doc = load_simple_yaml(YAML_PATH)
    forbidden_connect_as = {"records_owner", "records_fn_owner", "postgres",
                            "anon", "authenticated", "service_role"}
    for name, spec in doc["roles"].items():
        assert spec.get("supabase_target") in (None,), (
            "role %s must not declare supabase_target under Option B" % name
        )
        if spec.get("connects") is True:
            assert spec.get("connect_as") not in forbidden_connect_as, (
                "role %s connect_as is a forbidden identity: %r"
                % (name, spec.get("connect_as"))
            )
```

Update `test_yaml_parses_and_has_top_level_shape` to require version 2 and the new
top-level keys:

```python
def test_yaml_parses_and_has_top_level_shape():
    doc = load_simple_yaml(YAML_PATH)
    assert doc.get("version") == "2" or doc.get("version") == 2
    assert "roles" in doc and isinstance(doc["roles"], dict)
    assert "drm_boundary" in doc and isinstance(doc["drm_boundary"], dict)
    assert "dsn_form_inventory" in doc
    assert doc.get("data_api_exposed") is False, "records must declare data_api_exposed: false"
    assert "api_views" in doc, "contract must list api_views (records_api view scope)"
```

Update `test_every_non_connecting_role_is_owner_only_with_no_dsn` - the `supabase_target`
absence assertion still holds (owners never serve), so it needs no change; verify it
still passes. Update `test_dsn_form_inventory_has_expected_shapes` to require the new form:

```python
    expected = {
        "keyword_user",
        "url_userinfo",
        "url_driver_qualified",
        "pg_env_vars",
        "supavisor_qualified_user",
    }
```

- [ ] **Step 2: Run the tests - verify they FAIL against the v1 contract.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  ./.venv/bin/python -m pytest reference/records/test_serving_contract.py -q'
```
Expected: FAIL - v1 has `supabase_target`, `version: 1`, no `data_api_exposed`/`api_views`/`supavisor_qualified_user`.

- [ ] **Step 3: Rev `SERVING_CONTRACT.yaml` to v2.**

Keep the hand-rolled parser's constraints (block mappings only for role bodies - NO
`{ }` nested flow mappings; flow-style lists `[a, b]` are fine). New file body:

```yaml
version: 2
roles:
  records_api:
    connects: true
    serving_transport: direct_role_dsn
    connect_as: records_api
    write_scope: none
    tables_reachable: [ref_tables, wp_tables, api_views]
    policy_names: [p_<t>_read]
  records_intake_writer:
    connects: true
    serving_transport: direct_role_dsn
    connect_as: records_intake_writer
    write_scope: column_scoped
    tables_reachable: [ref_tables, wp_tables]
    policy_names: [p_<t>_read, p_<t>_ins, p_<t>_upd]
  records_auditor:
    connects: true
    serving_transport: direct_role_dsn
    connect_as: records_auditor
    write_scope: none
    tables_reachable: [audit_log]
    policy_names: [p_audit_log_sel]
  records_owner:
    connects: false
    owner_only: true
    dsn: none
  records_fn_owner:
    connects: false
    owner_only: true
    dsn: none
data_api_exposed: false
ref_tables: [asset_classes, form_templates, pm_programs, neta_procedures, neta_test_items, neta_tables, asset_class_neta_procedure, neta_procedure_xref]
wp_tables: [assets, form_submissions, form_field_values, pm_schedules, pm_events, persons]
api_views: [v_asset_test_history, v_pm_due]
owner_only_tables: [neta_table_source_links, audit_log]
drm_boundary:
  source_links_protects: lineage_provenance
  tolerance_values: first_class_record_content
dsn_form_inventory: [keyword_user, url_userinfo, url_driver_qualified, pg_env_vars, supavisor_qualified_user]
```

- [ ] **Step 4: Rewrite the `## Gate-9 rebind recipe` section of `SERVING_CONTRACT.md` for Option B.**

Replace the recipe (which currently says "bind to a Supabase connection identity ... authenticated for all three") with the direct-role recipe. Also flip the top "Status" note to record v2 and Option B. New recipe body:

```
## Gate-9 serving recipe (Option B, ratified 2026-07-03)

Serving connects SERVER-SIDE as the real least-privilege role over a direct or
Supavisor-session DSN - current_user = the role, so the Gate 5 `TO records_*`
policies apply natively. records is NOT exposed to the Data API.

1. For each `connects: true` role, mint one DSN authenticated AS that role
   (`connect_as`). Supavisor DSNs qualify the username as `<role>.<project_ref>`;
   the base role is still the sanctioned role.
2. Grant that role nothing beyond its existing Postgres grants - `write_scope` /
   `tables_reachable` are the ceiling. More access = a new migration + a contract
   update, never a wider identity mapping.
3. Never mint a DSN for `records_owner` or `records_fn_owner`. A perceived need to
   connect one is a design smell - re-open the Gate 5 posture decision.
4. Do NOT add `records` to the Data API exposed-schemas, and grant nothing to anon,
   authenticated, service_role, or PUBLIC. Point `RECORDS_SERVING_GLOBS` at the real
   serving config in the same change that introduces it (Check 3 arms then).
5. Re-run `test_serving_contract.py` after any change here.
```

- [ ] **Step 5: Run the tests - verify they PASS against v2, and ASCII holds.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  ./.venv/bin/python -m pytest reference/records/test_serving_contract.py -q && \
  for f in reference/records/SERVING_CONTRACT.yaml reference/records/SERVING_CONTRACT.md reference/records/test_serving_contract.py; do \
    LC_ALL=C grep -nP "[^\x00-\x7F]" "$f" && echo "NON-ASCII $f" || true; done'
```
Expected: all contract tests PASS; no non-ASCII lines.

- [ ] **Step 6: Commit.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  git add reference/records/SERVING_CONTRACT.yaml reference/records/SERVING_CONTRACT.md reference/records/test_serving_contract.py && \
  git diff --cached --check && \
  git commit -m "records(gate9): serving contract v2 - direct-role identity (kills supabase_target false-green)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

### Task 2: secret-audit Check 3 - 3-role allowlist + Supavisor form + uppercase PGUSER

**Files:**
- Modify: `infra/database/migrations/records/test_secret_audit_ac8.sh` (test first)
- Modify: `infra/secret-audit.sh` (Check 3 block only)

**Interfaces:**
- Consumes: contract v2's sanctioned-role set {records_api, records_intake_writer,
  records_auditor} and the `supavisor_qualified_user` form (Task 1).
- Produces: a Check 3 whose allowlist matches the contract (3 roles), parses the
  Supavisor `<role>.<project_ref>` username (exact base role, reject arbitrary dotted),
  and catches uppercase `PGUSER=`. Stays DORMANT by default (RECORDS_SERVING_GLOBS unset)
  so `test_secret_audit_check3_stays_dormant` (Task 1 file) still passes.

- [ ] **Step 1: Extend the ac8 self-test with the new fixtures (TDD).**

In `test_secret_audit_ac8.sh`, add fixtures built by runtime string concatenation
(never a live literal in the tracked file), following the existing pattern:

```bash
# --- NEW Gate 9 fixtures ---
# NEGATIVE (sanctioned) - records_auditor is now a sanctioned serving role.
auditor="user=""records_auditor"
# NEGATIVE (sanctioned) - Supavisor qualified username for a sanctioned base role.
supavisor_ok="user=""records_api"".""abcdefghijklmnop"
# POSITIVE (must FAIL) - Supavisor qualified username for a NON-sanctioned base role.
supavisor_bad="user=""postgres"".""abcdefghijklmnop"
# POSITIVE (must FAIL) - uppercase env-var form naming a non-app role.
pguser_bad="PGUSER=""records_owner"
```

Add assertions: with `RECORDS_SERVING_GLOBS` pointed at a temp dir containing the two
NEGATIVE fixtures (auditor keyword-form + Supavisor-OK), Check 3 must NOT flag them
(exit 0 for that group); with the two POSITIVE fixtures (supavisor_bad, pguser_bad),
Check 3 must exit 1 and print `records-serving-non-app-role`. Keep the value-silent
assertion (no planted VALUE appears in captured output) for every new fixture.

- [ ] **Step 2: Run ac8 - verify it FAILS against the current Check 3.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  bash infra/database/migrations/records/test_secret_audit_ac8.sh; echo "rc=$?"'
```
Expected: FAIL - current Check 3 flags `records_auditor` as non-app (not in the 2-role
allowlist), does not parse the Supavisor dot-form, and misses uppercase `PGUSER=`.

- [ ] **Step 3: Update the Check 3 block in `infra/secret-audit.sh`.**

Changes to the block (see the verbatim current block in the substrate map):

1. Update the header comment + `say` line to name all three sanctioned roles and drop
   the stale "AC8"-only framing.
2. Widen the sanctioned-role alternation in BOTH the keyword-form negative filter (rule a)
   and the URL-form negative filter (rule c) from
   `(records_api|records_intake_writer)` to
   `(records_api|records_intake_writer|records_auditor)`.
3. Rule (a): make the keyword match case-insensitive for the KEY so uppercase
   `PGUSER=`/`PGROLE=` is caught - change `grep -rHInoE "(user|role)..."` to
   `grep -rHInoiE "(user|role)..."` (add `i`), and keep the value-role alternation
   case-sensitive by matching the exact role names (they are lowercase). Verify the
   negative filter still excludes the 3 sanctioned lowercase roles.
4. Add a Supavisor-form normalization for rule (a)/(c): a username of the shape
   `<base>.<ref>` is sanctioned iff `<base>` is exactly one of the three roles and
   `<ref>` is a bare `[a-z0-9]+` project-ref (no further dots). Implement by extending
   the negative-filter alternation to also accept
   `(records_api|records_intake_writer|records_auditor)\.[a-z0-9]+` as a sanctioned
   username value; anything else dotted (e.g. `postgres.<ref>`, `evil.<ref>`, or a
   multi-dotted user) falls through and is FLAGged.
5. Keep rule (b) (bypass literals sb_secret_/service_role/bypassrls) unchanged.
6. Keep the block gated on `[[ -n "${RECORDS_SERVING_GLOBS:-}" ]]` and the SKIP branch
   text `no RECORDS_SERVING_GLOBS set` intact (so Task 1's dormancy test still passes).

- [ ] **Step 4: Run ac8 - verify it PASSES; confirm dormancy + contract tests still green.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  bash infra/database/migrations/records/test_secret_audit_ac8.sh && \
  ./.venv/bin/python -m pytest reference/records/test_serving_contract.py::test_secret_audit_check3_stays_dormant -q && \
  LC_ALL=C grep -nP "[^\x00-\x7F]" infra/secret-audit.sh infra/database/migrations/records/test_secret_audit_ac8.sh && echo NON-ASCII || echo "ascii ok"'
```
Expected: ac8 PASS; dormancy test PASS; ASCII clean.

- [ ] **Step 5: Commit.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  git add infra/secret-audit.sh infra/database/migrations/records/test_secret_audit_ac8.sh && \
  git diff --cached --check && \
  git commit -m "records(gate9): Check 3 - 3-role allowlist + Supavisor form + uppercase PGUSER

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

### Task 3: session_user startup identity assertion

**Files:**
- Create: `infra/database/migrations/records/serving_identity.py`
- Create: `infra/database/migrations/records/test_serving_identity.py`

**Interfaces:**
- Produces: `assert_serving_identity(conn, sanctioned=("records_api",
  "records_intake_writer", "records_auditor"))` - raises `ServingIdentityError` unless
  session_user == current_user, that role is in `sanctioned`, and it is NOT rolsuper,
  NOT rolbypassrls, and not an owner role. A serving process calls this before serving.

- [ ] **Step 1: Write the failing test.**

`test_serving_identity.py` - proves pass + the four fail modes, using SET SESSION
AUTHORIZATION (genuine-login simulation) and SET ROLE (the attack). Uses `_dbtest.dsn()`
(self-skips if no DB):

```python
import os, sys
import psycopg
import pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dbtest  # noqa: E402
from serving_identity import assert_serving_identity, ServingIdentityError  # noqa: E402


def _conn():
    return psycopg.connect(_dbtest.dsn())


def test_pass_when_authenticated_as_sanctioned_role():
    with _conn() as c, c.cursor() as cur:
        cur.execute("set session authorization records_api")  # session_user==current_user==records_api
        assert_serving_identity(c)  # must not raise
        cur.execute("reset session authorization")


def test_fail_on_set_role_masking_privileged_login():
    with _conn() as c, c.cursor() as cur:
        cur.execute("set role records_api")  # session_user stays the (super)login; current_user=records_api
        with pytest.raises(ServingIdentityError):
            assert_serving_identity(c)
        cur.execute("reset role")


def test_fail_on_superuser():
    with _conn() as c:
        with pytest.raises(ServingIdentityError):
            assert_serving_identity(c)  # connecting identity is the walk superuser


def test_fail_on_owner_role():
    with _conn() as c, c.cursor() as cur:
        cur.execute("set session authorization records_owner")
        with pytest.raises(ServingIdentityError):
            assert_serving_identity(c)
        cur.execute("reset session authorization")
```

- [ ] **Step 2: Run - verify it FAILS (module/function missing).**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python -m pytest infra/database/migrations/records/test_serving_identity.py -q'
```
Expected: FAIL - `serving_identity` module does not exist.

- [ ] **Step 3: Implement `serving_identity.py`.**

```python
"""Serving-time identity guard for records (Gate 9, Option B).

A records serving process authenticates AS a sanctioned least-privilege role over
a direct/Supavisor-session DSN. This asserts that invariant before serving:
session_user == current_user (no SET ROLE masking a privileged login), the role is
sanctioned, and it is not a superuser, not BYPASSRLS, and not an owner role. It does
NOT prove the absence of a privileged credential elsewhere - that stays a custody +
secret-audit concern.
"""

OWNER_ROLES = ("records_owner", "records_fn_owner")


class ServingIdentityError(Exception):
    pass


def assert_serving_identity(conn, sanctioned=("records_api", "records_intake_writer",
                                              "records_auditor")):
    with conn.cursor() as cur:
        cur.execute(
            "select session_user, current_user, "
            "  (select rolsuper from pg_roles where rolname = current_user), "
            "  (select rolbypassrls from pg_roles where rolname = current_user)"
        )
        session_user, current_user_, is_super, is_bypass = cur.fetchone()
    if session_user != current_user_:
        raise ServingIdentityError(
            "session_user (%r) != current_user (%r): a SET ROLE is masking the login"
            % (session_user, current_user_)
        )
    if current_user_ not in sanctioned:
        raise ServingIdentityError("identity %r is not a sanctioned serving role" % current_user_)
    if current_user_ in OWNER_ROLES:
        raise ServingIdentityError("identity %r is an owner role" % current_user_)
    if is_super:
        raise ServingIdentityError("identity %r is a superuser" % current_user_)
    if is_bypass:
        raise ServingIdentityError("identity %r has BYPASSRLS" % current_user_)
```

- [ ] **Step 4: Run - verify PASS + ASCII.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python -m pytest infra/database/migrations/records/test_serving_identity.py -q && \
  LC_ALL=C grep -nP "[^\x00-\x7F]" infra/database/migrations/records/serving_identity.py infra/database/migrations/records/test_serving_identity.py && echo NON-ASCII || echo "ascii ok"'
```
Expected: 4 tests PASS; ASCII clean.

- [ ] **Step 5: Commit.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  git add infra/database/migrations/records/serving_identity.py infra/database/migrations/records/test_serving_identity.py && \
  git diff --cached --check && \
  git commit -m "records(gate9): session_user startup identity assertion

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

### Task 4: Serving-matrix harness tier (`tier7_serving`)

**Files:**
- Modify: `infra/database/migrations/records/run_validation.py`

**Interfaces:**
- Consumes: the disposable-DB lifecycle, `snapshot_roles`, and the `expect_raise` /
  `SET SESSION AUTHORIZATION` idiom (tier5/tier6).
- Produces: a `tier7-serving` tier proving the Option-B matrix, wired into `parse_tiers`
  + `main()`, and a `snapshot_roles` whose `names` include the three Supabase stub roles
  so they are dropped after the run.

- [ ] **Step 1: Extend `snapshot_roles` to track the stub roles (so `[drop-role]` cleans them).**

Change the default `names` tuple:
```python
def snapshot_roles(admin, names=("records_api", "records_intake_writer",
                                 "records_owner", "records_fn_owner", "records_auditor",
                                 "anon", "authenticated", "service_role")):
```
(The finally-block already drops only roles absent before the run; the stubs `tier7`
creates will be dropped after the DB drop. Owners/fn_owner still drop only after the DB.)

- [ ] **Step 2: Write `tier7_serving` (the tier IS the test; it self-validates with negative controls).**

Model it on `tier5_roles`/`tier6_posture` - open one autocommit-free psycopg connection
as the walk superuser, use savepoints, `SET SESSION AUTHORIZATION <role>` for the
positive scope and `expect_raise(cur, sql, label, sqlstate='42501')` for denials. Create
the three Supabase stubs first (service_role WITH BYPASSRLS to faithfully simulate
Supabase), seed a join-satisfying fixture so the two views return under records_api, then
prove:

```python
def tier7_serving(child_dsn):
    """Prove the Gate 9 Option-B serving matrix on the disposable DB."""
    fails = []
    with _connect_txn(child_dsn) as (conn, cur):   # non-autocommit; see tier5 helper
        # --- create Supabase stubs, guarded (plain Postgres has no CREATE ROLE IF
        #     NOT EXISTS). snapshot_roles() records which were absent pre-run so the
        #     finally-block drops exactly the ones THIS run created. service_role gets
        #     BYPASSRLS to faithfully simulate Supabase. ---
        cur.execute("""
            do $$ begin
              if not exists (select 1 from pg_roles where rolname='anon') then create role anon nologin; end if;
              if not exists (select 1 from pg_roles where rolname='authenticated') then create role authenticated nologin; end if;
              if not exists (select 1 from pg_roles where rolname='service_role') then create role service_role nologin bypassrls; end if;
            end $$;
        """)

        # --- AC2: no records reachability for anon/authenticated/service_role/PUBLIC ---
        for role in ("anon", "authenticated", "service_role"):
            cur.execute("savepoint s")
            cur.execute(f"set session authorization {role}")
            # grants are checked before RLS; even service_role (BYPASSRLS) is denied absent a grant
            expect_raise(cur, "select 1 from records.assets limit 1",
                         f"7-{role}-assets-denied", fails, sqlstate="42501")
            expect_raise(cur, "select 1 from records.v_asset_test_history limit 1",
                         f"7-{role}-view-denied", fails, sqlstate="42501")
            expect_raise(cur, "select 1 from records.audit_log limit 1",
                         f"7-{role}-audit-denied", fails, sqlstate="42501")
            expect_raise(cur, "select 1 from records.neta_table_source_links limit 1",
                         f"7-{role}-source-links-denied", fails, sqlstate="42501")
            cur.execute("reset session authorization")
            cur.execute("rollback to savepoint s")
        # PUBLIC must hold no grant on any records table/view.
        cur.execute("""select count(*) from information_schema.role_table_grants
                       where table_schema='records' and grantee='PUBLIC'""")
        if cur.fetchone()[0] != 0:
            fails.append("7-public-grant: PUBLIC holds a grant on a records object")

        # --- AC4: records_api reads 14 tables + 2 views, writes nothing ---
        # seed a join-satisfying row set as admin so the views return under records_api.
        _seed_view_fixture(cur)   # inserts one asset + submission so v_asset_test_history/v_pm_due are non-empty
        cur.execute("savepoint s")
        cur.execute("set session authorization records_api")
        cur.execute("select count(*) from records.assets")               # allowed
        cur.execute("select count(*) from records.v_asset_test_history") # allowed (view in scope)
        cur.execute("select count(*) from records.v_pm_due")             # allowed
        expect_raise(cur, "insert into records.assets(asset_tag,name) values('x','y')",
                     "7-api-no-write", fails, sqlstate="42501")
        expect_raise(cur, "select 1 from records.neta_table_source_links limit 1",
                     "7-api-no-source-links", fails, sqlstate="42501")
        expect_raise(cur, "select 1 from records.audit_log limit 1",
                     "7-api-no-audit", fails, sqlstate="42501")
        cur.execute("reset session authorization")
        cur.execute("rollback to savepoint s")

        # --- AC5: records_intake_writer - col-scoped writes, no DELETE, NO views ---
        cur.execute("savepoint s")
        cur.execute("set session authorization records_intake_writer")
        cur.execute("select count(*) from records.assets")               # allowed read
        expect_raise(cur, "select 1 from records.v_asset_test_history limit 1",
                     "7-writer-no-view", fails, sqlstate="42501")
        expect_raise(cur, "select 1 from records.neta_table_source_links limit 1",
                     "7-writer-no-source-links", fails, sqlstate="42501")
        expect_raise(cur, "delete from records.persons where false",
                     "7-writer-no-delete", fails, sqlstate="42501")
        cur.execute("reset session authorization")
        cur.execute("rollback to savepoint s")

        # --- AC6: records_auditor - audit_log only ---
        cur.execute("savepoint s")
        cur.execute("set session authorization records_auditor")
        cur.execute("select count(*) from records.audit_log")            # allowed
        expect_raise(cur, "select 1 from records.assets limit 1",
                     "7-auditor-no-tables", fails, sqlstate="42501")
        expect_raise(cur, "select 1 from records.v_pm_due limit 1",
                     "7-auditor-no-view", fails, sqlstate="42501")
        expect_raise(cur, "select 1 from records.neta_table_source_links limit 1",
                     "7-auditor-no-source-links", fails, sqlstate="42501")
        cur.execute("reset session authorization")
        cur.execute("rollback to savepoint s")

        # --- AC7: audit_log append-only for serving roles ---
        cur.execute("savepoint s")
        cur.execute("set session authorization records_auditor")
        expect_raise(cur, "update records.audit_log set action=action",
                     "7-audit-no-update", fails, sqlstate="42501")
        expect_raise(cur, "delete from records.audit_log where false",
                     "7-audit-no-delete", fails, sqlstate="42501")
        cur.execute("reset session authorization")
        cur.execute("rollback to savepoint s")

        conn.rollback()   # discard the view fixture + all savepoint work
    if fails:
        return Tier("7-serving", "FAIL", "; ".join(fails))
    return Tier("7-serving", "PASS", "Option-B serving matrix proven (AC2/4/5/6/7/8)")
```
Reuse the file's existing `expect_raise` helper if present; if tier5 inlines it, extract
a shared `expect_raise(cur, sql, label, fails, sqlstate="42501")` helper and have tier5
use it too (DRY - but do not change tier5's assertions). `_connect_txn` = the non-autocommit
connect helper tier5/tier6 already use; reuse it. `_seed_view_fixture` inserts the minimal
rows the two views join over (inspect the view defs in 004/044-era migrations for the exact
columns) so records_api's positive read returns > 0 rows (a view that errors or is empty
would not prove reachability).

- [ ] **Step 3: Wire `tier7_serving` into `parse_tiers` and `main()`.**

Add `"7-serving"` (or `"7"`) to the valid tier set in `parse_tiers`, add it to the default
run set, and call it in `main()`'s DB-tier dispatch right after `tier6_posture(child_dsn)`,
appending its `Tier(...)` to `tiers`.

- [ ] **Step 4: Add a unit assertion that tier7 is registered (mirrors `test_run_validation_unit.py`).**

Add a case to `test_run_validation_unit.py` asserting `parse_tiers` accepts `7-serving`
and that `main`'s tier list includes it, so a future refactor cannot silently drop it.

- [ ] **Step 5: Run the full gate - tier7 must PASS, and prove it is not a no-op.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python -m pytest infra/database/migrations/records/test_run_validation_unit.py -q && \
  ./.venv/bin/python infra/database/migrations/records/run_validation.py --require-db'
```
Expected: unit test PASS; gate tiers 0-7 PASS, 0 SKIP. Confirm `[drop-role]` lines include
anon/authenticated/service_role (stubs cleaned). If tier7 passes even with a deliberately
broken assertion (temporarily), it is a no-op - fix the proof, do not accept a green no-op.

- [ ] **Step 6: Verify cluster residue is clean (roles + no leaked DBs).**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python - <<PY
import os, psycopg
admin=os.environ["RECORDS_PG_ADMIN_DSN"]
with psycopg.connect(admin, autocommit=True) as c:
    r=c.execute("select count(*) from pg_roles where rolname in ('anon','authenticated','service_role','records_api','records_intake_writer','records_auditor','records_owner','records_fn_owner')").fetchone()[0]
    d=c.execute("select count(*) from pg_database where datname like 'records_val_%'").fetchone()[0]
    print("residue_roles=%d residue_val_dbs=%d" % (r,d))
PY'
```
Expected: `residue_roles=0 residue_val_dbs=0` (value-silent - no DSN echoed).

- [ ] **Step 7: Commit.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  git add infra/database/migrations/records/run_validation.py infra/database/migrations/records/test_run_validation_unit.py && \
  git diff --cached --check && \
  git commit -m "records(gate9): tier7 serving-matrix proof (Option-B AC2/4/5/6/7/8)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

### Task 5: Prod-variant apply packet (reviewed, NOT applied)

**Files:**
- Create: `docs/operations/RECORDS-GATE9-PROD-APPLY-PACKET.md`

**Interfaces:**
- Consumes: the spec's section 7 + the contract v2 role set.
- Produces: a reviewed operator checklist; nothing is executed against prod in this lane.

- [ ] **Step 1: Author the packet.** ASCII. It is a checklist, not a runnable script. Include, each as an operator-checkable line:
  - Land the records migration stack 001-049 (first-ever prod landing) as reviewable SQL.
  - Ensure the three serving roles have LOGIN + out-of-band (Vault) passwords; ALTER any created NOLOGIN; no password in any migration.
  - Confirm FORCE RLS on every records table; confirm the three roles are non-owners.
  - Confirm records is NOT in the Data API exposed-schemas; no anon/authenticated/service_role/PUBLIC grant on any records object.
  - SCRAM-SHA-256 prefix check (`rolpassword like 'SCRAM-SHA-256%'`) on the fresh roles - verify not md5.
  - Run Supabase security advisors (security); review before accept (AC11).
  - Value-silent apply-evidence transcript: pre-SHA / post-object-counts / advisors, committed per the apply-evidence standard.
  - Explicit gate: NO apply proceeds without operator sign-off; this lane only produces this packet.

- [ ] **Step 2: ASCII check + commit.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  LC_ALL=C grep -nP "[^\x00-\x7F]" docs/operations/RECORDS-GATE9-PROD-APPLY-PACKET.md && echo NON-ASCII || true && \
  git add docs/operations/RECORDS-GATE9-PROD-APPLY-PACKET.md && git diff --cached --check && \
  git commit -m "records(gate9): reviewed prod-variant apply packet (not applied)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

### Task 6: Full validation gate + Gate 9 evidence doc

**Files:**
- Create: `docs/operations/RECORDS-GATE9-EVIDENCE-2026-07.md`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: the AC1-AC12 evidence map + a captured green transcript; the merge-readiness artifact.

- [ ] **Step 1: Run the complete gate green + capture the transcript (value-silent).**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python -m pytest infra/database/migrations/records/test__dbtest_helper.py \
     infra/database/migrations/records/test_run_validation_unit.py \
     infra/database/migrations/records/test_serving_identity.py \
     reference/records/test_serving_contract.py -q && \
  bash infra/database/migrations/records/test_secret_audit_ac8.sh && \
  ./.venv/bin/python infra/database/migrations/records/run_validation.py --require-db'
```
Expected: all green; tiers 0-7 PASS, 0 SKIP; `[drop-role]` cleans all stubs.

- [ ] **Step 2: Author `RECORDS-GATE9-EVIDENCE-2026-07.md`** mapping AC1-AC12 to the exact
  proof (file:test/tier), quoting the residue-clean transcript (roles 0 / val_dbs 0), and
  stating the honest-scope caveat + the "no prod apply in this lane" bound verbatim.

- [ ] **Step 3: ASCII check + commit.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  LC_ALL=C grep -nP "[^\x00-\x7F]" docs/operations/RECORDS-GATE9-EVIDENCE-2026-07.md && echo NON-ASCII || true && \
  git add docs/operations/RECORDS-GATE9-EVIDENCE-2026-07.md && git diff --cached --check && \
  git commit -m "records(gate9): AC1-AC12 evidence map + green gate transcript

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

## Plan-review gate (before merge)

After Task 6, run the heavy IRP: whole-branch Claude review + Codex cross-engine pass
(`apex-jobs review-run --review-head records/gate9-supabase-serving --base-ref main --json`).
Fold confirmed findings, re-verify the gate, then finishing-a-development-branch. No prod
apply.
