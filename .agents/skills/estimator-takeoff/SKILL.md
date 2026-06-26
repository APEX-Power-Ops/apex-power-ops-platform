---
name: estimator-takeoff
description: Turn an electrical drawing sheet into a priced NETA breaker takeoff - drawing-nav extract, per-tag operator voltage assertions, then the fail-closed run-artifact runner with a per-row reconciliation. Use when asked to price or estimate breaker testing from a drawing package.
---

# estimator-takeoff (agent workflow)

**Source of truth for the full contract:** `packages/estimator-takeoff/SKILL.md` in the apex-power-ops-platform repo. Read it if any rule below is ambiguous. This file is the short, executable version.

## When to use

A drawing sheet (one-line / switchgear) needs a priced NETA breaker takeoff that accounts for every device (a per-row reconciliation), not just a total.

## Steps

1. **Extract** (Windows, the drawing-nav repo - the PDF + producer live there):
   ```
   .venv/Scripts/python.exe drawing_nav.py extract "<PDF>" --page <N> --no-timestamp \
     --assert-voltage <V>:<TAG1,TAG2,...> --out <sheet>.artifact.json
   ```
   Scope to the sheet's page. Repeat `--assert-voltage` per voltage. Assert ONLY tags whose voltage you have confirmed.
2. **Run** (Olares host, the apex repo):
   ```
   pnpm --filter @apex/estimator-takeoff run-artifact \
     run <artifact.json> --project <PROJECT_NO> [--out <report.json>] [--allow-open-items]
   ```
   NO `--` before `run` (this pnpm forwards args straight to the CLI; a stray `--` becomes args[0] and the runner exits 2). The artifact path resolves relative to `packages/estimator-takeoff` (the script's working dir) - use an absolute path or one relative to that package.
3. **Read the reconciliation.** Confirm `accounted: true`. Decide clean vs partial (below).

## The voltage gate

The engine prices an LV breaker only when it has a voltage. The extractor refuses to guess voltage on a multi-bus sheet; the operator asserts it per tag. Detected voltage labels are hints only - the engine consumes the explicit assertion. Unknown or duplicate asserted tag -> ERROR (hard block). Assertion-vs-detected conflict -> operator wins, recorded as evidence.

## Failure rules (NEVER bypass)

- **ERROR findings -> non-zero exit, NO envelope.** `--allow-open-items` does NOT relax this. Fix the assertion or producer; do not launder it.
- **Zero matched lines -> hard block.**
- **`status: clean`** only when no row is `unmatched`/`question`, zero operator questions, zero error findings.
- **`status: partial_preview`** (requires `--allow-open-items`): open items remain. The envelope is NOT a complete bid. **Never report its `bid_cents` as a final estimate.** Resolve the open items (assert the remaining buses, confirm device types, add catalog rules) and re-run to `clean`, or carry the open items forward explicitly.

## Reading the report

Every input row gets a disposition: `matched | associated_source | unmatched | question | ignored`. An ambiguous/unclassifiable row is ALWAYS a `question` (blocks clean), never silently ignored; `ignored` is reserved for positively-identified non-breaker devices. Watch `unresolved_rows` (open dispositions) and `accounted` (false = engine bug, hard fail).

## Out of scope (do not improvise)

Gate UIs (voltage-assert / line-review), a general spec-parser / scope-profile layer, and non-breaker apparatus families (relays, transformers, etc.) are future design work, not runner invocations.
