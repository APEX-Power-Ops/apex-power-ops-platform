# Host XER Verification Runbook

**Packet:** `2026-04-18-pm-schema-020f`
**Purpose:** give the Apex host operator the exact command sequence needed to complete the real-host leg of packet 020f that the sandbox execution could not reach.
**Host target:** the Windows machine where `C:/APEX Platform/apex-power-ops-platform/` lives and the `apps/mutation-seam/` runtime is installed.
**Do not** follow this runbook inside the sandbox — it is the companion to the sandbox attribute probe and is explicitly authored because sandbox ≠ host (per the existing APEX memory rule).

---

## 1. Prerequisites

Confirm on the host, in a PowerShell or `cmd` prompt:

```powershell
cd "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam"
python --version
pip show PyP6Xer
```

Expected:

- Python is the same interpreter the mutation-seam service runs under.
- `PyP6Xer` is installed and `Version: 1.016.00` (or newer if the platform has since pinned a different version — record it).

If PyP6Xer is not installed:

```powershell
pip install PyP6Xer
```

and capture the installed version before proceeding.

---

## 2. Step 1 — attribute-name probe on the real host Reader

Run exactly:

```powershell
python -c "from xerparser.reader import Reader; r = Reader(r'C:/Users/jjswe/NETA ETT Study Material/PM-Pro-Guide-xer-Templates/PM Pro Guide xer Templates/Baseline Zone 2 Rev.01.xer'); print(sorted([a for a in dir(r) if not a.startswith('_')]))"
```

Record the printed list in the execution handoff. The **sandbox-observed** list for PyP6Xer 1.016.00 was:

```
['accounts', 'activities', 'activitycodes', 'activityresources', 'acttypes',
 'actvcodes', 'calendars', 'create_object', 'currencies', 'current_headers',
 'current_table', 'file', 'fintmpls', 'get_num_lines', 'nonworks', 'obss',
 'pcattypes', 'pcatvals', 'projects', 'projpcats', 'rcattypes', 'rcatvals',
 'relations', 'resourcecategories', 'resourcecurves', 'resourcerates',
 'resources', 'rolerates', 'roles', 'scheduleoptions', 'summary',
 'taskprocs', 'udftypes', 'udfvalues', 'wbss', 'write']
```

The host list MUST match this surface for packet 020d's compatibility-layer assumptions to hold. Specifically, the host MUST confirm that **none** of these names are present on the real Reader:

- `tasks` (loader uses this; real name is `activities`)
- `projwbs` (loader uses this; real name is `wbss`)
- `taskpreds` (loader uses this; real name is `relations`)
- `projbaselines` / `projbaseline` / `baselineprojects` / `baselineproject` (loader uses these; no such attribute exists on PyP6Xer 1.016.00)

If the host surface exposes any of those names, capture the surface verbatim in the handoff — that is a separate parser-version surface and a follow-on packet MUST reconcile 020d with it before this runbook can close.

---

## 3. Step 2 — raw-XER section probe

Run exactly:

```powershell
python -c "import re; raw = open(r'C:/Users/jjswe/NETA ETT Study Material/PM-Pro-Guide-xer-Templates/PM Pro Guide xer Templates/Baseline Zone 2 Rev.01.xer', 'rb').read().decode('latin-1', errors='replace'); print('projbaseline:', raw.count('PROJBASELINE')); print('baselineproject:', raw.count('BASELINEPROJECT')); print('sections:', sorted(set(re.findall(r'^%T\s+(\w+)', raw, flags=re.MULTILINE))))"
```

The **sandbox-observed** output for this specific file was:

```
projbaseline: 0
baselineproject: 0
sections: ['ACTVCODE', 'ACTVTYPE', 'CALENDAR', 'CURRTYPE', 'OBS', 'POBS',
           'PROJECT', 'PROJWBS', 'ROLES', 'RSRC', 'RSRCRATE', 'RSRCROLE',
           'SCHEDOPTIONS', 'TASK', 'TASKACTV', 'TASKPRED', 'TASKRSRC',
           'UDFTYPE', 'UDFVALUE']
```

