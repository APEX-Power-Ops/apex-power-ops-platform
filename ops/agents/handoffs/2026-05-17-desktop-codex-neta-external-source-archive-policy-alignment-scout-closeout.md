# Desktop Codex NETA External Source Archive Policy Alignment Scout Closeout

Date: 2026-05-17
Lane: NETA Study Material
Executor: Desktop Codex
Status: READY_FOR_VSCODE_REVIEW

## Purpose

Run the approved read-only scout for NETA external source archive policy alignment.

The goal was to draft minimal policy language acknowledging an external governed source archive for large/licensed/source PDF resources without embedding Jason's personal absolute Box path in learner-facing docs.

## Scope Performed

- Read the VS Code technical authority approval.
- Read the approved Resources docs/manifest alignment closeout.
- Read the Box archive location scout closeout.
- Read current `Resources/README.md` and `Resources/QUICK-LOOKUP.md`.
- Parsed current manifest metadata from `RESOURCE-MANIFEST-RAW.json` and `RESOURCE-MANIFEST.json`.
- Read the Box archive `README.md` only for provenance wording.
- Produced this one closeout handoff.

## Scope Not Performed

- Did not edit source-domain files.
- Did not edit platform repo docs other than this one closeout.
- Did not restore files.
- Did not delete files.
- Did not open or read source PDF contents.
- Did not open or read workbook/spreadsheet contents.
- Did not run macros.
- Did not access Supabase, Render, Vercel, Olares, hosted services, credentials, schemas, auth, ingress, runtime, or MCP services.
- Did not stage, commit, push, or fast-forward any host.
- Did not affect PM business state or activate TCC.

## Executive Finding

The approved `Resources` docs are acceptable as the current repo-local Resources authority state, but the newly approved external archive decision should be captured in one small follow-up source-domain doc edit.

Recommended edit target:

```text
C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md
```

Recommended no-edit targets for now:

```text
C:\APEX Platform\source-domains\neta-ett-study-material\Resources\QUICK-LOOKUP.md
C:\APEX Platform\source-domains\neta-ett-study-material\Resources\RESOURCE-MANIFEST-RAW.json
C:\APEX Platform\source-domains\neta-ett-study-material\Resources\RESOURCE-MANIFEST.json
```

Reason:

- `README.md` is the right policy surface for source archive rules.
- `QUICK-LOOKUP.md` is a fast learner/operator lookup and already avoids promising direct access to retired source folders.
- The manifests should remain local-filesystem-only until a dedicated archive-index packet exists.

## Required Analysis Answers

### 1. Minimal Repo-Facing Wording

Recommended repo-facing language:

```markdown
### External Governed Source Archive

Large, licensed, original-source, and reference PDF resources may be retained in an approved external governed source archive instead of Git. Repo-local `Resources/` should keep learner-facing content, curated extractions, reference metadata, manifests, and authority mappings lightweight and reviewable.

Do not restore source PDFs, standards, textbooks, screenshots, raw text, or workbook tools into Git by default. Reintroduce any source file only through an approved restore, extraction, audit, or provenance packet.

Learner-facing docs must not include personal absolute archive paths. Use internal operator handoffs for exact archive-location reconciliation.
```

This identifies the policy without exposing the personal Box path.

### 2. Internal-Only Wording

Recommended internal-only wording:

```markdown
Internal operator note: the approved external governed source archive for this cleanup tranche is `C:\Users\jjswe\Box\NETA Study\PDF Resources`. Use this path only in operator handoffs, reconciliation notes, and provenance/audit packets. Do not embed it in learner-facing repo docs, UI, generated study content, or public-facing documentation.
```

Internal handoffs may reference the exact path because VS Code approved it for governed archive reconciliation.

### 3. README and QUICK-LOOKUP Follow-Up Need

`Resources/README.md` should receive a small follow-up edit after VS Code approval.

Recommended placement:

- Add the repo-facing language under `## Active Authority Model`, after the existing bullets and before the licensed-material warning.

Current `README.md` already states:

- `References/` is active authority for NETA table workbooks/mappings.
- `Extractions/` is active authority for curated extraction outputs.
- `Source-PDFs/` is governed source inventory only.
- historical folders are not active just because older docs/manifests mention them.
- licensed standards/textbooks/screenshots/raw text/workbook tools need Jason/VS Code approval.

The only gap is that it does not yet explain the now-approved external governed source archive model.

`Resources/QUICK-LOOKUP.md` is acceptable as-is for this decision. It already treats textbooks as restricted/reference, PEARL/practice as supplemental-policy-only, and old templates as retired. A QUICK-LOOKUP edit is optional but not necessary.

### 4. Manifest Metadata Recommendation

Do not add external archive metadata to either manifest now.

Keep these files local-filesystem-only:

```text
Resources/RESOURCE-MANIFEST-RAW.json
Resources/RESOURCE-MANIFEST.json
```

Reasons:

- The current manifests were regenerated and approved as repo-local inventory.
- Adding external archive fields now would mix local filesystem inventory with off-repo archive authority.
- The Box archive has not yet been indexed through a dedicated archive-index packet.
- Absolute personal paths must not leak into learner-facing or machine-consumed repo metadata.

