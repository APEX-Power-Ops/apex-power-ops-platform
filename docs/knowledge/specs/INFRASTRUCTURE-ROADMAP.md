# NETA ETT Infrastructure Roadmap
## Phases 1-4: From Current State to Scalable Content Pipeline
### Created: December 19, 2025

Status note: This document remains useful as a historical foundation for why the project built governance, specs, and workflow structure the way it did. It is no longer the authoritative session-start or coordination protocol. For current operation, start with `GOVERNANCE-FRAMEWORK.md`, `MASTER-STANDARDS.md`, `Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md`, and `Development/Control-Plane/EXECUTION-TASKS-CURRENT.md`.

March 2026 addendum:

- the workspace now operates as a multi-root model with the sibling `tcc_v5_backend` repo included
- the old `.claude/CURRENT_STATE.md` and `CLAUDE-COMMUNICATION.md` coordination model is obsolete
- this roadmap should be read as an origin document plus migration-history context, not as the active workflow contract

---

## 🎯 OBJECTIVE

Transform the NETA ETT Study Material project from ad-hoc content creation into a systematic, documented infrastructure that enables:
- Consistent quality across all content types
- Efficient multi-role collaboration
- Reproducible workflows with clear handoff protocols
- Future migration readiness for RESA Power Platform

---

## 📊 CURRENT STATE (Pre-Roadmap)

### Repository Structure (as of Dec 19, 2025)
```
NETA ETT Study Material/
├── .claude/                    # Session state files
│   ├── CURRENT_STATE.md
│   ├── DECISIONS_LOG.md
│   └── HANDOFF_TEMPLATE.md
├── .github/
│   └── ISSUE_TEMPLATE/         # Content Gap, Enhancement templates
├── Build-Specs/                # THIS FOLDER - specs live here
├── Process-Guides/             # Workflow documentation
├── NETA-2/                     # Student content (COMPLETE)
├── NETA-3/                     # Student content (enhancement phase)
├── Development/                # Working files, staging, coordination
├── Resources/                  # Anki decks, extractions, crosswalk
├── Archive/                    # Superseded content
└── MASTER-STANDARDS.md         # Governing document (v1.2)
```

### Content Status
| Level | Practice Tests | Study Guides | Status |
|-------|---------------|--------------|--------|
| NETA-2 | 30/30 ✅ | 32 ✅ | COMPLETE |
| NETA-3 | 10 | 28 (enhancement phase) | IN PROGRESS |
| NETA-4 | 0 | 0 | NOT STARTED |

---

## 🔵 PHASE 1: Establish Canonical Documentation Hierarchy

**Goal:** Each document has ONE job. If you need practice test specs, there's ONE place to look.

### 1.1 Create Build-Specs/ (Consolidate scattered specs)

| New File | Consolidates From | Purpose |
|----------|-------------------|---------|
| `PRACTICE-TEST-SPEC.md` | NETA2-PRACTICE-TEST-CONTENT-SPEC.md, TEST-SCAFFOLDING-SPEC.md, GOLD-STANDARD-AUDIT.md | Single source for practice test requirements |
| `STUDY-GUIDE-SPEC.md` | Scattered requirements in various docs | Study guide format, depth requirements |
| `STAGING-WORKFLOW-SPEC.md` | STAGING-FORMAT-SPEC.md | How staged content should be formatted |
| `REFERENCE-SHEET-SPEC.md` | (new) | Quick reference card format |
| `FLASHCARD-SPEC.md` | (new) | Anki deck creation standards |

### 1.2 Create Process-Guides/ (Consolidate workflows)

| New File | Consolidates From | Purpose |
|----------|-------------------|---------|
| `SESSION-PROTOCOL.md` | Adapted from RESA WORKSPACE_PROTOCOL.md | Historical start/end procedure baseline; later superseded as an active protocol |
| `CONTENT-CREATION-WORKFLOW.md` | Various handoff docs | Extraction → Staging → Assembly → Final |
| `CROSS-INSTANCE-COORDINATION.md` | HANDOFF-PROTOCOL.md, early coordination docs | Governance vs execution responsibilities |
| `RESOURCE-EXTRACTION-GUIDE.md` | (new) | How to process source PDFs |
| `QUALITY-VALIDATION-CHECKLIST.md` | (new) | Pre-commit quality gates |

