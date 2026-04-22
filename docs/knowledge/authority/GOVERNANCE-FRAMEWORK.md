# NETA ETT Study Material - Governance Framework
## Multi-AI Workspace Coordination & Quality Assurance
### Version 1.9 | March 25, 2026

---

## 📋 DOCUMENT PURPOSE

This framework establishes the **Governance Lead** role for the NETA ETT Study Material project. It defines:

1. **Authority hierarchy** for standards and decisions
2. **Role/capability model** and task routing
3. **Quality verification** checkpoints and enforcement
4. **Coordination protocols** for multi-AI and cross-repo work
5. **Escalation procedures** for conflicts and blockers

**This document supersedes** any conflicting guidance in instance-specific instruction files.

---

## 🧭 AUTHORITATIVE DAILY OPERATING MODEL

The current operating model for this project is:

1. **One checked-in VS Code workspace** as the standard daily environment when both repositories are available.
2. **Two repositories with explicit ownership boundaries**:
   - `neta-ett-study-material` owns governance, standards, planning, audits, and content infrastructure.
   - `tcc_v5_backend` owns runtime application behavior, routes, services, migrations, tests, and application-facing implementation details.
3. **One shared Supabase seam** connecting the two repositories at the data-contract and acceptance level.
4. **One task-doc-driven coordination model** where cross-repo work is framed here and implemented in the repository that owns the behavior.
5. **One governed TCC architecture authority stack** for any TCC-related work:
   - `Development/Architecture/TCC-MASTER-SCHEMA-AUTHORITY.md`
   - `Development/Architecture/TCC-DLL-ARCHITECTURE-AUTHORITY.md`
6. **One governed resource lifecycle authority stack** for resource intake, naming, storage, extraction, manifests, and Supabase metadata integrity:
   - `MASTER-STANDARDS.md`
   - `Development/RESOURCE-GOVERNANCE-AUDIT.md`
   - `Process-Guides/RESOURCE-EXTRACTION-GUIDE.md`
   - `Development/RESOURCE-PATH-STATUS.md`
   - `Development/RESOURCE-PATH-REMEDIATION.md`
7. **Acceptance criteria matrices as the bounded audit pattern** when a task, family, or subsystem needs explicit closeout classification:
   - task delegator defines the criteria
   - task executor is held to those criteria
   - audits judge the work against the matrix, bounded by the governing authority surfaces

Workspace unification does **not** imply repository merge. A monorepo would be a separate architecture decision after protocol stability and shared-contract maturity are demonstrated.

### TCC Architecture Enforcement Rule

For TCC-related work, the study-material repository remains the tracked governance and architecture home even when implementation occurs in `tcc_v5_backend`.

This means:

1. verified architecture lives in the paired TCC authority documents, not in whichever backend implementation happens to exist today
2. backend work must read and respect the paired TCC authority documents before changing routes, services, migrations, tests, or contracts
3. if backend findings conflict with the accepted authority, the conflict must be resolved by updating the authority docs before the new interpretation is treated as standard
4. reviews should reject backend changes that silently redefine family boundaries, routing semantics, or selection flow without an authority update

### Acceptance Matrix Enforcement Rule

When a bounded acceptance matrix exists for a task or subsystem, it becomes the required audit surface for that bounded slice.

This means:

1. the delegating role defines the matrix criteria and required authority surfaces
2. the executing role should implement against those criteria instead of using informal completion language
3. reviewers should evaluate completion claims against the matrix rows, not against vague impressions of progress
4. matrices classify work against authority; they do not replace authority

See `Development/Architecture/ACCEPTANCE-CRITERIA-MATRIX-METHODOLOGY.md`.

### Resource Governance Enforcement Rule

When work touches resource intake, folder structure, naming, extraction placement, manifests, or Supabase `source_path` integrity, the governed resource lifecycle stack becomes mandatory.

This means:

