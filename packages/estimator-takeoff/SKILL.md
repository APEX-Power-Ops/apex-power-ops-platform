---
name: estimator-takeoff
description: Use when turning an electrical drawing package into a priced NETA breaker takeoff - drives the drawing-nav extract, the operator voltage-assertion gate, the fail-closed run-artifact runner, and reading its reconciliation. Anchored to the canonical STACK PHX02A E01-11 run.
---

# estimator-takeoff: drawing package to reconciled, priced NETA takeoff

Turns an electrical drawing package into a priced breaker-testing estimate envelope, accounting for EVERY device on the sheet so none is silently lost. The engine is deterministic and fail-closed: it prices only what it can positively classify, and surfaces everything else as an explicit operator question rather than dropping it.

**The contract, in one line:** a clean priced envelope is emitted ONLY when every input row resolved; anything unresolved either blocks the run or is emitted as a loudly-labeled `partial_preview` that is NOT a complete bid.

## When to use

- You have a drawing package (a one-line / switchgear sheet) and need a priced NETA breaker takeoff.
- You need to know exactly what was counted, what was not, and why - with a per-row reconciliation, not just a total.

Do NOT use it as a black-box price. The output is only trustworthy when you read the reconciliation (below) and confirm the open items.

## The pipeline (4 stages)

```
drawing-nav extract        operator voltage           run-artifact (host)         read the
(Windows, where the   ->   assertions (per tag)  ->   parse + reconcile +    ->   reconciliation
PDF + producer live)       baked into the artifact    fail-closed emit            (clean vs partial)
```

The producer (drawing-nav) and the engine (@apex/estimator-takeoff) are SEPARATE repos on SEPARATE hosts. drawing-nav runs on Windows (the proprietary PDF is not in the apex repo); the engine runs on the Olares host. Provenance is pinned by a manifest + drift-check so the two never drift silently.

### Stage 1 - Extract (Windows, drawing-nav)

Run drawing-nav's `extract` on the target sheet. Scope to the sheet's page; use `--no-timestamp` for a reproducible artifact:

```
.venv/Scripts/python.exe drawing_nav.py extract "<PATH TO PDF>" \
  --page <N> --no-timestamp \
  --assert-voltage 480:MSB-P1-110-GB,ACC-1-09-FB,ACC-1-10-FB \
  --out <sheet>.artifact.json
```

The output is an `ExtractionArtifact`: `{ pdf, apparatus[], profileWarnings?, voltageAssertions? }`. Each `apparatus` row carries `raw`, `tag?`, `sheet`, `page`, `bbox`, `evidence` (one-line | panel-schedule | switchgear-schedule | power-plan), and optional `busVoltageV` / `mountingHint`. The extractor deliberately REFUSES to broadcast a bus voltage on a multi-bus / MV-incoming sheet (it emits a `profileWarning` instead) - voltage is an operator input, never guessed.

### Stage 2 - Voltage assertions (the operator gate)

The engine prices an LV breaker only when it has a voltage. On a real multi-bus sheet the extractor leaves voltage unresolved, so the operator asserts it PER TAG via `--assert-voltage <volts>:<TAG1,TAG2,...>` (repeatable per voltage). The flag bakes a `voltageAssertions` array into the artifact. Rules the engine enforces (fail-closed):

- Voltage must be a positive integer. Detected voltage labels are HINTS only; the engine consumes the explicit per-tag assertion.
- Unknown asserted tag (no matching device) -> a blocking ERROR finding (the run hard-fails; fix the tag).
- Duplicate tag -> ERROR. A malformed or empty tag list is rejected by drawing-nav's `--assert-voltage` flag at extract time.
- Assertion vs detected-voltage CONFLICT -> the operator assertion WINS, and the conflict is recorded as a warning with both values (evidence of record).

Assert only the tags you have confirmed. Leaving a bus unasserted is safe: those rows surface as `missing_voltage` questions, not bad prices.

### Stage 3 - Run (Olares host)

```
pnpm --filter @apex/estimator-takeoff run-artifact \
  run <artifact.json> --project <PROJECT_NO> [--out <report.json>] [--allow-open-items]
```

Two gotchas: (1) do NOT put `--` before `run` - this pnpm forwards the args straight to the CLI, and a stray `--` becomes `args[0]` and the runner exits 2 with usage. (2) Artifact paths resolve relative to `packages/estimator-takeoff` (the script runs in the package directory), NOT the caller's shell directory - pass an absolute path or one relative to that package.

