# TCC Phase F - Validation Surface Closeout

Date: 2026-05-30
Status: PASS after DSN rerun; all five Phase F surfaces green
Purpose: Record the bounded Phase F read-only validation pass for Runtime 017, including the initial failed auth attempt and the successful rerun once the governed DSN was loaded correctly in the `olares` shell from the canonical host secrets path

---

## 1. Outcome

Phase F is green after a bounded rerun against the governed Supabase posture.

Final surface summary:

1. offline route surface: PASS
2. live integration surface: PASS
3. family smoke surface: PASS
4. ETU parity surface: PASS
5. E3 browser proof: PASS

Final outcome:

1. all five Phase F surfaces agree
2. DB posture remained read-only against governed Supabase via `APEX_OLARES_LIVE_DSN`
3. no local Postgres was used

This closeout supersedes the earlier same-day fail assessment that was captured before the DSN had been loaded correctly into the `olares` shell and before the one-terminal local-host rerun proved the remaining live-backed surfaces.

---

## 2. DB Posture Used

Read-only live posture used for the final passing run:

1. app config was already confirmed to prefer `APEX_OLARES_LIVE_DSN`
2. the canonical governed DSN loader path on this host is `/home/olares/apex-secrets/olares/ai-live-dsn.env`
3. no local Postgres was started
4. live integration ran directly against governed Supabase
5. smoke and parity ran against the local host on `http://127.0.0.1:8010`, backed by the same governed DSN

Host note:

1. the first failure was caused by DSN/auth setup not being usable from the actual `olares` shell context
2. `/home/olares/.apex-live.env` was created only as a temporary expedient during rerun recovery and should not remain the long-term host source of truth
3. once the DSN was loaded correctly in the `olares` shell, live auth succeeded
4. the later smoke/parity issue was not DB auth; it was only local host lifecycle in a one-terminal UI

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

1. `2 passed, 1 warning`

Interpretation:

1. governed Supabase auth succeeded from the `olares` shell
2. TMT and EMT both passed the live search -> context -> settings -> plot surface

### 3.3 Family Smoke Surface

Command:

1. `source /home/olares/apex-secrets/olares/ai-live-dsn.env && .venv/bin/python - <<'PY' ... PY`
2. the one-terminal rerun started `uvicorn`, waited for `/api/v1/neta/catalog/status`, then executed the smoke script against `http://127.0.0.1:8010`

Result:

1. PASS

Observed passing evidence:

1. `catalog-status: {"catalog":"live","manufacturer_count":63,"sensor_count":17831}`
2. artifact written to `/home/olares/code/apex/apex-power-ops-platform/output/dev/control-plane-local-neta-family-smoke.json`
3. ETU, TMT, and EMT known-scenario validation all returned green output

### 3.4 ETU Parity Surface

Command:

1. `source /home/olares/apex-secrets/olares/ai-live-dsn.env && .venv/bin/python apps/control-plane-api/scripts/probe_live_etu_sql_parity.py --base-url http://127.0.0.1:8010`

Result:

1. PASS

Observed passing evidence:

1. artifact written to `/home/olares/code/apex/apex-power-ops-platform/output/dev/control-plane-live-etu-sql-parity.json`
2. `RESULT PASS: live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 0`

### 3.5 E3 Browser Proof

Command:

1. `../../.venv/bin/pytest tests/test_demo_browser.py -k 'facet_grid_cross_filters' -q`

Result:

1. `2 passed, 20 deselected`

Interpretation:

1. the frontend facet-grid proof remains green and is not implicated in the live failure

---

## 4. Rerun History

Initial same-day failure mode:

1. live surfaces first failed because the governed DSN was not being consumed from the correct usable shell context
2. that produced a misleading temporary conclusion that live auth was bad on the host

What changed:

1. the host already had an established secrets location at `/home/olares/apex-secrets/olares/ai-live-dsn.env`, which should remain canonical
2. `/home/olares/.apex-live.env` was created only as a temporary duplicate during operator recovery and should be removed by host owner once no longer needed
3. live integration immediately turned green once the DSN was loaded correctly in the `olares` shell
4. a one-terminal host orchestration rerun kept `uvicorn` alive long enough for smoke and parity to execute cleanly

Conclusion:

1. there was no TCC runtime regression in the bounded Phase F slice
2. the stale fail assessment was procedural and is superseded by the passing rerun evidence above

---

## 5. Truthful Next Move

Phase F is complete and green from the rerun evidence captured above.

Admitted from this slice:

1. Phase F acceptance is satisfied
2. no code changes were required for the runtime itself; the fix was correct DSN loading plus correct local-host execution procedure

Still not admitted from this slice:

1. no Phase G hosted-parity decision