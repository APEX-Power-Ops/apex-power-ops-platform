# Apparatus Family Admission Process - Packet 006: Automatic / Transfer Switches (NETA 7.22.3)

Status: SCOPING PACKET (pre-spec). Author: CC (technical authority). Date: 2026-07-05.
Lane: estimator-takeoff/transfer-switch-family-admission (off main ef83b5d7). Dev-only; merge operator-gated.
Feeds: docs/superpowers/specs/<date>-estimator-takeoff-transfer-switch-family-design.md (next, after the operator ratifies the Open Decisions in Part 6).

Grounding sources (read-only, this session, verified DIRECTLY against the live files at main `ef83b5d7`):
- Doctrine + templates: Packets 001 (transformers), 002 (relays), 003 (GFP), 004 (instrument transformers), 005 (switches), all merged to main.
- Engine: `packages/estimator-takeoff/src/*` @ main ef83b5d7 (post-switch-R1: discriminated-union signature {breaker|transformer|relay|gfp|instrument_transformer|switch}, `scope_pending` disposition + optional `provisionalDefaultRef`, `candidateKind`, `NON_BREAKER`, parent/cross-family conflict guards, `ASSESS_TO_REASON` compiler-checked map, ASCII guards all live).
- Priced catalog (accounting SSoT): `packages/estimator-core/src/catalog/equipment-models.seed.json` (120 refs; 4 at the transfer family).
- NETA test-scope SSoT: `infra/database/migrations/records/006_neta_reference_seed.sql` (records.neta_procedures section **7.22.3**; + records datasheet model `gen_transfer_switch_template.py` / migration 023).
- The current boundary this family INVERTS: `normalize.ts:8` NON_BREAKER (holds ATS/MTS/STS) + `normalize.ts:25` SWITCH_EXCLUDE (holds "transfer switch") + `normalize.ts:489-493` the NON_BREAKER tail.

---

## Part 0 - Doctrine (reference) + two firsts for this family

This packet applies the Apparatus Family Admission doctrine (Packet 001 Part 0) to the **SEVENTH** family - automatic / transfer switches (NETA **7.22.3**) - after breakers (signature-deterministic), transformers (scope-driven), relays (scope-driven), GFP (recognition-gated single-ref), instrument transformers (scope-driven), and switches (scope-driven, recognition-crux). Doctrine unchanged: scoping-packet-first, accounting-before-pricing, fail-closed, in gate order (characterize vs the NETA SSoT -> ratify ACCOUNTING first -> define engine RECOGNITION / SIGNATURE / MATCH -> QUANTITY/ACCOUNTING semantics -> golden + tests). The engine only maps a recognized apparatus onto an already-priced ref; it never originates a price.

Two things make this family structurally UNLIKE the first six - both are Part-3/Part-6 decisions, called out here so they are not missed:

1. **It is the first NON-additive family: it must CLAIM rows the engine currently DROPS.** Every prior family was purely additive - a new positive recognizer routed among devices the engine already ignored or left unrecognized, with all prior goldens BYTE-IDENTICAL. Transfer devices are different: `ATS`, `MTS`, `STS` are already tokens in `NON_BREAKER` (normalize.ts:8), so they are actively SWALLOWED (silently `ignored`, or a `non_breaker_carries_rating` question when they carry a frame/trip), and the spelled-out `transfer switch` is actively EXCLUDED by the switch family (normalize.ts:25). Admitting this family means the recognizer must run BEFORE the NON_BREAKER tail and the tokens must be REMOVED from NON_BREAKER - an inversion no prior family required.

2. **It is the first family that CANNOT keep a prior golden byte-identical.** The canonical `E01-11` golden's `STS-*` rows carry `AF/AT` and today surface as `non_breaker_carries_rating` questions; claiming the transfer family MOVES them into a transfer disposition, so `golden-e01-11` MUST be intentionally re-baselined (D4). All NON-transfer rows still stay byte-identical.

