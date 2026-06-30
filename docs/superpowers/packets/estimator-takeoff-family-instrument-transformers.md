# Apparatus Family Admission Process - Packet 004: Instrument Transformers (CT / VT / CCVT)

Status: SCOPING PACKET (pre-spec). Author: CC (technical authority). Date: 2026-06-29.
Lane: estimator-takeoff/instrument-transformer-family-admission (off main fcbbe3c2). Dev-only; merge operator-gated.
Feeds: docs/superpowers/specs/<date>-estimator-takeoff-instrument-transformer-family-design.md (next, after operator ratifies the Open Decisions in Part 6).

Grounding sources (read-only, this session, verified directly against the live files at main fcbbe3c2):
- Doctrine + templates: Packet 001 (transformers), 002 (relays), 003 (GFP), all merged to main.
- Engine: packages/estimator-takeoff/src/* @ main fcbbe3c2 (post-GFP-merge: discriminated-union signature {breaker|transformer|relay|gfp}, scope_pending disposition with optional provisionalDefaultRef, candidateKind, NON_BREAKER, parent-shape + cross-family guards all live).
- Priced catalog (accounting SSoT): packages/estimator-core/src/catalog/equipment-models.seed.json (9 instrument-transformer refs).
- NETA test-scope SSoT: infra/database/migrations/records/006_neta_reference_seed.sql (records.neta_procedures 7.10.1/7.10.2/7.10.3, category instrument_transformers).
- Power-transformer recognizer (the cross-family hazard): packages/estimator-takeoff/src/signature/normalize.ts (TRANSFORMER_DEVICE, looksLikeTransformer).

---

## Part 0 - Doctrine (reference)

This packet applies the Apparatus Family Admission doctrine (Packet 001 Part 0) to the FIFTH family - instrument transformers (CT/VT/CCVT) - after breakers (signature-deterministic), transformers (scope-driven), relays (scope-driven), and GFP (recognition-gated single-ref). Doctrine unchanged: scoping-packet-first, accounting-before-pricing, fail-closed, in gate order (characterize vs the NETA SSoT -> ratify ACCOUNTING first -> define engine RECOGNITION / SIGNATURE / MATCH -> QUANTITY/ACCOUNTING semantics -> golden + tests). The engine only maps a recognized apparatus onto an already-priced ref; it never originates a price.

Instrument transformers land squarely on the **SCOPE/CONFIG-driven** end (the 3rd scope-driven family, with transformers + relays). This packet picks up the explicit Packet-001 D3 deferral ("V1 = power dry+oil only; defer instrument CT/VT/CCVT/PT").

---

## Part 1 - Instrument-transformer characterization (grounded)

### 1a. Canonical NETA test scope (SSoT = records.neta_procedures, category instrument_transformers)
Section 7.10, cleanly split by type:
- `7.10.1` Instrument Transformers, **Current Transformer** (CT)
- `7.10.2` Instrument Transformers, **Voltage Transformers** (VT / PT)
- `7.10.3` Instrument Transformers, **Coupling-Capacitor Voltage Transformers** (CCVT)
- `7.10.4` High-Accuracy Instrument Transformers - **RESERVED** in the standard (no test procedures defined).

The canonical taxonomy (CT / VT / CCVT) maps 1:1 to the firm's catalog types (Current Transformer / Potential Transformer / CCVT). Instrument-transformer testing also appears as an EMBEDDED sub-item inside other procedures ("Test instrument transformers in accordance with Section 7.10" within power-transformer + switchgear procedures) - but unlike GFP, the firm PRICES instrument transformers as their own line items (e.g. a dedicated "Current Transformer - Bushing HV/MV" ref), so they ARE counted as distinct apparatus when present (Part 3).

### 1b. Physical/role sub-types the takeoff must distinguish
- **Type:** CT (current) vs VT/PT (voltage/potential) vs CCVT (coupling-capacitor voltage). Distinct refs per type.
- **Voltage class:** LV vs MV vs HV. A ref discriminator (CT LV / CT MV / CT Bushing HV/MV; PT MV; CCVT = transmission/HV).
- **Packaging / count:** individual device vs a 3-phase SET (a CT/PT bank). The catalog carries BOTH individual and set refs for CTs, and "set" refs for PT/CCVT (Part 2 / Part 3 quantity crux).

### 1c. Identity on the drawing
A CT/PT/CCVT shows up as a small circle/symbol on a bus, feeder, or transformer/breaker bushing, often labeled `CT`/`PT`/`VT`/`CCVT` with a tag, sometimes with a ratio (e.g. `600:5`) or a phase/set notation (`3 x CT`, `CT (3)`). The literal words "Current Transformer" / "Potential Transformer" / "Voltage Transformer" appear in schedules.

---

## Part 2 - The accounting layer EXISTS, by type x voltage x packaging (key finding)

The estimator-core seed carries **9 instrument-transformer refs**, all `lifecycle_status: active`:

| ref | firm sec | ATS h | MTS h | unit_of_issue | note |
|---|---|---|---|---|---|
| Current Transformer - Bushing HV/MV | 7.14 | 2.0 | 2.0 | each | individual HV/MV bushing CT |
| Current Transformer - Bushing, HV/MV (Set) | 7.14 | 6.0 | 6.0 | **set** | the only uoi=set ref |
| Current Transformer LV - Set of 3 | 7.15 | 2.0 | 2.5 | each | LV 3-phase CT bank (priced per set) |
| Current Transformer MV - Set of 3 | 7.14 | 2.0 | 2.5 | each | MV 3-phase CT bank (priced per set) |
| Potential Transformer - MV | 7.1 | 3.0 | 3.0 | each | individual MV PT |
| Potential Transformer - MV Set | 7.1 | 3.0 | 3.0 | each | MV PT set (priced per set) |
| Potential Transformer (set) | 7.1 | 2.0 | 2.0 | each | generic PT set (priced per set) |
| CCVT Voltage Transformer - Individual | 7.1 | 5.0 | 5.0 | each | individual CCVT |
| CCVT Voltage Transformer - Set of 3 | 7.6 | 12.0 | 12.0 | each | CCVT 3-phase set (priced per set) |

**Answer to the Packet-001 D3 research question (instrument-transformer accounting):** the catalog is RICH (9 refs spanning CT/PT/CCVT x LV/MV/HV x individual/set) - accounting is largely SATISFIED at the catalog level, like transformers/relays. Admission = ENGINE-side recognition + match onto existing refs + a bounded completeness audit, NOT hour authoring.

**Data-hygiene trap #1 - SECTION DRIFT is EXTREME (HARD guard).** The firm `neta_section` for these 9 refs is scattered across **7.1, 7.6, 7.14, 7.15** - and NOT ONE of them is the canonical instrument-transformer section 7.10. (Canonical: CT/VT/CCVT = 7.10.1/2/3.) The firm sections are also overloaded (7.1 also holds switchgear/CPT/generator refs; 7.14 also holds GFP - see Packet 003). Therefore: **instrument-transformer refs MUST be matched by their exact ref/apparatus STRING, never by section.** This is the strongest section-unreliability case across all five families.

**Data-hygiene trap #2 - the unit_of_issue convention is INCONSISTENT (estimating authority, D1).** The ref NAME and the `unit_of_issue` disagree: most "Set of 3" / "Set" refs carry `uoi=each` (e.g. "CT MV - Set of 3" = 2.0h, uoi=each), while one carries `uoi=set` ("CT Bushing HV/MV (Set)" = 6.0h, uoi=set). The hours confirm the intent: "CT MV - Set of 3" at 2.0h is clearly the WHOLE 3-phase set (not 3x an individual CT's 2.0h). So the firm convention is: **a "Set" ref = ONE priced unit that bundles the 3-phase bank (qty counts SETS), regardless of whether uoi reads "each" or "set"; an individual ref = qty counts individual devices.** This drives the quantity crux (Part 3).

**Bounded catalog GAPS to confirm with the estimating/SME authority (D1):** no LV-individual CT, no LV or HV PT (PT is MV-only), no HV-individual CT distinct from the combined "Bushing HV/MV"; the CCVT refs are transmission-class only. Where the drawing shows a type x voltage with no priced home -> `catalog_gap` (surfaced, never fabricated).

---

## Part 3 - The design crux: power-transformer disambiguation + the set/each quantity semantics

Two engine-visible difficulties, both new relative to the prior families.

### 3a. Cross-family hazard: instrument transformer vs POWER transformer (the recognition crux)
A "Current Transformer" / "Potential Transformer" / "Voltage Transformer" is NOT a power transformer - but both contain the word "transformer". The EXISTING power-transformer recognizer keys on exactly that: `TRANSFORMER_DEVICE = /XFMR|transformer|dry.?type|pad.?mount|oil.?filled/`, and `looksLikeTransformer` fires on any "transformer" substring. So TODAY a "Current Transformer 480V" row is CLAIMED by the power-transformer family (it then fail-closes to `transformer_attrs_unparsed` since a CT has no kVA/coolant - fail-closed but WRONG family).

The guard (mirrors the GFP standalone-vs-parent logic, but here it is instrument-vs-power):
- An instrument transformer (CT/PT/VT/CCVT) is recognized by an INSTRUMENT-TYPE token + tag, and must be routed BEFORE the power-transformer path.
- `looksLikeTransformer` (power) must EXCLUDE instrument types: a POWER transformer is "transformer"/"XFMR" + a power signature (kVA rating OR a coolant/construction token dry/oil/pad-mount), and carries NO instrument-type qualifier (current/potential/voltage/coupling-capacitor/instrument).
- The discriminator is reliable: a power transformer has kVA + coolant; an instrument transformer has a type qualifier (current/potential/voltage/CCVT) and a ratio (600:5), never kVA/coolant.

### 3b. Quantity semantics: individual vs set (the accounting wrinkle)
A 3-phase CT/PT bank maps to EITHER qty=3 of an individual ref OR qty=1 of a "Set of 3" ref - and the catalog has both. The drawing shows phases/symbols (evidence of count) but not the firm's per-device-vs-per-set pricing CHOICE. So the engine cannot decide the ref (and therefore the qty) without the scope decision. This is folded into the Gate-2 scope question: surface the candidate ref-GROUP (individual + set variants for the recognized type x voltage) + the observed phase/count as EVIDENCE; the operator picks the packaging, which fixes the ref AND the qty. Never auto-priced. (Per-set refs are priced "1 unit = the bank"; individual refs are priced per device - the chosen ref's convention determines counting, per D1/Part 2.)

### 3c. Match model (consequence)
> signature (type + voltage class + packaging evidence) -> a candidate **ref-GROUP** (the type x voltage refs, individual + set variants) + a REQUIRED Gate-2 scope question (packaging/count), with a CONSERVATIVE provisional default where type+voltage are legible (e.g. an MV CT bank -> "Current Transformer MV - Set of 3"), and NO default where the type/voltage is illegible. A recognized instrument transformer surfaces as **scope_pending** (reusing the transformer/relay machinery), never auto-priced. A recognized type x voltage with no priced home (D1 gaps) -> `catalog_gap`.

---

## Part 4 - Engine admission seams (checklist, mirrors Packet 002/003 Part 4)

The breaker/transformer/relay/GFP slices built the machinery (discriminated-union signature, scope_pending + optional provisionalDefaultRef, candidateKind, NON_BREAKER, cross-family conflict guards, ASCII guards). Instrument-transformer admission REUSES it; the new work is a fifth `kind`, an instrument-type recognizer with the power-transformer guard, a type x voltage match table, and the set/each quantity handling.

1. **Recognition.** signature/normalize.ts: add `INSTRUMENT_TX` type tokens (`current transformer`/`CT`, `potential transformer`/`voltage transformer`/`PT`/`VT`, `CCVT`/`coupling.?capacitor`) and a `looksLikeInstrumentTransformer` (type token + tag, OR `candidateKind:'instrument_transformer'`). Route in assessCore BEFORE `looksLikeTransformer`. AMEND `looksLikeTransformer` to EXCLUDE instrument types (a power transformer needs kVA/coolant AND no instrument-type qualifier). Keep breaker/relay/GFP paths byte-intact; add an instrument-vs-power conflict guard if a row carries both a kVA rating and an instrument-type token.
2. **Signature.** signature/types.ts: extend `ApparatusSignature = ... | InstrumentTransformerSignature`. `InstrumentTransformerSignature { kind:'instrument_transformer'; itxType:'ct'|'vt'|'ccvt'; packaging:'individual'|'set'|'unknown'; phaseCount?: number; ratio?: string; voltageClass?: VoltageClass }`. voltageClass stays optional/contextual (inherited; never gates - cf relay/GFP).
3. **Parsing.** signature/normalize.ts: text-only fail-closed `parseItxType`, `parsePackaging` (set / set-of-3 / 3-phase notation -> set; else individual/unknown), `parsePhaseCount`, `parseRatio` (evidence); `assessInstrumentTransformer`. Absent/ambiguous -> scope_pending / question, never fabrication.
4. **Voltage routing.** signature/voltage.ts reused; voltage CLASS influences the candidate group but does NOT gate (absent -> wider group + a voltage note, not `missing_voltage`).
5. **Match model.** New catalog/instrument-transformer-map.ts + .data.ts: the 9 refs VERBATIM (exact strings); a `ITX_GROUPS` map keyed by `itxType x voltageClass` -> candidate ref-group (individual + set variants); `matchInstrumentTransformer(sig) -> { group, defaultRef?, scopeQuestion } | null`. Legible type+voltage -> group + conservative provisional default; illegible -> no default; no priced home -> null (catalog_gap). Never a single auto-priced ref.
6. **Quantify.** quantify/quantify.ts: extend `specKey` with the itx fields (type, voltageClass, packaging); kind-prefixed `deviceId` keeps itx rows from cross-bucketing. The set-vs-each count is NOT resolved in quantify (the ref/packaging is a Gate-2 choice); quantify carries phaseCount as evidence on the line.
7. **Buckets / disposition.** buckets/types.ts + emit/emit.ts: reuse `scope_pending` (candidate group + optional provisional default + scopeQuestion); add itx reason/question codes (`instrument_transformer_scope_pending`, `instrument_transformer_catalog_gap`, and an instrument-vs-power conflict code if 1 is built). Breaker/transformer/relay/GFP emit byte-intact. Update the compiler-checked `ASSESS_TO_REASON`.
8. **Catalog.** estimator-core seed: the 9 refs exist; NO new refs. AUDIT the bounded gaps (Part 2 / D1) + the set/each convention -> estimator/SME.
9. **Tests + golden.** normalize-itx, itx-map, itx-cross-family (the POWER-TRANSFORMER guard is the load-bearing test), set-vs-each quantity, exact-ref-vs-seed + section-overload proof, and a real golden (a switchgear/feeder one-line with CT bank + PT set + a real POWER transformer + a breaker coexisting) -> power transformer scope_pends to its own group, CTs/PTs scope_pend to instrument groups, breaker prices, partial_preview; Gate-2 stand-in prices a chosen itx ref. TDD; breaker AND transformer AND relay AND GFP goldens BYTE-IDENTICAL throughout.

**Unchanged (family-agnostic):** compile, rate-card, labor allocation, extended_cents, project_intake_qty/M4, voltage assertions, reconcile/isClean. Accounting->pricing boundary preserved: takeoff emits ref + qty only.

---

## Part 5 - Accounting-before-pricing, preserved

The takeoff emits pure accounting (ref, qty, designation, provenance); estimator-core's compile resolves ref_hours + M4/labor/rates. An instrument transformer never carries hours until (a) its type x voltage x packaging is fixed by a legible provisional default or the operator's Gate-2 choice AND (b) that ref already exists priced in the catalog. No path lets the engine originate an instrument-transformer price, and the per-set-vs-per-device count follows the chosen ref's convention (D1), never an engine guess.

---

## Part 6 - OPEN DECISIONS (operator ratification before spec)

Tiered, with my lean. These gate the move from this packet to the design spec.

**D1 - Accounting / catalog completeness + the set/each convention (estimating authority).** Confirm the 9 instrument-transformer refs are the V1 priced set, matched by exact ref STRING (NEVER section - the firm sections 7.1/7.6/7.14/7.15 are ALL drifted from canonical 7.10). *Lean:* use the 9 refs, author NO new hours. Two SME items: (a) **the set/each counting convention** - confirm that a "Set"/"Set of 3" ref = ONE priced unit per 3-phase bank (qty counts sets) and an individual ref = qty per device, so the takeoff counts correctly; (b) **bounded gaps** - no LV-individual CT, no LV/HV PT, no HV-individual CT distinct from "Bushing HV/MV"; where a drawing shows a type x voltage with no priced home -> `catalog_gap`. I produce the gap list + the convention question; ratifying/authoring is yours.

**D2 - Match model + packaging/quantity scope (design).** Ratify scope-driven: engine surfaces a candidate ref-GROUP (type x voltage, individual + set variants) + a Gate-2 packaging/count scope question, resolved at Gate-2, NEVER auto-priced; phase/count is surfaced as EVIDENCE for the operator's packaging choice (which fixes both the ref and the qty). *Lean:* scope-driven YES; provisional default ONLY where type+voltage are legible (e.g. MV CT bank -> "Current Transformer MV - Set of 3"); illegible type/voltage -> candidate group with NO default. R1 (the type x voltage -> default-ref table) PROVISIONAL until the estimator confirms.

**D3 - Recognition + the POWER-TRANSFORMER cross-family guard (the crux).** Ratify device-first recognition by instrument-TYPE token (current/potential/voltage/coupling-capacitor/instrument transformer, or CT/PT/VT/CCVT, + a tag), routed BEFORE the power-transformer path, AND amend `looksLikeTransformer` (power) to EXCLUDE instrument types (a power transformer = "transformer"/XFMR + kVA/coolant, never an instrument qualifier). Bare type abbreviations (`CT`/`PT`/`VT`) with no device anchor are evidence, never counted (device-first). *Lean:* as stated; the power-transformer recognizer yields to the instrument-transformer recognizer; an instrument-vs-power conflict (a row with BOTH kVA and an instrument token) surfaces a question, never a silent pick. Confirm the power-transformer goldens stay byte-identical (the amendment must not reclassify any existing power-transformer row).

**D4 - V1 sub-type scope.** *Lean:* V1 = CT + VT/PT + CCVT at the 9 existing refs - the firm's common cases. DEFER to V2: (a) high-accuracy instrument transformers (NETA 7.10.4, RESERVED - no procedures anyway); (b) metering-class vs relaying-class accuracy distinctions if the firm prices them separately; (c) the embedded-vs-standalone nuance (bushing CTs on a transformer/breaker that the firm sometimes rolls into the parent vs prices separately - V1 counts them when they appear as distinct tagged apparatus, the rolled-in case is a Gate-2 scope call); (d) ratio-based ref selection if the firm ever prices by ratio/burden; (e) the Gate-2 resolution UI.

(NETA-section reconciliation - the transformer D4 - is INFORMATIONAL here: canonical 7.10.1/2/3 is clean and matches the firm CT/PT/CCVT taxonomy, but the firm CATALOG sections are extremely drifted (7.1/7.6/7.14/7.15); the resolution is the match-by-string guard in Part 2/D1, not a separate decision.)

---

## Part 7 - Required spec tests (to pin at ratification)

Pre-stated so the spec inherits them:
- **Cross-family - POWER transformer (the load-bearing guard):** "Current Transformer" / "Potential Transformer" / "Voltage Transformer" + tag -> instrument-transformer family (NOT power transformer); a REAL power transformer (kVA + dry/oil) stays power transformer; the transformer golden stays BYTE-IDENTICAL.
- **Type recognition:** CT -> CT group, PT/VT -> VT group, CCVT -> CCVT group.
- **Voltage classification:** voltage class drives the candidate group (an MV CT -> MV CT refs); absent voltage -> wider group + note, NOT `missing_voltage`.
- **Device-first:** a bare `CT` / `PT` with no device anchor is NOT counted.
- **Set vs each (quantity):** a 3-phase CT bank -> scope_pending surfacing BOTH the individual and the set candidates + the phase-count evidence; never auto-priced.
- **Exact-ref validation + section-overload proof:** each of the 9 refs resolves verbatim in the live seed; assert the firm sections are scattered (7.1/7.6/7.14/7.15, none 7.10) so matching keys on the STRING, not the section.
- **Disposition:** a recognized instrument transformer -> scope_pending (group + optional provisional default), resolvable at Gate-2 to a valid priced envelope.
- **Breaker AND transformer AND relay AND GFP goldens BYTE-IDENTICAL** (four prior families now regression-guard the fifth).

---

## Part 8 - Next steps

1. Operator ratifies D1-D4 (Part 6) + the Part 7 test list.
2. Brainstorm -> spec the instrument-transformer engine slice (design doc), folding the ratified decisions, reusing the transformer/relay/GFP scope_pending machinery.
3. writing-plans -> SDD build (Workflow-orchestrated subagent TDD, ultracode), mirroring the prior families' contract-first / fixture-driven / fail-closed TDD rigor, with cross-engine (Codex) IRP before merge.
4. Breaker AND transformer AND relay AND GFP goldens stay byte-identical throughout (four prior families now regression-guard the fifth).

---

## Part 9 - Operator ratification (2026-06-29)

The operator independently grounded the packet (confirmed: the 9 refs exist; canonical 7.10.1/2/3 maps to CT/PT/CCVT; the current power-transformer recognizer WOULD claim Current/Potential Transformer unless instrument routes first) and ratified D1-D4 with two tightening patches + a must-pin test list. Recorded so the spec is built on the ratified state.

**Ratified decisions:**
- **D1 (accounting):** the 9 instrument-transformer refs are the V1 priced set; exact ref-STRING matching ONLY (NEVER section - firm 7.1/7.6/7.14/7.15 all drifted from canonical 7.10); author NO new hours; bounded gaps -> `catalog_gap`. SME owns the set/each counting convention.
- **D2 (match model) - PATCHED:** scope-driven, never auto-price; candidate ref-GROUP + Gate-2 packaging/count question. **Provisional default ONLY when PACKAGING evidence is explicit** (a `set` / `3 phase` / `set of 3` / clear symbol-grouping token) - type+voltage ALONE is NOT enough (PT-MV vs PT-MV-Set; CT individual vs set). Without packaging evidence -> scope_pending with NO default.
- **D3 (recognition) - PATCHED (do NOT over-tighten power recognition):** route the instrument recognizer FIRST, and add an instrument-token EXCLUSION at the TOP of `looksLikeTransformer` (so power yields instrument types) - but DO NOT add a kVA/coolant REQUIREMENT to power-transformer recognition. The existing power-transformer behavior (recognize "transformer"/XFMR device text, then fail-close to `transformer_attrs_unparsed` when attrs incomplete) must stay IDENTICAL for non-instrument rows, so a bare "Transformer T-1" still surfaces as a transformer question. An instrument+power evidence conflict (a row with BOTH kVA/coolant AND an instrument-type token) -> a question, never a silent pick. Transformer golden byte-identical.
- **D4 (V1 scope):** CT + VT/PT + CCVT at the 9 refs; defer high-accuracy (7.10.4 RESERVED), metering-vs-relaying accuracy class, embedded-vs-standalone bushing-CT nuance, ratio-based selection, Gate-2 UI.

**Contract patch (operator) - phase/packaging evidence is part of the CONTRACT, not just internal parsing:** the spec MUST place the evidence explicitly on `InstrumentTransformerSignature.phaseCount` + `InstrumentTransformerSignature.packagingEvidence`, AND carry it through the `scope_pending` line + the reconciliation report output, so Gate-2 has the evidence it needs to choose packaging.

**Must-pin spec/plan hard-gate tests (operator):**
1. "Current Transformer ..." + tag -> instrument transformer, NOT power transformer.
2. "Potential Transformer" / "Voltage Transformer" + tag -> instrument transformer.
3. "Transformer T-1 500kVA dry-type" -> remains POWER transformer.
4. "Transformer T-1" (bare, no kVA/coolant) -> still surfaces under the existing transformer fail-closed behavior (`transformer_attrs_unparsed`); NOT reclassified, NOT requiring kVA.
5. Bare "CT" / "PT" with no real device anchor -> NOT counted.
6. Type+voltage but NO packaging evidence -> scope_pending with NO provisional default.
7. All prior breaker/transformer/relay/GFP goldens BYTE-IDENTICAL.

These are folded into the spec; the spec is built on this ratified state.
