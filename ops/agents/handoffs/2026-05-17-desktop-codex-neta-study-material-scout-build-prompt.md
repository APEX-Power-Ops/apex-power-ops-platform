# Desktop Codex Prompt - NETA Study Material Scout/Build

You are Desktop Codex acting as delegated orchestration governor for the non-PM NETA Study Material lane under VS Code Codex technical authority.

## Objective

Create a bounded scout/build handoff for the NETA Study Material lane that helps organize study material, question-bank scaffolding, source inventory, and content QA needs without touching shared product code or production surfaces.

## Authority Band

Band A/B only.

## Required Reads

- `docs/operations/APEX-PARALLEL-LANE-ORCHESTRATION-GOVERNANCE-PLAN-2026-05-17.md`
- `ops/agents/handoffs/2026-05-17-desktop-codex-parallel-lane-orchestration-queue.md`
- Any existing NETA-related docs or handoffs you can identify inside the repo
- Source-domain NETA paths only for read-only inventory if available under `C:\APEX Platform\source-domains\`

## Allowed Writes

Write one handoff only:

- `ops/agents/handoffs/2026-05-17-desktop-codex-neta-study-material-scout-build-closeout.md`

## Forbidden Writes

- `apps/`
- `packages/`
- `infra/`
- `docs/authority/`
- `PROJECT_STATUS.md`
- `.env*`
- source-domain repositories
- any binary workbook, PDF, or generated output

## Allowed Work

1. Inventory relevant NETA study material sources.
2. Propose an artifact map for outlines, question-bank scaffolds, and QA checklists.
3. Identify source gaps and unclear ownership.
4. Recommend the next bounded NETA packet.
5. Return a concise evidence summary.

## Forbidden Work

1. Do not move or import source-domain files.
2. Do not edit shared code or package files.
3. Do not run workbook macros.
4. Do not create production artifacts.
5. Do not stage, commit, push, publish status, or fast-forward Olares.
6. Do not request credentials or access hosted services.

## Validation

Run:

```powershell
git diff --check -- ops/agents/handoffs/2026-05-17-desktop-codex-neta-study-material-scout-build-closeout.md
```

## Closeout Status

Return exactly one of:

- `READY_FOR_VSCODE_REVIEW`
- `READY_FOR_JASON_DECISION`
- `BLOCKED_CAPABILITY_GAP`
- `ABORTED_SCOPE_WIDENING`

## Stop Conditions

Stop if the work requires shared code edits, source import, schema, credentials, hosted services, macros, unclear source ownership, or Jason manually relaying technical context.