Accounting placement: transfer switches land on the **SCOPE-driven** end (like switches/transformers/relays), but with a NARROW scope axis - the catalog differentiates only automatic-vs-manual and base-vs-iso-bypass (Part 2), not amperage/voltage/pole. So the dominant difficulty is NOT tier selection and NOT accounting; it is the **routing inversion + the cross-family boundary** (Part 3), specifically the main-tie-main breaker-pair scheme.

---

## Part 1 - Transfer-switch characterization (grounded)

### 1a. Canonical NETA test scope (SSoT = records.neta_procedures) - and the section correction

**The canonical section is `7.22.3` "Emergency Systems, Automatic Transfer Switches"** (records.neta_procedures id `ac5ab82d-0932-557f-bbfb-5085ec8af62c`, category `emergency_systems`, status complete, `has_ats=true` + `has_mts=true`, ats_table_refs `[100.1, 100.12]`, mts_table_refs `[100.12]`). Scope = **11 visual-mechanical + 8 electrical = 19 items** (006_neta_reference_seed.sql:3656-3684). The VM set includes the two transfer-specific items that define the device: **"Perform manual transfer operation"** (VM.9) and **"Verify positive mechanical interlocking between normal and alternate sources"** (VM.10); the electrical set includes **"Calibrate and set all relays and timers"** (E.6) and **"Verify correct operation and timing of transfer functions"** (E.8). MTS is seeded as a distinct `standard` under the SAME 7.22.3 procedure (006:3685-3713).

**Section correction (load-bearing - do NOT inherit the wrong number):**
- The operator's label **"7.16" is WRONG** - `7.16.x` is **Motor Control** (Motor Starters LV/MV `7.16.1.1`/`7.16.1.2`; Motor Control Centers `7.16.2.x`), 006:53-56. If the family were keyed to "7.16" it would collide head-on with the 4 motor-control refs.
- The merged switches packet's **"7.18/7.22" is half-wrong**: `7.18.x` is **Direct-Current Systems** (batteries/chargers/rectifiers), 006:58-62 - NOT transfer. `7.22` is the correct CHAPTER (Emergency Systems), and `7.22.3` is the correct LEAF.
- **STS (static/solid-state transfer) has NO standalone NETA section.** The only "static transfer" test items live under `7.22.2` UPS (006:3600/3606/3613), whose ATS portion cross-refs 7.22.3. `7.22.2` UPS and `7.22.1` Engine Generator are DISTINCT sibling devices, not this family.

The two engine comments carrying the loose "transfer switch (7.18/22)" label (normalize.ts:24) should be corrected to 7.22.3 when the family lands.

### 1b. Physical/role sub-types the takeoff must distinguish (grounded in the 023 records model)
The records lane already ratified the enumerated ATS field/sub-type model (`ats_transfer_switch_v1`, migration 023): the takeoff should recognize/populate the same axes.
- **Automation class:** ATS (automatic) vs MTS (manual/non-automatic) - distinct `standard`s under 7.22.3, and distinct priced refs (Part 2). STS (static/solid-state) - no section, no ref (Part 2/D5).
- **Transition type** (023 `transition_type` selection): open / closed / delayed / soft_load - the real open-vs-closed-transition discriminator. NOT a priced axis (Part 2).
- **Bypass-isolation:** a bypass/isolation feature (the "Iso Bypass" catalog variant) - priced as ONE transfer device at a higher hour tier, NOT a second device (Part 2/H5).
- **Ratings:** voltage_rating, current_rating (continuous A), withstand_rating (kA close-on/withstand), poles (3P vs 4P/switched-neutral), phases. NONE of these are priced discriminators today (all refs are `each`, LV service-shaped).
- **Construction:** contactor-based vs breaker-based - not a records field, not a priced axis.

