# Desktop Codex NETA External Source Archive README Policy Patch Executor Prompt

You are Desktop Codex operating under VS Code Codex technical authority for the APEX Power Ops non-PM parallel lane.

## Assignment

Execute the approved README-only policy patch for the NETA external governed source archive decision.

The purpose is to add minimal repo-facing policy language to `Resources/README.md` that acknowledges an external governed source archive for large/licensed/source/reference materials without exposing Jason's personal absolute Box path.

## Authority Band

Band B - bounded documentation patch.

## Required Reads

- `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-external-source-archive-policy-alignment-technical-authority-approval.md`
- `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-external-source-archive-policy-alignment-scout-closeout.md`
- `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md`

Do not open or read source PDFs, workbook contents, spreadsheet contents, or macro-bearing files.

## Allowed Writes

Write exactly these files:

- `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md`
- `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-external-source-archive-readme-policy-patch-executor-closeout.md`

## Forbidden Writes

- Do not edit `Resources/QUICK-LOOKUP.md`.
- Do not edit `Resources/RESOURCE-MANIFEST-RAW.json`.
- Do not edit `Resources/RESOURCE-MANIFEST.json`.
- Do not restore files.
- Do not delete files.
- Do not regenerate manifests.
- Do not edit platform repo docs other than the one closeout handoff.
- Do not stage, commit, push, or fast-forward any host.

## Forbidden Surfaces

- Source PDF contents.
- Workbook or spreadsheet contents.
- Workbook macros.
- Supabase, Render, Vercel, Olares, hosted services, credentials, secrets, schemas, auth, ingress, runtime, or MCP services.
- PM business state.
- TCC activation.

## Patch Instruction

In `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md`, add this exact section under `## Active Authority Model`, after the existing authority bullets and before the sentence beginning `Licensed standards, textbooks, screenshots...`.

```markdown
### External Governed Source Archive

Large, licensed, original-source, and reference PDF resources may be retained in an approved external governed source archive instead of Git. Repo-local `Resources/` should keep learner-facing content, curated extractions, reference metadata, manifests, and authority mappings lightweight and reviewable.

Do not restore source PDFs, standards, textbooks, screenshots, raw text, or workbook tools into Git by default. Reintroduce any source file only through an approved restore, extraction, audit, or provenance packet.

Learner-facing docs must not include personal absolute archive paths. Use internal operator handoffs for exact archive-location reconciliation.
```

Do not include the exact Box path in `Resources/README.md`.

## Validation Required

Run only read/check commands needed to support the closeout. At minimum:

```powershell
rg -n "External Governed Source Archive|personal absolute archive paths|C:\\Users\\jjswe" "C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md"
git diff --check -- "C:\APEX Platform\source-domains\neta-ett-study-material\Resources\README.md" "C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-neta-external-source-archive-readme-policy-patch-executor-closeout.md"
```

Expected validation:

- `External Governed Source Archive` is present.
- `personal absolute archive paths` is present.
- the exact personal Box path is not present in `Resources/README.md`.
- `git diff --check` passes, or if the closeout is untracked and not included by the diff command, state that plainly and validate with a direct file read plus no forbidden status changes.

## Stop Conditions

Stop and classify `ABORTED_SCOPE_WIDENING` if the work requires source PDF content reads, workbook content reads, macros, archive mutation, restore/delete work, manifest regeneration, hosted access, credentials, staging, committing, or pushing.

Stop and classify `BLOCKED_CAPABILITY_GAP` if you cannot inspect or patch the required README without violating the guardrails.

## Expected Closeout Shape

The closeout must include:

- status;
- files read;
- files written;
- exact patch summary;
- commands run;
- validation results;
- explicit confirmation that no source PDFs/workbooks/macros/hosted services/staging/commit/push were used;
- explicit confirmation that `Resources/README.md` does not include the exact personal Box path;
- recommendation for whether the NETA lane should next return to the parked topic-spine comparative audit or run an archive-index scout.
