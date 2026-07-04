# Records Gate 9 - Supabase Serving (Option B) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Option-B serving posture for records - server-side DSN as the
real least-privilege roles - as a validated, disposable-DB-proven package plus a
reviewed prod-variant apply packet, with zero prod mutation.

**Architecture:** Extend the Gate 5 validation substrate (`run_validation.py` +
`_dbtest.py`) with a serving-proof tier (tier 7); rev the serving contract to v2
(direct-role identity, killing the `supabase_target: authenticated` false-green);
widen + harden `secret-audit.sh` Check 3; add a session_user-based startup identity
assertion (proven both by a DB-free unit test and live in tier 7); and author a
reviewed prod-variant apply packet. No runtime code is added.

**Tech Stack:** Python 3.11+ (system 3.12 on host), psycopg, pytest, bash, Postgres
15+ (local disposable `records_val_*` cluster via `RECORDS_PG_ADMIN_DSN`), the
`power-test-converters` + `records-import` editable installs.

Design spec (authoritative): `docs/superpowers/specs/2026-07-03-records-gate9-supabase-serving-design.md`
(rev 4).

## Rev 3 (plan-review fold #2, 2026-07-03)

Folds the operator's rev-2 review (4 findings) + a Task-0 credential-parse pre-check
learned from a live env-provisioning failure:
- tier7 grant matrix is now a FULL role x object x op cross-product driven from the
  contract expected-privilege matrix (every serving AND Data-API role, every object incl.
  views/owner-only, all 4 ops) - not partial per-class checks.
- Writer column scope is now a FULL per-column matrix on all 6 write-path tables (every
  actual column: granted -> true, every other -> false), which also proves the grant is
  column-scoped not table-wide.
- Check 3: the KEY (user/role/pguser) is matched case-insensitively but the sanctioned-role
  VALUE stays exact-lowercase, so an uppercase/mixed-case role value (PGUSER=RECORDS_API,
  records_API.ref) is FLAGGED; no single global grep -i.
- Residue check is a real snapshot-before / run / snapshot-after / compare-exact-sets.
- Task 0 adds a credential-parse pre-check: verify the admin DSN parses cleanly via
  dsn_params (all keys, password matches env, no surviving quotes, psql-path auth) BEFORE
  the baseline, so a quoted/mangled DSN fails fast with a clear message.

## Rev 2 (plan-review fold, 2026-07-03)

Folds the plan-review (operator + Codex + Claude IRP Workflow). Architecture
unchanged; all fixes are in the proof/harness-wiring layer:
- tier 7 redesigned around exhaustive `has_*_privilege` catalog assertions (fixes:
  representative-sampling false-green, PUBLIC via wrong info-schema view, missing
  schema-USAGE check, column-scope coverage) + a tier-local `expect_denied` helper
  that asserts `sqlstate == '42501'` + live view `count > 0` reachability.
- tier 7 wiring made exhaustive: ALL integer tier-set sites updated (parse_tiers
  144/149/151, db_wanted mask 707, full-run guard 718, dispatch 741-764) and the
  existing parse_tiers unit assertions updated (they currently assert `parse_tiers("7")`
  RAISES).
- AC10 no longer relies on a skippable DB test: a DB-free unit test always runs, and
  tier 7 proves it live under `--require-db`.
- Check 3 Supavisor parsing fixed (widen rule-(a) capture to include `.`, match the
  full dotted username exactly, reject multi-dot) + uppercase-PGUSER exclusion filter
  made key-case-insensitive; evidence-split documented.
- `SERVING_CONTRACT.md` fully rewritten (invariant table + role->target + view scope +
  dsn inventory), not just the recipe.
- Residue check uses a before/after role-set delta, not an absolute zero.
- Every ASCII check fails closed (`if grep ...; then exit 1; fi`).

## Global Constraints

- Never target `records_dev`. Disposable `records_val_*` DBs only; `_dbtest.guard_target`
  + `assert_val_name` enforce this - do not weaken them.
- No prod Supabase apply in this lane. The apply packet is produced + reviewed, NOT run.
- No migration or test sets a password. Owners stay NOLOGIN; serving-role passwords are
  out-of-band (Vault) at apply time.
- ASCII-only added lines. Every ASCII check FAILS CLOSED: `if LC_ALL=C grep -nP
  "[^\x00-\x7F]" "$F"; then echo NON-ASCII; exit 1; fi` - never `grep && echo || echo ok`.
- Serving credentials = exactly {records_api, records_intake_writer, records_auditor}.
  Never service_role, postgres, records_owner, records_fn_owner, a BYPASSRLS role, or
  an sb_secret_* key.
- records is NOT exposed to the Data API; no effective records privilege via anon,
  authenticated, service_role, or PUBLIC (no schema USAGE, no table/view grant).
- Value-silent: never echo a DSN or a password in test output or logs.
- Every disposable-DB run leaves the shared cluster clean: `snapshot_roles` tracks the
  stub roles so the `[drop-role]` finally-block drops exactly what the run created.
- Honest scope: this closes the non-superuser-owner RLS bypass only. Never describe
  records serving as "safe by enforcement" unqualified.

## File Structure

Created:
- `docs/operations/RECORDS-GATE9-EVIDENCE-2026-07.md` - AC1-AC12 evidence map (Task 6).
- `docs/operations/RECORDS-GATE9-PROD-APPLY-PACKET.md` - reviewed prod-variant apply
  checklist, NOT executed (Task 5).