### 1c. Identity on the drawing
A transfer device shows as: the abbreviations **`ATS` / `MTS` / `STS`** (currently NON_BREAKER tokens, normalize.ts:8) on a tag, OR the spelled-out **"AUTOMATIC TRANSFER SWITCH" / "MANUAL TRANSFER SWITCH" / "TRANSFER SWITCH"** (currently SWITCH_EXCLUDE, normalize.ts:25), with a tag + a continuous-ampere rating (e.g. `400A`, `800A`), sometimes a `BYPASS`/`ISO` token, a pole count (`3P`/`4P`/`SWN`), or a transition token. Critically, a genuine transfer device is rated in CONTINUOUS amperes; a `###AF/###AT` frame/trip pair on a "transfer"-labeled row is the breaker-pair-scheme hazard (Part 3/H3), not a transfer-device rating.

---

## Part 2 - The accounting layer EXISTS, moderate/rich-by-TYPE (key finding)

The estimator-core seed carries **4 transfer-switch refs** (all `unit_of_issue: each`, all `lifecycle_status: active`, `merged_into_ref: null`; `ref == apparatus`). Hours are `{ATS = acceptance-testing-spec, MTS = maintenance-testing-spec}` - the SAME two testing dimensions every catalog ref carries, NOT device types:

| ref (exact string) | firm sec (ATS/MTS) | ATS h | MTS h | uoi | note |
|---|---|---|---|---|---|
| `Automatic Transfer Switch - (IR/DLRO)` | 7.22 / 7.22 | 3.0 | 4.0 | each | plain automatic |
| `Automatic Transfer Switch - Iso Bypass (IR/DLRO)` | 7.22 / 7.22 | 4.0 | 6.0 | each | +bypass-isolation tier |
| `Automatic Transfer Switch (Functional Testing)` | 7.18 / 7.18 | null | 4.0 | each | mis-sectioned 7.18; ATS hrs null |
| `Manual Transfer Switch - (IR/DLRO)` | 7.22 / 7.22 | 2.0 | 3.0 | each | manual (MTS) |

Adjacent surrogate (NOT a device ref): `Infrared Scan - ATS` (section `IR`, 0.5/0.5, each) - a generic IR-scan add-on line keyed to the pseudo-section "IR", not a transfer-device model. Treat as an IR add-on, not the primary transfer classifier (D1).

**Answer to the accounting question:** the catalog is MODERATE/RICH-BY-TYPE - differentiated by automatic-vs-manual x base-vs-iso-bypass x (IR/DLRO)-vs-(Functional-Testing), NOT by amperage/voltage/pole. Admission = ENGINE-side recognition + match onto these 4 refs + a bounded gap audit, NOT hour authoring (like switches/transformers, unlike a from-scratch family).

**Data-hygiene trap #1 - the "ATS/MTS" KEY collision.** In this catalog, `ATS`/`MTS` are the two testing-spec column keys on EVERY ref (`neta_section: {ATS, MTS}`, `ref_hours: {ATS, MTS}`). So a naive grep for `ATS`/`MTS` matches all 120 refs. Transfer-DEVICE refs must be found by the ref STRING containing "transfer", never by the ATS/MTS keys.

**Data-hygiene trap #2 - DOUBLE section overload (match by exact STRING, never section).** Two independent traps force exact-ref-string matching:
- Firm `7.22` is shared by 3 transfer refs, and in the SSoT `7.22` also covers Engine Generator (7.22.1) and UPS (7.22.2) - so a bare-`7.22` match is ambiguous at the family level.
- Firm `7.18` is a HARD overload: the `Automatic Transfer Switch (Functional Testing)` ref sits at `7.18`, and so do two NON-transfer priced refs - `Direct-Current Systems - Batteries` and `Direct-Current Systems - Chargers`. A section-`7.18` match would conflate a transfer switch with DC-battery testing.
This is the recurring guard (GFP's 7.14/CT overload, switches' 7.5/PDU overload): **match by exact ref STRING.**

**Quantity is simple (NO set/each wrinkle):** all 4 refs are `each`; one priced unit per tagged transfer device. There is no 3-pole/4-pole/switched-neutral "set" convention and no pole-based ref - pole count is invisible to pricing (contrast the arrester `set` refs). A 4-pole ATS is ONE `each`.

