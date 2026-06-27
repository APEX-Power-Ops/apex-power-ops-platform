# F-79-03 - TMT Load-Completeness Anti-Join Runbook (Access-evidence packet)

Status: PREP ARTIFACT (operator-run). #79 follow-on. Author: CC. Date: 2026-06-26.
Disposition: F-79-03 is parked as **NEEDS ACCESS EVIDENCE**, not "needs more Codex review."
Cite: reference/tcc/G1-SCHEMA-GUIDE.md (lineage section 4; governed-load deltas section 5).

## Purpose and authority boundary

The TMT tables in governed `tcc.*` carry fewer rows than the Master Reference (Access OLEDB) counts in G1. This runbook gathers the **row-level evidence** needed to classify WHY, by table, into exactly one of four hypotheses. It is a discrimination procedure - it does **not** conclude the business truth. The authority is the live Access source (`D:\TCC_NEW.accdb`), which only the operator can export. Codex/CC may do the mechanical set-diff and characterization once the Access exports exist; neither may infer which hypothesis is true.

**The four hypotheses (mutually exclusive, per table):**
1. **Loader gap** - rows exist in Access, are valid, carry no exclusion reason, and were dropped by the load (e.g. batch truncation, a name-vs-id resolution failure like D1). Actionable: fix the loader / reload.
2. **Expected exclusion** - the missing rows share a property that justifies the load filtering them (RI-orphan parent, an inactive/flag column, a scratch/duplicate set). Actionable: document the rule; no fix.
3. **Stale reference count** - the G1/MR number is from an older Access snapshot; the LIVE `.accdb` count actually matches `tcc.*`. Actionable: correct G1; no data change.
4. **Restore / projection artifact** - the governed table is computed/derived (not a 1:1 Access load), so the Access count is not the right comparand; or it is a T7 restore loss (already ruled out for the sandbox: prod == sandbox). Actionable: re-characterize the comparand; no loader fix.

## Scope: the five TMT tables (lineage drives the method)

| tcc table | Access source table | G1 lineage | anti-join valid? | Access count (G1 MR) | tcc count (prod==sandbox) | delta |
|---|---|---|---|---:|---:|---:|
| `tcc.tmt_frames` | `Breaker_TMTFrameSizes` | **1:1 load** (DLL `ReadTmgnFrameRecordByFrameId`) | YES | 42,238 | 42,069 | -169 |
| `tcc.tmt_amps` | `Breaker_TMTFrameAmps` | **1:1 load** (`ReadTmgnTripAmpsByFrameId`) | YES | 67,206 | 66,960 | -246 |
| `tcc.tmt_settings` | `Breaker_TMTFrameSettings` | **1:1 load** (`ReadTmgnFrameInstSettingsByFrameId`) | YES | 58,041 | 57,983 | -58 |
| `tcc.tmt_curves` | `Breaker_TMTFrameCurves` | **COMPUTED** (G1 sec 4: "computed, not in Access"; reader N/A) | CAUTION (likely H4) | 1,143,458 | 1,139,025 | -4,433 |
| `tcc.tmt_thermal_adj` | `Breaker_TMTThermalTripAdj` | **DERIVED** (G1 sec 4/5 "thermal adj - derived"; governed-load delta) | CAUTION (likely H4) | 21,790 | 14,620 | -7,170 |

Keys: frames join Access `Breaker_TMTFrameSizes.ID` == `tcc.tmt_frames.id`. Children key Access `FrameSizeID` == `tcc.<child>.frame_id`; each child also has its own row `ID`/`id`.

Sandbox ID-space already characterized (parallel-codex findings, for context - NOT a substitute for the Access export):
- `tmt_frames`: rows 42,069, id 1..42,082, 13 internal gaps {33243-33250, 41555-41559}
- `tmt_amps`: 66,960, id 1..66,966, 6 gaps
- `tmt_settings`: 57,983, id 1..57,983, 0 gaps (dense, tail-short by 58)
- `tmt_curves`: 1,139,025, id 1..1,139,025, 0 gaps (dense, short 4,433)
- `tmt_thermal_adj`: 14,620, id 1..14,628, 8 gaps {11110-11117}, short 7,170 (looks tail-truncated)

Shape read (a HINT, not a verdict): mostly-dense loads that stop before the Access count = consistent with H1 (loader truncation) OR H4 (derived subset). The Access export discriminates.

## Procedure (per table; run for all five)

### Step 0 - Confirm lineage (resolves H4 up front)
For `tmt_curves` and `tmt_thermal_adj` ONLY: confirm with the calc-engine / Access authority whether the governed table is a **1:1 load of the Access table** or a **computed/derived** product. G1 says computed/derived. If derived, the Access table count is **not** the correct comparand and the "gap" is H4 by construction; record the real generation input and STOP (no anti-join against the Access table). If the operator asserts it IS a 1:1 load, proceed to Step 1. For `tmt_frames`/`tmt_amps`/`tmt_settings` (DLL 1:1 loads), go straight to Step 1.