- `infra/database/migrations/records/serving_identity.py` - `assert_serving_identity(conn)`
  reusable startup check (Task 3).
- `infra/database/migrations/records/test_serving_identity_unit.py` - DB-free unit proof
  (Task 3), always runs.

Modified:
- `reference/records/SERVING_CONTRACT.yaml` - v1 -> v2 direct-role identity (Task 1).
- `reference/records/SERVING_CONTRACT.md` - full rewrite for Option B (Task 1).
- `reference/records/test_serving_contract.py` - kill the false-green; assert v2 (Task 1).
- `infra/secret-audit.sh` - Check 3: 3-role allowlist + Supavisor form + uppercase PGUSER (Task 2).
- `infra/database/migrations/records/test_secret_audit_ac8.sh` - extend fixtures (Task 2).
- `infra/database/migrations/records/run_validation.py` - `snapshot_roles` +3 stub roles;
  new `tier7_serving`; ALL tier-set sites + dispatch (Task 4).
- `infra/database/migrations/records/test_run_validation_unit.py` - update the parse_tiers
  assertions for tier 7 (Task 4).

Provisioned (not committed): `apex-records-gate9/.venv` + `.env.dev` (Task 0).

---

### Task 0: Lane prep - venv, env, clean baseline

**Files:** Provision `.venv` + `.env.dev`; no source changes.

**Interfaces:**
- Produces: a runnable harness - `run_validation.py --require-db` green (tiers 0-6),
  `test_serving_contract.py` green (v1), `test_secret_audit_ac8.sh` green.