**Bounded catalog GAPS to confirm with the estimating/SME authority (D1):**
- **No STS / static / solid-state transfer ref** - and no NETA section either (Part 1a). A standalone STS on a one-line has no priced home.
- **No UPS device ref** (UPS is 7.22.2, a distinct class - out-of-family per D5).
- **No MV transfer ref** (all 4 refs are LV/service-entrance-shaped). An MV transfer device has no priced home.
- **The `(Functional Testing)` ref anomaly:** it is mis-sectioned at `7.18` (DC systems) and its acceptance (`ATS`) hours are `null` (priced only under maintenance). Is this a catalog data bug (should be 7.22.3) or an intentional "functional test billed under maintenance only" convention? (D1 - SME call.)
Where a drawing shows a transfer type with no priced home -> `transfer_catalog_gap` (surfaced, never fabricated).

---

## Part 3 - The design crux: the routing INVERSION + the cross-family hazards

Two difficulties, both RECOGNITION-side (accounting and quantity are easy here).

### 3a. The routing inversion (the A-prime crux for THIS family)
Every prior family routed ADDITIVELY among rows the engine ignored. Transfer devices are the opposite: they are ALREADY captured to be dropped.
- `NON_BREAKER = /\b(PDU|UPS|STS|ATS|MTS|SPD|PQM|METER|BUS\s*DUCT)\b/i` (normalize.ts:8) - so `ATS`/`MTS`/`STS` rows, in `assessCore`, hit the NON_BREAKER tail (normalize.ts:489-493): with a frame/trip -> `non_breaker_carries_rating` QUESTION; bare -> `non_breaker_excluded` -> stamped `ignored` FINAL (emit.ts:98-99), i.e. SILENTLY DROPPED (not even a question).
- `SWITCH_EXCLUDE = /\b(circuit[\s-]+switcher|transfer[\s-]+switch|switchgear|switchboard)\b/i` (normalize.ts:25) - so the spelled-out `transfer switch` is actively rejected by the switch family (its D3 tightening-3).

So this family must (i) run its recognizer BEFORE the NON_BREAKER tail (insert BETWEEN `looksLikeSwitch` at normalize.ts:485 and the NON_BREAKER catch at normalize.ts:489); (ii) REMOVE `ATS`/`MTS`/`STS` from NON_BREAKER (normalize.ts:8) so they route to the new family instead of being swallowed; (iii) CLAIM the spelled-out `transfer switch` anchor that switches reject. This is the single hardest engine-seam decision (D3) and it is why the E01-11 golden must move (D4).