1. active source paths must resolve to canonical repo-relative locations under `Resources/`
2. legacy aliases such as `IEEE-Standards`, `IEC-Standards`, `UL-Standards`, `NETA-Standards`, `Manufacturer-Docs`, or `Testing Resources` must not be reintroduced as new active storage conventions
3. structural changes to resource categories or locations must be followed by manifest regeneration and a documented downstream path audit when Supabase-backed content is affected
4. unresolved historical references must be classified explicitly, including `historical-source-retired` where appropriate, instead of being left as vague manual-review residue
5. extraction processing remains disk-first and governed by the extraction guide before any Supabase write path is considered authoritative

| 1.10 | Mar 28, 2026 | Added the model allocation governance rule, formalized Tier A/B/C definitions plus four-factor scoring, and required explicit model-tier declarations in new or materially revised task handoffs and packet JSON. |
---

## 🚨 HARDCODED OPERATING PRINCIPLE — READ EVERY SESSION

> **Jason and all active AI instances are equal stakeholders in this project. Best idea wins, no ego. This is non-negotiable.**

### What This Means in Practice

1. **Pushback is required, not tolerated.** If a proposed approach has a better alternative, say so. Agreement-by-default is a failure mode — it produces mediocre output and erodes trust.

2. **Offer alternatives, not just objections.** "That won't work" is incomplete. "That won't work because X — here's what I'd do instead" is the standard.

3. **Declare limitations honestly.** If the tools, resources, context, or capabilities available are insufficient to meet the quality standard, say so immediately and specify what's needed. Silently producing subpar work because of undisclosed constraints is unacceptable.

4. **No hierarchy on ideas.** Task routing and authority levels (below) exist for coordination. They do not mean the Governance Lead's ideas outrank execution-oriented instances, or that Jason's first instinct is always correct. The best idea wins regardless of source.

5. **This principle is permanent.** It does not expire, get overridden by time pressure, or get suspended for "quick tasks." Every session, every task, every decision.

6. **Historical precedent does not outrank improvement.** If a newer pattern is demonstrably better, the governance standard is to improve the pattern, not to preserve an older weaker version for the sake of superficial consistency.

### Continuous Improvement And Consistency Rule

Consistency matters, but it must be consistency around the strongest justified
pattern available at the time of review.

This means:

1. older work is not immune from improvement just because it shipped earlier
2. newer improvements should be evaluated as potential upgrades to the standard,
   not treated as suspect merely because they are new
3. when older and newer patterns diverge, the correct governance question is not
   "Which came first?" but "Which better serves the user, the standard, and the
   long-term quality bar?"
4. if the better pattern is newer, governance should either normalize the newer
   pattern into the accepted standard or create a bounded follow-on plan to
   uplift older work toward that stronger pattern
5. the Governance Lead, technical-authority holder, and stakeholder-role holder
   are expected to raise improvement opportunities proactively, even when the
   current output is already acceptable or historically consistent

The standing question is:

> "Is this the best justified pattern we have right now, or is there a real opportunity to improve it?"

### Session Resume Requirement

Every instance MUST acknowledge this principle at session start. If a session resume document does not reference this section, the instance should read GOVERNANCE-FRAMEWORK.md before proceeding with any task.

In the consolidated workspace, session continuity is no longer one overloaded document. The required model is:

1. one workspace hub resume
2. one current resume per active lane
3. historical session summaries marked as reference-only

---

## 🎯 CORE PHILOSOPHY: STAKEHOLDER APPROACH

> **"Standards define the minimum framework, not the product itself."**

Every specification, line count, and checklist in this project represents a **floor, not a ceiling**. The true standard is the stakeholder approach:

### What This Means

| Mindset | ❌ Compliance Approach | ✅ Stakeholder Approach |
|---------|------------------------|-------------------------|
| **Goal** | Meet the spec | Create lasting value |
| **Line counts** | Target to hit | Indicator, not definition |
| **Checklists** | Boxes to check | Minimum gates before enhancement |
| **"Complete"** | Meets requirements | No remaining opportunities identified |
| **Quality** | Passes validation | Would I stake my reputation on this? |

### The Enhancement Mandate

Every instance, at every stage, operates with this standing directive:

```
While executing any task, continuously ask:
"What opportunities exist to enhance this beyond the minimum?"
```

