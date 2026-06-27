# F-79-03 - TMT Load-Completeness Anti-Join Runbook (Access-evidence packet)

Status: PREP ARTIFACT (operator-run). #79 follow-on. Author: CC. Date: 2026-06-26.
Disposition: F-79-03 is parked as **NEEDS ACCESS EVIDENCE**, not "needs more Codex review."
Cite: reference/tcc/G1-SCHEMA-GUIDE.md (domain map section 1; join graph section 2; lineage section 4; governed-load deltas section 5).

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

### Keys (G1 sec 1 + sec 2) - the load-bearing correction

- **Frames** carry a surrogate PK: Access `Breaker_TMTFrameSizes.ID` (26 fields) == `tcc.tmt_frames.id`. Anti-join the frame **ID set** directly.
- **Children have NO surrogate row ID.** Each child is keyed by the FK `FrameSizeID` (declared FK -> `Breaker_TMTFrameSizes.ID`) plus a natural attribute set:
  - `Breaker_TMTFrameAmps` (2 fields): natural key **`(FrameSizeID, TripAmp)`**.
  - `Breaker_TMTFrameCurves` (4 fields): natural key **`(FrameSizeID, Class, Time, Amps)`** (`Class`: 0=Sec1 Opening / 1=Sec1 Clearing / 2=Sec2 Clearing).
  - `Breaker_TMTFrameSettings` (5 fields): `FrameSizeID` + setting columns - exact natural key **[CONFIRM-FROM-ACCESS]**.
  - `Breaker_TMTThermalTripAdj` (3 fields): `FrameSizeID` + adj columns - exact natural key **[CONFIRM-FROM-ACCESS]**.
- The `tcc.*` children carry their own surrogate `id` plus `frame_id` (the FK to `tmt_frames.id`). The tcc surrogate `id` is a load-order rank and does **NOT** correspond to any Access row id - so a child anti-join MUST be done at the **frame grain** (per-`FrameSizeID`/`frame_id` count), then row-level on the **natural key**, never on a surrogate.

Sandbox ID-space already characterized (parallel-codex findings, context only - NOT a substitute for the Access export):
- `tmt_frames`: rows 42,069, id 1..42,082, 13 internal gaps {33243-33250, 41555-41559}
- `tmt_amps`: 66,960; `tmt_settings`: 57,983 (dense, tail-short 58); `tmt_curves`: 1,139,025 (dense, short 4,433); `tmt_thermal_adj`: 14,620, 8 internal gaps {11110-11117}, short 7,170 (looks tail-truncated)

Shape read (a HINT, not a verdict): mostly-dense loads that stop before the Access count = consistent with H1 (loader truncation) OR H4 (derived subset). The Access export discriminates.

## Procedure

### Step 0 - Confirm lineage (resolves H4 up front)
For `tmt_curves` and `tmt_thermal_adj` ONLY: confirm with the calc-engine / Access authority whether the governed table is a **1:1 load of the Access table** or a **computed/derived** product. G1 says computed/derived. If derived, the Access table count is **not** the correct comparand and the "gap" is H4 by construction; record the real generation input and STOP (no anti-join against the Access table). If the operator asserts it IS a 1:1 load, treat it like the others. `tmt_frames`/`tmt_amps`/`tmt_settings` are DLL 1:1 loads - go to Step 1.

### Step 1 - Live Access count (resolves H3)
In the live `.accdb`, record `COUNT(*)` per table:
```sql
-- Access (TCC_NEW.accdb)
SELECT COUNT(*) AS live_access_rows FROM Breaker_TMTFrameSizes;   -- repeat per table
```
If `live_access_rows` is approximately the `tcc` count (not the G1 MR number), the gap is **H3 stale reference count** - record the live number, flag G1, STOP for that table. Else continue.

### Step 2 - Export the Access evidence (the authoritative input)

**(2a) Frame ID set** (the only surrogate anti-join):
```sql
-- Access: frames have a real ID PK
SELECT ID FROM Breaker_TMTFrameSizes;                 -- export: frames_access_ids.csv
```

**(2b) Per-frame child counts** (frame-grain, robust, needs no surrogate):
```sql
-- Access: one query per child table (amps shown)
SELECT FrameSizeID, COUNT(*) AS access_rows
FROM Breaker_TMTFrameAmps GROUP BY FrameSizeID;       -- export: amps_access_framecounts.csv
-- repeat for Breaker_TMTFrameSettings / Breaker_TMTFrameCurves / Breaker_TMTThermalTripAdj
```

**(2c) Child natural-key set** (for row-level diff inside the affected frames):
```sql
-- Access: amps natural key is known
SELECT FrameSizeID, TripAmp FROM Breaker_TMTFrameAmps;            -- export: amps_access_keys.csv
-- curves natural key is known
SELECT FrameSizeID, Class, Time, Amps FROM Breaker_TMTFrameCurves;-- export: curves_access_keys.csv
-- settings / thermal: export FrameSizeID + ALL columns; CONFIRM the natural key in this step
SELECT * FROM Breaker_TMTFrameSettings;                          -- export: settings_access_full.csv
SELECT * FROM Breaker_TMTThermalTripAdj;                         -- export: thermal_access_full.csv
```

