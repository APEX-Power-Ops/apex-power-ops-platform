# Estimator-Takeoff Gate-1 Voltage UI — Design

> Status: DRAFT for operator review. Lane `estimator-takeoff/gate1-voltage-ui` off main `3dff664c`. Dev-only; merge OPERATOR-GATED. This is the FIRST human gate of the estimator-takeoff pipeline.
>
> **Rev 2 (operator review, 2026-06-26) — four contract corrections, all verified against source:** (1) the interactive surface is built from `runTakeoff` + `reconcile` so `TakeoffResult.findings` is available — NOT `runFromArtifact`, whose `RunResult.findings` carries only estimator-core envelope findings and **drops the voltage-assertion findings** (every non-emit return path sets `findings: []`); (2) **untagged rows are read-only, not assertable** — the engine's `VoltageAssertion` is tag-keyed only, no `inputIndex` path; (3) **assertions merge by tag (replace, never blind-append)** — duplicate tags are a hard engine error; (4) **the UI surfaces ALL open items, not just missing voltage** — `isClean` blocks on error findings, any unresolved disposition, and any operator question.

## Goal

Turn the engineer-only `--assert-voltage` CLI step into a browser workflow a PM/estimator can drive: load a drawing-nav extraction artifact, see the reconciliation, resolve every `missing_voltage` question by asserting voltage per tag, and export a runner-ready artifact + report (and a priced envelope when the run is clean). No pricing edits, no Gate-2 line review, no apparatus-family expansion.

## Context (grounded 2026-06-26)

- The breaker engine, voltage-assertion contract, runner, and reconciliation are merged to main; the pipeline is proven end-to-end on sheet E01-11 but reachable only as a two-host CLI.
- `apps/operations-web` is a **pure browser shell**: Next.js 16.2.5 App Router, every page `'use client'`, **no `app/api` route handlers, no server actions, no RSC**. All API traffic is rewritten to the Python/FastAPI control-plane (`controlPlaneBaseUrl`, default `http://127.0.0.1:8010`). Server-side compute does not live in operations-web.
- The estimator TS engines already run **client-side** there: `app/estimator/page.tsx` (`'use client'`) calls estimator-core's `buildNativeEnvelope` in the browser via `lib/estimator.ts`.
- The `@apex/estimator-takeoff` library path is **browser-safe** — verified: no Node-only imports anywhere in `src` except `src/runner/cli.ts` (the sole `process.` hit elsewhere is a comment in `run.ts`). `parseArtifact` / `runFromArtifact` / `runTakeoff` / `reconcile` / `isClean` are pure TS.

## Decision: browser-side, ephemeral, standalone

Operator-ratified. The unknown in this slice is the **operator workflow**, not storage. Therefore:

- **Execution:** in the browser. Add `@apex/estimator-takeoff` to `apps/operations-web/package.json` (`workspace:*`) and `next.config.ts` `transpilePackages` (mirroring estimator-core). Import the engine directly in the page. No new backend route, no Python involvement for compute.
- **Persistence:** none server-side. The artifact lives in React state for the session. Output is downloaded (import/export only).
- **Discipline (so this is disciplined, not throwaway):** required project/package metadata on every export; export the same durable JSON shapes the runner already understands; loudly label non-clean output `partial_preview`; operator name/initials recorded as **evidence metadata, explicitly NOT authoritative audit**; **deterministic content hashes** so a later persistence slice can store byte-identical artifacts in JSONB without redesign.

## Architecture

```
file picker (browser)          in-browser engine                operator                 in-browser engine            export (download)
drawing-nav artifact.json  ->  parseArtifact + runFromArtifact  ->  resolve missing_   ->  embed voltageAssertions  ->  combined export JSON
(+ optional manifest.json)     (client-side, no backend)            voltage per tag        + re-run runFromArtifact     + runner-ready artifact.json
```

drawing-nav stays an offline Windows tool; the operator uploads its JSON output. operations-web never calls drawing-nav.

## Pipeline (6 stages)

### 1. Load
- A file `<input type="file" accept="application/json">` reads the artifact JSON via the browser `FileReader` (no upload to any server).
- `parseArtifact(json): ExtractionArtifact` validates the contract; `ArtifactContractError` (`.path`, `.expected`, `.got`) surfaces as a loud `role="alert"` red message naming the offending path.
- Optional: a second file input accepts the producer manifest sidecar (`*.manifest.json`); if provided, pre-fill the project-context form (`pdf`, `sheet`, `producerCommit`).