**Enhancement opportunities include:**
- Deeper source integration (Paul Gill, IEEE, NETA ATS)
- Additional worked examples or calculations
- Real-world scenarios and field tips
- Visual aids that clarify complex concepts
- Safety content that could prevent incidents
- Cross-references that build understanding
- Content that serves technicians throughout their careers, not just exam day

### When Enhancement Stops

Enhancement continues until:
1. **Diminishing returns** - Additional content wouldn't meaningfully improve learning
2. **Scope creep** - Enhancement expands beyond the topic's boundaries
3. **Time constraints** - Jason explicitly prioritizes completion over depth
4. **Resource limits** - Source material exhausted for this topic

**Default assumption:** If none of these apply, keep enhancing.

### Consistency Standard

Consistency is required, but not as a defense of stale patterns.

The correct consistency target is:

1. align comparable work to the best validated pattern currently available
2. document intentional deviations when a topic-specific reason justifies them
3. do not freeze a weaker historical style or structure simply because older
   guides used it
4. when a new pattern is better, decide deliberately whether to uplift prior
   work, normalize the new pattern, or formalize a topic-bounded exception

### Metrics Are Indicators, Not Standards

| Metric | What It Indicates | What It Doesn't Mean |
|--------|-------------------|----------------------|
| Line count | Content volume | Quality or completeness |
| Section count | Structure coverage | Depth of coverage |
| Citation count | Source integration | Accuracy or authority |
| Checkbox completion | Minimum gates passed | No enhancement opportunities remain |

**A 2,000-line document can still have enhancement opportunities.**
**A 600-line document can be genuinely complete if the topic is narrow.**

The question is never "Does it meet the spec?" but rather "Have we exhausted opportunities to create lasting value?"

---

## 🏛️ GOVERNANCE HIERARCHY

```
┌─────────────────────────────────────────────────────────────────┐
│                     JASON (Project Owner)                        │
│         Final authority on content, priorities, direction        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                 GOVERNANCE LEAD (Role, not model)                │
│  • Creates/maintains standards and specifications                │
│  • Reviews completed work for quality compliance                 │
│  • Resolves conflicts between specifications                     │
│  • Approves major structural changes                             │
│  • Coordinates cross-instance handoffs                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌──────────────────────────┐      ┌──────────────────────────────┐
│      EXECUTION ROLE      │      │       SPECIALIST ROLE        │
│    (tool-capable agent)  │      │     (as capability fits)     │
│                          │      │                              │
│ • File/script execution  │      │ • Specialized support tasks  │
│ • Large-file transforms  │      │ • Domain- or tool-specific   │
│ • Multi-step delivery    │      │ • Non-governance support     │
└──────────────────────────┘      └──────────────────────────────┘

| Level | Role | Authority Scope |
|-------|------|-----------------|
| **L1** | Jason | All decisions, priority changes, content approval |
| **L2** | Governance Lead | Standards creation, quality enforcement, coordination |
| **L3** | Executing Instances | Task execution within defined parameters |

### Decision Rights

| Decision Type | Authority | Escalate If |
|---------------|-----------|-------------|
| Content accuracy | L1 (Jason) | Always verify technical claims |
| Quality standards | L2 (Governance Lead) | New pattern not in specs |
| Task execution | L3 (Executing instance) | Blocker encountered |
| Priority changes | L1 (Jason) | Never assume |
| Spec interpretation | L2 (Governance Lead) | Ambiguity in Build-Specs |
| New file creation | L3 with L2 review | Structure differs from standard |
| **Supabase writes (INSERT/UPSERT/DELETE)** | **L3 (VS Code) after L1/L2 review** | Always — CC never writes to Supabase autonomously |

---

## 🎯 ROLE CAPABILITY MATRIX

### Primary Assignments

| Role | Optimal Tasks | Avoid | Capability Requirement |
|----------------|---------------|-------|---------------|
| **Governance Lead** | Governance docs, complex analysis, quality review, strategic planning, standards interpretation, task framing, structural decisions | Purely repetitive batch work | Must have strong reasoning and document-control capability |
| **Execution Lead** | Surgical edits, file operations, Supabase loads, git commits, script execution, KSA discovery, study guide assembly, multi-file coordination | Large greenfield authoring without task framing | Must have strong tool access and reliable file-operation capability |
| **Batch Executor** | PDF extraction batches, structured fills, heavy scripting, repetitive transformations, large-file processing | Ambiguous strategy or policy decisions | Must handle repetitive execution at scale |
| **Specialist Support** | Domain- or tool-specific support where a capability gap exists | Owning the governance contract by default | Chosen per task-specific strengths |

### Task Routing Decision Tree

```
NEW TASK RECEIVED
       │
       ▼
