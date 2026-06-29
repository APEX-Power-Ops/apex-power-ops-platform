# Estimator-Takeoff Transformer Family - Design Spec (V1)

Date: 2026-06-28. Status: DESIGN (post-packet; operator ratified D1-D4). Author: CC.
Lane: `estimator-takeoff/family-admission` (host worktree `apex-family-admission`, rebased onto main `6231f2b4`).
Packet (doctrine + grounding): `docs/superpowers/packets/estimator-takeoff-family-transformers.md`.
Feeds: `docs/superpowers/plans/2026-06-28-estimator-takeoff-transformer-family.md` (writing-plans next).
Grounded against current `origin/main` source (see Part 3 for the verified shapes).

## Goal

Admit the TRANSFORMER apparatus family into `packages/estimator-takeoff` as a bounded V1 slice, with the breaker engine's contract-first / fixture-driven / fail-closed rigor. V1 recognizes POWER transformers (dry-type + pad-mount oil) from a drawing extraction artifact, attributes them, and routes each to a SCOPE-PENDING operator decision carrying a candidate priced-ref GROUP. The engine NEVER auto-prices a transformer from drawing labels.

## Architecture

Transformers are the first SCOPE-DRIVEN family (vs the breaker's signature-deterministic model): the drawing yields the apparatus + physical attributes, but the priced ref depends on the test SCOPE the client/spec requires, which the drawing does not carry. So the match is `signature -> candidate ref-GROUP + default tier + scope question`, resolved later at Gate-2, never auto-priced.

Admitting the family is also the moment the engine grows a minimal FAMILY-DISPATCH (the generalization seam the readiness audit flagged): `ApparatusSignature` becomes a discriminated union on `kind`; recognition routes a transformer-recognized row to `assessTransformer`; the match step dispatches `match(sig)` on `sig.kind`; and the breaker-field consumers (`quantify.specKey`, `emit` line/envelope build) narrow on `kind`. The breaker path stays behaviorally identical (regression-guarded).

## Tech stack

TypeScript, `packages/estimator-takeoff` (pnpm workspace, vitest, Node 20, builds/tests on the Olares host). Imports `@apex/estimator-core` for the priced catalog (`equipment-models.seed.json`, 120 refs incl. the transformer family). The Python `drawing-nav` producer may stamp `candidateKind: 'transformer'`; the engine re-parses attributes from `raw` (producer stays a thin collector).

## Global constraints (every task inherits these)

- FAIL-CLOSED: unknown / ambiguous -> operator question; never a fabricated priced line.
- NEVER auto-price a transformer from drawing signature alone (D2). A transformer is `scope_pending` until a tier is chosen at Gate-2.
- EXISTING catalog refs only (D1). A recognized transformer that no priced ref-group covers -> a surfaced `catalog_gap` finding + question; NEVER a fabricated `custom_equipment` line and NEVER new authored hours.
- BREAKER behavior untouched. A regression test asserts the breaker golden envelope is byte-identical before/after.
- accounting-before-pricing: the takeoff emits `ref + qty` only; `estimator-core.compile` resolves `ref_hours` + M4 + labor + rates. No engine path originates a transformer price.
- ASCII-only in engine-emitted strings (questions / findings / envelope notes) - they surface into reports (lane discipline; prior runner slice was bitten by em-dash/ellipsis in `q()` strings).
- Voltage TAKEOFF routing convention unchanged: LV <1kV / MV 1kV-69kV / HV >69kV (`classifyVoltage` reused).

## Ratified decisions (operator, 2026-06-28)

| # | Decision | Resolution |
|---|---|---|
| D1 | Catalog completeness | Use EXISTING refs for V1. Engine emits a `catalog_gap` finding where no ref-group covers a recognized transformer. NO new hours; the dry size-split (NETA 7.2.1.1 vs 7.2.1.2) + substation non-pad-mount liquid ref are recorded as candidate gaps, not V1 blockers. |
| D2 | Match model | SCOPE-DRIVEN ratified: candidate ref-GROUP + default ATS tier, resolved at Gate-2; never auto-priced. Engine does NOT choose between TTR/IR, WR/PF, LTC, oil-sample, IR-scan unless scope is explicitly supplied. |
| D3 | V1 sub-type scope | Power transformers only: dry-type + pad-mount oil. DEFER instrument transformers (CT/VT/CCVT/PT) and Power-HV/MV-w/-LTC to V2. |
| D4 | NETA-section reconciliation | DEFER to the Gate-2 NETA-threading slice. The firm-section drift is RECORDED (packet Part 2); add a future reconciliation item. |

## Part 1 - V1 recognition + attribution (the family's "signature")

A transformer is recognized POSITIVELY (today `TX|XFMR|KVA` sit in `normalize.ts:8 NON_BREAKER` and are excluded). V1 inserts a transformer branch in `assessCore` BEFORE the NON_BREAKER exclusion:

- Recognition (EVIDENCE-GATED - bare `KVA` must NOT create a candidate): a row is transformer-recognized iff it carries equipment-like evidence - (a) producer `candidateKind === 'transformer'` (authoritative), OR (b) a transformer DEVICE token `TRANSFORMER_DEVICE = /\b(XFMR|transformer|dry.?type|pad.?mount|oil.?filled)\b/i`, OR (c) a kVA RATING pattern `/(?<!\w)\d+(?:\.\d+)?\s*kVA\b/i` (a NUMBER + kVA) PAIRED WITH a tag/designation. A bare `KVA` word with no rating number and no device token (load summaries, notes, schedules) is NOT a transformer candidate. `TX|XFMR` are REMOVED from `NON_BREAKER` (now recognized via the device token) and the bare `KVA` token is REMOVED too (recognition is rating-pattern-gated, not word-gated); the remaining NON_BREAKER tokens (`PDU|UPS|STS|ATS|MTS|SPD|PQM|METER|BUS DUCT`) are unchanged. (Recognition precision is regression-tested with real load-summary/note rows that contain `kVA` but are NOT transformers.)
- Conflict guard (fail-closed): a row that is transformer-recognized AND carries a breaker `FRAME_TRIP` rating -> an operator question (`transformer_breaker_conflict`), not a fabricated line of either kind. Mirrors the existing `non_breaker_carries_rating` guard.
- Attribution (text-only, fail-closed; absent evidence -> question, never invented):
  - `parseKva(raw)`: kVA rating. (Golden caught `30KVA` mis-read as `30kV` previously - kVA vs kV disambiguation is a required test.)
  - `parseCoolant(raw)`: `dry` (dry-type / AA / ventilated) vs `liquid` (oil-filled / pad-mount / liquid) vs `unknown`.
  - `parsePadMount(raw)`, `parseLtc(raw)` (V1 records `ltc` only to route LTC out of V1 scope - an LTC-positive transformer surfaces as `scope_pending` with a "LTC deferred to V2" question, never matched).
  - Voltage via the reused `classifyVoltage(busVoltageV)`; missing voltage -> question (same as breakers).
- `assessTransformer(x, voltageBasis?)` returns the same `ApparatusAssessment` shape (`{ signature, questions, isBreakerShaped:false, assessmentCode }`), with new assessment codes (Part 3).

## Part 2 - The scope-driven match model

`matchTransformer(sig: TransformerSignature) -> { group: string[]; defaultRef: string; scopeQuestion: string } | null`:

- Returns a candidate ref-GROUP (the priced scope tiers for the recognized coolant/class) + a `defaultRef` (the firm's standard ATS tier for that coolant - a NAMED constant the operator/estimator confirms) + a human `scopeQuestion` for Gate-2. It NEVER returns a single auto-priced ref.
- `null` = no ref-group covers this transformer -> a `catalog_gap` (D1): surfaced as a question + a warning finding carrying the recognized attributes; NEVER fabricated. `catalog_gap` (recognized transformer, NO applicable existing ref-group - e.g. a sub-type with no priced ref) is DISTINCT from `scope_pending` (a ref-group APPLIES but the tier is unchosen). A recognized dry/oil transformer that matches a `TRANSFORMER_MAP` rule is ALWAYS `scope_pending`, never `catalog_gap`.
- `TRANSFORMER_MAP` (new `catalog/transformer-map.ts` + `.data.ts`, mirroring `breaker-map`) - V1 rule families keyed on coolant:
  - DRY: group = the 3 dry tiers (`Transformer - Dry Type (TTR/IR)` 1.25h / `(TTR/WR/IR)` 3h / `(TTR/IR/WR/PF)` 8h); `defaultRef` = the firm-standard dry ATS tier [CONFIRM with operator: lean mid `(TTR/WR/IR)`].
  - PAD-MOUNT OIL: group = the 2 oil tiers (`Transformer - Pad Mount Oil (TTR/WR/IR)` 4h / `(TTR/IR/WR/PF/Oil)` 12h); `defaultRef` = the firm-standard oil ATS tier [CONFIRM].
- Family dispatch: a new `match(sig)` selects `matchBreaker` (kind `breaker`, returns ref|null, auto-price path unchanged) vs `matchTransformer` (kind `transformer`, returns group+default, scope-pending path). The breaker `matchBreaker` signature and behavior are untouched.

## Part 3 - Engine seams, concrete against current source

Verified current shapes (`origin/main`):
- `signature/types.ts:16` `ApparatusSignature { kind:'breaker'; ... }` (single-member). -> becomes a discriminated union:
  - `BaseSignature { voltageClass; voltageV?; voltageBasis; tag?; inputIndex?; source }`
  - `BreakerSignature extends BaseSignature { kind:'breaker'; frameA?; tripA?; functions; mounting; mountingBasis; mvType? }`
  - `TransformerSignature extends BaseSignature { kind:'transformer'; kvaRating?; coolant:'dry'|'liquid'|'unknown'; padMount?; ltc? }`
  - `type ApparatusSignature = BreakerSignature | TransformerSignature`
- `signature/normalize.ts`: `assessCore` (line 80) gains the transformer branch (Part 1); new `assessTransformer`; `AssessmentCode` (line 61) gains `transformer_scope_pending | transformer_catalog_gap | transformer_breaker_conflict | transformer_attrs_unparsed` (the last for missing kVA/coolant -> question). `assessApparatus`/`assessResolvedApparatus` unchanged signatures.
- `catalog/breaker-map.ts`: unchanged. New `catalog/transformer-map.ts` (`matchTransformer`) + `transformer-map.data.ts` (`TRANSFORMER_MAP`). New `catalog/match.ts` (`match(sig)` family dispatch) consumed by `runTakeoff`.
- `quantify/quantify.ts:7` `specKey(s)` reads breaker-only fields (`mounting`, `mvType`, `functions`, `frameA`, `tripA`) -> narrow on `kind`: transformer `specKey` = `kind|voltageClass|voltageV|voltageBasis|kvaRating|coolant|padMount|ltc|block`. `pickAuthoritative` (line 23, reads `s.mounting`) narrows: for transformers, representative = first (no mounting axis). V1 `unit_of_issue` = `each` (instrument `set` deferred to V2 with the instrument family).
- `buckets/types.ts`: `ApparatusDispositionStatus` (line 23) gains `scope_pending`. `DispositionReasonCode` (line 30) gains `transformer_scope_pending | transformer_catalog_gap | transformer_breaker_conflict | transformer_attrs_unparsed`. `ApparatusDisposition` (line 41) gains optional `candidateRefs?: string[]` + `defaultRef?: string` (populated only for `scope_pending`, so the exhaustive dispositions array carries everything Gate-2 needs). `OperatorQuestionCode` (line 9) gains the matching codes. `TakeoffFinding.code` (line 66, currently `VoltageAssertionCode` only) generalizes to also admit `'transformer_catalog_gap'` (severity `warning`).
- `emit/emit.ts`: `runTakeoff` (line 46) match step calls `match(sig)` (dispatch) instead of `matchBreaker` directly. A transformer line resolves to a `scope_pending` disposition (stamp `scope_pending` / `transformer_scope_pending`, carry `candidateRefs`+`defaultRef`) + an `OperatorQuestion` (`transformer_scope_pending`) carrying the group; a `catalog_gap` -> `unmatched` + warning finding. `MatchedLine` build (line 107, reads `mountingBasis`) is breaker-only -> guarded by `kind === 'breaker'`. `emitEnvelope` (line 122): scope_pending + catalog_gap lines are NOT matched lines, so they never enter the priced envelope; the zero-matched throw (line 131) is unchanged (a transformer-only takeoff legitimately has 0 priced lines -> handled by the runner's partial_preview path, not an error).
- `runner/run.ts` + `runner/report.ts`: `reconcile` + `isClean` count `scope_pending` rows as UNRESOLVED (like questions) - a run with open scope-pending transformers is NEVER `isClean`; it surfaces as `partial_preview` listing the Gate-2 scope questions. Provenance/drift unchanged.

## Part 4 - Fail-closed invariants (asserted by tests)

1. A recognized transformer with complete attributes but no chosen tier -> `scope_pending`, 0 priced lines for it, a Gate-2 scope question carrying the candidate group + default. Never auto-priced.
2. A recognized transformer that no ref-group covers -> `catalog_gap` question + warning finding with attributes; never a `custom_equipment`/fabricated line; never new hours.
3. A transformer-recognized row that also carries a breaker frame/trip -> `transformer_breaker_conflict` question; neither a breaker nor a transformer line is fabricated.
4. Missing kVA AND coolant -> `transformer_attrs_unparsed` question; not guessed. (kVA is metadata-only and not match-critical; the tier is scope-driven, not kVA-driven. Unknown coolant alone already surfaces as a `catalog_gap` via matchTransformer returning null.)
5. LTC-positive (out of V1 scope) -> `scope_pending` with an explicit "LTC scope deferred to V2" note; never matched to the LTC ref.
6. The breaker golden envelope is byte-identical before/after this slice (regression guard).
7. Every artifact row still gets EXACTLY one disposition (`assertExhaustive` holds across the new `scope_pending` status).
8. A `transformer` signature can NEVER reach `matchBreaker` and NEVER become a priced breaker `MatchedLine` - enforced by `kind` narrowing (TS compiler) AND an explicit test (a transformer through `runTakeoff` produces 0 breaker lines and never calls `matchBreaker`). All breaker-only readers (`specKey`, `pickAuthoritative`, `emit` line/envelope build, the matcher call) narrow by `kind`; a non-narrowed reader is a compile error.
9. V1 runtime ALWAYS exports a recognized transformer as `scope_pending` (or `catalog_gap`); it NEVER emits a priced transformer line absent an EXPLICIT resolved-scope INPUT. V1 ships no such input path by default (operator scope-resolution input is the next slice / V2). The Part 5 priced proof is a Gate-2 STAND-IN, not a V1 product-pricing path.

## Part 5 - Golden + tests (TDD, mirroring the breaker engine)

- `test/normalize-transformer.test.ts`: recognition (hint + candidateKind), parseKva (incl. `30KVA` != 30kV), parseCoolant (dry vs oil/pad-mount), conflict guard, missing-attr questions, voltage routing.
- `test/transformer-map.test.ts`: dry -> 3-tier group + default; oil -> 2-tier group + default; uncovered -> null -> catalog_gap; family dispatch picks the right matcher per kind.
- `test/transformer-golden.test.ts`: a REAL one-line extraction fixture carrying a dry-type AND a pad-mount-oil transformer (plus at least one breaker, to prove the families coexist) -> both transformers land `scope_pending` with candidate groups; breaker prices unchanged; envelope is `partial_preview` surfacing the scope questions. THEN a second assertion is the Gate-2 STAND-IN: take a scope_pending line's chosen-tier ref + qty and feed it DIRECTLY to `estimator-core` (`buildNativeEnvelope`), asserting `bid_cents > 0`. This proves the accounting->pricing seam for the transformer refs WITHOUT building Gate-2 resolution into the V1 takeoff engine (the engine itself never emits a priced transformer line in V1; Part 3 / invariant 1). This is the flagship priced-seam + scope-resolution proof.
- `test/family-dispatch.test.ts` (invariant 8): a `transformer` signature NEVER reaches `matchBreaker` and NEVER yields a priced breaker `MatchedLine`; `match(sig)` routes strictly by `kind`; a transformer through the full `runTakeoff` pipeline produces 0 breaker lines.
- `test/transformer-catalog.test.ts` (validates against the LIVE `estimator-core` seed): every `TRANSFORMER_MAP` group ref RESOLVES (exists in the seed), no group is EMPTY, each `defaultRef` is a member of its own group, and a recognized transformer with no applicable rule yields `catalog_gap` (NOT `scope_pending`).
- Regression: the existing breaker golden runs unchanged and asserts byte-identical output.

## Part 6 - Out of scope (V2, recorded so it is not lost)

- Instrument transformers (CT / VT / CCVT / PT) and their `unit_of_issue:'set'` semantics (set-priced, usually bundled with switchgear).
- Power-HV/MV-w/-LTC matching + the Tap Changer / Oil Sample / IR-scan ADDER refs (V1 only routes LTC OUT).
- The Gate-2 UI that RESOLVES a `scope_pending` tier choice (this slice produces the scope-pending data + default; the resolution UI is a separate Gate-2 slice).
- NETA firm-section -> canonical reconciliation (D4 deferred; drift recorded in the packet).
- drawing-nav transformer EXTRACTION precision (the producer may stamp `candidateKind`; deep transformer one-line parsing is a parallel producer slice). V1 engine works from `raw` + optional `candidateKind`.

## Part 7 - Risks / open items

- R1 (BLOCKING for implementation; non-blocking for design) - the two `defaultRef` constants (dry + oil firm-standard ATS tier) are an estimating-AUTHORITY call. Plan Task 1 (catalog-authority) either pins the RATIFIED defaults or encodes them as explicit FAIL-CLOSED placeholders that FAIL the catalog tests until ratified - never a quiet test-baked default. SETTLE R1 (confirm the two tiers) BEFORE SDD starts. Lean: mid dry `(TTR/WR/IR)`, mid oil `(TTR/WR/IR)`.
- R2 - Carving `TX|XFMR|KVA` out of `NON_BREAKER` must not regress any breaker row that incidentally contains `KVA`. Mitigated by: transformer recognition requires a transformer hint AND the conflict guard routes a frame/trip-bearing row to a question. Covered by a regression test.
- R3 - The discriminated-union refactor touches every breaker-field reader (`specKey`, `pickAuthoritative`, `emit` line/envelope build). Bounded + compiler-enforced (TS narrows); the breaker golden regression is the backstop.

## Part 8 - Decomposition preview (-> writing-plans)

Bounded V1 slice, ~8 TDD tasks mirroring the breaker engine: (1) CATALOG-AUTHORITY - pin the dry/oil default-ref tiers (R1) or fail-closed placeholders + the live-seed group-validation tests (every group ref resolves, no empty group, defaultRef in group); (2) signature discriminated-union refactor + breaker-regression guard + family-dispatch guard (transformer never reaches matchBreaker); (3) evidence-gated transformer recognition + NON_BREAKER carve-out + conflict guard; (4) attribute parsers (kVA-rating/coolant/padMount/ltc) + assessTransformer; (5) transformer-map (group + default) + `match(sig)` dispatch; (6) quantify/specKey kind-narrow; (7) scope_pending disposition + catalog_gap finding threaded through runTakeoff/emit + runner/reconcile scope_pending = unresolved + partial_preview; (8) real golden (dry + oil + breaker coexist) + the labeled Gate-2 stand-in priced proof. R1 settled before SDD. Cross-engine (Codex) IRP before merge; merge operator-gated.
