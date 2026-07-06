# Estimator-Takeoff Automatic / Transfer Switch Family (V1) - Design

Status: SPEC Rev 1.0 (operator-ratified packet 006 D1-D6, 2026-07-05, all as-leaned; D6 grounding correction folded - the 2x2 "manual iso-bypass" cell has NO priced ref, so it fails closed to `transfer_catalog_gap`). Date: 2026-07-05.
Lane: estimator-takeoff/transfer-switch-family-admission (off main ef83b5d7). Dev-only; merge operator-gated.
Packet: docs/superpowers/packets/estimator-takeoff-family-transfer-switches.md (Part 6 decisions + Part 9 ratification).
Predecessors (reused; must stay byte-identical EXCEPT the intentional re-baseline below): breaker engine + transformer (PR #49) + relay (PR #50) + GFP (PR #51) + instrument-transformer (PR #52) + switch (PR #53/#54).

**Goal:** Admit the AUTOMATIC / TRANSFER SWITCH family (NETA **7.22.3**) into `packages/estimator-takeoff` as a bounded V1 slice - the 7th apparatus family - so a recognized transfer switch is counted per device and routed to a Gate-2 automation-class scope decision (never auto-priced), a main-tie-main breaker-pair SCHEME keeps its breakers as breakers, and all prior families stay BYTE-IDENTICAL except the intentional, documented `E01-11` re-baseline (D4).

**Architecture:** Reuse the switch/transformer/relay `scope_pending` machinery (discriminated-union signature, `scope_pending` + optional `provisionalDefaultRef`, `candidateKind`, kind-prefixed `deviceId`, cross-family conflict guards). Add a seventh signature `kind:'transfer_switch'`. UNLIKE the six prior families (purely additive), this family is NON-ADDITIVE: `ATS`/`MTS`/`STS` are currently swallowed by `NON_BREAKER` (normalize.ts:8) and the spelled-out `transfer switch` is excluded by the switch family (normalize.ts:25). So this slice performs a ROUTING INVERSION - it REMOVES `ATS`/`MTS`/`STS` from `NON_BREAKER`, routes a device-first transfer recognizer BEFORE the `NON_BREAKER` tail, and CLAIMS the spelled-out `transfer switch` - while the recognizer's FIRST action is a breaker-pair conflict guard so a main-tie-main scheme is never collapsed into one silent transfer line.

**Tech stack:** TypeScript, Vitest, pnpm workspace; host build over `ssh olares-mesh`.

## Global Constraints

- **ASCII-only** in all authored code/comments AND engine-emitted strings (no em-dashes). Verbatim source DATA may be UTF-8.
- **Canonical NETA section = `7.22.3`** (Automatic Transfer Switches, under 7.22 Emergency Systems). The packet's "7.16" (Motor Control) and the switch packet's loose "7.18/7.22" (7.18 = DC Systems) are RECORDED mislabels; nothing keys on them.
- **Byte-identical after every task EXCEPT the intentional D4 re-baseline.** Breaker + transformer + relay + GFP + instrument + switch goldens byte-identical, AND every NON-transfer row of `E01-11` byte-identical. The ONLY permitted deltas: the `ATS`/`MTS`/`STS` disposition assertions in the shared `normalize`/`dispositions`/`runner-reconciliation` tests + the `E01-11` `STS-*` rows, which move out of `non_breaker_excluded`/`non_breaker_carries_rating` into the transfer family's dispositions (documented before/after; D4).
- **No new catalog refs and no new hours** (D1). V1 uses the existing priced refs ONLY, matched by exact ref STRING, NEVER by section (a DOUBLE overload: firm `7.22` is shared with generator/UPS in the SSoT, and firm `7.18` is shared with the DC-Battery/Charger refs).
- **The priced transfer refs (verbatim from the live seed, exact strings):** `Automatic Transfer Switch - (IR/DLRO)`; `Automatic Transfer Switch - Iso Bypass (IR/DLRO)`; `Manual Transfer Switch - (IR/DLRO)`. (Also present but NOT a V1 ref axis per D6: `Automatic Transfer Switch (Functional Testing)` - a test-scope variant of the same device, mis-sectioned 7.18 with null acceptance hours; the IR/DLRO scope is the V1 default. `Infrared Scan - ATS` is a generic IR add-on line, not a transfer-device ref.)
- **Transfer switches never auto-price** (D2). Every recognized transfer device -> `scope_pending` (candidate ref-GROUP + optional provisional default) or `transfer_catalog_gap`. No "matched" transfer line in V1.
- **Recognition is device-first (transfer anchor), NEVER a bare "switch"** (D3). The anchor set is transfer-device nouns/abbreviations (`automatic|manual transfer switch`, `transfer switch`, `ATS`, `MTS`, `STS`) + a tag, OR `candidateKind:'transfer_switch'`.
- **The routing inversion (D3, load-bearing):** REMOVE `ATS`/`MTS`/`STS` from `NON_BREAKER` (normalize.ts:8) - KEEP `UPS`/`PDU`/`SPD`/`PQM`/`METER`/`BUS DUCT`. Route `looksLikeTransferSwitch` in `assessCore` BETWEEN `looksLikeSwitch` (normalize.ts:485) and the `NON_BREAKER` catch (normalize.ts:489). The removal is MANDATORY (not cosmetic): the transfer conflict guard uses `NON_BREAKER.test()`, so leaving ATS/MTS/STS in `NON_BREAKER` would make every transfer row self-conflict. `SWITCH_EXCLUDE` (normalize.ts:25) is UNCHANGED - it still excludes `transfer switch` from the switch family; the new recognizer claims those rows because it routes right after `looksLikeSwitch` returns false on them.
- **The H3 breaker-pair conflict guard, guard-first (D3):** a transfer-anchored row carrying `FRAME_TRIP` (`###AF/###AT`), a single `###AF|###AT` token, a trip-function descriptor (LSIG), an unambiguous breaker hint (`MCB|MCCB|ACB|VCB|breaker|draw-out|GB|FB`), or a residual `NON_BREAKER` token (`UPS`/`PDU`/...) -> a `transfer_parent_conflict` question (signature null), NEVER a silent transfer line and NEVER suppressing a real breaker. This is the main-tie-main protection (two interlocked frame/trip breakers stay two priced breakers).
- **Provisional default ONLY when the automation class is legible** (D2): `automatic`/`ATS` -> Automatic ref (+`bypass`/`iso` -> Iso-Bypass ref); `manual`/`MTS` -> Manual ref. A bare `transfer switch` (automation class illegible) -> candidate group, NO default. Default scope = `(IR/DLRO)` (D6).
- **STS + UPS (D5):** `STS`/`static`/`solid-state` -> recognized transfer evidence but fail-closed to `transfer_catalog_gap` (no priced ref, no NETA section; NEVER mapped onto the contactor/breaker ATS refs). `UPS` -> OUT-of-family: stays in `NON_BREAKER`; a `UPS-*` breaker main stays a breaker where it is a breaker row.
- **Manual-iso-bypass gap (D6 correction):** a MANUAL transfer with bypass-isolation has NO priced ref -> `transfer_catalog_gap` (surfaced, never fabricated; an SME "author it?" item).
- **Gates (verified on host):** `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (cross-package false-green-trap gate).
- **Cross-engine (Codex) IRP** before merge; merge operator-gated (admin-rebase PR).
- **R1 (estimating authority) PROVISIONAL** (`TRANSFER_R1_RATIFIED=false`): the automation-class -> default-ref table, the parse precedence, the IR/DLRO-default convention, the two D1 SME questions (the 7.18/null-hours `(Functional Testing)` anomaly; STS + MV + manual-iso-bypass as true gaps) are provisional until the SME confirms. Never auto-priced, so provisional is fail-closed.

## The V1 Contract

1. **Recognize transfer devices DEVICE-FIRST by a transfer anchor (never a bare "switch").** Established by a producer `candidateKind:'transfer_switch'` OR a `TRANSFER_DEVICE` anchor + a tag. The anchor set: `automatic transfer switch`, `manual transfer switch`, `transfer switch`, `ATS`, `MTS`, `STS`. `bypass`/`iso`/`isolation` is an ATTRIBUTE (sets `bypassIsolation:true`) consumed only with a real anchor - never a standalone anchor.
2. **Claim before the NON_BREAKER tail; guard the breaker-pair conflict FIRST.** The route sits between `looksLikeSwitch` and the `NON_BREAKER` catch. Inside `assessTransferSwitch` the FIRST test is the H3 conflict guard (breaker-pair / frame-trip / residual non-breaker) -> `transfer_parent_conflict` (signature null); only a clean transfer row builds a signature.
3. **Scope-driven; never auto-price.** A recognized transfer device -> `scope_pending`: a candidate ref-GROUP (by automation class) + a Gate-2 scope question, with a PROVISIONAL default ONLY where the automation class is legible, NO default otherwise. STS / MV / manual-iso-bypass / no priced home -> `transfer_catalog_gap`.
4. **Quantity is per individual device.** Every transfer ref is `unit_of_issue: each`; one priced unit per tagged transfer device. NO set/each or pole packaging convention (a 4-pole ATS is ONE device).
5. **Voltage optional/contextual.** Voltage does NOT gate (all refs are LV/service-shaped); absent voltage -> the transfer disposition + a note, NEVER `missing_voltage`.
6. **All prior family paths untouched (except the D4 re-baseline).** `ApparatusSignature` is a discriminated union on `kind`; a transfer signature can never reach any `match*` of another family or a priced line (compiler-enforced). Breaker + transformer + relay + GFP + instrument + switch behavior byte-identical; the only motion is the intentional `ATS`/`MTS`/`STS`/`E01-11` re-baseline.

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
    // voltageClass stays optional (inherited): contextual; never gates.
  }
  ```
  `automationClass` is the SINGLE match discriminator. `static` is recognized but has NO priced home -> `transfer_catalog_gap` (D5). `bypassIsolation` is a match AXIS (pick the Iso-Bypass ref), not a second device (H5).
- `signature/types.ts:91`: `export type ApparatusSignature = ... | SwitchSignature | TransferSwitchSignature`.

### 3. Recognition + parse (`signature/normalize.ts`)
- **The inversion (normalize.ts:8):** `const NON_BREAKER = /\b(PDU|UPS|SPD|PQM|METER|BUS\s*DUCT)\b/i` (ATS/MTS/STS REMOVED; UPS/PDU/SPD/PQM/METER/BUS DUCT KEPT). `SWITCH_EXCLUDE` (normalize.ts:25) UNCHANGED.
- Token regexes (ASCII):
  - `TRANSFER_DEVICE` (transfer-device anchors): `/\b(automatic\s+transfer\s+switch|manual\s+transfer\s+switch|transfer\s+switch|ATS|MTS|STS)\b/i`.
  - `TRANSFER_BYPASS` (the bypass-isolation attribute - consumed only with an anchor): `/\b(iso(lation)?[\s-]?bypass|bypass[\s-]?iso(lation)?|bypass\s+isolation|\biso\b|\bbypass\b)\b/i`.
  - `TRANSFER_BREAKER_CONFLICT` (the unambiguous breaker subset, mirrors the switch guard; deliberately NOT the shared `vacuum`/`SF6`/`air frame`): `/\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|GB|FB)\b/i`.
  - `TRANSFER_FRAME_TRIP` (a single numbered frame/trip token): `/\b\d{2,6}\s*A[FT]\b/i` (reuse the switch `SWITCH_FRAME_TRIP` shape).
  - `TRANSFER_TRIP_FN` (a breaker trip-function descriptor on a transfer row = conflict): `/\bL(?=[SIGE]{2})(S?)(I?)(G?)(E?)\b/i` (reuse the switch `SWITCH_TRIP_FN` shape; the 2-letter lookahead avoids tag-prefix false positives).
  - `TRANSFER_AMP` (PLAIN continuous amps ONLY; `\bA\b` boundary so `800AF`/`800AT` never become amp evidence): `/(?<!\d)(\d{2,6})\s*A\b/i` - evidence only.
- `looksLikeTransferSwitch(x)`:
  ```ts
  function looksLikeTransferSwitch(x: ExtractedApparatus): boolean {
    if (x.candidateKind === 'transfer_switch') return true            // explicit producer signal wins
    if (x.candidateKind !== undefined && x.candidateKind !== 'transfer_switch') return false
    return TRANSFER_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0
  }
  ```
  (Like `looksLikeSwitch`/`looksLikeInstrumentTransformer`, the H3 conflict guard is NOT in `looksLikeTransferSwitch`; a conflicted row ENTERS the transfer route and is flagged inside `assessTransferSwitch`.)
- `parseAutomationClass(raw): TransferAutomationClass` - text-only, fail-closed:
  ```
  automatic transfer switch / \bATS\b       -> 'automatic'
  manual transfer switch    / \bMTS\b       -> 'manual'
  static / solid[\s-]?state / \bSTS\b        -> 'static'
  else (bare "transfer switch")             -> 'unknown'
  ```
- `parseBypassIsolation(raw): boolean | undefined`: `TRANSFER_BYPASS` -> `true`; else `undefined`.
- `parseAmpRating(raw): number | undefined`: continuous A (evidence only).
- `assessTransferSwitch(x, voltageBasis?): ApparatusAssessment` - H3 CONFLICT GUARD FIRST (transfer routes before the breaker fallback, so a misrouted breaker-pair must surface a question, never a silent transfer line):
  - `if (TRANSFER_BREAKER_CONFLICT.test(x.raw) || FRAME_TRIP.test(x.raw) || TRANSFER_FRAME_TRIP.test(x.raw) || TRANSFER_TRIP_FN.test(x.raw) || NON_BREAKER.test(x.raw))` -> `transfer_parent_conflict` question, signature null. (Covers a transfer-anchored row carrying a full `AF/AT` pair, a single `800AF`/`800AT`, a trip-function-only `LSIG`, a `VCB`/`ACB`/`breaker`, or a residual `UPS`/`PDU` token. This is the main-tie-main protection.)
  - else build the signature: `automationClass = parseAutomationClass(x.raw)`, `bypassIsolation = parseBypassIsolation(x.raw)`, `ampRating = parseAmpRating(x.raw)`, `voltageClass = classifyVoltage(x.busVoltageV)` (MAY be undefined - NOT gated). `assessmentCode:'transfer_recognized'`.
- `assessCore` order: insert the transfer route AFTER the `looksLikeSwitch` block (normalize.ts:485) and BEFORE the `NON_BREAKER` block (normalize.ts:489): `if (looksLikeTransferSwitch(x)) return assessTransferSwitch(x, voltageBasis)`. New order: instrument -> transformer -> GFP -> relay -> switch -> **TRANSFER** -> NON_BREAKER -> breaker.
- New `AssessmentCode` members (normalize.ts:388-394): `transfer_recognized`, `transfer_parent_conflict`.

### 4. Match (`catalog/transfer-switch-map.ts` + `.data.ts`)
- `.data.ts`: the 3 V1 refs VERBATIM (exact strings); `TRANSFER_GROUPS` keyed by `automationClass`; `TRANSFER_R1_RATIFIED = false`. Provisional R1 table:
  ```
  'automatic' -> ['Automatic Transfer Switch - (IR/DLRO)', 'Automatic Transfer Switch - Iso Bypass (IR/DLRO)']
  'manual'    -> ['Manual Transfer Switch - (IR/DLRO)']
  'unknown'   -> ['Automatic Transfer Switch - (IR/DLRO)', 'Manual Transfer Switch - (IR/DLRO)']
  // ABSENT (deliberate gaps): 'static' (no ref, no section); manual + bypassIsolation (no manual-iso-bypass ref); MV transfer (no MV ref)
  ```
- `.ts`: `interface TransferScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }`; `matchTransferSwitch(sig): TransferScopeMatch | null`:
  - **Static gap (D5, FIRST):** `if (sig.automationClass === 'static') return null` (-> `transfer_catalog_gap`; never mapped to the ATS refs).
  - **Manual-iso-bypass gap (D6, next):** `if (sig.automationClass === 'manual' && sig.bypassIsolation === true) return null` (-> gap; no priced manual-iso-bypass ref).
  - resolve the group by `automationClass` (`automatic`|`manual`|`unknown`); missing/empty -> `null`.
  - `defaultRef`: `automatic` -> `Automatic Transfer Switch - Iso Bypass (IR/DLRO)` when `bypassIsolation === true`, else `Automatic Transfer Switch - (IR/DLRO)`; `manual` -> `Manual Transfer Switch - (IR/DLRO)`; `unknown` -> NO default (D2). Never route to the `(Functional Testing)` ref in V1 (D6).
  - return `{ group: [...group], defaultRef, scopeQuestion: SCOPE_Q }`. Match by exact ref STRING (dual 7.22/7.18 overload guard).

### 5. Quantify (`quantify/quantify.ts`)
- Add an `s.kind === 'transfer_switch'` branch to `specKey` BEFORE the transformer fall-through: `[s.kind, s.automationClass, s.bypassIsolation ? 'BYP' : '-', s.voltageClass ?? '-', s.source.block ?? '-'].join('|')`. (`ampRating` is evidence, not in the key.) `deviceId` kind-prefixes (`transfer_switch:TAG`), so transfer rows never cross-bucket.
- `pickAuthoritative`: add a `richTransfer = auths.find((o) => o.kind === 'transfer_switch' && (o.automationClass !== 'unknown' || o.bypassIsolation !== undefined))` preference (mirrors the switch/relay evidence preference) so a sparse same-tag one-line occurrence cannot erase the automation-class/bypass evidence that drives the default-ref and the gap proofs.

### 6. Disposition + contract (`buckets/types.ts`, `emit/emit.ts`, `runner/report.ts`)
- `buckets/types.ts`: `OperatorQuestionCode` += `transfer_scope_pending` | `transfer_catalog_gap` | `transfer_parent_conflict`; `DispositionReasonCode` += same three; `TakeoffFinding.code` += `transfer_catalog_gap` (only the catalog_gap is a finding; the parent-conflict is a question/disposition code). Add optional contract evidence fields to `ScopePendingLine` + `ApparatusDisposition`: `automationClass?: string` + `bypassIsolation?: boolean`.
- `emit/emit.ts`: import `matchTransferSwitch` + `TRANSFER_R1_RATIFIED` + the `TransferSwitchSignature` type. Add the `sig.kind === 'transfer_switch'` branch in the match loop BEFORE the transformer fall-through (with `continue`): a scope match -> `scope_pending` (candidateRefs=group, provisionalDefaultRef=defaultRef [may be undefined], r1Ratified=TRANSFER_R1_RATIFIED, automationClass=sig.automationClass, bypassIsolation=sig.bypassIsolation, scopeQuestion), + stamp the evidence on each member disposition; a `null` match -> `transfer_catalog_gap` finding (severity warning) + `unmatched` disposition + question. Update `ASSESS_TO_REASON`: `transfer_recognized -> transfer_scope_pending` (unreachable; exhaustiveness), `transfer_parent_conflict -> transfer_parent_conflict`.
- `runner/report.ts`: the `scopePending` projection gains `automationClass` + `bypassIsolation`; `renderReportText` prints them on the Gate-2 block. Family-agnostic scope_pending handling (partial_preview) otherwise unchanged.

## The crux, expanded - the must-pin cases

1. **`Automatic Transfer Switch` (spelled) / `ATS-1` (tag) -> transfer `scope_pending` (automatic group, default IR/DLRO ref), NOT `non_breaker_excluded`.** Proves the inversion: `ATS` no longer in `NON_BREAKER`; the transfer route claims it before the tail.
2. **`MTS-2` (tag) -> transfer scope_pending (manual group, default Manual ref).**
3. **H3 main-tie-main: a bus with two `###AF/###AT` breakers + a "transfer"/"MTM"/"interlock" note -> the two breakers stay BREAKERS (priced), NO transfer line minted; a single transfer-anchored row carrying `AF/AT` -> `transfer_parent_conflict` (null signature), breaker NOT suppressed.** The breaker golden byte-identical.
4. **`STS-1` (clean) -> `transfer_catalog_gap`; `STS-1 800AF/800AT LSIG` -> `transfer_parent_conflict` (H3 guard-first, frame/trip present).** STS never maps to an ATS ref (D5).
5. **`UPS-P1-...-MIB 1600AF/1600AT LSIG` -> stays a BREAKER (UPS is in `NON_BREAKER` but the row is a breaker main; a bare `UPS` main -> non_breaker as today).** UPS out-of-family (D5); not over-claimed by the transfer recognizer (no transfer anchor -> `looksLikeTransferSwitch` false).
6. **`Automatic Transfer Switch - Iso Bypass` / `ATS + BYPASS` -> automatic group, default `... Iso Bypass (IR/DLRO)` (H5: bypass is a match axis, ONE device).**
7. **Bare `transfer switch` (no ATS/MTS/STS, no automation word) -> automation `unknown` -> group `[Automatic base, Manual base]`, NO default (D2).**
8. **Manual + bypass (`MTS ... bypass`) -> `transfer_catalog_gap` (no manual-iso-bypass ref; D6 correction).**
9. **A 7.5 `fused disconnect` / `safety switch` -> stays SWITCH family; `Switchgear`/`Switchboard` -> excluded; `Circuit Switcher` -> excluded; bare "switch" -> not a transfer device.** Switch/breaker goldens byte-identical.
10. **Exact-ref + DUAL section-overload proof:** the 3 V1 refs resolve verbatim in the live seed; assert the DC-Battery/Charger refs ALSO sit at firm `7.18` AND generator/UPS share chapter `7.22`, so matching keys on the STRING, never the section.

## R1 (estimating authority) - provisional

`TRANSFER_R1_RATIFIED = false`. R1 here = (a) the automation-class -> default-ref table; (b) the `parseAutomationClass` precedence; (c) the `(IR/DLRO)` default-scope convention (never routing to `(Functional Testing)` in V1); (d) the two D1 SME questions carried explicitly - **is `Automatic Transfer Switch (Functional Testing)` at firm 7.18 with null acceptance hours a data bug (should be 7.22.3) or a maintenance-only convention?** and **are STS, MV transfer, and manual-iso-bypass true catalog gaps for this lane?**; (e) the bounded catalog gaps (STS, MV, manual-iso-bypass). Surfaced as `r1Ratified:false` on the scope_pending line. Never auto-priced, so fail-closed. The SME confirms, then flips it.

## Testing (TDD; operator must-pin tests in bold)

- **#1 (inversion) `ATS-1` (tag, no rating) -> transfer `scope_pending` (automatic, default IR/DLRO), NOT `non_breaker_excluded`/ignored.** `Automatic Transfer Switch` (spelled) -> transfer family, not the switch-exclusion path.
- **#2 `MTS-2` -> transfer scope_pending (manual, default Manual ref).**
- **#3 (H3 - the load-bearing discriminator) two `###AF/###AT` breakers + a transfer/MTM/interlock note -> both stay BREAKERS, no transfer line; a single transfer-anchored row + `AF/AT` -> `transfer_parent_conflict` (null signature), breaker NOT suppressed. Breaker golden byte-identical.**
- **#4 (D5) `STS-1` clean -> `transfer_catalog_gap`; `STS-1 800AF/800AT LSIG` -> `transfer_parent_conflict`; STS never maps to an ATS ref.**
- **#5 (D5) a bare `UPS` main stays `non_breaker`; a `UPS-*-MIB 1600AF/1600AT` breaker main stays a BREAKER (no transfer anchor -> not claimed).**
- **#6 (H5) `Automatic Transfer Switch - Iso Bypass` / `ATS ... bypass` -> automatic group, default `... Iso Bypass (IR/DLRO)`, ONE device.**
- **#7 (D2) bare `transfer switch` (no automation word) -> automation `unknown`, group `[auto base, manual base]`, NO default.**
- **#8 (D6) `MTS ... bypass` (manual + iso) -> `transfer_catalog_gap` (no manual-iso-bypass ref).**
- **#9 (cross-family) `fused disconnect`/`safety switch` -> switch family; `switchgear`/`switchboard`/`circuit switcher` -> excluded; bare "switch" -> not transfer. Switch + breaker goldens byte-identical.**
- **#10 (exact-ref + DUAL overload) the 3 V1 refs resolve verbatim; DC-Battery/Charger ALSO at firm 7.18 and generator/UPS share 7.22 -> match by STRING.**
- **#11 Voltage:** absent voltage -> transfer disposition + note, NOT `missing_voltage`.
- **#12 Disposition:** a recognized transfer device -> `scope_pending` (group + optional default + scopeQuestion), resolvable at Gate-2 to a valid priced envelope.
- **#13 Cross-family + compiler:** a transfer signature can never reach any other family's `match*`; the union widening forces the `kind:'transfer_switch'` emit branch (the transformer fall-through cast fails to compile without it).
- **#14 ASSESS_TO_REASON:** `transfer_recognized -> transfer_scope_pending`, `transfer_parent_conflict -> transfer_parent_conflict`.
- **#15 Runner:** a transfer-only extraction -> `partial_preview`; the scope_pending carried in the report with `automationClass`/`bypassIsolation`.
- **#16 (D4 - the intentional re-baseline) `E01-11` re-baselined:** the `STS-*` rows (which carry `AF/AT`) move from `non_breaker_carries_rating` to `transfer_parent_conflict`; the `UPS-*` breaker mains + every NON-transfer row stay byte-identical; the priced bid is unchanged (transfer/STS rows remain questions, never newly priced). Documented before/after committed alongside.
- **#17 BREAKER AND TRANSFORMER AND RELAY AND GFP AND INSTRUMENT AND SWITCH goldens byte-identical** (six prior families regression-guard the seventh; the ONLY permitted motion is the D4 `ATS`/`MTS`/`STS` disposition assertions + the `E01-11` STS rows).

## Out of scope (V2)

MV transfer switches (no priced ref -> catalog_gap in V1); a manual-iso-bypass ref (catalog_gap until the SME authors it); the `(Functional Testing)` scope as a distinct priced line (V1 defaults to IR/DLRO); pole-count / switched-neutral (3P/4P/SWN) and transition-type (open/closed/delayed/soft) as price axes (no priced discriminator; notes only); contactor-vs-breaker construction; a standalone STS ref (if the firm later prices one); a UPS (7.22.2) family (its own future lane); the Gate-2 resolution UI; producer `candidateKind`-supplied evidence beyond text.