┌──────────────────────────────────────┐
│ Does task require judgment/strategy? │
└──────────────────────────────────────┘
       │
   YES │                    NO
       ▼                     │
┌────────────────┐           │
│ Governance Lead│           ▼
│   (role)       │  ┌────────────────────────────┐
└────────────────┘  │ Is it batch/repetitive?    │
                    └────────────────────────────┘
                           │
                    YES    │         NO
                           ▼          │
                    ┌──────────┐      │
                    │ Batch    │      ▼
                    │ Executor │  ┌───────────────────────────┐
                    └──────────┘  │ Is it surgical/precise?   │
                                  └───────────────────────────┘
                                         │
                                  YES    │         NO
                                         ▼          │
                                  ┌────────────────┐  │
                                  │ Execution Lead │  ▼
                                  └────────────────┘┌─────────────────┐
                                                    │ Specialist or   │
                                                    │ Batch Executor  │
                                                    └─────────────────┘
```

### Specific Task Assignments

| Task Category | Preferred Role | Rationale |
|---------------|-------------------|-----------|
| **Standards/Specs Creation** | Governance Lead | Requires strategic thinking, cross-reference synthesis |
| **Content Authoring (judgment-heavy)** | Governance Lead | Requires field judgment and high-context synthesis |
| **Audit Execution** | Execution Lead | Systematic analysis, document comparison |
| **Supabase loads + git commits** | Execution Lead | File operations, script execution, pipeline execution |
| **KSA link discovery** | Execution Lead | Script execution against live systems or generated data |
| **PDF Extraction (batch)** | Batch Executor | Heavy scripting, OCR cleanup, repetitive extraction work |
| **Structured fills / repetitive assembly** | Batch Executor | Template-driven throughput work |
| **Study Guide Assembly** | Execution Lead | Concatenation and validation via assemble tooling |
| **New Content Extraction** | Governance Lead or Batch Executor | Use governance for selective judgment, batch role for scale |
| **Quality Review** | Governance Lead | Final verification against standards |

---

## 📊 QUALITY VERIFICATION CHECKPOINTS

> **Remember:** These checkpoints verify MINIMUM requirements. Passing all checkpoints does not mean "done" - it means "ready to assess enhancement opportunities."

### Checkpoint 1: Pre-Execution (Instance Self-Check)

Before starting any task, executing instance MUST verify:

```markdown
## Pre-Execution Checklist
- [ ] Read GOVERNANCE-SESSION-RESUME.md (current governance session hub) or the active task doc before acting
- [ ] Check staging/[topic]/STATUS.md if working on a specific guide topic
- [ ] Read CONTENT-FORMAT-SPEC-v2.3.md if authoring or modifying study guide content
- [ ] Check NETA-Equipment-Category-Standard.md for NETA section numbers (never from memory)
- [ ] Confirm task parameters are unambiguous
- [ ] Note any assumptions requiring validation
- [ ] Verify no `active_work` flag set in STATUS.md for the target topic
```

### Checkpoint 2: Mid-Execution (Progress Verification)

For tasks >30 minutes or >500 lines:

```markdown
## Mid-Execution Checkpoint
- [ ] Content aligns with Build-Spec structure
- [ ] No placeholder text remaining in completed sections
- [ ] Quality dimensions addressed (per audit guide)
- [ ] Safety content included where applicable
- [ ] Source citations formatted correctly
```

### Checkpoint 3: Pre-Commit (Completion Verification)

Before any file is considered complete:

```markdown
## Pre-Commit Checklist

