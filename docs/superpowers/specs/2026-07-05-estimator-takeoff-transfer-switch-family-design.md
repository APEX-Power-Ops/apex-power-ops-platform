# Estimator-Takeoff Automatic / Transfer Switch Family (V1) - Design

Status: SPEC Rev 2.0 (Rev 1.0 folded operator-ratified packet 006 D1-D6 + the D6 grounding correction; **Rev 2.0 folds the adversarial IRP + Codex cross-engine review (5 lenses, 2026-07-05)**: the REDESIGNED inversion - do NOT edit `NON_BREAKER` (rev 1's edit had 4-way collateral: it regressed the GFP parent-shape guard, the transformer kVA-fallback exclusion, the NON_BREAKER tail, and the breaker-fallback guard); instead route the transfer recognizer BEFORE the NON_BREAKER tail and use a transfer-local conflict predicate - so every NON_BREAKER consumer stays byte-identical. Plus 8 folded fixes: SKILL.md added to the D4 re-baseline; the "7.22 dual-overload" claim corrected to the real 7.18-only priced-seed overload; must-pin #5 corrected (a UPS main stays `non_breaker_carries_rating`, NOT a priced breaker); dual-profile `ref_hours` (ATS/MTS) corrected; the re-baseline tests TIGHTENED to positively assert `transfer_parent_conflict` (non-vacuous); a `candidateKind:'transfer_switch'` hard-win short-circuit; D4 enumerated file:line; the rating-annotated-ATS recognition posture surfaced as OPEN DECISION T1. **Rev 3.0 folds the operator's T1 ruling (Option B, amended, 2026-07-06): a transfer-anchored `AF/AT` - a lone `AF`/`AT` token OR a full `###AF/###AT` PAIR - with NO trip-function / breaker-hint / co-located non-breaker token is RATING EVIDENCE (`ampRating`) -> transfer scope_pending (never auto-priced); `transfer_parent_conflict` fires ONLY on a trip-function (`LSI`/`LSIG`), an unambiguous breaker hint, or a co-located non-transfer non-breaker token. Route order + `NON_BREAKER` preservation UNCHANGED.**) Date: 2026-07-06.
Lane: estimator-takeoff/transfer-switch-family-admission (off main ef83b5d7). Dev-only; merge operator-gated.
Packet: docs/superpowers/packets/estimator-takeoff-family-transfer-switches.md (Part 6 decisions + Part 9 ratification).
Predecessors (reused; must stay byte-identical - now including the tagless-transfer + GFP + transformer paths): breaker + transformer (PR #49) + relay (PR #50) + GFP (PR #51) + instrument-transformer (PR #52) + switch (PR #53/#54).

**Goal:** Admit the AUTOMATIC / TRANSFER SWITCH family (NETA **7.22.3**) into `packages/estimator-takeoff` as a bounded V1 slice - the 7th apparatus family - so a recognized, TAGGED transfer switch is counted per device and routed to a Gate-2 automation-class scope decision (never auto-priced), a main-tie-main breaker-pair SCHEME keeps its breakers as breakers, and all prior families + tagless rows stay BYTE-IDENTICAL except the intentional, documented re-baseline of the TAGGED transfer rows (D4).

**Architecture:** Reuse the switch/transformer/relay `scope_pending` machinery (discriminated-union signature, `scope_pending` + optional `provisionalDefaultRef`, `candidateKind`, kind-prefixed `deviceId`, cross-family conflict guards). Add a seventh signature `kind:'transfer_switch'`. Transfer devices differ from the six prior families: `ATS`/`MTS`/`STS` are tokens in `NON_BREAKER` (normalize.ts:8) and the spelled-out `transfer switch` is in `SWITCH_EXCLUDE` (normalize.ts:25). **Rev-2 approach (post-IRP): DO NOT edit `NON_BREAKER`.** Instead route a device-first transfer recognizer BETWEEN `looksLikeSwitch` (normalize.ts:485) and the `NON_BREAKER` tail (normalize.ts:489), so a TAGGED transfer-anchored row is claimed BEFORE the tail runs; and give the transfer conflict guard a transfer-LOCAL non-breaker predicate (`NON_BREAKER` minus `ATS`/`MTS`/`STS`) so a plain `ATS` row never self-conflicts. Because `NON_BREAKER` is unchanged, every consumer of `NON_BREAKER.test()` (the GFP `isGfpParentShape` guard, the transformer kVA-fallback exclusion, the NON_BREAKER tail, the breaker-fallback guard, the switch/instrument conflict guards) stays byte-identical; the ONLY behavior change is that TAGGED transfer-anchored rows now route to the transfer family instead of falling to the tail.

**Tech stack:** TypeScript, Vitest, pnpm workspace; host build over `ssh olares-mesh`.

## Global Constraints

- **ASCII-only** in all authored code/comments AND engine-emitted strings (no em-dashes). Verbatim source DATA may be UTF-8.
- **Canonical NETA section = `7.22.3`** (Automatic Transfer Switches, under 7.22 Emergency Systems). The packet's "7.16" (Motor Control) and the switch packet's loose "7.18/7.22" are RECORDED mislabels; nothing keys on them.
- **`NON_BREAKER` (normalize.ts:8) is NOT edited** (rev-2 redesign). The transfer recognizer routes BEFORE the NON_BREAKER tail; a transfer-local conflict predicate replaces the full `NON_BREAKER.test` inside the transfer guard. This preserves the four NON_BREAKER consumers the rev-1 edit would have regressed (GFP `isGfpParentShape` normalize.ts:231; transformer kVA-fallback normalize.ts:106; the NON_BREAKER tail normalize.ts:489; the breaker-fallback guard normalize.ts:500).
- **Byte-identical after every task EXCEPT the D4 re-baseline of TAGGED transfer rows.** Breaker + transformer + relay + GFP + instrument + switch goldens byte-identical; ALL tagless `ATS`/`MTS`/`STS` rows byte-identical (they still fall to the NON_BREAKER tail); ALL `UPS`/`PDU`/... rows byte-identical. The ONLY permitted deltas (D4, enumerated file:line): the TAGGED `ATS`/`MTS`/`STS` disposition assertions + the `E01-11` `STS-*` rows (all tagged), which move into the transfer family's dispositions, PLUS the SKILL.md worked-example narrative.
- **No new catalog refs and no new hours** (D1). V1 uses the existing priced refs ONLY, matched by exact ref STRING, NEVER by section (the priced-seed overload is at firm `7.18`: the `(Functional Testing)` transfer ref AND the DC-Battery/DC-Charger refs all carry firm 7.18).
- **The priced transfer refs (verbatim strings; `ref_hours` is DUAL-PROFILE `{ATS: acceptance, MTS: maintenance}`):** `Automatic Transfer Switch - (IR/DLRO)` `{ATS:3.0, MTS:4.0}`; `Automatic Transfer Switch - Iso Bypass (IR/DLRO)` `{ATS:4.0, MTS:6.0}`; `Manual Transfer Switch - (IR/DLRO)` `{ATS:2.0, MTS:3.0}`. (Present but NOT a V1 ref axis per D6: `Automatic Transfer Switch (Functional Testing)` `{ATS:null, MTS:4.0}` - null in the ACCEPTANCE profile only, 4.0 in maintenance; a test-scope variant of the same device, mis-sectioned 7.18. `Infrared Scan - ATS` is a generic IR add-on line, not a transfer-device ref.)
- **Transfer switches never auto-price** (D2). Every recognized transfer device -> `scope_pending` (candidate ref-GROUP + optional provisional default) or `transfer_catalog_gap`. No "matched" transfer line in V1.
- **Recognition is device-first (transfer anchor) + tag, NEVER a bare "switch"** (D3). Anchor set: `automatic|manual transfer switch`, `transfer switch`, `ATS`, `MTS`, `STS` + a tag, OR `candidateKind:'transfer_switch'`. A TAGLESS transfer-anchored row is NOT claimed (it stays on the NON_BREAKER tail - byte-identical, fail-closed).
- **The routing inversion (D3, load-bearing, REDESIGNED rev-2):** insert `looksLikeTransferSwitch` in `assessCore` BETWEEN `looksLikeSwitch` (normalize.ts:485) and the `NON_BREAKER` catch (normalize.ts:489); AND short-circuit `candidateKind:'transfer_switch'` at the TOP of `assessCore` (a hard producer win, ahead of relay/GFP/switch - fixes the ordering hole where a producer-tagged transfer row containing relay wording would be claimed by `looksLikeRelay`). `NON_BREAKER` and `SWITCH_EXCLUDE` are UNCHANGED. A TAGGED transfer-anchored row is claimed by the transfer route before the tail; a tagless one falls to the tail (unchanged).
- **The H3 conflict guard, guard-first + transfer-LOCAL (D3 + T1-B):** inside `assessTransferSwitch`, `transfer_parent_conflict` (signature null) fires ONLY on a trip-function descriptor (`LSI`/`LSIG`), an unambiguous breaker hint (`MCB|MCCB|ACB|VCB|breaker|draw-out|GB|FB`), or a `TRANSFER_CONFLICT_NONBREAKER` token (`PDU|UPS|SPD|PQM|METER|BUS DUCT` = `NON_BREAKER` MINUS the transfer tokens). A transfer-anchored `AF/AT` - a lone `AF`/`AT` token OR a full `###AF/###AT` PAIR - carrying NONE of those signals is NOT a conflict: it is RATING EVIDENCE (`ampRating`) and builds a transfer signature -> scope_pending (T1-B, operator-ratified 2026-07-06; a real single ATS commonly carries its own frame/withstand rating, and an ATS has no integral trip curve, so `LSIG` is the strong "actually a breaker" discriminator). NEVER a silent transfer line, NEVER suppressing a real breaker, NEVER auto-priced. The transfer-local predicate (not full `NON_BREAKER`) also lets a plain `ATS`/`MTS`/`STS` row NOT self-conflict.
- **Provisional default ONLY when the automation class is legible** (D2): `automatic`/`ATS` -> Automatic ref (+`bypass`/`iso` -> Iso-Bypass ref); `manual`/`MTS` -> Manual ref. A bare `transfer switch` -> candidate group, NO default. Default scope = `(IR/DLRO)` (D6).
- **STS + UPS (D5):** `STS`/`static`/`solid-state` -> recognized transfer evidence but fail-closed to `transfer_catalog_gap` (no priced ref, no NETA section; NEVER mapped onto the ATS refs). `UPS` -> OUT-of-family: it is KEPT in `NON_BREAKER`; a `UPS-*` main carrying a frame/trip is (and stays) `non_breaker_carries_rating` - a question, NOT a priced breaker.
- **Manual-iso-bypass gap (D6 correction):** a MANUAL transfer with bypass-isolation has NO priced ref -> `transfer_catalog_gap`.
- **T1 RATIFIED (operator, 2026-07-06 - Option B amended):** a transfer-anchored `AF/AT` (lone token OR full pair) with no trip-function / breaker-hint / co-located non-breaker token is transfer RATING EVIDENCE -> `scope_pending` (never auto-priced, Gate-2 confirmed). Conflict fires only on `LSI`/`LSIG`, a breaker hint, or a `UPS|PDU|SPD|PQM|METER|BUS DUCT` token. **STS:** clean (incl. `STS` + a bare `AF/AT`) -> `transfer_catalog_gap`; `STS` + `LSIG` or a breaker hint -> `transfer_parent_conflict`. **Main-tie-main:** MAIN/TIE breaker rows (no transfer anchor) stay breakers; a transfer/interlock/MTM note never collapses real breaker rows into one transfer line.
- **Gates (verified on host):** `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (cross-package false-green-trap gate).
- **Cross-engine (Codex) IRP** before merge; merge operator-gated (admin-rebase PR).
- **R1 (estimating authority) PROVISIONAL** (`TRANSFER_R1_RATIFIED=false`): the automation-class -> default-ref table, the parse precedence, the `(IR/DLRO)` default convention, the ATS-vs-MTS hours-profile selection, and the two D1 SME questions are provisional until the SME confirms. Never auto-priced, so fail-closed.

## The V1 Contract

1. **Recognize transfer devices DEVICE-FIRST by a transfer anchor + a tag (never a bare "switch").** Established by `candidateKind:'transfer_switch'` (hard win, short-circuited first) OR a `TRANSFER_DEVICE` anchor + a tag. `bypass`/`iso`/`isolation` is an ATTRIBUTE (sets `bypassIsolation:true`) consumed only with a real anchor.
2. **Claim TAGGED transfer rows before the NON_BREAKER tail; guard the breaker-pair conflict FIRST (transfer-local predicate).** The route sits between `looksLikeSwitch` and the `NON_BREAKER` catch. Inside `assessTransferSwitch` the FIRST test is the H3 conflict guard (breaker signals + `TRANSFER_CONFLICT_NONBREAKER`) -> `transfer_parent_conflict` (signature null); only a clean transfer row builds a signature. `NON_BREAKER` is not edited, so a tagless transfer row falls to the tail unchanged.
3. **Scope-driven; never auto-price.** A recognized transfer device -> `scope_pending`: a candidate ref-GROUP + a Gate-2 scope question, default ONLY where automation class is legible. STS / MV / manual-iso-bypass / no priced home -> `transfer_catalog_gap`.
4. **Quantity is per individual device.** Every transfer ref is `unit_of_issue: each`; one priced unit per tagged transfer device. NO set/each or pole packaging convention.
5. **Voltage optional/contextual.** Voltage does NOT gate; absent voltage -> the transfer disposition + a note, NEVER `missing_voltage`.
6. **All prior family paths untouched (except the D4 TAGGED-transfer re-baseline).** `ApparatusSignature` is a discriminated union on `kind`; a transfer signature can never reach another family's `match*` or a priced line (compiler-enforced). Breaker + transformer + relay + GFP + instrument + switch behavior byte-identical; tagless `ATS`/`MTS`/`STS` + all `UPS`/`PDU` rows byte-identical; the only motion is the TAGGED `ATS`/`MTS`/`STS`/`E01-11-STS` re-baseline.

## Component Design (engine seams, grounded @ main ef83b5d7)

### 1. Extraction (`extraction/types.ts`, `extraction/parse.ts`)
- `extraction/types.ts:15`: widen `candidateKind` to `... | 'transfer_switch'`.
- `extraction/parse.ts:58`: widen the validation guard to accept `'transfer_switch'`; update the expected-string message.

### 2. Signature types (`signature/types.ts`)
- Add:
  ```ts
  export type TransferAutomationClass = 'automatic' | 'manual' | 'static' | 'unknown'
  export interface TransferSwitchSignature extends BaseSignature {
    kind: 'transfer_switch'
    automationClass: TransferAutomationClass
    bypassIsolation?: boolean   // 'iso'/'bypass'/'isolation-bypass' present; picks the Iso-Bypass ref
    ampRating?: number          // evidence/display only (continuous A; NOT a frame/trip pair)
  }
  ```
  `automationClass` is the SINGLE match discriminator. `static` -> `transfer_catalog_gap` (D5). `bypassIsolation` is a match AXIS (H5).
- `signature/types.ts:91`: `export type ApparatusSignature = ... | SwitchSignature | TransferSwitchSignature`.

### 3. Recognition + parse (`signature/normalize.ts`) - NON_BREAKER UNCHANGED
- **`NON_BREAKER` (normalize.ts:8) is UNCHANGED** (`/\b(PDU|UPS|STS|ATS|MTS|SPD|PQM|METER|BUS\s*DUCT)\b/i`). `SWITCH_EXCLUDE` (normalize.ts:25) UNCHANGED. No existing token regex is edited - this is what keeps GFP/transformer/tagless/switch-guard byte-identical.
- New token regexes (ASCII):
  - `TRANSFER_DEVICE`: `/\b(automatic\s+transfer\s+switch|manual\s+transfer\s+switch|transfer\s+switch|ATS|MTS|STS)\b/i`.
  - `TRANSFER_CONFLICT_NONBREAKER` (NON_BREAKER MINUS the transfer tokens - used ONLY inside the transfer H3 guard so a transfer row does not self-conflict): `/\b(PDU|UPS|SPD|PQM|METER|BUS\s*DUCT)\b/i`.
  - `TRANSFER_BYPASS` (attribute; consumed only with an anchor): `/\b(iso(lation)?[\s-]?bypass|bypass[\s-]?iso(lation)?|\biso\b|\bbypass\b)\b/i`.
  - `TRANSFER_FRAME_TRIP` (single numbered frame/trip token; reuse the switch `SWITCH_FRAME_TRIP` shape): `/\b\d{2,6}\s*A[FT]\b/i`.
  - `TRANSFER_TRIP_FN` (trip-function descriptor; reuse `SWITCH_TRIP_FN`): `/\bL(?=[SIGE]{2})(S?)(I?)(G?)(E?)\b/i`.
  - `TRANSFER_BREAKER_CONFLICT` (the unambiguous breaker subset): `/\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|GB|FB)\b/i`.
  - `TRANSFER_AMP` (evidence only): a plain continuous amp `/(?<!\d)(\d{2,6})\s*A\b/i`, OR - for a recognized (non-conflicted) transfer row - the frame value from a `###AF/###AT` token. `ampRating` is display/evidence only (NOT in `specKey`), so capturing the frame amps as the rating is safe (T1-B).
- `looksLikeTransferSwitch(x)`:
  ```ts
  function looksLikeTransferSwitch(x: ExtractedApparatus): boolean {
    if (x.candidateKind === 'transfer_switch') return true
    if (x.candidateKind !== undefined && x.candidateKind !== 'transfer_switch') return false
    return TRANSFER_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0
  }
  ```
- `parseAutomationClass(raw): TransferAutomationClass`: `automatic transfer switch`/`\bATS\b` -> `'automatic'`; `manual transfer switch`/`\bMTS\b` -> `'manual'`; `static|solid[\s-]?state|\bSTS\b` -> `'static'`; else (bare `transfer switch`) -> `'unknown'`.
- `parseBypassIsolation(raw)`, `parseAmpRating(raw)` - text-only, evidence.
- `assessTransferSwitch(x, voltageBasis?)` - H3 CONFLICT GUARD FIRST (T1-B):
  - `if (TRANSFER_TRIP_FN.test(x.raw) || TRANSFER_BREAKER_CONFLICT.test(x.raw) || TRANSFER_CONFLICT_NONBREAKER.test(x.raw))` -> `transfer_parent_conflict`, signature null. (A trip-function, a breaker hint, or a co-located non-transfer non-breaker token. `FRAME_TRIP` / `TRANSFER_FRAME_TRIP` are DELIBERATELY NOT conflict signals - a bare `AF/AT` on a transfer-anchored row is the ATS's own rating, T1-B. Uses `TRANSFER_CONFLICT_NONBREAKER`, NOT full `NON_BREAKER`, so a plain `ATS`/`MTS`/`STS` does not self-conflict. Emit a message distinguishing the trip/hint case from the co-located-non-breaker case.)
  - else build the signature: `automationClass`, `bypassIsolation`, `ampRating = parseAmpRating(x.raw)` (plain amps OR the `###AF/###AT` frame value, as evidence), `voltageClass` (may be undefined - NOT gated). `assessmentCode:'transfer_recognized'`. A `static` automationClass still routes to `matchTransferSwitch` -> null -> `transfer_catalog_gap` (so a clean STS or an STS + bare `AF/AT` is a gap; an STS + `LSIG`/hint hits the guard above).
- `assessCore`: (i) at the TOP, `if (x.candidateKind === 'transfer_switch') return assessTransferSwitch(x, voltageBasis)` (hard producer win). (ii) insert `if (looksLikeTransferSwitch(x)) return assessTransferSwitch(x, voltageBasis)` AFTER the `looksLikeSwitch` block (normalize.ts:485) and BEFORE the `NON_BREAKER` catch (normalize.ts:489). New order: `[candidateKind:transfer_switch] -> instrument -> transformer -> GFP -> relay -> switch -> TRANSFER(text-anchored) -> NON_BREAKER tail -> breaker`.
- New `AssessmentCode` members (normalize.ts:388-394): `transfer_recognized`, `transfer_parent_conflict`.
- **Explicit NON-edits (why the prior families stay byte-identical):** `isGfpParentShape` (normalize.ts:231) still sees `ATS`/`MTS`/`STS` via the unchanged `NON_BREAKER`, so a transfer-token GFP row stays parent-excluded (an `ATS ... GROUND FAULT` row still does NOT become a GFP device); `looksLikeTransformer`'s kVA-fallback (normalize.ts:106) still excludes `ATS`+kVA rows via `!NON_BREAKER.test`; the NON_BREAKER tail (normalize.ts:489) still catches TAGLESS `ATS`/`MTS`/`STS`; the breaker-fallback guard (normalize.ts:500) is unaffected. A TAGGED transfer row reaches the transfer route (inserted before the tail) and is claimed there; these earlier guards defer because their `NON_BREAKER`-based exclusions still hold.

### 4. Match (`catalog/transfer-switch-map.ts` + `.data.ts`)
- `.data.ts`: the 3 V1 refs VERBATIM; `TRANSFER_GROUPS` keyed by `automationClass`; `TRANSFER_R1_RATIFIED = false`:
  ```
  'automatic' -> ['Automatic Transfer Switch - (IR/DLRO)', 'Automatic Transfer Switch - Iso Bypass (IR/DLRO)']
  'manual'    -> ['Manual Transfer Switch - (IR/DLRO)']
  'unknown'   -> ['Automatic Transfer Switch - (IR/DLRO)', 'Manual Transfer Switch - (IR/DLRO)']
  // ABSENT (deliberate gaps): 'static'; manual+bypassIsolation; MV transfer
  ```
- `.ts`: `matchTransferSwitch(sig): TransferScopeMatch | null`:
  - **Static gap (D5, FIRST):** `if (sig.automationClass === 'static') return null`.
  - **Manual-iso-bypass gap (D6):** `if (sig.automationClass === 'manual' && sig.bypassIsolation === true) return null`.
  - resolve the group by `automationClass`; missing/empty -> `null`.
  - `defaultRef`: `automatic` -> Iso-Bypass ref when `bypassIsolation === true`, else base; `manual` -> Manual ref; `unknown` -> NO default. Never route to `(Functional Testing)` in V1 (D6).
  - Match by exact ref STRING (7.18 overload guard).

### 5. Quantify (`quantify/quantify.ts`)
- `s.kind === 'transfer_switch'` branch in `specKey` BEFORE the transformer fall-through: `[s.kind, s.automationClass, s.bypassIsolation ? 'BYP' : '-', s.voltageClass ?? '-', s.source.block ?? '-'].join('|')`. `deviceId` kind-prefixes (`transfer_switch:TAG`).
- `pickAuthoritative`: a `richTransfer = auths.find((o) => o.kind === 'transfer_switch' && (o.automationClass !== 'unknown' || o.bypassIsolation !== undefined))` preference (mirrors switch/relay) so a sparse same-tag occurrence cannot erase the automation-class/bypass evidence.

### 6. Disposition + contract (`buckets/types.ts`, `emit/emit.ts`, `runner/report.ts`)
- `buckets/types.ts`: `OperatorQuestionCode` += `transfer_scope_pending` | `transfer_catalog_gap` | `transfer_parent_conflict`; `DispositionReasonCode` += same three; `TakeoffFinding.code` += `transfer_catalog_gap`. Add optional `automationClass?: string` + `bypassIsolation?: boolean` to `ScopePendingLine` + `ApparatusDisposition`.
- `emit/emit.ts`: `sig.kind === 'transfer_switch'` branch BEFORE the transformer fall-through (with `continue`): scope match -> `scope_pending` (candidateRefs=group, provisionalDefaultRef, r1Ratified=TRANSFER_R1_RATIFIED, automationClass, bypassIsolation, scopeQuestion) + stamp evidence on each member; `null` match -> `transfer_catalog_gap` finding + `unmatched` disposition + question. Update `ASSESS_TO_REASON`: `transfer_recognized -> transfer_scope_pending`, `transfer_parent_conflict -> transfer_parent_conflict`.
- `runner/report.ts`: `scopePending` projection gains `automationClass` + `bypassIsolation`; printed on the Gate-2 block.

## The crux, expanded - the must-pin cases

1. **`Automatic Transfer Switch` (spelled) / `ATS-1` (TAGGED) -> transfer `scope_pending` (automatic, default IR/DLRO), NOT the NON_BREAKER tail.** Claimed by the transfer route before the tail (NON_BREAKER unedited).
2. **`MTS-2` (tagged) -> transfer scope_pending (manual, default Manual ref).**
3. **H3 main-tie-main: two `###AF/###AT` breakers (labeled MAIN/TIE, NO transfer anchor) -> both stay BREAKERS (priced); a transfer/interlock/MTM note never collapses them into one transfer line. A single transfer-anchored row carrying a bare `AF/AT` (no LSIG/hint) -> transfer `scope_pending` (rating evidence, T1-B); the same row with `LSIG` or a breaker hint -> `transfer_parent_conflict` (null signature), breaker NOT suppressed.**
4. **`STS-1` clean AND `STS-1 800AF/800AT` (bare `AF/AT`, no LSIG) -> `transfer_catalog_gap`; `STS-1 800AF/800AT LSIG` (LSIG present) -> `transfer_parent_conflict`.** STS never maps to an ATS ref (D5).
5. **A `UPS-*-MIB 1600AF/1600AT` main -> stays `non_breaker_carries_rating` (a QUESTION, unchanged), NOT a priced breaker (the NON_BREAKER tail runs before the breaker fallback); a bare `UPS` main -> `non_breaker_excluded`, unchanged.** UPS is not a transfer anchor -> `looksLikeTransferSwitch` false -> not claimed.
6. **`Automatic Transfer Switch - Iso Bypass` / `ATS ... bypass` -> automatic group, default `... Iso Bypass (IR/DLRO)`, ONE device (H5).**
7. **Bare `transfer switch` (no automation word) -> automation `unknown`, group `[auto base, manual base]`, NO default (D2).**
8. **`MTS ... bypass` -> `transfer_catalog_gap` (no manual-iso-bypass ref; D6).**
9. **TAGLESS `ATS 800AF/800AT` (no tag) -> UNCHANGED `non_breaker_carries_rating` (falls to the NON_BREAKER tail; not claimed by the tagged-only transfer route).** This is why NON_BREAKER is left intact.
10. **Cross-family byte-identical: `ATS-1 500kVA` (tagged, no frame/trip) -> transfer scope_pending, NOT transformer (the transformer kVA-fallback still excludes it via `!NON_BREAKER.test`); `ATS-1 ... GROUND FAULT PROTECTION` (tagged, candidateKind:'gfp') -> still GFP-parent-excluded, then claimed by transfer, NOT a priced GFP line.**
11. **Exact-ref + 7.18 overload proof:** the 3 V1 refs resolve verbatim in the live seed; assert the `(Functional Testing)` transfer ref AND the DC-Battery/DC-Charger refs all carry firm `7.18`, so matching keys on the STRING. (The 7.22 "shared with generator/UPS" is an SSoT `records.neta_procedures` fact, NOT a priced-seed fact - the priced seed has generator at 7.13 and no UPS ref - so it is NOT used as a seed-level overload proof.)

## R1 (estimating authority) - provisional

`TRANSFER_R1_RATIFIED = false`. R1 = (a) the automation-class -> default-ref table; (b) `parseAutomationClass` precedence; (c) the `(IR/DLRO)` default-scope convention (never `(Functional Testing)` in V1); (d) the ATS-vs-MTS `ref_hours` PROFILE selection (each transfer ref exposes distinct acceptance/maintenance hours; the Gate-2/compile step must choose the profile - a selection axis to ratify); (e) the two D1 SME questions - **is `Automatic Transfer Switch (Functional Testing)` at firm 7.18 with a null ACCEPTANCE-profile hour (4.0 maintenance) a data bug (should be 7.22.3) or a maintenance-only convention?** and **are STS, MV transfer, and manual-iso-bypass true catalog gaps?**. (T1 is RATIFIED 2026-07-06 - a bare `AF/AT` is transfer rating evidence, not a conflict; folded into the H3 guard, no longer an R1 open item.) Surfaced as `r1Ratified:false`; never auto-priced.

## Testing (TDD; operator must-pin tests in bold)

- **#1 (route) `ATS-1` (tagged) -> transfer `scope_pending` (automatic, default IR/DLRO).** `Automatic Transfer Switch` spelled -> transfer family.
- **#2 `MTS-2` -> transfer scope_pending (manual, default Manual ref).**
- **#3 (H3 + T1-B) two MAIN/TIE `###AF/###AT` breakers (no transfer anchor) -> both stay BREAKERS; `ATS-1 800AF/800AT` (bare `AF/AT`, NO LSIG/hint) -> transfer `scope_pending` (rating evidence); `ATS-1 800AF/800AT LSIG` -> `transfer_parent_conflict` (null signature), breaker NOT suppressed. Breaker golden byte-identical.**
- **#4 (D5 + T1-B) `STS-1` clean AND `STS-1 800AF/800AT` (bare `AF/AT`, no LSIG) -> `transfer_catalog_gap`; `STS-1 800AF/800AT LSIG` -> `transfer_parent_conflict`; never an ATS ref.**
- **#5 (Codex-corrected) a `UPS-*-MIB 1600AF/1600AT` main -> `non_breaker_carries_rating` (QUESTION, unchanged), NOT a priced breaker; a bare `UPS` main -> `non_breaker_excluded`, unchanged.**
- **#6 (H5) `ATS ... bypass` -> automatic group, default Iso-Bypass ref, ONE device.**
- **#7 (D2) bare `transfer switch` -> automation `unknown`, group `[auto base, manual base]`, NO default.**
- **#8 (D6) `MTS ... bypass` -> `transfer_catalog_gap`.**
- **#9 (TAGLESS byte-identical) `ATS 800AF/800AT` (NO tag) -> `non_breaker_carries_rating`, UNCHANGED; `STS 800AF/800AT` (no tag) -> unchanged. Proves NON_BREAKER intact + the tagged-only route.**
- **#10 (cross-family byte-identical - the rev-2 regression guards) `ATS-1 500kVA` (tagged) -> transfer scope_pending, NOT transformer_recognized/missing_voltage; a tagged `ATS-1 ... GROUND FAULT PROTECTION` with candidateKind:'gfp' -> NOT a priced GFP line (still parent-excluded, then transfer). The transformer AND GFP goldens byte-identical.**
- **#11 (exact-ref + 7.18 overload) the 3 V1 refs resolve verbatim; the `(Functional Testing)` + DC-Battery + DC-Charger refs all sit at firm 7.18 -> match by STRING. (Do NOT assert a 7.22 generator/UPS priced-seed overload - it does not exist in the seed.)**
- **#12 Voltage:** absent voltage -> transfer disposition + note, NOT `missing_voltage`.
- **#13 Cross-family + compiler:** a transfer signature can never reach another family's `match*`; the union widening forces the `kind:'transfer_switch'` emit branch.
- **#14 (producer hard-win) `candidateKind:'transfer_switch'` on a raw ALSO containing a relay device noun -> transfer family (the top-of-assessCore short-circuit beats `looksLikeRelay`).**
- **#15 ASSESS_TO_REASON:** `transfer_recognized -> transfer_scope_pending`, `transfer_parent_conflict -> transfer_parent_conflict`.
- **#16 Runner:** a transfer-only extraction -> `partial_preview`; scope_pending carried with `automationClass`/`bypassIsolation`.
- **#17 (D4 re-baseline - NON-VACUOUS) the TIGHTENED assertions: `MTS-2 800AF/800AT LSIG` and `STS-1 800AF/800AT LSIG` (normalize.test.ts:88-92,116-120) now assert `assessmentCode === 'transfer_parent_conflict'` (NOT merely signature-null + questions>0 - which would false-green a build that skipped the route); `ATS 800AF/800AT LSIG` tagged (dispositions.test.ts:51-57) asserts reasonCode `transfer_parent_conflict`. `E01-11` re-baselined: the 8 tagged `STS-*` rows move `non_breaker_carries_rating -> transfer_parent_conflict`; the 5 `UPS-*` mains + every non-transfer row byte-identical; `bid_cents 198000` / `39 operator_questions` / `0 findings` UNCHANGED (STS rows stay unpriced questions). Documented before/after committed.**
- **#18 (D4 doc) SKILL.md worked-example (line 104) updated: split the STS rows (now `transfer_parent_conflict`) from the UPS rows (still `non_breaker_carries_rating`); re-verify the 39-questions / 198000-bid / 0-findings figures hold verbatim.**
- **#19 BREAKER AND TRANSFORMER AND RELAY AND GFP AND INSTRUMENT AND SWITCH goldens byte-identical; tagless ATS/MTS/STS + all UPS/PDU rows byte-identical** (the ONLY permitted motion is the tagged `ATS`/`MTS`/`STS` disposition assertions + the `E01-11` tagged STS rows).
- **#20 (T1 RATIFIED 2026-07-06 - Option B amended):** `ATS-1 800AF/800AT` (bare `AF/AT` pair, no LSIG/hint) -> transfer `scope_pending` (automatic, rating evidence); `ATS-1 800A` (plain amp) -> scope_pending; `ATS-1 800AF/800AT LSIG` -> `transfer_parent_conflict`; `ATS-1 ... VCB` -> conflict; `ATS-1 ... UPS` (co-located non-breaker) -> conflict. A bare `AF/AT` NEVER auto-prices (scope_pending, Gate-2 confirmed).

## Out of scope (V2)

MV transfer switches (catalog_gap in V1); a manual-iso-bypass ref (catalog_gap until the SME authors it); the `(Functional Testing)` scope as a distinct priced line; pole-count / switched-neutral and transition-type as price axes; contactor-vs-breaker construction; a standalone STS ref; a UPS (7.22.2) family; the ATS-vs-MTS hours-profile auto-selection; the Gate-2 resolution UI; producer `candidateKind`-supplied evidence beyond text.