### 1.3 Create Reference/ (Extract from MASTER-STANDARDS)

| New File | Source | Purpose |
|----------|--------|---------|
| `FOLDER-STRUCTURE.md` | MASTER-STANDARDS.md Section 2 | Directory layout reference |
| `NAMING-CONVENTIONS.md` | MASTER-STANDARDS.md Section 3 | File naming rules |
| `TAGGING-SCHEMA.md` | Resources/Catalog/TAGGING-SCHEMA.md | KSA tagging system |

### 1.4 Archive Superseded Documents
Move to `Archive/Documentation/` after consolidation:
- Development/NETA-2/SESSION-RESUME-*.md files
- Development/NETA-3/SESSION-RESUME-*.md files
- Redundant spec files

### Phase 1 Deliverables
- [ ] Build-Specs/ folder with 5 spec documents
- [ ] Process-Guides/ folder with 5 workflow documents
- [ ] Reference/ folder with 3 reference documents
- [ ] MASTER-STANDARDS.md updated to v1.3 (references new locations)
- [ ] Superseded docs archived

---

## 🟢 PHASE 2: Git Version Control ✅ COMPLETE

**Status:** Implemented December 19, 2025

### Completed Items
- [x] GitHub repository created (private): `jasonlswenson-sys/neta-ett-study-material`
- [x] Issue templates configured (Content Gap, Enhancement)
- [x] .gitignore configured
- [x] All content committed and pushed
- [x] Commit format established

### Commit Message Format
```
[AREA] Brief description

- Detail 1
- Detail 2

Refs: #issue-number or context
```

**Area Tags:** [CONTENT], [SPEC], [PROCESS], [INFRA], [FIX], [REFACTOR], [EXTRACT]

---

## 🟡 PHASE 3: Formalize Session Protocol

Historical note: the specific protocol steps below describe the December 2025 operating model. They are retained to show the original infrastructure intent, but they are not the active March 2026 session protocol.

**Goal:** Standardized start/end procedures for any AI instance working on this project.

### 3.1 Session Start Protocol
```
1. Read GOVERNANCE-FRAMEWORK.md
2. Read Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md and Development/Control-Plane/EXECUTION-TASKS-CURRENT.md
3. Review relevant Build-Specs/ for current work type
4. Claim work through the active task/resume tracker model
```

### 3.2 Session End Protocol
```
1. Commit all changes with proper [AREA] tag
2. Update the active tracker/task/resume artifacts with:
   - Work completed
   - Work remaining
   - Any blockers
3. Log significant governance or architecture decisions in the current control-plane docs as needed
4. Push to remote
5. Record any needed handoff in the current task-doc / resume model
```

### 3.3 Memory Update Protocol

| Category | Examples | Update Frequency |
|----------|----------|------------------|
| **PERMANENT** | Project philosophy, team context, folder structure summary | Rarely (major changes only) |
| **SEMI-PERMANENT** | Current phase, major milestones, key file locations | Weekly or at phase transitions |
| **NEVER IN MEMORY** | Session-specific tasks, current file being edited | Lives in docs only |

### 3.4 Cross-Instance Coordination

| Operating Role | Primary Responsibilities | Typical Strengths |
|----------------|-------------------------|-------------------|
| **Governance Lead** | New content framing, specifications, task definition | Strategic analysis, standards control |
| **Execution Lead** | Surgical edits, analytics integration, pattern replication | Code editing, file navigation |
| **Batch Executor** | Large extraction batches, repetitive transformations | Throughput, extraction, scripting |

### Phase 3 Deliverables
- [ ] Process-Guides/SESSION-PROTOCOL.md created
- [ ] active control-plane documents updated to reflect the current session model
- [ ] deprecated coordination patterns clearly demoted or archived
- [ ] Memory update performed with new structure

