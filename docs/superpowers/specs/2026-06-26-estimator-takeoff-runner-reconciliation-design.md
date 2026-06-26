# estimator-takeoff Runner + Reconciliation Seam — Design

**Status:** design for review. Branch `estimator-takeoff/runner-reconciliation` off `main` `827c83b2`.

## 1. Goal & context

Today `@apex/estimator-takeoff` is a library: `runTakeoff(artifact) → emitEnvelope() → priced envelope`, driven only by vitest. The 2026-06-26 readiness audit found the engine's internal seams solid but the **product path unsafe**: a real artifact can lose devices (untagged-bbox undercount, unmatched refs, dropped malformed rows) and **`emitEnvelope` reads only `matchedLines`** — `unmatchedCandidates` and `operatorQuestions` vanish at the emit seam — yet still produce a clean-looking priced envelope no test or log flags. In a NETA bid an undercount is direct lost revenue.

This slice builds the **reconciliation seam**: a runnable entry that consumes a *real* drawing-nav artifact, validates it at runtime, accounts for **every** input row with a structured disposition, refuses to present an envelope as clean while unresolved work exists, and asserts a real priced value. It is the piece worth building **before** SKILL.md — the skill must document a workflow that has survived real producer JSON, validation, reconciliation, and priced output.

## 2. What this slice is NOT (scope boundary, YAGNI)

- **Not** SKILL.md / orchestration (next slice, builds on this).
- **Not** the two human gates, spec-parser, or scope-profile (`§6.5/6.7/6.8` of the takeoff design — separate tracks).
- **Not** apparatus generalization (stays breaker-only; `kind:'breaker'`).
- **Not** multi-PDF / multi-revision composition (one artifact in).
- **Not** a drawing-nav rewrite — Python stays thin; the TS seam does the rejecting.
- **Not** new pricing logic — `buildNativeEnvelope` is reused unchanged.

## 3. Engine contract additions — structured `dispositions`

The core of the slice. Today the engine returns buckets but **per-row fate is not recoverable**: `operatorQuestions` are free-text `{question, context}` with the tag in prose, and exclusion reasons (NON_BREAKER, location-only) are unstructured. We add a **row-level, exhaustive** disposition keyed by `inputIndex` (NOT tag — tags duplicate, go missing, or join incorrectly; tag-only reconciliation would recreate the silent-loss class under a nicer label).

### 3.1 Types (`src/buckets/types.ts`)

```ts
export type ApparatusDispositionStatus =
  | 'matched'             // counted into a line that matched a catalog ref
  | 'associated_source'   // folded as a source/occurrence of a counted device (not its own line)
  | 'unmatched'           // counted into a line with no catalog rule
  | 'question'            // breaker-shaped but unresolved → needs an operator answer
  | 'ignored'             // explicit exclusion (non-breaker / not breaker-shaped)

export type DispositionReasonCode =
  | 'catalog_rule'                  // matched
  | 'occurrence_of_counted_device' // associated_source (sibling occurrence, had a signature)
  | 'unresolved_tag_attached'      // associated_source (no signature, tag matched a counted line)
  | 'no_catalog_rule'              // unmatched
  | 'missing_voltage'              // question
  | 'location_only_non_authoritative' // question
  | 'non_breaker_carries_rating'   // question — non-breaker token + breaker rating (mislabel risk; confirm device)
  | 'unrecognized_apparatus_row'   // question — a producer candidate row the engine cannot classify either way
  | 'non_breaker_excluded'         // ignored — the ONLY safe-to-ignore case (positively a non-breaker device)
// INVARIANT (anti-silent-loss): `ignored` is, by construction, EXCLUSIVELY
// `non_breaker_excluded` — a positively-identified non-breaker device token.
// Every ambiguous or unclassifiable producer row (carries-rating, or not
// breaker-shaped at all) is a `question`, NOT ignored, so it blocks clean
// output (§5.2). A producer contract drift that drops `candidateKind` or emits
// an unfamiliar breaker suffix therefore surfaces as a question, never silently.
// A unit test asserts no disposition has status 'ignored' with any reasonCode
// other than 'non_breaker_excluded'.
//
// NOTE: advisory questions on an otherwise-counted row (LV frame/trip unparsed,
// missing power functions, mounting-hint conflict) do NOT change the row's
// disposition status (it stays matched/unmatched) — they ride the now-structured
// operatorQuestions (§3.6), linked back to the row by inputIndex, and still
// block clean output via the §5.2 gate.

export interface ApparatusDisposition {
  inputIndex: number                              // index into ExtractionArtifact.apparatus — the stable key
  tag?: string
  raw: string
  sheet: string
  page: number
  bbox: [number, number, number, number]
  evidence: EvidenceKind                          // re-exported from extraction/types
  status: ApparatusDispositionStatus
  reasonCode: DispositionReasonCode
  reason: string                                  // human-readable, ASCII
  ref?: string                                    // catalog ref when status==='matched'
  lineKey?: string                                // stable line identity (specKey) when the row joined a line
}
```

