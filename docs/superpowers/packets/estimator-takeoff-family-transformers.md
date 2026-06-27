# Apparatus Family Admission Process - Packet 001: Transformers

Status: SCOPING PACKET (pre-spec). Author: CC (technical authority). Date: 2026-06-26.
Lane: estimator-takeoff/family-admission (off main fa621789). Dev-only; merge operator-gated.
Feeds: docs/superpowers/specs/<date>-estimator-takeoff-transformer-family-design.md (next, after operator ratifies the Open Decisions in Part 6).

Grounding sources (read-only, this session):
- Engine: packages/estimator-takeoff/src/* (recognition, signature, voltage, quantify, catalog/breaker-map, emit, runner) @ main fa621789.
- Priced catalog (accounting SSoT): packages/estimator-core/src/catalog/equipment-models.seed.json (120 refs total; 28 transformer-family).
- NETA test-scope SSoT: infra/database/migrations/records/006_neta_reference_seed.sql (records.neta_procedures + records.neta_test_items).

---

## Part 0 - Why an admission PROCESS (the doctrine)

The takeoff engine's durable value is that it "generalizes by construction and fails closed" (the load-bearing design rationale): a per-package extraction artifact is matched against the firm's canonical estimating catalog, and anything unknown or ambiguous is surfaced, never fabricated. Admitting a NEW apparatus family must preserve that property, with the same rigor the breaker vertical was built with - not an overfit, one-off add.

The doctrine is **scoping-packet-first, accounting-before-pricing, fail-closed**, in this gate order:

1. **Characterize** the family against the canonical NETA SSoT (`records.neta_procedures`): what apparatus, what test procedures, what physical sub-types.
2. **Ratify the ACCOUNTING layer FIRST** - the firm's priced catalog refs (`estimator-core` seed) and `ref_hours` per ATS/MTS - BEFORE any engine recognition or pricing work. Where refs are missing, that is an operator/estimator/SME catalog decision (same authority that produced the breaker refs), never an engine invention.
3. **Define engine RECOGNITION, SIGNATURE, and the MATCH MODEL** (signature -> ref). Fail-closed: unknown/ambiguous -> operator question, never a priced line invented from thin evidence.
4. **Define the family's QUANTITY/ACCOUNTING semantics** (unit_of_issue each vs set; what is one priced unit; how typicals expand).
5. **Golden fixture + tests**; the two human gates (inventory verify, scope review) are unchanged.

The gate ordering is the whole point: the engine is only ever allowed to map a recognized apparatus onto a ref that has ALREADY been priced-and-blessed by the estimating authority. The engine never originates a priced thing.

**Family classification axis (the reusable output of step 3).** Each family is classified by how its priced ref is determined:
- **Signature-deterministic** (breakers): physical signature (voltage + mounting + frame + trip functions) -> exactly one ref. `matchBreaker` is total; auto-priced when evidence is complete.
- **Scope-driven** (transformers, and more so relays): the drawing yields the apparatus + physical attributes, but the priced ref depends on the SCOPE OF TESTING the client/spec requires, which the drawing does not carry. Match yields a candidate ref-GROUP + a required operator scope decision (resolved at Gate-2), with a default lean. Never auto-priced from the drawing alone.

This packet establishes the doctrine and applies it to the first new family (transformers). Relays are stubbed as a parallel research packet (Part 7).

---

## Part 1 - Transformer family characterization (grounded)

### 1a. Canonical NETA test scope (SSoT = records.neta_procedures)
Power transformers:
- `7.2.1.1` Transformers, Dry-Type, Air-Cooled, Low-Voltage, Small
- `7.2.1.2` Transformers, Dry-Type, Air-Cooled, Large
- `7.2.2`   Transformers, Liquid-Filled

Instrument transformers:
- `7.10.1` Current Transformer
- `7.10.2` Voltage (Potential) Transformer
- `7.10.3` Coupling-Capacitor Voltage Transformer (CCVT)
- `7.10.4` reserved (no procedures)

Test items that drive the priced scope tiers (from records.neta_test_items): insulation resistance (IR), turns ratio (TTR), winding resistance (WR), power factor / Doble (PF), excitation current, and - liquid-filled only - oil sampling/analysis. These are exactly the tokens the firm encodes into its priced ref names (Part 2).

### 1b. Physical sub-types that the takeoff must distinguish (to identify, not to scope)
- Coolant: **dry-type** vs **liquid/oil-filled (pad-mount)**. (Drives 7.2.1 vs 7.2.2 and which test set is even applicable; oil tests apply only to liquid.)
- Class: distribution vs power; LV / MV / HV (existing classifyVoltage routing applies unchanged).
- LTC present or not (load tap changer = separate priced ref + much larger scope).
- Instrument transformers (CT / VT / PT / CCVT) - frequently set-priced and usually bundled with their switchgear/relaying, not free-standing on a one-line.

---

## Part 2 - The accounting layer ALREADY EXISTS (key finding)

The estimator-core seed is the firm's **full estimating catalog** (120 active refs across ~25 firm sections), not a breaker-only list. It already carries **28 transformer-family refs** with `ref_hours` per ATS/MTS. The power-transformer core:

| ref | firm sec | ATS h | MTS h | uoi | note |
|---|---|---|---|---|---|
| Transformer - Dry Type (TTR/IR) | 7.2 | 1.25 | 2.0 | each | minimal scope tier |
| Transformer - Dry Type (TTR/WR/IR) | 7.2 | 3.0 | 4.0 | each | mid tier |
| Transformer - Dry Type (TTR/IR/WR/PF) | 7.2 | 8.0 | 10.0 | each | full scope (adds PF/Doble) |
| Transformer - Pad Mount Oil (TTR/WR/IR) | 7.2 | 4.0 | 5.0 | each | oil, mid tier |
| Transformer - Pad Mount Oil (TTR/IR/WR/PF/Oil) | 7.2 | 12.0 | 14.0 | each | oil, full scope + oil tests |
| Transformer - Power HV/MV w/ LTC | 7.2 | 80.0 | 80.0 | each | large power + LTC |
| Transformer - Oil Sample Draw | 7.2 | 1.0 | 2.0 | each | adder |
| Transformer Tap Changer | 7.12 | 8.0 | 10.0 | each | LTC adder |
| Infrared Scan - Transformer | IR | 0.5 | 0.5 | each | adder |

Instrument-transformer refs already present: CCVT Voltage Transformer (Individual; Set of 3), Control Power Transformer (LV Swbd; MV Swgr), Potential Transformer (set; MV; MV Set), Current Transformer (Bushing HV/MV; Bushing HV/MV Set; MV Set of 3; LV Set of 3).

**Consequence for the admission process:** for transformers, the accounting-before-pricing gate is largely **SATISFIED at the catalog level**. Step 2 reduces to a completeness AUDIT (Part 6 / D1), not authoring hours from scratch. This is the cheap-family case; a future family with no catalog presence would invert this and require an SME ref-authoring sub-step first.

**Data-hygiene flag (non-blocking).** The catalog's `neta_section` field is the firm's estimating-worksheet code, which DRIFTS from canonical NETA: power transformers sit at firm `7.2` (matches NETA), but instrument transformers sit at firm `7.1` / `7.14` / `7.15` (canonical is `7.10.x`), and one CCVT ref is mis-coded `7.6` (breakers). Matching is by **ref**, not by section, so this does not block the engine; but it must be reconciled before any NETA-section threading (Gate-2). Recorded as D4.

---

## Part 3 - The design crux: transformer ref selection is SCOPE-driven

This is the structural reason a per-family admission process is needed, made concrete:

- **Breakers (signature-deterministic):** `Circuit Breaker LV - Draw-Out (LSIG)` is fully determined by voltage + mounting + frame + functions parsed from the drawing. `matchBreaker(sig) -> ref` is total and auto-prices.
- **Transformers (scope-driven):** `Transformer - Dry Type (TTR/IR)` [1.25h], `(TTR/WR/IR)` [3h], and `(TTR/IR/WR/PF)` [8h] are the **same physical apparatus** (a dry-type transformer). They differ ONLY by which tests are performed - a SCOPE decision set by the client spec / job standard, **not present on the drawing**. The drawing tells you THAT there is a dry-type 480V transformer; it cannot tell you whether the job is TTR/IR or full TTR/IR/WR/PF.

Therefore the transformer match model is **not** signature -> one ref. It is:

> signature (coolant + class + LTC + voltage) -> a candidate **ref-GROUP** (e.g. the dry-type tier family) + a REQUIRED operator scope question, defaulted to the firm's standard ATS tier for that coolant, **resolved at Gate-2 (scope review)**.

A transformer therefore surfaces as a **scope-pending** disposition: identified, attributed, quantity-counted, but NOT auto-priced until the test tier is chosen. This is fail-closed (no fabricated hours) and routes the decision to exactly the human gate that owns test scope. It is the first concrete validation of the doctrine's family-classification axis (Part 0).

---

## Part 4 - Engine admission seams for transformers (corrected checklist)

Mirrors the breaker vertical; each item names the file and the change kind. Items marked (exists) need no new work.

1. **Recognition.** `signature/normalize.ts`: `TX|XFMR|KVA` currently sit in `NON_BREAKER` (excluded). Add a positive transformer recognition path - a `TRANSFORMER_HINT` (XFMR / transformer / kVA / dry-type / pad-mount / oil-filled) and/or a producer `candidateKind: 'transformer'` - so transformers become first-class candidates rather than silent exclusions. Keep the breaker path intact.
2. **Signature.** `signature/types.ts`: make `ApparatusSignature` a discriminated union on `kind: 'breaker' | 'transformer'`. Transformer fields: `kvaRating?`, `coolant: 'dry' | 'liquid' | 'unknown'`, `padMount?`, `ltc?`, plus existing `voltageClass`/`voltageV`/`voltageBasis`.
3. **Parsing.** `signature/normalize.ts`: text-only, fail-closed `parseKva()`, `parseCoolant()` (dry vs oil/liquid/pad-mount keywords), `parseLtc()`; new `assessTransformer()` routed by `assessCore`. No fabrication - absent evidence -> operator question.
4. **Voltage routing.** `signature/voltage.ts`: (exists) `classifyVoltage` is generic; reused unchanged.
5. **Match model.** New `catalog/transformer-map.ts` + `.data.ts`: `matchTransformer(sig) -> { group: ref[], defaultRef: ref, scopeQuestion } | null`. Returns a ref-GROUP + default tier (Part 3), NOT a single ref. Group membership keyed on coolant (dry vs pad-mount-oil) + LTC + class.
6. **Quantify.** `quantify/quantify.ts`: extend `specKey()` to include transformer fields; honor `unit_of_issue: 'set'` for instrument transformers (one priced unit = a set of 3). Generic grouping otherwise unchanged.
7. **Buckets / disposition.** `buckets/types.ts` + `emit/emit.ts`: add a `scope_pending` disposition for transformer lines awaiting a Gate-2 tier choice; carry the candidate group + default so Gate-2 can resolve. Emit still throws on zero matched/scoped.
8. **Catalog.** `estimator-core` seed: (mostly exists) NO new refs needed for the dry/oil power core; AUDIT for the one likely gap - a dry-type small-vs-large split to mirror NETA 7.2.1.1 vs 7.2.1.2, and a liquid-filled NON-pad-mount (substation) power ref. Gaps -> D1 (operator/SME).
9. **Tests + golden.** `test/normalize-transformer.test.ts`, `test/transformer-map.test.ts`, and a real transformer extraction fixture (a one-line with dry + pad-mount transformers) -> scope_pending lines -> Gate-2 resolves -> valid envelope. TDD, mirroring the breaker engine.

**Unchanged (family-agnostic):** compile, rate-card, labor allocation, extended_cents, project_intake_qty/M4, voltage assertions, reconcile/isClean. The accounting->pricing boundary is preserved: takeoff emits `ref + qty` only; estimator-core resolves hours and prices.

---

## Part 5 - Accounting-before-pricing, preserved

The takeoff continues to emit pure accounting (`ref`, `qty`, designation, provenance notes); estimator-core's `compile` resolves `ref_hours` from the catalog and applies M4/labor/rates. The transformer scope_pending model strengthens this: a transformer never carries hours until BOTH (a) its ref-group default or operator choice fixes the tier AND (b) that tier's ref already exists in the priced catalog. No path lets the engine originate a transformer price.

---

## Part 6 - OPEN DECISIONS (operator ratification before spec)

Tiered, with my lean. These gate the move from this packet to the design spec.

**D1 - Catalog completeness (accounting authority).** Confirm the existing transformer refs are the complete, correct priced set for V1, or identify gaps. *Lean:* the 3 dry tiers + 2 pad-mount-oil tiers + LTC/oil/IR adders cover the common takeoff cases; the one likely gap is a dry small-vs-large split (NETA 7.2.1.1 vs 7.2.1.2) and a liquid-filled non-pad-mount substation power ref. **Needs estimator/SME authority** (same source as the breaker refs) - I can produce the gap list; ratifying/authoring hours is yours.

**D2 - Match model (design).** Ratify that transformer ref selection is scope-driven: engine surfaces a candidate ref-group + a default tier, resolved at Gate-2, never auto-priced from the drawing. *Lean:* YES; default to the firm's standard ATS tier per coolant. This is the core of the spec.

**D3 - V1 sub-type scope.** *Lean:* power transformers only (dry-type + pad-mount oil) in V1 - highest takeoff volume; defer instrument transformers (CT/VT/CCVT/PT - set-priced, usually bundled with switchgear) and Power-HV-w/-LTC to V2.

**D4 - NETA-section reconciliation.** Build the firm-section -> canonical-NETA map now, or defer to the Gate-2 NETA-threading slice? *Lean:* defer (matching is by ref; reconciliation is a records-integration/Gate-2 concern), but the drift is RECORDED here (Part 2) so it is not lost.

---

## Part 7 - Relays (parallel research stub)

Per operator direction, relays run as a parallel research packet (`...-family-relays.md`, to follow). Early read: relays are even MORE scope/config-driven than transformers - priced by protective-element enumeration and device variant (cf. the records lane's hard AZ21 case: 18 SEL relays needing per-variant element enumeration, resolved against the live relaytcc engine). The same admission doctrine applies; the family classification will land firmly on the scope/config-driven end, and the catalog-accounting gate will likely reveal real gaps (unlike transformers). Research questions for that packet: does the firm catalog price relays by element/function or by device count; how does the takeoff identify relay model + variant from a one-line/relaying schematic; what is the unit of issue.

---

## Part 8 - Next steps

1. Operator ratifies D1-D4 (Part 6).
2. Brainstorm -> spec the transformer engine slice (design doc), folding the ratified decisions.
3. writing-plans -> SDD build, mirroring the breaker engine's contract-first / fixture-driven / fail-closed TDD rigor, with cross-engine (Codex) review per IRP.
4. Relays research packet in parallel.