**(2d) Access-side orphan check** (feeds H2 - children whose parent frame is absent in Access):
```sql
SELECT a.FrameSizeID, COUNT(*) AS orphan_rows
FROM Breaker_TMTFrameAmps AS a
LEFT JOIN Breaker_TMTFrameSizes AS f ON a.FrameSizeID = f.ID
WHERE f.ID IS NULL
GROUP BY a.FrameSizeID;                               -- export: amps_access_orphans.csv (repeat per child)
```

### Step 3 - The diff (mechanical; CC/Codex, no business inference)
Hand the CSVs back. CC/Codex pulls the matching `tcc` sets (read-only sandbox viewer / prod) and computes:
```sql
-- tcc side, read-only
SELECT id FROM tcc.tmt_frames ORDER BY id;                       -- frame id set
SELECT frame_id, COUNT(*) AS tcc_rows FROM tcc.tmt_amps GROUP BY frame_id;  -- per-frame counts (per child)
```
Then per table:
- **Frames:** `missing_in_tcc = access_ids \ tcc_ids`; `extra_in_tcc = tcc_ids \ access_ids`.
- **Children (frame grain first):** join `*_access_framecounts` to the tcc per-frame counts on `FrameSizeID = frame_id`; the frames where `access_rows > tcc_rows` are where rows were lost (and `tcc_rows > access_rows` = extra/projection artifacts, e.g. the 484 orphan `tmt_curves` from T7 = H4).
- **Children (row level, only inside the affected frames):** natural-key set-diff using the confirmed key (amps `(FrameSizeID,TripAmp)`, curves `(FrameSizeID,Class,Time,Amps)`, settings/thermal once the key is confirmed in 2c). This names the specific missing child rows.

### Step 4 - Characterize the missing set (discriminates H1 vs H2)
For the missing frames / child rows, the operator inspects the full Access rows and answers:
- **Tail-contiguous?** Missing frame IDs a contiguous high-end block, or child deficits concentrated in the highest `FrameSizeID`s? -> consistent with H1 loader truncation.
- **Shared exclusion property?** Missing rows share a null/invalid parent `FrameSizeID`, an inactive/disabled flag, a scratch/duplicate marker, or a manufacturer/name that fails resolution (the D1 name-vs-id pattern)? -> H2 expected exclusion (document the rule).
- **Random/valid?** Scattered, valid, fully-parented rows with no exclusion property -> H1 loader gap (actionable reload).

### Step 5 - Operator verdict (the only place truth is decided)
Per table, the operator records ONE classification (H1/H2/H3/H4) with the justifying evidence. CC/Codex supply the diff + characterization; the operator supplies the verdict.

## Expected evidence format (one row per table)

| field | source | example |
|---|---|---|
| `tcc_table` | fixed | `tcc.tmt_amps` |
| `access_table` | fixed | `Breaker_TMTFrameAmps` |
| `lineage` | Step 0 | `1:1_load` / `computed` / `derived` |
| `live_access_count` | Step 1 (Access) | `67206` |
| `tcc_count` | Step 3 (tcc) | `66960` |
| `delta` | computed | `-246` |
| `frames_with_deficit` | Step 3 (children) | count of `FrameSizeID` where access_rows > tcc_rows |
| `missing_rows_count` | Step 3 | `246` |
| `missing_rows_sample` | Step 3 | sample natural keys |
| `missing_tail_contiguous` | Step 4 | `true`/`false` |
| `missing_shared_property` | Step 4 | e.g. `null FrameSizeID` / `none` |
| `extra_in_tcc_count` | Step 3 | `0` |
| `operator_classification` | Step 5 | `H1_loader_gap` / `H2_expected_exclusion` / `H3_stale_ref` / `H4_projection_artifact` |
| `operator_note` | Step 5 | free-text justification |

Deliver as a 5-row table (one per TMT table) plus the raw CSVs. That table is the F-79-03 resolution record; it determines whether each table needs a loader fix (H1), a documented rule (H2), a G1 correction (H3), or a comparand re-characterization (H4) - none of which this packet decides.

## What this packet does NOT do
- It does not assert any table is a loader gap. The sandbox "tail-truncation" shape is a hint only.
- It does not touch prod or write any migration. F-79-03 is not migration-ready until the verdict table exists.
- It does not read the Access DB. Every Access query above is for the operator to run; the truth is the operator's export.
- It does not anti-join children on a surrogate id (they have none in Access, and the tcc `id` is a non-aligning load-order rank) - children diff at the frame grain, then on the natural key.