---

## 🔴 PHASE 4: Close Content Creation Loop

**Goal:** Complete, documented workflow from source material to production content.

### 4.1 Content Pipeline

```
SOURCE PDF → EXTRACTION → STAGING → ASSEMBLY → FINAL → COMMIT
     ↓            ↓           ↓          ↓         ↓        ↓
  Resources/   Resources/  Development/  Using    NETA-X/   Git
  Source-PDFs/ Extractions/ NETA-X/     template  [folder]/ push
                           Staging/
```

### 4.2 Stage-to-Assembly Workflow

**Staging Phase (Markdown):**
- Extract content from source materials
- Apply KSA tags per TAGGING-SCHEMA.md
- Name files: `##-TOPIC-STAGED.md`
- Location: `Development/NETA-X/Staging/`

**Assembly Phase (HTML):**
- Load staged content into master template
- Add analytics integration
- Add timer functionality (practice tests)
- Validate against spec checklist
- Name files per NAMING-CONVENTIONS.md
- Location: `NETA-X/[appropriate-folder]/`

### 4.3 Quality Gates

Before committing any content:
- [ ] Follows appropriate Build-Spec
- [ ] KSA tags applied (if study guide/test)
- [ ] NETA ATS references included
- [ ] Tested in browser (HTML files)
- [ ] Line count meets minimum (Practice Tests: 1000+, Study Guides: 500+)

### Phase 4 Deliverables
- [ ] Process-Guides/CONTENT-CREATION-WORKFLOW.md created
- [ ] Staging folder structure standardized
- [ ] Master HTML template documented
- [ ] Quality validation checklist created
- [ ] First content item created using full pipeline (proof of concept)

---

## 📋 EXECUTION PRIORITY

### Immediate (This Session)
1. Create Build-Specs/PRACTICE-TEST-SPEC.md (consolidate existing)
2. Create Process-Guides/SESSION-PROTOCOL.md (adapt from RESA)
3. Update the active governance/resume stack to reference the roadmap where appropriate

### Short-Term (Next 2-3 Sessions)
1. Complete Phase 1 documentation consolidation
2. Create remaining Build-Specs
3. Archive superseded documents

### Medium-Term (Week+)
1. Implement Phase 3 session protocol across all work
2. Create Phase 4 content pipeline documentation
3. Run proof-of-concept through full pipeline

---

## 🔗 KEY FILE LOCATIONS

| Document | Location | Purpose |
|----------|----------|---------|
| This Roadmap | Build-Specs/INFRASTRUCTURE-ROADMAP.md | Master execution plan |
| Current State | Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md + Development/Control-Plane/EXECUTION-TASKS-CURRENT.md | Active session continuity |
| Decisions Log | GOVERNANCE-FRAMEWORK.md + current control-plane docs | Decision history / active governance context |
| Master Standards | MASTER-STANDARDS.md | Governing document |
| Instance Coordination | Development task docs + resume/tracker model | Cross-role handoffs |

---

## March 2026 Priority Delta

For current workspace evolution, the highest-priority infrastructure work is now:

1. converge remaining active specs/templates away from obsolete `.claude` and `CLAUDE-COMMUNICATION.md` instructions
2. continue namespace cleanup inside `Development/`, especially for TCC planning and integration docs
3. reduce active dependence on raw absolute local paths where repo-name plus owned path is sufficient
4. preserve this roadmap as historical architecture context rather than using it as the live operating manual

---

## 📝 NOTES

- **Principle:** "Lasting value over immediate needs" - build infrastructure that scales
- **Philosophy:** Teach concepts, not memorization - this applies to documentation too
- **Future:** All infrastructure prepares for RESA Power Platform migration
- **Quality:** 60-65% time savings demonstrated with staging workflow - invest in process

---

*Last Updated: March 21, 2026 (historical foundation with current-state addendum)*
*Version: 1.1*
