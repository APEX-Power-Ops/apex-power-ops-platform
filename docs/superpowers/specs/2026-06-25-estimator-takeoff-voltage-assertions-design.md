# Estimator-Takeoff Voltage Assertions — Design

**Date:** 2026-06-25
**Branch:** `estimator-takeoff/voltage-assertions` (off `main` @ `99e3d74f`)
**Status:** ratified design → spec, **rev 2** (operator spec-review hardening folded in 2026-06-25)
**Author:** CC (technical authority), operator-ratified

> **Rev 2 changelog (operator spec review, 5 findings):** provenance is now
> non-forgeable (engine-only resolved wrapper; public JSON cannot set
> `voltageBasis`); assertion issues are **coded findings with severity**;
> `emitEnvelope` refuses on any *error*-severity finding (so "blocking" actually
> blocks); invalid voltages (non-integer / ≤ 0 / non-finite) are rejected
> engine-side; error-tagged devices are **tainted** so they can't price via a
> detected fallback; **conflict is a non-blocking warning** (operator wins,
> device prices, recorded as audit evidence) — it is no longer mislabeled
> "blocking."

---

## 1. Problem & Goal

A breaker cannot be classified (LV/MV/HV) or priced without a nominal bus
voltage. On real multi-bus drawings (STACK PHX02A `E01-11`) the extractor
**correctly refuses to guess** voltage — every `busVoltageV` comes back
`undefined`, so today every breaker-shaped row surfaces a "supply voltage"
question and nothing prices. The only safe way to supply the missing fact is an
**explicit operator statement**, not nearest-label geometry (which re-introduces
the wrong-bus error: a 208 V house panel sitting next to a 480 V board).

**Goal:** let an operator assert voltage **per device tag** (grouped/bulk for
ergonomics), have the **engine** treat that assertion as the authoritative
voltage for those devices, price each device at *its own* asserted voltage, and
record the provenance so a 'detected' value is never silently trusted over an
operator's statement — and so a malformed or ambiguous assertion **fails closed**
rather than mis-pricing.

This is the slice that replaces the current golden's broadcast-480-to-all hack
(`test/golden-e01-11.test.ts`, case 2) with a real per-tag assertion path.

### Coverage model (operator-decided, locked)

Model **C — tag-scoped operator voltage assertions**, grouped/bulk for
ergonomics. **Not A** (nearest-label geometry — re-introduces wrong-bus
inference). **Not B** (block-scoped single voltage — proven wrong on `E01-11`'s
mixed 480 + 208/120 bus). The contract is **final**, not a stepping stone:
Gate-1 UI later produces the *same* artifact block, visually.

---

## 2. Architecture

### 2.1 Authority split (operator-ratified)

> Voltage assertion is **not a drawing-nav concern**; it is an estimator
> intake / evidence concern. Python captures the operator's *statement*; it does
> not decide whether the statement is valid, conflicting, or price-authoritative.
> The TS engine is the single contract shared by CLI artifacts, Gate-1 UI
> artifacts, tests, and future review surfaces.

- **TS engine (`@apex/estimator-takeoff`) = sole validator + applier.** It owns
  every rule below (voltage validation, unknown-tag rejection, duplicate-tag
  rejection, conflict-recording, provenance). It **recomputes provenance from
  scratch** — artifact JSON can never assert provenance (§3.3). One honesty path
  for CLI, Gate-1, and tests.
- **Python `drawing-nav` CLI = thin assertion collector.** Parses
  `--assert-voltage`, emits the raw assertion block into the artifact, stamps
  `source: 'cli'` and optional `actor`/`note`. It performs **no** semantic
  validation (tag existence, conflicts, voltage sanity, authority). Format-parsing
  of its own flag (colon split, integer voltage) is the only check it does.
- **Gate-1 UI (future) = same artifact block**, visual, with the engine still
  the validator.

### 2.2 Two repositories (structural fact)

The slice spans two independent git repos joined only by the
`ExtractionArtifact` JSON seam:

| Repo | Path | Role | Test runner |
|------|------|------|-------------|
| `apex-power-ops-platform` | host worktree `/home/olares/code/apex/apex-takeoff-voltage`, branch `estimator-takeoff/voltage-assertions` | TS engine — defines + consumes the contract; **authoritative** | vitest |
| `drawing-nav` | local `C:\Users\jjswe\Tools\drawing-nav` (separate repo, `master` @ `42addd2`) | Python thin collector — *produces* the contract | pytest |

