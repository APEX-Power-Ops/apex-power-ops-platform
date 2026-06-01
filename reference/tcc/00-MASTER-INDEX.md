# TCC Master Reference — Master Index

> **This is the single source of truth for the EasyPower-derived TCC (Time-Current Curve) domain
> of the APEX power-ops platform.** Every TCC packet, dispatch, build step, and review starts here
> and cites the guide section it relies on. If reality and a guide disagree, the guide is fixed
> *first* (see the Single-Source-of-Truth Law below) — never silently worked around.

- **Status:** UNDER CONSTRUCTION — all guides DRAFTED 2026-05-31; **G0/G3/G4 validated vs the `EasyPower.DeviceLibrary` primary source · G1 vs live `tcc.*` (60 tables/0 views)** · G1/G2 deep-validation + full ratification in progress
- **Owner:** APEX TCC lane (Desktop authors; executors cite + amend)
- **Home:** `apex-power-ops-platform/reference/tcc/` (version-controlled, beside the packets that cite it)

---

## 0. Why this exists (read this first)

This project reached "the cusp" more than once and fell back to a fresh start. The cause was not
engineering — it was **memory loss**: hard-won details (how the breaker selects a trip unit, which
column routes which solver, which numbers are validated) were rediscovered, re-litigated, and lost
again until restarting was the only option. This reference is the mechanism that makes the *next*
build the *last* rediscovery. Its value is not in being written once; it is in **staying true** and
**grounding every step**.

---

## 1. The Single-Source-of-Truth (SSoT) Law

1. **Cite before you build.** Every TCC packet/dispatch names the guide section(s) it depends on.
2. **Update before you work around.** If a packet finds reality diverging from a guide, its **first
   deliverable** is the guide correction — with new provenance — *not* a silent workaround. Drift
   cannot accumulate because correcting the map is step one of every change.
3. **No orphan truth.** A fact that matters lives in a guide, tagged with its source. Scratch notes,
   handoffs, and discovery artifacts are *evidence*, not the source of truth — they feed the guides.
4. **Date what you validate.** Live-verified claims carry the date they were checked. Stale = flagged
   for re-validation, never assumed current.

---

## 2. Provenance & status tags (used on every load-bearing claim)

Every non-trivial statement in a guide carries one tag so any reader can re-verify it:

| Tag | Meaning |
|---|---|
| `[VERIFIED-LIVE <date>]` | Re-queried against the live source (Access `D:\TCC_NEW.accdb` via OLEDB/DAO, or governed Supabase `fxoyniqnrlkxfligbxmg`) on that date. |
| `[DLL <file:line>]` | Recovered from decompiled EasyPower source under `D:\Access DB\DLL Decomp\`. |
| `[DVL-DB <table.col>]` | From an Access field DESCRIPTION (the design-layer "DVL flag" metadata). |
| `[HANDOFF <id>]` | Established by a prior dispatch closeout under `ops/agents/handoffs/`. |
| `[INFERENCE]` | Reasoned from evidence, not directly attested — treat as provisional. |
| `[DEFERRED]` | Known-incomplete by decision; see the deferred-work ledger (G2). |
| `[OPEN-VALIDATION]` | Cannot be validated from currently-accessible sources (e.g. needs the host-only `neta-ett-study-material` artifacts). |

**Conflict rule:** when sources disagree, **engine source (`[DLL]`) outranks DB description (`[DVL-DB]`)
outranks inference.** The flagship case: `DS3_SEC3_I2T`/`DS1GF_SEC3_I2T` are described "0 or 1" in
the DB but the engine casts them to a 0..4 routing enum — the engine wins. Record both and the win.

---

## 3. The guide map

| Guide | Owns | Cite it when… | Status |
|---|---|---|---|
| **[G0 — Trip-Family Model](G0-TRIP-FAMILY-MODEL.md)** | The three trip families (SST/ETU · TMT · EMT) and **how breaker selection does/doesn't determine the trip** for each | deciding selection/compatibility behavior across breaker ↔ trip-unit | **DRAFT · ✅ validated vs DeviceLibrary 2026-05-31** |
| **[G1 — Schema Guide](G1-SCHEMA-GUIDE.md)** | The data model end-to-end (Access → staging → Supabase `tcc.*`), the full join graph, the **DVL-flag data dictionary**, source→persisted lineage + the **dropped-column register** | touching tables/columns, loaders, or migrations | DRAFT · ✅ validated vs live `tcc.*` |
| **[G2 — Rules Guide](G2-RULES-GUIDE.md)** | Invariants, frozen baselines, the deferred-work ledger + reopen-triggers, governance (incl. reference-of-record vs forward-port) | deciding whether something is settled, frozen, or open | DRAFT · synthesized ledger (deep-validation pending) |
| **[G3 — Routing Guide](G3-ROUTING-GUIDE.md)** | **Selection routing** (cascade, the GetDefaultTripInfo stitch, cross-filter) and **calc-dispatch routing** (`DS*_PICKUP_CALC`→SSTCalcMethod, `DS*_SEC3_I2T`→SSTDelayCalc) | building/altering a selection flow or a calc dispatch | DRAFT · ✅ validated vs DeviceLibrary 2026-05-31 |
| **[G4 — Calc Guide](G4-CALC-GUIDE.md)** | Pickup formulas, tolerance derivation, the delay/curve solvers, and the **field-trust matrix** (proven \| bounded \| deferred \| stub) | computing or shipping any pickup/delay/tolerance value | DRAFT · ✅ validated vs SSTSensorRecord 2026-05-31 |

---

## 4. Evidence base (the research the guides synthesize)

**Discovery artifacts** — `C:\Users\jjswe\Box\TCC_Master\_discovery\` (raw research; cited by the guides):

| # | Artifact | Source |
|---|---|---|
| 01 | `01-access-tables-inventory.md` | Access table CSV exports — table/column inventory + linkage map |
| 02 | `02-access-queries-joinmap.md` | 33 saved Access queries — join graph |
| 03 | `03-dll-decomp-sql-workflow.md` | DLL decomp — SQL + the breaker→trip-unit app-code stitch |
| 04 | `04-accdb-relationships-population.md` | Live `.accdb` — declared FKs, bridge population, join match-rates, `T8V-1600` worked lookup |
| 05 | `05-handoffs-digest-selection-crossfilter.md` | Prior decision history — selection/cross-filter rulings |
| 06 | `06-handoffs-digest-calc-inverse-equation.md` | Prior decision history — calc/inverse-equation, solver coverage |
| 07 | `07-handoffs-digest-fidelity-phases-closeout.md` | Prior decision history — frozen baselines + deferred-work ledger |
| 08 | `08-dvl-flag-dictionary.md` (+ `_dvl_raw.csv`, `_all_fields.csv`) | Live `.accdb` design layer — field descriptions (DVL flags), 110 described / 952 total fields |
| 09 | `09-dvl-constants-and-enums.md` | DLL decomp — authoritative `DVL_SST_SETTING_*` / `SSTDelayCalc` constant tables |

**Authoritative live/source surfaces:**
- Access master: `D:\TCC_NEW.accdb` (79 user tables; sole behavioral authority) — query read-only via `Microsoft.ACE.OLEDB.16.0` / DAO 120.
- Decompiled engine: `D:\Access DB\DLL Decomp\` (EasyPower.DeviceLibrary etc. — the managed mirror of the calc/selection logic).
- Governed Supabase: project `fxoyniqnrlkxfligbxmg`, schema `tcc.*` (the deployed persisted catalog).
- Reference-of-record runtime: `source-domains/tcc_v5_backend/` (the demo + `DLL_END_TO_END_MAPPING.md` + `DLL_SEMANTIC_FINDINGS.md`).

---

## 5. Open-validation gaps (honesty register)

These cannot be fully closed from currently-accessible sources and are tagged `[OPEN-VALIDATION]` wherever they appear:

- **`neta-ett-study-material` is host-only** — not on this clone. The calc-engine spec (§G/§J/§N/§O), the breaker-trip-unit workflow audit, and the `R-1..R-8` risk register live on the Olares host; guides cite the handoffs' verbatim excerpts until the host artifacts are read.
- **InvEq numerical parity** — the inverse-equation *dispatch* is proven, but the emitted curve/delay **numbers** (~6,200 sensors) were never validated row-for-row against EasyPower's native kernel. This is the #1 calc gap (see G4).
- **EMT breaker-selection edge** — how a breaker selects an EMT trip is not yet mapped (see G0).
- **No physical `.h` headers** — the constants the DB defers to ("source header files") survive only as the decompiled C# mirror; that mirror is treated as authoritative (`[DLL]`).

---

## 6. Maintenance

- Each guide carries a header: `Last validated · Validator · Open gaps`.
- `STATE.md` / `APEX_RESUME.md` (substrate) point at this index as TCC ground truth so every session boots into it.
- When a guide changes, bump its header date and note what was re-validated.
