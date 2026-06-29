# Apparatus Family Admission Process - Packet 002: Relays

Status: SCOPING PACKET (pre-spec). Author: CC (technical authority). Date: 2026-06-29.
Lane: estimator-takeoff/relay-family-admission (off main 4f05495f). Dev-only; merge operator-gated.
Feeds: docs/superpowers/specs/<date>-estimator-takeoff-relay-family-design.md (next, after operator ratifies the Open Decisions in Part 6).

Grounding sources (read-only, this session, verified directly against the live files):
- Doctrine + template: docs/superpowers/packets/estimator-takeoff-family-transformers.md (Packet 001, merged to main).
- Engine: packages/estimator-takeoff/src/* @ main 4f05495f (post-transformer-merge: discriminated-union signature, scope_pending disposition, candidateKind, NON_BREAKER all live).
- Priced catalog (accounting SSoT): packages/estimator-core/src/catalog/equipment-models.seed.json (120 refs total; 9 relay-family refs at NETA 7.9 + 1 adjacent GFP at 7.14).
- NETA test-scope SSoT: infra/database/migrations/records/006_neta_reference_seed.sql (records.neta_procedures 7.9.1 / 7.9.2 + records.neta_test_items, per-element ANSI device list).

---

## Part 0 - Doctrine (reference)

This packet applies the Apparatus Family Admission doctrine (established in Packet 001, Part 0) to the second new family, relays. The doctrine is unchanged: **scoping-packet-first, accounting-before-pricing, fail-closed**, in gate order: characterize against the NETA SSoT -> ratify the ACCOUNTING layer first (priced refs + ref_hours, an estimator/SME authority, never an engine invention) -> define engine RECOGNITION / SIGNATURE / MATCH MODEL (fail-closed) -> define QUANTITY/ACCOUNTING semantics -> golden + tests. The engine only ever maps a recognized apparatus onto a ref ALREADY priced-and-blessed by the estimating authority; it never originates a priced thing.

Family classification axis (Packet 001, Part 0): a family is either **signature-deterministic** (breakers: physical signature -> exactly one ref, auto-priced) or **scope-driven** (the drawing yields the apparatus + attributes, but the priced ref depends on the SCOPE OF TESTING, which the drawing does not carry; match yields a candidate ref-GROUP + a Gate-2 operator scope decision, never auto-priced). Packet 001 predicted relays would land "firmly on the scope/config-driven end" (Part 7). This packet confirms that and locates exactly where the relay difficulty differs from transformers.

---

## Part 1 - Relay family characterization (grounded)

### 1a. Canonical NETA test scope (SSoT = records.neta_procedures)
Two protective-relay procedures, split by technology:
- `7.9.1` Protective Relays, Electromechanical and Solid-State
- `7.9.2` Protective Relays, Microprocessor-Based

The 7.9.1 electrical test items enumerate calibration **per protective element, by ANSI device number** - confirmed in records.neta_test_items: 40 (Loss of Field), 46 (Current Balance), 46N (Neg-Seq Current), 47 (Phase Sequence/Balance Voltage), 49R (Thermal Replica), 49T (Temperature/RTD), 50 (Instantaneous OC), 51 (Time OC), 55 (Power Factor), 59 (Overvoltage), 60 (Voltage Balance), 63 (Sudden Pressure), 64 (Ground Detector), 67 (Directional OC), 79 (Reclosing), 81 (Frequency), and more - "devices listed in Section 7.9.1.B, 1 through 25," each calibrated to manufacturer tolerances at critical test points specified by the setting engineer.

### 1b. The key structural fact: two DIFFERENT granularities
- **NETA / field-execution granularity = per protective ELEMENT.** A single microprocessor relay performs many ANSI functions; NETA calibrates each. This is the per-variant element-enumeration burden seen in the records lane's hard AZ21 case (18 SEL relays). **That burden lives on the RECORDS / test-data-sheet side, not the estimating side.**
- **Firm estimating granularity = per DEVICE, by application tier** (Part 2). The firm rolls all of a device's element-calibration labor into ONE "each" hours figure chosen by the relay's protective application. The estimating takeoff therefore does NOT enumerate elements; it picks the right per-device tier.

This separation is the single most important relay finding and a refinement of Packet 001 Part 7 (which conflated the records per-element burden with estimating). The takeoff's job is per-device tier selection; element enumeration is explicitly out of scope (owned by the records/field lane).

### 1c. Physical/role sub-types the takeoff must distinguish (to identify, not to element-enumerate)
- Technology: **electromechanical/solid-state** (7.9.1) vs **microprocessor** (7.9.2). Drives the cheapest tier vs the function tiers (Part 2).
- Protective application/role: overcurrent, feeder, motor, bus-differential, differential, line, generator, multifunction-with-metering (these ARE the firm's priced tiers).
- Identity on the drawing: an ANSI device function number (or cluster), a vendor model (SEL-xxx, GE Multilin, Beckwith, Basler), or a relay box on a relaying/three-line schematic.

---

## Part 2 - The accounting layer EXISTS, priced by application tier (key finding)

The estimator-core seed carries **9 relay-family refs at NETA 7.9**, all `unit_of_issue: each`, priced by protective application and graded by scope/complexity:

| ref | firm sec | ATS h | MTS h | uoi | note |
|---|---|---|---|---|---|
| Protective Relay (Electromechanical) | 7.9 | 1.0 | 1.5 | each | legacy EM / single-function, cheapest tier |
| Protective Relay (Overcurrent Protection) | 7.9 | 4.0 | 5.0 | each | 50/51 OC |
| Protective Relay (Feeder Protection) | 7.9 | 4.0 | 5.0 | each | feeder uP relay |
| Protective Relay (Motor Control) | 7.9 | 6.0 | 8.0 | each | motor protection |
| Protective Relay - (Bus Differential) | 7.9 | 6.0 | 8.0 | each | 87B |
| Protective Relay (Differential Protection) | 7.9 | 6.0 | 8.0 | each | 87 / 87T |
| Protective Relay - (Line Protection) | 7.9 | 8.0 | 10.0 | each | line / distance (21); note the " - " in the exact ref |
| Protective Relay (Generator Protection) | 7.9 | 8.0 | 10.0 | each | gen multi-element |
| Protective Relay (Multi-function w Meter) | 7.9 | 8.0 | 10.0 | each | multifunction + metering |

Adjacent (NOT 7.9): `Ground Fault Protection Device LV` (firm 7.14, 4.0/4.0, each).

**Answers to Packet 001 Part 7 research questions:**
- *Priced by element/function or by device count?* Neither extreme: priced **per device (each), bucketed by protective APPLICATION tier**. Element complexity is captured implicitly in the tier hours, not enumerated.
- *Unit of issue?* `each` (one priced unit = one relay device).
- *Model-driven?* No. The ref is application-driven, vendor/model-agnostic. A SEL-751 and a GE 750 doing feeder protection map to the same "Feeder Protection" ref.

**Consequence for the admission process - refining Packet 001 Part 7.** Part 7 predicted "the catalog-accounting gate will likely reveal real gaps (unlike transformers)." The catalog is in fact **function-tier-RICH** (9 tiers). So the gap is NARROWER than predicted; the dominant relay difficulty is the **MATCH** (device/model/ANSI -> application tier), not missing refs. The residual catalog gaps to confirm with the estimating authority are bounded (Part 6 / D1): standalone auxiliary/lockout (86), reclosing (79), sync-check (25), and standalone voltage/frequency (27/59/81) relays have no obvious tier home; and the EM-vs-microprocessor tier convention needs confirming.

**Data-hygiene note (positive).** Unlike transformers, the relay firm-section (7.9) matches canonical NETA (7.9.1/7.9.2) with NO drift. The Packet-001-D4 NETA-section-reconciliation problem largely VANISHES for relays. (The one adjacent device, GFP LV at firm 7.14, is a different family and is deferred - D4.)

---

## Part 3 - The design crux: relay ref selection is the HARDEST scope-driven match yet

Where transformers had a clean physical discriminator (coolant: dry vs oil -> tier group), relays do not. The priced tier is the relay's protective APPLICATION, and:

- A single device carries **many ANSI functions** (a generator relay = 40+32+46+87G+24+81+...). "Which tier?" is the relay's dominant ROLE, which the drawing communicates only sometimes (e.g., an 87T circle clearly says differential; a bare "SEL-751" or "RELAY" says almost nothing about tier).
- Model alone is insufficient: the same model is configured for different applications across jobs.
- The clean default that transformers had (coolant -> standard ATS tier) is **weaker** for relays - there is no single safe modal tier for an unreadable relay.

Therefore the relay match model is, even more than transformers:

> signature (technology + recognized ANSI/role tokens + model) -> a candidate **ref-GROUP** (the application tiers) + a REQUIRED operator scope question, with at most a CONSERVATIVE provisional default where the role is legible (e.g. 87T -> Differential), and **no default at all** where it is not (a catalog-gap-shaped operator question) - **resolved at Gate-2 (scope review)**.

A relay surfaces as a **scope_pending** disposition (the same mechanism the transformer slice introduced): identified, counted, but NOT auto-priced until the application tier is chosen. This is fail-closed (no fabricated hours) and routes the decision to the human gate that owns test scope. Element enumeration is NOT part of this match (Part 1b).

---

## Part 4 - Engine admission seams for relays (checklist, mirrors Packet 001 Part 4)

The transformer slice already built the scope-driven machinery (discriminated-union signature, scope_pending, candidate-group + provisional default, candidateKind widening, ASCII guards). Relay admission REUSES that machinery; the new work is a third `kind`, a relay parser, and the application-tier match table.

1. **Recognition.** `signature/normalize.ts`: relays are currently neither recognized nor in `NON_BREAKER` (a bare "RELAY"/"87" label falls to the unrecognized-question path). Add a positive, evidence-gated relay path - a `RELAY_DEVICE` token (RELAY / vendor model families / explicit ANSI-in-protection-context) and/or producer `candidateKind: 'relay'`. Keep breaker + transformer paths byte-intact; add a relay-vs-breaker conflict guard mirroring `transformer_breaker_conflict`.
2. **Signature.** `signature/types.ts`: extend `ApparatusSignature = BreakerSignature | TransformerSignature | RelaySignature`. `RelaySignature { kind: 'relay'; technology: 'em' | 'microprocessor' | 'unknown'; ansiFunctions?: string[]; model?: string; role?: relay-role; ... }`. Breaker/transformer-only fields stay off RelaySignature (the family-leak lesson from the transformer build).
3. **Parsing.** `signature/normalize.ts`: text-only, fail-closed `parseRelayTechnology()`, `parseAnsiFunctions()`, `parseRelayModel()`; new `assessRelay()` routed by `assessCore`. Absent/ambiguous evidence -> operator question, never fabrication.
4. **Voltage routing.** `signature/voltage.ts`: (exists) reused unchanged (relays carry a bus voltage context but it does not drive the tier).
5. **Match model.** New `catalog/relay-map.ts` + `.data.ts`: `matchRelay(sig) -> { group: ref[], provisionalDefaultRef?: ref, scopeQuestion } | null`. A SMALL deterministic dominant-role -> tier table (e.g. 87T -> Differential, 87B -> Bus Differential, gen-function-cluster -> Generator, 21/distance -> Line, motor-cluster -> Motor Control, 50/51-only -> Overcurrent, EM-single-function -> Electromechanical); legible role -> conservative provisional default; illegible -> null default (catalog-gap-shaped question). Never a single auto-priced ref.
6. **Quantify.** `quantify/quantify.ts`: extend `specKey()` with relay fields (technology, role/tier, model); kind-prefixed `deviceId` (already established) keeps relay/breaker/transformer rows from cross-bucketing. `unit_of_issue: each`.
7. **Buckets / disposition.** `buckets/types.ts` + `emit/emit.ts`: reuse `scope_pending` for relay lines awaiting a Gate-2 tier choice; carry candidate group + (optional) provisional default + scopeQuestion. Add relay reason/question codes. Breaker + transformer emit behavior byte-intact.
8. **Catalog.** `estimator-core` seed: the 9 function tiers exist; NO new refs for the core. AUDIT the bounded gaps in Part 6/D1 (aux/lockout/sync/standalone-voltage/freq; EM-vs-uP convention) -> estimator/SME.
9. **Tests + golden.** `test/normalize-relay.test.ts`, `test/relay-map.test.ts`, cross-family guard tests (relay cannot reach matchBreaker/matchTransformer), and a real relaying-schematic-derived fixture (mixed: an 87T, a feeder uP relay, a bare unreadable relay) -> scope_pending lines -> Gate-2 resolves -> valid envelope. TDD, mirroring the breaker + transformer engines; breaker AND transformer goldens byte-identical throughout.

**Unchanged (family-agnostic):** compile, rate-card, labor allocation, extended_cents, project_intake_qty/M4, voltage assertions, reconcile/isClean. Accounting->pricing boundary preserved: takeoff emits `ref + qty` only.

---

## Part 5 - Accounting-before-pricing, preserved

The takeoff continues to emit pure accounting (`ref`, `qty`, designation, provenance); estimator-core's `compile` resolves `ref_hours` and applies M4/labor/rates. The relay scope_pending model preserves this: a relay never carries hours until BOTH (a) its tier is fixed by a legible-role provisional default or operator choice AND (b) that tier's ref already exists in the priced catalog. No path lets the engine originate a relay price, and element enumeration (records lane) never enters the estimate.

---

## Part 6 - OPEN DECISIONS (operator ratification before spec)

Tiered, with my lean. These gate the move from this packet to the design spec.

**D1 - Catalog completeness (accounting authority).** Confirm the 9 function-tier refs are the complete, correct priced set for V1, or identify gaps. *Lean:* the 9 tiers cover the common takeoff cases (the catalog is richer than Packet 001 predicted). Bounded residual gaps to confirm: (a) standalone auxiliary/lockout (86), reclosing (79), sync-check (25), and standalone voltage/frequency (27/59/81) relays have no clear tier home - fold into a tier, add a ref, or treat as catalog_gap; (b) the EM-vs-microprocessor convention - does a single-function microprocessor relay price at its function tier (e.g. Overcurrent 4-5h) while only legacy EM uses the 1-1.5h "Electromechanical" tier? **Needs estimator/SME authority** (same source as the breaker/transformer refs). I produce the gap list; ratifying/authoring hours is yours.

**D2 - Match model + default policy (design).** Ratify that relay ref selection is scope-driven: engine surfaces a candidate application-tier ref-group + an operator question, resolved at Gate-2, never auto-priced. The relay-specific wrinkle: the default is WEAKER than transformers (no clean physical discriminator). *Lean:* scope-driven YES; provisional default ONLY where the role is legible from the drawing (e.g. 87T -> Differential, gen-cluster -> Generator); where the role is illegible (bare "RELAY"/model-only), emit the candidate group with NO default - a catalog-gap-shaped operator question - rather than guessing a tier. This is the core of the spec and `R1` (the tier-mapping table) stays PROVISIONAL until the estimator confirms it.

**D3 - Recognition signal + element-enumeration boundary (relay-specific crux).** Ratify HOW the takeoff recognizes a relay and infers tier, and that element enumeration is OUT of estimating scope. *Lean:* recognize via candidateKind:'relay' OR a RELAY_DEVICE token OR ANSI-function-in-protection-context; infer tier from a small deterministic dominant-role table; everything ambiguous -> scope_pending question. The takeoff picks a per-device tier and NEVER enumerates protective elements (that burden is the records/field lane's, per Part 1b). Confirm this estimating/records boundary.

**D4 - V1 sub-type scope.** *Lean:* electromechanical + microprocessor protective relays at the 9 function tiers in V1 - highest takeoff volume. DEFER to V2: (a) Ground Fault Protection Device LV (firm 7.14 - adjacent family, fold into a later GFP/metering family); (b) network-protector relays; (c) any coupling to the live relaytcc catalog (tcc.relay_*, 1,442 relays) for model->variant->role auto-hinting - cross-product, availability-gated, fail-closed-by-omission in V1 (Part 7).

(NETA-section reconciliation - the transformer D4 - is NOT a relay decision: firm 7.9 == canonical NETA 7.9, no drift. Recorded as resolved in Part 2.)

---

## Part 7 - The relaytcc engine + records lane (scoped OUT of V1, noted for V2)

The firm already operates a live relay catalog/reference product: `tcc.relay_*` (1,442 relays), the model/variant SSoT behind the relaytcc engine and the relay TCC reference pages. It is the natural source for model -> variant -> protective-role identification (research Q2). V1 deliberately does NOT couple to it: cross-product coupling is availability-gated and adds failure modes, and a fail-closed operator question is safer than an auto-inferred tier. V2 may use relaytcc as a recognition HINT (model -> likely role) feeding the same scope_pending question, never an auto-price.

The records lane's per-variant element enumeration (the AZ21 case: 18 SEL relays, per-element rows against the live relaytcc engine) is the field-test-data-sheet burden and is explicitly separate from estimating (Part 1b). The two lanes share the relay identity but not the granularity.

---

## Part 8 - Next steps

1. Operator ratifies D1-D4 (Part 6).
2. Brainstorm -> spec the relay engine slice (design doc), folding the ratified decisions, reusing the transformer slice's scope_pending machinery.
3. writing-plans -> SDD build, mirroring the breaker + transformer contract-first / fixture-driven / fail-closed TDD rigor, with cross-engine (Codex) IRP review before merge.
4. Breaker AND transformer goldens stay byte-identical throughout (two prior families now regression-guard the third).

---

## Part 9 - Operator ratification (2026-06-29)

The operator independently grounded the packet and ratified D2-D4 with amendments, set a V1 policy for D1, and raised four findings (folded into the spec). Recorded here so the spec is built on the ratified state.

**Ratified decisions:**
- **D1 (catalog) - V1 POLICY, not "complete":** use the existing 9 relay refs, author NO new hours; send the orphan edge cases (86 lockout/aux, 79 reclosing, 25 sync-check, 27/59/81 standalone voltage/frequency) to `catalog_gap` or no-default `scope_pending` until estimator/SME authority decides. The catalog is NOT declared complete.
- **D2 (match model):** scope-driven YES, never auto-priced; **allow NO provisional default for illegible relays** (not just "weaker default").
- **D3 (recognition):** YES, but **device-first only** - ANSI function numbers are role EVIDENCE for an already-established relay device, never countable devices. Never count a standalone 50/51/79/81/etc. as a relay.
- **D4 (V1 scope):** YES, V1 = the 9 existing relay tiers only; defer GFP-LV, network-protector, and relaytcc model hints.

**Findings folded into the spec (with grounded engine locations):**
1. **(High) Voltage must not be blindly reused.** `BaseSignature.voltageClass` is REQUIRED (`signature/types.ts`) and `assessTransformer` hard-gates on it (`-> missing_voltage` before tier logic, `signature/normalize.ts`). Relay voltage must be optional/contextual; the relay assess path must never emit `missing_voltage`. Required test: a relay with no `busVoltageV` surfaces as `scope_pending`/`catalog_gap`, NOT `missing_voltage`.
2. **(High) Device-first recognition.** Per Part 1b the estimate is per device, not per element; D3 recognition must establish a relay DEVICE (tag/model/relay-box/`candidateKind:'relay'`) before reading ANSI as attributes. Required test: a standalone ANSI number with no device anchor is NOT counted as a relay device.
3. **(Medium) No-default contract change.** `ScopePendingLine.provisionalDefaultRef` is REQUIRED today (`buckets/types.ts`). The no-default relay case needs an explicit spec task: widen the type (+ report/runner/emit, with the cross-package operations-web typecheck gate) or a distinct no-default shape.
4. **(Low) Exact ref string fixed.** The Line-Protection ref is `Protective Relay - (Line Protection)` (with " - ", per the seed); matching is string-keyed. Corrected in the Part 2 table above.

**Required spec tests (operator-pinned):** no-voltage relay (not `missing_voltage`); standalone-ANSI non-count (device-first); exact-ref validation vs the live seed; no-default `scope_pending`; breaker AND transformer goldens byte-identical.
