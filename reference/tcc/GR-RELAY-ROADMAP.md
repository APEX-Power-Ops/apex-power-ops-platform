# GR Relay Roadmap — bringing the relay TCC lane to breaker parity

> **The forward tracker for the relay half of the TCC product.** The relay parallel to the
> breaker journey (G0–G4 → the `lvbreakertcc` field sheet). We chip away systematically,
> **smallest durable bites first**; every closed bite lands in **GR / G4 first** (SSoT Law)
> so coverage is permanent — we never re-derive from the source. Cite this like any guide.

- **Status:** LIVING TRACKER — created 2026-06-03. Re-confirm counts live (`[VERIFIED-LIVE]`) when a chip is scheduled.
- **Home:** `apex-power-ops-platform/reference/tcc/` · linked from `00-MASTER-INDEX.md`.
- **Pairs with:** `GR-RELAY-REFERENCE.md` (the relay G0–G4) and `TOLERANCE-COVERAGE-PUNCHLIST.md` **L10** (the relay fidelity close — analytical curves BOUNDED until the native kernel is recovered). This roadmap owns the **product-maturity** climb; L10 owns the **fidelity** climb; they meet at Chip 5.

---

## The north star (relay end-state = breaker parity)

A NETA tech opens a **`relaytcc` field sheet**, picks any protective relay through structured
(no-free-text) dropdowns, and gets — **per ANSI protection function** (51, 50, 51N, 49,
67…) — the **pickup/tap + time-dial + NETA tolerance bands + test points + the curve**, every
value **field-trust-gated** (`db` / `verify` / `withheld`), sourced from the validated GR/G4
SSoT. Same bar as `lvbreakertcc`, shaped for relays.

## Relay-specific shape (why it is NOT a copy of the breaker page)

1. **Selection cascade differs:** `Mfr → Type → Device Function → Single/Multi → CT → Trip` —
   shorter than the breaker `Class→Mfr→Type→Style`; **no Class/Style/Standard** dropdown.
   ANSI-vs-IEC is pushed into the **device-function suffix** + the **Curve** list. (GR §1)
2. **The "elements" are ANSI functions**, not LTPU/STPU/INST — the test form is pickup +
   **timing at multiples of tap**, per function (51 time-OC, 50 inst-OC, 49 thermal, …).
3. **The trustworthy layer is stored DATA, not the formula** — stored discrete settings +
   the raw Time/Current point grid (Model 1 TCP) are `db`; the analytical curve is the part
   that is bounded. (Inverse of the breaker, where the recovered formula was the spine.) (GR §6)
4. **Tolerance data source is an OPEN question** — the breaker DB carried per-sensor
   tolerances; relays likely need **per-manufacturer accuracy specs** (datasheet-grounded,
   like the breaker setting-catalog override layer). Characterize before building (Chip 3).

---

## The ladder — breaker rungs mapped to relay status

The rungs it took to get `lvbreakertcc` to where it is, with the relay lane's position on each.
Counts `[VERIFIED-LIVE 2026-06-03]` via the governed `tcc.relay_*` schema (project `fxoyniqnrlkxfligbxmg`).

| # | Rung (breaker side) | Relay status |
|---|---|---|
| 1 | **Reference SSoT** (G0–G4 + index) | ✅ **Done** — `GR-RELAY-REFERENCE.md` |
| 2 | **DB: unified schema + clean load** | ✅ **Done** — 21 `tcc.relay_*` tables, live (relays **1,442** / devices **6,850** / TD-sections **6,635** / TCP points **1,570,700**) |
| 3 | **DB: the bridge** (→ ETU sensor world) | ✅ **Done** — SST-2 carried; **39** relays (`use_sst=true`) route into breaker G4 |
| 4 | **Backend: selection cascade** (no-free-text) | ✅ **Chip 2 DONE** — `/relay/manufacturers` + `/relay/facets` (cross-filtered) + `manufacturer`/`standard`-filterable `/relay/sections`; live-verified on prod |
| 5 | **Backend: NETA calc/serving** (pickup + tolerance bands + test points) | ✅ **Chip 3 DONE (tolerance serving)** — `GET /relay/tolerances/{tsid}` serves per-relay pickup/timing acceptance bands, tier-resolved + trust-tagged; live-verified. (Per-element NETA-test-point serving like breaker `/calculate` still to come.) |
| 6 | **Backend: field-trust gating wired** | ✅ **Chips 1+3 DONE** — `relay_trust.py` classifier built **and** the tolerance serving route emits `trust=validated/withheld` (never a fabricated band) |
| 7 | **UI: the field sheet** (3 screens) | ⚠️ **Partial** — `RelayResourceExplorer` = what-if *exploration* (the breaker-resource-explorer parallel), **not** the `lvbreakertcc` field sheet (= Chip 4) |
| 8 | **Fidelity: native-kernel validation** → BOUNDED→PROVEN | ❌ **Not started** — kernel unrecovered (GR §7); = punch-list **L10** |
| 9 | **Coverage: per-mfr tolerance north-star** | 🟡 **Source secured** — Enoserv [VENDOR-DOC] catalog (155 exact + ~12 canonical ≈ 167 governed relays); per-mfr coverage tracking = Chip 6 |