### 2. Evaluate (run + reconcile) — thin helper, NOT runFromArtifact
- A thin browser helper composes exported primitives and returns **both** results:
  `const result = runTakeoff(artifact); const report = reconcile(artifact, result); // { result, report }`.
- **Why not `runFromArtifact`:** its `RunResult.findings` is estimator-core envelope findings only, and every non-emit return path sets `findings: []`. The voltage-assertion findings (unknown / duplicate / invalid tag, detected-vs-asserted conflict) live in `TakeoffResult.findings` and are summarized into `report.counts` (numbers only) — their codes/messages are otherwise lost by the runner wrapper. The interactive surface MUST read `result.findings` directly. `runFromArtifact` is reserved for CLI parity.
- `report.status` / `report.counts` / `result.dispositions` / `result.findings` / `result.operatorQuestions` / `result.unmatchedCandidates` render immediately. No envelope is emitted during review (only at export, when clean).

### 3. Missing-voltage worklist (grouped sheet -> block -> tag)
- Filter `report.dispositions` where `reasonCode === 'missing_voltage'`.
- `block` is NOT on `ApparatusDisposition` (known API gap) — recover it per row from `artifact.apparatus[disposition.inputIndex].block`. `sheet` and `tag` are on the disposition directly.
- Group by `sheet` -> `block` -> `tag`. **Untagged missing-voltage rows (no `tag`) are NOT assertable in V1** — `VoltageAssertion` is tag-keyed only (`{ voltageV, tags[] }`; `applyVoltageAssertions` validates asserted tags against extracted device tags; there is no `inputIndex`-based assertion path). They appear **read-only** in the "other open items" panel (Stage 4 / UI), flagged blocking-but-not-resolvable-here. An `inputIndex` assertion path would be an engine contract change — deferred.
- Display each resolvable (tagged) group with its `raw`, `evidence`, and the engine's question text (`disposition.reason`).

### 4. Assign voltage (per TAG / per selected group — tagged rows only)
- For TAGGED missing-voltage rows: per tag (or a multi-select of tags sharing a voltage) the operator enters an integer voltage. Untagged rows are not assertable here (Stage 3).
- Build `VoltageAssertion[]`: `{ voltageV: number, tags: string[], source: 'gate1', actor: <operator initials/name>, note?: string }`. `source: 'gate1'` is already allocated in the contract (`src/extraction/types.ts`) — **zero engine change**. `actor` is evidence metadata only; the engine never branches on it.
- Client-side pre-validation mirrors the engine (positive integer, non-empty tags) for fast feedback, but the engine remains the fail-closed authority.

### 5. Apply & re-evaluate
- **Merge by tag — replace, never blind-append.** Duplicate tags are a hard engine error (`voltage_assertion_duplicate_tag`, strict even for the same voltage). So the embed/export builder normalizes the assertion set by tag: a Gate-1 entry **replaces** any existing same-tag assertion — whether from a prior Gate-1 edit or from CLI `voltageAssertions` already present in the loaded artifact (last-write-wins from the Gate-1 UI). Result: a single assertion per tag; blind concatenation that could self-fail the page is forbidden. Computed on a **cloned** artifact (Stage 1 keeps a pristine copy so iterative resolution never compounds state).
- Re-evaluate via the same thin helper (`runTakeoff` + `reconcile`) on the clone.
- Surface assertion findings from **`result.findings`** (TakeoffResult) inline: errors (`voltage_assertion_unknown_tag`, `voltage_assertion_duplicate_tag`, `voltage_assertion_invalid_voltage`, `voltage_assertion_invalid_shape`) block; `voltage_assertion_conflict` is a warning (asserted overrides detected — show both values from `finding.detail`).
- Show `report.status`: **`clean`** vs **`partial_preview`** with a loud "NOT a complete bid" banner and `counts.unresolved_rows`. The "other open items" panel (UI) explains WHY a run is still `partial_preview` after all voltage is resolved.

### 6. Export / hand off
Two downloads, no server write:

1. **Combined export** `gate1-<projectNumber>-<sheet>-export.json` — the durable, persistence-ready record:
   ```jsonc
   {
     "schemaVersion": 1,
     "manifest": {
       "projectNumber": "<required>",
       "packageName": "<optional>",
       "sheet": "<from artifact/manifest or operator>",
       "pdf": "<artifact.pdf>",
       "producerCommit": "<from uploaded manifest, if any>",
       "status": "clean | partial_preview",
       "apparatusCount": <n>,
       "unresolvedRows": <n>,
       "gate1AssertionTags": ["..."],
       "operatorEvidence": { "name": "<operator>", "assertedAtClient": "<ISO from operator's clock>", "authoritative": false },
       "artifactContentHash": "<canonical sha256, see Determinism>",
       "reportContentHash": "<canonical sha256>"
     },
     "artifact": { /* modified ExtractionArtifact, voltageAssertions embedded */ },
     "report": { /* ReconciliationReport */ },
     "envelope": { /* EstimateEnvelope — present ONLY when status === 'clean' */ }
   }
   ```
2. **Runner-ready artifact** `<sheet>.artifact.json` — the bare modified `ExtractionArtifact` (assertions embedded), pretty-printed (2-space, LF) so the existing CLI runner (`pnpm run-artifact run <artifact.json> ...`) consumes it unchanged.

The `envelope` is produced by `emitEnvelope(result, { projectNumber })` and included ONLY when `isClean(result) && result.matchedLines.length > 0`. When `status !== 'clean'`, `envelope` is omitted and every export surface is labeled `partial_preview` / "NOT a complete bid".

## Engine import surface (all from `@apex/estimator-takeoff`)

```ts
import {
  parseArtifact, ArtifactContractError,
  runTakeoff, reconcile, isClean, emitEnvelope,   // interactive review path (composed in the browser)
  // runFromArtifact is exported too, but reserved for CLI parity — NOT the interactive surface
} from '@apex/estimator-takeoff'
import type {
  ExtractionArtifact, ExtractedApparatus, VoltageAssertion,
  TakeoffResult, ApparatusDisposition, DispositionReasonCode,
  OperatorQuestion, UnmatchedCandidate, MatchedLine,
  TakeoffFinding, VoltageAssertionCode, ReconciliationReport,
} from '@apex/estimator-takeoff'
```

