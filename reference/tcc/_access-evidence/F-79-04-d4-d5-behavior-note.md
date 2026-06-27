# F-79-04 - D4/D5 Helper/Override Columns: Access Behavior Note (template)

Status: PREP ARTIFACT (operator-fill). #79 follow-on. Author: CC. Date: 2026-06-26.
Disposition: F-79-04 is parked as **NEEDS ACCESS EVIDENCE**, not "needs more Codex review."
Gate: this note is filled from Access authority BEFORE any projection column/view is designed.
Cite: reference/tcc/G1-SCHEMA-GUIDE.md section 5 (dropped-column register D4/D5) + section 3 (DVL field dictionary).

## Purpose and authority boundary

D4 (TMT helper columns) and D5 (instantaneous-override / timing / rating columns) exist in source Access but are absent from governed `tcc.*`. Before designing any re-carry projection or view, we must capture the **business meaning** of each column from the authority that defines it: the Access field descriptions (`[DVL-DB]`), the calc-engine constants (`[DLL]`), and how the engine actually consumes them. The cells below are PRE-FILLED with what G1 already establishes (each tagged with its provenance and confidence); the cells marked **[CONFIRM-FROM-ACCESS]** require the operator's authoritative answer. CC/Codex must not invent these - G1's D4/D5 entries are explicitly `[OPEN-VALIDATION]` / `[INFERENCE]` / `[DEFERRED]`.

Stable re-carry key (already in place): `tcc.brk_{iccb,mccb,pcb}_styles.source_id` = Access `Breaker*Styles.ID`, populated NOT NULL + UNIQUE by migration 007. Any D4/D5 projection rides this key (the D1 SST re-carry, migration 006/007, is the working precedent: carry source-faithful NAME strings, resolve at query time, do not coerce to FK at load).

## RESOLUTION (2026-06-27) - reconciled into G1; only the scope cut-line remains

The D4/D5 questions below are now ANSWERED from the decompiled engine (`EasyPower.DeviceLibrary` + native `DvlEng`/`TccBase`) + live-data probes, cross-checked against G1 and operator-verified. **The authoritative decoded register now lives in G1 sec 3.1 (legends), sec 3.4 (the resolved native tier), and sec 5 D4/D5 (status upgraded) - this packet defers to G1.** Key results:

- **D4 decodes** (all `[DVL-DB]`, in G1 sec 3.1): `TMT_TripPlug` = `0 = Trip, 1 = Plug` (NOT a "rating-plug designation"); `TMT_BreakerType` = `0 = Thermal Magnetic, 1 = Motor Circuit Protector`; `TMT_ThermalMagnetic` = `0 = With Adjustable Instantaneous, 1 = Without`. `TMT_Thermal` = the **ICCB-class spelling** of `TMT_ThermalMagnetic` (both bind to `TMTThermalMagnetic`; per-class split, G1 sec 3.1). `TMT_TCCNumber` = free-text vendor-doc reference (Text, ~99% empty, NOT an FK). `TMT_Notes` = human memo.
- **D4 consumption:** there is **no saved query** - the bridge is C# app code (`DevLibBreakerStyle.GetBreakerStyles` -> `GetDefaultTripInfo`). The serving cascade reads only `TMT_Use_SST` + the inst-gate flag (`TMT_Thermal`/`ThermalMagnetic`); `BreakerType`/`TripPlug`/`TCCNumber`/`Notes` are metadata, not engine-consumed.
- **D5 / the `N` prefix:** `N`/`ninst` = **Non-Instantaneous** (instantaneous defeated / short-time-only), NOT an In-vs-Ir basis. Proof: TccBase `CTccCurveBase.GetIntKaNonInst`; DvlEng `r_*_ninst_*` strings + the NInst->Inst fallback (`-Module-.cs:12172`); PCB `r_int_ninst < r_int_inst` in 585/1431 (never higher). The override is applied native (`CdvlInstOvr` = 208-byte container, curve recalc in TccBase) - **`[NATIVE-BOUNDED]`: recoverable input layout only, not enum legends or curve math.** Not consumed by serving.
- **Trust tiers** (see `VOCABULARY_MAP.md`): `source_faithful` (served managed-cascade fields) / `native_bounded` (D5 override internals) / `deferred` (full-fidelity curve/rating behavior).