**Gap to parity = rungs 4–9.** Heavy lifts: 5 (NETA serving), 7 (the field-sheet UI), 8 (the close).

## The key sequencing lesson from the breakers

The breaker field sheet **shipped before** the native-kernel campaign finished — live with
pickups badged `db` and curves badged `verify`/illustration, then the B-series + I2X work
**raised the tiers underneath it**. Same move here: **ship the relay sheet at honest tiers
first (Chips 1–4), raise them via the fidelity close after (Chip 5 / L10)**. Rung 8 is a
quality ratchet that runs in parallel, **not** a blocker for a usable product.

---

## The chip sequence (smallest durable bites first)

### Chip 1 — `relay_trust.py` field-trust classifier ✅ DONE (2026-06-03)
Pure-logic encoding of the GR §6 matrix (relay parallel to `delay_trust.py`):
stored settings + raw TCP grid → `db`; analytical/TCP-interpolation families
{TCP,IEC,MEQ,BSL,SWZ,PCD} → `verify`; Bassler-0/RXD/LRM/EGC → `unsupported`; SST-2 (`use_sst`)
→ `defer_g4` (gate via the breaker matrix). `services/neta/relay_trust.py` +
`tests/test_relay_trust.py` (108 green, incl. a calc-engine drift guard). **No serving effect
yet** — it is the foundation every later chip gates against. Refines GR §6 row 4 ("withhold"
→ "verify/show-flagged", justified by the §69 parity).

### Chip 2 — selection cascade backend ✅ DONE (2026-06-03)
Guided, no-free-text dropdowns on the governed `tcc.relay_*` schema (relay parallel to the breaker
`/tmt|emt/manufacturers`): `GET /relay/manufacturers` (cascade top, 119 mfrs with curve sections) →
`GET /relay/facets` (cross-filtered `relay_types` / `device_functions` / `standards` / `families`, proper
faceted-search exclusion) → `GET /relay/sections` (now `manufacturer_source_id`- + `standard_code`-
filterable, backward-compatible). `relays.manufacturer_source_id = manufacturers.id` (100%);
`standard_code` = `0 ANSI / 1 IEC / 2 Both`. **115 relay unit tests + SQL validated live + the 3 routes
live-verified on prod** (Schweitzer → swz-dominated families, SEL-151 sections). Commit `apex 331b4e37`.
GR §1 banked the join + mapping + cardinalities. (Frontend dropdowns = Chip 4.)

### Chip 3 — relay NETA serving layer ✅ DONE (2026-06-03)
**Tolerance serving SHIPPED + live-verified.** `services/neta/relay_tolerance.py` +
`data/relay_tolerance_catalog.json` (583 cited `[VENDOR-DOC]` entries) + `GET /relay/tolerances/{tsid}`
(`apex 464fbe9a`, 11 unit tests, relay suite 156 green). Given `(manufacturer, relay_type)` it resolves a
per-relay pickup/timing acceptance band, tier-resolved **Enoserv catalog (PRIMARY) → `Relays.Note` OEM seed
→ withheld** and trust-tagged (`validated` | `withheld`, **never a fabricated band**). Matching = exact
normalized type, then a conservative *canonical* match (strips revision parentheticals / trailing year —
`CO-11(92)`→CO-11, `SEL-751 - 2017`→SEL-751; no family bridging). **Coverage: 155 exact + ~12 canonical ≈
167 governed relays**, on the workhorse families (SEL 34, Westinghouse 31, ABB 31, GE 28, Basler 13,
Beckwith 8, Multilin 4, Alstom 3, Siemens 3). Live-verified: SEL-751 (exact, ±5%/±5%), ABB CO-11(92)
(canonical, ±5%/±10%), Toshiba ICO17D (withheld). The Enoserv catalog is harvested **values only** from the
operator's licensed install (not Enoserv's library). **Remaining (later):** per-element NETA test-point
serving (the breaker `/calculate` parallel) + the NETA generic floor for the ~1,287 Enoserv doesn't cover.

<details><summary>Original Chip-3 decision gate (resolved) — tolerance source triangulation</summary>

