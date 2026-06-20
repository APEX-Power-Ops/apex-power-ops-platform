# Agent-runner live e2e proof — 2026-06-20

The durable multi-agent loop, proven end-to-end with a **real headless `claude -p`**
(not the offline fake agent). T8 live confirmation, complementing the 54-test offline suite.

## What ran
- **DB:** `orchestration_dev` (the engine's default target).
- **Throwaway base:** `e2e-base-2026-06-20` off `main` (`74689780`), not checked out.
- **Enqueue (T7 CLI):**
  `apex-jobs enqueue --kind agent --dispatch-id 2026-06-20-agent-canary --title "agent canary" --base-ref e2e-base-2026-06-20 --env-required host --prompt "Create a file HELLO.md containing the single line: apex agent works."`
- **Run:** `run_pool(as_='cc', env='host', concurrency=1, max_jobs=1)` → real `claude` v2.1.183.

## Result (verified)
- `run_pool` → `{"status": "succeeded", "no_changes": false}`; job parked `awaiting_promotion`.
- The agent created `HELLO.md` with exactly `apex agent works.` (captured diff: `HELLO.md | 1 +`).
- Promotion via the **T7 `approve` verb** (`apex-jobs approve --gate <id> --by operator` → `engine.promote`):
  - `e2e-base-2026-06-20` advanced to no-ff merge `7d28b242` ("promote 2026-06-20-agent-canary");
  - `e2e-base:HELLO.md` == `apex agent works.`; job → `succeeded`;
  - agent branch `job/...` + worktree `~/.apex-jobs/runs/...` removed.
- Throwaway `e2e-base-2026-06-20` deleted after proof.

## Live flag pinned (the plan's open risk, now closed)
`AGENT_CMD["cc"]` = `claude -p {prompt} --output-format json --permission-mode acceptEdits`.
- Headless `claude -p` denies file writes under the default permission mode (confirmed: a
  no-flag pre-flight returned `permission_denials: [Write]`). `acceptEdits` auto-accepts edits.
- `acceptEdits` is the **conservative** posture: it accepted the Write but **denied** the agent's
  unprompted attempt to run `Bash`. Agents that must run commands would need `bypassPermissions`
  — a deliberate, separate security decision, NOT adopted here.

## Cost
~$0.32 total across pre-flight + canary (claude-opus-4-8[1m]).