Future archive indexing should use a separate artifact, not the repo-local resource manifests by default.

Recommended future artifact name if needed:

```text
Resources/Catalog/EXTERNAL-SOURCE-ARCHIVE-INDEX.md
```

or, for internal-only provenance:

```text
ops/agents/handoffs/<date>-desktop-codex-neta-external-source-archive-index-scout-closeout.md
```

### 5. Smallest Safe Follow-Up Packet

Recommended next packet:

```text
Desktop Codex NETA External Source Archive README Policy Patch Executor
```

Purpose:

- Edit only `Resources/README.md`.
- Add the approved repo-facing external archive policy language.
- Do not include Jason's personal absolute Box path.
- Do not edit `QUICK-LOOKUP.md` or manifests unless VS Code explicitly expands scope.

Allowed writes:

```text
C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\<date>-desktop-codex-neta-external-source-archive-readme-policy-patch-executor-closeout.md
```

Forbidden:

- source PDF/workbook contents,
- archive mutation,
- restore/delete work,
- manifest regeneration,
- macros,
- Supabase/hosted services,
- staging/commit/push.

## Recommended Exact Patch Text

Recommended addition to `Resources/README.md`:

```markdown
### External Governed Source Archive

Large, licensed, original-source, and reference PDF resources may be retained in an approved external governed source archive instead of Git. Repo-local `Resources/` should keep learner-facing content, curated extractions, reference metadata, manifests, and authority mappings lightweight and reviewable.

Do not restore source PDFs, standards, textbooks, screenshots, raw text, or workbook tools into Git by default. Reintroduce any source file only through an approved restore, extraction, audit, or provenance packet.

Learner-facing docs must not include personal absolute archive paths. Use internal operator handoffs for exact archive-location reconciliation.
```

Recommended insertion point:

- After the `Active Authority Model` bullets in `Resources/README.md`.
- Before the sentence beginning `Licensed standards, textbooks, screenshots...`.

## Files Read

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-external-source-archive-policy-alignment-scout-prompt.md
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-resources-cleanup-archive-technical-authority-approval.md
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-resources-docs-and-manifest-alignment-executor-closeout.md
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-box-pdf-resources-archive-location-scout-closeout.md
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-parallel-lane-orchestration-queue.md
C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md
C:\APEX Platform\source-domains\neta-ett-study-material\Resources\QUICK-LOOKUP.md
C:\APEX Platform\source-domains\neta-ett-study-material\Resources\RESOURCE-MANIFEST-RAW.json
C:\APEX Platform\source-domains\neta-ett-study-material\Resources\RESOURCE-MANIFEST.json
C:\Users\jjswe\Box\NETA Study\PDF Resources\README.md
```

No source PDF, workbook, spreadsheet, or macro-bearing contents were read.

## Commands Run

```powershell
rg -n "NETA|source-domain|Box|Resources" "C:\Users\jjswe\.codex\memories\MEMORY.md"
git status --short
git status --short -- "Resources"
rg -n "Box|external|archive|Source-PDFs|References|Extractions|Templates|Tools|Jason|personal" "Resources/README.md" "Resources/QUICK-LOOKUP.md"
rg -n "technical approval|next scout prompt|orchestration queue|External Source Archive|Box archive|PDF Resources" .
Get-Content -Path "ops\agents\handoffs\2026-05-17-desktop-codex-neta-external-source-archive-policy-alignment-scout-prompt.md"
Get-Content -Path "ops\agents\handoffs\2026-05-17-desktop-codex-neta-resources-cleanup-archive-technical-authority-approval.md"
Get-Content -Path "ops\agents\handoffs\2026-05-17-desktop-codex-neta-resources-docs-and-manifest-alignment-executor-closeout.md" -TotalCount 260
Get-Content -Path "ops\agents\handoffs\2026-05-17-desktop-codex-neta-box-pdf-resources-archive-location-scout-closeout.md" -TotalCount 260
Get-Content -Path "ops\agents\handoffs\2026-05-17-desktop-codex-parallel-lane-orchestration-queue.md" -TotalCount 90
Get-Content -Path "Resources\README.md"
Get-Content -Path "Resources\QUICK-LOOKUP.md"
Get-Content -LiteralPath "C:\Users\jjswe\Box\NETA Study\PDF Resources\README.md" -TotalCount 220
```

Inline Python was used to parse both resource manifests, report top-level keys, summary metadata, status counts, file count, and a sample file record without reading source PDF/workbook contents.

## Validation

Required validation target:

```powershell
git diff --check -- "ops/agents/handoffs/2026-05-17-desktop-codex-neta-external-source-archive-policy-alignment-scout-closeout.md"
```

Expected result:

```text
PASS
```

## Final Recommendation

Approve one tiny source-domain README policy patch. Do not edit manifests. Do not edit QUICK-LOOKUP unless VS Code wants the fast lookup to carry an additional one-line operator reminder.

The clean governance model is:

- repo-local docs and manifests describe the active local authority state,
- external governed source archive exists for large/licensed/source/reference materials,
- exact personal path stays in internal handoffs/operator notes only,
- future archive indexing is a separate packet,
- source PDFs stay out of Git by default.