Pipeline: read file -> `parseArtifact` (fail-closed runtime validator) -> `runTakeoff` (assess, quantify, match, build exhaustive dispositions) -> assert the exhaustiveness invariant -> build the reconciliation report -> decide emit -> print/write the report. `--out` writes the report JSON; otherwise it prints the human report. Exit code is non-zero on any block.

### Stage 4 - Read the reconciliation

The report accounts for every input row. Key fields:

- `apparatus_in` - rows in the artifact. `matched_lines` (qty) - priced catalog lines. `associated_sources` - non-representative occurrences folded into a counted device. `unmatched_candidates` - breaker-shaped lines with no catalog rule. `operator_questions` - advisory + per-row questions (includes legend/profile warnings). `unresolved_rows` - dispositions still open (status `unmatched` or `question`); this is the honest "how much is not done" count. `ignored` - positively-identified non-breaker devices (the ONLY safe-to-ignore class). `error`/`warning` findings. `accounted` - true only when the dispositions internally reconcile with the produced lines (a false here is a hard failure - an engine bug, never user input).
- Per-row table: `inputIndex  status  reasonCode  tag  ref`. Statuses: `matched | associated_source | unmatched | question | ignored`. An ambiguous or unclassifiable row is ALWAYS a `question` (it blocks clean output), never silently ignored.

## The fail-closed contract (read before trusting any output)

- **Error findings are an unconditional hard block.** A blocking finding (e.g. an unknown asserted tag) means non-zero exit, NO envelope, and `--allow-open-items` does NOT relax it. Fix the assertion/producer, do not launder it.
- **Zero matched lines blocks.** Nothing to price -> non-zero exit, no envelope.
- **clean** is computed over the EXHAUSTIVE dispositions: no row is `unmatched` or `question`, zero operator questions, zero error findings. Only then is the envelope emitted as `status: clean`.
- **partial_preview** (only with `--allow-open-items`): open items exist (unmatched/questions, no error findings). The runner emits an envelope from the matched lines, stamps `partial_preview`, and prints a loud `WARNING: partial preview - N unresolved row(s) ...; envelope is NOT a complete bid`.

**NEVER treat a `partial_preview` envelope as a bid.** Its `bid_cents` covers only the resolved lines; the unresolved rows are real work that is not yet priced. Resolve the open items (assert their voltage, confirm device types, add catalog rules) and re-run until `status: clean`, or carry the open items forward explicitly.

## Worked example - STACK PHX02A, sheet E01-11

The canonical fixture (`test/fixtures/stack-phx02a-e01-11.artifact.json`, provenance pinned by its `.manifest.json` + the drift-check test) is the real extract of a primary-block one-line: 41 devices, with 480V asserted for the three confirmed draw-out mains (`MSB-P1-110-GB`, `ACC-1-09-FB`, `ACC-1-10-FB`).

```
pnpm --filter @apex/estimator-takeoff run-artifact \
  run test/fixtures/stack-phx02a-e01-11.artifact.json --project PHX02A-DEMO --allow-open-items
```

```
WARNING: partial preview - 38 unresolved row(s) (0 unmatched candidate-lines, 39 flagged questions); envelope is NOT a complete bid
Reconciliation: partial_preview
  apparatus_in         41
  matched_lines        2  (qty 3)
  associated_sources   0
  unmatched_candidates 0
  operator_questions   39
  unresolved_rows      38
  ignored              0
  findings             0 error, 0 warning
  accounted            true
  bid_cents            198000
```

How to read it: the 3 asserted mains priced (`matched_lines 2 (qty 3)` -> LV Draw-Out LSIG breakers, `bid_cents 198000`, validator-clean). The other 38 rows are NOT lost - they surface as `question` dispositions (the un-asserted breakers as `missing_voltage`; the 8 tagged `STS-P1-110` transfer rows carry an LSI trip so they surface as `transfer_parent_conflict`; the 5 `UPS-*` rows as `non_breaker_carries_rating`) plus the sheet's MV/LV profile warning, totalling 39 operator questions. `accounted true` confirms every one of the 41 rows is reconciled. This is a `partial_preview`, not a bid: to turn it into a real estimate, assert the remaining buses' voltages and confirm the non-breaker device types, then re-run.

## Deferred (not part of this skill - do not improvise them)

The following are designed-or-future, NOT instructions to execute here: the two human review/approval gates (Gate-1 voltage-assert UI, Gate-2 line review); a general spec-parser / scope-profile layer; apparatus-family generalization beyond breakers (relays, transformers, etc.). If a task needs one of these, treat it as new design work, not a runner invocation.
