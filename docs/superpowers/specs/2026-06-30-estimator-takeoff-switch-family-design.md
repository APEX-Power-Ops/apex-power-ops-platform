# Estimator-Takeoff Switch / Disconnect Family (V1) - Design

Status: SPEC Rev 2.0 (operator-ratified packet 005; Rev 1.0 folded D1-D4 + the four operator tightenings [D2 conservative-default; D3 NF-as-paired-attribute; D3 breaker-hint conflict guard BOTH directions; D3 circuit-switcher exclusion ordered FIRST] + the eight added must-pin tests; Rev 2.0 folds 3 spec-review patches: [Important] the breaker-conflict guard now also catches single-token numbered AF|AT and trip-function-only rows, and SWITCH_AMP parses PLAIN amps only so AF/AT can never become switch amp evidence; [Medium] pickAuthoritative's rich-switch preference also keeps fused/ampRating evidence so a non-fused NF representative is not lost to a sparse sibling; [Refinement] air switch -> open; Rev 2.1 folds the post-build review wave (opus 3-lens + operator round 2): SWITCH_TRIP_FN tightened to require >=2 trip-function letters [was false-positiving on 2-char tag prefixes LS/LG/LI/LE carried into the raw], the partial-preview core-contract assertions pinned, and the Load-Interrupter-Switch anchor gap + the Normally-Open contact-state conflation logged as R1/SME items; Rev 2.2 folds the cross-engine Codex IRP round [4 review-run passes]: P1 vacuum-switch-priced-as-breaker [added a vacuum-switch anchor -> catalog_gap], P2 vacuum-widened-to-any:unknown [NO_HOME guard], P2 negated-fused class [non/un x fused/fusible parsed non-fused], P2 bare-NF-tag-vs-explicit-Fused precedence, and P2 richSwitch amp-only order-dependence [two-tier fused/type-over-amp] - all fixed; the Vista/Motor-Operated bare-label recognition gap is logged under R1 (f) as the remaining operator/SME decision). Date: 2026-06-30.
Lane: estimator-takeoff/switch-family-admission (off main 89aa24a1). Dev-only; merge operator-gated.
Packet: docs/superpowers/packets/estimator-takeoff-family-switches.md (Part 6 decisions + Part 9 ratification).
Predecessors (reused, must stay byte-identical): breaker engine + transformer slice (PR #49) + relay slice (PR #50) + GFP slice (PR #51) + instrument-transformer slice (PR #52).

**Goal:** Admit the SWITCH / DISCONNECT family (NETA 7.5) into `packages/estimator-takeoff` as a bounded V1 slice - the 6th apparatus family and 4th scope-driven family - so a recognized non-automatic switch/disconnect is counted per device and routed to a Gate-2 voltage-x-type scope decision (never auto-priced), while the breaker recognizer and all five prior families stay BYTE-IDENTICAL.

**Architecture:** Reuse the transformer/relay/GFP/instrument scope_pending machinery (discriminated-union signature, `scope_pending` + optional `provisionalDefaultRef`, candidateKind, kind-prefixed `deviceId`, cross-family routing). Add a sixth signature `kind: 'switch'`, a device-first switch recognizer routed AFTER the five prior families (a switch never carries their tokens) whose FIRST actions are an EXCLUSION pass and a switch-local breaker-conflict guard, a voltage-x-type match group, and catalog-gap handling. The defining difficulty is pure RECOGNITION: "switch" is the most overloaded device word in the catalog (switchboard/switchgear/transfer-switch/circuit-switcher all contain it), and a switch shares the SF6/vacuum/air medium tokens with the EXISTING breaker recognizer - so the switch route must intercept anchored switch rows before the breaker fallback WITHOUT changing breaker behavior.

**Tech stack:** TypeScript, Vitest, pnpm workspace; host build over `ssh olares-mesh`.

## Global Constraints

- **ASCII-only** in all authored code/comments AND engine-emitted strings (no em-dashes). Verbatim source DATA may be UTF-8.
- **Breaker AND transformer AND relay AND GFP AND instrument-transformer goldens byte-identical** after every task. Five prior families now regression-guard the sixth.
- **No new catalog refs and no new hours.** V1 uses the 11 existing switch refs only (D1). Matched by exact ref STRING, NEVER by section (a 12th ref, `PDU (Power Distribution Unit)`, also sits at firm 7.5 - the overload that forces string matching).
- **The 11 switch refs (verbatim from the live seed, exact strings):** `Switch LV - Fused Disconnect`; `Switch LV - Fused Disconnect (Open)`; `Switch MV - Fused Disconnect`; `Switch MV - Open`; `Switch MV - Cutout`; `Switch MV - Oil Insulated`; `Switch MV - Motor Operated`; `Switch (SF6) - Medium Voltage`; `Switch (Pad Mount Vista) - Medium Voltage`; `Switch HV - Open`; `Switch HV - Motor Operated`.
- **Switches never auto-price.** Every recognized switch -> `scope_pending` (candidate ref-GROUP + optional provisional default) or `catalog_gap`. No "matched" switch line in V1.
- **Recognition is device-first (anchor), NEVER the bare token "switch"** (D3). The anchor set is COMPOUND switch-device nouns; the bare word "switch" with no qualifier is not an anchor.
- **NF is an ATTRIBUTE, never a standalone anchor** (D3 T1): `NF` (non-fused) sets `fused:false` only when paired with a real anchor or `candidateKind:'switch'`; a bare `NF-1` tag or raw text merely containing `NF` does NOT mint a switch candidate.
- **The breaker-conflict guard keys on the UNAMBIGUOUS breaker subset, NOT the shared medium** (D3 T2): `vacuum`/`SF6`/`air frame` live inside the live `BREAKER_HINT` (normalize.ts L7), so the switch route uses a switch-local predicate over (a) `SWITCH_BREAKER_CONFLICT = /\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|GB|FB)\b/i`, (b) the full `FRAME_TRIP` pair, (c) a single numbered `AF|AT` token (`SWITCH_FRAME_TRIP`), (d) a trip-function descriptor (`SWITCH_TRIP_FN`, the LSIG family), and (e) `NON_BREAKER`. The shared medium tokens (`SF6`/`vacuum`/`air frame`) are switch CONSTRUCTION evidence, NOT conflict signals. `BREAKER_HINT`/`FRAME_TRIP`/`NON_BREAKER` are NOT modified.
- **SWITCH_AMP parses PLAIN continuous amps only** (D3 T2 corollary): a numbered `AF`/`AT` token can NEVER be read as switch amp evidence (it has no priced-amp meaning for a switch and is breaker-shaped) - the amp parser requires a plain `A` word boundary, so `800AF`/`800AT` are excluded by construction and only reach the conflict guard.
- **Circuit-switcher exclusion ordered FIRST** (D3 T3): `circuit switcher` (firm 7.3), `transfer switch`, `switchgear`, `switchboard` are EXCLUDED as the recognizer's first action, before any anchor/medium matching. Excluded rows keep their current (pre-switch-family) disposition - byte-identical.
- **Provisional default ONLY with voltage class AND a specific type token** (D2): a candidate group is always offered; a `provisionalDefaultRef` is set only when BOTH a voltage class AND a specific type/construction token (fused disconnect / cutout / oil / SF6 / Vista / motor operated / explicit open) are present. A generic `disconnect`/`switch` anchor alone -> group, NO default. Illegible voltage -> group, NO default.
- **Gates (verified on host):** `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (cross-package false-green-trap gate).
- **Cross-engine (Codex) IRP** before merge; merge operator-gated (admin-rebase PR).
- **R1 (estimating authority) PROVISIONAL** (`SWITCH_R1_RATIFIED=false`): the voltage-x-type -> default-ref table, the parse precedence, the open-vs-enclosed default tier, and the bounded catalog gaps are provisional until the SME confirms (D1). Never auto-priced, so provisional is fail-closed.

## The V1 Contract

1. **Recognize switches DEVICE-FIRST by a COMPOUND anchor (never the bare token "switch").** A switch is established by a producer `candidateKind:'switch'` OR a switch-device anchor + a device identity (tag). The anchor set (`SWITCH_DEVICE`) is compound switch-device nouns: `disconnect`/`disconnect switch`, `fused`/`fusible switch`, `safety switch`, `load(-)break switch`/`LBS`, `isolation`/`isolating switch`, `knife switch`, `air switch`, `oil switch`, `SF6 switch`, `cutout`, `non-fused disconnect`. The bare word "switch" with no qualifier is NOT an anchor. `NF` is NOT an anchor (it is an attribute consumed only when a real anchor is present).
2. **Exclude the "switch"-overload families FIRST, then guard the breaker conflict, then match the anchor.** In `looksLikeSwitch`, the FIRST test is the exclusion pass (`circuit switcher` / `transfer switch` / `switchgear` / `switchboard` -> false). A misrouted parent (a switch-anchored row that ALSO carries an unambiguous breaker signal) is surfaced INSIDE `assessSwitch` as a `switch_parent_conflict` question (signature null), never a silent switch line and never suppressing a real breaker.
3. **Scope-driven; never auto-price.** A recognized switch -> `scope_pending`: a candidate ref-GROUP (the voltage-x-type refs) + a Gate-2 scope question, with a PROVISIONAL default ONLY where voltage class AND a specific type token are present, NO default otherwise. A recognized voltage-x-type with no priced home (D1 gaps: LV non-fused, vacuum, HV fused/cutout/oil/SF6) -> `catalog_gap`.
4. **Quantity is per individual device.** Every switch ref is `unit_of_issue: each`; a 3-phase disconnect is ONE switch. NO set/each packaging convention (unlike instrument transformers).
5. **Voltage optional/contextual.** Voltage class drives the candidate group WHEN present; absent voltage -> a WIDER candidate group (all switch refs, or all refs of the parsed type) + a voltage note, NEVER `missing_voltage`.
6. **All prior family paths untouched.** `ApparatusSignature` is a discriminated union on `kind`; a switch signature can never reach `matchBreaker`/`matchTransformer`/`matchRelay`/`matchGfp`/`matchInstrumentTransformer` or a priced line (compiler-enforced). Breaker + transformer + relay + GFP + instrument behavior byte-identical.

## Component Design (engine seams, grounded @ main 89aa24a1)

### 1. Extraction (`extraction/types.ts`, `extraction/parse.ts`)
- `extraction/types.ts`: widen `candidateKind` to `'breaker' | 'transformer' | 'relay' | 'gfp' | 'instrument_transformer' | 'switch'`.
- `extraction/parse.ts`: widen the validation guard to accept `'switch'`; update the expected-string message.

### 2. Signature types (`signature/types.ts`)
- Add:
  ```ts
  export type SwitchType =
    | 'fused_disconnect' | 'open' | 'oil' | 'sf6' | 'cutout'
    | 'motor_operated' | 'vista' | 'vacuum' | 'unknown'
  export interface SwitchSignature extends BaseSignature {
    kind: 'switch'
    switchType: SwitchType
    fused?: boolean        // CONTRACT: NF -> false; fused/fusible -> true; undefined when unstated. Disambiguates the LV non-fused gap.
    ampRating?: number     // evidence/display only (continuous A; NOT a frame/trip pair)
    // voltageClass stays optional (inherited): contextual; drives the group when present, never gates.
  }
  ```
  Note: `switchType` is the SINGLE match discriminator. Motor-operation is carried as `switchType:'motor_operated'` (NOT a separate boolean - a deliberate simplification of the packet sketch, since the firm prices it as its own ref). `vacuum` is a recognized type with NO priced ref (an honest gap). `fused` is kept as a separate evidence flag ONLY because it disambiguates a non-fused LV disconnect (a catalog gap) from a fused one.
- `export type ApparatusSignature = BreakerSignature | TransformerSignature | RelaySignature | GfpSignature | InstrumentTransformerSignature | SwitchSignature`.

### 3. Recognition + parse (`signature/normalize.ts`)
- Token regexes (ASCII):
  - `SWITCH_EXCLUDE` (the "switch"-overload families - tested FIRST, T3): `/\b(circuit\s+switcher|transfer\s+switch|switchgear|switchboard)\b/i`.
  - `SWITCH_DEVICE` (compound switch-device anchors - NEVER the bare token "switch"): `/\b(disconnect(\s+switch)?|fus(ed|ible)\s+switch|safety\s+switch|load[\s-]?break\s+switch|LBS|isolat(ion|ing)\s+switch|knife\s+switch|air\s+switch|oil\s+switch|SF6\s+switch|cutout|non[\s-]?fused\s+disconnect)\b/i`.
  - `SWITCH_BREAKER_CONFLICT` (the UNAMBIGUOUS breaker subset for the switch-local guard - DELIBERATELY excludes the shared `vacuum`/`SF6`/`air frame`): `/\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|GB|FB)\b/i`.
  - `SWITCH_FRAME_TRIP` (a single numbered frame/trip token - catches `800AF` or `800AT` even WITHOUT the full `FRAME_TRIP` pair): `/\b\d{2,6}\s*A[FT]\b/i`.
  - `SWITCH_TRIP_FN` (a breaker trip-function descriptor on a switch row = conflict; mirrors the breaker `parseFunctions` L(SIGE) shape): `/\bL(?=[SIGE]{2})(S?)(I?)(G?)(E?)\b/i`. The `(?=[SIGE]{2})` lookahead REQUIRES at least two function letters after `L` so the genuine `LSI`/`LSIG` family matches while a bare 2-char TAG prefix carried into the raw (`LS-1`/`LG-2`/`LI-7`/`LE-3`, where the delimiter satisfies `\b` after a single SIGE letter) does NOT - this avoids the false-positive (post-build review, Rev 2.1) that mis-flagged a legitimate disconnect as `switch_parent_conflict`. The ordered groups + `\b` still spare `LBS` (L+B), `LV` (L+V), and English words (`LESS`/`LIGHT`).
  - `SWITCH_NF` (the non-fused attribute - consumed ONLY when a real anchor is present): `/\bN\.?F\.?\b|\bnon[\s-]?fused\b/i`.
  - `SWITCH_AMP` (PLAIN continuous-ampere evidence ONLY - a `\bA\b` word boundary means `800AF`/`800AT` do NOT match, so AF/AT can never become switch amp evidence): `/(?<!\d)(\d{2,6})\s*A\b/i` - evidence only.
- `looksLikeSwitch(x)`:
  ```ts
  function looksLikeSwitch(x: ExtractedApparatus): boolean {
    if (SWITCH_EXCLUDE.test(x.raw)) return false               // T3: overload families excluded FIRST
    if (x.candidateKind === 'switch') return true              // explicit producer signal wins
    if (x.candidateKind !== undefined && x.candidateKind !== 'switch') return false  // defer to other producer signals
    return SWITCH_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0   // compound anchor + tag
  }
  ```
  (Like `looksLikeInstrumentTransformer`, the breaker-conflict guard is NOT in `looksLikeSwitch`; a conflicted row ENTERS the switch route and is flagged inside `assessSwitch`, mirroring the instrument parent-conflict precedent at normalize.ts L186.)
- `parseSwitchType(raw): SwitchType` - text-only, fail-closed, with a documented PRECEDENCE (most specific product/actuation first; provisional R1):
  ```
  pad-mount vista          -> 'vista'
  motor operated / M.O.    -> 'motor_operated'
  SF6                      -> 'sf6'
  oil                      -> 'oil'
  cutout                   -> 'cutout'
  vacuum                   -> 'vacuum'        (recognized; no priced ref -> gap)
  fused/fusible (disc)     -> 'fused_disconnect'
  air switch / "open"      -> 'open'          (air-open switches ARE the firm "Open" refs; spec-review refinement)
  else                     -> 'unknown'       (generic disconnect/switch anchor; group + NO default)
  ```
  A generic `disconnect`/`safety switch` with no medium/actuation token -> `'unknown'` (still a recognized switch; D2 conservative -> no default).
- `parseFused(raw): boolean | undefined`: `SWITCH_NF` -> `false`; `/\bfus(ed|ible)\b/i` -> `true`; else `undefined`.
- `parseAmpRating(raw): number | undefined`: continuous A (evidence only).
- `assessSwitch(x, voltageBasis?): ApparatusAssessment` - CONFLICT GUARD FIRST (switch routes before the breaker fallback, so a misrouted parent must surface a question, never a silent switch scope_pending):
  - `if (SWITCH_BREAKER_CONFLICT.test(x.raw) || FRAME_TRIP.test(x.raw) || SWITCH_FRAME_TRIP.test(x.raw) || SWITCH_TRIP_FN.test(x.raw) || NON_BREAKER.test(x.raw))` -> `switch_parent_conflict` question, signature null. (Covers `candidateKind:'switch'` + a full `AF/AT` pair, a SINGLE `800AF`/`800AT` token, a trip-function-only row [`LSIG` with no AF/AT], a switch-anchored row carrying VCB/ACB/breaker, and a NON_BREAKER token. The shared `SF6`/`vacuum`/`air frame` do NOT trip this guard.)
  - else build the signature: `switchType = parseSwitchType(x.raw)`, `fused = parseFused(x.raw)`, `ampRating = parseAmpRating(x.raw)`, `voltageClass = classifyVoltage(x.busVoltageV)` (MAY be undefined - NOT gated). `assessmentCode: 'switch_recognized'`.
- `assessCore` order: insert the switch route AFTER the `looksLikeRelay` block (normalize.ts L352-354) and BEFORE the `NON_BREAKER` block (L356): `if (looksLikeSwitch(x)) return assessSwitch(x, voltageBasis)`. New order: instrument -> transformer -> GFP -> relay -> SWITCH -> NON_BREAKER -> breaker. This placement is load-bearing: a switch-anchored row carrying a shared medium token (`SF6 switch`, `vacuum switch`) has `looksLikeBreaker === true` today and would otherwise fall through to the breaker assessment (L362 `!looksLikeBreaker` is false); the switch route intercepts it first.
- New `AssessmentCode` members: `switch_recognized`, `switch_parent_conflict`. (No `switch_type_unparsed`: a generic anchor with no type token is a RECOGNIZED switch with `switchType:'unknown'`, not a null - it produces a no-default scope_pending, per D2.)

### 4. Match (`catalog/switch-map.ts` + `.data.ts`)
- `.data.ts`: the 11 refs VERBATIM (exact strings); a `SWITCH_GROUPS: Record<string, string[]>` keyed by `${SwitchType}:${VoltageClass}` plus generic `any:${VoltageClass}` and `any:unknown` groups; `SWITCH_R1_RATIFIED = false`. Provisional R1 table:
  ```
  'fused_disconnect:LV' -> ['Switch LV - Fused Disconnect', 'Switch LV - Fused Disconnect (Open)']
  'fused_disconnect:MV' -> ['Switch MV - Fused Disconnect']
  'open:MV'             -> ['Switch MV - Open']
  'open:HV'             -> ['Switch HV - Open']
  'cutout:MV'           -> ['Switch MV - Cutout']
  'oil:MV'              -> ['Switch MV - Oil Insulated']
  'motor_operated:MV'   -> ['Switch MV - Motor Operated']
  'motor_operated:HV'   -> ['Switch HV - Motor Operated']
  'sf6:MV'              -> ['Switch (SF6) - Medium Voltage']
  'vista:MV'            -> ['Switch (Pad Mount Vista) - Medium Voltage']
  'any:LV'              -> ['Switch LV - Fused Disconnect', 'Switch LV - Fused Disconnect (Open)']
  'any:MV'              -> [all 7 MV refs]
  'any:HV'              -> ['Switch HV - Open', 'Switch HV - Motor Operated']
  'any:unknown'         -> [all 11 refs]
  // ABSENT keys (deliberate gaps): vacuum:*, fused_disconnect:HV, cutout:HV, oil:HV, sf6:HV, open:LV
  ```
- `.ts`: `interface SwitchScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }`; `matchSwitch(sig): SwitchScopeMatch | null`:
  - **Non-fused LV gap rule (D1, FIRST):** LV is FUSED-ONLY (both LV refs are "Fused Disconnect"), so a definitively non-fused LV disconnect has no priced home. If `sig.fused === false` AND `voltageClass === 'LV'` AND `switchType` in {`unknown`, `fused_disconnect`} -> `null` (catalog_gap). (MV/HV are NOT gated here: "Switch MV - Open" / "Switch HV - Open" are plausible non-fused homes, so a non-fused MV/HV disconnect resolves to the `any` group with no default, not a gap.)
  - resolve the group: if `switchType !== 'unknown'`, key = `${switchType}:${voltageClass ?? 'unknown'}`; if `switchType === 'unknown'`, key = `any:${voltageClass ?? 'unknown'}`.
  - if the key is missing OR present-and-empty -> `null` (-> catalog_gap). (Covers vacuum, HV fused/cutout/oil/SF6, LV open.)
  - `defaultRef` set ONLY when `voltageClass !== undefined` AND `switchType !== 'unknown'` AND the group is non-empty: the FIRST (conservative-tier) ref in the group (e.g. `fused_disconnect:LV` -> `Switch LV - Fused Disconnect`, the enclosed tier, NOT the `(Open)` variant). A generic anchor (`switchType:'unknown'`) -> NO default even with voltage. Absent voltage -> NO default.
  - return `{ group: [...group], defaultRef, scopeQuestion: SCOPE_Q }`. Match by exact ref STRING (PDU overload guard).

### 5. Quantify (`quantify/quantify.ts`)
- Add an `s.kind === 'switch'` branch to `specKey` BEFORE the transformer fall-through: `[s.kind, s.switchType, s.voltageClass ?? '-', s.fused === undefined ? '-' : (s.fused ? 'F' : 'NF'), s.source.block ?? '-'].join('|')`. (`ampRating` is evidence, NOT in the key - two switches of the same type/voltage/fused aggregate.) `deviceId` kind-prefixes (`switch:TAG`), so switch rows never cross-bucket with breakers.
- `pickAuthoritative`: add a `richSwitch = auths.find((o) => o.kind === 'switch' && (o.switchType !== 'unknown' || o.fused !== undefined || o.ampRating !== undefined))` preference (mirrors the relay role preference, broadened per spec review). It must keep ANY recognition evidence - critically `fused:false` from an `NF disconnect` row whose `switchType` is still `unknown` - so a sparse same-tag one-line occurrence cannot win and erase the evidence that drives the LV non-fused catalog-gap proof.

### 6. Disposition + contract (`buckets/types.ts`, `emit/emit.ts`, `runner/report.ts`)
- `buckets/types.ts`: `OperatorQuestionCode` += `switch_scope_pending` | `switch_catalog_gap` | `switch_parent_conflict`; `DispositionReasonCode` += same three; `TakeoffFinding.code` += `switch_catalog_gap` (ONLY catalog_gap is a finding; the parent-conflict is a question/disposition code, not a finding). Add optional contract evidence fields to `ScopePendingLine`: `switchType?: string` + `fused?: boolean`; and the same optional fields to `ApparatusDisposition` (carried alongside candidateRefs/provisionalDefaultRef/scopeQuestion so Gate-2/UI consumers have the recognition evidence).
- `emit/emit.ts`: import `matchSwitch` + `SWITCH_R1_RATIFIED` + the `SwitchSignature` type. Add the `sig.kind === 'switch'` branch in the match loop BEFORE the transformer fall-through (with `continue`, so the `const tsig: TransformerSignature = sig` cast at the tail stays compiler-valid - the union widening forces this branch): a scope match -> `scope_pending` (candidateRefs=group, provisionalDefaultRef=defaultRef [may be undefined], r1Ratified=SWITCH_R1_RATIFIED, switchType=sig.switchType, fused=sig.fused, scopeQuestion), AND stamp `disp.switchType`/`disp.fused` on each member disposition; a `null` match -> `switch_catalog_gap` finding (severity warning) + `unmatched` disposition + question. Update `ASSESS_TO_REASON`: `switch_recognized -> switch_scope_pending` (unreachable; exhaustiveness), `switch_parent_conflict -> switch_parent_conflict`.
- `runner/report.ts`: the `scopePending` projection gains `switchType` + `fused`; `renderReportText` prints them on the Gate-2 block (e.g. `type=sf6 fused=-`). Family-agnostic scope_pending handling (partial_preview) otherwise unchanged.

## The crux, expanded - the must-pin recognition cases

1. **"Fused Disconnect ..." / "Safety Switch ..." + tag -> switch.** `looksLikeSwitch` matches (compound anchor + tag); routed after the five families; no breaker conflict -> `switch_scope_pending`.
2. **A real breaker (`###AF/###AT` + LSIG) -> stays BREAKER.** No switch anchor -> `looksLikeSwitch` false -> the breaker path is unchanged. Breaker golden byte-identical.
3. **`SF6 switch` -> switch (SF6 group); `SF6 breaker` / `VCB` / `800AF/800AT LSIG` -> NOT a switch (BOTH directions, T2).** `SF6 switch`: compound anchor present, `SWITCH_BREAKER_CONFLICT` does NOT match `SF6` -> recognized switch, `switchType:'sf6'`. `SF6 breaker` / `VCB`: no switch anchor -> `looksLikeSwitch` false -> stays breaker. A switch-anchored row that ALSO carries `VCB`/`AF/AT` -> `switch_parent_conflict` question (null signature), breaker not suppressed.
4. **`Circuit Switcher MV/HV` -> NOT a switch (T3).** `SWITCH_EXCLUDE` matches `circuit switcher` FIRST -> `looksLikeSwitch` false -> falls through to the existing unrecognized handling; byte-identical to today.
5. **`Automatic Transfer Switch` / `Manual Transfer Switch` (spelled out) -> NOT a 7.5 switch.** `SWITCH_EXCLUDE` matches `transfer switch` -> false. (The ATS/MTS abbreviations are already in `NON_BREAKER`; the spelled-out forms fall through to unrecognized.)
6. **`Switchgear` / `Switchboard` -> NOT a switch.** `SWITCH_EXCLUDE` matches -> false; byte-identical.
7. **`NF` with NO disconnect/switch anchor -> NOT counted (T1).** A bare tag `NF-1` or raw text merely containing `NF` with no `SWITCH_DEVICE` anchor -> `looksLikeSwitch` false. `NF` is consumed by `parseFused` only when a real anchor is present.
8. **`NF disconnect` + tag -> switch candidate, then catalog_gap or no-default per voltage/type (T1 + D1).** Anchor `disconnect` present -> recognized switch, `fused:false`. At LV (fused-only) -> `matchSwitch` returns `null` -> `switch_catalog_gap`. With no voltage -> `any:unknown` group, NO default.
9. **Generic `disconnect` + voltage but NO type token -> scope_pending with NO default (D2).** e.g. "Disconnect, MV" + tag, no fused/open/medium token -> `switchType:'unknown'` -> `any:MV` group, `provisionalDefaultRef` undefined.
10. **LV non-fused / vacuum / HV fused/cutout/oil/SF6 -> `switch_catalog_gap` (D1).** Recognized switch, no priced home -> `matchSwitch` null -> surfaced, never fabricated.

