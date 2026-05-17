# Desktop Codex NETA Source Map And Artifact Backlog Closeout

Date: 2026-05-17
Status: READY_FOR_JASON_DECISION
Lane: NETA Study Material
Authority band: Band A/B only

## Summary

The NETA Study Material lane is ready for a focused read-only pilot content audit. It is not ready for broad content authoring, source import, Supabase reconciliation, or generated artifact production.

The source-domain workspace already contains a large student-facing artifact set by level, mature build specifications, process guides, extraction inventories, and APEX-side extraction/gap reports. The practical bottleneck is not missing folders or lack of candidate material. The bottleneck is deciding which artifact family should become the first governed pilot and proving that its study guide, reference sheet, practice test, flashcard, source citation, KSA mapping, and quality checks line up without requiring Jason to manually inspect the whole corpus.

Recommended next admission: one read-only `NETA Level II Electrical Fundamentals Pilot Content Audit` packet. That packet should audit one low-risk foundational family before any authoring or schema work.

## Source-To-Artifact Map

| Source surface | Role | Current evidence | Candidate artifact outputs | Human approval needed |
| --- | --- | --- | --- | --- |
| `README.md`, `GOVERNANCE-FRAMEWORK.md`, `MASTER-STANDARDS.md` | Source-domain authority and operating model | Active startup chain, authority hierarchy, folder standards, naming rules, resource governance | Packet guardrails, stop conditions, artifact ownership boundaries | Jason/VS Code approval before changing source-domain governance |
| `Build-Specs/*.md` | Canonical artifact specifications | Complete specs for practice tests, study guides, reference sheets, flashcards, staging, infrastructure, scaffolding, templates | Audit rubric, backlog acceptance criteria, future authoring prompt templates | Jason approval before treating any generated artifact as final |
| `Process-Guides/*.md` | Supporting workflow and QA | Content creation workflow, citation guide, quality checklist, extraction guides, session protocol | QA checklist, citation rules, audit pass/fail fields | Jason approval for any content-quality disposition that affects priority |
| `Resources/Extractions/ETT-2022` | KSA source | Level II, III, IV KSA extraction files and index observed by inventory | KSA coverage checks for guides, tests, flashcards | Human review for ambiguous KSA mapping |
| `Resources/Extractions/Exam-Resources` | Exam orientation and direct prep | Exam outline, reference list, formulas, study guide, quiz questions, broader exam resources | Exam-alignment checks, source priority hints, question-bank source candidates | Human approval before using quiz content in generated questions |
| `Resources/Extractions/ETT-Study-Aids` | High-value study aids and fact sheets | 28 files observed by inventory; APEX reports say these were previously high-value ETT aids | Pilot source pool for foundational and equipment-topic audits | Human approval before copying/adapting content |
| `Resources/Extractions/NETA-Standards`, `ATS-2025`, `MTS-2023` | Governing standards sources | ATS, MTS, ETT, ECS and table/section extractions observed | Citation checks, acceptance criteria, procedure references | Human review for edition-sensitive values |
| `Resources/Extractions/Paul-Gill` | Technical depth source | Curated and raw Paul Gill chapter extractions observed | Technical explanations, field tips, calculation support | Human review for technical interpretation |
| `Resources/Extractions/IEEE`, `NFPA-70E`, `OSHA`, `NEMA`, `IEC`, `UL`, `ASTM` | External standards/reference support | Large extraction set observed by category count | Advanced citation checks, safety/code alignment, topic depth | Human review for edition conflicts or legal/source constraints |
| `NETA-2/` | Level II student package | Study plan, 14 reference sheets, 45 study guides, 47 practice-test files, flashcards, 2 mock exams, progress tracker | First pilot audit target | Human approval before authoring changes |
| `NETA-3/` | Level III student package | Study plan, 23 reference sheets, 35 study guides, 32 practice-test files, flashcards, 2 mock exams, 2 trackers | Second-phase audit target after Level II proof | Human approval before pulling in advanced/TCC-adjacent topics |
| `NETA-4/` | Level IV student package | Study plan, 23 reference sheets, 31 study guides, 31 practice-test files, flashcards, mock exam, tracker | Later advanced audit target | VS Code/Jason review for system-level and architecture-adjacent content |
| APEX `ops/knowledge-resource-operations/*.md` | APEX-side extraction and resource-state history | March 2026 gap reports, load reports, resource audit, coverage and path status | Gap classification, stale-vs-current warnings | VS Code/Jason approval before treating historical load state as current |