**What remains for the operator = the scope cut-line only:** which of D4 / D5 belong in the lvbreakertcc **serving contract** vs carried as `native_bounded` reference vs left `deferred`. Data-carry path: **D4** re-carry the `TMT_*` helper cols into `tcc.brk_{iccb,mccb}_styles` via `source_id`; **D5** raw-carry `InstOvr*`/`NInstOvr*`/`BrkTimes*`/`r_int_*`/`r_iec_*`/`Breaker_OvrCurves` as raw cols or a side table tagged `native_bounded`, WITHOUT wiring to serving. The `[CONFIRM-FROM-ACCESS]` cells below are retained as optional Access-side ratification; the structural/engine answers are no longer blocking.

---

## D4 - TMT helper columns (ICCB / MCCB style tables)

Source tables: `BreakerICCBStyles`, `BreakerMCCBStyles` (ICCB/MCCB only; not PCB).
Target (proposed): `tcc.brk_iccb_styles`, `tcc.brk_mccb_styles`.
G1 status: **SUPERSEDED 2026-06-27 - now CONFIRMED DROPPED + CHARACTERIZED (G1 sec 5 D4).** Decodes + consumption are settled (see RESOLUTION above); the table + questions below are retained as OPTIONAL Access ratification only. (Original template status: LIKELY DROPPED `[OPEN-VALIDATION]`.)
G1 role: describe the **thermal-magnetic alternative** used when `TMT_Use_SST = 0`, and decode the TMT breaker sub-type.

| column | provisional meaning (G1) | provenance | [CONFIRM-FROM-ACCESS] |
|---|---|---|---|
| `TMT_TCCNumber` | RESOLVED: free-text vendor-doc reference (Text, ~99% empty; e.g. `GES-6164`, `SC-3501-77C`); NOT an FK | `[VERIFIED-LIVE]` | (resolved - display/provenance only) |
| `TMT_Notes` | free-text note (the memo field that 6x-inflated CSV line counts) | `[VERIFIED-LIVE]` (memo) | any structured content the engine parses, or purely human notes? |
| `TMT_TripPlug` | RESOLVED: `0 = Trip, 1 = Plug` (G1 sec 3.1; ~99% are 0); NOT consumed by the serving cascade | `[DVL-DB]` | (resolved - metadata) |
| `TMT_BreakerType` | TM breaker sub-type: `0 = Thermal Magnetic`, `1 = Motor Circuit Protector` (per G1 sec 3) | `[DVL-DB]` | confirm the full enum + any values beyond 0/1 |
| `TMT_ThermalMagnetic` | `0 = With Adjustable Instantaneous`, `1 = Without adj instantaneous` (G1 sec 3, `[DVL-DB]`) | `[DVL-DB]` | confirm decode; interaction with `TMT_TripPlug` |
| `TMT_Thermal` | RESOLVED: the ICCB-class spelling of `TMT_ThermalMagnetic` (`0 = With Adjustable Instantaneous, 1 = Without`); the engine reads it on ICCB, binds to `TMTThermalMagnetic` | `[DLL]` `[DVL-DB]` | (resolved - G1 sec 3.1 split) |

D4 questions (RESOLVED 2026-06-27 from the engine - see RESOLUTION + G1 sec 3.1/3.4; retained for reference, answers now in G1):
1. **Source query/keys:** Which saved Access queries (if any) read these columns? G1 sec 4 notes zero saved queries walk the TMT joins (the engine resolves them in `DeviceLibrary.cs` application code) - confirm, and name the DLL reader(s) that consume D4 (analogous to `ReadTmgn*`).
2. **Downstream use:** When `TMT_Use_SST = 0`, how does the engine use D4 to characterize/serve the TMT breaker (curve selection, rating, sub-type display)? What breaks today in lvbreakertcc by their absence (vs only in the broader calc engine)?
3. **Scope:** Is D4 needed for the lvbreakertcc serving contract, or only for full calc-engine fidelity? (028 currently surfaces `d4_tmt_helper_columns_absent_from_projection` as a hazard string only.)
4. **Cardinality:** one row per style (`source_id`), or any per-frame fan-out?

---

## D5 - instantaneous-override / timing / rating columns (all style tables)