### 3b. The five cross-family hazards (both directions)
- **H1 - ATS vs a 7.5 disconnect SWITCH.** Both carry "switch". A fused/safety disconnect is 7.5 (the switch family); an automatic/manual TRANSFER switch is 7.22.3 (this family). Anchor on `transfer`/`ATS`/`MTS`, NEVER the bare word "switch".
- **H2 - ATS vs a 7.1 switchgear/switchboard ASSEMBLY.** Switches already exclude switchgear/switchboard; this recognizer must KEEP that exclusion (a transfer scheme drawn inside a switchboard lineup stays the lineup's 7.1 assembly unless a discrete transfer device is tagged).
- **H3 - ATS vs a BREAKER-PAIR transfer SCHEME (main-tie-main / two interlocked breakers). THE LOAD-BEARING HAZARD.** A main-tie-main is a TOPOLOGY whose breakers must each be counted as BREAKERS (each `###AF/###AT` prices as a breaker), NOT collapsed into one ATS device. The false-positive is minting one ATS line from an interlock note while DOUBLE-dropping the two real breakers. Guard: an ATS DEVICE requires a discrete transfer-device anchor + tag; mere `transfer`/`interlock`/`MTM` text on a bus with two frame/trip breakers is NOT an ATS device (mirrors GFP's "ANSI number is evidence, not a device" and switches' parent-conflict). A transfer-labeled row that ALSO carries `FRAME_TRIP` -> a `transfer_parent_conflict` QUESTION (null signature), never a silent ATS line and never suppressing the breakers.
- **H4 - ATS vs STS vs UPS.** The catalog has NEITHER an STS nor a UPS ref, and STS has no NETA section (UPS = 7.22.2). So STS/UPS are NOT the ATS/MTS refs. STS -> recognized as transfer-family evidence but fail-closed to `transfer_catalog_gap` (never mapped onto the contactor/breaker ATS refs - different device physics). UPS -> OUT-of-family (leave in NON_BREAKER; its own future 7.22.2 family). Note: on the E01-11 golden the `UPS-*-MIB/MOB/LBB` tokens are UPS BREAKER mains (main-input/output/bypass breakers), NOT the ATS - the recognizer must not over-claim them.
- **H5 - bypass-isolation.** The catalog prices bypass-isolation as an ATS sub-variant (`...- Iso Bypass`, one device at +1-2h), NOT a standalone 7.5 switch. So a bypass/isolation feature is a MATCH AXIS (pick the Iso-Bypass ref), never a second counted device (mirrors switches' NF-as-attribute).

### 3c. Scope axis + match model (consequence)
The ref is selected by **automation class (automatic vs manual) x bypass-isolation-present**. Both are often legible on a one-line (ATS vs MTS token; a `BYPASS`/`ISO` token). So:
> signature (automation class + bypass evidence) -> the transfer ref-GROUP + a Gate-2 scope question, with a CONSERVATIVE provisional default where the automation class is legible (an "ATS"/"automatic transfer switch" -> `Automatic Transfer Switch - (IR/DLRO)`; +`bypass`/`iso` -> `...- Iso Bypass`; "MTS"/"manual transfer switch" -> `Manual Transfer Switch - (IR/DLRO)`), and NO default where the automation class is illegible (bare "transfer switch"). A recognized transfer device surfaces as **`scope_pending`** (reusing the switch/transformer/relay machinery), never auto-priced. The `(IR/DLRO)` vs `(Functional Testing)` split is a TEST-SCOPE axis on the SAME device - default to `(IR/DLRO)`, never mint two device lines (D1). STS/MV/no-home -> `transfer_catalog_gap`.

---

## Part 4 - Engine admission seams (checklist, mirrors Packet 005 Part 4; exact line refs)

The six prior slices built the machinery (discriminated-union signature, `scope_pending` + optional `provisionalDefaultRef`, `candidateKind`, `NON_BREAKER`, cross-family conflict guards, ASCII guards). Transfer admission REUSES it; the NEW work is a seventh `kind`, a transfer anchor recognizer with the H3 guard, the routing INVERSION (the net-new part), a narrow automation-class match table, and the golden re-baseline.

1. **Recognition (INVERSION - the net-new seam).** signature/normalize.ts: add `TRANSFER_DEVICE` anchor tokens (`automatic|manual transfer switch`, `transfer switch`, `ATS`, `MTS`; STS pending D5) and a `looksLikeTransferSwitch` (anchor + tag, OR `candidateKind:'transfer_switch'`). REMOVE `ATS`/`MTS`/`STS` from `NON_BREAKER` (L8) - KEEP `UPS`/`PDU`/`SPD`/`PQM`/`METER`/`BUS DUCT` (D5). Route in `assessCore` BETWEEN `looksLikeSwitch` (L485) and the NON_BREAKER catch (L489). The route's FIRST action is the H3 breaker/parent conflict guard (frame/trip or unambiguous breaker hint -> `transfer_parent_conflict`), so it runs before the breaker fallback WITHOUT stealing breakers. Keep breaker/transformer/relay/GFP/instrument/switch paths byte-intact.
2. **Signature.** signature/types.ts: extend `ApparatusSignature = ... | TransferSwitchSignature` (types.ts:91). `TransferSwitchSignature { kind:'transfer_switch'; automationClass:'automatic'|'manual'|'static'|'unknown'; bypassIsolation?: boolean; ampRating?: number; voltageClass?: VoltageClass }`. voltageClass optional/contextual (never gates - cf switch/relay).
3. **Parsing.** signature/normalize.ts: text-only fail-closed `parseAutomationClass` (ATS/MTS/STS + spelled forms), `parseBypassIsolation`, `parseAmpRating` (evidence); `assessTransferSwitch`. Bare "transfer switch" with no automation class -> candidate group / no default (never fabrication).
4. **Voltage routing.** signature/voltage.ts reused; voltage does NOT gate (all refs LV; absent voltage -> the transfer disposition, never `missing_voltage`).
5. **Match model.** New `catalog/transfer-switch-map.ts` + `.data.ts`: the 4 refs VERBATIM (exact strings); a group keyed by `automationClass x bypassIsolation` -> candidate ref-group; `matchTransferSwitch(sig) -> { group, defaultRef?, scopeQuestion } | null`. Legible automation class -> group + conservative default (IR/DLRO scope); illegible -> no default; STS/MV/no-home -> null (`transfer_catalog_gap`). Match by exact ref STRING (dual-section-overload guard). Never auto-priced.
6. **Quantify.** quantify/quantify.ts: extend `specKey` with the transfer fields (automationClass, bypassIsolation); kind-prefixed `deviceId` keeps transfer rows from cross-bucketing. Quantity = per individual device (`each`).
7. **Buckets / disposition.** buckets/types.ts + emit/emit.ts: reuse `scope_pending` (group + optional provisional default + scopeQuestion); add transfer reason/question codes (`transfer_scope_pending`, `transfer_catalog_gap`, `transfer_parent_conflict`) to the three code unions (buckets/types.ts OperatorQuestionCode + DispositionReasonCode; normalize.ts:388-394 AssessmentCode) and the `ASSESS_TO_REASON` map. Emit branch modeled on the switch branch (emit.ts:238-256). Breaker/transformer/relay/GFP/instrument/switch emit byte-intact.
8. **Catalog.** estimator-core seed: the 4 refs exist; NO new refs. AUDIT the bounded gaps (Part 2 / D1): STS, UPS-out-of-family, MV transfer, the `(Functional Testing)` 7.18/null-ATS anomaly -> estimator/SME.
9. **Tests + golden (RE-BASELINE - the net-new part).** normalize-transfer, transfer-map, transfer-cross-family (the H3 main-tie-main guard + the H1/H2 switch/switchgear exclusions + the H4 STS/UPS handling are the load-bearing tests), exact-ref-vs-seed + the dual 7.22/7.18 section-overload proof, and a real golden. **The `E01-11` golden MUST be re-baselined** (its `STS-*` rows move out of `non_breaker_carries_rating` into the transfer disposition) - intentional, reviewed, with a documented before/after. All SIX prior families' goldens stay BYTE-IDENTICAL EXCEPT the specific `ATS`/`MTS`/`STS` disposition assertions in the shared normalize/dispositions/runner-reconciliation tests, which must be intentionally updated (D4).

**Unchanged (family-agnostic):** compile, rate-card, labor allocation, extended_cents, project_intake_qty/M4, voltage assertions, reconcile/isClean. Accounting->pricing boundary preserved: takeoff emits ref + qty only.

---

## Part 5 - Accounting-before-pricing, preserved

The takeoff emits pure accounting (ref, qty, designation, provenance); estimator-core's compile resolves ref_hours + M4/labor/rates. A transfer switch never carries hours until (a) its automation class is fixed by a legible provisional default or the operator's Gate-2 choice AND (b) that ref already exists priced in the catalog. No path lets the engine originate a transfer price; an STS / MV / unhomed transfer -> `transfer_catalog_gap`, never a fabricated ref; a main-tie-main's breakers stay priced as breakers.

---

## Part 6 - OPEN DECISIONS (operator ratification before spec)

Tiered, with my lean. These gate the move from this packet to the design spec. (More decisions than prior families, because the routing inversion + golden re-baseline are net-new.)

**D1 - Accounting / catalog completeness (estimating authority).** Confirm the 4 transfer refs are the V1 priced set, matched by EXACT ref STRING (never section - firm 7.22 AND 7.18 are both overloaded). *Lean:* use the 4 refs, author NO new hours; default to the `(IR/DLRO)` scope (the `(Functional Testing)` variant is the same device under a different test scope - a Gate-2 choice, never a second line). SME items: (a) the `(Functional Testing)` ref is mis-sectioned at `7.18` with `null` acceptance hours - is that a data bug (should be 7.22.3) or a deliberate "functional test = maintenance-only" convention? (b) confirm STS / UPS / MV / 4-pole are genuine gaps -> `transfer_catalog_gap` / out-of-family (vs an SME-blessed nearest-ref). I produce the gap list + the anomaly flag; ratifying/authoring is yours.

**D2 - Match model + scope (design).** Ratify scope-driven: engine surfaces a candidate transfer ref-GROUP + a Gate-2 scope question, NEVER auto-priced. *Lean:* scope-driven YES; provisional default ONLY where the automation class is legible (`ATS`/`automatic` -> Automatic ref; `+bypass`/`iso` -> Iso-Bypass ref; `MTS`/`manual` -> Manual ref); bare "transfer switch" -> candidate group with NO default. R1 (the automation-class x bypass -> default-ref table) PROVISIONAL until the estimator confirms.

**D3 - Recognition + THE ROUTING INVERSION + cross-family guards (THE CRUX).** Ratify device-first recognition by a transfer-device anchor (`automatic|manual transfer switch`, `transfer switch`, `ATS`, `MTS` + tag, OR `candidateKind:'transfer_switch'`) - NEVER a bare "switch". Ratify the INVERSION: REMOVE `ATS`/`MTS`/`STS` from `NON_BREAKER` (normalize.ts:8), route the recognizer BEFORE the NON_BREAKER tail (between L485 and L489), and CLAIM the spelled-out `transfer switch` that SWITCH_EXCLUDE rejects. Ratify the H3 guard: a transfer-labeled row carrying `AF/AT` (FRAME_TRIP) or an unambiguous breaker hint -> `transfer_parent_conflict` question (null signature), never a silent ATS line and never suppressing a real breaker (the main-tie-main protection). EXCLUDE switchgear/switchboard (7.1) and circuit switcher (7.3). *Lean:* as stated; this is the load-bearing decision - the inversion is the whole difficulty of this family. Confirm all six prior goldens stay byte-identical except the ATS/MTS/STS disposition assertions (D4).

**D4 - E01-11 golden RE-BASELINE (unavoidable).** Because ATS/MTS/STS move out of `non_breaker_carries_rating`/`ignored` into the transfer disposition, the `E01-11` golden and the specific `ATS`/`MTS`/`STS` disposition assertions in the shared normalize/dispositions/runner-reconciliation tests CANNOT stay byte-identical. *Lean:* re-baseline them INTENTIONALLY, with a documented before/after (the STS-* rows become transfer scope_pending / catalog_gap), keeping every NON-transfer row byte-identical. This is the first family to require it; call it out so the review does not read it as a regression.

**D5 - STS + UPS scope (H4).** *Lean:* STS (static/solid-state transfer) - recognize as transfer-family evidence but fail-closed to `transfer_catalog_gap` (no priced ref, no NETA section; NEVER map onto the contactor/breaker ATS refs). UPS - OUT-of-family: leave `UPS` in `NON_BREAKER`; it is 7.22.2, its own future family, and the E01-11 `UPS-*-MIB/MOB/LBB` are UPS breaker mains that must stay breakers. (If you prefer STS folded onto the ATS ref instead of a gap, say so; I lean gap - honest fail-closed.)

**D6 - V1 sub-type scope.** *Lean:* V1 = the 4 refs (automatic + manual, base + iso-bypass), defaulting to the `(IR/DLRO)` scope. Poles / switched-neutral (3P/4P/SWN), transition type (open/closed/delayed/soft), contactor-vs-breaker construction, MV transfer, and the `(Functional Testing)`-only scope are NOT V1 ref axes (no priced discriminator) - they surface as notes/`transfer_catalog_gap`, never a fabricated line. DEFER: MV transfer; 4-pole-as-a-price-axis; functional-testing as a separate line; the Gate-2 resolution UI; STS-if-the-firm-later-prices-it.

(NETA-section reconciliation is CORRECTIVE here, not informational: the family's canonical anchor is `7.22.3`; the operator's "7.16" (motor control) and the switch packet's loose "7.18/7.22" are recorded as mislabels so the spec + any records linkage key on 7.22.3.)

---

## Part 7 - Required spec tests (to pin at ratification)

Pre-stated so the spec inherits them:
- **The routing inversion (the load-bearing claims):** a bare `ATS-1` (tag, no rating) -> a transfer `scope_pending` line, NOT `non_breaker_excluded`/ignored (proves the NON_BREAKER removal + the before-tail route). `Automatic Transfer Switch` (spelled out) -> transfer family, NOT the switch-exclusion path. `MTS-2` -> manual transfer ref group.
- **H3 - main-tie-main (the discriminator):** a bus with two `###AF/###AT` breakers + a "transfer"/"interlock"/"MTM" note -> the two breakers stay BREAKERS (priced), NO ATS line minted. A single transfer-anchored row that ALSO carries `AF/AT` -> `transfer_parent_conflict` question (null signature), breaker NOT suppressed. The breaker golden stays BYTE-IDENTICAL.
- **H1/H2 - cross-family exclusions:** a 7.5 `fused disconnect`/`safety switch` -> stays switch family; `Switchgear`/`Switchboard` -> NOT transfer; `Circuit Switcher` -> NOT transfer; bare "switch" -> not a transfer device.
- **Device-first / anchor:** `automatic|manual transfer switch` / `ATS` / `MTS` + tag -> recognized; `candidateKind:'transfer_switch'` -> recognized; bare "switch" alone -> not counted.
- **Automation-class recognition + match:** `ATS`/`automatic` -> Automatic ref group; `+bypass`/`iso` -> Iso-Bypass ref; `MTS`/`manual` -> Manual ref group; bare "transfer switch" -> group with NO default.
- **H4 - STS + UPS:** a standalone `STS`/`static transfer switch` -> `transfer_catalog_gap` (surfaced, never mapped to the ATS ref); `UPS` stays `NON_BREAKER` (out-of-family); a `UPS-*-MIB`/`MOB`/`LBB` breaker main stays a BREAKER (not over-claimed).
- **Test-scope axis (one device, not two):** an ATS carries `(IR/DLRO)` vs `(Functional Testing)` scope -> ONE transfer line (default IR/DLRO), never two device lines.
- **Voltage:** absent voltage -> the transfer disposition, NOT `missing_voltage`.
- **Exact-ref + DUAL section-overload proof:** each of the 4 refs resolves verbatim in the live seed; assert the DC-Battery/Charger refs also sit at firm `7.18` AND generator/UPS share chapter `7.22`, so matching keys on the STRING, not the section.
- **Disposition:** a recognized transfer device -> `scope_pending` (group + optional provisional default), resolvable at Gate-2 to a valid priced envelope.
- **Golden re-baseline (D4):** `E01-11` re-baselined intentionally (STS-* rows -> transfer disposition); all NON-transfer rows + all six prior families' non-ATS goldens BYTE-IDENTICAL.

---

## Part 8 - Next steps

1. Operator ratifies D1-D6 (Part 6) + the Part 7 test list (or amends the leans).
2. Brainstorm -> spec the transfer-switch engine slice (design doc), folding the ratified decisions, reusing the switch/transformer/relay `scope_pending` machinery, and specifying the routing inversion + golden re-baseline precisely.
3. writing-plans -> SDD build (Workflow-orchestrated subagent TDD, ultracode), mirroring the prior families' contract-first / fixture-driven / fail-closed TDD rigor, with a cross-engine (Codex) IRP before merge.
4. All six prior families' goldens stay byte-identical EXCEPT the intentional ATS/MTS/STS disposition re-baseline (D4) - the re-baseline is reviewed, not silent.

---

## Part 9 - Operator ratification (2026-07-05)

PENDING. (To be filled with the operator's D1-D6 decisions + any tightenings; the spec is built on that ratified state.)