## Level-By-Level Artifact Backlog

### Level II Backlog

Observed level package:

1. `01-Study-Plan`: 1 file.
2. `02-Reference-Sheets`: 14 files.
3. `03-Study-Guides`: 45 files.
4. `04-Practice-Tests`: 47 files, including dashboards/drill engines and one PDF.
5. `05-Flashcards`: 1 file.
6. `06-Mock-Exams`: 2 files.
7. `07-Progress-Tracker`: 1 file.

Recommended backlog order:

1. Audit `Electrical Fundamentals / Basic Electrical Theory / Ohm's Law / Power Calculations / Three-Phase Fundamentals` as the first pilot family.
2. Verify that each study guide has a matching or intentionally absent reference sheet, practice test, and cross-reference.
3. Verify source citations against NETA/Paul Gill/IEEE/NFPA where applicable.
4. Verify practice-test question objects against `QUESTION-SCHEMA-SPEC.md`.
5. Verify flashcard coverage only after the guide/test pair is proven.

Why Level II first:

1. Lowest integration risk.
2. Strong existing artifact count.
3. Foundational content is useful before advanced relay/TCC-adjacent material.
4. Jason gets a repeatable audit pattern without needing to review advanced technical edge cases first.

### Level III Backlog

Observed level package:

1. `01-Study-Plan`: 1 file.
2. `02-Reference-Sheets`: 23 files.
3. `03-Study-Guides`: 35 files.
4. `04-Practice-Tests`: 32 files.
5. `05-Flashcards`: 1 file.
6. `06-Mock-Exams`: 2 files.
7. `07-Progress-Tracker`: 2 files.

Recommended backlog order:

1. Wait until the Level II audit proves the pattern.
2. Audit `Transformer Testing`, `Circuit Breaker Testing`, `Protective Relay Testing`, `Grounding`, and `Power Quality` families.
3. Keep `Protective Relay Testing`, `Time-Current Curve`, and coordination material out of TCC execution unless a separate TCC packet is approved.
4. Confirm Level III practice tests include enhanced feedback, KSA tags, and source references before schema or database planning.

### Level IV Backlog

Observed level package:

1. `01-Study-Plan`: 1 file.
2. `02-Reference-Sheets`: 23 files.
3. `03-Study-Guides`: 31 files.
4. `04-Practice-Tests`: 31 files.
5. `05-Flashcards`: 1 file.
6. `06-Mock-Exams`: 1 file.
7. `07-Progress-Tracker`: 1 file.

Recommended backlog order:

1. Defer until Level II and Level III audit patterns are proven.
2. Audit CT/ET/SF guide families against Level IV KSA tags and advanced source citations.
3. Treat system coordination, SCADA/IEC 61850, DER, NERC, relay coordination, and power-system studies as higher-review topics.
4. Require VS Code/Jason review before authoring or integrating any advanced runtime, schema, hosted, TCC, or platform-facing work.

## Candidate First Pilot Family

Recommended first pilot:

`NETA Level II Electrical Fundamentals Pilot Content Audit`

Suggested pilot scope:

1. `NETA-2/03-Study-Guides/01-Ohms-Law-Complete-Guide.html`
2. `NETA-2/03-Study-Guides/02-Power-Calculations-Guide.html`
3. `NETA-2/03-Study-Guides/03-Series-Parallel-Circuits-Guide.html`
4. `NETA-2/03-Study-Guides/04-Three-Phase-Fundamentals-Guide.html`
5. matching Level II reference sheets where present,
6. matching Level II practice tests `01` through `04`,
7. related `ETT-Study-Aids` and exam-resource extractions only as read-only citation/context sources.

