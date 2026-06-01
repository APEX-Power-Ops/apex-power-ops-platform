# G2 — Rules Guide (Invariants · Frozen Baselines · Deferred-Work Ledger · Governance · Adoption Gates)

> **Owns:** what is **locked**, what is **open**, and **how changes are governed** in the TCC domain.
> Cite this guide when deciding whether a thing is *settled* (don't re-litigate), *frozen* (don't mutate
> without a governance entry), or *open* (reopen only on the stated trigger). This is the deferred-work
> ledger of record and the home of the reference-of-record vs forward-port rule.
>
> Status: DRAFT (agent-authored 2026-05-31; DB-checkable subset deep-validated 2026-05-31)
>
> Last validated · 2026-06-01 · Desktop (DB-checkable subset **100% MATCH, 0 discrepancies** — `_discovery/_validation/v2-g2-rules-validation.md`) · Open gaps · **(1)** R-1..R-8 residual-risk per-risk prose is host-only `[OPEN-VALIDATION]`; **(2)** InvEq numeric parity (D-11) **SPLIT + patched 2026-06-01** — the Ansi half (100 rows / 23 sensors) is **✅ hard-excluded (lean 1)**, Therm `CalcThermEq` is recovered + patched (`c4/c5` used), and captured EasyPower fixture parity remains; **(3)** SST-bridge governance entry §4.3 stands — D1 confirmed dropped live, D2 (relay) **reversed → carried**; **(4)** EMT breaker-selection edge **REFINED** — no *stored* breaker→EMT default, but a runtime-selectable trip type per `[EZPDOC]` (G0 §5); **(5)** `tcc.brk_mccb` 41-row drop **✅ CLOSED 2026-06-01 (lean 2)** — too-narrow `UNIQUE(manufacturer_id,name)` widened to the Access 4-tuple, 41 MCCB twins reloaded (§4.6); **(6)** deployed-catalog RLS posture **✅ COMPLETED 2026-06-01 (lean 3)** — all 60 `tcc.*` RLS-on, public-read/service-write (§4.7). *Live-confirmed: anchors 4604/16671/4174 present + 6258-absent (F-8 holds); D-11 sizing exact (4,524+1,713=6,237); `tcc`=60/0; `tcc.manufacturers`=450; `brk_mccb`=640/`brk_iccb`=29/`brk_pcb`=157.*

---

## 0. How to read this guide

Three load-bearing distinctions govern everything below. Keep them separate:

| Term | Meaning | Mutation rule |
|---|---|---|
| **Invariant** | An always-true rule of the domain. Holds across every packet and rebuild. | Never violated. A change here is a re-architecture, not a packet. |
| **Frozen baseline** | A *locked state* established by a closed packet (a validated corpus, a rename, a swap). | Mutable only by a packet that re-validates and re-freezes — and that first amends this guide (SSoT Law §2, cross-ref 00). |
| **Deferred item** | Known-incomplete by decision. | Reopens **only** on its named trigger, via a separately-authored governance-controlled packet. "Nothing is open by default." `[HANDOFF 2026-04-29-...-completion]` `[07]` |

Provenance tags follow 00 §2 exactly: `[VERIFIED-LIVE <date>]` · `[DLL <file:line>]` · `[DVL-DB <table.col>]` ·
`[HANDOFF <id>]` · `[INFERENCE]` · `[DEFERRED]` · `[OPEN-VALIDATION]`. Conflict rule: **engine source
(`[DLL]`) outranks DB description (`[DVL-DB]`) outranks inference** (00 §2; see Invariant INV-4).

---

## 1. Invariants — the always-true rules

These are the rules that survive every rebuild. They are the reason "the next build is the last
rediscovery." Each is load-bearing; tags cite where it is attested.

