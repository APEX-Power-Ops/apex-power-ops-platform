# Estimator-Takeoff Instrument Transformer (CT / VT / CCVT) Family (V1) - Design

Status: SPEC (operator-ratified packet 004; folds D1-D4 + the 2 operator patches [D3 additive-exclusion-not-kVA-requirement; D2 default-only-with-packaging-evidence] + the contract patch [phaseCount + packagingEvidence on signature + scope_pending + report] + the 7 must-pin tests). Date: 2026-06-29.
Lane: estimator-takeoff/instrument-transformer-family-admission (off main fcbbe3c2). Dev-only; merge operator-gated.
Packet: docs/superpowers/packets/estimator-takeoff-family-instrument-transformers.md (Part 6 decisions + Part 9 ratification).
Predecessors (reused, must stay byte-identical): breaker engine + transformer slice (PR #49) + relay slice (PR #50) + GFP slice (PR #51).

**Goal:** Admit the INSTRUMENT TRANSFORMER family (CT / VT-PT / CCVT, NETA 7.10) into `packages/estimator-takeoff` as a bounded V1 slice - the 3rd scope-driven family - so a recognized instrument transformer is counted per device and routed to a Gate-2 packaging/count scope decision (never auto-priced), while the POWER-transformer family's recognition and fail-closed behavior stay BYTE-IDENTICAL.

**Architecture:** Reuse the transformer/relay/GFP scope_pending machinery (discriminated-union signature, `scope_pending` + optional `provisionalDefaultRef`, candidateKind, kind-prefixed `deviceId`, cross-family routing). Add a fifth signature `kind: 'instrument_transformer'`, a device-first instrument-type recognizer routed FIRST in `assessCore`, an ADDITIVE instrument-token exclusion atop `looksLikeTransformer`, a type x voltage match group, and the set/each packaging+count handling. The defining difficulty is carving instrument transformers away from the EXISTING power-transformer recognizer (both contain the word "transformer") WITHOUT changing power-transformer behavior - the exclusion is purely additive (no kVA/coolant requirement is introduced).

**Tech stack:** TypeScript, Vitest, pnpm workspace; host build over `ssh olares-mesh`.

## Global Constraints

- **ASCII-only** in all authored code/comments AND engine-emitted strings (no em-dashes). Verbatim source DATA may be UTF-8.
- **Breaker AND transformer AND relay AND GFP goldens byte-identical** after every task. Four prior families now regression-guard the fifth.
- **No new catalog refs and no new hours.** V1 uses the 9 existing instrument-transformer refs only (D1). Matched by exact ref STRING, NEVER by section (the firm sections 7.1/7.6/7.14/7.15 are ALL drifted from canonical 7.10 - the strongest section-unreliability case across the families).
- **Instrument transformers never auto-price.** Every recognized instrument transformer -> `scope_pending` (candidate ref-GROUP + optional provisional default) or `catalog_gap`. No "matched" instrument-transformer line in V1.
- **Power-transformer behavior is PRESERVED.** The ONLY change to `looksLikeTransformer` is an ADDITIVE instrument-token EXCLUSION at the top; NO kVA/coolant requirement is introduced. A bare "Transformer T-1" (no kVA/coolant) MUST still surface as `transformer_attrs_unparsed`, exactly as today.
- **Provisional default ONLY with explicit packaging evidence** (D2): a candidate group is always offered; a `provisionalDefaultRef` is set only when packaging evidence (`set` / `set of 3` / `3 phase` / clear symbol grouping) is explicit. Type+voltage alone -> NO default.
- **phaseCount + packagingEvidence are CONTRACT fields** (operator contract patch): present on `InstrumentTransformerSignature`, carried onto the `scope_pending` line AND the reconciliation report, so Gate-2 has the evidence to choose packaging.
- **Gates (verified on host):** `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (cross-package false-green-trap gate).
- **Cross-engine (Codex) IRP** before merge; merge operator-gated (admin-rebase PR).
- **R1 (estimating authority) PROVISIONAL** (`ITX_R1_RATIFIED=false`): the type x voltage -> default-ref table + the set/each counting convention are provisional until the SME confirms (D1). Never auto-priced, so provisional is fail-closed.

## The V1 Contract

1. **Recognize instrument transformers DEVICE-FIRST by TYPE.** An instrument transformer is established by a producer `candidateKind:'instrument_transformer'` OR an instrument-type token + a device identity (tag). Type tokens: full device nouns `CURRENT TRANSFORMER` (CT), `POTENTIAL TRANSFORMER`/`VOLTAGE TRANSFORMER` (VT/PT), `CCVT`/`COUPLING(-)CAPACITOR (VOLTAGE TRANSFORMER)` (CCVT), or the bare abbreviations `CT`/`PT`/`VT` WITH a tag. A bare abbreviation with NO tag/anchor is NEVER counted.
2. **Route instrument FIRST; exclude instrument from power additively.** In `assessCore`, the instrument recognizer runs BEFORE the power-transformer block. `looksLikeTransformer` gains an additive exclusion: an explicit `candidateKind:'instrument_transformer'` -> false, and a FULL instrument device-noun token (current/potential/voltage transformer, CCVT, coupling-capacitor; NOT the bare CT/PT/VT abbreviations - too collision-prone for the power exclusion) -> false. NOTHING else in `looksLikeTransformer` changes; no kVA/coolant requirement is added.
3. **Scope-driven; never auto-price.** A recognized instrument transformer -> `scope_pending`: a candidate ref-GROUP (the type x voltage refs, individual + set variants) + a Gate-2 packaging/count scope question, with a PROVISIONAL default ONLY where packaging evidence is explicit, NO default otherwise. A recognized type x voltage with no priced home (D1 gaps) -> `catalog_gap`.
4. **phaseCount + packagingEvidence are contract.** The signature carries them; emit stamps them onto the `scope_pending` line; the reconciliation report surfaces them. (The operator's Gate-2 packaging decision depends on this evidence.)
5. **Voltage optional/contextual.** Voltage class drives the candidate group WHEN present; absent voltage -> a WIDER candidate group (all refs of that type) + a voltage note, NEVER `missing_voltage`.
6. **All prior family paths untouched.** `ApparatusSignature` is a discriminated union on `kind`; an instrument-transformer signature can never reach `matchBreaker`/`matchTransformer`/`matchRelay`/`matchGfp` or a priced line (compiler-enforced). Power-transformer + breaker + relay + GFP behavior byte-identical.

## Component Design (engine seams, grounded @ fcbbe3c2)

### 1. Extraction (`extraction/types.ts`, `extraction/parse.ts`)
- `extraction/types.ts`: widen `candidateKind` to `'breaker' | 'transformer' | 'relay' | 'gfp' | 'instrument_transformer'`.
- `extraction/parse.ts`: widen the validation guard to accept `'instrument_transformer'`; update the expected-string message.

### 2. Signature types (`signature/types.ts`)
- Add:
  ```ts
  export type ItxType = 'ct' | 'vt' | 'ccvt'
  export type ItxPackaging = 'individual' | 'set' | 'unknown'
  export type ItxPackagingEvidence = 'set_token' | 'set_of_3' | 'three_phase' | 'symbol_group' | 'none'
  export interface InstrumentTransformerSignature extends BaseSignature {
    kind: 'instrument_transformer'
    itxType: ItxType
    packaging: ItxPackaging
    packagingEvidence: ItxPackagingEvidence   // CONTRACT: why packaging was inferred (drives the Gate-2 default gate)
    phaseCount?: number                         // CONTRACT: observed phase/count evidence (e.g. 3); display/Gate-2 only
    ratio?: string                              // evidence/display only (e.g. "600:5")
    // voltageClass stays optional (inherited): contextual; drives the group when present, never gates.
  }
  ```
- `export type ApparatusSignature = BreakerSignature | TransformerSignature | RelaySignature | GfpSignature | InstrumentTransformerSignature`.

### 3. Recognition + parse (`signature/normalize.ts`)
- Token regexes (ASCII):
  - `INSTRUMENT_TX_DEVICE` (full device nouns - used for BOTH recognition AND the power exclusion; conservative, no bare abbreviations): `/\b(current\s+transformer|potential\s+transformer|voltage\s+transformer|coupling[\s-]?capacitor(\s+voltage\s+transformer)?|CCVT|instrument\s+transformer)\b/i`.
  - `INSTRUMENT_TX_ABBR` (bare abbreviations - recognition ONLY, tag-gated, NOT in the power exclusion): `/\b(CT|PT|VT)\b/`.
- `looksLikeInstrumentTransformer(x)`: `x.candidateKind === 'instrument_transformer'` -> true; else `(INSTRUMENT_TX_DEVICE.test(x.raw) || INSTRUMENT_TX_ABBR.test(x.raw)) && x.tag !== undefined && x.tag.length > 0`. (Device-first; bare abbreviation needs a tag.)
- `parseItxType(raw)`: CCVT/coupling-capacitor -> `ccvt`; potential/voltage transformer or `\bPT\b`/`\bVT\b` -> `vt`; current transformer or `\bCT\b` -> `ct`. (Order: CCVT before VT so "CCVT" is not read as VT.)
- `parsePackaging(raw)`: returns `{ packaging, packagingEvidence }` - `set of 3` -> `('set','set_of_3')`; `\bset\b` -> `('set','set_token')`; `3\s*(phase|ph|-phase)` or `3\s*x` -> `('set','three_phase')`; else `('unknown','none')`. (Symbol-group evidence is producer-supplied via a future field; `symbol_group` reserved.)
- `parsePhaseCount(raw)`: a leading `3 x` / `(3)` / `3-phase` -> 3; else undefined.
- `parseRatio(raw)`: capture `\d+:\d+` if present (evidence only).
- `assessInstrumentTransformer(x, voltageBasis?)`: build the signature (itxType, packaging+packagingEvidence, phaseCount, ratio, `voltageClass = classifyVoltage(x.busVoltageV)` MAY be undefined - NOT gated). `assessmentCode: 'instrument_transformer_recognized'`. Conflict guard: if the row ALSO carries a power-transformer signal (`KVA_RATING` or a coolant token) -> `instrument_transformer_power_conflict` question, signature null (an instrument-vs-power ambiguity is surfaced, never silently picked).
- `looksLikeTransformer` (power) - ADDITIVE exclusion ONLY (insert after the `candidateKind === 'relay'` line, before `candidateKind === 'transformer'`):
  ```ts
  if (x.candidateKind === 'instrument_transformer') return false   // explicit instrument producer signal yields
  if (INSTRUMENT_TX_DEVICE.test(x.raw)) return false               // instrument device noun is NOT a power transformer (additive; no kVA/coolant requirement added)
  ```
  Everything else in `looksLikeTransformer` is UNCHANGED (so a bare "Transformer T-1" still -> TRANSFORMER_DEVICE -> assessTransformer -> `transformer_attrs_unparsed`).
- `assessCore` order: insert the instrument route FIRST, before the `looksLikeTransformer` block: `if (looksLikeInstrumentTransformer(x)) return assessInstrumentTransformer(x, voltageBasis)`. New order: instrument -> transformer -> GFP -> relay -> NON_BREAKER -> breaker.
- New `AssessmentCode` members: `instrument_transformer_recognized`, `instrument_transformer_power_conflict`.

### 4. Match (`catalog/instrument-transformer-map.ts` + `.data.ts`)
- `.data.ts`: the 9 refs VERBATIM (exact strings); an `ITX_GROUPS: Record<\`${ItxType}:${VoltageClass|'unknown'}\`, string[]>`-shaped map -> candidate ref-group (individual + set variants for that type x voltage); `ITX_R1_RATIFIED = false`.
- `.ts`: `interface ItxScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }`; `matchInstrumentTransformer(sig): ItxScopeMatch | null`:
  - resolve the candidate group by `itxType x voltageClass` (absent voltage -> the union of that type's refs across voltage = wider group);
  - `defaultRef` set ONLY when `sig.packagingEvidence !== 'none'` AND the group has a clear individual-vs-set member matching the packaging (e.g. packaging `set` + MV CT -> "Current Transformer MV - Set of 3"); else `undefined` (D2 - no default without packaging evidence);
  - no priced home for the type x voltage -> `null` (-> catalog_gap).

### 5. Quantify (`quantify/quantify.ts`)
- Add an `s.kind === 'instrument_transformer'` branch to `specKey` BEFORE the transformer fall-through: `[s.kind, s.itxType, s.voltageClass ?? '-', s.packaging, s.source.block ?? '-'].join('|')`. (`phaseCount`/`ratio` are evidence, NOT in the key - two banks of the same type/voltage/packaging aggregate; the operator resolves count at Gate-2.) `deviceId` kind-prefixes (`instrument_transformer:TAG`). `pickAuthoritative` needs no itx-specific change.

### 6. Disposition + contract (`buckets/types.ts`, `emit/emit.ts`, `runner/report.ts`)
- `buckets/types.ts`: `OperatorQuestionCode` += `instrument_transformer_scope_pending` | `instrument_transformer_catalog_gap` | `instrument_transformer_power_conflict`; `DispositionReasonCode` += same three; `TakeoffFinding.code` += `instrument_transformer_catalog_gap`. **Add the contract evidence fields to `ScopePendingLine`: `packagingEvidence?: string` + `phaseCount?: number`** (optional; only instrument-transformer lines set them).
- `emit/emit.ts`: import `matchInstrumentTransformer` + `ITX_R1_RATIFIED` + the type. Add the `sig.kind === 'instrument_transformer'` branch in the match loop BEFORE the transformer fall-through: a scope match -> `scope_pending` (candidateRefs=group, provisionalDefaultRef=defaultRef [may be undefined], r1Ratified=ITX_R1_RATIFIED, **packagingEvidence=sig.packagingEvidence, phaseCount=sig.phaseCount**, scopeQuestion); a `null` match -> `catalog_gap` finding + disposition. **Update `ASSESS_TO_REASON`** for `instrument_transformer_recognized` -> `instrument_transformer_scope_pending` and `instrument_transformer_power_conflict` -> `instrument_transformer_power_conflict`.
- `runner/report.ts`: the `scopePending` projection gains `packagingEvidence` + `phaseCount`; `renderReportText` prints them on the Gate-2 block (e.g. `packaging=set_of_3 phases=3`). Family-agnostic scope_pending handling (partial_preview) otherwise unchanged.

## The crux, expanded - the must-pin recognition cases

1. **"Current Transformer ..." + tag -> instrument, NOT power.** `looksLikeInstrumentTransformer` matches (device noun + tag); routed first. Even if it reached `looksLikeTransformer`, `INSTRUMENT_TX_DEVICE` excludes it.
2. **"Potential Transformer" / "Voltage Transformer" + tag -> instrument.** Same path; `parseItxType` -> `vt`.
3. **"Transformer T-1 500kVA dry-type" -> POWER transformer.** No instrument device noun -> `looksLikeInstrumentTransformer` false; `looksLikeTransformer` unchanged -> TRANSFORMER_DEVICE + kVA -> assessTransformer (recognized power transformer). Byte-identical.
4. **"Transformer T-1" (bare) -> existing fail-closed behavior.** No instrument noun, no kVA/coolant -> instrument false; `looksLikeTransformer` -> TRANSFORMER_DEVICE true -> assessTransformer -> `transformer_attrs_unparsed`. IDENTICAL to today (the additive exclusion did not touch this path).
5. **Bare "CT" / "PT" with no anchor -> not counted.** `INSTRUMENT_TX_ABBR` matches but no tag -> `looksLikeInstrumentTransformer` false; not an instrument device noun for the power exclusion; no power signal -> falls to NON_BREAKER/unrecognized. Not counted.
6. **Type+voltage but NO packaging evidence -> scope_pending, NO default.** e.g. "Current Transformer, 480V" + tag, no set/phase token -> group offered, `provisionalDefaultRef` undefined (D2).
7. **Instrument+power conflict -> question.** A row with an instrument noun AND a kVA rating -> `instrument_transformer_power_conflict` (surfaced, never silently picked).

## R1 (estimating authority) - provisional

`ITX_R1_RATIFIED = false`. R1 here = (a) the type x voltage -> default-ref table (the `ITX_GROUPS` defaults) AND (b) the set/each counting convention (a "Set" ref = one priced unit per 3-phase bank; an individual ref = per device). Surfaced as `r1Ratified:false` on the scope_pending line. Never auto-priced, so fail-closed. The SME confirms the convention + the bounded catalog gaps (no LV-individual CT, no LV/HV PT, no HV-individual CT distinct from "Bushing HV/MV"), then flips it.

## Testing (TDD; operator must-pin tests in bold)

- **#1 Current Transformer + tag -> instrument_transformer (NOT power); disposition `instrument_transformer_scope_pending`.**
- **#2 Potential Transformer / Voltage Transformer + tag -> instrument_transformer (itxType vt).**
- **#3 "Transformer T-1 500kVA dry-type" -> power transformer (transformer_scope_pending / its existing path), NOT instrument.**
- **#4 "Transformer T-1" (bare) -> `transformer_attrs_unparsed` (existing fail-closed behavior, unchanged).**
- **#5 bare "CT"/"PT" no anchor -> NOT counted (unrecognized).**
- **#6 type+voltage, no packaging evidence -> scope_pending with `provisionalDefaultRef` undefined.**
- **#7 breaker AND transformer AND relay AND GFP goldens byte-identical.**
- type recognition: CT/PT/CCVT -> correct itxType + candidate group.
- voltage classification: MV CT -> MV CT group; absent voltage -> wider group + note, NOT `missing_voltage`.
- set-vs-each: "Current Transformer (3) MV" / "...Set of 3" -> scope_pending surfacing BOTH individual + set candidates, `packagingEvidence` + `phaseCount` carried onto the line AND the report.
- exact-ref validation + section-overload proof: each of the 9 refs resolves verbatim in the live seed; assert the firm sections are scattered (7.1/7.6/7.14/7.15, none 7.10) so matching keys on the STRING.
- instrument+power conflict: instrument noun + kVA -> `instrument_transformer_power_conflict`.
- cross-family: an instrument-transformer signature can never reach matchBreaker/matchTransformer/matchRelay/matchGfp; a power-transformer/breaker/relay/GFP row never produces an instrument line.
- ASSESS_TO_REASON: the two new codes map to their reason codes.
- runner: an instrument-only extraction -> `partial_preview`; the scope_pending carried in the report with packagingEvidence/phaseCount.
- golden: a real switchgear/feeder one-line (a 3-phase CT bank + a PT set + a REAL power transformer + a breaker coexist) -> power transformer scope_pends to its group, CT/PT scope_pend to instrument groups, breaker prices, `partial_preview`; Gate-2 stand-in prices a chosen instrument ref via estimator-core.

## Out of scope (V2)

High-accuracy instrument transformers (NETA 7.10.4, RESERVED - no procedures); metering-class vs relaying-class accuracy distinctions if the firm prices them; the embedded-vs-standalone bushing-CT nuance (a bushing CT the firm sometimes rolls into the parent transformer/breaker vs prices separately - V1 counts a distinct tagged instrument transformer; the rolled-in case is a Gate-2 scope call); ratio/burden-based ref selection; producer `symbol_group` packaging evidence (the field is reserved but V1 infers packaging from text only); the Gate-2 resolution UI.