### Step 1 - Live Access count (resolves H3)
In the live `.accdb`, run and record:
```sql
-- Access (run in TCC_NEW.accdb)
SELECT COUNT(*) AS live_access_rows FROM Breaker_TMTFrameSizes;   -- and each table
```
If `live_access_rows` is approximately the `tcc` count (not the G1 MR number), the gap is **H3 stale reference count** - record the live number, flag G1 for correction, STOP for that table. Else continue.

### Step 2 - Export the Access key set (the authoritative input)
Export to CSV (one file per table). Include the key plus the columns needed for characterization:
```sql
-- Access: frames
SELECT ID, FrameSizeID_isnull = IIF(1=1,Null,Null)  -- frames has no parent; ID only
FROM Breaker_TMTFrameSizes;            -- export: ID  (-> frames_access_ids.csv)

-- Access: a child (amps shown; settings identical shape)
SELECT ID, FrameSizeID                 -- key + parent FK for orphan analysis
FROM Breaker_TMTFrameAmps;             -- export: ID, FrameSizeID (-> amps_access_ids.csv)
```
Also export, for the child tables, the set of `FrameSizeID` values whose parent is absent from `Breaker_TMTFrameSizes` (Access-side orphan check - feeds H2):
```sql
-- Access: children whose parent frame does not exist in Access
SELECT a.ID, a.FrameSizeID
FROM Breaker_TMTFrameAmps AS a
LEFT JOIN Breaker_TMTFrameSizes AS f ON a.FrameSizeID = f.ID
WHERE f.ID IS NULL;                    -- export: amps_access_orphans.csv
```

### Step 3 - The diff (mechanical; CC/Codex, no business inference)
Hand the Access CSVs back. CC/Codex pulls the matching `tcc` id sets from the live sandbox viewer (read-only) and computes:
```sql
-- tcc side (sandbox viewer / prod, read-only): the id set per table
SELECT id FROM tcc.tmt_frames ORDER BY id;
SELECT id, frame_id FROM tcc.tmt_amps ORDER BY id;          -- and settings/curves/thermal_adj
```
Then the two directed differences per table:
- **missing_in_tcc** = `access_ids \ tcc_ids` (the F-79-03 shortfall - the rows to classify)
- **extra_in_tcc** = `tcc_ids \ access_ids` (restore/projection artifacts; e.g. the 484 orphan `tmt_curves` from T7 - H4)

### Step 4 - Characterize `missing_in_tcc` (discriminates H1 vs H2)
For the missing key set, the operator pulls the FULL Access rows and answers:
- **Tail-contiguous?** Are the missing IDs a contiguous block at the high end (e.g. last N)? -> consistent with H1 loader truncation.
- **Shared exclusion property?** Do the missing rows share a null/invalid parent `FrameSizeID`, an inactive/disabled flag, a scratch/duplicate marker, or a manufacturer/name that fails resolution (the D1 name-vs-id pattern)? -> H2 expected exclusion (document the rule).
- **Random/valid?** Scattered, valid, fully-parented rows with no exclusion property -> H1 loader gap (actionable reload).

### Step 5 - Operator verdict (the only place truth is decided)
Per table, the operator records ONE classification (H1/H2/H3/H4) with the evidence that justifies it. CC/Codex supply the diff + characterization; the operator supplies the verdict.

## Expected evidence format (one row per table)

| field | source | example |
|---|---|---|
| `tcc_table` | fixed | `tcc.tmt_frames` |
| `access_table` | fixed | `Breaker_TMTFrameSizes` |
| `lineage` | Step 0 | `1:1_load` / `computed` / `derived` |
| `live_access_count` | Step 1 (Access) | `42238` |
| `tcc_count` | Step 3 (tcc) | `42069` |
| `delta` | computed | `-169` |
| `missing_in_tcc_count` | Step 3 | `169` |
| `missing_in_tcc_sample` | Step 3 | first/last 20 ids |
| `missing_tail_contiguous` | Step 4 | `true`/`false` |
| `missing_shared_property` | Step 4 | e.g. `null FrameSizeID` / `none` |
| `extra_in_tcc_count` | Step 3 | `0` |
| `extra_in_tcc_sample` | Step 3 | ids |
| `operator_classification` | Step 5 | `H1_loader_gap` / `H2_expected_exclusion` / `H3_stale_ref` / `H4_projection_artifact` |
| `operator_note` | Step 5 | free text justification |

Deliver as a 5-row table (one per TMT table) plus the raw CSVs. That table is the F-79-03 resolution record; it determines whether each table needs a loader fix (H1), a documented rule (H2), a G1 correction (H3), or a comparand re-characterization (H4) - none of which this packet decides.

## What this packet does NOT do
- It does not assert any table is a loader gap. The sandbox "tail-truncation" shape is a hint only.
- It does not touch prod or write any migration. F-79-03 is not migration-ready until the verdict table exists.
- It does not read the Access DB. Every Access query above is for the operator to run; the truth is the operator's export.