Source tables: `BreakerICCBStyles`, `BreakerMCCBStyles`, `BreakerPCBStyles`.
Target (proposed): `tcc.brk_{iccb,mccb,pcb}_styles`.
G1 status: **SUPERSEDED 2026-06-27 - now DEFERRED (serving) + `[NATIVE-BOUNDED]` (data) (G1 sec 5 D5).** The `N` prefix (= Non-Instantaneous) + the full column inventory are RESOLVED (see RESOLUTION above + G1 sec 3.4); the table + questions below are OPTIONAL ratification. (Original: DEFERRED `[INFERENCE]`.)
G1 role: frame-limited instantaneous override + mechanism timing + interrupt ratings.

| column block | provisional meaning (G1) | provenance | [CONFIRM-FROM-ACCESS] |
|---|---|---|---|
| `InstOvr*` (approx 16 cols) | instantaneous-override block: amps / tolerances / open-clear delay + radius | `[DEFERRED] [INFERENCE]` | full column list + per-column meaning + units |
| `NInstOvr*` (15 cols) | RESOLVED: the **Non-Instantaneous** variant of `InstOvr*` (breaker with instantaneous defeated / short-time-only); defaults to `InstOvr*` when N cols absent (G1 sec 3.4) | `[NATIVE-BOUNDED]` | (resolved) |
| `BrkTimes*50/60` | mechanism timing at 50/60 Hz | `[INFERENCE]` | exact columns; units; engine use |
| `r_int_*` / `r_iec_*` | LV interrupt-rating columns (ANSI vs IEC) | `[INFERENCE]` | full list; needed for rating display? |

D5 questions (RESOLVED 2026-06-27 from the engine - see RESOLUTION + G1 sec 3.4; retained for reference, answers now in G1):
1. **Source/keys:** which Access tables/columns exactly (the `InstOvr*`/`NInstOvr*` blocks are undescribed in G1 - need the real column list), keyed on `Breaker*Styles.ID`.
2. **Downstream use:** the inst-override mechanism (per G0 sec 4) - how does the engine apply these to the instantaneous trip band / curve? Is it per-frame or per-style?
3. **Scope/priority:** D5 is the larger, more deferred block. Confirm it is NOT needed for the current lvbreakertcc nominal-curve serving (028 surfaces `d5_inst_override_columns_absent_from_projection` as a hazard string only), and rank it for a future fidelity slice.

---

## Memo/notes re-carry handling (D4 `TMT_Notes` + D5 `InstOvrNoteText`)

Added 2026-06-27 from a read-only ODBC probe of the live `D:\TCC_NEW.accdb` (SELECT only; never opened
writable). The D4 `TMT_Notes` and D5 `InstOvrNoteText` columns are Access **Long Text (memo)** fields. A
prior CSV export 6x-inflated their line counts (embedded CR/LF mis-parsed as new rows), which seeded a false
"the notes cannot be queried or migrated" impression. The probe DISPROVES that: every memo column queries
cleanly and reads back verbatim. The inflation was a CSV-parsing artifact, never a query limit - which is
exactly why G1 kept the OLEDB `COUNT(*)` as authoritative (sec 5). This sub-section pins the handling so the
re-carry projection is built correctly; the business meaning is still the operator's Access ruling.

### In-scope breaker-style memo columns (ride `brk_{iccb,mccb,pcb}_styles.source_id`)

| Access column | target style table | rows / non-null | max len | rows w/ embedded CR/LF | dim |
|---|---|---|---|---|---|
| `BreakerICCBStyles.TMT_Notes` | `tcc.brk_iccb_styles` | 608 / 608 | 134 | 7 | D4 |
| `BreakerMCCBStyles.TMT_Notes` | `tcc.brk_mccb_styles` | 10335 / 10236 | 1353 | 5276 | D4 |
| `BreakerICCBStyles.InstOvrNoteText` | `tcc.brk_iccb_styles` | 608 / 480* | 0* | 0 | D5 |
| `BreakerMCCBStyles.InstOvrNoteText` | `tcc.brk_mccb_styles` | 10335 / 8679* | 0* | 0 | D5 |
| `BreakerPCBStyles.InstOvrNoteText` | `tcc.brk_pcb_styles` | 3279 / 3027 | 378 | 17 | D5 |