Per protection function: pickup/tap + time-dial + **NETA tolerance bands** + test points,
each tagged with `classify_relay_trust(...)`. **⚠️ Decision gate (the real research item):
where do relay tolerances come from?** **TRIANGULATED `[VERIFIED-LIVE 2026-06-03]`:** **(a) no STRUCTURED
tolerance** anywhere (governed `tcc.relay_*` + source Access 154 DVL descriptions + DLL `CdbRELRow` shell; the
SAME Access+DLL DO carry breaker tolerance → EasyPower plots relays as nominal curves), **but (b) OEM tolerance
IS recorded as free text in `Relays.Note`** for a small legacy/GF-heavy subset (~17 explicit ±; up to ~49 with
a %/± signal — Brown Boveri, Fed Pioneer Digital 600, Siemens 7SK88, C-H/Westinghouse GFR…). Evidence:
**`GR-RELAY-FIELD-DICTIONARY.md`** + GR §7. → **three-tier source:** **(0) parse `Relays.Note`** for the
embedded per-relay OEM tolerance (a `[VENDOR-DOC]`-already-in-DB seed, ~dozens of relays); **(1) NETA generic
floor** for the rest (flagged `est`); **(2) datasheet catalog** to extend. The operator-approved two-tier
holds; the in-DB Note adds a tier-0 seed. **Remaining input (operator):** the generic NETA relay band values +
which OEMs to prioritise (e.g. SEL for Y1202C). Then build the serving layer + the Note-parser.
</details>

### Chip 4 — the `relaytcc` field-sheet UI
3-screen parallel to `lvbreakertcc` (select → settings/tolerances → curve + NETA markers),
consuming Chips 2–3, badged at the honest tiers from Chip 1. (New page; see deferred decision.)

> **Inheritable machinery (2026-06-12, STATE §215–§216):** the breaker side now ships (a) the governed
> **`tcc.field_terminology`** dictionary (migration 026 — element/dial vocabulary, MFR/VERIFY/N/A badges,
> method labels, honesty notes; relay vocabulary would be new `lineage` rows, the mechanism is built) and
> (b) the **print-ready field-sheet pattern** (`apps/operations-web/lib/field-sheet.ts` pure builder over
> the SERVED payloads + the `FieldSheetView` print overlay + letter-landscape print CSS). Chip 4 should
> reuse both rather than re-invent — the relay sheet differs in the ELEMENT MODEL (variable per
> variant, below), not in the sheet/print mechanics.

**KEY DESIGN DRIVER (operator, 2026-06-03) — variant / available-element handling.** This is where the
relay sheet *diverges* from the breaker sheet, and the crux of Chip 4. Breakers have a **fixed** element
model (LTPU/STPU/INST/GF); relays do **not** — the **available protection elements vary by relay model and
variant** (e.g. SEL-751 exposes 50/51 phase·ground·neg-seq·neutral + 27/59/81…; a CO-11 exposes one OC
element; SEL-751 vs SEL-751A vs model-style/firmware variants expose *different* element sets). So the UI
must, per selected relay/variant: (1) **enumerate the available elements** from the governed graph
(`relay_td_sections` → `relay_devices.device_function` per the selected `relays` row / variant), not a fixed
template; (2) render per-element settings + tolerance + test-points **only for elements that exist**; (3)
treat the **variant axis** as first-class (the selection cascade already reaches a TD-section, but the sheet
needs the *set* of a relay's elements, and to disambiguate variant when one `relay_type` has model-style
sub-variants). The Chip 3 tolerance serving is per-relay (uniform across elements) — fine; the *element list*
is what's variant-dependent. **Open for Chip 4 kickoff:** confirm the element-enumeration query + how variant
(model-style / `SEL-751` vs `SEL-751A` vs `SEL-751 - 2017`) maps to a distinct available-element set vs a
cosmetic label. **PAUSED here 2026-06-03** (operator pivoting to the breaker `lvbreakertcc` TCC plot screen).

### Chip 5 — fidelity close (parallel / after) = punch-list L10
Promote Models 1–6 BOUNDED→PROVEN. **Captured EasyPower relay-curve fixtures first** (export
real plotted curves, diff vs our 6 solvers — the lighter path we proved on the breaker
composite); **Ghidra-headless on `EasyPower.exe`** (`CTccRelayCurveBase` + per-family
evaluators + the non-public constant tables) only for families that fail the fixtures or need
the constants. Each promotion flips a Chip-1 tier `verify→db` and re-badges Chip-4.

### Chip 6 — relay tolerance-coverage
The durable per-manufacturer relay-accuracy north-star (the relay rows of the punch-list).

---

## Decisions deferred (surfaced now, settled at the owning rung — with leans)

