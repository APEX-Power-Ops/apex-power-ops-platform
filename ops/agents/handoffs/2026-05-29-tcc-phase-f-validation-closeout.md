# TCC Phase F - Validation Surface Closeout

Date: 2026-05-30
Status: FAIL for live validation due governed Supabase authentication failure; PASS for offline and browser surfaces
Purpose: Record the bounded Phase F read-only validation attempt for Runtime 017 and distinguish repo-green surfaces from the external live-DB authentication blocker

---

## 1. Outcome

Phase F was executed as a read-only validation pass against the governed Supabase posture.

Surface summary:

1. offline route surface: PASS
2. live integration surface: FAIL
3. family smoke surface: FAIL
4. ETU parity surface: FAIL
5. E3 browser proof: PASS

The failing surfaces all collapsed for the same reason:

1. the sourced governed DSN produced Supabase pooler authentication failures before any family-specific contract disagreement could be evaluated

This is not a truthful repo-green Phase F close. It is a truthful read-only failure report caused by live credential/auth posture.

---

## 2. DB Posture Used

Read-only live posture used for this attempt:

1. sourced host env file before live commands
2. app config confirmed it prefers `APEX_OLARES_LIVE_DSN`
3. no local Postgres was started
4. smoke and parity were executed against the local host on `http://127.0.0.1:8010`

Host note:

1. the shorthand path `~/.apex-live.env` was not present on this host
2. the actual host file used for this run was `/home/olares/apex-secrets/olares/ai-live-dsn.env`
3. sourcing that file set `APEX_OLARES_LIVE_DSN`, but the live surfaces still failed authentication at the Supabase pooler

---

## 3. Validation Results

### 3.1 Offline Route Surface

Command:

1. `source /home/olares/apex-secrets/olares/ai-live-dsn.env && ../../.venv/bin/pytest tests/test_demo_route.py tests/test_etu_search_route.py tests/test_cascade_route.py tests/test_etu_breaker_cascade_route.py tests/test_neta_tmt_facets_route.py tests/test_neta_emt_facets_route.py -q`

Result:

1. `53 passed`

Interpretation:

1. the repo-owned ETU demo/search/cascade and TMT/EMT facet route surfaces remain green offline

### 3.2 Live Integration Surface

Command:

1. `source /home/olares/apex-secrets/olares/ai-live-dsn.env && ../../.venv/bin/pytest tests/test_neta_tmt_live_integration.py tests/test_neta_emt_live_integration.py -q -rs`

Result:

1. `2 failed`

Observed failure:

1. `psycopg2.OperationalError: ... password authentication failed for user "postgres"`
2. both TMT and EMT failed before family-specific live assertions ran

### 3.3 Family Smoke Surface

Command:

1. `source /home/olares/apex-secrets/olares/ai-live-dsn.env && .venv/bin/python -m uvicorn main:app --app-dir apps/control-plane-api --host 0.0.0.0 --port 8010`
2. `source /home/olares/apex-secrets/olares/ai-live-dsn.env && .venv/bin/python apps/control-plane-api/scripts/smoke_local_neta_family_routes.py --base-url http://127.0.0.1:8010`

Result:

1. FAIL at catalog-status gate

Observed failure:

1. `Catalog is not live: {'catalog': 'unavailable', ... 'error': '(psycopg2.OperationalError) ... password authentication failed ...'}`

### 3.4 ETU Parity Surface

Command:

1. `source /home/olares/apex-secrets/olares/ai-live-dsn.env && .venv/bin/python apps/control-plane-api/scripts/probe_live_etu_sql_parity.py --base-url http://127.0.0.1:8010`

Result:

1. FAIL before parity comparisons could run

Observed failure:

1. `RESULT FAIL: GET /api/v1/neta/settings/25 returned HTTP 500: {'detail': 'Internal Server Error'}`
2. server log showed the same Supabase pooler password-auth failure when the route tried to load ETU settings

### 3.5 E3 Browser Proof

Command:

1. `../../.venv/bin/pytest tests/test_demo_browser.py -k 'facet_grid_cross_filters' -q`

Result:

1. `2 passed, 20 deselected`

Interpretation:

1. the frontend facet-grid proof remains green and is not implicated in the live failure

---

## 4. Root Cause Assessment

Most likely blocker:

1. the governed DSN currently sourced on this host does not authenticate successfully against the Supabase pooler used by the control-plane runtime

Evidence supporting that assessment:

1. live integration tests fail immediately on DB connect with password-auth errors
2. local host starts, but catalog/status and ETU settings calls fail on first DB access with the same auth error
3. offline route tests and browser proof remain green, which argues against a recent repo regression in the bounded TCC code paths

---

## 5. Truthful Next Move

Phase F cannot be promoted from this run.

Next required action:

1. Desktop must refresh or replace the governed read-only DSN / auth material on the host
2. rerun the same five Phase F surfaces unchanged once Supabase authentication succeeds

Not admitted from this slice:

1. no Phase G hosted decision
2. no code changes were required or made for the validation attempt itself