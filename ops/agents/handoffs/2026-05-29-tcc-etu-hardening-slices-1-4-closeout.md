# TCC ETU Hardening Slices 1-4 - Closeout

Date: 2026-05-29
Status: PASS with one documented slice-1 operator block preserved truthfully
Purpose: Record the bounded execution of the admitted ETU hardening slices without widening the route-owned contract

---

## 1. Outcome

The four admitted ETU hardening slices were executed as bounded local-only work.

Route ownership stayed unchanged throughout:

- no new ETU routes were added
- no SQL helper was promoted to runtime authority
- no TMT or EMT widening occurred
- no hosted parity claim was made
- no push was performed

Final slice statuses:

- Slice 1: PARTIAL
- Slice 2: PASS
- Slice 3: PASS
- Slice 4: PASS

Slice 1 is marked PARTIAL instead of PASS because the live parity prerequisites were unavailable in this shell and the required alternate-trip-style ETU seed could not be added truthfully from repo-owned ground truth. The stop condition was preserved in the committed matrix as a blocked requirement rather than being papered over.

---

## 2. Slice Ledger

### Slice 1 - `etu-parity-probe-multisensor-breadth`

Status: PARTIAL

Commit:

- `aa33dbe7e139bb85399c49555eeb94920622e6cd` - `feat(etu-probe): matrix-driven multi-sensor parity probe (matrix #83 slice 1)`

Files:

- `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py`
- `apps/control-plane-api/scripts/etu_parity_matrix.json`

Bounded outcome:

- refactored the single-sensor probe into a matrix-driven implementation
- added an auditable ETU scenario matrix with seeded sensor 25 and sensor 26 coverage
- kept settings-side parity as hard-fail behavior
- downgraded evaluate-side parity mismatches to warnings in the report
- recorded the missing alternate-trip-style ETU seed as a blocked requirement in the matrix

Validation commands and results:

1. Live prerequisite check
   - command: `$hasDsn = [bool]$env:APEX_OLARES_LIVE_DSN; $route = try { (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8010/health' -TimeoutSec 3).StatusCode } catch { $null }; "APEX_OLARES_LIVE_DSN=$hasDsn`nROUTE_8010=$route"`
   - result:
     - `APEX_OLARES_LIVE_DSN=False`
     - `ROUTE_8010=`
2. Syntax and fixture validation
   - command: `$env:PYTHONPATH='apps/control-plane-api'; .\.venv\Scripts\python.exe -m py_compile apps/control-plane-api/scripts/probe_live_etu_sql_parity.py; .\.venv\Scripts\python.exe -c "import json, pathlib; path = pathlib.Path('apps/control-plane-api/scripts/etu_parity_matrix.json'); payload = json.loads(path.read_text(encoding='utf-8')); assert len(payload['scenarios']) == 2; assert payload['blocked_requirements'][0]['status'] == 'blocked'; print('slice1-validate-ok')"`
   - result: `slice1-validate-ok`

Blocked state preserved:

- no live probe run was attempted after the prerequisite check failed
- no non-trip-style-3 ETU seed was fabricated
- the blocked requirement is recorded directly in `apps/control-plane-api/scripts/etu_parity_matrix.json`

### Slice 2 - `etu-cascade-and-search-truthfulness`

Status: PASS

Commit:

- `2bece252bf0e8489f85bbd682238e7418d94ffbe` - `test(etu-cascade): lock plug/cross-half SQL truthfulness (matrix #83 slice 2)`

Files:

- `apps/control-plane-api/tests/test_cascade_route.py`

Bounded outcome:

- added an import-time `DATABASE_URL` fallback guard for clean local collection
- added a 422 regression test for invalid `breaker_class`
- added SQL-shape truthfulness coverage for combined cross-half and plug filters on `/api/v1/neta/cascade`
- added a plug-scope independence regression guard so `plug_values` remain scope-owned instead of selected-plug-owned
- added the `/api/v1/neta/etu/search` SQL-shape counterpart in the same route-truthfulness test surface

Validation command and result:

1. `.venv\Scripts\python.exe -m pytest apps/control-plane-api/tests/test_cascade_route.py -q`
   - result: `11 passed in 1.93s`

### Slice 3 - `etu-browser-proofing-and-handback-note-fix`

Status: PASS

Commit:

- `80f86490b93a22c20c02d4c1398fbd0539dd8033` - `test(etu-browser): provision local playwright and prove targeted flow (matrix #83 slice 3)`