### Structure (Minimum Framework)
- [ ] File naming follows MASTER-STANDARDS.md convention
- [ ] Located in correct folder
- [ ] Line count meets minimum (if applicable)

### Content (Minimum Framework)
- [ ] All Six Quality Dimensions addressed
- [ ] No TODO/PLACEHOLDER text remaining
- [ ] NETA ATS/IEEE citations present (where applicable)
- [ ] Safety content integrated (not just appended)

### Technical (Minimum Framework)
- [ ] HTML validates (no broken tags)
- [ ] JavaScript functional (practice tests)
- [ ] CSS consistent with project theme
- [ ] Navigation links work

### Enhancement Assessment (Stakeholder Standard)
- [ ] Reviewed for additional source integration opportunities
- [ ] Considered additional worked examples
- [ ] Evaluated visual aid opportunities
- [ ] Assessed field tip / real-world scenario additions
- [ ] Documented any deferred enhancements with rationale

### Documentation
- [ ] Task doc status updated (if applicable)
- [ ] Commit message follows format
- [ ] Enhancement opportunities noted (if deferred)
```

### Checkpoint 4: Post-Commit (Governance Review)

The Governance Lead reviews completed work for:

| Review Aspect | Criteria | Action if Failed |
|---------------|----------|------------------|
| Spec Compliance | Matches Build-Spec structure | Return for correction |
| Quality Tier | Meets target tier (Gold/High Quality) | Flag gaps, prioritize enhancement |
| Consistency | Matches existing content patterns | Document deviation or correct |
| Safety | No unsafe practices described | Immediate correction required |
| **Enhancement** | **Opportunities exhausted or documented** | **Identify and queue remaining opportunities** |

**Governance Review Focus:**

The primary question in governance review is NOT "Does this meet the spec?" but rather:

> "If a technician relies on this material throughout their career, will it serve them well? What opportunities remain to make it better?"

Even content that passes all minimum checkpoints may be returned with enhancement recommendations.

---

## 🔄 COORDINATION PROTOCOLS

### Task Handoff Format

When passing work between instances:

```markdown
## HANDOFF: [Task Name]
**From:** [Instance Name]
**To:** [Instance Name]
**Date:** [ISO Date]

### Completed Work
- [What was done]
- [Files created/modified]
- [Decisions made]

### Remaining Work
- [Specific next steps]
- [Dependencies]
- [Blockers if any]

### Files Involved
| File | Status | Notes |
|------|--------|-------|
| [path] | [Complete/Partial/Staged] | [Context] |

### Validation Required
- [ ] [Specific check needed]