Pilot output should be one APEX handoff only, not edits to source-domain artifacts.

Pilot audit should answer:

1. Which files form the family?
2. Are study guide, reference sheet, practice test, and flashcard coverage aligned?
3. Are citations present and suitable?
4. Are KSA references present or missing?
5. Are practice-test question objects compatible with the existing schema?
6. What specific authoring work should be admitted next, if any?

## QA Checklist Proposal

Use a compact pass/warn/block model so Jason does not need to read every artifact.

Required audit fields:

1. artifact family name,
2. level,
3. files included,
4. artifact type for each file,
5. source/citation status,
6. KSA status,
7. schema status for tests/questions,
8. browser/render status if a future packet admits browser checks,
9. safety/code/edition sensitivity,
10. gaps found,
11. recommended disposition.

Recommended dispositions:

1. `PASS_AUDIT_READY`: coherent enough for Jason review.
2. `WARN_AUTHORING_NEEDED`: useful but needs bounded authoring cleanup.
3. `WARN_SOURCE_TRACEABILITY`: content may be useful, but source/citation/KSA mapping is weak.
4. `BLOCK_EDITION_OR_SAFETY`: do not use until a human confirms source edition or safety-critical content.
5. `BLOCK_SCHEMA_OR_RUNTIME`: do not integrate into question-bank or platform workflow without VS Code review.

Minimum checklist:

1. File path and naming match `MASTER-STANDARDS.md`.
2. Study guide depth and required sections match `STUDY-GUIDE-SPEC.md`.
3. Reference sheets are scannable, citation-backed, and field usable per `REFERENCE-SHEET-SPEC.md`.
4. Practice tests include complete question data per `PRACTICE-TEST-SPEC.md`.
5. Question objects include required `id`, `question`, `options`, `correct`, `explanation`, `whyMatters`, `commonMistake`, and `guideRef` fields per `QUESTION-SCHEMA-SPEC.md`.
6. Optional `sourceRef`, `levelTag`, `ksa`, and `difficulty` fields are either valid or explicitly absent.
7. Flashcards are treated as derived from a canonical deck contract, not as sole source-of-truth, per `FLASHCARD-SPEC.md`.
8. Citations use accepted source categories and source-chip expectations from `SOURCE-CITATION-GUIDE.md`.
9. Quality review checks content basics, references, KSA coverage, browser readiness, and placeholders per `QUALITY-VALIDATION-CHECKLIST.md`.
10. Any safety-critical, standard-edition-sensitive, or calculation-sensitive content is marked for human review.

## Gap Classification

### Current Gaps

1. The first pilot family has not been audited at file-content level in this packet.
2. Source-domain generated HTML files were inventoried but not opened or browser-tested.
3. Practice-test JavaScript/question object details were not parsed.
4. Flashcard canonical source versus HTML app source-of-truth remains unproven.

### Stale Or Historical Gaps

1. APEX extraction/load reports are March 2026 snapshots and may not reflect the current source-domain state.
2. APEX `EXTRACTION-LOAD-GAP-REPORT.md` says many files were on disk only as of 2026-03-15.
3. APEX `EXTRACTION-PRIORITY-QUEUE.md` includes historical queue body content retained until a full refresh.

### Superseded Or Possibly Closed Gaps

1. The extraction queue says direct exam-prep materials were extracted by late February/March 2026.
2. The queue says IEEE 1106-2015 was later extracted as `EXT-IEEE-303`.
3. Many high-priority IEEE and field-reference gaps appear marked complete in the queue, but were not revalidated against current database state because Supabase access is not admitted.

### Acquisition-Needed Gaps

1. IEEE C62.22-2009 remains identified as an open exam-edition acquisition gap.
2. Any edition-sensitive standards conflict must be held for human review.

