# E2E proof — live `codex exec review` via apex-jobs (IRP cross-engine gate)

**Date:** 2026-06-22 · **Lane:** `orchestration/codex-executor` · **DB:** `orchestration_dev`
**Runner:** `apex_jobs.agent_runner.run_review_job` (Cycles 2–3) · driver `ops/orchestration/e2e_codex_review.py`

## What this proves

A `kind='agent'` **review** job runs a real cross-engine review through the durable
runner: it checks out the ref under review (`payload.review_head`, detached) in an
isolated worktree, runs `codex exec review --base <base_ref>`, captures the findings
(stdout) as the run result, and **opens NO promotion gate** — a review only reports,
there is nothing to merge. This is the structural bottleneck the IRP needs solved:
Claude cannot run a non-Claude engine, so the Codex pass runs as an apex-jobs job.

## Run

- Setup: throwaway `e2e-review-base` at HEAD; `e2e-review-head` = base + one file
  `REVIEW_ME.py` with `def add(a, b): return a - b` (an intentional add/sub bug).
- Enqueue: `kind='agent'`, `target='codex'`, `base_ref='e2e-review-base'`,
  `payload.review_head='e2e-review-head'`.
- Drove `run_review_job` **directly** (not `run_pool`) so the e2e never claims one of
  the unrelated pending jobs in `orchestration_dev`.
- Engine: codex-cli 0.141.0, model gpt-5.5, reasoning effort xhigh, headless (`approval: never`).

## Result — PASS

- `run` status `succeeded`; result `is_review=True`, `base_ref=e2e-review-base`,
  `review_head=e2e-review-head`; run.branch recorded `e2e-review-head` (audit).
- **Codex caught the planted bug** (findings, 412 chars):
  > The new `add` helper performs subtraction instead of addition, so the patch
  > introduces incorrect behavior.
  > - [P2] Return the sum from add — REVIEW_ME.py:3-3 … `add(2, 1)` returns `1`
  >   rather than `3`.
- **No promotion gate** opened (`gates_for == []`); job terminal at `succeeded`
  (NOT `awaiting_promotion`) — the capture-result / no-promotion review variant.
- Git branches + worktree cleaned up; the completed job row remains in
  `orchestration_dev` as the audit artifact.

## Offline coverage (TDD, `orchestration_test`)

`tests/test_agent_runner.py` — `_review_argv` builds `codex exec review --base`;
`run_review_job` captures findings + opens no promotion gate (success + failure);
`_run_one` routes review jobs to the review path. Suite 11/11 green.

Note: codex emits a benign `could not find bubblewrap on PATH` warning to stderr and
falls back to its bundled sandbox — no action needed for headless review runs.
