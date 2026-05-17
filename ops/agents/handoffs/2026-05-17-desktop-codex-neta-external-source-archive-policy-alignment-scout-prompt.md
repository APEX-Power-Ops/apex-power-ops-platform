# Desktop Codex NETA External Source Archive Policy Alignment Scout Prompt

You are Desktop Codex operating under VS Code Codex technical authority for the APEX Power Ops non-PM parallel lane.

## Assignment

Run a read-only scout for NETA external source archive policy alignment.

The purpose is to draft the minimal policy language needed to acknowledge the external governed source archive for large/licensed/source PDF resources without embedding Jason's personal absolute Box path in learner-facing docs.

## Authority Band

Band A - Research / Scout only.

## Required Reads

- `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-resources-cleanup-archive-technical-authority-approval.md`
- `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-resources-docs-and-manifest-alignment-executor-closeout.md`
- `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-box-pdf-resources-archive-location-scout-closeout.md`
- `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md`
- `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\QUICK-LOOKUP.md`
- `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\RESOURCE-MANIFEST-RAW.json`
- `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\RESOURCE-MANIFEST.json`

Optional read, if needed for provenance wording only:

- `C:\Users\jjswe\Box\NETA Study\PDF Resources\README.md`

Do not open or read source PDFs, workbook contents, spreadsheet contents, or macro-bearing files.

## Allowed Write

Write exactly one closeout handoff:

- `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-external-source-archive-policy-alignment-scout-closeout.md`

## Forbidden Writes

- Do not edit source-domain files.
- Do not edit active platform repo docs other than the one closeout handoff.
- Do not restore files.
- Do not delete files.
- Do not stage, commit, push, or fast-forward any host.

## Forbidden Surfaces

- Source PDF contents.
- Workbook or spreadsheet contents.
- Workbook macros.
- Supabase, Render, Vercel, Olares, hosted services, credentials, secrets, schemas, auth, ingress, runtime, MCP services.
- PM business state.
- TCC activation.

## Required Analysis

Answer these questions:

1. What minimal repo-facing wording should identify an external governed source archive without exposing the personal absolute Box path?
2. What internal-only wording may reference the exact Box path for operator reconciliation and provenance?
3. Do `Resources/README.md` and `Resources/QUICK-LOOKUP.md` need follow-up edits, or are they acceptable as-is after the approved Resources alignment?
4. Should either manifest include external archive metadata now, or should manifests stay local-filesystem-only until a dedicated archive-index packet exists?
5. What is the smallest safe follow-up packet if edits are needed?

## Validation Required

Run only read/check commands needed to support the closeout. At minimum:

```powershell
git diff --check -- "C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-external-source-archive-policy-alignment-scout-closeout.md"
```

If using `git diff --check` against a newly untracked closeout is not meaningful in your environment, state that plainly and validate with a direct file read plus no forbidden status changes.

## Stop Conditions

Stop and classify `ABORTED_SCOPE_WIDENING` if the work requires source-domain edits, archive mutation, source PDF content reads, workbook content reads, macros, hosted access, credentials, staging, committing, or pushing.

Stop and classify `BLOCKED_CAPABILITY_GAP` if you cannot inspect the required markdown/json surfaces or cannot produce the closeout without violating the guardrails.

## Expected Output Shape

The closeout must include:

- status,
- files read,
- commands run,
- answers to the five required analysis questions,
- recommended exact policy wording split into repo-facing and internal-only language,
- whether source-domain edits are recommended,
- exact proposed next packet if edits are recommended,
- explicit confirmation that no source PDFs/workbooks/macros/hosted services/staging/commit/push were used.
