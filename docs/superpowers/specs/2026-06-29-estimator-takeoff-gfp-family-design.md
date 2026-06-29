# Estimator-Takeoff Standalone Ground-Fault Protection Device/System (LV) (V1) - Design

Status: SPEC Rev 2 (operator-ratified packet 003; Rev 2 folds the operator's standalone-only tightening: GFP is a narrow STANDALONE escape hatch, not a broad apparatus family - embedded GFP is PARENT evidence, never a counted GFP line; `candidateKind:'gfp'` means "producer asserts a STANDALONE GFP device"; a HARD parent-device exclusion overrides even candidateKind; function/scope text ("ground fault test", "per 7.14") is parent evidence, not a device token; `gfp_breaker_conflict` dropped as unreachable). Date: 2026-06-29.
Lane: estimator-takeoff/gfp-family-admission (off main ab43c569). Dev-only; merge operator-gated.
Packet: docs/superpowers/packets/estimator-takeoff-family-gfp.md (Part 6 decisions + Part 9 ratification).
Predecessors (reused, must stay byte-identical): breaker engine (signature-deterministic) + transformer slice (scope_pending machinery, PR #49) + relay slice (device-first recognition, cross-family guards, PR #50).

**Goal:** Admit a narrow STANDALONE Ground-Fault Protection Device/System (LV) escape hatch into `packages/estimator-takeoff` as a bounded V1 slice - so that ONLY a standalone GFP device/system is counted (per device) and routed to a one-click Gate-2 scope confirmation, never auto-priced, while an EMBEDDED ground-fault function (a breaker's LSIG element, an ATS/SPD/etc. ground-fault function) stays with its PARENT apparatus and produces NO GFP line. Breaker / transformer / relay behavior is untouched.

**Architecture:** Reuse the relay/transformer scope_pending machinery (discriminated-union signature, `scope_pending` disposition with optional `provisionalDefaultRef`, R1-provisional flag, kind-prefixed `deviceId`, cross-family routing). Add a fourth signature `kind: 'gfp'` (standalone GFP only), a STANDALONE-ONLY recognizer, and a trivial one-ref match. The defining property: GFP is recognition-gated and fail-closed against FALSE POSITIVES. A ground-fault burden that belongs to a parent is ALREADY represented in the parent ref (e.g. the breaker `LSIG` ref/hours vs `LS/LSI`), so a parent-shaped row must never produce a separate GFP line - this is a HARD exclusion that overrides even `candidateKind:'gfp'`. A real standalone GFP device is its OWN, non-parent-shaped row. Two engine-visible specifics: (1) the accounting layer is a SINGLE priced ref, so there is no tier ambiguity, no candidate GROUP, and no V1 `catalog_gap`/`null` path - `matchGfp` always returns the one ref as both the only candidate and the provisional default (a confirm gate, not a choice); (2) recognition is the entire difficulty and is the load-bearing guard.

**Tech stack:** TypeScript, Vitest, pnpm workspace; host build over `ssh olares-mesh`.

## Global Constraints

- **ASCII-only** in all authored SQL/comments AND engine-emitted strings (questions, findings, scope questions, notes). Verbatim source DATA may be UTF-8. (No em-dashes in engine strings.)
- **Breaker AND transformer AND relay goldens byte-identical** after every task. Three prior families now regression-guard the fourth.
- **No new catalog refs and no new hours.** V1 uses the single existing NETA-7.14 ref `Ground Fault Protection Device LV` only (D1 V1-policy). Matched by exact ref STRING, never by section (firm "7.14" is overloaded with CT refs).
- **GFP never auto-prices.** Every recognized standalone GFP device -> `scope_pending` (single ref as provisional default + a confirm question). There is no "matched" GFP line and no GFP `catalog_gap` in V1.
- **STANDALONE-ONLY; hard parent exclusion.** A parent-shaped row - one that `looksLikeBreaker` (frame/hint) OR matches `NON_BREAKER` (ATS/MTS/SPD/PDU/UPS/...) - NEVER produces a GFP line, EVEN with `candidateKind:'gfp'`. Embedded ground-fault is carried by the parent ref. Function/scope text ("ground fault test", "per 7.14", bare "ground fault protection") is parent evidence, NOT a device token.
- **`candidateKind:'gfp'` = producer asserts a STANDALONE GFP device** (not "this row mentions ground fault"). It is honored only on a non-parent-shaped row.
- **Gates (verified on host):** `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (the cross-package gate; `--filter apex-operations-web` matches NOTHING - false-green trap).
- **Cross-engine (Codex) IRP** before merge; merge operator-gated (admin-rebase PR).
- **R1 (estimating authority) stays PROVISIONAL** (`GFP_R1_RATIFIED=false`) until the SME confirms the single-ref-covers-all convention (D1). GFP never auto-prices, so provisional is safe.

## The V1 Contract

1. **Recognize ONLY standalone GFP devices, device-first, with a STRONG anchor.** A standalone GFP device is established by either a producer `candidateKind:'gfp'` OR a dedicated GFP DEVICE-NOUN token (`GFP`/`GFPE`/`GFR`, or `GROUND FAULT` + `RELAY|SENSOR|MONITOR|MODULE|SYSTEM|DEVICE|UNIT`, or `GROUND FAULT PROTECTION` + `SYSTEM|DEVICE|UNIT|RELAY|MODULE|PANEL`) together with a device identity (tag) - AND the row is NOT parent-shaped. Bare ANSI ground functions (50G/51G/50N/51N/64) and function/scope phrasings ("ground fault protection" alone, "ground fault test", "per 7.14") are NEVER device tokens; they are role/scope evidence only.
2. **Hard parent exclusion (the load-bearing guard).** If a row `looksLikeBreaker` (frame/hint) or matches `NON_BREAKER`, GFP does NOT fire - EVEN with `candidateKind:'gfp'`. The ground-fault burden of that parent is already in its ref (breaker `LSIG` vs `LS/LSI`; ATS/SPD/etc. carry their own function or are out of V1). The exclusion is checked BEFORE the `candidateKind` honor, so a parent-shaped row can never reach `assessGfp`. (A standalone GFP device that genuinely co-locates with a parent on one extracted row is not representable in V1's one-`candidateKind`/one-`tag` extraction schema -> V2.)
3. **Routing precedence.** `assessCore` order is `transformer -> GFP -> relay -> NON_BREAKER -> breaker`. GFP precedes relay so a dedicated `GROUND FAULT RELAY` becomes a standalone GFP, not a generic relay. But because `looksLikeGfp` already hard-excludes parent shapes, GFP only ever fires on a clean standalone row; routing order matters solely for the GFP-vs-relay carve-out.
4. **Voltage is optional/contextual.** A GFP device carries an optional bus-voltage context for provenance/display, but voltage never gates recognition and the GFP assess path must not emit `missing_voltage`. (GFP is LV-by-definition in V1; the ref is "... LV".)
5. **Never auto-price; SINGLE ref.** A recognized standalone GFP device is `scope_pending` with `candidateRefs = ['Ground Fault Protection Device LV']` and `provisionalDefaultRef =` the same single ref (a one-click Gate-2 confirm, not a tier choice). No candidate GROUP, no GFP `catalog_gap` in V1.
6. **Breaker + transformer + relay paths untouched.** `ApparatusSignature` is a discriminated union on `kind`; every other-family-field reader narrows on `kind`; a GFP signature can never reach `matchBreaker`/`matchTransformer`/`matchRelay` or a priced line. The widen forces a `gfp` branch in `specKey` and the emit match loop (compiler-enforced).

## Component Design (engine seams, grounded @ ab43c569)

### 1. Extraction (`extraction/types.ts`, `extraction/parse.ts`)
- `extraction/types.ts:15`: widen `candidateKind?: 'breaker' | 'transformer' | 'relay'` to `... | 'gfp'`. Add a comment: `'gfp'` = producer asserts a STANDALONE ground-fault protection device (not a mere ground-fault mention; honored only on a non-parent-shaped row).
- `extraction/parse.ts:58`: widen the validation guard to accept `'gfp'`; update the expected-string message to `'breaker'|'transformer'|'relay'|'gfp'`. No other extraction change.

### 2. Signature types (`signature/types.ts`)
- `BaseSignature.voltageClass` is already optional (post-relay) - no change; GFP inherits the optional voltage, so a GFP device is never voltage-gated.
- Add `export interface GfpSignature extends BaseSignature { kind: 'gfp'; ansiFunctions?: string[] }`. (No breaker/transformer/relay fields - the family-leak guard. `model` omitted in V1; `ansiFunctions` is evidence/display only.)
- `export type ApparatusSignature = BreakerSignature | TransformerSignature | RelaySignature | GfpSignature`.

### 3. Recognition + parse (`signature/normalize.ts`) - standalone-only, hard parent exclusion
- `GFP_DEVICE` token (ASCII regex, DEVICE NOUNS only - not function/scope phrasings): `/\b(GFPE?|GFR|ground[\s-]?fault\s+(relay|sensor|monitor|module|system|device|unit)|ground[\s-]?fault\s+protection\s+(system|device|unit|relay|module|panel))\b/i`. This deliberately does NOT match: a bare ANSI ground function (50G/51G/64), the trip-function letter `G`, bare "ground fault protection" (function name), "ground fault test", or "per 7.14".
- `looksLikeGfp(x): boolean` - parent exclusion FIRST, then candidateKind, then token:
  - `if (looksLikeBreaker(x.raw)) return false`   // breaker GF burden is in its LSIG ref - operator test #1; overrides candidateKind
  - `if (NON_BREAKER.test(x.raw)) return false`   // ATS/MTS/SPD/PDU/UPS GF function stays with that device; overrides candidateKind
  - `if (x.candidateKind === 'gfp') return true`   // producer asserts a STANDALONE GFP device (row is not parent-shaped)
  - `return GFP_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0`
- `assessGfp(x, voltageBasis?): ApparatusAssessment`: build `GfpSignature` with `ansiFunctions = parseAnsiFunctions(x.raw)` (reuse the existing parser; evidence only), `voltageClass = classifyVoltage(x.busVoltageV)` (MAY be undefined - NOT gated; no `missing_voltage`), `voltageV`, `voltageBasis` derived `detected`/`none`, `tag`, `source`. `assessmentCode: 'gfp_recognized'`. NO `FRAME_TRIP`/conflict guard: `looksLikeGfp` already hard-excludes any breaker-shaped row (FRAME_TRIP is breaker-specific notation a standalone GFP device does not carry), so `assessGfp` is only ever reached for a clean standalone row. The invariant is pinned by a test (`candidateKind:'gfp'` + `AF/AT` -> no GFP line), not by a runtime conflict code.
- `assessCore` order: insert `if (looksLikeGfp(x)) return assessGfp(x, voltageBasis)` BETWEEN the `looksLikeTransformer` block and the `looksLikeRelay` block. GFP MUST precede relay (a dedicated `GROUND FAULT RELAY` carries the `RELAY` token and would otherwise be claimed by `looksLikeRelay`).
- New `AssessmentCode` member: `gfp_recognized` (only - no conflict code).

### 4. Match (`catalog/gfp-map.ts` + `catalog/gfp-map.data.ts`) - single ref, R1 provisional
- `gfp-map.data.ts`:
  - `export const GFP_REF = 'Ground Fault Protection Device LV'` (VERBATIM from the estimator-core seed; string-keyed match).
  - `export const GFP_R1_RATIFIED = false` (the single-ref-covers-all convention is provisional until the SME confirms GFPE/sensor/GF-relay pricing - D1).
- `gfp-map.ts`:
  - `export interface GfpScopeMatch { group: string[]; defaultRef: string; scopeQuestion: string }` (`defaultRef` always set - the single ref).
  - `const SCOPE_Q = 'Confirm this standalone ground-fault protection device/system is in test scope (NETA 7.14); it is priced per device, separate from any breaker/ATS ground-fault trip function (which is carried by the parent ref).'`
  - `export function matchGfp(_sig: GfpSignature): GfpScopeMatch { return { group: [GFP_REF], defaultRef: GFP_REF, scopeQuestion: SCOPE_Q } }` - always returns the single-ref scope match (no `null`/`catalog_gap` in V1).

### 5. Quantify (`quantify/quantify.ts`)
- Add an explicit `s.kind === 'gfp'` branch to `specKey` BEFORE the transformer fall-through (the fall-through reads `s.coolant`/`s.kvaRating`, absent on `GfpSignature` - the widen makes this a compile error until the branch is added): `return [s.kind, s.voltageClass ?? '-', s.source.block ?? '-'].join('|')`. (ANSI evidence is NOT in the key: two GFP devices that differ only in evidence still map to the one ref - qty aggregates correctly.)
- `deviceId` already kind-prefixes (`gfp:TAG`) - no change.
- `pickAuthoritative` needs NO GFP-specific change: GFP has no richness gradient, so the existing `richBreaker`/`richRelay` finds skip a GFP bucket and `auths[0]` is correct.

### 6. Disposition + contract (`buckets/types.ts`, `emit/emit.ts`, `runner/run.ts`, `runner/report.ts`)
- `buckets/types.ts`: add `OperatorQuestionCode += 'gfp_scope_pending'`; `DispositionReasonCode += 'gfp_scope_pending'`. NO `gfp_catalog_gap` (no V1 gap path), NO `gfp_breaker_conflict` (unreachable under the hard exclusion). `ScopePendingLine` already supports the GFP shape (`provisionalDefaultRef?`, `r1Ratified`) - no change. `TakeoffFinding.code` unchanged.
- `emit/emit.ts`:
  - Import `matchGfp` (`../catalog/gfp-map`), `GFP_R1_RATIFIED` (`../catalog/gfp-map.data`), and the `GfpSignature` type.
  - Add `if (sig.kind === 'gfp') { ... continue }` in the per-line match loop BEFORE the transformer fall-through (after the breaker and relay branches; required so the `const tsig: TransformerSignature = sig` narrowing still holds). The branch: `const gsig: GfpSignature = sig; const scope = matchGfp(gsig)`; push a `ScopePendingLine` with `candidateRefs: scope.group`, `provisionalDefaultRef: scope.defaultRef`, `r1Ratified: GFP_R1_RATIFIED`, `scopeQuestion: scope.scopeQuestion`, `qty: line.qty`, `block: gsig.source.block ?? gsig.source.sheet`, `line`; for each `memberIndex` `stamp(... 'scope_pending', 'gfp_scope_pending', scope.scopeQuestion, undefined, line.lineKey)` and set `disp.candidateRefs`/`disp.provisionalDefaultRef`/`disp.scopeQuestion`; `questions.push({ question: scope.scopeQuestion, context: '<tag> (standalone GFP; priced per device; NETA 7.14)', code: 'gfp_scope_pending' })`.
  - **Update the compiler-checked `ASSESS_TO_REASON` map** for the new member `gfp_recognized: 'gfp_scope_pending'` (unreachable - has signature; present for exhaustiveness). (Adding the member forces this; a NAMED task with its own test, per the relay/transformer laundering-cast precedent.)
- `runner/run.ts`: no change - scope_pending-only / partial_preview handling is family-agnostic; a GFP-only extraction becomes `partial_preview` (confirmed by a test).
- `runner/report.ts`: no change - `scopePending` rendering is family-agnostic; a GFP scope_pending line renders `provisional=Ground Fault Protection Device LV` (confirmed by a test).

## Recognition signal (the crux, expanded) - operator-pinned cases under the standalone-only model

Standalone-only, hard parent exclusion (D3 + Rev 2). The cases:

1. **`800AF/800AT LSIG` (+ "ground fault protection" text) -> breaker ONLY (no GFP line).** `looksLikeGfp` returns false at the first guard (`looksLikeBreaker` true via FRAME_TRIP) - even before any token/candidateKind check. The row is priced as `Circuit Breaker LV - ... (LSIG)`; that ref already carries the ground-fault burden. No GFP line, no conflict.
2. **dedicated `GROUND FAULT RELAY` (+ tag, standalone) -> GFP.** Not breaker-shaped, not NON_BREAKER, `GFP_DEVICE` matches `ground fault relay` (device noun), tag present -> standalone GFP. GFP precedes relay so the `RELAY` token does not steal it.
3. **`SEL-751 50G 51G` (+ tag) -> relay; only a dedicated standalone GFP device -> GFP.** `GFP_DEVICE.test('SEL-751 50G 51G')` is false (no device-noun GFP token; `50G`/`51G` are ANSI elements) -> not GFP -> `looksLikeRelay` (SEL model + tag) -> relay. A relay merely carrying a ground ELEMENT stays a relay. Only if the row is explicitly a standalone GFP device (e.g. `... GROUND FAULT RELAY`/`GROUND FAULT PROTECTION SYSTEM`) does GFP claim it.
4. **bare ANSI ground functions / function text -> NO counted device.** `50G`/`64`/"ground fault test"/"per 7.14"/bare "ground fault protection" with no device-noun token and no anchor -> `looksLikeGfp` false, `looksLikeRelay` false, not NON_BREAKER, not breaker -> `unrecognized_apparatus_row`. Not counted as any device; function/scope text is parent evidence only.
5. **`candidateKind:'gfp'` + `###AF/###AT` frame -> NO GFP line (parent exclusion overrides candidateKind).** The `looksLikeBreaker` guard returns false before the `candidateKind` honor; the row routes to the breaker path. This pins the contract that `candidateKind:'gfp'` is honored ONLY on a non-parent-shaped row.
6. **`ATS ... GROUND FAULT PROTECTION SYSTEM` (or with `candidateKind:'gfp'`) -> NOT GFP (stays `non_breaker_excluded`).** The `NON_BREAKER` guard returns false before any token/candidateKind check. An embedded ATS ground-fault function is parent evidence; it does not produce a GFP line in V1.

## R1 (estimating authority) - provisional

`GFP_R1_RATIFIED = false`. Unlike relays (where R1 is a role->tier MAP), GFP's R1 is the single-ref-covers-all CONVENTION: the one priced ref covers every standalone GFP device in V1. Surfaced on the scope_pending line as `r1Ratified:false` (a Gate-2 provisional, never authoritative). GFP never auto-prices, so this is fail-closed. The SME confirms whether a dedicated GFPE / ground-fault relay / ground-fault sensor ever prices differently from the one "device" ref (D1); if so, those become catalog gaps in a later slice and `GFP_R1_RATIFIED` flips when the convention is confirmed.

## Testing (TDD; operator-pinned tests in bold)

- **operator #1 - breaker stays breaker (hard exclusion):** `800AF/800AT LSIG` (and a variant that literally includes "GROUND FAULT PROTECTION" text) -> a breaker matched line; NO GFP line, NO gfp disposition. Breaker golden byte-identical.
- **operator #2 - dedicated standalone GFP -> GFP:** `GROUND FAULT RELAY` + tag, and `GROUND FAULT PROTECTION SYSTEM` + tag -> `scope_pending` GFP line (single ref, provisional default = the ref).
- **operator #3 - relay element stays relay:** `SEL-751 50G 51G` + tag -> relay disposition (NOT GFP); `SEL-751 ... GROUND FAULT RELAY` + tag -> GFP (explicit standalone device).
- **operator #4 - bare ANSI / function text non-count:** `50G` / `64` / "perform ground fault test per 7.14" / bare "ground fault protection" with no device-noun token -> `unrecognized_apparatus_row` (or stays parent), NOT a GFP device.
- **parent exclusion overrides candidateKind (breaker):** `candidateKind:'gfp'` + `400AF/400AT` -> NO GFP line; routes to breaker. Proves candidateKind is honored only on non-parent rows.
- **parent exclusion overrides candidateKind (NON_BREAKER):** `candidateKind:'gfp'` on an `ATS ... GROUND FAULT PROTECTION` row -> NOT a GFP device (stays `non_breaker_excluded`).
- **no-voltage GFP:** a standalone GFP device with no `busVoltageV` -> GFP `scope_pending`, NEVER `missing_voltage`.
- **exact-ref validation:** `GFP_REF` exists VERBATIM in the live estimator-core seed (string-keyed match safety); matching keys on the string, not "7.14" (which the firm catalog overloads onto CT refs).
- **single-ref disposition:** a recognized standalone GFP device -> `scope_pending` with `candidateRefs=[GFP_REF]` and `provisionalDefaultRef=GFP_REF`; the reconciliation report renders `provisional=Ground Fault Protection Device LV`.
- **quantify:** two standalone GFP devices (different tags, same block) aggregate to one line `qty=2`; a GFP and a breaker/relay sharing a tag are NOT cross-bucketed (kind-prefixed deviceId).
- **cross-family guards:** a GFP signature can never reach `matchBreaker`/`matchTransformer`/`matchRelay`; a breaker/relay/transformer row never produces a GFP line.
- **ASSESS_TO_REASON:** a test that `gfp_recognized` maps to its reason code (the compiler-checked map).
- **runner:** a GFP-only extraction -> `partial_preview`; GFP scope_pending carried in the report.
- **breaker AND transformer AND relay goldens byte-identical.**
- **golden:** a real service-main one-line fixture (a standalone GFP system with a tag + a breaker-with-LSIG + a feeder relay coexist) -> breaker prices, relay scope_pending, GFP scope_pending; `partial_preview`; a Gate-2 stand-in confirms the GFP ref and prices it via estimator-core. The breaker-with-LSIG row in this fixture proves the embedded-GFP-stays-parent rule end-to-end.

## Out of scope (V2)

- Intra-row parent+standalone separation (a standalone GFP device co-located with a breaker/ATS on ONE extracted row) - needs an extraction-schema change to carry a separate standalone-device signal; V1 requires the standalone GFP device to be its own row.
- MV/HV ground-fault schemes priced differently (none in catalog today); zone-interlocking / multi-zone GFP systems if the firm prices per-zone; GFPE-vs-GFP service distinctions if the SME separates them (D1 may surface a catalog gap); network-protector ground relays (also a relay-family V2 defer).
- Auto-price-on-confident-recognition (D2 V2 optimization, after the recognizer is field-proven); the Gate-2 resolution UI; coupling to any live ground-fault device catalog for model hinting.