**Phasing.** Phase A (TS engine) is the merge-gated, self-contained deliverable
of this branch — fully testable with hand-authored artifacts carrying
`voltageAssertions`, **no Python required**. Phase B (drawing-nav
`--assert-voltage`) is a small companion in the drawing-nav repo, immediately
following, gated on the frozen JSON contract. Single-writer is preserved: the
two repos are distinct worktrees.

### 2.3 The pipeline seam

Today (`src/emit/emit.ts`):

```
runTakeoff(artifact)
  └─ for x of artifact.apparatus → assessApparatus(x)   // classifyVoltage(x.busVoltageV)
  └─ quantify → matchBreaker → MatchedLine[]
```

New — a pure pass runs **before** the apparatus loop, resolves effective voltage
from assertions, and returns engine-owned **resolved wrappers** + coded findings:

```
runTakeoff(artifact)
  ├─ applyVoltageAssertions(artifact) → { resolved, findings }      // NEW pure pass
  │     resolved : ResolvedApparatus[]  (engine wrapper carrying voltageBasis)
  │     findings : TakeoffFinding[]     (coded, severity-tagged)
  └─ for { apparatus, voltageBasis } of resolved → assessResolvedApparatus(apparatus, voltageBasis)
     (engine-internal entry; the PUBLIC assessApparatus(x) is one-arg — see Rev 3 addendum)

emitEnvelope(result)
  ├─ if any finding.severity === 'error' → THROW (fail closed)      // NEW
  └─ if matchedLines.length === 0 → THROW (existing)
```

`applyVoltageAssertions` is **pure and clock-free** (preserves determinism /
golden tests). It branches only on `voltageV` and `tags`; `actor`/`note`/
`source`/`at` are carried through as evidence and never affect engine logic.

**Evidence of record (decided 2026-06-25 — Rev 3).** The durable assertion
evidence is the **input `ExtractionArtifact.voltageAssertions[]` itself**: it
retains `voltageV`/`tags`/`actor`/`note`/`source`/`at` verbatim and is the
authoritative record. The engine is a pure function over it and does NOT
re-materialize full evidence into `TakeoffResult`: `actor`/`source` survive on
conflict-finding `detail`, and the per-line emit note is a concise human
summary (`voltage <V>V (<basis>)`) — `note` is intentionally not echoed there.
Gate-1, when built, surfaces full per-assertion evidence by joining its line
back to the originating assertion in the artifact (keyed by tag). Structured
per-line evidence on `TakeoffResult` is deliberately deferred (YAGNI) until a
consumer needs it; this is a documented choice, not an omission.

---

## 3. The Contract (data shapes)

### 3.1 `VoltageAssertion` (new, `src/extraction/types.ts`)

```ts
export interface VoltageAssertion {
  voltageV: number          // asserted nominal voltage (V), applied to every listed tag.
                            // Engine REQUIRES Number.isInteger(voltageV) && voltageV > 0 (§4 step 2).
  tags: string[]            // device tags this assertion covers (>= 1)
  actor?: string            // who asserted — carried to evidence; engine NEVER branches on it
  note?: string             // free-text rationale — carried to evidence
  source?: 'cli' | 'gate1'  // channel that produced the assertion — carried to evidence
  at?: string               // OPTIONAL ISO author-time; UNTRUSTED metadata.
                            // Engine never trusts `at` for ordering or authority.
                            // V1 CLI omits it (no Python authority-stamping);
                            // reserved for Gate-1 acceptance-time stamping.
}
```

### 3.2 `ExtractionArtifact` += `voltageAssertions`

```ts
export interface ExtractionArtifact {
  pdf: string
  extractedAt?: string
  profileWarnings?: string[]
  apparatus: ExtractedApparatus[]
  voltageAssertions?: VoltageAssertion[]   // NEW — raw operator evidence, optional
}
```

### 3.3 Provenance is non-forgeable — internal `ResolvedApparatus`

**`ExtractedApparatus` does NOT gain a `voltageBasis` field.** (Fixes the
laundering vector: a JSON producer must not be able to set
`busVoltageV: 480, voltageBasis: 'asserted'` and have the engine honor a
provenance it never earned.)

`busVoltageV` on `ExtractedApparatus` is still permitted (a schedule extraction
may legitimately carry one) — but the engine always labels it `'detected'`,
never `'asserted'`. Only `applyVoltageAssertions` can grant `'asserted'`.

