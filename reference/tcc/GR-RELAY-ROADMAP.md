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
| 4 | **Backend: selection cascade** (no-free-text) | ⚠️ **Partial** — read-only `/relay/{sections,context,settings,plot-tcc}` exist; selection is search-style, **not** structured cascade endpoints |
| 5 | **Backend: NETA calc/serving** (pickup + tolerance bands + test points) | ⚠️ **Partial** — `/relay/settings` + `/plot-tcc` exist; **no** per-function tolerance-band + NETA-test-point serving like breaker `/calculate` |
| 6 | **Backend: field-trust gating wired** | 🟡 **Chip 1 DONE** — `relay_trust.py` classifier built (was on-paper-only in GR §6); not yet consumed by a serving route |
| 7 | **UI: the field sheet** (3 screens) | ⚠️ **Partial** — `RelayResourceExplorer` = what-if *exploration* (the breaker-resource-explorer parallel), **not** the `lvbreakertcc` field sheet |
| 8 | **Fidelity: native-kernel validation** → BOUNDED→PROVEN | ❌ **Not started** — kernel unrecovered (GR §7); = punch-list **L10** |
| 9 | **Coverage: per-mfr tolerance north-star** | ❌ **Not started** — no relay tolerance source yet (Chip 3 decision) |

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

### Chip 2 — selection cascade backend
`Mfr → Type → Device-Function → Curve` dropdown endpoints (relay parallel to
`/etu|tmt|emt/manufacturers`), no free-text. Characterize the existing `/relay/*` routes +
the `tcc.relay_*` cascade columns first.

### Chip 3 — relay NETA serving layer
Per protection function: pickup/tap + time-dial + **NETA tolerance bands** + test points,
each tagged with `classify_relay_trust(...)`. **⚠️ Decision gate (the real research item):
where do relay tolerances come from?** — per-mfr accuracy specs (datasheets) vs NETA tables
vs any stored DB field. Characterize-before-test.

### Chip 4 — the `relaytcc` field-sheet UI
3-screen parallel to `lvbreakertcc` (select → settings/tolerances → curve + NETA markers),
consuming Chips 2–3, badged at the honest tiers from Chip 1. (New page; see deferred decision.)

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

## Cross-references
- The relay G0–G4 (selection · schema · `Model` 0–8 dispatcher · SST-2 · field-trust) → **`GR-RELAY-REFERENCE.md`**.
- The relay fidelity close (native kernel) → **`TOLERANCE-COVERAGE-PUNCHLIST.md` L10**.
- The breaker field sheet this parallels → `project_tcc_lvbreaker_mvp_page_2026-06-01` (memory) + **G4**.
- SSoT Law, provenance tags, evidence base → **`00-MASTER-INDEX.md`**.
