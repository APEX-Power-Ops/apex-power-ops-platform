# Estimator-Takeoff Voltage Assertions — Design

**Date:** 2026-06-25
**Branch:** `estimator-takeoff/voltage-assertions` (off `main` @ `99e3d74f`)
**Status:** ratified design → spec (engine-side application ratified by operator 2026-06-25)
**Author:** CC (technical authority), operator-ratified

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
operator's statement.

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
  every rule below (unknown-tag rejection, duplicate-tag rejection,
  conflict-recording, provenance). One honesty path for CLI, Gate-1, and tests.
- **Python `drawing-nav` CLI = thin assertion collector.** Parses
  `--assert-voltage`, emits the raw assertion block into the artifact, stamps
  `source: 'cli'` and optional `actor`/`note`. It performs **no** semantic
  validation (tag existence, conflicts, authority). Format-parsing of its own
  flag (colon split, integer voltage) is the only check it does.
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

New: a pure pass runs **before** the apparatus loop and resolves effective
voltage from assertions, returning the resolved apparatus + any blocking
findings:

```
runTakeoff(artifact)
  ├─ applyVoltageAssertions(artifact) → { apparatus, questions }   // NEW pure pass
  └─ for x of apparatus → assessApparatus(x)   // classifyVoltage now sees asserted voltage
```

`applyVoltageAssertions` is **pure and clock-free** (preserves determinism /
golden tests). It branches only on `voltageV` and `tags`; `actor`/`note`/
`source`/`at` are carried through as evidence and never affect engine logic.

---

## 3. The Contract (data shapes)

### 3.1 `VoltageAssertion` (new, `src/extraction/types.ts`)

```ts
export interface VoltageAssertion {
  voltageV: number          // asserted nominal voltage (V), applied to every listed tag
  tags: string[]            // device tags this assertion covers (>= 1)
  actor?: string            // who asserted — carried to evidence; engine NEVER branches on it
  note?: string             // free-text rationale — carried to evidence
  source?: 'cli' | 'gate1'  // channel that produced the assertion — carried to evidence
  at?: string               // OPTIONAL ISO author-time; UNTRUSTED metadata.
                            // The engine never trusts `at` for ordering or authority.
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

### 3.3 `ExtractedApparatus` += transient `voltageBasis`

```ts
export interface ExtractedApparatus {
  // ...existing fields...
  voltageBasis?: 'detected' | 'asserted'   // NEW — engine-internal, set by applyVoltageAssertions.
                                           // The Python producer NEVER sets this.
                                           // Absent → assessApparatus derives 'detected'/'none'.
}
```

### 3.4 `ApparatusSignature` += `voltageBasis` (mirrors `mountingBasis`)

`src/signature/types.ts`:

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

- `asserted` — effective voltage came from an operator assertion (authoritative).
- `detected` — effective voltage came from the extractor's `busVoltageV`
  (back-compat; used only as a fallback, provenance-surfaced so the estimator
  sees it was **not** operator-confirmed).
- `none` — no voltage at all (no signature is produced in this case; the value
  exists in the union only for type-parallelism with `MountingBasis`).

### 3.5 `MatchedLine` += `voltageBasis`

`src/buckets/types.ts`:

```ts
export interface MatchedLine {
  ref: string; qty: number; block: string
  mountingBasis: MountingBasis
  voltageBasis: VoltageBasis   // NEW
  line: QuantifiedLine
}
```

---

## 4. `applyVoltageAssertions` — the validator/applier

New file `src/signature/voltage-assertions.ts`.

```ts
export interface AppliedAssertions {
  apparatus: ExtractedApparatus[]   // resolved copies (effective busVoltageV + voltageBasis)
  questions: OperatorQuestion[]     // blocking findings (unknown tag / duplicate tag / conflict)
}