## R1 (estimating authority) - provisional

`SWITCH_R1_RATIFIED = false`. R1 here = (a) the voltage-x-type -> default-ref table (the `SWITCH_GROUPS` defaults), (b) the `parseSwitchType` precedence (vista > motor_operated > sf6 > oil > cutout > vacuum > fused_disconnect > open), (c) the `air switch -> open` mapping (an air-open switch maps to the firm "Open" refs), (d) the open-vs-enclosed default tier (the enclosed "Switch LV - Fused Disconnect" 1.0h as the LV default over the "(Open)" 2.0h variant), and (e) the bounded catalog gaps (LV non-fused, LV open, vacuum, HV fused/cutout/oil/SF6). Surfaced as `r1Ratified:false` on the scope_pending line. Never auto-priced, so fail-closed. The SME confirms the convention + mappings + gaps, then flips it.

Post-build review additions to the R1/SME gate (all fail-closed in V1, NOT defects - surfaced for the operator/SME, not silently shipped): (f) **anchor coverage** - several subtypes the parser/catalog support are not yet reachable from bare extractor text because `SWITCH_DEVICE` omits their anchors, so they route to `unrecognized_apparatus_row` (or, for Pad-Mount-Vista, are claimed by the transformer `pad.?mount` recognizer that runs before the switch branch) - surfaced as a question, never priced, never lost, and reachable today via `candidateKind:'switch'` or a paired `disconnect`/`switch` device noun. The gate should decide (with real bench labels) whether to add: `load[\s-]?interrupter\s+switch` (Load Interrupter Switch); `motor[\s-]?operated`/`M\.?O\.?` switch anchors (so "M.O. Switch" recognizes without a paired "disconnect"); `vista`/`pad[\s-]?mount\s+vista` (and order the switch branch ahead of, or carve a Vista exception into, the transformer `pad.?mount` recognizer so a Vista switch is not mis-claimed as a transformer). Each addition broadens the operator-ratified D3 anchor set, hence the SME gate. (g) **contact-state vs construction** - `parseSwitchType` reads `Normally Open Disconnect` as `switchType:'open'` (the construction tier), conflating contact-state with construction; the SME confirms whether `normally open` should be distinguished from a construction `open` (low impact: scope_pending only, R1 provisional, operator picks the tier at Gate-2). (Resolved in code, not deferred: the negated-fused class [`non`/`un` x `fused`/`fusible`] and the bare-`NF`-tag-vs-explicit-`Fused` precedence are both handled in `parseFused`/`parseSwitchType`.)

