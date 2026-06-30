# Apparatus Family Admission Process - Packet 005: Switches / Disconnects (NETA 7.5)

Status: RATIFIED (D1-D4 ratified 2026-06-30 with tightenings - see Part 9). Author: CC (technical authority). Date: 2026-06-30.
Lane: estimator-takeoff/switch-family-admission (off main 89aa24a1). Dev-only; merge operator-gated.
Feeds: docs/superpowers/specs/2026-06-30-estimator-takeoff-switch-family-design.md (the ratified state in Part 9 is the spec's basis).

Grounding sources (read-only, this session, verified directly against the live files at main 89aa24a1):
- Doctrine + templates: Packet 001 (transformers), 002 (relays), 003 (GFP), 004 (instrument transformers), all merged to main.
- Engine: packages/estimator-takeoff/src/* @ main 89aa24a1 (post-ITX-merge: discriminated-union signature {breaker|transformer|relay|gfp|instrument_transformer}, scope_pending disposition with optional provisionalDefaultRef, candidateKind, NON_BREAKER, parent-shape + cross-family conflict guards all live; assessCore order = instrument -> transformer -> GFP -> relay -> NON_BREAKER -> breaker).
- Priced catalog (accounting SSoT): packages/estimator-core/src/catalog/equipment-models.seed.json (11 switch refs at firm section 7.5).
- NETA test-scope SSoT: infra/database/migrations/records/006_neta_reference_seed.sql (records.neta_procedures category switches, sections 7.5.1.1 / 7.5.1.2 / 7.5.1.3 / 7.5.2 / 7.5.3 / 7.5.4 / 7.5.5; status complete).
- Breaker recognizer (the cross-family hazard): packages/estimator-takeoff/src/signature/normalize.ts (looksLikeBreaker, FRAME_TRIP, NON_BREAKER).

---

## Part 0 - Doctrine (reference)

This packet applies the Apparatus Family Admission doctrine (Packet 001 Part 0) to the SIXTH family - switches / disconnects (NETA 7.5) - after breakers (signature-deterministic), transformers (scope-driven), relays (scope-driven), GFP (recognition-gated single-ref), and instrument transformers (scope-driven). Doctrine unchanged: scoping-packet-first, accounting-before-pricing, fail-closed, in gate order (characterize vs the NETA SSoT -> ratify ACCOUNTING first -> define engine RECOGNITION / SIGNATURE / MATCH -> QUANTITY/ACCOUNTING semantics -> golden + tests). The engine only maps a recognized apparatus onto an already-priced ref; it never originates a price.

Switches land on the **SCOPE/CONFIG-driven** end (the 4th scope-driven family). The accounting is RICH (Part 2) and the firm section is the LEAST-drifted of any family so far (genuinely at 7.5) - so the dominant difficulty is NOT accounting and NOT section drift; it is **RECOGNITION**: the token "switch" is the most overloaded device word in the whole catalog (switchBOARD, switchGEAR, transfer SWITCH, circuit SWITCHer all contain it), and a switch must be told apart from a circuit breaker (both interrupt current).

---

## Part 1 - Switch characterization (grounded)

### 1a. Canonical NETA test scope (SSoT = records.neta_procedures, category switches)
Section 7.5, by INSULATION MEDIUM x VOLTAGE (all status=complete, has_ats + has_mts):
- `7.5.1.1` Switches, Air, Low-Voltage
- `7.5.1.2` Switches, Air, Medium-Voltage, Metal-Enclosed
- `7.5.1.3` Switches, Air, Medium- and High-Voltage, Open
- `7.5.2`   Switches, Oil, Medium-Voltage
- `7.5.3`   Switches, Vacuum, Medium-Voltage
- `7.5.4`   Switches, SF6, Medium-Voltage
- `7.5.5`   Switches, Cutouts

This canonical taxonomy (air/oil/vacuum/SF6/cutout x LV/MV/HV x open-vs-enclosed) maps onto the firm catalog's construction-type x voltage refs (Part 2). NETA 7.5 covers NON-automatic switching/isolation devices (disconnects, isolators, load-interrupter switches, cutouts) - distinct from circuit breakers (7.6, automatic, with a trip unit), transfer switches (ATS/MTS, 7.18/7.22), circuit switchers (7.3), and switchgear/switchboard ASSEMBLIES (7.1).

### 1b. Physical/role sub-types the takeoff must distinguish
- **Insulation medium / construction:** air (open or metal-enclosed) vs oil vs vacuum vs SF6 vs cutout (fuse cutout). A ref discriminator.
- **Voltage class:** LV vs MV vs HV. A strong ref discriminator (Switch LV / MV / HV variants).
- **Fused vs non-fused:** a fused disconnect carries fuses (a test-scope adder - fuse continuity); the firm LV/MV refs are "Fused Disconnect".
- **Actuation:** manual vs MOTOR-OPERATED (the firm prices motor-operated MV/HV higher - 6.0h - for the operator-mechanism test).
- **Enclosure:** open (exposed) vs enclosed/metal-clad (the "(Open)" / "Open" ref variants).

### 1c. Identity on the drawing
A disconnect/safety switch shows as a break/blade symbol on a feeder or service, labeled with a switch/disconnect designation (`DS`, `DISC`, `SW`, `FU-SW`, `SAFETY SWITCH`, `DISCONNECT`, `FUSED DISCONNECT`, `LOAD BREAK SWITCH`, `LBS`) + a tag + a continuous-ampere rating (e.g. `400A`, `200AF` fusible / `NF` non-fused), sometimes a medium token (`SF6`, `OIL`, `VACUUM`) or `M.O.` (motor-operated) or `CUTOUT`. The literal words "Switch" / "Disconnect" / "Cutout" appear in schedules. Crucially the ampere rating is a CONTINUOUS rating, NOT a frame/trip `AF/AT` pair (the breaker discriminator, Part 3).

---

## Part 2 - The accounting layer EXISTS, by voltage x construction-type (key finding)

The estimator-core seed carries **11 switch refs**, all at firm `neta_section` ATS/MTS = 7.5, `unit_of_issue: each`, all active:

| ref | firm sec | ATS h | uoi | canonical NETA map |
|---|---|---|---|---|
| Switch LV - Fused Disconnect | 7.5 | 1.0 | each | 7.5.1.1 air LV (enclosed) |
| Switch LV - Fused Disconnect (Open) | 7.5 | 2.0 | each | 7.5.1.1 air LV (open) |
| Switch MV - Fused Disconnect | 7.5 | 2.5 | each | 7.5.1.2 air MV metal-enclosed |
| Switch MV - Open | 7.5 | 4.0 | each | 7.5.1.3 air MV open |
| Switch MV - Cutout | 7.5 | 2.0 | each | 7.5.5 cutouts |
| Switch MV - Oil Insulated | 7.5 | 6.0 | each | 7.5.2 oil MV |
| Switch MV - Motor Operated | 7.5 | 6.0 | each | motor-operated variant (crosses media) |
| Switch (SF6) - Medium Voltage | 7.5 | 6.0 | each | 7.5.4 SF6 MV |
| Switch (Pad Mount Vista) - Medium Voltage | 7.5 | 6.0 | each | MV pad-mount load-interrupter (SF6/vacuum) |
| Switch HV - Open | 7.5 | 4.0 | each | 7.5.1.3 air HV open |
| Switch HV - Motor Operated | 7.5 | 6.0 | each | motor-operated HV variant |

**Answer to the accounting question:** the catalog is RICH (11 refs spanning LV/MV/HV x air/oil/SF6/cutout/Vista x fused/open/motor-operated) - accounting is largely SATISFIED at the catalog level, like transformers/relays/instrument-transformers. Admission = ENGINE-side recognition + match onto existing refs + a bounded completeness audit, NOT hour authoring.

**Data-hygiene trap #1 - section is CLEAN-at-7.5 but OVERLOADED by PDU (still match by STRING).** Unlike the instrument-transformer extreme drift, all 11 switch refs genuinely carry firm section 7.5 = canonical. BUT a 12th ref also sits at firm 7.5: **`PDU (Power Distribution Unit)`** (2.0h) - a NON_BREAKER device, NOT a switch. So a section-7.5 match would sweep PDU. Therefore: **switch refs MUST be matched by their exact ref/apparatus STRING, never by section** (the recurring guard - same lesson as GFP's 7.14/CT overload and the ITX drift).

**Bounded catalog GAPS to confirm with the estimating/SME authority (D1):**
- **No LV NON-fused disconnect** (LV has only "Fused Disconnect" + its "(Open)" variant) - a plain LV safety disconnect with no fuses has no exact home.
- **No explicit VACUUM switch ref** (canonical 7.5.3 exists; the firm may fold vacuum MV into "Pad Mount Vista" or "SF6", or it is a gap).
- **No HV fused / HV cutout / HV oil / HV SF6** (HV has only Open + Motor-Operated).
- **No MV non-fused open enclosed vs open distinction beyond "Open"** and **no LV motor-operated / LV open beyond the two LV refs.**
Where a drawing shows a voltage x type with no priced home -> `catalog_gap` (surfaced, never fabricated).

**Quantity is simple here (NO set/each wrinkle):** every switch ref is `uoi=each` and a disconnect/switch is counted as an individual device (qty per tagged device). There is no 3-phase "set" pricing convention as with CT/PT banks - a 3-phase disconnect is ONE switch. So the instrument-transformer set/each crux does NOT recur.

---

## Part 3 - The design crux: the "switch" token overload + the breaker-vs-switch discriminator

Two recognition difficulties; both are RECOGNITION-side (the accounting and quantity are easy here).

### 3a. The "switch" token is the most overloaded device word in the catalog (the A-prime crux)
The bare word "switch" appears in at least FOUR non-7.5 device families that the engine already prices or must NOT claim:
- **switchBOARD** ("Switchboard - Low Voltage" / "Distribution LV") and **switchGEAR** ("Switchgear - Medium Voltage") - ASSEMBLIES, section 7.1.
- **transfer SWITCH** ("Automatic Transfer Switch", "Manual Transfer Switch") - sections 7.18 / 7.22; the ATS/MTS abbreviations are already in NON_BREAKER, but the SPELLED-OUT "transfer switch" is NOT.
- **circuit SWITCHer** ("Circuit Switcher MV/HV") - section 7.3, a distinct device.
- (and a "disconnect switch" on a switchgear lineup is still a 7.5 switch, but the lineup itself is 7.1).

So recognition CANNOT key on the bare token "switch". It must key on a **disconnect/switch-DEVICE anchor** - a dedicated noun that names a 7.5 switch: `disconnect` / `disconnect switch`, `fused`/`fusible` `switch`, `safety switch`, `load(-)break switch` / `LBS`, `isolation`/`isolating switch`, `knife switch`, `air switch`, `oil switch`, `cutout`, `SF6 switch`, `non-fused disconnect`/`NF` - OR the producer `candidateKind:'switch'`. The bare word "switch" with no disconnect-device anchor (especially in a switchboard / switchgear / transfer / circuit-switcher context) is NOT counted (device-first, A-prime style, mirroring the relay bare-ANSI and the instrument-transformer bare-CT rules).

### 3b. The breaker-vs-switch discriminator (the cross-family hazard)
A switch and a circuit breaker both interrupt current, but a 7.5 switch is NON-automatic: it has **NO trip unit** - no `AF/AT` frame/trip pair, no `LSIG` trip functions, no trip curve. It is rated in CONTINUOUS amperes (and fused vs non-fused). So:
- A row with a frame/trip signature (`FRAME_TRIP` = `###AF/###AT`) or breaker trip functions is a BREAKER, even if the word "switch" appears (e.g. a "molded-case switch" drawn with a trip rating, or a mislabeled row) - the breaker recognizer must keep it.
- The switch recognizer must therefore carry a **breaker/parent conflict guard** (mirrors the instrument-transformer parent_conflict): a switch-anchored row that ALSO carries `AF/AT` or a breaker hint -> a `switch_parent_conflict` QUESTION (null signature), never a silent switch scope_pending and never suppressing a real breaker. Likewise a NON_BREAKER token (PDU/UPS/STS/ATS/MTS/...) on the row -> not a switch.

### 3c. Scope axis + match model (consequence)
The ref is selected by **voltage class x construction-type** (air/oil/SF6/cutout/Vista) x {fused, motor-operated, open-vs-enclosed}. Some of this is legible in the drawing text (fused, SF6, oil, motor-operated/M.O., cutout, Vista, open); the enclosure tier (open vs metal-enclosed) and the precise medium are often NOT on a one-line. So:
> signature (voltage class + construction/type evidence) -> a candidate **ref-GROUP** (the voltage x plausible-type refs) + a Gate-2 scope question, with a CONSERVATIVE provisional default where voltage + a type token are legible (e.g. an MV row reading "fused disconnect" -> "Switch MV - Fused Disconnect"), and NO default where voltage or type is illegible. A recognized switch surfaces as **scope_pending** (reusing the transformer/relay/instrument-transformer machinery), never auto-priced. A recognized voltage x type with no priced home (D1 gaps - e.g. LV non-fused, vacuum, HV fused) -> `catalog_gap`.

---

## Part 4 - Engine admission seams (checklist, mirrors Packet 003/004 Part 4)

The five prior slices built the machinery (discriminated-union signature, scope_pending + optional provisionalDefaultRef, candidateKind, NON_BREAKER, cross-family conflict guards, ASCII guards). Switch admission REUSES it; the new work is a sixth `kind`, a disconnect-anchor recognizer with the breaker/parent guard, a voltage x type match table, and the catalog-gap handling.

1. **Recognition.** signature/normalize.ts: add `SWITCH_DEVICE` anchor tokens (disconnect / fused|fusible switch / safety switch / load[-]break switch|LBS / isolation|isolating switch / knife switch / air switch / oil switch / SF6 switch / cutout / non-fused|NF disconnect) and a `looksLikeSwitch` (anchor token + tag, OR `candidateKind:'switch'`). Route in assessCore AFTER the existing families (instrument/transformer/GFP/relay) - a switch never carries their tokens - and the route's FIRST action is the breaker/NON_BREAKER conflict guard so it can run before the breaker fallback without stealing breakers. Keep breaker/transformer/relay/GFP/instrument paths byte-intact.
2. **Signature.** signature/types.ts: extend `ApparatusSignature = ... | SwitchSignature`. `SwitchSignature { kind:'switch'; switchType:'fused_disconnect'|'open'|'oil'|'sf6'|'cutout'|'motor_operated'|'vista'|'unknown'; fused?: boolean; motorOperated?: boolean; ampRating?: number; voltageClass?: VoltageClass }`. voltageClass stays optional/contextual (inherited; never gates - cf relay/GFP/instrument).
3. **Parsing.** signature/normalize.ts: text-only fail-closed `parseSwitchType` (medium/construction tokens), `parseFused`, `parseMotorOperated`, `parseAmpRating` (evidence); `assessSwitch`. Absent/ambiguous type -> scope_pending candidate group / no default, never fabrication. No type token at all (a bare disconnect anchor with no medium/voltage) -> a `switch_type_unparsed`-style fail-closed question OR a wide candidate group (D-decision, mirrors the instrument-transformer type-unparsed guard).
4. **Voltage routing.** signature/voltage.ts reused; voltage CLASS strongly influences the candidate group (LV vs MV vs HV are distinct ref sets) but does NOT gate (absent -> wider group + a voltage note, not `missing_voltage`).
5. **Match model.** New catalog/switch-map.ts + .data.ts: the 11 refs VERBATIM (exact strings); a `SWITCH_GROUPS` map keyed by `voltageClass x switchType` -> candidate ref-group; `matchSwitch(sig) -> { group, defaultRef?, scopeQuestion } | null`. Legible voltage+type -> group + conservative provisional default; illegible -> no default; no priced home -> null (catalog_gap). Match by exact ref STRING (PDU overload guard). Never a single auto-priced ref.
6. **Quantify.** quantify/quantify.ts: extend `specKey` with the switch fields (switchType, voltageClass, fused, motorOperated); kind-prefixed `deviceId` keeps switch rows from cross-bucketing. Quantity = per individual device (no set/each wrinkle).
7. **Buckets / disposition.** buckets/types.ts + emit/emit.ts: reuse `scope_pending` (candidate group + optional provisional default + scopeQuestion); add switch reason/question codes (`switch_scope_pending`, `switch_catalog_gap`, `switch_parent_conflict`, and a `switch_type_unparsed` if D3 chooses the fail-closed-on-no-type path). Breaker/transformer/relay/GFP/instrument emit byte-intact. Update the compiler-checked `ASSESS_TO_REASON`.
8. **Catalog.** estimator-core seed: the 11 refs exist; NO new refs. AUDIT the bounded gaps (Part 2 / D1) + the open-vs-enclosed labor tier convention -> estimator/SME.
9. **Tests + golden.** normalize-switch, switch-map, switch-cross-family (the BREAKER guard + the switchboard/switchgear/transfer-switch/circuit-switcher exclusions are the load-bearing tests), exact-ref-vs-seed + PDU-section-overload proof, and a real golden (a service one-line with a fused disconnect + an MV switch + a REAL breaker + an assembly coexisting) -> switches scope_pend to their groups, breaker prices, assemblies excluded, partial_preview; Gate-2 stand-in prices a chosen switch ref. TDD; breaker AND transformer AND relay AND GFP AND instrument goldens BYTE-IDENTICAL throughout.

**Unchanged (family-agnostic):** compile, rate-card, labor allocation, extended_cents, project_intake_qty/M4, voltage assertions, reconcile/isClean. Accounting->pricing boundary preserved: takeoff emits ref + qty only.

---

## Part 5 - Accounting-before-pricing, preserved

The takeoff emits pure accounting (ref, qty, designation, provenance); estimator-core's compile resolves ref_hours + M4/labor/rates. A switch never carries hours until (a) its voltage x type is fixed by a legible provisional default or the operator's Gate-2 choice AND (b) that ref already exists priced in the catalog. No path lets the engine originate a switch price; an unhomed voltage x type -> catalog_gap, never a fabricated ref.

---

## Part 6 - OPEN DECISIONS (operator ratification before spec)

Tiered, with my lean. These gate the move from this packet to the design spec.

**D1 - Accounting / catalog completeness (estimating authority).** Confirm the 11 switch refs are the V1 priced set, matched by exact ref STRING (NEVER section - PDU also sits at firm 7.5). *Lean:* use the 11 refs, author NO new hours. SME items: (a) the bounded GAPS - no LV non-fused disconnect, no explicit vacuum-switch ref, no HV fused/cutout/oil/SF6 - confirm these are real gaps -> `catalog_gap` (vs an SME-blessed nearest-ref mapping); (b) the **open-vs-enclosed** convention - "Switch LV - Fused Disconnect" (1.0h) vs "...(Open)" (2.0h) and "Switch MV - Open" (4.0h): confirm "(Open)"/"Open" = open/exposed construction (a labor tier) vs enclosed, so the default is the conservative tier. I produce the gap list + the convention question; ratifying/authoring is yours.

**D2 - Match model + scope (design).** Ratify scope-driven: engine surfaces a candidate ref-GROUP (voltage x plausible type) + a Gate-2 scope question, resolved at Gate-2, NEVER auto-priced. *Lean:* scope-driven YES; provisional default ONLY where voltage + a type token are legible (e.g. MV + "fused disconnect" -> "Switch MV - Fused Disconnect"; MV + "SF6" -> "Switch (SF6) - Medium Voltage"); illegible voltage or type -> candidate group with NO default. R1 (the voltage x type -> default-ref table + the open-vs-enclosed default) PROVISIONAL until the estimator confirms.

**D3 - Recognition + the cross-family guards (THE CRUX).** Ratify device-first recognition by a disconnect/switch-DEVICE anchor (disconnect / fused|fusible switch / safety switch / load-break switch|LBS / isolation switch / cutout / oil|SF6|air switch / NF disconnect, + a tag), OR `candidateKind:'switch'` - NEVER the bare word "switch". EXCLUDE switchboard + switchgear (7.1 assemblies), transfer switch / ATS / MTS (7.18/7.22), and circuit switcher (7.3). Add a **breaker/parent conflict guard**: a switch-anchored row carrying `AF/AT` (FRAME_TRIP), a breaker hint, or a NON_BREAKER token -> a `switch_parent_conflict` question (null signature), never a silent switch line and never suppressing a real breaker. Route the switch recognizer so it cannot steal a breaker (guard-first) and cannot be stolen (it runs after the other five families, which do not key on switch tokens). *Lean:* as stated; this is the load-bearing decision - the "switch" overload is the whole difficulty of this family. Confirm all five prior goldens stay byte-identical.

**D4 - V1 sub-type scope.** *Lean:* V1 = ALL 11 refs (LV/MV/HV x fused-disconnect / open / oil / SF6 / cutout / motor-operated / Vista) - the recognition is text-driven and the refs already exist, so there is little cost to covering the full set, with `catalog_gap` for unhomed voltage x type (LV non-fused, vacuum, HV fused/cutout). Alternative (narrower): V1 = the common LV/MV fused-disconnect + open only, defer SF6 / Vista / oil / cutout / motor-operated to V2. I lean FULL set (cheap, and the gaps are the honest fail-closed). DEFER regardless: load-interrupter vs isolation-only test-scope distinctions if the firm prices them; the fuse-element test as a separate line; the Gate-2 resolution UI; the open-vs-enclosed auto-inference (operator picks at Gate-2 in V1).

(NETA-section reconciliation is INFORMATIONAL here: canonical 7.5.1.1/7.5.1.2/7.5.1.3/7.5.2/7.5.3/7.5.4/7.5.5 maps cleanly to the firm air/oil/vacuum/SF6/cutout x voltage taxonomy; the firm CATALOG sections are NOT drifted (all genuinely 7.5) - the only section hazard is the PDU overload, resolved by the match-by-string guard in Part 2/D1.)

---

## Part 7 - Required spec tests (to pin at ratification)

Pre-stated so the spec inherits them:
- **The "switch" overload (the load-bearing exclusions):** "Switchboard ..." / "Switchgear ..." -> NOT a switch (stays its assembly/unrecognized path); "Automatic Transfer Switch" / "Manual Transfer Switch" -> NOT a 7.5 switch; "Circuit Switcher ..." -> NOT a 7.5 switch; bare "switch" with no disconnect anchor -> NOT counted.
- **Cross-family - BREAKER (the discriminator):** a "fused disconnect" / "safety switch" + tag (no AF/AT) -> switch family; a real breaker (`###AF/###AT` + LSIG) -> stays BREAKER; a switch-anchored row that ALSO carries `AF/AT` -> `switch_parent_conflict` question (null signature), breaker NOT suppressed. The breaker golden stays BYTE-IDENTICAL.
- **Device-first / A-prime:** a disconnect/fused-switch/cutout anchor + tag -> recognized; `candidateKind:'switch'` -> recognized; bare "switch" alone -> not counted.
- **Type + voltage recognition:** MV + "fused disconnect" -> MV fused-disconnect group; MV + "SF6" -> SF6 group; MV + "cutout" -> cutout group; "motor operated"/"M.O." -> motor-operated group; LV fused disconnect -> LV group.
- **Voltage classification:** voltage class drives the candidate group (an MV switch -> MV switch refs); absent voltage -> wider group + note, NOT `missing_voltage`.
- **Catalog gap:** an LV non-fused disconnect / a vacuum switch / an HV fused switch (no priced home) -> `switch_catalog_gap` (surfaced, never fabricated).
- **Exact-ref validation + PDU-overload proof:** each of the 11 refs resolves verbatim in the live seed; assert PDU also sits at firm 7.5 so matching keys on the STRING, not the section.
- **Disposition:** a recognized switch -> scope_pending (group + optional provisional default), resolvable at Gate-2 to a valid priced envelope.
- **Breaker AND transformer AND relay AND GFP AND instrument goldens BYTE-IDENTICAL** (five prior families now regression-guard the sixth).

---

## Part 8 - Next steps

1. Operator ratifies D1-D4 (Part 6) + the Part 7 test list.
2. Brainstorm -> spec the switch engine slice (design doc), folding the ratified decisions, reusing the transformer/relay/GFP/instrument scope_pending machinery.
3. writing-plans -> SDD build (Workflow-orchestrated subagent TDD, ultracode), mirroring the prior families' contract-first / fixture-driven / fail-closed TDD rigor, with cross-engine (Codex) IRP before merge.
4. Breaker AND transformer AND relay AND GFP AND instrument goldens stay byte-identical throughout (five prior families now regression-guard the sixth).

---

## Part 9 - Operator ratification (2026-06-30)

Operator ratified D1-D4 on 2026-06-30 with four tightenings (D2 conservative-default; D3 NF-as-paired-attribute; D3 breaker-hint conflict guard in BOTH directions; D3 circuit-switcher exclusion ordered FIRST) and eight added must-pin tests. The spec is built on THIS ratified state.

### D1 - Accounting / catalog completeness - RATIFIED
- The 11 switch refs are the V1 priced set, matched by EXACT ref STRING only (never by section). No new hours.
- Confirmed independently by the operator: firm section 7.5 carries 12 refs because `PDU (Power Distribution Unit)` also sits at 7.5 - so the PDU-overload test is REQUIRED (match by string, never by section).
- Bounded catalog gaps (LV non-fused disconnect; explicit vacuum switch; HV fused/cutout/oil/SF6) become `switch_catalog_gap` (surfaced, never fabricated, never a nearest-ref guess).

### D2 - Match model + scope - RATIFIED with conservative-default tightening
- Scope-driven: the engine surfaces a candidate ref-GROUP (voltage class x plausible type) + a Gate-2 scope question; NEVER auto-priced.
- Provisional default ONLY when BOTH a voltage class AND a specific type/construction token are present:
  - `fused disconnect`, `cutout`, `oil`, `SF6`, `Vista`, `motor operated`/`M.O.`, and explicit `open` MAY default where the catalog has a home (with legible voltage).
  - A generic `disconnect`/`switch` anchor ALONE produces a candidate group with NO default - it does NOT default to "fused disconnect" by assumption.
- R1 (the voltage class x type -> default-ref table, and the open-vs-enclosed default tier) stays PROVISIONAL until the estimator/SME confirms.

### D3 - Recognition + cross-family guards (THE CRUX) - RATIFIED with three tightenings
Device-first recognition by a disconnect/switch-DEVICE anchor (a COMPOUND noun): `disconnect`/`disconnect switch`, `fused`/`fusible switch`, `safety switch`, `load(-)break switch`/`LBS`, `isolation`/`isolating switch`, `knife switch`, `air switch`, `oil switch`, `SF6 switch`, `cutout` + a tag, OR producer `candidateKind:'switch'`. NEVER the bare word "switch".

TIGHTENING 1 - NF is NOT a standalone anchor. `NF` (non-fused) is an ATTRIBUTE only (it sets `fused:false`), valid solely when paired with a real anchor (`disconnect`, `disc`, `safety switch`, `switch`) or `candidateKind:'switch'`. A bare tagged row (`NF-1`) or raw text merely containing `NF` does NOT mint a switch candidate.

TIGHTENING 2 - Breaker-hint conflict guard, BOTH directions (grounded mechanism). The live breaker recognizer (normalize.ts L7) is `BREAKER_HINT = /\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|vacuum|SF6|air\s*frame|GB|FB)\b/i`, and `looksLikeBreaker = BREAKER_HINT || FRAME_TRIP` (L46-47). CRITICAL: `vacuum`, `SF6`, and `air frame` are SHARED medium tokens that live inside BREAKER_HINT - so `looksLikeBreaker("SF6 switch")` is TRUE today, and such a row currently falls through to the BREAKER assessment (L362 `!looksLikeBreaker` is false). A naive ITX-style guard (`if looksLikeBreaker -> conflict`) would therefore WRONGLY block every legitimate SF6/vacuum/air switch that D4 commits to recognizing. Resolution (do NOT modify BREAKER_HINT - keep the breaker path byte-intact): the switch route uses a SWITCH-LOCAL conflict predicate keyed on the UNAMBIGUOUS breaker subset + frame/trip, NOT on the shared medium:
  - `SWITCH_BREAKER_CONFLICT = /\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|GB|FB)\b/i` (the unambiguous subset) OR `FRAME_TRIP` (`###AF/###AT`) OR trip functions (LSIG) OR a `NON_BREAKER` token.
  - The shared medium tokens (`vacuum`/`SF6`/`air frame`) are NOT conflict signals; they are switch CONSTRUCTION evidence consumed by `parseSwitchType`.
  Both directions, pinned:
  - `SF6 switch` (compound anchor present, no unambiguous breaker hint) -> SWITCH family (SF6 group).
  - `SF6 breaker` / `VCB` / `ACB` / `800AF/800AT` / LSIG (no switch anchor, or anchor + unambiguous hint) -> stays BREAKER, or `switch_parent_conflict` when a switch anchor co-occurs with an unambiguous hint/frame-trip. NEVER a silent switch line; NEVER suppress a real breaker.
  Build-time watch: introducing the switch route re-routes any row that TODAY falls through to the breaker assessment via `looksLikeBreaker=true` but actually carries a switch anchor. The five-golden byte-identical gate is the net - if an existing golden row moves, investigate before proceeding.

TIGHTENING 3 - Circuit-switcher exclusion is load-bearing and ORDERED FIRST. `Circuit Switcher MV/HV` (firm 7.3) CONTAINS the "switch" token, so the recognizer must EXCLUDE `circuit switcher` (plus `transfer switch`, `switchgear`, `switchboard`) as its FIRST action, BEFORE any anchor/SF6 matching. Note the live `NON_BREAKER` (L8) already carries the ATS/MTS abbreviations, but the SPELLED-OUT `transfer switch`/`circuit switcher`/`switchgear`/`switchboard` are NOT in any existing guard - the switch recognizer owns this exclusion list.

Route: the switch recognizer runs in `assessCore` AFTER the five prior families (insert after `looksLikeRelay`, L353; before the NON_BREAKER/breaker tail, L356-362). Its FIRST action is the TIGHTENING-3 exclusion, THEN the TIGHTENING-2 conflict guard, THEN compound-anchor detection - so it cannot steal a breaker and cannot itself be stolen. All five prior goldens (breaker/transformer/relay/GFP/instrument) stay BYTE-IDENTICAL.

### D4 - V1 sub-type scope - RATIFIED (full 11-ref set)
V1 covers ALL 11 refs (LV/MV/HV x fused-disconnect / open / oil / SF6 / cutout / motor-operated / Vista). The full set is cheap (recognition is text-driven, refs already exist) and every ambiguous/unhomed case fails closed to `switch_catalog_gap`. Narrowing to common fused/open only would discard useful coverage without reducing risk. DEFER: load-interrupter vs isolation-only test-scope split; the fuse-element test as a separate line; the Gate-2 resolution UI; open-vs-enclosed auto-inference (operator picks at Gate-2 in V1).

### Consolidated must-pin test list (Part 7 carried + eight added at ratification)
Carried from Part 7: switchboard/switchgear exclusion; ATS/MTS exclusion; bare-"switch"-not-counted; breaker discriminator + parent_conflict; device-first/A-prime; type+voltage recognition; voltage classification (no `missing_voltage`); `switch_catalog_gap`; exact-ref + PDU-overload proof; disposition -> Gate-2; five prior goldens byte-identical.

Added at ratification (the tightening tests):
1. `NF` with NO disconnect/switch anchor -> NOT counted (no switch candidate).
2. `NF disconnect` + tag -> switch candidate (then catalog_gap or no-default per voltage/type).
3. `Circuit Switcher MV/HV` -> NOT a switch (excluded FIRST, before any SF6/anchor matching).
4. `Automatic Transfer Switch` / `Manual Transfer Switch` (spelled out) -> NOT a 7.5 switch.
5. `Switchgear` / `Switchboard` -> NOT a switch.
6. `SF6 switch` -> switch (SF6 group); `SF6 breaker` / `VCB` / `800AF/800AT` LSIG -> NOT a switch (stays breaker, or `switch_parent_conflict`). BOTH directions.
7. Generic `disconnect` + voltage but NO fused/open/type token -> scope_pending with NO provisional default.
8. LV non-fused / vacuum / HV fused/cutout/oil/SF6 -> `switch_catalog_gap`.

### Engine-seam consequences of the tightenings (for the spec)
- Anchor set = COMPOUND switch-device nouns; the bare token "switch" is NOT an anchor. `NF` is an attribute lexeme, never an anchor.
- `looksLikeSwitch`: run the TIGHTENING-3 EXCLUSION pass (`circuit switcher`, `transfer switch`, `switchgear`, `switchboard`) FIRST, then the TIGHTENING-2 switch-local conflict guard (`SWITCH_BREAKER_CONFLICT` | FRAME_TRIP | LSIG | NON_BREAKER), then compound-anchor / `candidateKind:'switch'` detection. SF6/air/vacuum are switch-eligible ONLY with an anchor and absent an unambiguous breaker hint.
- `matchSwitch`: conservative-default rule - default ref only with voltage class + a specific type token; a generic anchor yields a group with no default.
- Do NOT alter BREAKER_HINT/FRAME_TRIP/NON_BREAKER or any prior family path; the switch family is purely additive.

Status: RATIFIED. Proceed to spec.