| # | Invariant | Why it holds / provenance |
|---|---|---|
| **INV-1** | **Per-sensor tolerances are authoritative off `DatSensor`.** Tolerance windows (and the delay-calc routing bytes that derive them) are a property of the individual sensor row, not of the breaker, manufacturer, or any rolled-up family default. | The selection contract terminates at the sensor leaf; plugs are sensor-rooted, curves are calc-time. `[HANDOFF sst-filter-workflow-implementation-completion]` `[05]` §1.5. Delay routing reads `DatSensor.DS3_SEC3_I2T` / `DS1GF_SEC3_I2T`. `[DLL DvlEng.cs:105701]` `[06]` |
| **INV-2** | **Family-distinct (Gap 5): ETU/SST SQL never references TMT or EMT tables**, and vice-versa. Each trip family keeps its own cascade; browse helpers are never reused across families. | Workflow-audit "Gap 5" ruling, preserved unbroken through slices α/β/γ. `[HANDOFF stage1-slice-gamma-...-completion]` `[05]` §28, §2. Cross-ref G0 §1–§5. |
| **INV-3** | **One canonical apparatus/equipment identity.** Every schema's apparatus/sensor identity resolves to the single canonical identity; separate schemas are fine, divergent apparatus identity is forbidden. | Schema-role invariant (ARCHITECTURE Decision 010 elevating 003); structural precondition for on-demand-at-point-of-need retrieval. `[INFERENCE]` (substrate decision, not a TCC handoff — cross-ref G1 for the FK realization). |
| **INV-4** | **Engine source outranks DB description.** When the decompiled engine and an Access field DESCRIPTION disagree, the engine wins; record both and the win. | 00 §2 conflict rule. Flagship: `DS3_SEC3_I2T`/`DS1GF_SEC3_I2T` are DB-described "0 or 1" but the engine casts a 0..4 routing enum (`SSTDelayCalc`/`DB_SST_DLCALC_*`). `[DLL DeviceLibrary.cs:67-75]` `[09]` `[06]` |
| **INV-5** | **Access `D:\TCC_NEW.accdb` is the sole behavioral authority** (and `D:\EasyPower\11.0\Stdlib.mdb` for the calc-engine lane). The Supabase `tcc.*` catalog is a *persisted projection*; where it diverges from Access, Access is right and the projection is the bug. | Stated as a hard limit in every fidelity handoff. `[HANDOFF 2026-04-26-tcc-runtime-016-...]` `[07]` F-1; TASK-D names `Stdlib.mdb` runtime authority `[07]`. |
| **INV-6** | **The breaker→trip-unit stitch is application code, not a saved query.** The composite-key join (`BreakerXXXStyles.TMT_SST_{Mfr,Type,Style}` → `DatStyle(TYPE,STYLE)` → `STYLE_ID` → `DatSensor.StyleID`) is bound in `DevLibBreakerStyle.GetBreakerStyles` / surfaced by `GetDefaultTripInfo`, not in SQL. | Contract-DLL-authority revision: `DvlEng.dll` owns workflow shape, `DeviceLibrary.cs` owns SQL; runtime is a partial implementation. `[DLL DevLibBreakerStyle.cs:135-139]` `[DLL DeviceLibrary.cs:478]` `[HANDOFF contract-dll-authority-revision-completion]` `[05]` §6. Cross-ref G0 §3. |
| **INV-7** | **Deferred dispatch families are surfaced, never silently computed.** Sensors routing to a STUB/DIAGNOSTIC path (WEG OCR Type A, GE-TU, I2X-255, etc.) must emit "unsupported", not a default number. | Calc-engine field-trust rule R3. `[HANDOFF task-e-path-execution]` `[06]` (WEG N.4 → explicit diagnostic exclusion, no solver call). |

> **A note on INV-1 vs the Series B Excel:** the per-sensor `DatSensor` tolerance is authoritative
> *over* the Series B workbook — the workbook is **calibration-only** and was itself DB-derived; on any
> divergence the DB wins (cross-ref F-11). This is why the field-tolerance MVP treats DB per-sensor
> tolerances as the north-star and not the spreadsheet. `[HANDOFF task-d-...-handoff]` `[07]` F-11.

---

## 2. Frozen baselines — the locked states

Each row is a state a closed packet **froze**: what it froze, the provenance, and (where relevant) what
still rides *below* the frozen line. Mutating any of these requires a re-validating packet that amends
this guide first (SSoT Law §2).