`TakeoffResult` gains:

```ts
export interface TakeoffResult {
  matchedLines: MatchedLine[]
  unmatchedCandidates: UnmatchedCandidate[]
  operatorQuestions: OperatorQuestion[]
  findings: TakeoffFinding[]
  dispositions: ApparatusDisposition[]   // NEW — EXACTLY one per artifact.apparatus row
}
```

### 3.2 The exhaustiveness invariant (load-bearing)

`dispositions.length === artifact.apparatus.length`, and `dispositions[i].inputIndex === i` for every `i`. Every input row resolves to exactly one disposition. This invariant is the anti-silent-loss guarantee — a row cannot vanish without being accounted for. It is asserted by a unit test and re-checked by the runner before it trusts any count.

### 3.3 Threading `inputIndex`

- `ApparatusSignature` gains `inputIndex: number` (set in `runTakeoff` when the signature is built, carried untouched through `quantify`).
- `applyVoltageAssertions` already maps `artifact.apparatus → resolved` 1:1 in array order; `runTakeoff` iterates with the index and stamps it.
- The unresolved-row records carry their `inputIndex` and the source `ExtractedApparatus`.

### 3.4 `quantify` return change (`src/quantify/quantify.ts`, `quantify/types.ts`)

`QuantifiedLine` gains `lineKey: string` (= the existing `specKey`) and `memberIndices: number[]` (the `inputIndex` of each representative counted into the line). `quantify` returns:

```ts
{
  lines: QuantifiedLine[]                                  // memberIndices + lineKey added
  associated: { inputIndex: number; lineKey: string }[]    // NEW — non-representative occurrences folded as sources
  locationOnly: { inputIndex: number; sig: ApparatusSignature }[]  // now index-carrying
}
```

Today only the representative of each `deviceId` reaches `counted`; sibling occurrences contribute their source via `sourcesByDevice` but are otherwise dropped. They become `associated` entries (status `associated_source`) so they are accounted for, not lost.

### 3.5 Disposition assignment (status × reasonCode × condition)

`runTakeoff` builds a `dispositions` array of length `apparatus.length`, stamping each index exactly once:

| When (from the real code) | status | reasonCode |
|---|---|---|
| `NON_BREAKER` token, no frame/trip (`assessCore` L79) | `ignored` | `non_breaker_excluded` |
| `NON_BREAKER` + frame/trip (L77, also pushes a question) | `question` | `non_breaker_carries_rating` |
| not breaker-shaped (L81) — a producer candidate the engine can't classify | `question` | `unrecognized_apparatus_row` |
| breaker-shaped, no classifiable voltage (L87) | `question` | `missing_voltage` |
| signature built → representative counted → `matchBreaker` ref | `matched` | `catalog_rule` (set `ref`,`lineKey`) |
| signature built → representative counted → no ref | `unmatched` | `no_catalog_rule` (set `lineKey`) |
| signature built → non-representative occurrence (quantify `associated`) | `associated_source` | `occurrence_of_counted_device` (set `lineKey`) |
| signature built → device only on non-authoritative evidence (`locationOnly`) | `question` | `location_only_non_authoritative` |
| no signature, but `tag` matches a counted line's `memberTags` (today emit.ts L29-33) | `associated_source` | `unresolved_tag_attached` (set `lineKey`) |