### Content-Authoring-Needed Gaps

1. Missing KSA mapping in existing guides/tests, if found in pilot audit.
2. Missing source citations or weak traceability.
3. Practice tests that do not meet required question object fields.
4. Study guides missing worked examples, common mistakes, field tips, or level badges.
5. Reference sheets with values/formulas lacking source authority.

## What Should Remain Automated Vs Human-Approved

Automated or delegated under future Band A/B packets:

1. directory inventory,
2. markdown/spec reading,
3. source-to-artifact mapping,
4. file-family grouping,
5. draft audit tables,
6. schema-shape inspection of local HTML/JS where admitted,
7. citation-presence checks,
8. line/count/path/naming checks,
9. one-closeout evidence packaging.

Human-approved:

1. final technical correctness,
2. safety-critical content,
3. source-edition conflicts,
4. KSA interpretation when ambiguous,
5. adapting official exam questions into generated questions,
6. any source-domain file edits,
7. any generated study guide, practice test, flashcard deck, PDF, or workbook artifact,
8. any Supabase, schema, hosted, Olares, TCC, or shared product integration.

## Capability Gaps

1. No admitted authority to query Supabase, so database load state and `study_questions` ownership remain unverified.
2. No admitted authority to write source-domain files, so this packet cannot repair discovered content gaps.
3. No browser/render pass was admitted, so HTML functionality and visual quality remain unverified.
4. No binary extraction/render pass was admitted, so PDFs/DOCX/PPTX assets remain out of scope.
5. No TCC execution is admitted, even though relay/TCC-adjacent content exists inside the NETA source-domain.
6. No canonical manifest was produced in source-domain because the only allowed write is this APEX handoff.

## Recommended Next Bounded Packet

Packet name:

`Desktop Codex NETA Level II Electrical Fundamentals Pilot Content Audit`

Recommended status after this closeout:

`READY_FOR_JASON_DECISION`

Allowed reads:

1. this closeout,
2. prior NETA scout/build closeout,
3. APEX parallel-lane governance plan and queue,
4. source-domain `README.md`, `GOVERNANCE-FRAMEWORK.md`, `MASTER-STANDARDS.md`,
5. relevant `Build-Specs/*.md` and `Process-Guides/*.md`,
6. the Level II pilot family files listed above,
7. directly related `Resources/Extractions/ETT-Study-Aids`, `Exam-Resources`, and standards extraction files only when needed for citation checks.

Allowed write:

One APEX closeout handoff in `ops/agents/handoffs/`.

Forbidden:

1. no source-domain writes,
2. no content generation,
3. no broad Level III/IV audit,
4. no TCC execution,
5. no Supabase access,
6. no product code,
7. no package or environment files,
8. no binary generation,
9. no staging, commit, push, status publication, or Olares fast-forward.

Expected output:

1. pilot family file map,
2. pass/warn/block audit table,
3. exact source/citation/KSA/schema gaps,
4. recommended authoring packet or schema-audit packet,
5. explicit decision on whether question-bank schema audit should come next.

Recommendation:

Run the pilot content audit next. Defer question-bank schema audit until at least one real Level II guide/test family proves the content-quality and source-traceability pattern. Defer pilot artifact authoring until after that audit returns a narrow authoring list.

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

