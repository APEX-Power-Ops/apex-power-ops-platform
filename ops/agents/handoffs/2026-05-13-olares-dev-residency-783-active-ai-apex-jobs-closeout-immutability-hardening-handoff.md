# Olares Dev Residency Packet 783 - Active AI Apex Jobs Closeout Immutability Hardening

Date: 2026-05-13
Packet: 783
Status: Closed
Scope: direct `apex-jobs` run-ledger hardening inside the admitted AI/operator boundary

## Purpose

Land one bounded repo-side hardening slice in the already-selected `services/mcp/apex-jobs` surface so the run ledger refuses post-close mutation and carries direct package-level contract coverage for closeout, filtering, and promotion rules.

## Execution Result

Shared ledger types and logic for closeout, filtering, and promotion now live in `services/mcp/apex-jobs/src/ledger.ts` and are used by both the stdio and HTTP transports.

`end_run` now refuses any run that is already closed, whether that closure is represented by a non-`running` status or an existing `completed_at` timestamp.

`list_runs` filtering and `promote_packet` supporting-run selection now route through the same shared ledger module instead of duplicating that contract in both transports.

Focused package-level tests were added under `services/mcp/apex-jobs/tests/ledger.test.mjs`, and the source-owned README plus the repo-owned apex-jobs trust contract now state the closed-run immutability rule explicitly.

## Validation

Executed:

```powershell
corepack pnpm --filter apex-jobs build
corepack pnpm --filter apex-jobs test
```

Observed result:

1. package build passed cleanly,
2. seven focused contract tests passed,
3. the direct package test path now proves that closed runs cannot be rewritten,
4. direct tests now also prove `since` filtering plus promotion refusal and success behavior.

## Boundaries Preserved

1. The admitted MCP trio remains `apex-fs`, `apex-db`, and `apex-jobs`.
2. No broader queue controller or `ai_tasks` admission was introduced.
3. Promotion still requires successful `env=host` evidence.
4. No host-qualified proof was claimed; the governed live-DSN blocker remains external to this repo slice.

## Next Candidate

Materialize the governed workstation and authoritative-host live-DSN sources, then rerun the workstation baseline and host managed drills using the hardened `apex-jobs` ledger path as the evidentiary floor.