All of the above are already exported from `src/index.ts` (verified) — **no new engine exports are required for V1.** The interactive surface is `runTakeoff` + `reconcile` (so `TakeoffResult.findings` is reachable); `emitEnvelope(result, { projectNumber })` builds the export envelope and is called ONLY when `isClean(result) && result.matchedLines.length > 0` (mirroring `runFromArtifact`'s emit discipline — zero-matched and error findings never emit). Two known API gaps handled consumer-side (NOT blockers): `block` recovered via `artifact.apparatus[inputIndex].block`; `OperatorQuestion.inputIndex` is optional (profile-warning questions carry none) — null-guard before indexing.

## Determinism & hashing

- The existing `test/drift-check.test.ts` hashes the **raw artifact file bytes** (`createHash('sha256').update(artifactBytes)`, LF-pinned). That is correct for drawing-nav's immutable output but does not survive Gate-1's modification or a JSONB round-trip.
- Gate-1 therefore hashes a **canonical serialization**: `canonicalJson(value)` recursively sorts object keys and emits compact JSON (no insignificant whitespace, UTF-8). `artifactContentHash = sha256(canonicalJson(modifiedArtifact))`, `reportContentHash = sha256(canonicalJson(report))`, computed in-browser via `crypto.subtle.digest('SHA-256', ...)` (available in operations-web's secure context).
- This canonical hash is reproducible from the parsed object on any platform (browser now, server later), so a future persistence slice can store the artifact in `jsonb` and recompute the identical hash — the property the operator requires. The spec explicitly notes the canonical hash is a DIFFERENT basis from drawing-nav's raw-byte drift hash; the two coexist (raw-byte for the producer->CLI provenance pin, canonical for Gate-1 persistence stability).
- `canonicalJson` lives in `lib/gate1-canonical.ts`, is pure, and is unit-tested (key-order independence, nested arrays/objects, number/string fidelity).

## UI design

- **Route:** top-level `app/takeoff/page.tsx` (a takeoff tool, not a PM-review surface) + `app/takeoff/loading.tsx` skeleton. Add `{ path: '/takeoff', marker: '<unique h1 text>' }` to `scripts/smoke-hosted-routes.mjs`. Add a nav link where the other top-level tools are linked.
- **Lib (`lib/gate1.ts` + `lib/gate1-canonical.ts`):** typed view-model + a `Gate1Error extends Error` (`.path`) class + pure helpers (no `fetch` — ephemeral has no API, so fully unit-testable without DOM/network):
  - `evaluate(artifact): { result: TakeoffResult; report: ReconciliationReport }` — the thin helper (`runTakeoff` + `reconcile`).
  - `resolvableVoltageGroups(result, artifact): SheetGroup[]` — TAGGED `missing_voltage` dispositions grouped sheet→block→tag (`block` via `artifact.apparatus[inputIndex].block`).
  - `otherOpenItems(result, artifact): OpenItem[]` — everything else that blocks clean: untagged `missing_voltage` rows, `unmatchedCandidates`, profile-warning + other `question` dispositions (read-only).
  - `mergeAssertionsByTag(existing, gate1Entries): VoltageAssertion[]` — replace-by-tag dedup (last-write-wins from Gate-1); guarantees ≤1 assertion per tag.
  - `buildExport(...)`, `canonicalJson`, `sha256Hex`.
- **Page (`app/takeoff/page.tsx`):** `'use client'`. State: `artifact` (pristine), `result` + `report`, `assertions` (operator entries keyed by tag), `projectCtx` (projectNumber/package/operatorName), `busy`, `err`. `useCallback` handlers for load / assert / applyAndReevaluate / export. **Two panels** (load-bearing — `isClean` blocks on more than voltage, so a single-panel UI would leave the operator at `partial_preview` with no visible reason): **(1) "Voltage questions I can resolve"** — the tagged `missing_voltage` worklist (grouped sheet→block→tag), inline per-tag voltage entry + Apply, mirroring `pm-review/estimator-intake` inline edits; **(2) "Other open items blocking clean output"** — read-only list from `otherOpenItems(...)`. Status-gated buttons; `role="alert"` (red) errors / `aria-live="polite"` (green) success, matching estimator-intake. Export disabled until `projectNumber` is set.
- **Styling:** existing CSS-variable tokens + `hero-card` / `status-pill` / table conventions from `app/globals.css`; the same Tailwind-syntax class strings the recognition/estimator-intake pages already use.

## Testing

- **Unit (`tests/gate1.unit.spec.ts`, `tests/gate1-canonical.unit.spec.ts`):** `evaluate` returns both result+report; `resolvableVoltageGroups` grouping + `block` join + EXCLUDES untagged rows; `otherOpenItems` includes untagged missing-voltage + unmatched candidates + profile warnings; `mergeAssertionsByTag` REPLACES a same-tag existing/CLI assertion with no duplicate-tag error (the adversarial test: load an artifact that already carries a CLI assertion for a tag the operator re-asserts); `buildExport` omits `envelope` unless `clean` and labels `partial_preview`; `canonicalJson` key-order independence; `sha256Hex` reproducibility.
- **Browser smoke (`tests/browser-shell.takeoff.smoke.spec.ts`):** ephemeral has no API to mock; the smoke drives the real page using the committed E01-11 fixture artifact (`packages/estimator-takeoff/test/fixtures/stack-phx02a-e01-11.artifact.json`, copied or imported into the test). It loads the artifact, asserts the missing-voltage worklist renders grouped, asserts a voltage for the 3 demo tags, applies + re-runs, and asserts the `clean`/`partial_preview` banner + that the export buttons enable and produce a JSON whose `manifest.status` matches. Add the route to `smoke-hosted-routes.mjs`.
- The estimator-takeoff package's own suite is unchanged (the engine is imported, not modified).

## Out of scope (operator-confirmed)

- Pricing edits, feathering, rate/travel adjustments.
- Gate-2 line review (matched/unmatched/question bucket approval).
- Apparatus-family expansion beyond breakers.
- Multi-sheet / multi-PDF / multi-revision composition (one artifact = one sheet, per the runner-reconciliation design).
- Real multi-user auth (continues the dev `NEXT_PUBLIC_OPS_DEV_PM_ID` / operator-typed-name pattern; the operator name is evidence, not authenticated identity).
- Any server-side persistence (no `app/api` route, no control-plane route, no migration, no `ops.takeoff_runs` table).

## Follow-on (NOT this slice)

The persisted, project-linked model (`ops.takeoff_runs` JSONB columns + control-plane routes + the `ops_app` role boundary, feeding the ops/recognition pipeline) is the correct long-term home. It is deliberately deferred until this UI proves the human gate. Because the export already carries the durable JSON shapes + canonical content hashes, the upgrade is additive: the persistence slice stores the exact same `artifact`/`report`/`envelope` objects and recomputes the identical hash.

## Open questions

None blocking. Minor items decided with leans (override at review): top-level `/takeoff` route name; single combined export JSON + a bare runner artifact (no zip / no new dependency); the interactive surface always shows the full reconciliation (no `allowOpenItems` toggle — the export simply omits `envelope` when not clean).
