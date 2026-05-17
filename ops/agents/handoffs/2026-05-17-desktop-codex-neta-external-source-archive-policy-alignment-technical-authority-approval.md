# Desktop Codex NETA External Source Archive Policy Alignment Technical Authority Approval

Date: 2026-05-17
Reviewer: VS Code Codex
Lane: NETA Study Material
Status: APPROVED WITH README-ONLY EXECUTOR

## Review Input

Primary closeout reviewed:

- `ops/agents/handoffs/2026-05-17-desktop-codex-neta-external-source-archive-policy-alignment-scout-closeout.md`

Related authority input:

- `ops/agents/handoffs/2026-05-17-desktop-codex-neta-resources-cleanup-archive-technical-authority-approval.md`
- `ops/agents/handoffs/2026-05-17-desktop-codex-neta-resources-docs-and-manifest-alignment-executor-closeout.md`
- `ops/agents/handoffs/2026-05-17-desktop-codex-neta-box-pdf-resources-archive-location-scout-closeout.md`

## Verdict

Approved.

The scout closeout satisfied the approved Band A boundary. The recommended model is correct:

- repo-facing resource docs may acknowledge an approved external governed source archive;
- learner-facing docs must not include Jason's personal absolute Box path;
- exact archive path references belong only in internal handoffs, reconciliation notes, and provenance/audit packets;
- `RESOURCE-MANIFEST-RAW.json` and `RESOURCE-MANIFEST.json` should remain repo-local filesystem inventories until a dedicated archive-index packet exists;
- `Resources/QUICK-LOOKUP.md` does not need a follow-up edit for this decision.

## Decisions

1. The external source archive policy alignment scout is approved.
2. The next permitted Desktop Codex move is a README-only source-domain policy patch.
3. The approved patch target is:
   - `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md`
4. The following files are not approved for edit in the next packet:
   - `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\QUICK-LOOKUP.md`
   - `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\RESOURCE-MANIFEST-RAW.json`
   - `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\RESOURCE-MANIFEST.json`
5. The exact Box path remains approved for internal operator use only and must not be embedded in learner-facing source-domain docs.
6. Future archive indexing must be a separate packet and must not be mixed into the current repo-local resource manifests by default.

## Required Amendments

No amendment is required to the scout finding.

The next executor prompt must keep the write set narrow and must prohibit restore work, delete work, source PDF reads, workbook reads, macros, hosted services, credentials, staging, committing, and pushing.

## Next Approved Packet

`Desktop Codex NETA External Source Archive README Policy Patch Executor`

Allowed writes:

- `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md`
- `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-external-source-archive-readme-policy-patch-executor-closeout.md`

Forbidden:

- source PDF contents;
- workbook or spreadsheet contents;
- workbook macros;
- source PDF restore;
- file deletion;
- manifest regeneration;
- `Resources/QUICK-LOOKUP.md`;
- `Resources/RESOURCE-MANIFEST-RAW.json`;
- `Resources/RESOURCE-MANIFEST.json`;
- Supabase, Render, Vercel, Olares, hosted services, credentials, auth, schemas, ingress, runtime, or MCP services;
- staging, committing, pushing, or host fast-forwarding.

## Required Closeout Evidence

The executor closeout must include:

- exact files read;
- exact files written;
- patch summary;
- confirmation that no personal absolute Box path was added to `Resources/README.md`;
- confirmation that no source PDF/workbook/macro/hosted-service/staging/commit/push activity occurred;
- validation output for direct README inspection and `git diff --check`.

## Technical Authority Note

This approval keeps NETA as a delegated non-PM lane under VS Code Codex technical authority. Desktop Codex may execute the README-only patch, but VS Code Codex retains final review and repo integration authority.