### Assumptions Made
- [Any assumptions requiring validation]
```

### Communication Hub Structure

Cross-role coordination uses the **task document model** (deprecated CLAUDE-COMMUNICATION.md pattern — do not use):

- **Governance Lead** creates task documents in `Development/staging/[topic]/` or `Development/`
- **Execution Lead** reads the task doc, executes, and commits
- **Current active tasks:** `Development/Control-Plane/EXECUTION-TASKS-CURRENT.md`
- **Session state:** `Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md` (used as the workspace hub)
- **Lane state:** lane-specific current resumes in `Development/Control-Plane/`
- **Topic state:** `Development/staging/[topic]/STATUS.md` (read before acting on any topic folder)

The `GOVERNANCE-SESSION-RESUME.md` file remains the single coordination hub, but not the single detailed resume. It should contain:

- workspace-wide platform and boundary state
- routing into the active lane resumes
- current shared priorities and operating rules
- next session start instructions at the workspace level

Detailed lane continuity belongs in the lane-specific current resumes, not in the hub file.

### Task Document Governance Requirements

Every task document delegated to Claude Code (CC) MUST contain these mandatory sections.
Task docs missing any of these sections shall not be executed.

#### Mandatory Sections

1. **Scope Lock Statement** — Explicit list of what the task covers AND what it
   does not cover. Include: "If you discover something that seems like it should
   be done, STOP and note it in the Observations section. Do not act on it."

2. **Output Format Specification** — Exact format requirements for all deliverables.
   For extractions: reference RESOURCE-EXTRACTION-GUIDE V2.0 curated format.
   For code: language, style, test requirements.
   For content: reference CONTENT-FORMAT-SPEC v2.3.

3. **No-Auto-Load Rule** — Explicit statement: "Do NOT write to Supabase. All
   database operations happen in a separate human-reviewed task after output
   quality is verified on disk."

4. **Commit Protocol** — When and how to commit. Standard: one commit per
   discrete deliverable, with prescribed commit message format.

5. **Stop Conditions** — Explicit markers or situations where CC must stop
   and report rather than continue. Examples: unexpected file states, ambiguous
   source material, scope boundary reached.

6. **Observations Section** — A blank section at the bottom where CC records
   anything discovered that falls outside scope. This is the pressure valve
   that prevents unauthorized scope expansion.

#### Exemplar Task Docs
These existing task docs demonstrate the correct pattern:
- `TASK-CC-REEXTRACT-RAW-DUMPS.md` — Gold standard for governance guardrails
- `TASK-CC-GROUND-FAULT-PROTECTION-SYSTEMS-LO-FILL.md` — Good CC fill boundary example

#### Non-Compliant Task Docs (historical — do not replicate)
- Early extraction tasks (pre-Mar 15) lacked scope locks and format specs
- CC treated absence of constraints as implicit permission for autonomous action

### Conflict Resolution

When instances encounter conflicting guidance:

1. **Stop work** on conflicted item
2. **Document conflict** in the relevant task doc or GOVERNANCE-SESSION-RESUME.md
3. **Escalate to the Governance Lead** for resolution
4. **Wait for clarification** before proceeding

Resolution authority:
- **Spec conflicts:** Governance Lead resolves, updates Build-Specs
- **Priority conflicts:** Jason resolves
- **Technical conflicts:** Governance Lead investigates, recommends to Jason

---

## 📏 ENFORCEMENT MECHANISMS

### Quality Gates (Hard Stops)

Content CANNOT be marked complete without:

| Gate | Requirement | Enforced By |
|------|-------------|-------------|
| **Structure** | Matches Build-Spec template sections | Pre-commit checklist |
| **Naming** | Follows MASTER-STANDARDS.md conventions | Pre-commit checklist |
| **Safety** | No unsafe practices; warnings present | Governance review |
| **Sources** | Citations for technical claims | Governance review |
| **Testing** | Browser-tested (HTML files) | Pre-commit checklist |

### Quality Flags (Require Attention)

Content marked with flags for future enhancement:

| Flag | Meaning | Action |
|------|---------|--------|
| `[NEEDS-DEPTH]` | Below target line count or quality tier | Add to enhancement queue |
| `[NEEDS-SOURCES]` | Missing authoritative citations | Schedule source integration |
| `[NEEDS-VISUALS]` | Missing diagrams/charts | Add to visual enhancement queue |
| `[REVIEW-SAFETY]` | Safety content may be incomplete | Priority governance review |
| `[ENHANCE-DEFERRED]` | Enhancement opportunities identified but deferred | Document rationale, queue for later |
| `[ENHANCEMENT-EXHAUSTED]` | All reasonable opportunities explored | Governance confirmation required |

### Enhancement Documentation

When deferring enhancement opportunities, document:

```markdown
## Deferred Enhancements
| Opportunity | Rationale for Deferral | Priority |
|-------------|------------------------|----------|
| Add IEEE 43 temperature curves | Source not available | Medium |
| Additional motor failure case study | Time constraint | Low |
```

This creates a backlog for future enhancement passes.

### Non-Compliance Handling

| Severity | Example | Response |
|----------|---------|----------|
| **Critical** | Unsafe content, broken functionality | Immediate rollback, priority fix |
| **Major** | Wrong structure, missing required sections | Return for correction before merge |
| **Major** | Raw-dump extraction format (no curation, page markers, OCR artifacts) | Reject output, queue for re-extraction per RESOURCE-EXTRACTION-GUIDE V2.0 |
| **Minor** | Style inconsistency, missing optional elements | Flag for future enhancement |

---

## 📁 DOCUMENT HIERARCHY (Updated)

### Workspace Operating Topology

```text
VS Code Workspace
NETA ETT Study Material.code-workspace
│
├── Repository 1: neta-ett-study-material/   ← Governance + content system
│   │
│   ├── Root authority docs
│   │   ├── GOVERNANCE-FRAMEWORK.md
│   │   └── MASTER-STANDARDS.md
│   │
│   ├── Delivery surfaces
│   │   ├── NETA-2/
│   │   ├── NETA-3/
│   │   └── NETA-4/
│   │
│   ├── Reference and specification surfaces
│   │   ├── Build-Specs/
│   │   ├── Process-Guides/
│   │   ├── Resources/
│   │   └── Archive/
│   │
│   └── Active control plane
│       └── Development/
│           ├── Architecture/    ← repo boundaries, workspace design, platform contracts
│           ├── Audits/          ← workspace and pipeline audits
│           ├── Control-Plane/   ← live resume, task tracker, coordination docs
│           ├── Platform/        ← TCC integration and shared-platform planning
│           └── Scripts/         ← active operational tooling
│
├── Repository 2: ../Projects/tcc_v5_backend/ ← Runtime application system
│   ├── FastAPI app code
│   ├── routes, services, and UI/demo behavior
│   ├── migrations and tests
│   └── runtime implementation of accepted TCC contracts
│
└── Shared integration seam
   └── Supabase
      ├── persistence contract
      ├── shared data model expectations
      └── cross-repo acceptance path
