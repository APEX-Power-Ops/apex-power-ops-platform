# Apparatus Family Admission Process - Packet 003: Ground-Fault Protection Devices (LV)

Status: SCOPING PACKET (pre-spec). Author: CC (technical authority). Date: 2026-06-29.
Lane: estimator-takeoff/gfp-family-admission (off main ab43c569). Dev-only; merge operator-gated.
Feeds: docs/superpowers/specs/<date>-estimator-takeoff-gfp-family-design.md (next, after operator ratifies the Open Decisions in Part 6).

Grounding sources (read-only, this session, verified directly against the live files at main ab43c569):
- Doctrine + templates: Packet 001 (transformers) and Packet 002 (relays), both merged to main.
- Engine: packages/estimator-takeoff/src/* @ main ab43c569 (post-relay-merge: discriminated-union signature {breaker|transformer|relay}, scope_pending disposition with optional provisionalDefaultRef, candidateKind, NON_BREAKER, cross-family guards all live).
- Priced catalog (accounting SSoT): packages/estimator-core/src/catalog/equipment-models.seed.json (one GFP-family ref).
- NETA test-scope SSoT: infra/database/migrations/records/006_neta_reference_seed.sql (records.neta_procedures section 7.14 + records.neta_test_items, procedure f0a65f6c).
- Breaker ground-fault coupling: packages/estimator-takeoff/src/catalog/breaker-map.data.ts (hasG / LSIG refs).

---

## Part 0 - Doctrine (reference) + a new classification point

This packet applies the Apparatus Family Admission doctrine (Packet 001 Part 0) to the FOURTH family - ground-fault protection devices (GFP-LV) - after breakers (signature-deterministic), transformers (scope-driven), and relays (scope-driven). Doctrine unchanged: scoping-packet-first, accounting-before-pricing, fail-closed, in gate order (characterize vs the NETA SSoT -> ratify ACCOUNTING first -> define engine RECOGNITION / SIGNATURE / MATCH -> QUANTITY/ACCOUNTING semantics -> golden + tests). The engine only maps a recognized apparatus onto an already-priced ref; it never originates a price.

**A third classification point.** The two axes so far were signature-deterministic (breakers: physical signature -> exactly one ref, auto-priced) and scope-driven (transformers/relays: a candidate ref-GROUP gated by a Gate-2 scope choice). GFP-LV is NEITHER cleanly. The accounting layer has exactly ONE priced ref (Part 2), so there is NO tier ambiguity to defer - the scope-driven "which ref?" question does not exist. Yet GFP is not cleanly signature-deterministic either, because its defining signature - a STANDALONE ground-fault protection device versus a ground-fault TRIP FUNCTION embedded in a breaker/switch/ATS - is precisely the hard-to-read part. GFP is therefore a **recognition-gated, single-ref family**: the entire difficulty is the cross-family recognition boundary (Part 3), not tier selection and not accounting. It is the cleanest family on the accounting axis and the trickiest on the recognition axis.

---

## Part 1 - GFP-LV characterization (grounded)

### 1a. Canonical NETA test scope (SSoT = records.neta_procedures)
One procedure: `7.14` "Ground-Fault Protection Systems, Low-Voltage" (category ground_fault_protection; has_ats + has_mts; table 100.12). The 7.14 electrical test items (verified in records.neta_test_items, procedure f0a65f6c) describe a SYSTEM test:
- Perform ground-fault protective-device pickup tests by PRIMARY current injection.
- Pickup acceptance: greater than 90% of the device pickup setting and less than the smaller of 1200 A or 125% of pickup.
- Measure time delay at >= 150% of pickup.
- Two-CT polarity/direction test (operates with same relative polarity, does NOT operate with opposite) - i.e. zone/sensor wiring verification.

This is a test of the ground-fault SYSTEM (sensor / zero-sequence CT + sensing relay or monitor + the shunt-trip path it actuates), performed as one unit, priced "each".

### 1b. The key structural fact: ground-fault testing appears in TWO places in the SSoT
The records SSoT shows ground-fault testing at two granularities (both verified this session):
- **Standalone, as procedure 7.14** (the GFP device/system itself - procedure f0a65f6c).
- **As an embedded SUB-ITEM inside OTHER (non-7.14) apparatus procedures** - multiple non-GFP procedures carry a ground-fault sub-item, either a direct cross-reference ("Perform ground fault test in accordance with Section 7.14.") or a "Determine ground-fault pickup and delay by primary current injection." item under a different procedure id.

This is the cross-family boundary written into the SSoT itself: a ground-fault function that is part of another apparatus (the trip-unit / control test of a breaker, switch, or transfer switch - the expected parent classes, to confirm by procedure-id mapping in the spec phase) is tested UNDER that parent's procedure, and is NOT a separate GFP line. Only a STANDALONE ground-fault protective device earns the 7.14 GFP ref. (Part 3 is the engine consequence.)

### 1c. Real-world context (where GFP-LV appears)
GFP-LV is NEC-driven (NEC 230.95: GFP required on solidly-grounded wye services over 150 V to ground and at least 1000 A; also common on large LV switchboard / switchgear mains and tie breakers, and around ATS/MTS service arrangements). On the drawing it shows up as: a ground-fault relay / sensor / monitor block on a service main or switchboard one-line; a labeled "GFP" / "GFPE" / "GROUND FAULT" device; a zero-sequence CT plus ground-fault relay; or a monitor panel. These are the standalone devices the takeoff must count. (Operator intake note: service equipment, switchboards, ATS/MTS environments - exactly where missed GFP scope hurts.)

---

## Part 2 - The accounting layer EXISTS as a SINGLE priced ref (key finding; resolves the operator crux)

The operator-flagged crux ("does the catalog carry a real GFP priced ref, or is V1 recognize-and-catalog-gap-only?") is resolved: the estimator-core seed carries exactly ONE GFP-family ref, fully priced and active:

| ref | firm sec | ATS h | MTS h | uoi | status |
|---|---|---|---|---|---|
| Ground Fault Protection Device LV | 7.14 | 4.0 | 4.0 | each | active |

So V1 is NOT catalog-gap-only. It is a single priced ref, per device. Consequences:
- **No tier ambiguity.** Unlike relays (9 tiers) or transformers (dry/oil groups), a recognized standalone GFP device maps to exactly ONE ref. There is nothing to choose at Gate-2 on the ref axis.
- **The difficulty is recognition, not accounting or tier selection** (Part 0, Part 3).

**Data-hygiene trap (HARD guard).** The firm catalog's `neta_section` is OVERLOADED at "7.14": besides the GFP ref, three Current-Transformer refs (Current Transformer - Bushing HV/MV; Current Transformer - Bushing, HV/MV (Set); Current Transformer MV - Set of 3) ALSO carry firm-section "7.14". Canonical NETA puts instrument transformers at 7.10 and ground-fault at 7.14, so the firm catalog has section DRIFT on the CT side. Therefore: **the GFP ref must be matched by its exact ref/apparatus STRING ("Ground Fault Protection Device LV"), never by section number.** Keying on "7.14" would sweep in CTs. (This mirrors the Packet-001 transformer section-drift lesson; for GFP the drift sits on the neighboring CT rows, not the GFP row.)

**No other GFP refs.** There is no separate GFPE, ground-fault-relay, ground-fault-sensor, or ground-fault-monitor ref in the catalog. If the firm prices any of those differently from the single "device" ref, that is a catalog gap for the estimating authority (D1) - the engine will not invent one.

---

## Part 3 - The design crux: recognition boundary (standalone DEVICE vs embedded FUNCTION)

The entire GFP difficulty is one disambiguation, and it is fail-closed-critical because the dominant risk is a FALSE POSITIVE (counting a breaker/ATS ground-fault function as a separate GFP device, i.e. double-counting hours the parent already carries).

Three boundaries the engine must hold:
1. **Breaker trip-function ground fault is NOT a GFP device.** The breaker engine already keys on the ground-fault function: `hasG(s)` selects the LSIG refs (Circuit Breaker LV - Draw-Out / Electrically Operated / Insulated Case (LSIG)) in breaker-map.data.ts. A breaker with an LSIG/LSIGE trip unit is a BREAKER; its ground-fault element is tested in the breaker's trip-unit test. GFP recognition must explicitly YIELD to / never fire on the breaker hasG path.
2. **ANSI ground-fault function numbers are role EVIDENCE, never countable devices.** 50G/51G/50N/51N/64 on a one-line are evidence that SOME device does ground-fault sensing; they do not, alone, constitute a standalone GFP device. (Mirrors the relay device-first ruling: a bare ANSI number is never a counted apparatus.)
3. **Dedicated ground-fault relay -> GFP (7.14); multifunction relay with a ground element -> relay (7.9).** A device whose SOLE protective role is ground fault (a dedicated ground-fault relay / sensor / monitor) is a GFP device (7.14). A multifunction protective relay that merely INCLUDES a ground element is a relay (its dominant-role tier, 7.9) - already handled by the relay family. The relay packet (Packet 002 D4) explicitly carved GFP-LV OUT of the relay family and pointed it here; this packet defines the inbound boundary.

The recognition model is therefore DEVICE-FIRST with a STRONG, dedicated anchor:
> a GFP device requires a producer `candidateKind: 'gfp'` OR a dedicated GFP device token (GFP, GFPE, "GROUND FAULT PROTECTION", a dedicated "GROUND FAULT RELAY/SENSOR/MONITOR", GFR) WITH a tag - AND must NOT be a breaker/switch/ATS that merely carries a ground-fault function. Ambiguous ground-fault mentions with no standalone-device anchor are NOT counted (fail-closed: they stay with their parent or remain unrecognized).

---

## Part 4 - Engine admission seams (checklist, mirrors Packet 002 Part 4)

The breaker / transformer / relay slices already built the machinery (discriminated-union signature, scope_pending with optional provisionalDefaultRef, candidateKind, NON_BREAKER, cross-family conflict guards, ASCII guards). GFP admission REUSES it; the new work is a fourth `kind`, a GFP recognizer with a strong cross-family guard, and a one-entry match.

1. **Recognition.** signature/normalize.ts: add a positive, evidence-gated `looksLikeGfp` - a GFP_DEVICE token and/or candidateKind:'gfp'; a breaker/relay-style exclusion so a breaker with hasG/LSIG and a relay-with-ground-element are NOT stolen. Keep breaker + transformer + relay paths byte-intact. Route in assessCore BEFORE the breaker path (GFP and breaker both touch "ground fault"; GFP must claim only standalone devices, breaker keeps everything else).
2. **Signature.** signature/types.ts: extend ApparatusSignature = Breaker | Transformer | Relay | GfpSignature. `GfpSignature { kind: 'gfp'; model?: string; ansiFunctions?: string[]; ... }`. voltageClass stays OPTIONAL on the base and is NOT re-declared required on GfpSignature (relay lesson: do not blind-gate a new family on voltage). GFP never emits missing_voltage.
3. **Parsing.** signature/normalize.ts: text-only fail-closed `parseGfp*` helpers + `assessGfp()`; absent/ambiguous evidence -> fail-closed (not counted), never fabrication. A `gfp_breaker_conflict` guard mirroring relay_breaker_conflict for the case where GFP and breaker evidence collide on one tag.
4. **Voltage routing.** Reused unchanged; GFP is LV-by-definition in V1 (the ref is "... LV"); voltage does not gate.
5. **Match model.** New catalog/gfp-map.ts + .data.ts: `matchGfp(sig) -> { ref: 'Ground Fault Protection Device LV' (the single ref), disposition } | null`. Exactly one ref; no group, no tier table. Disposition per D2. Exact-ref string validated against the live seed (test).
6. **Quantify.** quantify/quantify.ts: extend specKey() with the gfp kind + model; kind-prefixed deviceId keeps GFP rows from cross-bucketing with breaker/relay/transformer. unit_of_issue: each.
7. **Buckets / disposition.** buckets/types.ts + emit/emit.ts: per D2 (scope_pending with the single ref as provisional default, in V1). Add gfp reason/question codes. Breaker + transformer + relay emit behavior byte-intact.
8. **Catalog.** estimator-core seed: the single ref exists; NO new refs. AUDIT the bounded gaps in Part 6/D1 (GFPE / dedicated GF relay / sensor pricing if the firm distinguishes them) -> estimator/SME.
9. **Tests + golden.** test/normalize-gfp.test.ts, test/gfp-map.test.ts, cross-family guard tests (a breaker with LSIG stays breaker and emits NO GFP line; a multifunction relay with a ground element stays relay; a bare 50G/51G is not counted; GFP cannot reach matchBreaker/matchRelay/matchTransformer), and a real fixture (a service-main one-line with a standalone GFP system + a breaker-with-LSIG + a feeder relay coexisting) -> GFP scope_pending line + untouched breaker/relay lines -> Gate-2 resolves -> valid envelope. TDD; breaker AND transformer AND relay goldens byte-identical throughout.

**Unchanged (family-agnostic):** compile, rate-card, labor allocation, extended_cents, project_intake_qty/M4, voltage assertions, reconcile/isClean. Accounting->pricing boundary preserved: takeoff emits ref + qty only.

---

## Part 5 - Accounting-before-pricing, preserved

The takeoff continues to emit pure accounting (ref, qty, designation, provenance); estimator-core's compile resolves ref_hours and applies M4/labor/rates. A GFP device never carries hours until (a) it is recognized as a standalone GFP device (Part 3) and (b) the single 7.14 ref - which already exists priced in the catalog - is the resolved/confirmed ref. No path lets the engine originate a GFP price, and a breaker/ATS ground-fault function never produces a GFP line (it stays inside its parent's already-priced ref).

---

## Part 6 - OPEN DECISIONS (operator ratification before spec)

Tiered, with my lean. These gate the move from this packet to the design spec.

**D1 - Accounting / catalog completeness (estimating authority).** Confirm the SINGLE ref `Ground Fault Protection Device LV` (firm 7.14, 4.0/4.0, each, active) is the complete, correct priced set for GFP-LV V1, matched by exact ref STRING (NOT by section - the firm "7.14" is overloaded with CT refs, Part 2). *Lean:* the single ref is the complete V1 set; author NO new hours. Bounded residual gap to confirm with the estimating/SME authority: does the firm price a dedicated GFPE / ground-fault relay / ground-fault sensor differently from the one "device" ref, or do they all roll into it? If differently -> those are catalog gaps (add refs later, fail-closed in the meantime); if the same -> the one ref covers them. I produce the gap question; ratifying/authoring hours is yours.

**D2 - Disposition model (single ref: price vs scope_pending).** Because there is exactly one ref, the relay-style "candidate group + Gate-2 tier choice" does not apply; the only question is whether a CONFIDENTLY-recognized standalone GFP device auto-prices (breaker-like - there is nothing to defer) or surfaces as scope_pending(single ref) for a one-click Gate-2 confirm. *Lean:* **V1 = scope_pending with the single ref as the provisional default; never auto-price in V1.** Rationale: keeps the disposition machinery uniform with transformers/relays, stays maximally fail-closed against the false-positive (cross-family) risk that is GFP's whole difficulty, and Gate-2 confirmation of the handful of GFP devices per job is cheap. Auto-price-on-confident-recognition is noted as a V2 optimization once the recognizer has field-proven precision. (This is a genuine fork - if you prefer breaker-like auto-pricing of high-confidence GFP devices in V1, say so and I will build that instead.)

**D3 - Recognition boundary (the crux) + cross-family guards.** Ratify device-first, strong-anchor recognition and the three boundaries of Part 3: (a) a breaker with a ground-fault trip function (hasG/LSIG) is a BREAKER, never a GFP device; (b) ANSI ground-fault numbers (50G/51G/50N/51N/64) are role evidence, never countable devices; (c) a dedicated ground-fault relay / sensor / monitor -> GFP (7.14), a multifunction relay with a ground element -> relay (7.9). *Lean:* recognize a GFP device only via candidateKind:'gfp' OR a dedicated GFP device token + tag, with an explicit exclusion that yields to the breaker hasG path and to the relay path; everything ambiguous is NOT counted (fail-closed). Required tests pinned in Part 7.

**D4 - V1 sub-type scope.** *Lean:* V1 = standalone LOW-VOLTAGE ground-fault protection devices/systems at the single 7.14 ref - the firm's common service-entrance / switchboard-main case. DEFER to V2: (a) any MV/HV ground-fault scheme priced differently (none in catalog today); (b) zone-interlocking / multi-zone GFP systems if the firm prices them per-zone rather than per-device; (c) GFPE-vs-GFP service distinctions if the firm separates them (D1 may surface this); (d) network-protector ground relays (already a relay-family V2 defer); (e) auto-price-on-confident-recognition (D2 V2 optimization).

(NETA-section reconciliation - the transformer D4 - is NOT a GFP decision in the canonical SSoT: records 7.14 == canonical 7.14 for ground fault. The only section issue is the firm CATALOG overloading 7.14 onto CTs, handled as the match-by-string guard in Part 2 / D1, not a separate decision.)

---

## Part 7 - Required spec tests (to pin at ratification)

Mirroring the relay packet's operator-pinned test list, pre-stated so the spec inherits them:
- **Cross-family - breaker:** a breaker with LSIG (hasG) stays breaker and emits NO GFP line (no double count). Breaker golden byte-identical.
- **Cross-family - relay:** a multifunction protective relay with a ground element stays in the relay family; a dedicated standalone ground-fault relay becomes a GFP device. Relay golden byte-identical.
- **Device-first:** a bare ANSI ground-fault number (50G/51G/50N/51N/64) with no standalone-device anchor is NOT counted as a GFP device.
- **No-voltage:** a GFP device with no busVoltage surfaces as its GFP disposition, NOT missing_voltage.
- **Exact-ref validation:** the emitted ref string equals the live seed exactly ("Ground Fault Protection Device LV"); matched by string, not section.
- **Disposition (per D2):** a recognized standalone GFP device surfaces as scope_pending(single provisional default) [V1 lean], resolvable at Gate-2 to a valid priced envelope.
- **Transformer golden byte-identical** (third prior family now regression-guards the fourth).

---

## Part 8 - Next steps

1. Operator ratifies D1-D4 (Part 6) + the Part 7 test list.
2. Brainstorm -> spec the GFP engine slice (design doc), folding ratified decisions, reusing the relay/transformer scope_pending machinery.
3. writing-plans -> SDD build, mirroring the breaker / transformer / relay contract-first / fixture-driven / fail-closed TDD rigor, with cross-engine (Codex) IRP before merge.
4. Breaker AND transformer AND relay goldens stay byte-identical throughout (three prior families now regression-guard the fourth).

---

## Part 9 - Operator ratification (2026-06-29)

The operator independently grounded the packet (confirmed: exactly one GFP-priced ref; section 7.14 overloaded by CT refs; exact-ref matching required and section-based matching forbidden) and ratified D1-D4 as written, with spec-phase tightening on recognition precedence. Recorded here so the spec is built on the ratified state.

**Ratified decisions:**
- **D1 (accounting):** the single ref `Ground Fault Protection Device LV` is the complete V1 priced set; author NO new hours. SME note left open (do NOT block V1): whether GFPE / ground-fault-sensor / dedicated ground-fault-relay variants ever price differently from the one "device" ref (catalog gap if so; fail-closed meanwhile).
- **D2 (disposition):** `scope_pending(single ref)` for V1; NEVER auto-price. Accounting is unambiguous but RECOGNITION is not - GFP's main risk is double-counting breaker LSIG/GF elements or relay ground elements, so a one-click confirm gate is the safer V1 posture. Auto-price deferred to V2 after producer evidence proves recognition quality.
- **D3 (recognition):** strong-anchor / device-first. Dedicated GFP / GFPE / GFR-style device evidence surfaces the GFP family. Bare ANSI 50G/51G/50N/51N/64 NEVER counts. Breaker hasG/LSIG stays breaker; a multifunction relay with a ground element stays relay.
- **D4 (V1 scope):** standalone LV GFP only. Defer MV/HV schemes, zone interlocking, network-protector ground relays, and auto-pricing.

**Spec-phase directives (operator):**
- **Precedence wording must be tightened.** The packet's "route GFP before breaker" is necessary but NOT sufficient: the implementation must NOT let a GFP regex steal breaker rows. The strong-anchor exclusion (GFP yields to the breaker hasG/LSIG path and to the relay path) is the load-bearing guard, not the routing order.
- **Pinned regression tests (operator-required, in addition to Part 7):**
  1. `800AF/800AT LSIG` + ground-fault text -> breaker ONLY (no GFP line).
  2. dedicated `GROUND FAULT RELAY` -> GFP.
  3. `SEL` / relay + `50G/51G` -> remains relay UNLESS dedicated GFP wording is present.
  4. bare ANSI ground functions -> NO counted device.

These are folded into the spec; the spec is built on this ratified state.

(Host worktree cleanup - the ~45 stale `apex-jobs/runs/review-*` worktrees + the orphaned `apex-family-admission` worktree - is to be done as a SEPARATE housekeeping pass, inventory-first, NOT inside this GFP lane. Recorded here only so it is not forgotten.)