- [ ] **Step 1: Provision the venv (do NOT copy gate5's .venv - it is path-bound).**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  python3 -m venv .venv && ./.venv/bin/python -m pip install --upgrade pip && \
  ./.venv/bin/pip install -e packages/power-test-converters && \
  ./.venv/bin/pip install -e "packages/records-import[test]"'
```

- [ ] **Step 2: Provision `.env.dev` (value-silent copy; operator-approved pattern).**

```bash
ssh olares-mesh 'install -m 600 /home/olares/code/apex/apex-records-gate5/.env.dev \
  /home/olares/code/apex/apex-records-gate9/.env.dev && echo ".env.dev in place (0600)"'
```

- [ ] **Step 3: Credential-parse pre-check (fail fast on a quoted/mangled DSN).**

The harness's `_child_env` re-derives the psql password from the admin DSN via the naive
`_dbtest.dsn_params` regex, which does NOT strip quotes like libpq. A DSN value with
surviving quotes (e.g. nested `'"..."'`) yields a wrong psql password and a confusing
tier-3 failure while psycopg still connects. Verify the parse is clean BEFORE the baseline
(value-silent - booleans only):

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python - <<'"'"'PY'"'"'
import os, sys, subprocess
sys.path.insert(0, "infra/database/migrations/records"); import _dbtest
p = _dbtest.dsn_params(os.environ["RECORDS_PG_ADMIN_DSN"])
dp = p.get("password") or ""; ep = os.environ.get("RECORDS_DEV_PGPASSWORD") or ""
env = {**os.environ, "PGSSLMODE": "disable"}; env.pop("PGPASSWORD", None); env["PGPASSWORD"] = dp
rc = subprocess.run([_dbtest.psql_exe(), "-h", p.get("host","127.0.0.1"), "-p", p.get("port","5432"),
                     "-U", p.get("user","postgres"), "-d", p["dbname"], "-tAc", "select 1"],
                    capture_output=True, text=True, env=env).returncode
ok = (rc == 0 and dp == ep and not any(c in dp for c in " \x27\x22")
      and sorted(p.keys()) == ["dbname","host","password","port","sslmode","user"])
print("cred_parse_clean:", ok)
sys.exit(0 if ok else 1)
PY'
```
Expected: `cred_parse_clean: True`. If False, the admin DSN in `.env.dev` has surviving
quotes or a field mismatch - the operator fixes it to a single-layer-quoted keyword DSN
(`RECORDS_PG_ADMIN_DSN="host=127.0.0.1 port=5432 dbname=postgres user=postgres password=<pw> sslmode=disable"`
- one layer of quotes, no nesting) before proceeding. Never edit the credential value blindly.

- [ ] **Step 4: Baseline (must be green BEFORE any Gate 9 change).**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python -m pytest infra/database/migrations/records/test__dbtest_helper.py \
     infra/database/migrations/records/test_run_validation_unit.py -q && \
  ./.venv/bin/python -m pytest reference/records/test_serving_contract.py -q && \
  bash infra/database/migrations/records/test_secret_audit_ac8.sh && \
  ./.venv/bin/python infra/database/migrations/records/run_validation.py --require-db'
```
Expected: all green; tiers 0-6 PASS, 0 SKIP. Any SKIP under `--require-db` = stop and fix env.

- [ ] **Step 5: Record the baseline SHA** (`git rev-parse HEAD`) - it is the review-package BASE for Task 1.

---

### Task 1: Serving contract v2 (kill the `supabase_target: authenticated` false-green)

**Files:** Modify `reference/records/test_serving_contract.py`, `SERVING_CONTRACT.yaml`, `SERVING_CONTRACT.md`.

**Interfaces:**
- Produces: contract v2 - each `connects: true` role has `serving_transport: direct_role_dsn`
  + `connect_as: <role>`, no `supabase_target`; top-level `data_api_exposed: false`;
  `api_views: [v_asset_test_history, v_pm_due]`; `dsn_form_inventory` includes
  `supavisor_qualified_user`.

- [ ] **Step 1: Write the failing test changes (TDD).** In `test_serving_contract.py`,
REPLACE `test_every_connecting_role_has_supabase_target` and ADD the drift guard:

```python
def test_every_connecting_role_has_direct_role_identity():
    doc = load_simple_yaml(YAML_PATH)
    for name, spec in doc["roles"].items():
        if spec.get("connects") is True:
            assert spec.get("serving_transport") == "direct_role_dsn", name
            assert spec.get("connect_as") == name, (name, spec.get("connect_as"))
            assert "supabase_target" not in spec, name


def test_no_role_serves_via_authenticated_service_role_or_owner():
    doc = load_simple_yaml(YAML_PATH)
    forbidden = {"records_owner", "records_fn_owner", "postgres", "anon",
                 "authenticated", "service_role"}
    for name, spec in doc["roles"].items():
        assert spec.get("supabase_target") is None, name
        if spec.get("connects") is True:
            assert spec.get("connect_as") not in forbidden, (name, spec.get("connect_as"))
```

Update `test_yaml_parses_and_has_top_level_shape` to require `version` 2, `data_api_exposed`
is False, and `api_views` present. Update `test_dsn_form_inventory_has_expected_shapes`
`expected` to add `"supavisor_qualified_user"`. Leave
`test_every_non_connecting_role_is_owner_only_with_no_dsn` and
`test_known_roles_present_with_expected_connect_posture` unchanged (verify they still pass).

- [ ] **Step 2: Run - verify FAIL against v1.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && ./.venv/bin/python -m pytest reference/records/test_serving_contract.py -q'
```

- [ ] **Step 3: Rev `SERVING_CONTRACT.yaml` to v2.** Keep block-mapping role bodies (the
hand-rolled parser rejects `{ }` nested flow mappings); flow-style lists `[a, b]` are fine.

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

- [ ] **Step 4: FULLY rewrite `SERVING_CONTRACT.md` for Option B (not just the recipe).**
Every v1 statement that maps connecting roles to `authenticated`, or omits the view scope,
must be corrected. Specifically:
  - Flip the top `Status` line to v2 / Option B (server-side direct-role DSN).
  - Rewrite the "The invariant" role->target table so all three connecting roles show
    `serving_transport: direct_role_dsn` + `connect_as`, not `supabase_target: authenticated`.
  - Add `records_api`'s view read-scope (v_asset_test_history, v_pm_due) to the per-table
    listing; state the writer/auditor do NOT get the views.
  - Update the DSN-form list to include the Supavisor `<role>.<project_ref>` form.
  - Replace the "Gate-9 rebind recipe" with the direct-role recipe (records off the Data
    API; grant nothing to anon/authenticated/service_role/PUBLIC; arm RECORDS_SERVING_GLOBS
    with the serving config; never mint an owner DSN).
Grep the file for `authenticated` and `supabase_target` after editing - zero matches
except where explicitly documenting the DEPRECATED Option-A path.

- [ ] **Step 5: Run + fail-closed ASCII, then commit.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  ./.venv/bin/python -m pytest reference/records/test_serving_contract.py -q && \
  for f in reference/records/SERVING_CONTRACT.yaml reference/records/SERVING_CONTRACT.md reference/records/test_serving_contract.py; do \
    if LC_ALL=C grep -nP "[^\x00-\x7F]" "$f"; then echo "NON-ASCII $f"; exit 1; fi; done && \
  ! grep -nE "supabase_target|: authenticated" reference/records/SERVING_CONTRACT.yaml && \
  git add reference/records/SERVING_CONTRACT.yaml reference/records/SERVING_CONTRACT.md reference/records/test_serving_contract.py && \
  git diff --cached --check && \
  git commit -m "records(gate9): serving contract v2 - direct-role identity (kills supabase_target false-green)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

### Task 2: secret-audit Check 3 - 3-role allowlist + Supavisor dotted-user + uppercase PGUSER

**Files:** Modify `test_secret_audit_ac8.sh` (test first), then `infra/secret-audit.sh` (Check 3).

**Interfaces:**
- Produces: a Check 3 whose allowlist matches the contract (3 roles), captures the FULL
  username (including dots) then sanctions only exact `<role>` or `<role>.<ref>` (single
  dot), rejects multi-dotted/unsanctioned bases, and is key-case-insensitive so uppercase
  `PGUSER=records_api` is NOT falsely flagged. Stays DORMANT by default.

- [ ] **Step 1: Extend `test_secret_audit_ac8.sh` with the new fixtures (TDD).** Build every
signature by runtime concatenation (never a live literal in the tracked file). Add:

```bash
auditor="user=""records_auditor"                 # NEGATIVE (sanctioned, 3rd role)
supavisor_ok="user=""records_api"".""abcdefghijklmnop"   # NEGATIVE (sanctioned base.ref)
supavisor_multidot="user=""records_api"".""evil"".""postgres"  # POSITIVE (multi-dot masking - must FAIL)
supavisor_badbase="user=""postgres"".""abcdefghijklmnop"       # POSITIVE (non-sanctioned base - must FAIL)
pguser_ok="PGUSER=""records_api"              # NEGATIVE (sanctioned, uppercase key - must NOT flag)
pguser_bad="PGUSER=""records_owner"           # POSITIVE (owner via uppercase key - must FAIL)
pguser_upper="PGUSER=""RECORDS_API"           # POSITIVE (uppercase role VALUE - must FAIL)
supavisor_mixed="user=""records_API"".""abcdefgh"   # POSITIVE (mixed-case role value - must FAIL)
```
Assert: the four NEGATIVE fixtures do NOT trip Check 3 (exit 0 for that group); the three
POSITIVE fixtures exit 1 with `records-serving-non-app-role`. Keep the value-silent
assertion (no planted VALUE in captured output) for each.

- [ ] **Step 2: Run ac8 - verify FAIL against current Check 3.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && bash infra/database/migrations/records/test_secret_audit_ac8.sh; echo "rc=$?"'
```
Expected: FAIL - current Check 3 flags `records_auditor` (2-role allowlist), truncates the
Supavisor username at the first dot (so `records_api.evil.postgres` passes), and mis-handles
uppercase `PGUSER=`.

- [ ] **Step 3: Update the Check 3 block in `infra/secret-audit.sh`.** Changes:
  1. Header comment + `say` line: name all THREE sanctioned roles; add an evidence-split
     note: "Check 3 detects config-shape + literal bypass tokens; live BYPASSRLS on an
     otherwise-sanctioned role is proven separately by assert_serving_identity (Task 3),
     which Check 3 cannot see from static config."
  2. Rule (a) match regex: (i) make ONLY the KEY case-insensitive via explicit character
     classes - `[Uu][Ss][Ee][Rr]`, `[Rr][Oo][Ll][Ee]`, `[Pp][Gg][Uu][Ss][Ee][Rr]`,
     `[Pp][Gg][Rr][Oo][Ll][Ee]` - NOT a global `grep -i` (a global `-i` case-folds the value
     too and would wrongly sanction `PGUSER=RECORDS_API`); (ii) widen the value capture class
     from `[A-Za-z0-9_]+` to `[A-Za-z0-9_.]+` so the FULL dotted username is captured, not
     truncated at the first dot.
  3. Rule (a) negative (allowlist) filter: same case-insensitive KEY classes, and match the
     WHOLE username value with a LITERAL-LOWERCASE role alternation:
     `(records_api|records_intake_writer|records_auditor)(\.[a-z0-9]+)?` anchored to the end of
     the value token. This sanctions a bare sanctioned role and a single `<role>.<ref>`
     (ref = `[a-z0-9]+`, no further dots) - while `records_api.evil.postgres`, `postgres.<ref>`,
     any non-sanctioned base, AND any uppercase/mixed-case role value (`RECORDS_API`,
     `records_API.ref`) fall through and are FLAGGED. Never case-fold the value.
  4. Rule (c) URL-form: same 3-role widening + same `<role>.<ref>` sanctioning; keep
     value-silent (stop before the password).
  5. Rule (b) (sb_secret_/service_role/bypassrls literals): unchanged.
  6. Keep the block gated on `[[ -n "${RECORDS_SERVING_GLOBS:-}" ]]` and the SKIP text
     `no RECORDS_SERVING_GLOBS set` intact (Task 1's dormancy test depends on it).

- [ ] **Step 4: Run ac8 + dormancy + fail-closed ASCII.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  bash infra/database/migrations/records/test_secret_audit_ac8.sh && \
  ./.venv/bin/python -m pytest reference/records/test_serving_contract.py::test_secret_audit_check3_stays_dormant -q && \
  for f in infra/secret-audit.sh infra/database/migrations/records/test_secret_audit_ac8.sh; do \
    if LC_ALL=C grep -nP "[^\x00-\x7F]" "$f"; then echo "NON-ASCII $f"; exit 1; fi; done'
```
Expected: ac8 PASS; dormancy PASS; ASCII clean.

- [ ] **Step 5: Commit** (`git add infra/secret-audit.sh infra/database/migrations/records/test_secret_audit_ac8.sh`, `git diff --cached --check`, commit `records(gate9): Check 3 - 3-role allowlist + full Supavisor dotted-user parsing + uppercase PGUSER`).

---

### Task 3: session_user startup identity assertion (DB-free unit proof; live proof in tier 7)

**Files:** Create `serving_identity.py` + `test_serving_identity_unit.py`.

**Interfaces:**
- Produces: `assert_serving_identity(conn, sanctioned=("records_api",
  "records_intake_writer", "records_auditor"))` raising `ServingIdentityError` unless
  session_user == current_user, the role is sanctioned, and it is NOT rolsuper, NOT
  rolbypassrls, and not an owner role. Consumed live by tier 7 (Task 4).

- [ ] **Step 1: Write the failing DB-FREE unit test** (always runs; no skip). It feeds the
function a fake connection whose cursor returns controlled `(session_user, current_user,
is_super, is_bypass)` rows, exercising all branches without a database:

```python
import os, sys
import pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serving_identity import assert_serving_identity, ServingIdentityError  # noqa: E402


class _FakeCur:
    def __init__(self, row): self._row = row
    def execute(self, *a, **k): pass
    def fetchone(self): return self._row
    def __enter__(self): return self
    def __exit__(self, *a): return False


class _FakeConn:
    def __init__(self, row): self._row = row
    def cursor(self): return _FakeCur(self._row)


def test_pass_sanctioned():
    assert_serving_identity(_FakeConn(("records_api", "records_api", False, False)))


def test_fail_set_role_masks_login():
    with pytest.raises(ServingIdentityError):
        assert_serving_identity(_FakeConn(("postgres", "records_api", True, False)))


def test_fail_superuser():
    with pytest.raises(ServingIdentityError):
        assert_serving_identity(_FakeConn(("postgres", "postgres", True, False)))


def test_fail_bypassrls():
    with pytest.raises(ServingIdentityError):
        assert_serving_identity(_FakeConn(("service_role", "service_role", False, True)))


def test_fail_owner_role():
    with pytest.raises(ServingIdentityError):
        assert_serving_identity(_FakeConn(("records_owner", "records_owner", False, False)))


def test_fail_unsanctioned():
    with pytest.raises(ServingIdentityError):
        assert_serving_identity(_FakeConn(("some_role", "some_role", False, False)))
```

- [ ] **Step 2: Run - verify FAIL** (module missing). `./.venv/bin/python -m pytest infra/database/migrations/records/test_serving_identity_unit.py -q`.

- [ ] **Step 3: Implement `serving_identity.py`.**

```python
"""Serving-time identity guard for records (Gate 9, Option B)."""

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
        session_user, cur_user, is_super, is_bypass = cur.fetchone()
    if session_user != cur_user:
        raise ServingIdentityError(
            "session_user (%r) != current_user (%r): a SET ROLE is masking the login"
            % (session_user, cur_user))
    if cur_user not in sanctioned:
        raise ServingIdentityError("identity %r is not a sanctioned serving role" % cur_user)
    if cur_user in OWNER_ROLES:
        raise ServingIdentityError("identity %r is an owner role" % cur_user)
    if is_super:
        raise ServingIdentityError("identity %r is a superuser" % cur_user)
    if is_bypass:
        raise ServingIdentityError("identity %r has BYPASSRLS" % cur_user)
```

- [ ] **Step 4: Run - verify PASS + fail-closed ASCII.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  ./.venv/bin/python -m pytest infra/database/migrations/records/test_serving_identity_unit.py -q && \
  for f in infra/database/migrations/records/serving_identity.py infra/database/migrations/records/test_serving_identity_unit.py; do \
    if LC_ALL=C grep -nP "[^\x00-\x7F]" "$f"; then echo "NON-ASCII $f"; exit 1; fi; done'
```
Expected: 6 tests PASS; ASCII clean. (The LIVE four-fail-mode proof runs in tier 7 under
`--require-db`, so AC10 cannot be recorded green via a skip.)

- [ ] **Step 5: Commit** (`records(gate9): session_user startup identity assertion + DB-free unit proof`).

---

### Task 4: tier 7 serving-matrix proof + exhaustive tier wiring

**Files:** Modify `run_validation.py` and `test_run_validation_unit.py`.

**Interfaces:**
- Consumes: the disposable-DB lifecycle, `snapshot_roles`, the tier5/tier6 inline
  `psycopg.connect(child_dsn)` idiom (there is NO `_connect_txn` helper - do not reference
  one), `assert_serving_identity` (Task 3), and contract v2's object lists.
- Produces: `tier7_serving(child_dsn)` returning a `Tier("7-serving", ...)`, wired into
  EVERY integer tier-set site + the unit assertions.

- [ ] **Step 1: Extend `snapshot_roles` default `names`** to add the three stubs so the
finally-block drops them:

```python
def snapshot_roles(admin, names=("records_api", "records_intake_writer",
                                 "records_owner", "records_fn_owner", "records_auditor",
                                 "anon", "authenticated", "service_role")):
```

- [ ] **Step 2: Add `tier7_serving`.** Model the connection on tier5_roles (line ~327:
`conn = psycopg.connect(child_dsn)` then `cur = conn.cursor()`, autocommit off). Define a
tier-LOCAL `expect_denied` that asserts the SPECIFIC `42501` sqlstate (not "any error") -
do NOT reuse or refactor tier5/tier6's nested `expect_raise`. The core proof is exhaustive
`has_*_privilege` catalog assertions (deterministic, fixture-free, driven from the FULL
contract object lists - this is what makes it exhaustive and fixes the PUBLIC/USAGE gaps),
plus targeted live probes. Skeleton:

```python
REF = ["asset_classes", "form_templates", "pm_programs", "neta_procedures",
       "neta_test_items", "neta_tables", "asset_class_neta_procedure", "neta_procedure_xref"]
WP = ["assets", "form_submissions", "form_field_values", "pm_schedules", "pm_events", "persons"]
VIEWS = ["v_asset_test_history", "v_pm_due"]
OWNER_ONLY = ["neta_table_source_links", "audit_log"]
DATA_API_ROLES = ["anon", "authenticated", "service_role"]  # real roles; each INHERITS PUBLIC grants


def tier7_serving(child_dsn):
    fails = []
    conn = psycopg.connect(child_dsn)   # autocommit=False, matches tier5/tier6
    try:
        cur = conn.cursor()
        # stubs, guarded (no CREATE ROLE IF NOT EXISTS in Postgres); snapshot_roles cleans up.
        cur.execute("""
            do $$ begin
              if not exists (select 1 from pg_roles where rolname='anon') then create role anon nologin; end if;
              if not exists (select 1 from pg_roles where rolname='authenticated') then create role authenticated nologin; end if;
              if not exists (select 1 from pg_roles where rolname='service_role') then create role service_role nologin bypassrls; end if;
            end $$;""")

        def hasp(role, obj, priv):
            cur.execute("select has_table_privilege(%s, %s, %s)", (role, "records." + obj, priv))
            return cur.fetchone()[0]

        def has_schema(role):
            cur.execute("select has_schema_privilege(%s, 'records', 'USAGE')", (role,))
            return cur.fetchone()[0]

        def want(cond, label):
            if not cond:
                fails.append(label)

        # --- EXHAUSTIVE ACL EXACTNESS: full role x object x op matrix ---
        # Drive EVERY (role, object, op) from the contract's expected-privilege matrix and
        # assert has_table_privilege == expected - catching BOTH leaked and missing grants on
        # ANY object class (ref/wp/views/owner-only) for EVERY serving and Data-API role.
        allobjs = REF + WP + VIEWS + OWNER_ONLY
        SERVING = ["records_api", "records_intake_writer", "records_auditor"]
        ALL_ROLES = SERVING + DATA_API_ROLES   # DATA_API_ROLES = anon/authenticated/service_role

        def expected_ops(role, obj):
            if role == "records_api":
                return {"SELECT"} if obj in REF + WP + VIEWS else set()
            if role == "records_intake_writer":
                if obj in WP:
                    return {"SELECT", "INSERT", "UPDATE"}   # column-scoped writes; never DELETE
                if obj in REF:
                    return {"SELECT"}
                return set()                                 # views + owner-only: nothing
            if role == "records_auditor":
                return {"SELECT"} if obj == "audit_log" else set()
            return set()                                     # anon/authenticated/service_role: nothing

        for role in ALL_ROLES:
            for obj in allobjs:
                exp = expected_ops(role, obj)
                for op in ("SELECT", "INSERT", "UPDATE", "DELETE"):
                    want(hasp(role, obj, op) == (op in exp),
                         "7-acl-%s-%s-%s-want-%s" % (role, obj, op, op in exp))

        # Schema USAGE: serving roles need it; Data-API roles must NOT have it.
        for role in SERVING:
            want(has_schema(role), "7-usage-missing-" + role)
        for role in DATA_API_ROLES:
            want(not has_schema(role), "7-usage-leak-" + role)

        # PUBLIC (pseudo-role, grantee OID 0): direct nspacl + relacl check.
        # (has_*_privilege cannot take 'public'; role_table_grants omits PUBLIC by design.)
        cur.execute("select count(*) from pg_namespace n, lateral aclexplode(n.nspacl) a "
                    "where n.nspname='records' and a.grantee = 0")
        want(cur.fetchone()[0] == 0, "7-public-schema-usage")
        cur.execute("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace, "
                    "lateral aclexplode(c.relacl) a where n.nspname='records' and a.grantee = 0")
        want(cur.fetchone()[0] == 0, "7-public-object-grant")

        # --- COLUMN-SCOPE EXACTNESS (AC5): FULL per-column matrix on the 6 write-path tables ---
        # Build the expected granted-column set per WP table from 045's column grants (source of
        # truth), then assert has_column_privilege for EVERY actual column of the table:
        # granted -> True, every other column (reserved / trigger-maintained / owner) -> False.
        # A table-wide grant would make a reserved column True and fail here, so this also proves
        # the grant is column-scoped, not broad. GRANTED_COLS below is transcribed from 045 - the
        # implementer MUST re-verify each list against 045_records_security_rls.sql.
        GRANTED_COLS = {
            "assets": ["asset_tag", "name", "asset_class_id", "parent_asset_id", "site_ref",
                       "client_ref", "location_label", "region", "jobsite", "plant", "substation",
                       "gps_lat", "gps_long", "manufacturer", "model", "serial_number",
                       "rated_voltage", "rated_current", "year_manufactured", "last_tested_at",
                       "apparatus_ref", "equipment_model_id", "source", "provenance_status",
                       "legacy_source_id", "notes"],
            "form_submissions": ["template_id", "asset_id", "project_ref", "work_package_ref",
                       "pm_event_id", "overall_assessment", "as_found_as_left", "test_status_label",
                       "job_number", "test_date", "technician", "ambient_temp_c", "relative_humidity",
                       "test_equipment", "summary_notes", "source", "provenance_status",
                       "legacy_source_id", "origin_device", "client_rev", "client_captured_at",
                       "synced_at", "neta_standard", "technician_person_id"],
            "form_field_values": ["form_submission_id", "field_key", "field_label", "test_group",
                       "sequence_no", "value_kind", "value_numeric", "value_text", "value_boolean",
                       "unit", "expected_value", "min_acceptable", "max_acceptable", "measured_at",
                       "notes", "origin_device", "client_rev", "client_captured_at", "synced_at"],
            "pm_schedules": ["pm_program_id", "asset_id", "last_performed_at", "next_due_at",
                       "is_active", "notes"],
            "pm_events": ["pm_schedule_id", "asset_id", "scheduled_for", "performed_at",
                       "form_submission_id", "project_ref", "outcome", "notes", "origin_device",
                       "client_rev", "client_captured_at", "synced_at"],
            "persons": ["display_name"]}
        for tbl in WP:
            cur.execute("select column_name from information_schema.columns "
                        "where table_schema='records' and table_name=%s", (tbl,))
            actual_cols = [r[0] for r in cur.fetchall()]
            granted = set(GRANTED_COLS[tbl])
            for col in actual_cols:
                for op in ("INSERT", "UPDATE"):
                    cur.execute("select has_column_privilege('records_intake_writer', %s, %s, %s)",
                                ("records." + tbl, col, op))
                    want(cur.fetchone()[0] == (col in granted),
                         "7-col-%s.%s-%s-want-%s" % (tbl, col, op, col in granted))

        # --- LIVE BEHAVIORAL PROBES (prove the RLS+grant chain, not just the ACL) ---
        cur.execute("savepoint s")
        _seed_view_fixture(cur)   # one asset+template+submission and one active pm_schedule+program
        cur.execute("set session authorization records_api")
        for v in VIEWS:
            cur.execute("select count(*) from records." + v)
            if cur.fetchone()[0] < 1:
                fails.append("7-view-empty-" + v)   # reachability must return the seeded row
        cur.execute("reset session authorization")
        cur.execute("rollback to savepoint s")
        # service_role (BYPASSRLS) is still blocked at the GRANT layer absent a grant.
        cur.execute("savepoint s")
        cur.execute("set session authorization service_role")
        expect_denied(cur, "select 1 from records.assets limit 1", "7-service_role-grant-layer", fails)
        cur.execute("reset session authorization")
        cur.execute("rollback to savepoint s")
        # AC10 live: assert_serving_identity passes as a sanctioned role and fails the 4 modes.
        _prove_serving_identity(cur, conn, fails)   # SET SESSION AUTHORIZATION pass; SET ROLE / super / owner fail
        conn.rollback()
    finally:
        conn.close()
    if fails:
        return Tier("7-serving", "FAIL", "; ".join(sorted(set(fails))))
    return Tier("7-serving", "PASS", "Option-B serving matrix proven exhaustively (AC1-AC10)")
```
`expect_denied(cur, sql, label, fails)`: run `sql`; if it does NOT raise, append `label`;
if it raises `psycopg.errors.Error` with `sqlstate != "42501"`, append `label + "-wrong-sqlstate"`;
a `42501` is the only pass. `_seed_view_fixture(cur)`: insert (as the walk superuser) the
minimal join-satisfying rows for both views - one `asset_classes` (if FK-required) + one
`assets` + one `form_templates` + one `form_submissions` (joins v_asset_test_history), and
one `pm_programs` + one `pm_schedules` with `is_active=true` (joins v_pm_due) - so each view
returns >= 1 row; consult migration 004 (view defs) + the base-table NOT NULL constraints.
`_prove_serving_identity(cur, conn, fails)`: `set session authorization records_api` ->
`assert_serving_identity` must not raise; then prove it RAISES for `set role records_api`
(from the superuser session), plain superuser, and `set session authorization records_owner`;
`reset` after each; use a nested savepoint per probe.

- [ ] **Step 3: Wire tier 7 into EVERY integer tier-set site** (grounded line numbers):
  - `parse_tiers` (lines 144, 149, 151): `{0,1,2,3,4,5,6}` -> `{0,1,2,3,4,5,6,7}`; error text `0-6` -> `0-7`.
  - db-tier mask (line 707): `db_wanted = wanted & {3, 4, 5, 6}` -> `& {3, 4, 5, 6, 7}`.
  - full-run guard (line 718): `if wanted != {0, 1, 2, 3, 4, 5, 6}:` -> `!= {0, 1, 2, 3, 4, 5, 6, 7}`.
  - dispatch (after the `6 in db_wanted` block, ~line 761): add
    ```python
    if 7 in db_wanted and not any(t.name == "3-migrations" and t.status == "FAIL" for t in tiers):
        if 3 in db_wanted or args.db_dsn:
            tiers.append(tier7_serving(child_dsn))
        else:
            tiers.append(Tier("7-serving", "SKIP", "needs tier 3 or --db-dsn"))
    elif 7 in db_wanted:
        tiers.append(Tier("7-serving", "SKIP", "tier 3 failed"))
    ```
  Note `--only` is INT-parsed (`int(x)`), so the tier id is the integer `7` (there is no
  `"7-serving"` token in `--only`); the Tier NAME string is `"7-serving"`.

- [ ] **Step 4: Update the parse_tiers unit assertions** in `test_run_validation_unit.py`
(they currently assert tier 7 is INVALID):
  - line 81 + 87: `{0, 1, 2, 3, 4, 5, 6}` -> `{0, 1, 2, 3, 4, 5, 6, 7}`.
  - line 94: `parse_tiers("7")` currently expected to RAISE -> change to `assert rv.parse_tiers("7") == {7}`.
  - line 95-96: keep an unknown-tier rejection but move the boundary: `rv.parse_tiers("9")`
    (or `"8"`) still raises; update the `match=` text from `tiers 0-6` to `0-7`.
  - Add: `assert rv.parse_tiers("7") == {7}` and confirm `parse_tiers("")` includes 7.

- [ ] **Step 5: Run the full gate - tier 7 PASS, 0 SKIP, and prove it dispatched.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python -m pytest infra/database/migrations/records/test_run_validation_unit.py -q && \
  ./.venv/bin/python infra/database/migrations/records/run_validation.py --require-db 2>&1 | tee /tmp/g9gate.txt; \
  grep -qE "7-serving.*PASS" /tmp/g9gate.txt && echo "TIER7 RAN + PASSED" || { echo "TIER7 MISSING/FAILED"; exit 1; }'
```
Expected: unit PASS; gate tiers 0-7 PASS, 0 SKIP; the grep proves tier 7 actually appears in
the summary (guards against the "never dispatched" false-green). Do NOT accept a green gate
whose summary lacks a `7-serving` line. Sanity: temporarily break one tier7 assertion and
confirm the gate FAILS (not a no-op), then revert.

- [ ] **Step 6: Residue check - snapshot before, run the gate, snapshot after, compare.**

One command does the before-snapshot, the gate run, the after-snapshot, and the comparison
(value-silent):

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python - <<'"'"'PY'"'"'
import os, subprocess, psycopg
admin = os.environ["RECORDS_PG_ADMIN_DSN"]
names = ("anon","authenticated","service_role","records_api","records_intake_writer",
         "records_auditor","records_owner","records_fn_owner")
def snap():
    with psycopg.connect(admin, autocommit=True) as c:
        return {r[0] for r in c.execute("select rolname from pg_roles where rolname = any(%s)",
                                        (list(names),)).fetchall()}
before = snap()
rc = subprocess.run(["./.venv/bin/python",
                     "infra/database/migrations/records/run_validation.py", "--require-db"]).returncode
after = snap()
with psycopg.connect(admin, autocommit=True) as c:
    vd = c.execute("select count(*) from pg_database where datname like 'records_val_%'").fetchone()[0]
print("gate_rc:", rc)
print("role_set_delta_empty:", before == after)
print("leaked_roles:", sorted(after - before))
print("residue_val_dbs:", vd)
PY'
```
Expected: `gate_rc: 0`, `role_set_delta_empty: True`, `leaked_roles: []`, `residue_val_dbs: 0`.
The harness drops only the roles IT created, so the correct invariant is delta == 0 (the
pre-existing set unchanged), NOT absolute zero on a shared cluster. Value-silent.

- [ ] **Step 7: Commit** (`run_validation.py` + `test_run_validation_unit.py`; `records(gate9): tier7 exhaustive serving-matrix proof + full tier wiring`).

---

### Task 5: Prod-variant apply packet (reviewed, NOT applied)

**Files:** Create `docs/operations/RECORDS-GATE9-PROD-APPLY-PACKET.md`.

- [ ] **Step 1: Author the packet** (ASCII; a checklist, not a runnable script):
  - Land records migration stack 001-049 (first-ever prod landing) as reviewable SQL.
  - **DSNs/passwords are minted only for a role with a REAL consumer.** Do not pre-mint a
    dormant DSN/password unless the operator explicitly chooses to; a role with no consumer
    gets no credential. Passwords out-of-band (Vault), 0600 caches; ALTER any role the
    migrations created NOLOGIN; no password in any migration.
  - Confirm FORCE RLS on every records table; confirm the three serving roles are non-owners.
  - Confirm records is NOT in the Data API exposed-schemas; no anon/authenticated/service_role/PUBLIC grant on any records object.
  - SCRAM-SHA-256 prefix check on the fresh roles (`rolpassword like 'SCRAM-SHA-256%'`) - not md5.
  - Run Supabase security advisors; review before accept (AC11).
  - Value-silent apply-evidence transcript (pre-SHA / post-counts / advisors), committed.
  - Gate: NO apply without operator sign-off; this lane only produces this packet.

- [ ] **Step 2: Fail-closed ASCII + commit.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && \
  if LC_ALL=C grep -nP "[^\x00-\x7F]" docs/operations/RECORDS-GATE9-PROD-APPLY-PACKET.md; then echo NON-ASCII; exit 1; fi && \
  git add docs/operations/RECORDS-GATE9-PROD-APPLY-PACKET.md && git diff --cached --check && \
  git commit -m "records(gate9): reviewed prod-variant apply packet (not applied)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

### Task 6: Full validation gate + Gate 9 evidence doc

**Files:** Create `docs/operations/RECORDS-GATE9-EVIDENCE-2026-07.md`.

- [ ] **Step 1: Run the complete gate green + capture (value-silent).**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python -m pytest infra/database/migrations/records/test__dbtest_helper.py \
     infra/database/migrations/records/test_run_validation_unit.py \
     infra/database/migrations/records/test_serving_identity_unit.py \
     reference/records/test_serving_contract.py -q && \
  bash infra/database/migrations/records/test_secret_audit_ac8.sh && \
  ./.venv/bin/python infra/database/migrations/records/run_validation.py --require-db'
```
Expected: all green; tiers 0-7 PASS, 0 SKIP; `[drop-role]` cleans the stubs.

- [ ] **Step 2: Author `RECORDS-GATE9-EVIDENCE-2026-07.md`** mapping AC1-AC12 to the exact
proof (file:test/tier), noting AC10 is proven both DB-free (unit) and live (tier 7), quoting
the residue delta transcript, and stating the honest-scope caveat + "no prod apply in this
lane" verbatim.

- [ ] **Step 3: Fail-closed ASCII + commit** (`records(gate9): AC1-AC12 evidence map + green gate transcript`).

---

## Plan-review gate (before merge)

After Task 6, run the whole-branch Claude review + Codex cross-engine pass
(`apex-jobs review-run --review-head records/gate9-supabase-serving --base-ref main --json`).
Fold confirmed findings, re-verify the gate, then finishing-a-development-branch. No prod apply.