1. `ops/agents/handoffs/2026-05-17-desktop-codex-neta-study-material-scout-build-closeout.md`
2. `ops/agents/handoffs/2026-05-17-desktop-codex-parallel-lane-orchestration-queue.md`
3. `ops/agents/handoffs/2026-05-17-desktop-codex-relay-review-burden-closeout.md`
4. `ops/agents/handoffs/2026-05-17-desktop-codex-neta-study-material-scout-build-prompt.md`
5. `ops/agents/handoffs/2026-05-17-desktop-codex-tcc-scout-prompt.md`
6. `ops/agents/handoffs/2026-05-17-parallel-lane-orchestration-governance-review-handoff.md`
7. `docs/operations/APEX-PARALLEL-LANE-ORCHESTRATION-GOVERNANCE-PLAN-2026-05-17.md`
8. `ops/knowledge-resource-operations/EXTRACTION-GAP-REPORT.md`
9. `ops/knowledge-resource-operations/EXTRACTION-LOAD-GAP-REPORT.md`
10. `ops/knowledge-resource-operations/EXTRACTION-PRIORITY-QUEUE.md`
11. `ops/knowledge-resource-operations/REMAINING-EXTRACTION-QUEUE.md`
12. `ops/knowledge-resource-operations/RESOURCE-AUDIT-REPORT.md`
13. `ops/knowledge-resource-operations/RESOURCE-COVERAGE-REPORT.md`
14. `ops/knowledge-resource-operations/RESOURCE-GOVERNANCE-AUDIT.md`
15. `ops/knowledge-resource-operations/RESOURCE-OPERATIONS-CHECKLIST.md`
16. `ops/knowledge-resource-operations/RESOURCE-PATH-REMEDIATION.md`
17. `ops/knowledge-resource-operations/RESOURCE-PATH-STATUS.md`

Source-domain files:

1. `C:\APEX Platform\source-domains\neta-ett-study-material\README.md`
2. `C:\APEX Platform\source-domains\neta-ett-study-material\GOVERNANCE-FRAMEWORK.md`
3. `C:\APEX Platform\source-domains\neta-ett-study-material\MASTER-STANDARDS.md`
4. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\FLASHCARD-SPEC.md`
5. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\INFRASTRUCTURE-ROADMAP.md`
6. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\PRACTICE-TEST-SPEC.md`
7. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\QUESTION-SCHEMA-SPEC.md`
8. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\README.md`
9. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\REFERENCE-SHEET-SPEC.md`
10. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\STAGING-FORMAT-SPEC.md`
11. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\STAGING-WORKFLOW-SPEC.md`
12. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\STUDY-GUIDE-SPEC.md`
13. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\TEMPLATE-FRAMEWORK-SPEC.md`
14. `C:\APEX Platform\source-domains\neta-ett-study-material\Build-Specs\TEST-SCAFFOLDING-SPEC.md`
15. `C:\APEX Platform\source-domains\neta-ett-study-material\Process-Guides\CONTENT-CREATION-WORKFLOW.md`
16. `C:\APEX Platform\source-domains\neta-ett-study-material\Process-Guides\NFPA-70B-2023-EXTRACTION-GUIDE.md`
17. `C:\APEX Platform\source-domains\neta-ett-study-material\Process-Guides\QUALITY-VALIDATION-CHECKLIST.md`
18. `C:\APEX Platform\source-domains\neta-ett-study-material\Process-Guides\README.md`
19. `C:\APEX Platform\source-domains\neta-ett-study-material\Process-Guides\RESOURCE-EXTRACTION-GUIDE.md`
20. `C:\APEX Platform\source-domains\neta-ett-study-material\Process-Guides\SESSION-PROTOCOL.md`
21. `C:\APEX Platform\source-domains\neta-ett-study-material\Process-Guides\SOURCE-CITATION-GUIDE.md`

Read-only directory inventories:

1. `C:\APEX Platform\source-domains\neta-ett-study-material\NETA-2`
2. `C:\APEX Platform\source-domains\neta-ett-study-material\NETA-3`
3. `C:\APEX Platform\source-domains\neta-ett-study-material\NETA-4`
4. `C:\APEX Platform\source-domains\neta-ett-study-material\Resources\Extractions`

## Exact File Written

1. `ops/agents/handoffs/2026-05-17-desktop-codex-neta-source-map-and-artifact-backlog-closeout.md`

## Validation

Required validation:

```powershell
git diff --check -- ops/agents/handoffs/2026-05-17-desktop-codex-neta-source-map-and-artifact-backlog-closeout.md
```

Result: PASS.

## Final Status

READY_FOR_JASON_DECISION