The basis travels in an **engine-constructed wrapper**, internal to the package,
that JSON cannot forge:

```ts
// src/signature/voltage-assertions.ts (NOT exported to artifact producers)
export interface ResolvedApparatus {
  apparatus: ExtractedApparatus     // effective busVoltageV already applied/cleared
  voltageBasis: VoltageBasis        // authoritative — computed by applyVoltageAssertions, recomputed from scratch
}
```

`applyVoltageAssertions` is the **sole producer** of `ResolvedApparatus` and sets
`voltageBasis` for **every** element from scratch; it never reads a basis off its
input. Any stray `voltageBasis` key smuggled into the artifact JSON is therefore
ignored (it isn't in the public type and is never read at runtime).

**Scope of the guarantee (precise, Rev 3).** `'asserted'` is non-forgeable
**through the artifact JSON and through the public package root** (`src/index.ts`
exports only the one-arg `assessApparatus`; `assessResolvedApparatus(x, basis)`
is NOT re-exported there). It is *not* a hard boundary against a deep import of
`signature/normalize.ts` from inside this package — `assessResolvedApparatus` is
module-exported for `emit.ts`. For a private, single-package consumer that is
acceptable: forging it requires already being inside the package source, not a
JSON producer or an external importer.

### 3.4 `ApparatusSignature` += `voltageBasis` (mirrors `mountingBasis`)

`src/signature/types.ts` — this is an **engine output**, not artifact input:

```ts
export type VoltageBasis = 'detected' | 'asserted' | 'none'

export interface ApparatusSignature {
  kind: 'breaker'
  voltageClass: VoltageClass
  voltageV?: number
  voltageBasis: VoltageBasis   // NEW — always present, parallel to mountingBasis
  // ...rest unchanged...
}
```

- `asserted` — effective voltage came from a *valid* operator assertion (authoritative).
- `detected` — effective voltage came from the extractor's `busVoltageV`
  (back-compat fallback; provenance-surfaced so the estimator sees it was **not**
  operator-confirmed).
- `none` — no usable voltage (no signature is produced; value exists in the union
  for type-parallelism with `MountingBasis`).

### 3.5 `MatchedLine` += `voltageBasis`; `TakeoffResult` += `findings`

`src/buckets/types.ts`:

```ts
export interface MatchedLine {
  ref: string; qty: number; block: string
  mountingBasis: MountingBasis
  voltageBasis: VoltageBasis   // NEW
  line: QuantifiedLine
}

export type FindingSeverity = 'error' | 'warning'

export type VoltageAssertionCode =
  | 'voltage_assertion_unknown_tag'
  | 'voltage_assertion_duplicate_tag'
  | 'voltage_assertion_conflict'
  | 'voltage_assertion_invalid_voltage'

export interface TakeoffFinding {
  code: VoltageAssertionCode    // (union grows as more finding-producers are added)
  severity: FindingSeverity
  message: string               // human-readable
  context: string               // tag/sheet locator, like OperatorQuestion.context
  detail?: { tag?: string; detectedV?: number; assertedV?: number; actor?: string; source?: string }
}

export interface TakeoffResult {
  matchedLines: MatchedLine[]
  unmatchedCandidates: UnmatchedCandidate[]
  operatorQuestions: OperatorQuestion[]   // existing soft questions (missing voltage, location-only, etc.)
  findings: TakeoffFinding[]              // NEW — coded, severity-tagged assertion findings
}
```

> **Naming note.** `TakeoffResult.findings` (takeoff-level, pre-envelope) is
> distinct from the `findings` returned *by* `emitEnvelope` /
> `buildNativeEnvelope` (estimator-core envelope-level findings). Both exist; they
> live on different types and are not merged.

### 3.6 Severity policy (the heart of "fail closed")

| Code | Severity | Device outcome |
|------|----------|----------------|
| `voltage_assertion_unknown_tag` | **error** | no matching device (operator typo / wrong sheet) |
| `voltage_assertion_duplicate_tag` | **error** | device **tainted** → effective voltage cleared → never prices |
| `voltage_assertion_invalid_voltage` | **error** | device(s) **tainted** → never price |
| `voltage_assertion_conflict` | **warning** | **operator wins** → device prices at asserted V, basis `'asserted'`; recorded as audit evidence (non-blocking) |

Any **error** finding makes `emitEnvelope` refuse (§4.4). A **warning**
(`conflict`) never blocks — the operator's assertion is authoritative, so there is
nothing to block; the record exists purely for the audit trail.

---

## 4. `applyVoltageAssertions` — the validator/applier

New file `src/signature/voltage-assertions.ts`.

```ts
export function applyVoltageAssertions(
  artifact: ExtractionArtifact,
): { resolved: ResolvedApparatus[]; findings: TakeoffFinding[] }
```

**Algorithm:**

1. **No assertions** → wrap each apparatus with basis
   `busVoltageV !== undefined ? 'detected' : 'none'`; `findings: []`. (Full
   back-compat — detected voltages still flow, labeled honestly.)
2. **Validate each assertion's `voltageV`** — require
   `Number.isInteger(voltageV) && voltageV > 0`. Reject non-finite, non-integer,
   fractional, zero, and negative. Each rejected assertion → `error`
   `voltage_assertion_invalid_voltage`, and **every tag it named is tainted**
   (step 6). (Fixes `0:TAG` / `-1:TAG` pricing as LV.)
3. **Build a (tag → voltageV) index** from the *valid* assertions by flattening
   every `(entry, tag)` pair.
4. **Duplicate-tag = error.** Any tag appearing in **more than one** valid
   `(entry, tag)` pair — *regardless of whether the voltages agree* — produces an
   `error` `voltage_assertion_duplicate_tag` and the tag is **tainted** (step 6).
   Idempotent collapse of exact duplicates was **rejected** (§7 D3): ambiguity
   must surface.
5. **Unknown-tag = error.** Any asserted tag not present in the artifact's
   apparatus tag set → `error` `voltage_assertion_unknown_tag`. (No device to
   taint; it is pure operator feedback.)
6. **Taint set.** Collect every tag with an `error`-severity issue
   (invalid-voltage, duplicate). For each apparatus whose tag is tainted: emit a
   `ResolvedApparatus` with `busVoltageV` **cleared to `undefined`** and basis
   `'none'`. A tainted device therefore **cannot** price via a detected fallback
   (fixes Medium-1) and surfaces as the standard "no voltage" question.
7. **Apply** — for each apparatus whose tag has exactly **one valid, non-tainted**
   assertion:
   - effective `busVoltageV = asserted voltageV`, basis `'asserted'`.
   - **Conflict (warning):** if the apparatus already carried a *detected*
     `busVoltageV` **different** from the asserted value → emit `warning`
     `voltage_assertion_conflict` with `detail { tag, detectedV, assertedV, actor,
     source }`. **Operator wins**: effective = asserted, basis = `'asserted'`, the
     device prices. Non-blocking. If they agree, no finding (operator confirmed
     the detected value).
   - emit a `ResolvedApparatus` (never mutate the input apparatus).
8. **Uncovered apparatus** → wrap unchanged with basis
   `busVoltageV !== undefined ? 'detected' : 'none'`.

**Fail-closed semantics:** a malformed (invalid-voltage), ambiguous
(duplicate), or non-existent (unknown) assertion never fabricates or mis-prices a
device. Error-tagged devices are tainted (no detected fallback) **and** any
error finding makes `emitEnvelope` refuse globally (§4.4) — two independent
guards. Conflict is the one *non*-error case: the operator's stated voltage is
authoritative, the device prices, and the override is recorded for audit.

### 4.1 `assessApparatus` change — basis via controlled parameter

> **⚠ SUPERSEDED BY REV 3 (see addendum at end).** The single public
> `assessApparatus(x, voltageBasis?)` shape below was the design intent but is
> **dangerous** (an in-process caller could pass `'asserted'` and forge
> provenance). The implemented + correct shape is a **private basis-taking core**
> split into a one-arg public function and an engine-internal resolved entry.
> The block below is retained for design rationale only — do **not** build to it.

`src/signature/normalize.ts`. The basis arrives as an **explicit parameter** from
the resolved wrapper — it is never read off the (forgeable) apparatus object.
**Implemented form (Rev 3):**

```ts
// PRIVATE core — NOT exported.
function assessCore(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  // voltageBasis defaults to a recomputed detected/none; 'asserted' ONLY ever
  // arrives via the controlled parameter from applyVoltageAssertions.
  const basis: VoltageBasis = voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none')
  // ...included in the constructed ApparatusSignature (only when voltageClass resolved)...
}

// PUBLIC — one-arg only; a caller cannot supply 'asserted'.
export function assessApparatus(x: ExtractedApparatus): ApparatusAssessment {
  return assessCore(x)
}

// ENGINE-INTERNAL — runTakeoff/emit pass the validated/controlled basis.
// Module-exported for emit.ts; DELIBERATELY NOT re-exported from src/index.ts.
export function assessResolvedApparatus(x: ExtractedApparatus, voltageBasis: VoltageBasis): ApparatusAssessment {
  return assessCore(x, voltageBasis)
}
```

A direct public call `assessApparatus(rawApparatus)` (no second arg) can yield
only `'detected'` or `'none'`, never `'asserted'`. `normalizeApparatus` is
unchanged in signature (delegates with no basis). The "no associated bus voltage"
question is unchanged — it now fires when neither a valid assertion nor a detected
value supplied voltage (including tainted devices).

### 4.2 `runTakeoff` wiring

`src/emit/emit.ts`:

```ts
export function runTakeoff(artifact: ExtractionArtifact): TakeoffResult {
  const { resolved, findings } = applyVoltageAssertions(artifact)
  const questions: OperatorQuestion[] = []
  const sigs: ApparatusSignature[] = []
  for (const { apparatus, voltageBasis } of resolved) {
    const a = assessApparatus(apparatus, voltageBasis)
    if (a.signature) { sigs.push(a.signature); questions.push(...a.questions); continue }
    // ...existing unresolved/location handling, now over `resolved` apparatus...
  }
  // ...quantify / match unchanged...
  return { matchedLines, unmatchedCandidates, operatorQuestions: questions, findings }
}
```

### 4.3 Provenance surfacing in the envelope

`MatchedLine.voltageBasis` set from `line.signature.voltageBasis`; the per-line
`notes` string gains voltage + basis, parallel to construction basis:

```ts
notes: `from ${src?.sheet}; construction basis: ${m.mountingBasis}; voltage ${m.line.signature.voltageV}V (${m.voltageBasis})`
```

### 4.4 `emitEnvelope` refuses on blocking findings (makes "blocking" real)

```ts
export function emitEnvelope(result: TakeoffResult, opts: { projectNumber: string }) {
  const blocking = result.findings.filter((f) => f.severity === 'error')
  if (blocking.length > 0) {
    const codes = [...new Set(blocking.map((f) => f.code))].join(', ')
    throw new Error(
      `estimator-takeoff: refusing to emit — ${blocking.length} blocking voltage-assertion finding(s) [${codes}]. ` +
      `Resolve the operator voltage assertions before emitting.`,
    )
  }
  if (result.matchedLines.length === 0) {
    throw new Error('estimator-takeoff: refusing to emit an envelope with zero matched lines — ...')
  }
  // ...existing scope build...
}
```

This closes High-1: a single bad assertion now blocks emission **even when other
lines match**. (Defense-in-depth with the per-device tainting of §4 step 6.)

---

## 5. Python thin collector (Phase B, drawing-nav repo)

`drawing_nav.py` — the `extract` subparser and `cmd_extract`:

```python
# extract subparser (after --no-timestamp):
s.add_argument("--assert-voltage", action="append", default=[],
               metavar="V:TAG[,TAG...]",
               help="operator voltage assertion, repeatable (e.g. 480:MSB-A,MSB-B)")
s.add_argument("--assert-actor")   # optional, carried to evidence
s.add_argument("--assert-note")    # optional, carried to evidence
```

```python
# in cmd_extract, after building `art`:
assertions = []
for spec in a.assert_voltage:            # ["480:TAG1,TAG2", "208:TAG3"]
    v, _, tags = spec.partition(":")
    if not _ or not tags.strip():
        raise SystemExit(f"--assert-voltage: expected V:TAG[,TAG...], got {spec!r}")
    try:
        voltage = int(v)
    except ValueError:
        raise SystemExit(f"--assert-voltage: voltage must be an integer, got {v!r}")
    entry = {"voltageV": voltage, "tags": [t.strip() for t in tags.split(",") if t.strip()],
             "source": "cli"}
    if a.assert_actor: entry["actor"] = a.assert_actor
    if a.assert_note:  entry["note"]  = a.assert_note
    assertions.append(entry)
if assertions:
    art["voltageAssertions"] = assertions
```

- **No semantic validation** — tag existence, conflicts, voltage sanity (≤ 0 etc.),
  and authority are the **engine's** job. The CLI only checks its own flag syntax
  (colon split, `int()` parse), failing with a nonzero exit. A negative or zero
  integer *passes* the CLI (it is syntactically an int) and is rejected
  authoritatively by the engine (`voltage_assertion_invalid_voltage`) — the CLI
  deliberately does not duplicate that judgment.
- **No `at` stamp** in V1 (honors "do not let Python stamp the authoritative
  timestamp"). The artifact's existing `extractedAt` records file-production time.

Usage:

```
drawing-nav extract E01-11.pdf --out e01-11.json \
  --assert-voltage 480:MSB-P1-110-GB,ACC-1-09-FB,ACC-1-10-FB \
  --assert-voltage 208:CRAH-1234-01-1234-FB
```

---

## 6. Test plan

### TS (vitest, `packages/estimator-takeoff/test/`)

`test/voltage-assertions.test.ts` (new):
- **applies asserted voltage** → resolved apparatus classifies; signature
  `voltageBasis === 'asserted'`, `voltageV` = asserted; `findings` empty.
- **unknown tag** → one `error` `voltage_assertion_unknown_tag`; no throw in
  `runTakeoff`; other devices unaffected.
- **duplicate tag** (same tag in two entries, even same voltage) → `error`
  `voltage_assertion_duplicate_tag`; tag tainted.
- **duplicate tag WITH a detected `busVoltageV`** → tainted device does **not**
  price via the detected fallback (Medium-1 regression guard): its tag produces
  no matched line and basis is not `'detected'`.
- **invalid voltage** (`0`, `-1`, `12.5`, `NaN`) → `error`
  `voltage_assertion_invalid_voltage`; tag tainted; no priced line. (High-3.)
- **conflict** (apparatus has detected `busVoltageV: 480`, assertion `208`) →
  `warning` `voltage_assertion_conflict` with `detail.detectedV===480`,
  `detail.assertedV===208`; device **prices** at 208, basis `'asserted'`;
  `emitEnvelope` **succeeds** (non-blocking).
- **emit refusal** — a result with ≥ 1 matched line **and** an `error` finding →
  `emitEnvelope` **throws** `/blocking voltage-assertion/`. (High-1.)
- **provenance non-forgeable** — an artifact whose apparatus JSON carries a stray
  `voltageBasis: 'asserted'` but **no** matching assertion entry → the resulting
  signature basis is `'detected'` (or `'none'`), never `'asserted'`. (High-2.)
- **multi-voltage per-tag** (synthetic fixture: tag A asserted 480, tag B asserted
  208) → each device classifies at *its own* voltage → distinct quantify lines.
- **no assertions** → passthrough identical (back-compat), `findings` empty.

`test/golden-e01-11.test.ts` (rewrite case 2):
- Replace `apparatus.map(a => ({...a, busVoltageV: 480}))` with
  `voltageAssertions: [{ voltageV: 480, tags: [<real main-bus tags>], source: 'cli' }]`.
- Assert matched lines > 0; matched lines carry `voltageBasis === 'asserted'`;
  draw-out LSIG line still present with `mountingBasis === 'estimating_baseline'`;
  `findings` has no `error`.
- Case 1 (pure-auto negative — no assertion, all `busVoltageV` undefined,
  ≥ 20 questions, zero matches, `emitEnvelope` throws on zero lines) **unchanged**.

`test/emit.test.ts`, `test/normalize.test.ts`: extend for the new
`MatchedLine.voltageBasis` / `ApparatusSignature.voltageBasis` fields and the
`findings` channel.

New fixture `test/fixtures/synthetic-mixed-voltage.json`: 2–3 hand-built breaker
apparatus (distinct tags, `busVoltageV` undefined) for the per-tag proof — kept
synthetic so no false electrical claim is made about a real sheet.

### Python (pytest, drawing-nav `tests/`)

`tests/test_assert_voltage.py` (new):
- `--assert-voltage 480:A,B --assert-voltage 208:C` →
  `art["voltageAssertions"] == [{voltageV:480,tags:[A,B],source:cli}, {voltageV:208,tags:[C],source:cli}]`.
- malformed `--assert-voltage foo` (no colon) → nonzero exit.
- non-integer `--assert-voltage 4.8:A` → nonzero exit.
- `--assert-actor`/`--assert-note` carried through.

---

## 7. Design decisions (resolved)

- **D1 — Engine is sole validator/applier** (operator ratified). Python thin.
- **D2 — Provenance enum `voltageBasis: detected|asserted|none`** mirrors the
  existing `mountingBasis`; surfaced on `ApparatusSignature`, `MatchedLine`, and
  the envelope notes.
- **D3 — Duplicate-tag = error + taint, strict.** Any tag asserted more than once
  (even at the same voltage) fails closed *and* is tainted so it cannot price via
  a detected fallback. Idempotent collapse rejected: ambiguity must surface.
- **D4 — `actor`/`note`/`source`/`at` are evidence-only**; the engine never
  branches on them. V1 CLI omits `at` (no Python authority-stamping); `at` is
  reserved for Gate-1 acceptance-time stamping and, if ever supplied by an offline
  artifact, is treated as untrusted metadata.
- **D5 — 'detected' retained for back-compat, no new geometry inference.** The
  engine consumes only the `busVoltageV` the extractor *already* associated and
  always labels it `'detected'`; it adds no nearest-label inference. The
  anti-wrong-bus guarantee lives at the extractor (refuses to broadcast) plus the
  assertion override.
- **D6 — Coded, severity-tagged findings in V1** (`TakeoffFinding`, four stable
  codes). Only a *persistent / queryable* audit store is deferred to Gate-1; the
  in-memory structured findings (code + severity + detail) ship now. (Replaces the
  rev-1 "string-encoded" plan per operator Medium-2.)
- **D7 — Mixed-voltage per-tag proof via a synthetic fixture**; the real `E01-11`
  golden asserts 480 V to actual main-bus tags only (no fabricated 208 V claim).
- **D8 — Invalid voltages rejected engine-side** before application
  (`Number.isInteger(v) && v > 0`); the CLI does not duplicate this judgment.
  (operator High-3.) Optional belt-and-suspenders: a lower-bound guard in
  `classifyVoltage` (`<= 0 → undefined`) is compatible with existing tests and
  may be added in the plan as defense-in-depth.
- **D9 — Provenance is non-forgeable.** Public `ExtractedApparatus` carries no
  `voltageBasis`; basis lives in the engine-only `ResolvedApparatus` wrapper and
  is recomputed from scratch every run. (operator High-2.)
- **D10 — Conflict is a non-blocking warning** (operator wins, device prices,
  audit-recorded). Only `unknown_tag` / `duplicate_tag` / `invalid_voltage` block.
  Resolves the rev-1 inconsistency of labeling conflict "blocking" while still
  emitting. (operator's closing point.)

## 8. Open questions (for operator at spec review)

- **O1 — Real mixed-bus golden?** D7 proves per-tag on a synthetic fixture and
  asserts 480 V on real `E01-11`. If you want a *real* `E01-11` mixed 480/208
  golden, I need the authoritative 480-vs-208 **tag map** (electrical input I will
  not fabricate). Default without it: synthetic-only per-tag proof.
- **O2 — Positive-golden 480 tag set.** The `MSB-*/STS-*/UPS-*/ACC-*/MDP-*` rows
  on `E01-11` are all on the 480 V board. Confirm the assertion targets that full
  tagged set, or a named subset.

> **Note:** rev-1 open question "structured evidence now or deferred?" is now
> **resolved** as D6 (structured coded findings ship in V1) per the operator's
> Medium-2 finding — no longer open.

## 9. Scope / out-of-scope (YAGNI)

**In:** the artifact contract; `applyVoltageAssertions` (engine validator with
voltage validation, taint, coded findings); provenance enum + non-forgeable
wrapper + surfacing; `emitEnvelope` blocking-finding refusal; the
`--assert-voltage` thin CLI; the tests above.

**Out (deferred):** Gate-1 UI and its grouped-tag selection widget; a *persistent
/ queryable* assertion-audit store; multi-sheet or multi-block voltage maps;
voltage *ranges*; auto-detection of voltage from schedule tables; any non-CLI /
non-Gate-1 ingestion channel.

## 10. Files touched

**`apex-power-ops-platform` (branch `estimator-takeoff/voltage-assertions`):**
- Modify `packages/estimator-takeoff/src/extraction/types.ts` — `VoltageAssertion`, `ExtractionArtifact.voltageAssertions`. (**No** `voltageBasis` on `ExtractedApparatus`.)
- Modify `packages/estimator-takeoff/src/signature/types.ts` — `VoltageBasis`, `ApparatusSignature.voltageBasis`.
- Create `packages/estimator-takeoff/src/signature/voltage-assertions.ts` — `ResolvedApparatus`, `applyVoltageAssertions` (validation + taint + coded findings).
- Modify `packages/estimator-takeoff/src/signature/normalize.ts` — private `assessCore(x, voltageBasis?)` + public one-arg `assessApparatus(x)` + engine-internal `assessResolvedApparatus(x, basis)` (NOT re-exported from index.ts); set `signature.voltageBasis`. (Rev 3 — replaces the superseded single 2-arg public function.)
- Modify `packages/estimator-takeoff/src/buckets/types.ts` — `MatchedLine.voltageBasis`, `FindingSeverity`, `VoltageAssertionCode`, `TakeoffFinding`, `TakeoffResult.findings`.
- Modify `packages/estimator-takeoff/src/emit/emit.ts` — call `applyVoltageAssertions`; iterate resolved wrappers; `MatchedLine.voltageBasis`; notes; **`emitEnvelope` blocking-finding refusal**.
- Modify `packages/estimator-takeoff/src/index.ts` — export `applyVoltageAssertions`, `VoltageAssertion`, `VoltageBasis`, `TakeoffFinding`, `VoltageAssertionCode`, `FindingSeverity`.
- Create `packages/estimator-takeoff/test/voltage-assertions.test.ts`.
- Create `packages/estimator-takeoff/test/fixtures/synthetic-mixed-voltage.json`.
- Modify `packages/estimator-takeoff/test/golden-e01-11.test.ts`, `test/emit.test.ts`, `test/normalize.test.ts`.

**`drawing-nav` (separate repo, `C:\Users\jjswe\Tools\drawing-nav`, Phase B):**
- Modify `drawing_nav.py` — `extract` subparser flags + `cmd_extract` assertion parse.
- Create `tests/test_assert_voltage.py`.

---

## Rev 3 — post-merge doc reconciliation (2026-06-25)

Folds the grounded audit of the merged slice. No engine *behavior* changed; this
reconciles the document with the implemented + verified code and records two
decisions. Implemented engine = apex `main` `3d17a8f3`; producer = drawing-nav
`master` `e7a3fb4`.

1. **`assessApparatus` API split (corrects §4.1 and the §3-flow).** The committed
   text described a single public `assessApparatus(x, voltageBasis?)` — a
   forgeable shape (any in-process caller could pass `'asserted'`). The
   **implemented + correct** shape is: a **private** `assessCore(x, basis?)`; a
   **public one-arg** `assessApparatus(x)`; and an **engine-internal**
   `assessResolvedApparatus(x, basis)` that `runTakeoff`/`emit` use and that is
   **not re-exported** from `src/index.ts`. §4.1 is marked superseded inline.

2. **Non-forgeable scope (precise).** `'asserted'` is non-forgeable **through the
   artifact JSON and the public package root**. It is not a hard wall against a
   deep import of `signature/normalize.ts` inside this package
   (`assessResolvedApparatus` is module-exported for `emit.ts`) — acceptable for
   a private single-package consumer (§3.3).

3. **Assertion evidence of record (decision).** The durable evidence IS the input
   `ExtractionArtifact.voltageAssertions[]` (retains `actor`/`note`/`source`/`at`
   verbatim). The engine surfaces a concise per-line summary in emit notes
   (`voltage <V>V (<basis>)`); `actor`/`source` also survive on conflict-finding
   `detail`; `note` is intentionally not echoed. Structured per-line evidence on
   `TakeoffResult` is deferred (YAGNI) until Gate-1 needs it — Gate-1 joins its
   line back to the artifact assertion by tag (§3-flow note).

4. **Hygiene.** Seven src/test files carried a UTF-8 BOM from the Phase-A
   Write→cat-pipe transport; stripped in a hygiene commit on this branch (tsc
   accepted them; no behavior change).

5. **Auditability.** drawing-nav `e7a3fb4` banked as a git bundle on Olares
   (`/home/olares/archive/drawing-nav-e7a3fb4.bundle`) so the Phase-B Python +
   41-test claim is independently verifiable from the host (the host previously
   held only the pre-B1 `42addd2` bundle).

Producer cross-engine note (Phase B, not in the original plan): Codex flagged a
real fail-closed gap — empty tag slots (`480:A,,B`) were silently dropped — now
rejected with `SystemExit` (+3 tests). A second Codex item (`int(" 480 ")`
tolerates surrounding whitespace) was adjudicated a non-defect: it never yields a
silently-wrong value and is symmetric with the spec's lenient tag-whitespace
trim; left as-is pending any operator preference for strictness.