**Source of truth — `assessmentCode`.** The engine must NOT infer the no-signature disposition from `questions.length`: `assessCore` returns the identical `{signature:null, questions:[], isBreakerShaped:false}` shape for both a safe non-breaker (NON_BREAKER token, L79) and a not-breaker-shaped row (L81). `ApparatusAssessment` therefore carries a structured `assessmentCode` (`classified | non_breaker_excluded | non_breaker_carries_rating | missing_voltage | unrecognized_apparatus_row`) set at each return; `runTakeoff` stamps the disposition from it. Only `non_breaker_excluded` maps to `ignored`; the rest map to `question`.

**Advisory questions on an otherwise-counted row** (LV frame/trip unparsed L96, missing power functions L109, mounting-hint conflict L106) do **not** change the row's primary status (it is still `matched`/`unmatched`) — they are pushed to the now-**structured** `operatorQuestions` (§3.6) carrying their `inputIndex` + `code`, so the reconciliation links every question back to its row without scraping prose. Because clean output requires zero `operatorQuestions` (§5.2), a counted-but-uncertain row still blocks a clean envelope.

The `unresolved → attach-to-line` logic that currently lives in `emitEnvelope`'s caller (`runTakeoff`, emit.ts L29-41) moves earlier so the disposition can be stamped; behavior is preserved.

### 3.6 Structured operator questions

So reconciliation is fully structured (not part-prose), `OperatorQuestion` gains a stable `code` and an optional `inputIndex` linking it to its row:

```ts
export type OperatorQuestionCode =
  | 'missing_voltage'
  | 'lv_frame_trip_unparsed'
  | 'missing_power_functions'
  | 'mounting_hint_conflict'
  | 'non_breaker_carries_rating'
  | 'location_only'
  | 'unrecognized_apparatus_row'
  | 'profile_warning'             // legend/profile-level; no single row → inputIndex omitted

export interface OperatorQuestion {
  question: string                // human-readable, ASCII (unchanged)
  context: string                 // unchanged
  code: OperatorQuestionCode      // NEW — stable, machine-checkable
  inputIndex?: number             // NEW — the apparatus row it pertains to (omitted for profile-level)
}
```

The `q(x, …)` helper in `normalize.ts` is extended to take a `code` and (when called per-row) the `inputIndex`; `runTakeoff` supplies the index it already holds. `profileWarnings` map to `code: 'profile_warning'` with no `inputIndex`. The reconciliation report joins questions to rows by `inputIndex`, so a counted-but-uncertain row shows its advisory question codes inline — no free-text scraping.

## 4. Runtime contract validator (`src/extraction/parse.ts`)

