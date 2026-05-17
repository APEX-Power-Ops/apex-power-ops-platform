# Desktop Codex NETA Study Material Scout/Build Closeout

Date: 2026-05-17
Status: READY_FOR_JASON_DECISION
Lane: NETA Study Material
Authority band: Band A/B only

## Summary

The NETA Study Material lane is ready for one bounded follow-on packet, but not yet for broad content production or source import.

The source-domain inventory shows a mature existing NETA ETT study-material workspace with active governance, build specifications, process guides, level-specific student-facing content, extracted exam resources, ETT study aids, NETA standards extractions, handbooks, flashcards, mock exams, and many prior AI task prompts. The right next move is not to create new study content immediately. The next move should first create a source-to-artifact map and choose one narrow pilot artifact family.

Recommended next admission: one NETA source-map and artifact-backlog packet, still one-closeout-only, before any generated study guide, question bank, or production artifact work.

## Source Inventory

Primary source-domain root:

`C:\APEX Platform\source-domains\neta-ett-study-material`

Relevant active surfaces observed:

1. `README.md`: current repository orientation and governance startup chain.
2. `GOVERNANCE-FRAMEWORK.md`: multi-AI coordination, authority hierarchy, quality checkpoints, resource-governance rules, and acceptance-matrix pattern.
3. `MASTER-STANDARDS.md`: single-source-of-truth stack, build spec routing, resource governance surfaces, and quality audit references.
4. `Build-Specs/`: canonical specs for practice tests, study guides, infrastructure roadmap, staging workflow, test scaffolding, staging format, reference sheets, and flashcards.
5. `Process-Guides/`: supporting workflow references, extraction guide, quality checklist, and content workflow; not current startup authority.
6. `Development/Control-Plane/`: active control-plane, task prompts, resumes, ETT content queue, workspace governance, and many prior AI task packets.
7. `Resources/`: source PDFs, extractions, catalogs, references, manifests, and quick lookup surfaces.
8. `Resources/Extractions/Exam-Resources/`: NETA exam content outline, reference list, quiz questions, study guide, formulae, and broader exam resources.
9. `Resources/Extractions/ETT-Study-Aids/`: fact sheets, practice exams, study guides, math help, and topic-specific aids.
10. `Resources/Extractions/NETA-Standards/`: ATS, MTS, ETT, ECS standards extractions and archive.
11. `Resources/Extractions/NETA-Handbooks/`: handbook-series extractions and relay handbook material.
12. `NETA-2/`, `NETA-3/`, `NETA-4/`: level-specific student-facing folders with study plans, reference sheets, study guides, practice tests, flashcards, mock exams, and progress trackers.

Important source-domain boundary note:

The source repo contains `.secrets/`, `.venv/`, `.pytest_cache/`, `.git/`, binary source materials, and generated/delivery assets. These were not opened, copied, moved, imported, or modified. Inventory intentionally stayed on human-readable governance, markdown, directory, and existing HTML surface names.

## Existing Repo NETA References

APEX repo references relevant to this lane:

1. `ops/knowledge-resource-operations/EXTRACTION-PRIORITY-QUEUE.md`
2. `ops/knowledge-resource-operations/EXTRACTION-LOAD-GAP-REPORT.md`
3. `ops/knowledge-resource-operations/RESOURCE-AUDIT-REPORT.md`
4. `ops/knowledge-resource-operations/REMAINING-EXTRACTION-QUEUE.md`
5. `ops/knowledge-resource-operations/RESOURCE-GOVERNANCE-AUDIT.md`
6. `ops/agents/handoffs/2026-05-17-desktop-codex-neta-study-material-scout-build-prompt.md`
7. `ops/agents/handoffs/2026-05-17-desktop-codex-relay-review-burden-closeout.md`

The APEX-side resource-operation docs already contain useful NETA extraction and gap history. They should be treated as routing/context surfaces, not as permission to write source-domain content or Supabase state.

## Artifact Map

Recommended near-term artifact families:

1. Source map:
   - maps existing source-domain roots to usable study-material categories,
   - distinguishes active control-plane sources from historical/archive sources,
   - flags sensitive or forbidden folders such as `.secrets/`.

2. Study guide backlog:
   - maps Level II, III, and IV guide families to existing study guides, reference sheets, and ETT study aids,
   - identifies where existing guides appear complete enough for audit versus where a new guide should be scoped.

3. Question-bank scaffold:
   - starts from `Build-Specs/QUESTION-SCHEMA-SPEC.md`, `PRACTICE-TEST-SPEC.md`, and existing quiz/practice-test materials,
   - does not copy question text or generate new questions until a separate content-authoring packet is approved.

4. QA checklist:
   - uses `Process-Guides/QUALITY-VALIDATION-CHECKLIST.md`, build specs, and `MASTER-STANDARDS.md`,
   - separates technical correctness, source traceability, exam relevance, clarity, and artifact readiness.

5. Extraction-gap register:
   - starts with APEX `EXTRACTION-PRIORITY-QUEUE.md` and source-domain resource governance docs,
   - classifies gaps as current, stale, superseded, acquisition-needed, or content-authoring-needed.

## Gaps And Unclear Ownership

