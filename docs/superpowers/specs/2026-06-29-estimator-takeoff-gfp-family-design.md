# Estimator-Takeoff Ground-Fault Protection Device (LV) Family (V1) - Design

Status: SPEC (operator-ratified packet 003; folds D1-D4 + the operator's Part 9 spec-phase directives: strong-anchor exclusion as the load-bearing guard, 4 pinned regression tests). Date: 2026-06-29.
Lane: estimator-takeoff/gfp-family-admission (off main ab43c569). Dev-only; merge operator-gated.
Packet: docs/superpowers/packets/estimator-takeoff-family-gfp.md (Part 6 decisions + Part 9 ratification).
Predecessors (reused, must stay byte-identical): breaker engine (signature-deterministic) + transformer slice (scope_pending machinery, PR #49) + relay slice (device-first recognition, cross-family guards, PR #50).

**Goal:** Admit the GROUND-FAULT PROTECTION DEVICE (LV) family into `packages/estimator-takeoff` as a bounded V1 slice - a recognition-gated, SINGLE-ref family - so a recognized standalone GFP device is counted per device and routed to a one-click Gate-2 scope confirmation, never auto-priced, with breaker / transformer / relay behavior untouched and no breaker/ATS ground-fault FUNCTION ever double-counted as a GFP device.

**Architecture:** Reuse the relay/transformer scope_pending machinery (discriminated-union signature, `scope_pending` disposition with optional `provisionalDefaultRef`, R1-provisional flag, kind-prefixed `deviceId`, cross-family routing). Add a fourth signature `kind: 'gfp'`, a strong-anchor device-first GFP recognizer, and a trivial one-ref match. GFP differs from the prior scope-driven families in two engine-visible ways: (1) the accounting layer is a SINGLE priced ref, so there is no tier ambiguity and no candidate GROUP - `matchGfp` always returns the one ref as both the only candidate and the provisional default (a confirm gate, not a choice), and there is no V1 `catalog_gap`/`null` path; (2) recognition is the entire difficulty and is fail-closed against FALSE POSITIVES - `looksLikeGfp` requires a DEDICATED GFP device token and yields outright to breaker-shaped and NON_BREAKER rows, so a ground-fault TRIP FUNCTION embedded in a breaker/ATS/SPD stays with its parent.

**Tech stack:** TypeScript, Vitest, pnpm workspace; host build over `ssh olares-mesh`.

## Global Constraints

- **ASCII-only** in all authored SQL/comments AND engine-emitted strings (questions, findings, scope questions, notes). Verbatim source DATA may be UTF-8. (No em-dashes in engine strings.)
- **Breaker AND transformer AND relay goldens byte-identical** after every task. Three prior families now regression-guard the fourth.
- **No new catalog refs and no new hours.** V1 uses the single existing NETA-7.14 ref `Ground Fault Protection Device LV` only (D1 V1-policy). Matched by exact ref STRING, never by section (firm "7.14" is overloaded with CT refs).
- **GFP never auto-prices.** Every recognized GFP device -> `scope_pending` (single ref as provisional default + a confirm question). There is no "matched" GFP line and no GFP `catalog_gap` in V1.
- **Recognition is fail-closed against false positives.** A ground-fault function on a breaker (hasG/LSIG) or a NON_BREAKER device (ATS/MTS/SPD/PDU/UPS/...) is NEVER a GFP device. Only a dedicated standalone GFP device token (+ tag) or an explicit `candidateKind:'gfp'` produces a GFP line.
- **Gates (verified on host):** `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (the cross-package gate; `--filter apex-operations-web` matches NOTHING - false-green trap).
- **Cross-engine (Codex) IRP** before merge; merge operator-gated (admin-rebase PR).
- **R1 (estimating authority) stays PROVISIONAL** (`GFP_R1_RATIFIED=false`) until the SME confirms the single-ref-covers-all convention (D1: whether GFPE / dedicated GF-relay / sensor variants ever price differently). GFP never auto-prices, so provisional is safe.

## The V1 Contract

1. **Recognize GFP devices positively, DEVICE-FIRST, with a STRONG anchor.** A GFP device is established by either a producer `candidateKind:'gfp'` OR a DEDICATED GFP device token (`GFP`/`GFPE`/`GFR`/`GROUND FAULT RELAY|SENSOR|MONITOR|PROTECTION|DEVICE|SYSTEM`) together with a device identity (tag). The token path additionally requires the row to be NEITHER breaker-shaped NOR a NON_BREAKER device. ANSI ground-fault function numbers (50G/51G/50N/51N/64) are parsed ONLY as role/evidence attributes of an established GFP device; a bare ANSI number with no device anchor is NEVER counted (falls through to `unrecognized_apparatus_row`).
2. **Routing precedence + the load-bearing exclusion.** `assessCore` order is `transformer -> GFP -> relay -> NON_BREAKER -> breaker`. GFP precedes relay so a dedicated `GROUND FAULT RELAY` becomes GFP, not a generic relay. But routing order is NOT the guard: the guard is the `looksLikeGfp` exclusion (`!looksLikeBreaker && !NON_BREAKER`), which keeps a breaker/ATS/SPD ground-fault FUNCTION out of the GFP family regardless of order. A breaker with `LSIG` (hasG) stays a breaker and is priced as a breaker; GFP emits no line for it.
3. **Voltage is optional/contextual.** A GFP device carries an optional bus-voltage context for provenance/display, but voltage never gates recognition and the GFP assess path must not emit `missing_voltage`. (GFP is LV-by-definition in V1; the ref is "... LV".)
4. **Never auto-price; SINGLE ref.** A recognized GFP device is `scope_pending` with `candidateRefs = ['Ground Fault Protection Device LV']` and `provisionalDefaultRef =` the same single ref (a one-click Gate-2 confirm, not a tier choice). There is no candidate GROUP and no GFP `catalog_gap` in V1 (recognition is the gate; a recognized GFP device always maps to the one ref).
5. **Breaker + transformer + relay paths untouched.** `ApparatusSignature` is a discriminated union on `kind`; every other-family-field reader narrows on `kind`; a GFP signature can never reach `matchBreaker`/`matchTransformer`/`matchRelay` or a priced line. The widen forces a `gfp` branch in `specKey` and the emit match loop (compiler-enforced).

## Component Design (engine seams, grounded @ ab43c569)

### 1. Extraction (`extraction/types.ts`, `extraction/parse.ts`)
- `extraction/types.ts:15`: widen `candidateKind?: 'breaker' | 'transformer' | 'relay'` to `... | 'gfp'`.
- `extraction/parse.ts:58`: widen the validation guard to accept `'gfp'` and update the expected-string message to `'breaker'|'transformer'|'relay'|'gfp'`. No other extraction change.

### 2. Signature types (`signature/types.ts`)
- `BaseSignature.voltageClass` is already optional (post-relay) - no change; GFP inherits the optional voltage (never re-declared required), so a GFP device is never voltage-gated.
- Add `export interface GfpSignature extends BaseSignature { kind: 'gfp'; ansiFunctions?: string[] }`. (No breaker/transformer/relay fields - the family-leak guard. `model` is intentionally omitted in V1; ansiFunctions is evidence/display only.)
- `export type ApparatusSignature = BreakerSignature | TransformerSignature | RelaySignature | GfpSignature`.

### 3. Recognition + parse (`signature/normalize.ts`) - strong-anchor device-first
- `GFP_DEVICE` token (ASCII regex, dedicated devices only): `/\b(GFPE?|GFR|ground[\s-]?fault\s+(relay|sensor|monitor|protection|device|system))\b/i`. This deliberately does NOT match a bare ANSI ground function (50G/51G/64) or the trip-function letter `G`.
- `looksLikeGfp(x): boolean`:
  - `if (x.candidateKind === 'gfp') return true` (explicit producer signal wins).
  - `if (looksLikeBreaker(x.raw)) return false` (a breaker with a ground-fault function stays a breaker - operator test #1).
  - `if (NON_BREAKER.test(x.raw)) return false` (a ground-fault function on an ATS/MTS/SPD/PDU/UPS stays with that device).
  - `return GFP_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0` (dedicated token + device identity).
- `assessGfp(x, voltageBasis?): ApparatusAssessment`:
  - Conflict guard (mirrors `assessRelay`): `if (FRAME_TRIP.test(x.raw))` -> `signature: null`, `assessmentCode: 'gfp_breaker_conflict'`, question "Label names a GFP device but carries a breaker frame/trip rating - confirm device type before counting." (Reachable only via `candidateKind:'gfp'` on a frame row, since the token path already excludes breaker-shaped rows; defensive and consistent with the lane's fail-closed posture.)
  - Else build `GfpSignature` with `ansiFunctions = parseAnsiFunctions(x.raw)` (reuse the existing parser; evidence only), `voltageClass = classifyVoltage(x.busVoltageV)` (MAY be undefined - NOT gated; no `missing_voltage`), `voltageV`, `voltageBasis` derived `detected`/`none`, `tag`, `source`. `assessmentCode: 'gfp_recognized'`.
- `assessCore` order: insert `if (looksLikeGfp(x)) return assessGfp(x, voltageBasis)` BETWEEN the `looksLikeTransformer` block and the `looksLikeRelay` block. GFP MUST precede relay (a dedicated `GROUND FAULT RELAY` carries the `RELAY` token and would otherwise be claimed by `looksLikeRelay`). GFP follows transformer (established precedence; no real overlap).
- New `AssessmentCode` members: `gfp_recognized`, `gfp_breaker_conflict`.

### 4. Match (`catalog/gfp-map.ts` + `catalog/gfp-map.data.ts`) - single ref, R1 provisional
- `gfp-map.data.ts`:
  - `export const GFP_REF = 'Ground Fault Protection Device LV'` (VERBATIM from the estimator-core seed; string-keyed match).
  - `export const GFP_R1_RATIFIED = false` (the single-ref-covers-all convention is provisional until the SME confirms GFPE/sensor/GF-relay pricing - D1).
- `gfp-map.ts`:
  - `export interface GfpScopeMatch { group: string[]; defaultRef: string; scopeQuestion: string }` (`defaultRef` always set - the single ref).
  - `const SCOPE_Q = 'Confirm this standalone ground-fault protection device is in test scope (NETA 7.14); it is priced per device, separate from any breaker/ATS ground-fault trip function.'`
  - `export function matchGfp(_sig: GfpSignature): GfpScopeMatch { return { group: [GFP_REF], defaultRef: GFP_REF, scopeQuestion: SCOPE_Q } }` - always returns the single-ref scope match (no `null`/`catalog_gap` in V1).

### 5. Quantify (`quantify/quantify.ts`)
- Add an explicit `s.kind === 'gfp'` branch to `specKey` BEFORE the transformer fall-through (the fall-through reads `s.coolant`/`s.kvaRating`, which do not exist on `GfpSignature` - the widen makes this a compile error until the branch is added): `return [s.kind, s.voltageClass ?? '-', s.source.block ?? '-'].join('|')`. (ANSI evidence is NOT in the key: two GFP devices that differ only in evidence still map to the one ref - qty aggregates correctly.)
- `deviceId` already kind-prefixes (`gfp:TAG`), preventing cross-family bucketing - no change.
- `pickAuthoritative` needs NO GFP-specific change: GFP has no role/mounting richness gradient, so the existing `richBreaker`/`richRelay` finds skip a GFP bucket and `auths[0]` (first authoritative) is correct.

### 6. Disposition + contract (`buckets/types.ts`, `emit/emit.ts`, `runner/run.ts`, `runner/report.ts`)
- `buckets/types.ts`: add codes `OperatorQuestionCode += 'gfp_scope_pending' | 'gfp_breaker_conflict'`; `DispositionReasonCode += 'gfp_scope_pending' | 'gfp_breaker_conflict'`. NO `gfp_catalog_gap` (no V1 gap path). `ScopePendingLine` already supports the GFP shape (`provisionalDefaultRef?`, `r1Ratified`) - no change. `TakeoffFinding.code` unchanged (no GFP finding in V1).
- `emit/emit.ts`:
  - Import `matchGfp` (`../catalog/gfp-map`), `GFP_R1_RATIFIED` (`../catalog/gfp-map.data`), and the `GfpSignature` type.
  - Add `if (sig.kind === 'gfp') { ... continue }` in the per-line match loop BEFORE the transformer fall-through (after the breaker and relay branches; required so the `const tsig: TransformerSignature = sig` narrowing still holds). The branch: `const gsig: GfpSignature = sig; const scope = matchGfp(gsig)`; push a `ScopePendingLine` with `candidateRefs: scope.group`, `provisionalDefaultRef: scope.defaultRef`, `r1Ratified: GFP_R1_RATIFIED`, `scopeQuestion: scope.scopeQuestion`, `qty: line.qty`, `block: gsig.source.block ?? gsig.source.sheet`, `line`; for each `memberIndex` `stamp(... 'scope_pending', 'gfp_scope_pending', scope.scopeQuestion, undefined, line.lineKey)` and set `disp.candidateRefs`/`disp.provisionalDefaultRef`/`disp.scopeQuestion`; `questions.push({ question: scope.scopeQuestion, context: '<tag> (priced per device; NETA 7.14)', code: 'gfp_scope_pending' })`.
  - **Update the compiler-checked `ASSESS_TO_REASON` map** for the new `AssessmentCode` members: `gfp_recognized: 'gfp_scope_pending'` (unreachable - has signature; present for exhaustiveness) and `gfp_breaker_conflict: 'gfp_breaker_conflict'`. (Adding the members forces this; a NAMED task with its own test, per the relay/transformer laundering-cast precedent.)
- `runner/run.ts`: no change - the scope_pending-only / partial_preview handling (`result.scopePendingLines`) is family-agnostic; a GFP-only extraction becomes `partial_preview` exactly as a relay-only one does. (Confirmed by a test, not a code change.)
- `runner/report.ts`: no change - `scopePending` rendering is family-agnostic; a GFP scope_pending line renders with `provisional=Ground Fault Protection Device LV`. (Confirmed by a test.)

## Recognition signal (the crux, expanded) - the 4 operator-pinned cases

Device-first, strong-anchor (D3). Establish a DEDICATED GFP device, THEN read ANSI/voltage as attributes. The four operator-pinned regression cases and how the design resolves each:

1. **`800AF/800AT LSIG` + ground-fault text -> breaker ONLY (no GFP line).** `looksLikeGfp` returns false because `looksLikeBreaker` is true (FRAME_TRIP matches `800AF/800AT`). The row falls through to the breaker path and is priced as `Circuit Breaker LV - ... (LSIG)`. No GFP line; no conflict. The exclusion - not the routing order - is what holds this.
2. **dedicated `GROUND FAULT RELAY` -> GFP.** `looksLikeGfp`: not breaker-shaped, not NON_BREAKER, `GFP_DEVICE` matches `ground fault relay`, tag present -> GFP. Because GFP precedes relay in `assessCore`, the `RELAY` token does not steal it.
3. **`SEL`/relay + `50G/51G` -> remains relay UNLESS dedicated GFP wording present.** `looksLikeGfp`: `GFP_DEVICE.test('SEL-751 50G 51G')` is false (no dedicated GFP token; `50G`/`51G` are ANSI, not GFP device tokens) -> not GFP -> falls to `looksLikeRelay` (SEL model + tag) -> relay. If the same row also carries dedicated GFP wording (e.g. `... GROUND FAULT RELAY`), `GFP_DEVICE` matches and GFP (checked first) wins - exactly the "unless dedicated GFP wording present" carve-out.
4. **bare ANSI ground functions -> NO counted device.** A row whose `raw` is just `50G`/`51N`/`64` (no `candidateKind`, no GFP token, no relay/breaker anchor): `looksLikeGfp` false (no GFP token), `looksLikeRelay` false (no RELAY/model token), not NON_BREAKER, not breaker -> `unrecognized_apparatus_row`. Not counted as any device.

## R1 (estimating authority) - provisional

`GFP_R1_RATIFIED = false`. Unlike relays (where R1 is a role->tier MAP), GFP's R1 is the single-ref-covers-all CONVENTION: the one priced ref is asserted to cover every standalone GFP device in V1. It is surfaced on the scope_pending line as `r1Ratified:false` (a Gate-2 provisional, never authoritative). GFP never auto-prices, so this is fail-closed. The SME confirms whether a dedicated GFPE / ground-fault relay / ground-fault sensor ever prices differently from the one "device" ref (D1); if so, those become catalog gaps in a later slice and `GFP_R1_RATIFIED` flips when the convention is confirmed.

## Testing (TDD; operator-pinned tests in bold)

- **operator #1 - breaker stays breaker:** `800AF/800AT LSIG` (+ ground-fault text) -> a breaker matched line; NO GFP line, NO gfp disposition. Breaker golden byte-identical.
- **operator #2 - dedicated GFP -> GFP:** `GROUND FAULT RELAY` + tag -> `scope_pending` GFP line (single ref, provisional default = the ref).
- **operator #3 - relay stays relay unless dedicated GFP wording:** `SEL-751 50G 51G` + tag -> relay `scope_pending`/disposition (NOT GFP); `SEL-751 ... GROUND FAULT RELAY` + tag -> GFP.
- **operator #4 - bare ANSI non-count:** `50G` / `64` with no device anchor -> `unrecognized_apparatus_row`, NOT a GFP device.
- **no-voltage GFP:** a GFP device with no `busVoltageV` -> GFP `scope_pending`, NEVER `missing_voltage`.
- **exact-ref validation:** a test asserts `GFP_REF` exists VERBATIM in the live estimator-core seed (string-keyed match safety), and that the firm-section overload does not affect matching (we match the string, not "7.14").
- **NON_BREAKER exclusion:** an `ATS ... GROUND FAULT PROTECTION` row -> NOT a GFP device (stays `non_breaker_excluded`); proves the exclusion covers ATS/SPD/etc., not only breakers.
- **gfp_breaker_conflict:** `candidateKind:'gfp'` + a `###AF/###AT` frame -> `gfp_breaker_conflict` question, no GFP line.
- **single-ref disposition:** a recognized GFP device -> `scope_pending` with `candidateRefs=[GFP_REF]` and `provisionalDefaultRef=GFP_REF`; the reconciliation report renders `provisional=Ground Fault Protection Device LV`.
- **quantify:** two GFP devices (different tags, same block) aggregate to one line `qty=2`; a GFP and a breaker/relay sharing a tag are NOT cross-bucketed (kind-prefixed deviceId).
- **cross-family guards:** a GFP signature can never reach `matchBreaker`/`matchTransformer`/`matchRelay`; a breaker/relay/transformer row never produces a GFP line.
- **ASSESS_TO_REASON:** a test that the `gfp_recognized` / `gfp_breaker_conflict` codes map to their reason codes (the compiler-checked map).
- **runner:** a GFP-only extraction -> `partial_preview` (not clean, not zero-to-price); GFP scope_pending carried in the report.
- **breaker AND transformer AND relay goldens byte-identical.**
- **golden:** a real service-main one-line fixture (a standalone GFP system with a tag + a breaker-with-LSIG + a feeder relay coexist) -> breaker prices, relay scope_pending, GFP scope_pending; `partial_preview`; a Gate-2 stand-in confirms the GFP ref and prices it via estimator-core.

## Out of scope (V2)

MV/HV ground-fault schemes priced differently (none in catalog today); zone-interlocking / multi-zone GFP systems if the firm prices per-zone rather than per-device; GFPE-vs-GFP service distinctions if the SME separates them (D1 may surface a catalog gap); network-protector ground relays (also a relay-family V2 defer); auto-price-on-confident-recognition (D2 V2 optimization, after the recognizer is field-proven); the Gate-2 resolution UI; coupling to any live ground-fault device catalog for model hinting.