A hand-rolled validator (no new dependency — matches estimator-core's `validator.ts` style; the schema is small and enumerable). `parseArtifact(json: unknown): ExtractionArtifact` runs **before** `runTakeoff` and fails closed with a precise, ASCII message naming the offending path:

- top: `pdf` is a non-empty string; `apparatus` is an **array** (reject non-array — today's `as ExtractionArtifact` cast silently accepts garbage); `profileWarnings?` array of string; `voltageAssertions?` array.
- each `apparatus[i]`: `raw` non-empty string; `sheet` non-empty string; `page` an integer ≥ 0; `bbox` a 4-tuple of finite numbers; `evidence` ∈ `EvidenceKind`; optional `tag`/`block` strings; `busVoltageV?` a **positive integer** (`Number.isInteger && > 0` — mirrors the voltage-assertion rule; rejects `480.5`/`0.5`, which `classifyVoltage` would otherwise route to a class); `mountingHint?` a valid `Mounting`; `candidateKind?` === `'breaker'`.
- each `voltageAssertions[i]`: shape-only (`voltageV` number, `tags` non-empty string array) — **semantic** validation (integer/positive/tag-existence/conflict) stays in the engine's `applyVoltageAssertions`; the parser only rejects structural garbage so a malformed cross-host artifact cannot reach the engine.
- bounded: reject an artifact whose `apparatus.length` exceeds a sane cap (e.g. 5000) to refuse a hostile oversized payload.

Errors throw `ArtifactContractError` with `path` + `expected` + `got`. Boring, precise, hostile to malformed input.

## 5. The runner (`src/runner/`, `bin`)

### 5.1 CLI

`package.json` gains a `bin`: `estimator-takeoff`. `src/runner/cli.ts` (thin argv) → `src/runner/run.ts` (pure, testable):

```
estimator-takeoff run <artifact.json> --project <N> [--out <report.json>] [--allow-open-items]
```

Pipeline: read file → `parseArtifact` → `runTakeoff` → assert the exhaustiveness invariant → build the reconciliation report → decide emit per §5.2 → write/print report.

**Exit codes:** `0` clean (or accepted partial with `--allow-open-items`); non-zero on: file unreadable / invalid JSON / `ArtifactContractError` / error-severity findings / zero matched lines / open items without `--allow-open-items`. Each non-zero path prints a precise stderr reason.

### 5.2 Emit discipline (loud)

- **Clean** is computed over the **exhaustive `dispositions`** (the robust source of truth), via a shared `isClean(result)` predicate: **no disposition has status `unmatched` or `question`**, AND zero `operatorQuestions` (catches advisory-on-matched and profile-level questions), AND zero error-severity findings. It is disposition-based on purpose: an `unrecognized_apparatus_row` is a `question` *disposition* that emits no `operatorQuestion`, so a bucket-only gate (counting `operatorQuestions`/`unmatchedCandidates`) would let it pass. Only when `isClean` holds is the priced envelope emitted as clean / `status: "clean"`.
- **Error findings are an UNCONDITIONAL hard failure** — non-zero exit, **no envelope**, and **`--allow-open-items` does NOT relax this**. This preserves the voltage-assertion fail-closed contract (`emitEnvelope` already throws on any error-severity finding); the flag must never be able to launder a blocking finding into a "partial preview". Error findings are a producer/assertion defect to fix, not an "open item" to acknowledge.
- **`--allow-open-items` tolerates ONLY non-empty `unmatchedCandidates` and/or `operatorQuestions`** (genuine open work an operator can knowingly defer): it produces the envelope from matched lines, stamps the report `status: "partial_preview"`, and prints `WARNING: partial preview — N unmatched, M open questions; envelope is NOT a complete bid` to **stderr**. (Error-finding count is never part of this path — if any exist, the run already hard-failed above.)
- Without `--allow-open-items`, any non-empty `unmatchedCandidates` or `operatorQuestions` → **refuse** (non-zero exit, no envelope presented as clean).
- This is the direct fix for "unmatched vanish at emit seam": unmatched/questions can no longer be silently absent — they are either blocking or explicitly marked `partial_preview`; error findings remain hard-blocking regardless.
- `emitEnvelope`'s existing throws (error findings, zero matched) are preserved as the backstop; the runner surfaces them as precise non-zero exits rather than uncaught throws.

## 6. Reconciliation report (`src/runner/report.ts`)

A pure function `reconcile(artifact, result): ReconciliationReport`, rendered to stdout (human table) and optionally written as JSON (`--out`).

```ts
interface ReconciliationReport {
  status: 'clean' | 'partial_preview'
  counts: {
    apparatus_in: number          // === artifact.apparatus.length
    matched_lines: number
    matched_qty: number           // Σ matchedLines.qty
    associated_sources: number
    unmatched_candidates: number
    operator_questions: number
    error_findings: number
    warning_findings: number
    ignored: number
  }
  accounted: boolean              // every input row has a disposition AND counts reconcile
  dispositions: ApparatusDisposition[]   // per-row, by inputIndex
  envelopeTotals?: { bid_cents: number }  // present when an envelope was emitted
  manifest?: ArtifactManifest     // §7, when present beside the artifact
}
```

`accounted` asserts `apparatus_in === dispositions.length` and that the disposition status tally is internally consistent (matched-row count ⊆ matchedLines members, etc.). A `false` here is itself a hard failure (the reconciliation cannot vouch for the run).

## 7. Provenance — regen command + manifest + drift-check

`drawing-nav` stays thin. Provenance lives in a **manifest sidecar** beside the committed artifact:

```jsonc
// test/fixtures/stack-phx02a-e01-11.artifact.manifest.json
{
  "artifact": "stack-phx02a-e01-11.artifact.json",
  "producerRepo": "drawing-nav",
  "producerCommit": "e7a3fb4",
  "pdf": "20260616 – PHX02A – ADDENDUM 4 – ELEC.pdf",
  "command": "drawing-nav extract \"<abs path to PDF>\" --no-timestamp --assert-voltage 480:MSB-P1-110-GB,ACC-1-09-FB,ACC-1-10-FB",
  "sha256": "<hex of the committed artifact bytes>",
  "apparatusCount": 44,
  "voltageAssertionTags": ["MSB-P1-110-GB", "ACC-1-09-FB", "ACC-1-10-FB"]
}
```

- **Regen** (manual, Windows-side where the PDF + drawing-nav live): a small `scripts/regen-fixture` (documented in the manifest `command`) runs the producer, writes the artifact, computes the sha256, and writes the manifest. It cannot run in host CI (the proprietary PDF is not in the repo) — by design.
- **Drift-check test** (host vitest): recompute `sha256(committed artifact)` and `apparatus.length`, assert they equal the manifest. Any byte-level drift (a hand edit, a re-extraction with a different producer) goes **red**, forcing a conscious manifest update. This makes the 41-vs-44 class of drift impossible to hand-wave.

## 8. Canonical fixture + golden re-baseline (D2)

- The drifted hand-cleaned `test/fixtures/stack-phx02a-e01-11-extract.json` (41 rows, no `voltageAssertions`) is **replaced** by `stack-phx02a-e01-11.artifact.json` — regenerated from drawing-nav `e7a3fb4` on the real PDF **with** `--assert-voltage 480:MSB-P1-110-GB,ACC-1-09-FB,ACC-1-10-FB` — plus its manifest. History stays in git; there is no second active truth.
- The producer's noise (bare `MBB`/`MCB`, the `STSDP-…-MCB` duplicate join, `STS`/`SPARE` rows) is **part of the proof**: it surfaces as `unmatched`/`ignored`/`question` dispositions, demonstrating the reconciliation works on real, imperfect output.
- `test/golden-e01-11.test.ts` re-baselines onto the canonical artifact: a single E2E that (a) runs the runner on the real artifact, (b) asserts the exhaustiveness invariant, (c) asserts the demo 480V mains land as `matched` with a catalog ref, (d) asserts the noise lands as `unmatched`/`ignored`, (e) asserts a non-clean status (open items present → `partial_preview`), and (f) §9.

## 9. Pricing assertion (closes "never value-validated")

The E2E asserts a real matched line prices through `buildNativeEnvelope` to **`envelope.totals.bid_cents > 0`** — not merely that a catalog ref resolved — **and** that the envelope is **validator-clean** (`envelope.findings` empty / no error-severity validation findings). Asserting both makes the priced seam *positive and clean*: a non-zero bid that smuggled a validation finding would otherwise look like a pass. First test to pin a positive dollar value across the emit→estimator-core seam.

## 10. Tests

- `parse.test.ts`: rejects non-array apparatus, missing `pdf`, bad `bbox` arity, non-finite bbox, bad `evidence` enum, `page` non-integer, **non-integer `busVoltageV` (`480.5`, `0.5`)**, oversized payload, malformed `voltageAssertions` shape; accepts a valid artifact. Each asserts the error `path`.
- `dispositions.test.ts`: the exhaustiveness invariant (length + index alignment); each status/reasonCode row from §3.5 with a crafted fixture (matched, `associated_source` via sibling occurrence, `associated_source` via unresolved-tag-attach, unmatched, `missing_voltage` question, `location_only` question, **`non_breaker_carries_rating` question**, **`unrecognized_apparatus_row` question**, `non_breaker_excluded` ignored); **plus the ignored-invariant: no disposition has status `ignored` with any reasonCode other than `non_breaker_excluded`**.
- `questions.test.ts`: every `operatorQuestion` carries a `code`; row-scoped questions carry the correct `inputIndex` (advisory on a counted row links back to its row); `profileWarnings` map to `code:'profile_warning'` with no `inputIndex`.
- `quantify.test.ts` (extend): `memberIndices`/`lineKey` populated; `associated` lists non-representative occurrences.
- `runner.test.ts`: clean vs partial_preview gating; `--allow-open-items` stamps `partial_preview` + stderr warning for unmatched/questions; **error findings hard-fail even WITH `--allow-open-items` (no envelope) — the fail-closed contract is not bypassable**; exit codes for invalid JSON / contract error / zero-matched / open-items-without-flag.
- `drift-check.test.ts`: committed artifact sha256 + count === manifest.
- `golden-e01-11.test.ts` (re-baseline): §8 + §9 on the real canonical artifact — including `bid_cents > 0` **and** `envelope.findings` empty.

## 11. Files touched

- Modify `src/buckets/types.ts` — `ApparatusDisposition*`, `DispositionReasonCode`, `TakeoffResult.dispositions`; `OperatorQuestion.code` + `inputIndex` + `OperatorQuestionCode`; re-export `EvidenceKind`.
- Modify `src/signature/normalize.ts` — extend `q()` to carry `code` (+ `inputIndex` when row-scoped); set codes at each question site.
- Modify `src/signature/types.ts` — `ApparatusSignature.inputIndex`.
- Modify `src/quantify/quantify.ts`, `quantify/types.ts` — `lineKey`, `memberIndices`, `associated`, index-carrying `locationOnly`.
- Modify `src/emit/emit.ts` — `runTakeoff` builds `dispositions` (move the attach-to-line logic earlier, thread inputIndex); `emitEnvelope` unchanged behavior.
- Create `src/extraction/parse.ts` — `parseArtifact` + `ArtifactContractError`.
- Create `src/runner/{cli.ts,run.ts,report.ts}`; `package.json` `bin`.
- Modify `src/index.ts` — export `parseArtifact`, the runner entry, `ApparatusDisposition*` types.
- Replace `test/fixtures/stack-phx02a-e01-11-extract.json` → `stack-phx02a-e01-11.artifact.json` + `.manifest.json`; `scripts/regen-fixture`.
- Tests per §10.

## 12. Decisions (ratified)

- **D1 — row-level dispositions keyed by `inputIndex`** (not tag-only): tags duplicate/miss/join-wrong; tag-only reconciliation recreates silent-loss. `associated_source` for a location/occurrence folded into a counted breaker; `ignored` reserved for explicit non-breaker/not-breaker-shaped exclusions.
- **D2 — replace the 41-row hand-cleaned fixture** with a canonical artifact regenerated from drawing-nav `e7a3fb4` + manifest + sha. Noise is part of the proof; history stays in git.
- **D3 — hand-rolled validator**, no Zod. Boring, precise, hostile to malformed input.
- **Loud partial preview** — clean output requires zero unmatched + zero questions + zero error findings; `--allow-open-items` stamps `partial_preview` and warns on stderr.
- **Sequence** — this slice precedes SKILL.md.

### Rev 2 — spec-review fixes (2026-06-26)
- **Error findings are an unconditional hard block** (§5.2): `--allow-open-items` tolerates ONLY `unmatchedCandidates`/`operatorQuestions`; `error_findings > 0` always fails with no envelope, preserving the voltage-assertion fail-closed contract (it must not be launderable into a partial preview).
- **`ignored` ⟺ `non_breaker_excluded` only** (§3.1/3.5): the unsafe `not_breaker_shaped` and `non_breaker_carries_rating` cases are reclassified to `question` (`unrecognized_apparatus_row` / `non_breaker_carries_rating`), so a producer drift (dropped `candidateKind`, unfamiliar suffix) surfaces as a blocking question instead of a silently-ignored row. Guarded by an invariant test.
- **Structured operator questions** (§3.6): `OperatorQuestion` gains `code` + optional `inputIndex` so advisory questions on counted rows link back to the row — reconciliation is fully structured, no prose-scraping.
- **Detected voltage must be a positive integer** (§4): `busVoltageV` validated `Number.isInteger && > 0`, mirroring the assertion rule (rejects `480.5`/`0.5`).
- **Pricing assertion is positive AND clean** (§9): assert `bid_cents > 0` and `envelope.findings` empty.