| # | Frozen baseline | What it froze | Provenance |
|---|---|---|---|
| **F-1** | **Sole behavioral authority** | Access `D:\TCC_NEW.accdb` (79 user tables) is the behavioral authority; `Stdlib.mdb` for the calc-engine lane. No Phase work overrides Access. | every fidelity handoff `[07]` F-1; `[VERIFIED-LIVE 2026-05-31]` (00 §4) |
| **F-2** | **Phase 4 validated ETU baseline** *(THE keystone)* | Canonical `tcc_etu_*` tables; pre-rebuild preserved at `*_pre_rebuild`; view rebinds; ORM aliasing pattern; 5-file regression **67 passed / 2 skipped / 0 failed (8.02s)**; live anchors `4604` (cascade) + `16671` (override). Checklist **29 PASS / 2 CONDITIONAL PASS / 0 FAIL / 0 BLOCKED**. | Phase 4 evidence §6.1 `[HANDOFF 2026-04-26-tcc-phase-4-validation-and-acceptance-...]` `[07]` F-2 |
| **F-3** | **Atomic swap** | Maint-A compatibility bridge + **20 table renames** + view rebinds, executed atomically; canonical ETU names now point at the rebuilt source-faithful corpus. Post-swap regression **67/2/0**; Phase 4 entry = GO. | `[HANDOFF 2026-04-26-tcc-runtime-016-atomic-swap-prep-...]` `[07]` F-3 |
| **F-4** | **MAINT runtime contract** | `maint_*` + `params_json` materialized via a compatibility bridge from raw `tcc_etu_sensor_maint_v2` (NOT a pure-rename); consumers (`vw_sensor_calc_context` + MAINT SQL/Python) stable across cutover. | Runtime-016 MAINT decision `[07]` F-4 |
| **F-5** | **Runtime-contract trio part 1** | Delay-routing **codes, not booleans** (sensor-context aliases `stpu/gfpu_delay_calc_code` + `_name`); Python STPU override branch (5/5 tests on `12000A` / asym tol / `0.025`/`0.067`s); linked-selection contract; degraded-plug downgraded to **diagnostic-only** warning. Combined regression **59/59**. | `[HANDOFF 2026-04-26-tcc-runtime-015-...]` `[07]` F-5 |
| **F-6** | **SQL=Python override parity** | `fn_calculate_test_currents` honors the override branch identically to Python (anchor sensor `16671`); proven by `test_sql_rpc_matches_python_for_stpu_override_sensor_16671`. | Runtime-016 (TASK-012 part 2) `[07]` F-6 |
| **F-7** | **Tier A canonical renames** | `stpu_i2t → stpu_delay_calc_code` and `gfpu_i2t → ground_delay_calc_code` on the canonical ETU sensor surface; `COMMENT ON COLUMN` docs added; lineage proven to `DatSensor.DS3_SEC3_I2T` / `DS1GF_SEC3_I2T`; 5-file post-rename regression **67/2/0**; anchors `4604` + `16671` PASS. Audit-confirmed live still matches evidence. | `[HANDOFF 2026-04-26-tcc-phase-5-6-...]` + `[HANDOFF 2026-04-27-tcc-phase-5-tier-a-review-...]` `[07]` F-7 `[VERIFIED-LIVE 2026-04-27]` |
| **F-8** | **Split-anchor fixture policy** | `4604` = pickup/cascade anchor; `4174` = IEEE-depth anchor. `6258` is **pre-rebuild historical only** (absent from rebuilt-v2 corpus — cannot anchor rebuilt-state proof); `11442` rejected as substitute. `test_calc_engine.py` = historical lineage only. | Runtime 015/016 `[07]` F-8 |
| **F-9** | **Plug-fingerprint methodology** | Divergent-style count `290 / 1,801 / 2,091 = 86.13%` is the load-bearing **L1** metric; the `12,071 vs 720` distinct-sensor-fingerprint discrepancy is a **tokenization-artifact NOTE**, not L1 evidence. | Phase 4 §5.3 `[07]` F-9 |
| **F-10** | **Tier B read-models published side-by-side** | `vw_etu_calc_context` and `vw_etu_browse` exist and are lineage-proven, **but the runtime contract surfaces REMAIN `vw_sensor_calc_context` (context) + `vw_trip_unit_cascade` (browse/cascade)**. Tier B views are NOT adopted. | Tier B Slice 1/2 `[HANDOFF 2026-04-27-tcc-phase-5-tier-b-...]` `[07]` F-10 — FROZEN (NOT adopted); adoption gated, see §5 |
| **F-11** | **Series B calc-engine DB contract** | Full SE identity = `3000A + 4000A` (workbook `3600A` label = workbook-only divergence, **not** a DB override); DB-side is the **direct-band path** (`DatSection3STD` / `DatSection1GfGFD`), independent of unresolved InvEq; Full SE GFD `2000A` literal-amperes anchor; **rejects the workbook `12 × Plug` shortcut**; PX-6B ordinal-0 asymmetry preserved exactly; STPU dispatch `DS3_PICKUP_CALC = 1` (Series B). Row-for-row tuple parity SE `(10,10,2)` / MX `(6,6,1)` / PX-6B mixed `[(4,10,2),(10,10,2),(6,6,2),(6,6,2)]`. | TASK-D + TASK-H `[07]` F-11; `[06]` (TASK-C safe parity, 8 tests PASS) |
| **F-12** | **Decision-012 `tcc.*` schema unification** | Breaker `public.tcc_*` + relay `work.tcc_relay_*` unified into the **sole `tcc.*` schema** (Decision 010 apparatus-role). D2 = live-verified **189-mfr name-based remap** (averted 185-mfr corruption; **the 189 is a remap-operation scope count, NOT a table cardinality** — live `tcc.manufacturers` = **450** full Access mirror / **140** distinct `manufacturer_id` across the breaker/EMT/trip-type FK tables `[VERIFIED-LIVE 2026-05-31]`). CLOSED end-to-end: 60 tables → `tcc.*`; all back-compat views + 10 orphaned `_pre_rebuild` + 1 `_v2` dropped; all consumers (raw SQL + ORM, API + calc-engine) repointed; **10 MUST-KEEP `_pre_rebuild` pinned by `tcc_test_plans` FK (D1, retire later)**. | `[HANDOFF Decision-012 closeout]` (STATE §74-§89) `[INFERENCE]` (from substrate memory; not in artifacts 05/06/07 — cross-ref G1 for the schema realization) `[VERIFIED-LIVE 2026-05-30]` |
| **F-13** | **Program "closed-through-current-scope"** | All Phase 1–5 lanes closed; **ZERO blocked lanes**; **no implementation packet open by default**; only named conditional triggers may reopen lanes. Focused verification `pytest 23/23`. Preserved-verbatim rulings: DEC-005/008/010/012/013/021. | Program closeout `[HANDOFF 2026-04-29-tcc-program-closeout-...]` `[07]` F-12 |

> **Two CONDITIONAL-PASS items** ride below F-2 as the only non-PASS Phase-4 checklist outcomes (each
> carries a remediation/deferred owner). They are tracked, not unknowns. `[07]` §4.

---

## 3. Deferred-work ledger — what is OPEN + reopen triggers

**Rule of the ledger:** every item below reopens **only** via a separately-authored,
governance-controlled packet on the stated condition. *Nothing is open by default.* `[07]` Part 3.

### 3.1 Core deferred-work ledger (D-1 .. D-10, from artifact 07)