1. The NETA source-domain repo has its own governance/control-plane stack. APEX Desktop Codex should not assume it can rewrite that stack from the APEX repo.
2. The extraction queue is dated March 2026 and explicitly says some queue body content is historical until a full refresh is performed.
3. Direct exam materials appear extracted, but question-bank loading and study-question table ownership are not fully proven from this scout.
4. Some extraction gaps are acquisition or partial-extraction gaps, including the noted IEEE C62.22-2009 acquisition gap, partial PEARL/IEEE Color Books/NFPA 70E/formula-sheet work, and source gaps around batteries, VFDs, and SCADA/DCS references.
5. The source-domain repo references Supabase-backed study content and shared seams, but this NETA lane has no authority to query Supabase, write Supabase, change schema, or reconcile database state.
6. TCC-related material appears inside the NETA source-domain control plane, but TCC remains parked under the APEX parallel-lane plan and must not be pulled into this NETA lane.
7. Binary PDFs, DOCX, PPTX, workbook-like assets, and generated HTML/content outputs need their own read/render/extraction packet before any quality claims about content details.

## Recommended Next Bounded NETA Packet

Packet name:

`Desktop Codex NETA Source Map And Artifact Backlog`

Authority:

Band A/B, one closeout handoff only.

Allowed reads:

1. NETA prompt, Relay closeout, APEX parallel-lane queue, and APEX governance plan.
2. `C:\APEX Platform\source-domains\neta-ett-study-material\README.md`
3. `C:\APEX Platform\source-domains\neta-ett-study-material\GOVERNANCE-FRAMEWORK.md`
4. `C:\APEX Platform\source-domains\neta-ett-study-material\MASTER-STANDARDS.md`
5. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\*.md`
6. `C:\APEX Platform\source-domains\neta-ett-study-material\Process-Guides\*.md`
7. directory inventory only under `NETA-2/`, `NETA-3/`, `NETA-4/`, and `Resources/Extractions/`
8. APEX `ops/knowledge-resource-operations/*.md`

Allowed write:

One closeout handoff in `ops/agents/handoffs/`.

Forbidden:

1. no source-domain writes,
2. no content generation,
3. no binary extraction,
4. no Supabase access,
5. no schema or runtime work,
6. no TCC execution,
7. no product code,
8. no package/environment files,
9. no staging, commit, push, or Olares fast-forward.

Expected output:

1. source-to-artifact map,
2. level-by-level artifact backlog,
3. candidate first pilot family,
4. QA checklist proposal,
5. gap classification,
6. recommendation on whether the next packet should be content audit, question-bank schema audit, or pilot artifact authoring.

## Status Recommendation

Return to Jason for decision:

1. Approve the next NETA source-map and artifact-backlog packet.
2. Keep TCC parked until the NETA source-map closeout proves this non-PM substance-lane workflow remains concise.
3. Do not start content generation yet.

## Stop-Condition Confirmation

No shared product code was edited.
No package files were edited.
No product UI was touched.
No source-domain files were written.
No binary workbook, PDF, DOCX, PPTX, or generated output was created.
No workbook macros were run.
No Supabase, Render, Vercel, Olares, MCP, hosted service, credential, schema, or runtime surface was accessed or changed.
No TCC scout work was executed.
No staging, commit, push, status publication, or Olares fast-forward was performed.

## Exact Files Read

APEX repo:

1. `ops/agents/handoffs/2026-05-17-desktop-codex-neta-study-material-scout-build-prompt.md`
2. `docs/operations/APEX-PARALLEL-LANE-ORCHESTRATION-GOVERNANCE-PLAN-2026-05-17.md`
3. `ops/agents/handoffs/2026-05-17-desktop-codex-parallel-lane-orchestration-queue.md`
4. `ops/agents/handoffs/2026-05-17-desktop-codex-relay-review-burden-closeout.md`
5. `ops/knowledge-resource-operations/EXTRACTION-PRIORITY-QUEUE.md`

Source-domain files:

1. `C:\APEX Platform\source-domains\neta-ett-study-material\README.md`
2. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\README.md`
3. `C:\APEX Platform\source-domains\neta-ett-study-material\Process-Guides\README.md`
4. `C:\APEX Platform\source-domains\neta-ett-study-material\GOVERNANCE-FRAMEWORK.md`
5. `C:\APEX Platform\source-domains\neta-ett-study-material\MASTER-STANDARDS.md`

Read-only directory inventories:

1. `C:\APEX Platform\source-domains`
2. `C:\APEX Platform\source-domains\neta-ett-study-material`
3. `C:\APEX Platform\source-domains\neta-ett-study-material\Resources`
4. `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\Extractions`
5. `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\Extractions\Exam-Resources`
6. `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\Extractions\ETT-Study-Aids`
7. `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\Extractions\NETA-Standards`
8. `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\Extractions\NETA-Handbooks`
9. `C:\APEX Platform\source-domains\neta-ett-study-material\NETA-2`
10. `C:\APEX Platform\source-domains\neta-ett-study-material\NETA-3`
11. `C:\APEX Platform\source-domains\neta-ett-study-material\NETA-4`
12. `C:\APEX Platform\source-domains\neta-ett-study-material\Development\Control-Plane`

## Exact File Written

1. `ops/agents/handoffs/2026-05-17-desktop-codex-neta-study-material-scout-build-closeout.md`

## Validation

Required validation:

```powershell
git diff --check -- ops/agents/handoffs/2026-05-17-desktop-codex-neta-study-material-scout-build-closeout.md
```

Result: PASS.

## Final Status

READY_FOR_JASON_DECISION