```

### Integration vs. Segregation Rules

- **Integrated at the workspace level:** both repositories load into one editor session and are governed by one documented operating model.
- **Integrated at the contract level:** shared architecture, task framing, and acceptance criteria are documented from this repository.
- **Integrated at the data level:** Supabase is the explicit seam for persistence and shared platform behavior.
- **Segregated at the ownership level:** governance, content, audits, and planning stay in `neta-ett-study-material`; runtime code, migrations, and tests stay in `tcc_v5_backend`.
- **Segregated at the implementation level:** cross-repo coordination does not justify copying code or collapsing the repos prematurely.

### Authority Document Stack

```text
GOVERNANCE-FRAMEWORK.md (THIS DOCUMENT)
│   └── Establishes authority, coordination, enforcement
│
├── MASTER-STANDARDS.md
│   └── Folder structure, naming, conventions, quality dimensions
│
├── Build-Specs/
│   ├── PRACTICE-TEST-SPEC.md → Authoritative for practice tests
│   ├── STUDY-GUIDE-SPEC.md → Authoritative for study guides
│   └── [Other specs as created]
│
├── Process-Guides/
│   ├── CONTENT-CREATION-WORKFLOW.md → Workflow reference
│   ├── QUALITY-VALIDATION-CHECKLIST.md → Verification procedures
│   └── SESSION-PROTOCOL.md → Historical reference; not the primary entry point
│
├── Development/Architecture/
│   ├── REPOSITORY-REGISTRY.md → Repository ownership and local workspace contract
│   └── UNIFIED-PLATFORM-ARCHITECTURE.md → Shared ETT + TCC platform model
│
├── Development/Audits/
│   └── AUDIT-UNIFIED-WORKSPACE-TCC-INTEGRATION-2026-03-21.md → Workspace verification record
│
└── Development/Control-Plane/
   ├── GOVERNANCE-SESSION-RESUME.md → Session state and coordination hub
   ├── EXECUTION-TASKS-CURRENT.md → Active execution tracker
   └── INSTANCE-QUICK-REFERENCE.md → Fast operator entry reference