| # | Deferred item | Reopen trigger / condition | Tag | Status after recent discovery |
|---|---|---|---|---|
| **D-1** | Adopt `vw_etu_calc_context` into the runtime contract | A packet records a concrete consumer that natively assembles sensor-context **+** all per-sensor `ltd_params` curves in one shot **AND** proves the −1 RTT saving outweighs per-call server-side slowdown for that consumer's sensor mix | `[DEFERRED]` CONDITIONAL-TRIGGER (HOLD) | unchanged |
| **D-2** | Adopt `vw_etu_browse` into the runtime contract | A packet records **(a)** a concrete one-call child-relation-flags consumer **AND (b)** a published **trip-type identity harmonization** decision (expose `trip_type_id` w/o the legacy natural-key CTE, **or** migrate cascade models to `trip_type_name`) | `[DEFERRED]` CONDITIONAL-TRIGGER (HOLD) | unchanged — harmonization gate still binding (§5 gate 2) |
| **D-3** | Tier B Slice 3 (materialized facets / facet counts) | A measurement packet records **(a)** a measured browse-latency target **OR (b)** a documented operator-simplicity target. **Both currently NOT SET** (`/cascade` warm exec already <5ms; no documented pain point) | `[DEFERRED]` CONDITIONAL-TRIGGER (GATED) | unchanged |
| **D-4** | TASK-E inverse-equation **scoping** | Future scoping packet referencing DEC-021 §12/§8 anchors — **now OPTIONAL** (TASK-E *execution* itself has landed, 43/43) | `[DEFERRED]` CONDITIONAL-TRIGGER (optional) | superseded by execution; only re-scoping is optional |
| **D-5** | Spec line 766 rewrite | Future spec-rewrite (TASK-G-equivalent) packet — **bookkeeping only**; DEC-021 explicitly leaves spec line 766 unchanged | `[DEFERRED]` CONDITIONAL-TRIGGER (cosmetic) | unchanged |
| **D-6** | TASK-F fixture generation | Future fixture-generation packet | `[DEFERRED]` CONDITIONAL-TRIGGER | unchanged |
| **D-7** | Phase 7 cleanup (TASK-022 / 023 / 024) | Future Phase 7 cleanup packet | `[DEFERRED]` CONDITIONAL-TRIGGER | unchanged |
| **D-8** | `_009_rollback_snapshot` retention review | The 2026-05-02-dated retention review (memory-tracked); read-only keep-vs-retire draft | `[DEFERRED]` CONDITIONAL-TRIGGER (dated) | unchanged |
| **D-9** | Phase 6 items (cross-family FK retarget, dropped-UI-view rebuild, non-runtime ORM realignment) | Authorized in principle by Phase 4 §6.2 but never opened; subsumed under Phase 7 cleanup posture | `[DEFERRED]` | partly overtaken by F-12 `tcc.*` unification (FK retarget realized there — cross-ref G1) |
| **D-10** | Tier C normalization probes **+** the Phase 5A **No-Go list** | Explicitly out of scope throughout; **no reopen authorized** | `[DEFERRED]` (No-Go) | unchanged |
| **—** | **RETIRED — Trigger #3: breaker-side hierarchy ownership** | Satisfied 2026-04-29 via contract-authority revision → scoping ruling → Slice α/β/γ chain | CLOSED | see §3.2 — the SST-bridge discovery is a *candidate new* product-direction trigger that re-elevates this surface (item-1 PARTIAL), distinct from the retired Trigger #3 |

### 3.2 Breaker→trip-unit bridge — the 5-gate acceptance list (from artifact 05)

The deferred breaker-style → trip-style/sensor **bridge** ("available but not currently desired", Lane-1
completion §5) carries a **pre-registered 5-gate acceptance list** — the program's own criteria for
lifting the manufacturer-axis ceiling to true breaker-style→sensor narrowing. `[HANDOFF schema-augmentation-lane1-ac-dc-code-completion]` `[05]` §3.

| Gate | Requirement | Status after the `TMT_SST_*` discovery |
|---|---|---|
| **BG-1** | Resolve `BreakerStyles_Union_Table_Dedup` family-discriminator semantics | **Likely MOOT / BYPASSED** — the live stitch is the `TMT_SST_*` name-composite columns + app code, not these staging tables. `[INFERENCE]` `[05]` §4 |
| **BG-2** | Resolve `BreakerHierarchy_Flat` child-edge column semantics | **Likely MOOT / BYPASSED** — same reason as BG-1. `[INFERENCE]` `[05]` §4 |
| **BG-3** | **Prove a real breaker-style → ETU `DatStyle.STYLE_ID` / trip-style / sensor mapping for representative devices** | **SUBSTANTIALLY ANSWERED / UNBLOCKED** — the mapping IS `BreakerXXXStyles.TMT_SST_{Mfr,Type,Style}` → `DatStyle(TYPE,STYLE)` → `DatStyle.STYLE_ID` → `DatSensor.StyleID`; worked example `T8V-1600` → ABB PR332/P → 1 `DatStyle` (1230) → 5 sensors. `[VERIFIED-LIVE 2026-05-31]` `[04]` `[05]` §4. Cross-ref G0 §3 |
| **BG-4** | Define a **dedicated bridge surface** (e.g. `vw_etu_breaker_contract_bridge`) instead of overloading the present CTE | **✅ MET 2026-06-01 (D1, migration `006`).** New view **`tcc.vw_breaker_sst_bridge`** (breaker class/id/style_id/frame + tmt_sst triple → trip_style_id → sensor_id/rating); does NOT overload `vw_trip_unit_cascade`. Fed by the re-carried `tmt_sst_*` cols. 4,253 breaker styles → 388 trip_styles → 2,922 sensors. Match-rates ICCB 100 / MCCB 95.6 / PCB 97.5% (non-null) == Access live-join. `[VERIFIED-LIVE 2026-06-01]` |
| **BG-5** | Only then move the ETU UI beyond manufacturer-axis disclosure | **UNBLOCKED, not yet done.** BG-4 + the dropped-column reload (§4.3) are DONE, so the data foundation exists; the remaining work is the **UX wiring on operations-web** to consume `vw_breaker_sst_bridge` — the separate **Phase D** follow-on packet. Deployed cross-filter stays manufacturer-axis only until then. `[05]` §28 |

