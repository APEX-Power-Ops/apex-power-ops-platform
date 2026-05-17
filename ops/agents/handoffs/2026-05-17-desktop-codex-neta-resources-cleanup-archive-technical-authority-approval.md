# Desktop Codex NETA Resources Cleanup And Archive Technical Authority Approval

Date: 2026-05-17
Reviewer: VS Code Codex
Lane: NETA Study Material
Status: APPROVED WITH BOUNDED NEXT SCOUT

## Review Inputs

Primary handoffs reviewed:

- `ops/agents/handoffs/2026-05-17-desktop-codex-neta-resources-docs-and-manifest-alignment-executor-closeout.md`
- `ops/agents/handoffs/2026-05-17-desktop-codex-neta-box-pdf-resources-archive-location-scout-closeout.md`

Source-domain files reviewed:

- `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md`
- `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\QUICK-LOOKUP.md`
- `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\RESOURCE-MANIFEST-RAW.json`
- `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\RESOURCE-MANIFEST.json`

## Verdict

Approved.

The four source-domain Resources docs/manifest updates are approved as the current repo-local Resources authority state. They accurately move the active authority emphasis to `References/`, `Extractions/`, and governed source inventory while treating `Templates/` and `Tools/` as retired or rebuild-required surfaces.

The Box archive is approved as the external governed source archive for large, licensed, source, and reference PDF resources, subject to one policy condition: learner-facing repo docs must not embed Jason's personal absolute Box path. Internal handoffs and operator-only policy notes may reference the path when needed for governed archive reconciliation.

## Decisions

1. The four Desktop Codex source-domain modifications are approved.
2. `C:\Users\jjswe\Box\NETA Study\PDF Resources` is recognized as the external governed source archive for large/licensed/source PDF resources.
3. Deleted tracked source-reference paths under `Resources/Source-PDFs/NETA`, `Resources/Source-PDFs/NFPA-OSHA`, `Resources/Source-PDFs/PEARL`, and `Resources/Source-PDFs/Textbooks` should remain deleted from Git by default because exact filename matches were verified in the Box archive.
4. `Resources/Templates` and `Resources/Tools/Calculator-Spreadsheets` should remain retired or rebuild-required by default. They should not be restored into NETA learner resources without a separate tooling/template packet.
5. The next approved packet is `Desktop Codex NETA External Source Archive Policy Alignment Scout`.

## Evidence Verified

- Box archive exists.
- Box archive contains `903` files, `840` PDFs, and approximately `3970.23 MB`.
- Deleted tracked source-reference filename matches:
  - `Source-PDFs/NETA`: `10 / 10`
  - `Source-PDFs/NFPA-OSHA`: `32 / 32`
  - `Source-PDFs/PEARL`: `4 / 4`
  - `Source-PDFs/Textbooks`: `2 / 2`
- Current deleted tracked Resources buckets:
  - `_Unsorted`: `1`
  - `NETA`: `10`
  - `NFPA-OSHA`: `32`
  - `PEARL`: `4`
  - `Templates`: `13`
  - `Textbooks`: `2`
  - `Tools`: `32`
- `RESOURCE-MANIFEST-RAW.json` parses with `1261` records, `0` missing paths, `614` PDFs, and `2049.5 MB`.
- `RESOURCE-MANIFEST.json` parses with `1261` records, `0` missing paths, `614` PDFs, `2049.5 MB`, and status counts `176 extraction_only`, `648 not_applicable`, `437 unextracted`.
- `git diff --check` on the four source-domain files passed, with only expected CRLF warnings on markdown files.

No source PDF contents or workbook contents were read during this review.

## Approval Boundaries

This approval does not admit:

- restoring source PDFs into Git by default,
- restoring Templates or Tools by default,
- reading source PDF contents,
- reading workbook contents,
- running workbook macros,
- Supabase, Render, Vercel, Olares, or hosted-service access,
- staging, committing, pushing, or publishing source-domain changes,
- source-domain cleanup beyond the reviewed Resources scope,
- NETA learner content generation,
- PM lane impact,
- TCC lane activation.

## Next Approved Packet

`Desktop Codex NETA External Source Archive Policy Alignment Scout` is approved as the next Desktop Codex NETA packet.

The packet should draft minimal repo-doc policy language that acknowledges the Box archive as the external governed source archive without embedding Jason's personal absolute Box path in learner-facing docs. It should identify whether `Resources/README.md`, `Resources/QUICK-LOOKUP.md`, and manifest metadata need a follow-up adjustment and classify what language belongs in internal operator notes versus repo-facing learner/resource docs.

Allowed output is one closeout handoff only. Any source-domain edits require a later approval.