export function applyVoltageAssertions(artifact: ExtractionArtifact): AppliedAssertions
```

**Algorithm:**

1. **No assertions** → return `{ apparatus: artifact.apparatus, questions: [] }`
   unchanged (full back-compat).
2. **Build (tag → voltageV) index** by flattening every `(entry, tag)` pair
   across all assertion entries.
3. **Duplicate-tag = fail closed (Pin: duplicate/conflicting same tag).** Any
   tag appearing in **more than one** `(entry, tag)` pair — *regardless of
   whether the voltages agree* — produces a blocking finding
   `voltage_assertion_duplicate_tag` and is **excluded** from application (its
   intent is ambiguous; no voltage is applied). Exact-duplicate idempotent
   collapse was **rejected** (see §7 D3): ambiguity must surface, not be
   silently resolved.
4. **Unknown-tag = fail closed (Pin 1).** Any asserted tag not present in the
   artifact's apparatus tag set → blocking finding
   `voltage_assertion_unknown_tag` (operator typo / wrong sheet). Never silently
   ignored.
5. **Apply** — for each apparatus whose tag has exactly **one** valid assertion:
   - set effective `busVoltageV = asserted voltageV`, `voltageBasis = 'asserted'`.
   - **Conflict (Pin 2):** if the apparatus already carried an extractor
     `busVoltageV` *different* from the asserted value → assertion **wins**
     (effective = asserted, basis = `'asserted'`) **and** record a blocking
     finding carrying the full detail (`tag`, `detected=<V>`, `asserted=<V>`,
     `actor`, `source`). If they agree, no conflict (operator confirmed the
     detected value).
   - emit a resolved **copy** (never mutate the input apparatus).
6. **Uncovered apparatus** → passed through unchanged; `assessApparatus` derives
   `voltageBasis = busVoltageV !== undefined ? 'detected' : 'none'`.

**Fail-closed semantics:** an unknown/duplicate/typo'd assertion never fabricates
or mis-prices a device. The affected device gets **no** effective voltage from
the bad assertion and surfaces as a question; the rest of the takeoff proceeds.
`emitEnvelope` already throws on zero matched lines, so a wholesale-bad assertion
set fails closed end-to-end.

> **Question interaction (resolve in the plan).** A *duplicate-tagged* device is
> excluded from application, so it then also hits the standard "no associated bus
> voltage" question in `assessApparatus` — both questions are legitimate (the
> assertion was ambiguous *and* the device still has no usable voltage); the plan
> may choose to suppress the redundant one or keep both. An *unknown-tag*
> assertion has no matching device at all, so it produces only the one
> unknown-tag question.

### 4.1 `assessApparatus` change

`src/signature/normalize.ts` — set the signature's `voltageBasis`:

```ts
const voltageBasis: VoltageBasis =
  x.voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none')
// ...included in the constructed ApparatusSignature (only when voltageClass resolved)
```

No other normalize logic changes. The "no associated bus voltage" question is
unchanged — it now fires only when neither an assertion nor a detected value
supplied voltage.

### 4.2 `runTakeoff` wiring

`src/emit/emit.ts`:

```ts
export function runTakeoff(artifact: ExtractionArtifact): TakeoffResult {
  const { apparatus, questions: assertionQuestions } = applyVoltageAssertions(artifact)
  const questions: OperatorQuestion[] = [...assertionQuestions]
  // ...loop over `apparatus` (not artifact.apparatus); rest unchanged...
}
```

### 4.3 Provenance surfacing in the envelope

`emit.ts` — `MatchedLine.voltageBasis` set from `line.signature.voltageBasis`;
the per-line `notes` string gains voltage + basis, parallel to construction
basis:

```ts
notes: `from ${src?.sheet}; construction basis: ${m.mountingBasis}; voltage ${m.line.signature.voltageV}V (${m.voltageBasis})`
```

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
    entry = {"voltageV": int(v), "tags": [t.strip() for t in tags.split(",") if t.strip()],
             "source": "cli"}
    if a.assert_actor: entry["actor"] = a.assert_actor
    if a.assert_note:  entry["note"]  = a.assert_note
    assertions.append(entry)
if assertions:
    art["voltageAssertions"] = assertions
```

- **No semantic validation** — tag existence, conflicts, and authority are the
  engine's job. The only checks are format (`int(v)` and the colon split), which
  fail the CLI with a nonzero exit (a thin collector validating *its own flag
  syntax*, not electrical truth).