> **The dropped-column root cause (the discovery's headline):** the 4 bridge columns
> (`tmt_use_sst`, `tmt_sst_mfr`, `tmt_sst_type`, `tmt_sst_style` on `BreakerXXXStyles`) were
> **dropped during the Access→Supabase load** (a loader expecting numeric `Manufacturers.ID` silently
> dropped the name-composite key). This re-characterizes Slice γ's "manufacturer-axis ceiling … within
> the persisted schema's structural ceiling" from *an inherent data gap* to *recoverable by reloading
> dropped source columns.* `[HANDOFF stage1-slice-gamma-...-completion]` `[05]` §28 §4; cross-ref G0 §3
> + G1 dropped-column register + §4.3 below.

### 3.3 Calc-path deferrals (from artifact 06)

The calc/InvEq lane has its **dispatch/routing** proven but several **numerical** and **solver** paths
deferred. A field-tolerance sheet must respect every "DEFERRED/STUB" row (INV-7). `[06]` solver matrix.

| # | Calc deferral | Reopen trigger / condition | Tag |
|---|---|---|---|
| **D-11** | **InvEq numerical parity** — `IEEEInverseTimeSolver` vs EasyPower native `CalcThermEq`/`CalcAnsiEqGF` on ~6,200 InvEq sensors (4,524 STD-side + 1,713 GF-side) | Captured EasyPower point fixtures remain the gate before InvEq TD windows ship on a field sheet | `[DEFERRED]` `[06]` — **PRECISELY CHARACTERIZED 2026-05-31, SPLIT + PATCHED 2026-06-01** (G4 §3e/§5): corpus = **STD 100% Therm, GF 8,450 Therm + 100 Ansi ROWS / 23 sensors / 3 trip styles**. `CalcThermEq` was recovered from `TccBase.dll` and uses `c4/c5` (`rIref`/`rM`); `IEEEInverseTimeSolver` now dispatches Therm-shaped rows to the recovered formula. `CalcAnsiEqGF` was also recovered (`A + B/(I-C) + D/(I-C)^2 + E/(I-C)^3`, with tolerance-adjusted current and `Tmin` floor), but the Ansi family remains hard-excluded through `gf_inveq_is_excluded_ansi` / `id_open_eq` until a family-aware solver path has captured EasyPower fixtures. Focused tests: `test_source_faithful_adapters.py` + `test_etu_delay_routing.py` = 12/12. Residual: captured EasyPower point fixtures and final field-sheet trust promotion. `[VERIFIED-LIVE 2026-06-01]` |
| **D-12** | **GE-TU-STD / GE-TU-Gnd solver** (`SSTDelayCalc = 3 / 4`; `DS1GF_SEC3_I2T = 4` TUG) | A dedicated solver RE/implementation packet; currently diagnostic fall-through only | `[DEFERRED]` (NOT IMPLEMENTED) `[06]` |
| **D-13** | **I2X = 255 solver** (§N.2) | I2X open question never closed; needs its own RE pass | `[DEFERRED]` `[06]` |
| **D-14** | **WEG OCR Type A pickup** (`DS1GF_PICKUP_CALC = 6`, §N.4) — 7 SensorIDs | Pickup formula UNKNOWN; only a separate RE pass lifts the exclusion. Until then **hard-exclude** these sensors (show "unsupported") | `[DEFERRED]` (STUB/DIAGNOSTIC) `[06]` (INV-7) |
| **D-15** | Other §N open questions — `DS3_I2T_TYPE=10` (N.1), `DS2_DLY_PTY`/LTD delay-parity (N.3), `Sec4Inst*` INST curve-calc (N.5); plus §G/§J InvEq Paths 1&3, §K override math | Each a fresh blocker if a driving job's sensors hit it; characterize per-element before computing | `[DEFERRED]` `[06]` |
| **D-16** | `*ICalc = 0 → byICalc = 2` branch DB-fact check | Pass-5 proved the translator (`FUN_01208640`); whether any DB row stores `*ICalc=0` is an unverified **DB-fact** question (risk R4) | `[OPEN-VALIDATION]` `[06]` |

> **What the recent discovery does NOT unblock:** the `TMT_SST_*` bridge discovery is a *selection*
> finding. It does **not** touch any calc deferral D-11..D-16 — InvEq numeric parity and the unsolved
> solvers remain exactly as deferred. Bridge progress lets you *reach the right sensor*; it says nothing
> about whether that sensor's curve numbers are field-trustworthy. `[INFERENCE]`

### 3.4 Residual-risk register (R-1 .. R-8)

The keystone closeout artifact records **8 named residual risks R-1 .. R-8** (closeout §5). The
**per-risk prose lives only in the host-only `neta-ett-study-material` artifact**, which is **not on this
filesystem** — so the individual R-n statements cannot be transcribed here. `[OPEN-VALIDATION]`
`[HANDOFF 2026-04-29-tcc-program-closeout-...]` `[07]` (Provenance caveat). The calc-lane risks R1–R5
in artifact 06's synthesis (IEEE-solver parity, thin cohort, deferred fall-through, `*ICalc=0` DB-fact,
reference-of-record drift) are a *distinct, separately-sourced* risk list and are captured as D-11/D-16
above and §4.1 below — they are **not** assumed identical to closeout R-1..R-8.

