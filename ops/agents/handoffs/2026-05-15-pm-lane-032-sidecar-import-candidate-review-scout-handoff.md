# PM Lane 032 Sidecar Import-Candidate Review Scout Handoff

Date: 2026-05-15
Executor: External sidecar
Scope: Project Miner Temp Power import-candidate review experience recommendation
Output boundary: handoff only

## Objective

Propose the simplest review experience for the read-only Project Miner Temp Power import candidate so Jason can approve business intent and exceptions without manually coordinating source interpretation, workbook mapping, task shaping, or AI handoffs.

The recommended posture is:

1. show the system's proposed import candidate as a concise approval packet,
2. make traceability and warnings visible without requiring workbook spelunking,
3. require human approval only before real PM business-state mutation,
4. keep source reading, grouping, dedupe, and warning generation automated and repeatable.

## 1. Recommended Import-Candidate Review Sections

The review surface should be one PM-facing candidate page or artifact with these sections, in this order:

1. Candidate Summary
   - Project name, client, site/location, source package name, generated-at timestamp, candidate ID, and read-only status.
   - Counts for proposed workpackages, tasks, apparatus rows, source rows, drawings, equipment inventory rows, capability rows, warnings, duplicates, and required decisions.
   - A single readiness state: Ready for approval, Needs edits, or Blocked.

2. Required Decisions
   - Short exception queue showing only items Jason or PM/Ops must decide.
   - Each row should include decision type, affected workpackage/task/apparatus, recommended action, risk level, and source trace.
   - This is the default landing focus because it protects Jason from reviewing every normalized row when only exceptions need attention.

3. Proposed Project Structure
   - Proposed project row.
   - Proposed workpackages grouped by estimator scope, drawing area, or Temp Power phase.
   - Proposed task groups under each workpackage.
   - Apparatus count and total estimated hours per group.

4. Apparatus And Task Candidates
   - A dense table of proposed task/apparatus rows.
   - Default view should be grouped and filterable by warning status, workpackage, drawing, designation, source sheet, apparatus type, and approval state.
   - Rows with no warnings should be collapsible so the PM review starts with risks rather than raw volume.

5. Source Traceability
   - For every proposed row, preserve source workbook, sheet, row, quantity expansion index when quantity is greater than one, source drawing/PDF, drawing page or designation when available, and source field/value evidence.
   - Include direct drillthrough metadata even if the first UI implementation only displays text references.

6. Duplicate And Conflict Review
   - Candidate duplicate groups by designation, apparatus type, drawing reference, source row, and normalized dedupe key.
   - Distinguish true duplicate candidates from valid repeated apparatus units created from estimator quantity expansion.

7. Resource Context
   - Equipment inventory coverage summary.
   - Technician capability coverage summary.
   - Gaps that may affect staffing, equipment availability, or execution readiness.

8. Import Impact Preview
   - Read-only preview of rows that a later admitted import mutation would create: project, workpackage, task, apparatus.
   - Explicitly state that no Supabase write, schedule mutation, assignment, or status change has occurred.

9. Audit Footer
   - Files used, command or endpoint used to generate the candidate, generation timestamp, validation status, capability gaps, and approval state history.

## 2. Required Fields For Jason's Approval View

The approval view should require only enough information for a trustworthy approve/edit/return decision:

1. Candidate identity
   - Candidate ID
   - Generated timestamp
   - Planning root
   - Candidate status
   - Read-only generation marker

2. Project identity
   - Project name
   - Client/customer
   - Site/location
   - Job number or external reference when available
   - Project lead or PM when available
   - Source package label, such as Project Miner Temp Power

3. Source evidence
   - Estimator workbook path/name
   - Estimator sheet and row references
   - SLD/PDF path/name
   - Drawing/page/designation references when available
   - Equipment inventory workbook path/name
   - Capability matrix workbook path/name
   - Project data-entry workbook and reference tracker lineage when used

4. Proposed import rows
   - Workpackage name
   - Workpackage source/scope
   - Task name
   - Task type or NETA standard when available
   - Apparatus type
   - Apparatus designation
   - Quantity and expansion index
   - Estimated hours per unit and total hours when available
   - Drawing reference
   - Apparatus category
   - Proposed priority/readiness, if derived

5. Review controls
   - Approve candidate
   - Edit candidate row or grouping
   - Return for correction
   - Mark duplicate as merge/ignore/keep separate
   - Add PM note
   - Require re-generation after source change

6. Approval certification
   - Approver name
   - Approval timestamp
   - Approval note
   - Acknowledgement that approval only authorizes the candidate for the later admitted import path and does not itself write production state unless a separate admitted mutation exists.

## 3. Top Warnings And Exceptions To Surface

Surface these warnings at the top of the candidate before the full row table:

1. Missing or ambiguous project identity
   - Missing project name, client, site, job number, or lead metadata.

2. Missing source traceability
   - Any proposed row without workbook, sheet, row, drawing, or designation trace where that evidence should exist.