If the host sees the same, the record becomes: this file is **not** baseline-bearing in the P6 sense despite its name, and cannot be admitted as a golden fixture under §3 of `BASELINE_XER_FIXTURE_CONTRACT.md`. Log that outcome in the handoff.

If a different host-side XER is available that contains `PROJBASELINE` or `BASELINEPROJECT` sections, re-run Step 2 against it and record the results. That file becomes the candidate for §4 below.

---

## 4. Step 3 — end-to-end loader dry-run

This step requires either:

- a host-side `.xer` that passes the Step 2 section probe with a non-zero `PROJBASELINE` / `BASELINEPROJECT` count, **or**
- an explicit decision to validate only the live-import lane on a non-baseline-bearing XER.

Run exactly (adjust the path to the chosen file):

```powershell
cd "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam"
python -m app.schedule.loader --xer "<path-to-xer>" --dry-run
```

Expected for the **sandbox dry-run** against `Baseline Zone 2 Rev.01.xer`:

- `projects` count: 1
- `wbs_nodes`, `tasks`, `relationships` counts: all 0 (because the loader uses `reader.tasks` / `reader.projwbs` / `reader.taskpreds`, which do not exist on PyP6Xer 1.016.00)
- `baselines` entry count: 0 (no PROJBASELINE surface)

If the host result matches, this confirms that `apps/mutation-seam/app/schedule/loader.py` is **currently unable to import live activities** from real PyP6Xer 1.016.00 output, regardless of baseline content. A follow-on packet MUST reconcile the attribute-name mismatch before any concrete golden fixture can drive meaningful loader coverage.

If the host result differs (non-zero tasks / relationships / baselines), capture the full dry-run output in the handoff — it means the host PyP6Xer surface is not the 1.016.00 surface the sandbox observed.

---

## 5. Step 4 — integrity check on loader.py

Run exactly:

```powershell
python -c "import ast; src = open(r'C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/schedule/loader.py').read(); ast.parse(src); print('OK', len(src.splitlines()))"
```

Expected: `OK <line count>`. The **sandbox-observed** state of the working-copy `loader.py` was:

```
SyntaxError: unterminated triple-quoted string literal (detected at line 716)
```

If the host also reports `SyntaxError`, the working copy is truncated and the packet-020d "20 passed" claim cannot be reproduced on-disk. The operator MUST restore `loader.py` from the last clean commit (or from the bytecode cache `app/schedule/__pycache__/loader.cpython-*.pyc` if the commit history is unavailable) before any run in §4 can be trusted. Record the outcome in the handoff.

If the host reports `OK`, the mutation-seam working copy is intact — log the line count and move on.

---

## 6. Step 5 — packet-020d regression re-run (only after §5 passes)

Run exactly:

```powershell
cd "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam"
python -m pytest tests/test_schedule_baseline.py -q
```

Expected: `20 passed` (per the packet-020d handoff). If fewer pass or errors surface, capture the full pytest output in the handoff and do **not** mark 020f as host-validated.

---

## 7. Recording disposition

At the end of the runbook, the operator MUST set one of these three disposition tags in the execution handoff:

- `host-validated` — §1–§6 all succeeded and the real loader emitted at least one baseline entry against a genuine baseline-bearing XER.
- `sandbox-probed-host-runbook-authored` — this runbook was authored but the host steps have not yet run, OR they ran but surfaced the PyP6Xer 1.016.00 mismatch documented above and therefore cannot produce baseline entries without a parser-side follow-on.
- `blocked-no-real-baseline-bearing-xer` — no baseline-bearing XER is available on the host, regardless of loader health.

Do not invent a fourth disposition. If the host outcome does not match any of the three, open a new clarification packet before closing 020f.

---

## 8. Compliance statement

This runbook:

1. Authors no SQL. Authors no DDL. Authors no migration.
2. Does not modify `apps/mutation-seam/app/schedule/loader.py`.
3. Adds no bridge route and changes no response shape.
4. Does not modify the PM UI or any other client code.
5. Does not bypass the integration-lane / operational-lane separation defined in 020b.

---

*Authored under packet `2026-04-18-pm-schema-020f`. Host-verification runbook; no runtime changes.*