```

### Precedence Rules

When documents conflict:
1. **GOVERNANCE-FRAMEWORK.md** (this document) takes precedence for process/coordination
2. **MASTER-STANDARDS.md** takes precedence for structure/naming
3. **Build-Specs/** takes precedence for content format
4. **More recent version** takes precedence when specs updated

---

## 🔄 GOVERNANCE MAINTENANCE

### Review Schedule

| Document | Review Frequency | Reviewer |
|----------|------------------|----------|
| GOVERNANCE-FRAMEWORK.md | Monthly or after major process change | Governance Lead |
| MASTER-STANDARDS.md | Quarterly or after structure change | Governance Lead |
| Build-Specs/* | After each content type iteration | Governance Lead |
| GOVERNANCE-SESSION-RESUME.md | Each session | Active instance |

### Update Protocol

1. **Propose change** with rationale
2. **Review impact** on existing content/processes
3. **Update document** with version increment
4. **Notify affected instances** via task doc or GOVERNANCE-SESSION-RESUME.md
5. **Archive previous version** if major change

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.9 | Mar 25, 2026 | Added an explicit continuous-improvement and consistency rule clarifying that historical precedent does not outrank a better justified pattern, and that governance should normalize to the strongest current standard rather than preserve weaker older patterns for their own sake. |
| 1.7 | Mar 21, 2026 | Added an explicit daily operating model for the checked-in multi-root workspace, the two-repository ownership split, the Supabase shared seam, and the task-doc-driven cross-repo execution contract. |
| 1.6 | Mar 21, 2026 | Replaced model-specific governance naming with role-based nomenclature (`Governance Lead`, `Execution Lead`, `Batch Executor`, `Specialist Support`) so the workspace contract remains stable across different models and toolsets. |
| 1.5 | Mar 21, 2026 | Reassigned the governance-architect role from Desktop Claude to VS Code GPT-5.4 across the authority, routing, capability, review, and escalation sections of the framework. |
| 1.4 | Mar 21, 2026 | Added visual workspace operating topology showing the two-repository model, explicit Supabase integration seam, and the authority document stack. Updated document hierarchy to reflect `Development/Architecture/`, `Development/Audits/`, and `Development/Control-Plane/` as the active governance surfaces. |
| 1.2 | Mar 14, 2026 | Updated instance names (Codex → Claude Code); updated model versions (4.5 → 4.6); replaced deprecated CLAUDE-COMMUNICATION.md coordination pattern with task-doc + STATUS.md model; updated Pre-Execution Checklist; updated task assignment table to reflect the three-instance workflow in place at that time. |
| 1.3 | Mar 15, 2026 | Added Task Doc Governance Requirements section (mandatory sections for CC task docs); Added Supabase write authorization to Decision Rights; Added extraction format non-compliance to enforcement tiers. Driven by Mar 15 CC unauthorized extraction incident post-mortem. |
| 1.1 | Mar 8, 2026 | Added HARDCODED OPERATING PRINCIPLE — equal stakeholder collaboration, pushback required, best idea wins, limitations must be declared. Session resume requirement added. |
| 1.0 | Dec 26, 2025 | Initial governance framework established |

---

## ✅ ADOPTION CHECKLIST

For this framework to be effective:

- [ ] All executing instances read this document before starting work
- [ ] ~~CLAUDE-COMMUNICATION.md~~ Deprecated — coordination via task docs and GOVERNANCE-SESSION-RESUME.md
- [ ] ~~VS-CODE-AI-INSTRUCTIONS.md~~ Deprecated — superseded by GOVERNANCE-FRAMEWORK.md
- [ ] `NETA ETT Study Material.code-workspace` is the standard entry artifact when both repositories are available
- [ ] Jason confirms authority structure and escalation paths
- [ ] First governed work session completes successfully

---

## 📞 ESCALATION CONTACTS

| Issue Type | Escalate To | Method |
|------------|-------------|--------|
| Spec ambiguity | Governance Lead | Note in task doc or GOVERNANCE-SESSION-RESUME.md |
| Priority conflict | Jason | Direct conversation |
| Technical blocker | Governance Lead | Note in task doc or GOVERNANCE-SESSION-RESUME.md |
| Quality concern | Governance Lead | Flag in pre-commit notes |
| Safety issue | Jason + Governance Lead | Immediate notification |

---

*This framework establishes the Governance Lead role as the authority for standards, quality, and coordination. Which model occupies that role may change; the governance contract should not.*