---

## 4. Governance rules

### 4.1 Reference-of-record vs forward-port

**The behavior authority for the calc/InvEq runtime is the source-domain demo, not the deployed app.**
The deployed app is a **lagging forward-port.** `[06]` (risk R5).

- **Reference-of-record (authoritative for behavior):** `source-domains/tcc_v5_backend/services/calc_engine/`
  — `etu_delay_routing.py` (InvEq dispatch) + `etu_curves.py` (`IEEEInverseTimeSolver` kernel) + the
  `EASYPOWER-CALC-ENGINE-SPEC.md` contract. `[06]` Provenance Notes.
- **Forward-port (lagging target):** the deployed application surface. A "remembered-better-state" gap is
  a **lagging-port gap, NOT an in-repo regression** — resolve via function-level diff against the
  reference-of-record, not git archaeology. `[HANDOFF TCC-Runtime-017]` `[INFERENCE]`
- **Operating rule:** any field-sheet generator must consume the **current dispatcher**
  (`etu_delay_routing.py`), never a stale forward-port copy. Verify the consumed module before shipping.
  `[06]` R5.

### 4.2 The "silent gap below a frozen baseline" rule *(the dropped-column case)*

> **Rule:** A frozen baseline freezes a corpus **as loaded.** If a *source* column/row was dropped
> *before* the freeze, that loss is a **silent gap below the frozen line — not a tracked deferral** — and
> it requires **its own governance entry** to become visible. A frozen-baseline statement is **not** a
> warranty that the load was complete.

**Worked example (load-bearing):** the Phase-4 baseline (F-2) froze the `tcc_etu_*` corpus *as loaded*.
The 4 SST-bridge columns (`tmt_use_sst`, `tmt_sst_mfr/type/style`) were dropped during the
Access→Supabase staging load. **No frozen-baseline statement covers that loss** — none of the 16
fidelity/closeout handoffs even mention those columns. Therefore the dropped columns are **not** D-1..D-10;
they are a silent gap that this guide now surfaces as a governance entry (see §4.3). `[HANDOFF 2026-04-29-...closeout]`
`[07]` (discovery-context note); `[05]` §28; cross-ref G0 §3.

### 4.3 SST-bridge dropped-column governance entry *(new, surfaced by §4.2)*

| Field | Value |
|---|---|
| **What was dropped** | `tmt_use_sst`, `tmt_sst_mfr`, `tmt_sst_type`, `tmt_sst_style` on `tcc.brk_{iccb,mccb,pcb}_styles` (the `BreakerXXXStyles.TMT_SST_*` name-composite bridge key). |
| **When/why** | At the Access→Supabase load; a loader expecting numeric `Manufacturers.ID` silently dropped the manufacturer-**name** composite key. `[VERIFIED-LIVE 2026-05-31]` `[05]` §8 |
| **Impact** | The deployed cross-filter is **manufacturer-axis only** (cannot collapse 7,271 breaker styles to the compatible-sensor set). Blocks the field-tolerance MVP's breaker→compatible-sensor narrowing. `[05]` §28; cross-ref G0 §3 |
| **Status** | **✅ RECOVERED 2026-06-01 (D1, migration `006_brk_styles_sst_bridge.sql`).** The 4 cols re-carried (source-faithful NAME strings, NOT coerced to FK) on all 3 style tables via the proven `rank=id` mapping; BG-4 surface `tcc.vw_breaker_sst_bridge` built; the 325 day-one orphan MCCB styles repointed (0 orphans). `tmt_use_sst` true = 1704/515/3193. Match-rates ICCB 100 / MCCB 95.6 / PCB 97.5% (non-null) == Access live-join; `T8V-1600`→ABB PR332/P→5 sensors live. **Residual:** `source_id` bulk-population DEFERRED (ready file; rank=id is the proven provenance); **D4** `TMT_*` helper cols still OPEN (co-located, not re-carried); **BG-5** UX wiring = Phase D. `[VERIFIED-LIVE 2026-06-01]` |
| **Owner / cross-refs** | G1 **dropped-column register** (schema realization) · G0 §3 (the bridge mechanism) · §3.2 BG-1..BG-5 (acceptance gates) · §3.1 RETIRED-Trigger-#3 (the product-direction trigger that re-elevates this). |

### 4.4 Authoritative-vs-inference tagging policy

1. **Tag everything load-bearing.** Every non-trivial claim carries exactly one provenance tag (00 §2).
2. **Record both sides of a conflict and the win.** Per INV-4, when `[DLL]` and `[DVL-DB]` disagree,
   write down both values and which one wins. Do not silently drop the loser.
