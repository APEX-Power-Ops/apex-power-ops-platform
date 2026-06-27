# F-79-04 - D4/D5 Helper/Override Columns: Access Behavior Note (template)

Status: PREP ARTIFACT (operator-fill). #79 follow-on. Author: CC. Date: 2026-06-26.
Disposition: F-79-04 is parked as **NEEDS ACCESS EVIDENCE**, not "needs more Codex review."
Gate: this note is filled from Access authority BEFORE any projection column/view is designed.
Cite: reference/tcc/G1-SCHEMA-GUIDE.md section 5 (dropped-column register D4/D5) + section 3 (DVL field dictionary).

## Purpose and authority boundary

D4 (TMT helper columns) and D5 (instantaneous-override / timing / rating columns) exist in source Access but are absent from governed `tcc.*`. Before designing any re-carry projection or view, we must capture the **business meaning** of each column from the authority that defines it: the Access field descriptions (`[DVL-DB]`), the calc-engine constants (`[DLL]`), and how the engine actually consumes them. The cells below are PRE-FILLED with what G1 already establishes (each tagged with its provenance and confidence); the cells marked **[CONFIRM-FROM-ACCESS]** require the operator's authoritative answer. CC/Codex must not invent these - G1's D4/D5 entries are explicitly `[OPEN-VALIDATION]` / `[INFERENCE]` / `[DEFERRED]`.

Stable re-carry key (already in place): `tcc.brk_{iccb,mccb,pcb}_styles.source_id` = Access `Breaker*Styles.ID`, populated NOT NULL + UNIQUE by migration 007. Any D4/D5 projection rides this key (the D1 SST re-carry, migration 006/007, is the working precedent: carry source-faithful NAME strings, resolve at query time, do not coerce to FK at load).

---

## D4 - TMT helper columns (ICCB / MCCB style tables)

Source tables: `BreakerICCBStyles`, `BreakerMCCBStyles` (ICCB/MCCB only; not PCB).
Target (proposed): `tcc.brk_iccb_styles`, `tcc.brk_mccb_styles`.
G1 status: **LIKELY DROPPED** - co-located with the D1 `TMT_*`/`SST_*` block, dropped by the same name-vs-id loader assumption; not individually live-confirmed `[OPEN-VALIDATION] [INFERENCE]`.
G1 role: describe the **thermal-magnetic alternative** used when `TMT_Use_SST = 0`, and decode the TMT breaker sub-type.

| column | provisional meaning (G1) | provenance | [CONFIRM-FROM-ACCESS] |
|---|---|---|---|
| `TMT_TCCNumber` | TCC reference number for the thermal-magnetic curve set | `[INFERENCE]` | exact semantics; is it an FK into a curve/TCC table? which? |
| `TMT_Notes` | free-text note (the memo field that 6x-inflated CSV line counts) | `[VERIFIED-LIVE]` (memo) | any structured content the engine parses, or purely human notes? |
| `TMT_TripPlug` | trip-plug / rating-plug designation for the TM breaker | `[INFERENCE]` | value domain; does it drive sensor/rating selection? |
| `TMT_BreakerType` | TM breaker sub-type: `0 = Thermal Magnetic`, `1 = Motor Circuit Protector` (per G1 sec 3) | `[DVL-DB]` | confirm the full enum + any values beyond 0/1 |
| `TMT_ThermalMagnetic` | `0 = With Adjustable Instantaneous`, `1 = Without adj instantaneous` (G1 sec 3, `[DVL-DB]`) | `[DVL-DB]` | confirm decode; interaction with `TMT_TripPlug` |
| `TMT_Thermal` | thermal-element descriptor/flag | `[INFERENCE]` | meaning + value domain |

D4 questions for the operator (the behavior note proper):
1. **Source query/keys:** Which saved Access queries (if any) read these columns? G1 sec 4 notes zero saved queries walk the TMT joins (the engine resolves them in `DeviceLibrary.cs` application code) - confirm, and name the DLL reader(s) that consume D4 (analogous to `ReadTmgn*`).
2. **Downstream use:** When `TMT_Use_SST = 0`, how does the engine use D4 to characterize/serve the TMT breaker (curve selection, rating, sub-type display)? What breaks today in lvbreakertcc by their absence (vs only in the broader calc engine)?
3. **Scope:** Is D4 needed for the lvbreakertcc serving contract, or only for full calc-engine fidelity? (028 currently surfaces `d4_tmt_helper_columns_absent_from_projection` as a hazard string only.)
4. **Cardinality:** one row per style (`source_id`), or any per-frame fan-out?

---

## D5 - instantaneous-override / timing / rating columns (all style tables)

Source tables: `BreakerICCBStyles`, `BreakerMCCBStyles`, `BreakerPCBStyles`.
Target (proposed): `tcc.brk_{iccb,mccb,pcb}_styles`.
G1 status: **DEFERRED** - known deferred item (G0 sec 4 inst-override) `[DEFERRED] [INFERENCE]`.
G1 role: frame-limited instantaneous override + mechanism timing + interrupt ratings.

| column block | provisional meaning (G1) | provenance | [CONFIRM-FROM-ACCESS] |
|---|---|---|---|
| `InstOvr*` (approx 16 cols) | instantaneous-override block: amps / tolerances / open-clear delay + radius | `[DEFERRED] [INFERENCE]` | full column list + per-column meaning + units |
| `NInstOvr*` (approx 16 cols) | the `N`-variant inst-override block (negative? neutral? new?) - meaning of the `N` prefix unknown | `[INFERENCE]` | what `N` denotes; relationship to `InstOvr*` |
| `BrkTimes*50/60` | mechanism timing at 50/60 Hz | `[INFERENCE]` | exact columns; units; engine use |
| `r_int_*` / `r_iec_*` | LV interrupt-rating columns (ANSI vs IEC) | `[INFERENCE]` | full list; needed for rating display? |

D5 questions for the operator:
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

## Gate: design projection ONLY after this note is filled

Once the [CONFIRM-FROM-ACCESS] cells and the per-block questions are answered from Access authority, the projection design follows the D1 precedent:
1. Carry source-faithful values on `brk_*_styles`, keyed on the existing `source_id` (Access `.ID`), name-faithful (no load-time FK coercion).
2. Decode enums at query time using the confirmed dictionary.
3. Surface via a view (analogous to `vw_breaker_sst_bridge`), with field-trust tagging.
4. The 028 projection-hazard strings (`d4_*`, `d5_*`) become resolvable once the columns are carried.

This note does not design that projection. It captures the authority needed to design it correctly, and nothing here is treated as settled until the operator confirms it from Access.