- **New `relaytcc` page vs evolving `RelayResourceExplorer`** (Chip 4). **Lean: new page** —
  mirrors the breaker split (`lvbreakertcc` field sheet ≠ `breaker-resource-explorer`); the
  explorer stays the what-if surface.
- **Relay tolerance data source** (Chip 3). The genuine unknown; characterize the schema +
  decide datasheet-catalog vs NETA-table vs stored-field before building.
- **Captured-fixtures vs Ghidra-EXE** for the close (Chip 5). **Lean: captured first**, EXE
  only on failure — same call we made on the breaker composite.

---

## Status log
- **2026-06-03** — Roadmap created; **Chip 1 DONE** (`relay_trust.py` + 108 tests; GR §6 row-4
  reconciliation). Live counts re-confirmed via the governed `tcc.relay_*` schema.
- **2026-06-03** — **Chip 2 DONE** (`/relay/manufacturers` + `/relay/facets` + filterable
  `/relay/sections`; 115 unit tests; live-verified on prod; `apex 331b4e37`). GR §1 banked the cascade
  join + `standard_code` map + cardinalities.
- **2026-06-03** — **Chip 3 tolerance-source TRIANGULATED (with a correction)**: no STRUCTURED tolerance
  (governed + Access DVL descriptions + DLL), **but OEM tolerance IS in `Relays.Note`** for a legacy/GF-heavy
  subset — surfaced by the operator's challenge (a column-name probe ≠ proof of absence).
  Captured `GR-RELAY-FIELD-DICTIONARY.md` + GR §7. Source model = parse-Note seed + NETA floor + datasheet
  catalog.
- **2026-06-03** — **Chip 3 tier-0 BUILT: `Relays.Note` tolerance parser** (`services/neta/relay_note_tolerance.py`,
  19 tests, `apex 97d8adc7`). Precision-gated extraction of element/facet/low/high/unit/confidence. **Coverage
  (live): 24 of 1442 relays (~1.7%) / 12 mfrs** — a thin seed.
- **2026-06-03** — **Enoserv RTS = PRIMARY structured tolerance source (STATE §127).** `D:\Enoserv RTS`
  FasData7 SQLite (`.dbrts`, specs byte-(−10) obfuscated, read-only): **588 relays / 14 mfrs (SEL 61, GE 282,
  WH/ABB 149, Basler 44, Siemens 30…)**, per-element pickup+timing tolerances — `MIN/MAX_RANGE` (%) +
  `MIN/MAX_RANGE2` (absolute). **SEL-751 covered: pickup ±5%, timing ±5%/±0.03 s** (fills the Y1202C gap).
  **Tier order revised: Enoserv PRIMARY > Notes seed (24) > NETA floor > datasheet.** Next: the FasData7
  harvester + Enoserv↔`tcc.relays` match, on operator confirm (IP + match key). (RESA bench-day copies in the
  same folder left untouched.)
- **2026-06-03** — **Enoserv harvester + match + coverage (STATE §128).** Harvested 631 routines (88% carry
  structured tolerance); curated 463/535 clean-accuracy distinct. Server-side normalized-name + manufacturer-alias
  join → **155 of 1,442 governed relays exact-match** (high-precision floor; only 2 ambiguous outliers). Pickup
  ≈ ±5% universal; timing ±5%/±10% by family. By family w/ tol: SEL 34, Westinghouse 31, ABB 31, GE 28,
  Basler 13, Beckwith 8, Multilin 4, Alstom 3, Siemens 3.
- **2026-06-03** — **Chip 3 DONE: tolerance serving layer SHIPPED + live-verified (STATE §129).** Operator gave
  the IP go-ahead (persist Enoserv-derived **values** as a cited `[VENDOR-DOC]` catalog) + accepted leans
  (new `relaytcc` page; ship the floor). Built `relay_tolerance.py` + `data/relay_tolerance_catalog.json` (583
  entries) + `GET /relay/tolerances/{tsid}` (tier resolver, exact+canonical match, trust-tagged; `apex 464fbe9a`,
  11 tests). Canonical match lifts the floor +12 → **≈167 served**. Live-verified exact / canonical / withheld.
  GR §7 + this roadmap updated. **Next = Chip 4 (the `relaytcc` field-sheet UI).**

## Cross-references
- The relay G0–G4 (selection · schema · `Model` 0–8 dispatcher · SST-2 · field-trust) → **`GR-RELAY-REFERENCE.md`**.
- The relay fidelity close (native kernel) → **`TOLERANCE-COVERAGE-PUNCHLIST.md` L10**.
- The breaker field sheet this parallels → `project_tcc_lvbreaker_mvp_page_2026-06-01` (memory) + **G4**.
- SSoT Law, provenance tags, evidence base → **`00-MASTER-INDEX.md`**.