*ICCB/MCCB `InstOvrNoteText` non-null values are zero-length strings (MAX(LEN)=0); only PCB carries real
content (max 378). PCB has NO `TMT_Notes` (TMT_Notes is ICCB/MCCB-only, consistent with D4 = the
thermal-magnetic alternative). Probe samples of `TMT_Notes` read as HUMAN curve-provenance prose
(e.g. "POWER BREAK with MagneTrip ... Time-current Curves"), i.e. descriptive, not engine-parsed.

Out-of-scope memo columns (catalogued, NOT in this re-carry; each rides its own table's key if/when its
domain is projected): `BreakerHVStyles.Notes`, `DatStyle.NOTES`, `MOCStyles.NOTES`, `SwitchStyles.Notes`,
`EMT.Note`, `Relays.Note`, `zSysVersion.Comment`, `WkPermitTasks.{TaskDesc,HRCSubst,DetJobDesc,SafeWorkPract}`.

### Migration contract (how to carry memo columns)

1. **Read row-level, never aggregate.** The Access ODBC/ACE driver truncates or misbehaves on memo columns
   under aggregate / ORDER BY / GROUP BY / DISTINCT (silent 255-char truncation). A plain row-level SELECT of
   the column value is complete and reliable - the only supported read path. (The Access Fidelity Harness
   `access_raw` layer already reads this way.)
2. **Never via CSV.** Embedded CR/LF makes CSV row-counting wrong (see `TMT_Notes` 5276/10236). Use the
   direct ODBC -> PG path and preserve the newlines verbatim.
3. **Type = Postgres `text`** (Access memo is unbounded; no length cap).
4. **Key = `brk_{iccb,mccb,pcb}_styles.source_id`** (= Access `Breaker*Styles.ID`, NOT NULL + UNIQUE per mig
   007). One memo value per style row (cardinality 1:1 with the style; no per-frame fan-out).
5. **Name-faithful (D1 precedent).** Carry the raw memo string; do NOT parse or restructure at load. If a
   consumer parses structured content, decode at QUERY time, not load. Surface via the style view with
   field-trust tagging.

### Operator confirmation needed (folds into the D4/D5 questions above)

- **D4 `TMT_Notes`** - probe evidence = human curve-provenance prose. CONFIRM: does any consumer PARSE it, or
  is it display-only provenance metadata? (Drives surface-in-serving-contract vs reference-metadata-only.)
- **D5 `InstOvrNoteText`** - ICCB/MCCB are empty-string-populated, only PCB carries text. CONFIRM the
  `'' -> NULL` vs keep-`''` decision, and whether `InstOvrNoteText` is needed at all for the inst-override
  projection.
- **Scope** - confirm these memo columns belong in the lvbreakertcc serving contract vs full-fidelity-only
  (028 currently flags `d4_*` / `d5_*` as hazard labels only).

---

## Gate (SUPERSEDED 2026-06-27)

The structural/engine answers are RESOLVED (see RESOLUTION above + G1 sec 3.1/3.4/5) - the projection / data-carry design **no longer waits** on filling this template. The data-carry design is settled (`VOCABULARY_MAP.md` Lane-2 plan) and follows the D1 precedent:
1. Carry source-faithful values on `brk_*_styles` (D4) / a `native_bounded` side table keyed `(breaker_class, source_id)` (D5), keyed on `source_id`, name-faithful (no load-time FK coercion), **lower_snake_case target columns with `COMMENT` preserving the Access names**.
2. Decode enums at query time using the confirmed dictionary (G1 sec 3.1).
3. Surface D4 via a view (analogous to `vw_breaker_sst_bridge`) with field-trust tagging; D5 raw stays reference-only (NOT wired to serving).
4. The 028 projection-hazard strings (`d4_*`, `d5_*`) become resolvable once the columns are carried.

**The ONLY remaining operator inputs** are the SCOPE CUT-LINE (which of D4/D5 wires into the serving contract vs stays `native_bounded` reference vs `deferred`), the `canonical_term` drafts (`VOCABULARY_MAP.md`), and optional Access ratification of the `[CONFIRM-FROM-ACCESS]` cells. None blocks the data-carry.