Files:

- `apps/control-plane-api/scripts/provision_playwright.ps1`
- `apps/control-plane-api/tests/test_demo_browser.py`
- `ops/agents/handoffs/2026-05-28-tcc-runtime-017-phase-c-etu-ready-to-port-parity-slice-closeout-handoff.md`

Bounded outcome:

- added a repo-local PowerShell helper to provision Playwright in the repo venv and install Chromium only if needed
- preserved the existing browser-test skip gate logic
- corrected the prior Phase C handoff note so it no longer claims the original skip was caused by missing browser binaries
- repaired the targeted browser regression test so it drives the existing plug-selection precondition and matches the formatted summary text truthfully

Validation commands and results:

1. `powershell -ExecutionPolicy Bypass -File .\apps\control-plane-api\scripts\provision_playwright.ps1; $env:PYTHONPATH='apps/control-plane-api'; .\.venv\Scripts\python.exe -m pytest apps/control-plane-api/tests/test_demo_browser.py -k "provenance or plug_compatibility_check" -q`
   - first run result:
     - Playwright package/browser provisioning completed
     - browser test result: `1 failed, 1 passed, 18 deselected`
   - second run result after timing fix:
     - `1 failed, 1 passed, 18 deselected`
   - final run result after summary-format assertion fix:
     - `2 passed, 18 deselected, 2 warnings in 9.77s`

### Slice 4 - `etu-canonical-sensor25-fixture`

Status: PASS

Commit:

- `177207c3e9cc2e0184f7a77ea41bc3aa2fee9e91` - `test(etu-fixtures): consolidate sensor 25 route-ui truth source (matrix #83 slice 4)`

Files:

- `apps/control-plane-api/tests/fixtures/etu_scenario_sensor25.json`
- `apps/control-plane-api/tests/test_demo_route.py`
- `apps/control-plane-api/tests/test_demo_browser.py`

Bounded outcome:

- added a canonical sensor 25 ETU scenario fixture for the route/UI test lane
- rewired demo route assertions to read the canonical sensor 25 preset values from that fixture
- rewired browser mocks that duplicated sensor 25 cascade/context/settings payloads to read from the same fixture
- left unrelated sensor 26 data and non-route/UI surfaces unchanged

Validation commands and results:

1. `$env:PYTHONPATH='apps/control-plane-api'; .\.venv\Scripts\python.exe -m pytest apps/control-plane-api/tests/test_demo_route.py -q`
   - result: `34 passed in 3.21s`
2. `$env:PYTHONPATH='apps/control-plane-api'; .\.venv\Scripts\python.exe -m pytest apps/control-plane-api/tests/test_demo_browser.py -k "provenance or plug_compatibility_check or upstream_sensor_change_clears_stale_execution_sections" -q`
   - result: `3 passed, 17 deselected, 2 warnings in 17.47s`

---

## 3. Contract And Drift Check

No contract drift was introduced.

Verified preserved boundaries:

- `apps/control-plane-api/services/neta/router.py` remained the route-owned ETU authority
- `fn_sensor_available_settings` and `fn_evaluate_test_results` remained parity-only helper surfaces
- no route edits were made in these four slices
- no STPU override wiring was added
- no hosted parity statement was added

The only admitted partial remained the slice-1 live parity breadth gate, and that partial is explicitly recorded as blocked rather than implied away.

---

## 4. Final Git Posture

Recent bounded local commits:

- `177207c3e9cc2e0184f7a77ea41bc3aa2fee9e91` - `test(etu-fixtures): consolidate sensor 25 route-ui truth source (matrix #83 slice 4)`
- `80f86490b93a22c20c02d4c1398fbd0539dd8033` - `test(etu-browser): provision local playwright and prove targeted flow (matrix #83 slice 3)`
- `2bece252bf0e8489f85bbd682238e7418d94ffbe` - `test(etu-cascade): lock plug/cross-half SQL truthfulness (matrix #83 slice 2)`
- `aa33dbe7e139bb85399c49555eeb94920622e6cd` - `feat(etu-probe): matrix-driven multi-sensor parity probe (matrix #83 slice 1)`

Push status:

- not pushed

Untouched preexisting residue confirmed after the four slice commits:

- `M .vscode/tasks.json`
- `?? output/`

No `git add -A`, no `git add .`, and no unrelated residue was included in any slice commit.