3. **`[INFERENCE]` is provisional.** Control-flow-inferred-from-decompile or reasoned-from-evidence claims
   are `[INFERENCE]` / `[INFERENCE-ONLY]` and must **not** be promoted to binding parity. The calc lane
   held this line rigorously — every InvEq handoff stated "no parity claim" explicitly. `[06]`
4. **`[OPEN-VALIDATION]` is honest absence.** Where a fact cannot be validated from currently-accessible
   sources (host-only artifacts, off-disk DLLs, unproven numerics), tag it `[OPEN-VALIDATION]` rather than
   guessing — and register it in 00 §5.
5. **Date what you validate.** `[VERIFIED-LIVE <date>]` carries the check date; stale = re-validate, never
   assume current (SSoT Law §4).

### 4.5 The Single-Source-of-Truth Law (cross-ref 00 §1)

This guide is the *settled/frozen/open* authority, but it lives **under** the SSoT Law in 00:

1. **Cite before you build** — every TCC packet names the guide section(s) it depends on.
2. **Update before you work around** — if a packet finds reality diverging from a guide, its **first
   deliverable** is the guide correction with new provenance, *not* a silent workaround. (This is exactly
   how §4.3 came to exist: the dropped-column discovery's first deliverable is this governance entry, not
   a quiet schema patch.)
3. **No orphan truth** — handoffs and discovery artifacts (05/06/07) are **evidence**, not the source of
   truth; they feed the guides.
4. **Date what you validate** — see §4.4.5.

### 4.6 Governed-load unique-key drop governance entry — `tcc.brk_mccb` AC/DC twins *(new 2026-06-01, lean 2)*

A second instance of the §4.2 "silent gap below a frozen baseline" rule (the first was §4.3's dropped SST
bridge columns). Surfaced + characterized under §98 lean 2.

| Field | Value |
|---|---|
| **What was dropped** | **41 of 640 `BreakerMCCB` parent rows** did not load into `tcc.brk_mccb` (599 present before remediation). `[VERIFIED-LIVE 2026-06-01]` |
| **Root cause** | The governed table carries `UNIQUE (manufacturer_id, name)`, but the Access natural key is the **4-tuple `(Mfr_ID, Type, cStandard, Acdc)`** (0 dups there; unique only at the full tuple). 43 `(Mfr_ID, Type)` pairs have a second row differing **only by `Acdc` (AC↔DC) and/or `cStandard` (ANSI↔IEC)** — e.g. ABB `Formula`/`Tmax [IEC]`, GE `E100`, Siemens `Sentron`. The too-narrow unique index collapsed them. **41, not 43:** 2 pairs survived because their `name` differs only by letter-case (`Multi 9`/`MULTI 9`, `ComPact [IEC]`/`COMPACT [IEC]`) — Access groups case-insensitively, the Postgres unique index is case-sensitive. `[VERIFIED-LIVE 2026-06-01]` |
| **NOT the D1 cause** | This is **not** the D1 manufacturer-name-vs-id drop: `manufacturer_id` is preserved 1:1 (Access `Mfr_ID` == Supabase `manufacturer_id`) and all FKs resolve. `brk_iccb` (29→29) and `brk_pcb` (157→157) loaded fully — they have **no** `(Mfr_ID, Type)` collisions. |
| **Impact** | Mostly the **DC twin** (and some IEC twin) of a manufacturer+type is missing; `ac_dc_code`/`standard` exist as columns but were not part of the dedup key. Low impact for AC LV NETA work; a real catalog-completeness gap for DC / IEC selection. |
| **Status / remediation** | **✅ CLOSED 2026-06-01.** Migration `infra/database/migrations/tcc/005_brk_loadpath_unique_key_reload.sql` dropped the old `(manufacturer_id, name)` keys, added `UNIQUE NULLS NOT DISTINCT (manufacturer_id, name, standard, ac_dc_code)` on `brk_{mccb,iccb,pcb}`, normalized existing parent rows (MCCB 121, PCB 10), and inserted the 41 missing MCCB twins. Final live counts: `brk_mccb` 640/640, `brk_iccb` 29/29, `brk_pcb` 157/157; each Access 4-tuple present exactly once. |
| **Cross-refs** | §4.2 (the silent-gap rule) · §4.3 (the sibling SST-bridge entry) · G1 load-delta register · the breaker load-path packet. |

### 4.7 Deployed-catalog RLS posture — public read-only, service-role writes *(decided + applied 2026-06-01, lean 3)*

The governed `tcc.*` catalog's row-level-security posture, completed under §98 lean 3.