- **No `at` stamp** in V1 (honors "do not let Python stamp the authoritative
  timestamp"). The artifact's existing `extractedAt` already records when the
  file was produced.

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
  `voltageBasis === 'asserted'`, `voltageV` = asserted.
- **unknown tag** → one blocking question; no throw; other devices unaffected.
- **duplicate tag** (same tag in two entries, even same voltage) → blocking
  question; tag not applied.
- **conflict** (apparatus has detected `busVoltageV: 480`, assertion `208`) →
  effective `208`, basis `'asserted'`, conflict question records `480`→`208`.
- **multi-voltage per-tag** (synthetic fixture: tag A asserted 480, tag B
  asserted 208) → each device classifies at *its own* voltage → distinct
  quantify lines. Proves per-tag, not block-scoped.
- **no assertions** → passthrough identical (back-compat).

`test/golden-e01-11.test.ts` (rewrite case 2):
- Replace `apparatus.map(a => ({...a, busVoltageV: 480}))` with
  `voltageAssertions: [{ voltageV: 480, tags: [<real main-bus tags>], source: 'cli' }]`.
- Assert matched lines > 0; matched lines carry `voltageBasis === 'asserted'`;
  the draw-out LSIG line still present with `mountingBasis === 'estimating_baseline'`.
- Case 1 (pure-auto negative — no assertion, all `busVoltageV` undefined,
  ≥20 questions, zero matches, `emitEnvelope` throws) **unchanged**.

`test/emit.test.ts`, `test/normalize.test.ts`: extend assertions for the new
`MatchedLine.voltageBasis` / `ApparatusSignature.voltageBasis` fields.

New fixture `test/fixtures/synthetic-mixed-voltage.json`: 2–3 hand-built breaker
apparatus (distinct tags, `busVoltageV` undefined) for the per-tag proof — kept
synthetic so no false electrical claim is made about a real sheet.

### Python (pytest, drawing-nav `tests/`)

`tests/test_assert_voltage.py` (new):
- `--assert-voltage 480:A,B --assert-voltage 208:C` →
  `art["voltageAssertions"] == [{voltageV:480,tags:[A,B],source:cli}, {voltageV:208,tags:[C],source:cli}]`.
- malformed `--assert-voltage foo` (no colon) → nonzero exit.
- `--assert-actor`/`--assert-note` carried through.

---

## 7. Design decisions (resolved)

- **D1 — Engine is sole validator/applier** (operator ratified). Python thin.
- **D2 — Provenance enum `voltageBasis: detected|asserted|none`** mirrors the
  existing `mountingBasis` exactly; surfaced on `ApparatusSignature`,
  `MatchedLine`, and the envelope notes.
- **D3 — Duplicate-tag = blocking, strict.** Any tag asserted more than once
  (even at the same voltage) fails closed. Idempotent collapse rejected:
  ambiguity must surface.
- **D4 — `actor`/`note`/`source`/`at` are evidence-only**; the engine never
  branches on them. V1 CLI omits `at` (no Python authority-stamping); `at` is
  reserved for Gate-1 acceptance-time stamping and, if ever supplied by an
  offline artifact, is treated as untrusted metadata.
- **D5 — 'detected' retained for back-compat, no new geometry inference.** The
  engine consumes only the `busVoltageV` the extractor *already* associated; it
  adds no nearest-label inference. The anti-wrong-bus guarantee lives at the
  extractor (refuses to broadcast) plus the assertion override.
- **D6 — Findings via the existing `OperatorQuestion` channel**, with full
  structured detail encoded in the strings (consistency + YAGNI). A queryable
  structured audit store is deferred to Gate-1.
- **D7 — Mixed-voltage per-tag proof via a synthetic fixture**; the real
  `E01-11` golden asserts 480 V to actual main-bus tags only (no fabricated
  208 V claim about that sheet).

## 8. Open questions (for operator at spec review)

- **O1 — Real mixed-bus golden?** D7 proves per-tag on a synthetic fixture and
  asserts 480 V on real `E01-11`. If you want a *real* `E01-11` mixed 480/208
  golden, I need the authoritative 480-vs-208 **tag map** (electrical input I
  will not fabricate). Default without it: synthetic-only per-tag proof.
- **O2 — Structured evidence now or deferred?** D6 encodes conflict detail in
  question strings for V1. Confirm that's acceptable, or pull the structured
  `VoltageAssertionRecord[]` audit forward into this slice.
- **O3 — Positive-golden 480 tag set.** The `MSB-*/STS-*/UPS-*/ACC-*/MDP-*` rows
  on `E01-11` are all on the 480 V board. Confirm the assertion targets that full
  tagged set, or a named subset.

## 9. Scope / out-of-scope (YAGNI)

**In:** the artifact contract; `applyVoltageAssertions` (engine validator);
provenance enum + surfacing; the `--assert-voltage` thin CLI; the tests above.

**Out (deferred):** Gate-1 UI and its grouped-tag selection widget; a persistent
/ queryable assertion audit store; multi-sheet or multi-block voltage maps;
voltage *ranges*; auto-detection of voltage from schedule tables; any non-CLI /
non-Gate-1 ingestion channel.

## 10. Files touched

**`apex-power-ops-platform` (branch `estimator-takeoff/voltage-assertions`):**
- Modify `packages/estimator-takeoff/src/extraction/types.ts` — `VoltageAssertion`, `ExtractionArtifact.voltageAssertions`, `ExtractedApparatus.voltageBasis`.
- Modify `packages/estimator-takeoff/src/signature/types.ts` — `VoltageBasis`, `ApparatusSignature.voltageBasis`.
- Create `packages/estimator-takeoff/src/signature/voltage-assertions.ts` — `applyVoltageAssertions`.
- Modify `packages/estimator-takeoff/src/signature/normalize.ts` — set `signature.voltageBasis`.
- Modify `packages/estimator-takeoff/src/emit/emit.ts` — call `applyVoltageAssertions`; `MatchedLine.voltageBasis`; notes.
- Modify `packages/estimator-takeoff/src/buckets/types.ts` — `MatchedLine.voltageBasis`.
- Modify `packages/estimator-takeoff/src/index.ts` — export `applyVoltageAssertions`, `VoltageAssertion`, `VoltageBasis`.
- Create `packages/estimator-takeoff/test/voltage-assertions.test.ts`.
- Create `packages/estimator-takeoff/test/fixtures/synthetic-mixed-voltage.json`.
- Modify `packages/estimator-takeoff/test/golden-e01-11.test.ts`, `test/emit.test.ts`, `test/normalize.test.ts`.

**`drawing-nav` (separate repo, `C:\Users\jjswe\Tools\drawing-nav`, Phase B):**
- Modify `drawing_nav.py` — `extract` subparser flags + `cmd_extract` assertion parse.
- Create `tests/test_assert_voltage.py`.