## Testing (TDD; operator must-pin tests in bold)

- **#1 Fused disconnect / safety switch + tag -> switch (`switch_scope_pending`), NOT a breaker.**
- **#2 Real breaker (`800AF/800AT` LSIG) -> stays breaker; breaker golden byte-identical.**
- **#3 (T2 BOTH directions) `SF6 switch` -> switch (`switchType:'sf6'`, SF6 group); `SF6 breaker` / `VCB` -> stays breaker; switch anchor + `VCB`/`AF/AT` -> `switch_parent_conflict` (null signature, breaker not suppressed).**
- **#4 (T3) `Circuit Switcher MV/HV` -> NOT a switch (excluded FIRST, before any SF6/anchor matching).**
- **#5 `Automatic Transfer Switch` / `Manual Transfer Switch` (spelled out) -> NOT a 7.5 switch.**
- **#6 `Switchgear` / `Switchboard` -> NOT a switch.**
- **#7 (T1) `NF` with no disconnect/switch anchor (bare `NF-1` tag; raw containing `NF`) -> NOT counted.**
- **#8 (T1 + D1) `NF disconnect` + tag -> switch candidate; LV -> `switch_catalog_gap`; no voltage -> `any:unknown` group, no default.**
- **#9 (D2) Generic `disconnect` + voltage, no type token -> `switch_scope_pending` with `provisionalDefaultRef` undefined.**
- **#10 (D1) LV non-fused / vacuum / HV fused/cutout/oil/SF6 -> `switch_catalog_gap` (recognized, no priced home).**
- **#11 Type+voltage recognition:** MV + "fused disconnect" -> `fused_disconnect:MV` group + default; MV + "SF6" -> `sf6:MV`; MV + "cutout" -> `cutout:MV`; "motor operated"/"M.O." -> `motor_operated` group; LV "fused disconnect" -> `fused_disconnect:LV` default `Switch LV - Fused Disconnect` (enclosed tier, not `(Open)`).
- **#12 Voltage classification:** an MV switch -> MV switch refs; absent voltage -> wider group (`any:unknown`) + a voltage note, NOT `missing_voltage`.
- **#13 Exact-ref validation + PDU-overload proof:** each of the 11 refs resolves verbatim in the live seed; assert `PDU (Power Distribution Unit)` ALSO sits at firm 7.5 so matching keys on the STRING, not the section.
- **#14 Disposition:** a recognized switch -> `scope_pending` (group + optional provisional default + scopeQuestion), resolvable at Gate-2 to a valid priced envelope.
- **#15 (parse precedence)** "MV motor-operated SF6 switch" -> `switchType:'motor_operated'` (actuation outranks medium per R1 precedence).
- **#16 Cross-family + compiler:** a switch signature can never reach matchBreaker/matchTransformer/matchRelay/matchGfp/matchInstrumentTransformer; the union widening forces the `kind:'switch'` emit branch (the transformer fall-through cast fails to compile without it).
- **#17 ASSESS_TO_REASON:** `switch_recognized` -> `switch_scope_pending`, `switch_parent_conflict` -> `switch_parent_conflict`.
- **#18 Runner:** a switch-only extraction -> `partial_preview`; the scope_pending carried in the report with `switchType`/`fused`.
- **#19 (the real golden):** a service one-line with a fused disconnect + an MV switch + a REAL breaker + an assembly (switchgear) coexisting -> the switches scope_pend to their groups, the breaker prices, the assembly is excluded (not a switch), `partial_preview`; a Gate-2 stand-in prices a chosen switch ref via estimator-core.
- **#20 BREAKER AND TRANSFORMER AND RELAY AND GFP AND INSTRUMENT goldens byte-identical** (five prior families regression-guard the sixth). Includes the build-time watch: confirm no existing golden row that today falls through to the breaker assessment via a shared medium token (`SF6 switch`-shaped) moves into the switch family.
- **#21 (spec-review Important - AF/AT/LSIG guard + amp parse):** a switch-anchored row with a SINGLE `800AF` (no `/`-pair) -> `switch_parent_conflict`; a switch-anchored row with a trip-function descriptor only (e.g. "Disconnect DS-1 LSIG", no AF/AT) -> `switch_parent_conflict`; `parseAmpRating` reads "400A" as 400 but returns undefined for "800AF"/"800AT" (AF/AT never become switch amp evidence).
- **#22 (spec-review Refinement - air switch -> open):** "Air Switch" + MV + tag -> `switchType:'open'` -> `open:MV` group, default `Switch MV - Open`; "Air Switch" + HV -> default `Switch HV - Open`; "Air Switch" + LV -> `switch_catalog_gap` (`open:LV` absent); "Air Switch" no voltage -> the wider open group, NO default. (Negative: "air frame" with no switch anchor is NOT pulled into the switch family - it stays its breaker path.)
- **#23 (spec-review Medium - rich switch keeps fused evidence):** for one tag, an authoritative schedule row "NF Disconnect" (fused:false, switchType unknown) + a sparser authoritative one-line occurrence (no fused signal) -> `pickAuthoritative` returns the `fused:false` occurrence as the representative, so an LV bank yields `switch_catalog_gap` (the non-fused gap proof is NOT erased by the sparse sibling).

## Out of scope (V2)

Load-interrupter vs isolation-only test-scope distinctions if the firm prices them; the fuse-element continuity test as a separate line; ratio/burden-based ref selection; the open-vs-enclosed AUTO-inference (V1 surfaces the group; the operator picks the tier at Gate-2); the Gate-2 resolution UI; a dedicated transfer-switch (7.18/7.22) or circuit-switcher (7.3) family (V1 only EXCLUDES them - it does not yet price them); producer `candidateKind`-supplied construction evidence beyond text.