3. Duplicate candidates
   - Same normalized designation, apparatus type, drawing, or source row appears more than once.
   - Quantity-expanded rows must be labeled clearly so valid repeated units are not mistaken for accidental duplicates.

4. Formula or workbook reliability warnings
   - Formula errors, blank expected cells, unsupported workbook shape, unreadable sheets, hidden mapping assumptions, or stale reference workbook counts.

5. Drawing and designation mismatch
   - Estimator apparatus designation does not appear in SLD/PDF evidence, drawing reference is missing, or multiple drawing references conflict.

6. Unmapped estimator rows
   - Rows skipped because quantity, equipment type, hours, scope, or designation could not be normalized.

7. Unassigned grouping
   - Apparatus rows that could not be confidently assigned to a workpackage or task group.

8. Resource context gaps
   - Apparatus type has no obvious equipment inventory support.
   - Required skill/capability is missing or unclear.

9. Import-blocking guardrail warnings
   - Candidate requires schema, mutation, macro execution, Supabase direct write, AI status assignment, or schedule mutation not admitted by the current lane.

10. Hosted proof gap
   - Render/Vercel parity missing when hosted UI proof is required, while still allowing local read-only candidate review to proceed if the candidate evidence is trustworthy.

## 4. Suggested Approval, Edit, And Return Flow

Keep the flow deliberately small:

1. Generate candidate
   - System reads the planning folder and produces a read-only candidate with warnings, traceability, and proposed grouping.

2. Review exceptions first
   - Jason or PM/Ops starts on Required Decisions.
   - Clean rows remain visible but collapsed by default.

3. Edit only the candidate, not source workbooks
   - PM/Ops can adjust grouping, display names, duplicate disposition, task naming, and approval notes on the candidate.
   - Source files remain immutable inputs during this lane.

4. Return for correction when source or parser evidence is insufficient
   - Return reasons should be structured: missing file, wrong source pair, ambiguous duplicate, missing drawing evidence, unreadable formula, bad grouping, or business-rule decision needed.

5. Approve candidate
   - Approval freezes the candidate version and records approver, timestamp, warnings accepted, warnings still blocking, and final row counts.
   - Approval does not write to Supabase by itself.

6. Hand off to later admitted import mutation
   - A separate packet can admit an idempotent Render-mediated import after the candidate review flow is proven.
   - The import mutation should reject stale, unapproved, or source-mismatched candidates.

## 5. What Should Remain Automated Vs Human-Approved

Automated and read-only:

1. Planning folder file resolution.
2. Workbook/PDF opening through deterministic readers.
3. Estimator row normalization.
4. Quantity expansion into apparatus candidates.
5. Proposed project/workpackage/task grouping.
6. Dedupe key generation and duplicate clustering.
7. Formula, blank-field, and unsupported-shape warning generation.
8. Source traceability capture.
9. Equipment inventory and technician capability summaries.
10. Candidate JSON/artifact generation.
11. Local validation and evidence summary.

Human-approved:

1. Final project identity.
2. Workpackage grouping when the source evidence is ambiguous.
3. Duplicate disposition where merge/keep/ignore affects real scope.
4. Apparatus/task inclusion or exclusion when business judgment is required.
5. Acceptance of material warnings.
6. Approval to advance a frozen candidate to a later import mutation.
7. Any field-facing process change.
8. Any production write, schedule change, assignment, status mutation, or escalation policy.

Never automatic in the current boundary:

1. Direct Excel-to-Supabase writes.
2. Workbook macro execution.
3. Schema migration.
4. AI assignment of apparatus or crews.
5. AI status/schedule mutation.
6. Importing into Supabase before approval and separate packet admission.

## 6. Capability Gaps

1. Hosted Render mutation-seam parity remains a blocker for hosted live proof when the candidate review must be exercised through deployed UI/API surfaces.
2. The import mutation is not admitted; the candidate review must stay read-only until a later packet admits a narrow idempotent write path.
3. Excel MCP or live Excel inspection may accelerate workbook understanding, but it is not a production runtime dependency and was not used by this sidecar.
4. PDF designation extraction quality may limit confidence if SLD/PDF references cannot be reliably mapped to estimator rows.
5. Candidate edit persistence needs an admitted storage location or artifact convention before UI editing becomes durable.
6. Approval identity/audit storage needs a later decision: local artifact metadata for preview, or Render/Supabase-backed approval state after write authority is admitted.
7. The review UI needs a clear stale-source check so Jason is not approving a candidate generated from outdated planning-folder inputs.

## 7. Exact Files Read

1. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
2. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
3. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
4. `docs/operations/APEX-OPS-VISUAL-SYSTEM-MAP-2026-05-15.md`

## Closeout Notes

No product code, tests, packets, status files, package files, environment files, workbook files, or source PM docs were edited.

No macros were run.

No Supabase, Render, or Vercel access was attempted.

No commit or staging was performed.