| Field | Value |
|---|---|
| **Posture (now uniform)** | **Public read-only reference catalog, service-role writes.** Every `tcc.*` table carries two policies: `tcc_<t>_select` (`FOR SELECT TO public USING (true)`) + `tcc_<t>_service` (`FOR ALL ... USING (auth.role() = 'service_role')`). This was the **established** pattern on 12 tables (brk_*/tmt_*/trip_types); lean 3 applied the identical pattern to the remaining 48 so all **60/60 are RLS-on with ≥2 policies** (0 RLS-off, 0 RLS-on-without-policy). `[VERIFIED-LIVE 2026-06-01]` |
| **Why safe / behavior-preserving** | Grants were **not** touched. The advisor finding was **defense-in-depth, not an active leak**: `anon` lacks `USAGE` on schema `tcc` (verified — `SET ROLE anon` → "permission denied for schema tcc"), so anon never reached `tcc.*` directly; the live explorer reads via the privileged/service-role path, which the `_service` policy preserves (privileged sanity reads post-change: `etu_sensors`=17,831, `relay_devices`=6,850). |
| **What it closes** | The Supabase security advisor `rls_disabled_in_public` for all 48 previously-RLS-off `tcc.*` tables (27 ETU/EMT/`manufacturers`/`trip_styles` + 21 `relay_*`). Migration `tcc_enable_rls_public_read_catalog_lean3` (idempotent). |
| **Deliberately NOT changed** | The 21 `relay_*` tables have **no `anon` SELECT grant** (backend-only) — left as-is. If the relay explorer is meant to be client-side/anon like the breaker explorer, that is a **separate, deliberate exposure decision** (a grant change), not part of closing the RLS advisor. Flagged for the operator. |
| **Cross-refs** | G1 (deployed `tcc.*` catalog) · the 12-table precedent this completes. |

---

## 5. Adoption gates — conditioning Tier-B view adoption

A recurring, load-bearing pattern: **build-and-prove is decoupled from adopt.** Every Tier-B view
(`vw_etu_calc_context`, `vw_etu_browse`) was authored, lineage-proven, and published *side-by-side* — but
**none is wired into the runtime contract** (F-10). Three **nested** gates govern any future adoption; all
must clear. `[07]` Part 4.

| Gate | Name | Condition (must hold to adopt) | Current state |
|---|---|---|---|
| **AG-1** | **Consumer-need gate** | A **file-backed, on-disk consumer** must exist that needs the view. Diagnostic EXPLAIN / RTT probes do **NOT** count as a consumer or as a performance target. | **NONE FOUND** for either view (repo-wide grep + live `/context` + `/cascade` + calc-engine `etu_ltd.py` direct-access path reviewed). HOLD persists. `[07]` |
| **AG-2** | **Trip-type identity harmonization gate** *(browse-specific)* | `vw_etu_browse` adoption is **additionally** blocked until a separately-governed decision resolves `trip_type_id` (int FK, required by `/cascade` + `CascadeTripType` + `CascadeSensor`) **vs** the view's `trip_type_name`. | UNRESOLVED — `vw_etu_browse` omits `trip_type_id`, exposes `trip_type_name`. Binding prerequisite for D-2. `[07]` |
| **AG-3** | **Measurement gate** *(Slice 3)* | Facet/materialization work stays GATED until a **measured browse-latency target OR a documented operator-simplicity target** is recorded. Inventing one violates the hard limits. | **Both NOT SET.** `/cascade` warm exec already <5ms; Slice-1/2 numbers are diagnostic EXPLAIN probes, not thresholds; zero frontend references to the Slice-2 five-flag set. Slice 3 GATED. `[07]` |

**Runtime contract surfaces that REMAIN authoritative pending all gates:** `vw_sensor_calc_context`
(context) and `vw_trip_unit_cascade` (browse/cascade). `[07]` Part 4.

> **Note — adoption gates (Tier-B views) vs bridge gates (§3.2):** AG-1..AG-3 condition *adopting an
> already-built derived view into the runtime*. BG-1..BG-5 condition *building the breaker→sensor bridge
> in the first place*. They are independent gate families; the `TMT_SST_*` discovery moves BG-3 but does
> **not** touch AG-1..AG-3. A bridge would be a **new lane built ON TOP of** Slice α's `etu_breaker_combined`
> CTE, not a reopening of α/β/γ (which remain validly closed). `[05]` §4.

---

## 6. Cross-references

- The three trip families + the breaker×family interaction matrix + the bridge mechanism → **G0**.
- Schema realization of every frozen table, the `tcc.*` unification, and the **dropped-column register**
  (the schema side of §4.3) → **G1**.
- Selection-routing + calc-dispatch constant tables (`SSTCalcMethod`, `SSTDelayCalc`) → **G3**.
- Per-family pickup/delay formulas + the **field-trust matrix** (proven | bounded | deferred | stub) that
  realizes D-11..D-16 → **G4**.
- The SSoT Law, provenance-tag definitions, evidence base, and open-validation register → **00**.

---

## Appendix — Evidence base for this guide

| Artifact | Contributes |
|---|---|
| `_discovery/07-handoffs-digest-fidelity-phases-closeout.md` | Frozen baselines F-1..F-13, deferred ledger D-1..D-10, adoption gates AG-1..AG-3, R-1..R-8 register (host-only), the silent-gap discovery-context note (§4.2). **Keystone.** |
| `_discovery/05-handoffs-digest-selection-crossfilter.md` | Invariants INV-1/2/6, the 5-gate bridge list BG-1..BG-5, the manufacturer-axis ceiling history, what `TMT_SST_*` reopens/supersedes (§3.2, §4.3). |
| `_discovery/06-handoffs-digest-calc-inverse-equation.md` | Invariant INV-7, calc deferrals D-11..D-16, the reference-of-record vs forward-port rule (§4.1), the calc-lane risk list. |

*G2 authored 2026-05-31 (agent draft). Read-only on all sources. Pending Desktop validation — bump the
header `Last validated` line and resolve the four open gaps on acceptance.*
