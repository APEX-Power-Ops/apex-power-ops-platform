# NETA ETT Study Material - Master Standards Guide
## The Single Source of Truth
### Version 3.6 | Updated: March 25, 2026

---

## 📋 DOCUMENT PURPOSE

This document defines **all** standards, conventions, and protocols for the NETA ETT Study Material project. All development work, file organization, naming conventions, and cross-role collaboration follows these standards.

**If it's not in this document (or a referenced sub-guide), it's not standard.**

### Governance
- **GOVERNANCE-FRAMEWORK.md** - Multi-AI workspace coordination, authority hierarchy, quality enforcement
- **Development/Control-Plane/INSTANCE-QUICK-REFERENCE.md** - Quick reference for executing instances
- **Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md** - Workspace-hub resume and governance-resume entry point
- **Development/Control-Plane/EXECUTION-TASKS-CURRENT.md** - Active execution tracker
- **Development/Control-Plane/SESSION-LANE-PROTOCOL.md** - Active lane declaration, switching, and resume-designation rules
- **Development/Control-Plane/RESUME-ETT-CONTENT-CURRENT.md** - Current resume for ETT content and standards work
- **Development/Control-Plane/ETT-GUIDE-LIFECYCLE-OPERATING-MODEL-2026-03-26.md** - Active operating model for ETT guide source gating, activation, authoring, audit/review, load, and reload decisions
- **Development/Control-Plane/ETT-V2.4-RELOAD-DECISION-MATRIX-2026-03-26.md** - Active decision surface for which content-complete v2.4 guides should actually be reloaded
- **Development/Control-Plane/ETT-REMAINING-V2.3-GUIDE-INVENTORY-AND-ACTION-MATRIX.md** - Active bounded inventory of the remaining legacy v2.3 estate and its retain / park / carryforward recommendations
- **Development/Control-Plane/RESUME-TCC-RUNTIME-CURRENT.md** - Current resume for TCC runtime and backend work
- **Development/Control-Plane/RESUME-WORKSPACE-GOVERNANCE-CURRENT.md** - Current resume for workspace-governance and protocol work
- **Development/Architecture/PROJECT-INTENT-FRAMEWORK-METHODOLOGY-GOALS-BASELINE.md** - Project baseline for intent, framework, methodology, and goals
- **Development/Architecture/REPOSITORY-REGISTRY.md** - Cross-repo ownership and workspace boundary contract
- **Development/Architecture/UNIFIED-PLATFORM-ARCHITECTURE.md** - Shared ETT + TCC platform model
- **Development/Architecture/TCC-MASTER-SCHEMA-AUTHORITY.md** - Stable TCC schema authority
- **Development/Architecture/TCC-DLL-ARCHITECTURE-AUTHORITY.md** - Stable TCC runtime and DLL authority
- **Development/Architecture/ACCEPTANCE-CRITERIA-MATRIX-METHODOLOGY.md** - Standard for bounded acceptance matrices used by delegators, executors, and auditors

For any TCC backend, migration, API, or architecture task, these two TCC authority documents are the required paired validation surface. Neither may be treated as optional when the task touches TCC family selection, routing, schema meaning, or runtime behavior.

### Related Documentation
- **Process Guides:** See `Process-Guides/` for workflow references and legacy process material after session startup
  - `CONTENT-CREATION-WORKFLOW.md` - Content development process
  - `RESOURCE-EXTRACTION-GUIDE.md` - Authoritative extraction and disk-first resource processing standard
  - `QUALITY-VALIDATION-CHECKLIST.md` - Quality standards and review
  - `SESSION-PROTOCOL.md` - Historical reference only; deprecated as an active coordination entry point
- **Build Specifications:** See `Build-Specs/` for technical specifications
  - `PRACTICE-TEST-SPEC.md` - Practice test HTML structure and features
  - `STAGING-WORKFLOW-SPEC.md` - Canonical workflow for staged content lifecycle and closeout
  - `FLASHCARD-SPEC.md` - Canonical flashcard structure, tagging, and export contract
  - `REFERENCE-SHEET-SPEC.md` - Canonical quick-lookup reference-sheet format and publication contract
  - `INFRASTRUCTURE-ROADMAP.md` - Project architecture and roadmap
- **Resource Governance Surfaces:** Use these together for resource control, coverage, and Supabase reconciliation
  - `Development/RESOURCE-GOVERNANCE-AUDIT.md` - End-to-end resource lifecycle policy, audit findings, and corrective controls
  - `Development/RESOURCE-COVERAGE-REPORT.md` - Extraction coverage and remaining source-library gaps
  - `Development/RESOURCE-PATH-STATUS.md` - Current Supabase `study_content.source_path` audit snapshot
  - `Development/RESOURCE-PATH-REMEDIATION.md` - Current disposition of remaining path mismatches and retired historical sources
- **Quality Audit Guides:** See `Development/Shared/` for the currently maintained audit guides until they are migrated into a dedicated namespace
  - `AUDIT-GUIDE-PRACTICE-TESTS.md` - Practice test quality assessment
  - `AUDIT-GUIDE-STUDY-GUIDES.md` - Study guide quality assessment
  - `AUDIT-GUIDE-REFERENCE-SHEETS.md` - Reference sheet quality assessment
  - *(Quality framework now integrated into this document - see "Six Quality Dimensions" below)*

### Document Status Model

All non-code documents in the active workspace should be treated as one of four types:

| Status | Meaning | Rule |
|--------|---------|------|
| **Active** | Defines or directs current work | Can govern current execution |
| **Reference** | Supports active work but does not override active governance | Use after session startup and only within the current governance model |
| **Historical** | Kept for archaeology, provenance, or transition context | Must not be treated as current operating contract |
| **Archived** | Superseded and no longer part of active paths | Should not appear in startup or execution surfaces |

If a document can be mistaken for current operational authority, it must be either re-labeled, moved, or archived.

### TCC Source-Of-Truth Rule

For all TCC-related implementation and design work across both repositories, the governed source of truth is the paired authority stack in:

1. `Development/Architecture/TCC-MASTER-SCHEMA-AUTHORITY.md`
2. `Development/Architecture/TCC-DLL-ARCHITECTURE-AUTHORITY.md`

Supporting migration docs, trace packets, staging docs, backend code, and implementation notes may elaborate or prove details, but they do not override the authority stack.

If a supporting artifact reveals a better interpretation, update the authority stack first. Do not let backend code or a one-off spec become the project's de facto architecture source.

### Acceptance Matrix Rule

When a task, subsystem, or family needs bounded closeout criteria, use an acceptance matrix rather than broad completion labels.

Acceptance matrices must:

1. be bounded by the governing authority documents for that surface
2. be defined by the task delegator
3. be used by the task executor as the active acceptance target
4. be used by reviewers and auditors as the classification surface

Do not let a matrix become a replacement source of truth. It is a bounded audit and classification tool only.

---

## 🏗️ WORKSPACE AND REPOSITORY STRUCTURE

### Ideal Daily Workspace Layout

```text
C:\Users\jjswe\
│
├── NETA ETT Study Material\              ← Content + governance repository
└── Projects\
  └── tcc_v5_backend\                   ← Runtime application repository
```

This is the accepted daily operating layout: one checked-in multi-root workspace, two repositories, and one explicit shared platform seam.

### Daily Workspace Rule

When both repositories are available, open `NETA ETT Study Material.code-workspace` as the standard daily entry artifact rather than opening the content repository alone.

This workspace model is the active baseline, not a transition experiment.

### Session Continuity Rule

Session continuity is split into:

1. one workspace hub resume in `Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md`
2. one current resume per active lane in `Development/Control-Plane/`
3. historical or detailed session summaries outside the control-plane as reference-only surfaces

Do not let one detailed topic-specific resume become the de facto resume for the entire consolidated workspace.

### Integration vs. Segregation Model

| Concern | Home | Rule |
|---------|------|------|
| Governance, standards, audits, architecture | `NETA ETT Study Material` | Authoritative documentation lives here |
| ETT content, resources, build specs, archive | `NETA ETT Study Material` | Keep content-system ownership explicit |
| FastAPI code, routes, services, migrations, tests | `tcc_v5_backend` | Runtime ownership stays with the application repo |
| Shared persistence and product seam | Supabase | Shared contract, not shared source folders |
| Daily editor workflow | Multi-root workspace | Unified workspace does not imply merged repositories |

### Primary Repository Structure

```text
C:\APEX Platform\source-domains\neta-ett-study-material\
│
├── README.md                              ← Human and agent entry point
├── GOVERNANCE-FRAMEWORK.md                ← Authority hierarchy, routing, enforcement
├── MASTER-STANDARDS.md                    ← THIS DOCUMENT
├── NETA ETT Study Material.code-workspace ← Checked-in multi-root workspace
│
├── Build-Specs/                           ← Authoritative implementation specs
├── Process-Guides/                        ← Workflow references and historical process docs
├── Resources/                             ← Shared reference materials and extracted assets
├── Archive/                               ← Historical and superseded material
│
├── Development/                           ← Active control plane for this repository
│   ├── Architecture/                      ← Repo boundaries, workspace design, platform contracts
│   ├── Audits/                            ← Workspace and pipeline audit records
│   ├── Control-Plane/                     ← Live resume, current tasks, operator quick reference
│   ├── Platform/                          ← TCC integration and shared-platform planning
│   ├── Scripts/                           ← Active operational tooling
│   ├── Pipeline/                          ← Pipeline framework and active pipeline docs/tools
│   ├── staging/                           ← Topic-level working directories
│   ├── Templates/                         ← Active templates
│   ├── NETA-Data/                         ← Generated data artifacts used by active workflows
│   └── [Transitional active docs/assets]  ← Remaining root-density to be reduced over time
│
├── NETA-2/                                ← Student content ONLY (Level II)
├── NETA-3/                                ← Student content ONLY (Level III)
├── NETA-4/                                ← Student content ONLY (Level IV)
│
└── [Additional root files by exception only]
```

---

## 📛 NAMING CONVENTIONS

### Folder Names
| Convention | Example | Rule |
|------------|---------|------|
| Project folders | `NETA-2`, `NETA-3` | Hyphenated, capitalized |
| Content folders | `01-Study-Plan`, `02-Reference-Sheets` | Number prefix, hyphenated |
| Development folders | `Test-Staging`, `Question-Bank` | Pascal-case with hyphens |

### File Names
| Type | Convention | Example |
|------|------------|---------|
| Study Guides | `##-Topic-Name-Guide.html` | `01-Ohms-Law-Complete-Guide.html` |
| Practice Tests | `##-Topic-Name-Practice.html` | `01-Basic-Electrical-Theory-Practice.html` |
| Reference Sheets | `Topic-Name-Reference.html` | `Electrical-Formulas-Reference.html` |
| Flashcards | `NETA-Level-#-Flashcards.html` | `NETA-Level-2-Flashcards.html` |
| Mock Exams | `Mock-Exam-#.html` | `Mock-Exam-1.html` |
| Development docs | `UPPERCASE-WITH-HYPHENS.md` | `GOVERNANCE-SESSION-RESUME.md` |
| Staging files | `##-TOPIC-NAME-STAGED.md` | `22-CABLE-TESTING-STAGED.md` |

### Prohibited in File/Folder Names
- Spaces (use hyphens)
- Special characters except hyphens
- Lowercase-only names for development docs
- Ambiguous abbreviations

---

## 📁 CONTENT FOLDER STANDARDS

### NETA-X/ (Student Content Folders)

**Structure - Identical across all levels:**
```
NETA-X/
├── 00-Quick-Start.html              ← Entry point
├── 01-Study-Plan/
│   └── Study-Schedule.html
├── 02-Reference-Sheets/
│   └── [Topic]-Reference.html
├── 03-Study-Guides/
│   ├── 00-Study-Guide-Index.html
│   └── ##-[Topic]-Guide.html
├── 04-Practice-Tests/
│   ├── 00-Practice-Test-Dashboard.html
│   └── ##-[Topic]-Practice.html
├── 05-Flashcards/
│   └── NETA-Level-X-Flashcards.html
├── 06-Mock-Exams/
│   └── Mock-Exam-#.html
├── 07-Progress-Tracker/
│   └── Daily-Checklist.html
└── README.html
```

**ALLOWED in NETA-X/ folders:**
- Final HTML content files
- Index/dashboard HTML files
- README.html
- Navigation assets (if self-contained)

**PROHIBITED in NETA-X/ folders:**
- Markdown (.md) files
- PDF files
- Scripts (.py, .js, .gs)
- Working/staging files
- Archive folders
- Development documentation
- .venv, .vscode, node_modules
- Any non-deliverable content

---

## 📚 RESOURCES FOLDER STANDARDS

### Resource Governance Model

`Resources/` is a governed content platform, not a miscellaneous storage area. Every source, extraction, catalog surface, and Supabase path reference must fit the same lifecycle:

1. Intake to `Resources/Source-PDFs/_Unsorted/`
2. Classification into a canonical source category
3. Manifest rebuild (`RESOURCE-MANIFEST-RAW.json` then `RESOURCE-MANIFEST.json`)
4. Curated extraction to `Resources/Extractions/`
5. Coverage/crosswalk review
6. Supabase load using canonical repo-relative source paths
7. Periodic drift audit and remediation

The authoritative detailed audit for this lifecycle is `Development/RESOURCE-GOVERNANCE-AUDIT.md`.

### Resources/Source-PDFs/
**Contains:** Canonical source library of original reference documents used by extraction and study-content workflows.

```text
Source-PDFs/
├── ASTM/
├── CIGRE/
├── Equipment-Manuals/
├── Exam-Resources/
├── IEC/
├── IEEE/
├── Industry-Guides/
├── Industry-NETA/
├── Instrument-Transformers/
├── NEMA/
├── NETA/
├── NFPA-OSHA/
├── PEARL/
├── Textbooks/
├── UL/
├── VFD/
└── _Unsorted/
```

**Rules:**
- `Source-PDFs/` is the canonical source-of-record for active PDFs. Do not use legacy aliases such as `IEEE-Standards/`, `IEC-Standards/`, `UL-Standards/`, `NETA-Standards/`, `Manufacturer-Docs/`, or `Testing Resources/` for new work.
- Source files must live in exactly one canonical category. Do not duplicate the same active source across categories.
- `_Unsorted/` is an intake queue only. Files remain there only until named, categorized, and cataloged.
- Active categories should hold source artifacts, not extracted markdown, helper text dumps, or temporary admin notes.
- Historical materials from retired trees may be archived for provenance, but they are not part of the active source-library contract until explicitly reclassified into a canonical category.

**Preferred source PDF naming:**
- Standards: `[ORG]-[STANDARD]-[YEAR]-[Short-Title].pdf`
- Manuals/books/guides: `[Publisher-or-Author]-[Short-Title].pdf`
- Use hyphens, preserve meaningful identifiers, and avoid vague names such as `scan1.pdf` or `standard.pdf`.

### Resource Manifests
**Contains:** Inventory and enriched linkage surfaces for the entire active resource platform.

- `Resources/RESOURCE-MANIFEST-RAW.json` - tree walk inventory generated from the live `Resources/` structure
- `Resources/RESOURCE-MANIFEST.json` - enriched manifest joining inventory to extraction and Supabase coverage context

**Rules:**
- Manifest files are the primary machine-readable tracking surface for resource inventory.
- Structural changes to `Resources/` should be followed by manifest regeneration.
- Coverage or Supabase reconciliation work should reference the manifest instead of ad hoc folder browsing.

### Resources/Catalog/
**Contains:** Human-readable indexes, crosswalks, and legacy/reference catalog surfaces that still support research and authoring.

- `KSA-MASTER-INDEX.md` - KSA reference index
- `SOURCE-INDEX-[Name].md` - per-source content indexes where maintained
- `TOPIC-CROSSWALK.md` - topic and source relationship mapping
- `TAGGING-SCHEMA.md` - taxonomy documentation

**Rule:** `Catalog/` is a supporting reference surface. It does not replace the manifests or Supabase as the canonical tracking system.

### Resources/Extractions/
**Contains:** Curated markdown derived from governed source materials.

```text
Extractions/
├── [canonical categories]
├── [governed legacy categories retained for continuity]
└── EXTRACTION-CATALOG.md
```

**Rules:**
- All new extraction work follows `Process-Guides/RESOURCE-EXTRACTION-GUIDE.md`.
- Extractions are disk-first artifacts. Human review comes before any Supabase load.
- New extraction placement should follow the canonical source category where practical. Existing governed legacy folders may persist temporarily for continuity, but they are exceptions, not the default pattern.
- Extraction filenames should retain the content ID at the front when assigned: `EXT-[ORG]-[NNN]-[descriptive-slug].md`.
- Raw OCR dumps, page-by-page text dumps, and uncurated scratch output are not valid extraction deliverables.

### Supabase Resource Metadata Rule

For resource-backed records in Supabase:

- `study_content.source_path` must use the canonical repo-relative path under `Resources/`.
- Do not write legacy path aliases to Supabase once a canonical path exists.
- If a referenced legacy source no longer exists in the governed active library and no verified replacement exists, mark it as a documented historical-source-retired case rather than guessing a remap.
- Any batch correction of `source_path` values must produce an updated status snapshot and remediation record.

### Retired Legacy Trees

`Testing Resources/` is a retired historical source family, not an active top-level resource tree. Its previous contents were triaged into one of four outcomes:

- promoted into canonical `Source-PDFs/` categories
- retained only as historical/archive material
- discarded as web-help/installers/noise
- left documented as historical-source-retired when used only for provenance

Do not recreate `Testing Resources/` or other legacy top-level aliases as active working locations.

### Resources/Templates/
**Contains:** Reusable content creation templates
- Practice test HTML template
- Study guide HTML template
- Reference sheet HTML template
- Flashcard HTML template

---

## 🔧 DEVELOPMENT FOLDER STANDARDS

### Development/ (Active Working Directory)
```text
Development/
├── Architecture/                ← Workspace design, repo registry, platform architecture
├── Audits/                      ← Active audit records and verification passes
├── Control-Plane/               ← Governance resume, execution tracker, quick reference
├── Platform/                    ← Shared ETT + TCC planning and acceptance framing
├── Scripts/                     ← Active operational tooling, organized by function
├── Pipeline/                    ← New Material Pipeline framework and supporting docs
├── staging/                     ← Topic staging directories (see STAGING-PROCESS.md)
│   ├── STAGING-PROCESS.md       ← Authoritative workspace process doc
│   └── {topic-slug}/            ← Per-topic working area
│       ├── STATUS.md            ← Required: lifecycle state snapshot
│       ├── SG-{DOMAIN}-{slug}.md ← Assembled guide (source of truth)
│       └── [intermediates]      ← Scaffolds, fills, scripts, data packets
├── Templates/                   ← Active development and content templates
├── NETA-Data/                   ← Pipeline outputs (master JSON, compact, indexes)
├── Flashcards/                  ← Flashcard HTML apps
├── MockExams/                   ← Mock exam HTML files
├── EquipmentManuals/            ← Equipment manual inventory
└── [Transitional docs/assets]   ← Existing root-density being reduced in controlled passes
```

**Primary active namespaces:** Architecture/, Audits/, Control-Plane/, Platform/, Scripts/, Pipeline/, staging/, Templates/, NETA-Data/
**Supporting active directories:** Flashcards/, MockExams/, EquipmentManuals/
**Transition rule:** new structural work should target the namespaced layout above rather than adding new root-density under `Development/`.

---

## 🖼️ ASSET STORAGE STANDARDS

### Images and Diagrams
**Location:** `Development/NETA-X/Assets/`
```
Development/NETA-X/Assets/
├── Images/           ← Screenshots, photos, diagrams
├── Diagrams/         ← Technical drawings, schematics
└── Icons/            ← UI icons, badges
```

**Naming:** `[Topic]-[Description]-[Size].png`
- Example: `transformer-winding-diagram-800w.png`

**For Production:** Images embedded in final HTML should use base64 encoding or relative paths within the NETA-X folder structure.

### CSS/Styling
**Standard:** All HTML files are self-contained with inline CSS.
- No external stylesheet dependencies
- Ensures portability and offline use
- Consistent styling defined in content templates

### JavaScript
**Standard:** Minimal, inline JavaScript only.
- Interactive elements (timers, toggles) use inline scripts
- No external JS library dependencies
- All functionality works offline

---

## 📊 FILE LIFECYCLE STATES

### State Definitions (Study Guide Pipeline)

The current pipeline uses Supabase as the deployed platform. Git is authoritative.

| State | Location | Description |
|-------|----------|-------------|
| **Planned** | Backlog only | Topic identified, no files yet |
| **Scaffolded** | `Development/staging/[topic]/` | Folder + STATUS.md + scaffold file created |
| **In Progress** | `Development/staging/[topic]/` | Active authoring — STATUS.md `active_work` set |
| **Assembled** | `Development/staging/[topic]/SG-*.md` | Guide assembled from components, not yet loaded |
| **IMG Pass** | Same file, updated | `{{IMG:}}` placeholders inserted, format version v2.3 confirmed |
| **Staged** | Same file | IMG pass done, pre-flight checks passed, ready for VS Code load |
| **Loaded** | Supabase `study_content` | VS Code executed INSERT/UPDATE, UUID assigned, KSA links discovered |
| **Published** | Supabase `status: published` | VERIFY flags resolved, quality review passed |
| **Archived** | `Development/archive/staging-superseded/` | Superseded or retired |

### State Transitions
```
Planned → Scaffolded → In Progress → Assembled → IMG Pass → Staged → Loaded → Published
                                                                              ↓
                                                                          Archived (if retired)
```

### Status Tracking
- Each topic folder in `Development/staging/[topic]/` contains a `STATUS.md`
- `STATUS.md active_work` field signals whether authoring is in progress
- Loaded state: UUID and KSA link counts recorded in STATUS.md and GUIDE-REGISTRY.md
- Platform state tracked in `Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md`

---

## 🔗 CROSS-LINKING POLICY

### Shared Topics Across Levels
Some topics appear in multiple certification levels (e.g., Ohm's Law, Safety).

**Policy:**
1. Each level has its OWN content file (no cross-folder linking)
2. Level II content = foundational coverage
3. Level III content = Level II + advanced depth
4. Level IV content = Level III + system-level analysis

**Content Reuse:**
- Use Resources/Extractions/ as the single source
- Each level's content is tailored to that level's depth
- Do NOT copy-paste between levels - adapt and enhance

### Internal HTML Links
- Use relative paths within NETA-X folder
- Example: `href="../02-Reference-Sheets/Electrical-Formulas-Reference.html"`
- Never use absolute paths (breaks portability)
- Never link to Development/ or Archive/ folders

### External References
- Link to Resources/Catalog/ documents for source citations
- Include page numbers for PDF references
- Format: `[ATS-2025, Section 7.3, p.42]`

---

## 💾 BACKUP AND VERSION CONTROL

### File Backup Protocol
**Primary:** Active content in NETA-2/, NETA-3/, NETA-4/; pipeline work in Development/
**Archive:** Superseded versions in Archive/

### Version Tracking
- Major changes: Update file, document in relevant task doc
- Breaking changes: Archive old version with date suffix
- Example: `01-Ohms-Law-Guide-2025-12-15.html` → Archive/

### Recovery Procedure
If content is lost or corrupted:
1. Check Archive/ for previous versions
2. Re-enter through `Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md`, `Development/Control-Plane/SESSION-LANE-PROTOCOL.md`, and the correct lane resume before treating any older resume surface as current
3. For ETT content recovery, confirm current state in `Development/Control-Plane/RESUME-ETT-CONTENT-CURRENT.md`, `Development/GUIDE-REGISTRY.md`, `Development/RESOURCE-COVERAGE-REPORT.md`, and `Resources/RESOURCE-MANIFEST.json`
4. Rebuild from Resources/Extractions/ and staging files

### What to Archive
- Original markdown files (pre-HTML conversion)
- Superseded HTML versions
- Deprecated planning documents
- Failed experiments (with notes on why they failed)

---

## 🤝 CROSS-INSTANCE COLLABORATION PROTOCOL

### Communication Hub (v2 — Task Doc Model)
Cross-instance work uses **task documents** created by the Governance Lead and executed by the Execution Lead:
- Governance Lead creates task documents in `Development/` (e.g., `EXECUTION-TASK-[date].md`)
- Execution Lead reads the task document, executes, and commits
- Current active tasks: `Development/Control-Plane/EXECUTION-TASKS-CURRENT.md`

Session state is maintained in:
- `Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md` — Governance session hub
- `Development/Control-Plane/SESSION-LANE-PROTOCOL.md` — Lane declaration and resume-routing rules
- `Development/Control-Plane/RESUME-ETT-CONTENT-CURRENT.md` — Current ETT content and standards restart surface
- `Development/GUIDE-REGISTRY.md` — Live loaded-guide and parked-queue state for ETT content work
- `Development/RESOURCE-COVERAGE-REPORT.md` and `Resources/RESOURCE-MANIFEST.json` — Durable resource-platform restart surfaces for ETT content work

### Instance Responsibilities

**Governance Lead:**
- Strategy, planning, and specification
- Large document generation and content creation
- PDF content analysis and extraction
- Task document authorship
- Cross-reference synthesis across large context

**Execution Lead:**
- File operations, moves, renames
- Script execution and debugging
- Git operations (branch, commit, push)
- Surgical code edits
- Multi-file coordination and data pipeline execution

**Batch Executor / Specialist Support:**
- Repetitive extraction or transformation work
- Tool- or domain-specific assistance when needed
- High-throughput structured tasks under a defined contract

### Handoff Protocol (Task Doc Model)
1. Governance Lead creates `EXECUTION-TASK-[date].md` with clear phase/step breakdown
2. Execution Lead reads task doc completely before starting
3. Execution Lead executes phases in order, committing after each
4. Execution Lead updates `EXECUTION-TASKS-CURRENT.md` on completion
5. Governance Lead reviews committed results in the next session

### When to Use Which Instance
| Task | Instance |
|------|----------|
| Generate new content with heavy judgment | Governance Lead |
| Edit/fix existing files | Execution Lead |
| Run Python scripts | Execution Lead |
| Git operations | Execution Lead |
| Analyze PDFs and extract at scale | Batch Executor or Specialist Support |
| Plan architecture and write specs | Governance Lead |
| Execute multi-file reorganization | Execution Lead |

---

## 📄 DOCUMENT HIERARCHY

```
MASTER-STANDARDS.md (This Document)
│
├── Content Framework:
│   ├── Development/CONTENT-FORMAT-SPEC-v2.3.md
│   ├── Development/TEMPLATE-study-guide.md
│   └── Development/MIGRATION-PLAYBOOK.md
│
├── Build Specifications:
│   ├── Build-Specs/PRACTICE-TEST-SPEC.md
│   └── Build-Specs/STUDY-GUIDE-SPEC.md
│
├── Pipeline Documentation:
│   ├── Development/Pipeline/README.md
│   └── Development/NETA-Data/README.md
│
└── Project Coordination:
    ├── Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md
    ├── Development/Control-Plane/INSTANCE-QUICK-REFERENCE.md
    ├── Development/Control-Plane/EXECUTION-TASKS-CURRENT.md
    ├── Development/Control-Plane/SESSION-LANE-PROTOCOL.md
    ├── Development/Control-Plane/RESUME-ETT-CONTENT-CURRENT.md
    └── Development/GUIDE-REGISTRY.md
```

**Rule:** If a document isn't referenced here or in a task doc, it should be in Archive/ or deleted.

---

## 🏷️ CONTENT TAGGING SCHEMA

### Level Tags
| Tag | Meaning |
|-----|---------|
| `Level-II` | NETA Level II content |
| `Level-III` | NETA Level III content |
| `Level-IV` | NETA Level IV content |
| `Foundation` | Applies to all levels |

### Content Type Tags
| Tag | Meaning |
|-----|---------|
| `Formula` | Mathematical formulas, equations |
| `Procedure` | Step-by-step testing procedures |
| `Acceptance-Criteria` | Pass/fail values from standards |
| `Safety` | NFPA 70E, LOTO, arc flash |
| `Theory` | Conceptual explanations |
| `Equipment-Specific` | Applies to specific equipment type |

### Domain Tags
| Tag | Meaning |
|-----|---------|
| `Electrical-Theory` | Ohm's law, power, circuits |
| `Safety-NFPA-70E` | Arc flash, boundaries, PPE |
| `Testing-Fundamentals` | Test procedures, equipment |
| `Systems-Commissioning` | System-level testing |
| `Protective-Relays` | Relay testing, coordination |

### Source Type Tags
| Tag | Meaning |
|-----|---------|
| `Standard` | NETA ATS/MTS/ETT, IEEE (authoritative) |
| `Textbook` | Paul Gill, technical references |
| `Practice` | Exam-focused materials |

---

## ✅ CONTENT QUALITY STANDARDS (v2.0)

**Philosophy:** Line counts are reference indicators, not quality metrics. A well-structured 800-line document with deep, authoritative content outperforms a 1,500-line document with shallow coverage.

**Our materials serve two purposes:**
1. **Certification Preparation** - Help technicians pass NETA ETT exams
2. **Ongoing Professional Reference** - Resources technicians return to throughout their careers

**Every audit is an opportunity to identify enhancements that increase long-term value.**

### The Six Quality Dimensions

All content is evaluated across these dimensions:

| Dimension | Description |
|-----------|-------------|
| **Theoretical Foundation** | Does it explain the "why" behind the "what"? |
| **Practical Application** | Can a technician apply this in the field tomorrow? |
| **Authoritative Sources** | Paul Gill, IEEE, NETA ATS/MTS integration? |
| **Common Mistakes** | Real errors with real consequences? |
| **Why It Matters** | Connected to safety, cost, career impact? |
| **Progressive Depth** | Appropriate for the certification level? |

### Quality Tiers

| Tier | Description |
|------|-------------|
| **Gold Standard** | All 6 dimensions strong; comprehensive source integration |
| **Complete/High Quality** | 4-5 dimensions adequate; solid educational value |
| **Adequate** | Structure complete; content gaps exist |
| **Needs Enhancement** | Significant gaps in multiple dimensions |

### Primary Source Materials

| Source | Abbreviation | Citation Format |
|--------|--------------|-----------------|
| Paul Gill - *Electrical Power Equipment Maintenance and Testing* (4th Ed.) | EPEMT | `(Ref: Paul Gill EPEMT § 6.4.2)` |
| NETA ATS (Acceptance Testing Specifications) | ATS | `(Ref: NETA ATS Table 100.18)` |
| NETA MTS (Maintenance Testing Specifications) | MTS | `(Ref: NETA MTS § 7.3)` |
| IEEE Standards | IEEE [Number] | `(Ref: IEEE 400-2012 § 5.2)` |
| NFPA 70E | 70E | `(Ref: NFPA 70E-2024 Table 130.5(C))` |

### Detailed Audit Guidelines

Comprehensive audit procedures are maintained in separate guides:

| Document | Location | Purpose |
|----------|----------|---------|
| **Practice Test Audit Guide** | `Development/Shared/AUDIT-GUIDE-PRACTICE-TESTS.md` | Question quality, Foundation Reviews, source integration |
| **Study Guide Audit Guide** | `Development/Shared/AUDIT-GUIDE-STUDY-GUIDES.md` | Content depth, visual aids, safety integration |
| **Reference Sheet Audit Guide** | `Development/Shared/AUDIT-GUIDE-REFERENCE-SHEETS.md` | Value accuracy, scannability, source verification |

### Safety Audit Requirements

**All content must reinforce safe work practices.** Each audit guide includes specific safety checklists covering:
- NFPA 70E references and compliance
- PPE requirements
- Arc flash/shock hazard awareness
- LOTO/ESWC procedures
- Test equipment safety (CAT ratings)
- Hazard warnings and callouts

### Structural Baselines (Reference Only)

These structural elements are necessary but not sufficient for quality:

**Practice Tests:**
- Foundation Reviews (2-3) with interactive toggles
- Learning Path Selector (Guided/Direct modes)
- 20-24 questions with difficulty progression
- Timer, analytics, results panel

**Study Guides:**
- Level badges (II/III/IV indicators)
- Visual aids (diagrams, charts, decision trees)
- Common mistakes and field tips sections
- Self-check questions

**Reference Sheets:**
- Print-friendly format
- Source citations for all values
- Safety warnings where applicable

---

## 🔄 WORKFLOW STANDARDS

### New Content Creation (New Material Pipeline)
1. Generate data packet via `build_topic_packet.py` (Phase 0)
2. Generate scaffold via `build_guide_scaffold.py` (Phase 1)
3. Populate content section-by-section following CONTENT-FORMAT-SPEC-v2.3.md (Phase 2)
4. Validate via `validate_guide.py` (Phase 3)
5. Human review for technical accuracy (Phase 4)
6. Load to Supabase when approved

### Content Enhancement
1. Read current file, assess against 6 Quality Dimensions
2. Check GENUINE-CONTENT-GAPS.md for coverage status
3. Enhance content following MIGRATION-PLAYBOOK.md
4. Update file in place
5. Update EXECUTION-TASKS-CURRENT.md

### Resource Extraction
1. Read source PDF from Resources/Source-PDFs/
2. Create extraction doc in Resources/Extractions/[Source]/
3. Update Resources/Catalog/SOURCE-INDEX-[Source].md
4. Update Resources/Catalog/TOPIC-CROSSWALK.md

### Extraction Quality Standards

All extractions stored in `Resources/Extractions/` must meet the curated format
standard defined in `Process-Guides/RESOURCE-EXTRACTION-GUIDE.md` (V2.0+).

#### Extraction Lifecycle States

| State | Definition | Location |
|---|---|---|
| **planned** | Source identified, not yet extracted | Noted in task doc or config JSON |
| **extracted** | Raw text pulled from source | Disk only — NOT loaded to Supabase |
| **curated** | Organized, structured, readable per format standard | Disk only — ready for review |
| **loaded** | Inserted into Supabase `study_content` table | Supabase + disk |
| **verified** | KSA links discovered, quality confirmed | Supabase + disk |

#### Quality Gate

Extractions MUST pass human review before Supabase load. The review verifies:
- Curated format (not raw dump)
- Correct metadata header (content_id, neta_section, quality_tier, domain)
- Organized body (chapter/section headings, clean tables, [p.XX] references)
- No OCR artifacts or page-marker dumps
- Calcium Andite Rule compliance (no invented claims)

#### Format Authority

The authoritative extraction format standard is:
`Process-Guides/RESOURCE-EXTRACTION-GUIDE.md` (V2.0+)

Exemplar extractions demonstrating correct format:
- `EXT-IEEE-073` (IEEE C57.147) — Transformer DGA guide
- `EXT-IEEE-074` (IEEE 1184) — UPS systems guide
- `EXT-NEMA-005` (NEMA ICS 2 R2020) — Controllers and contactors

---

## 🚀 SUPABASE PLATFORM — CURRENT STATE

Supabase is the **current** deployed platform. Platform migration from static HTML is complete for the study guide workstream.

### Platform Architecture

| Layer | Role | Technology |
|---|---|---|
| **Git** | Authoritative source — `.md` files are master | GitHub (`jasonlswenson-sys/neta-ett-study-material`) |
| **Supabase** | Deployed platform — content served to web/mobile | PostgreSQL + Supabase Storage |
| **staging/** | Active authoring workspace — assembled guides + intermediates | Local filesystem |

### Key Tables

| Table | Purpose |
|---|---|
| `study_content` | Study guides, extractions, reference sheets (`resource_type` enum) |
| `ksa_content_links` | Many-to-many: KSA codes ↔ content rows |
| `study_questions` | Question bank (2,144 questions) |
| `ksas` | KSA master list (483 entries, 100% coverage) |
| `image_assets` | Future: IMG tag resolution (schema defined, not yet populated) |

### Content IDs (Current Format)

Study guides use the format `SG-[DOMAIN]-[TOPIC]`:

| Content Type | ID Format | Example |
|---|---|---|
| Study Guide | `SG-CT-[TOPIC]` or `SG-IT-[TOPIC]` | `SG-CT-MV-SWITCHGEAR` |
| Extraction | `EXT-[SOURCE]-[NNN]` | `EXT-IEEE-043` |
| Practice Test | `PT-[TOPIC]` | future |
| Reference Sheet | `RS-[TOPIC]` | future |

### resource_type Enum Values
`extraction` | `study_guide` | `practice_test` | `reference_sheet` | `document`

### Platform Status (as of Mar 15, 2026)
- **21 guides loaded** (`status: draft`)
- **791 study_content rows**
- **17,486 ksa_content_links**
- **483/483 KSAs covered (100%)**
- Services and API layers: scaffolded, empty shells — future development
- TCC v5 (2.4M row breaker catalog): local PostgreSQL, future Supabase migration

---

## � DATA INFRASTRUCTURE & BUILD PIPELINE
*Added v3.0 — February 2026*

### Architecture Overview
```
8 Source Files → rebuild_master.py → Master JSON
                                          ↓
                                   build_compact.py → Compact JSON
                                          ↓
                             build_reference_app.py → HTML App
                             build_searchable_index.py → Search Index
                             build_keyword_db.py → Keyword DB
```

### Source Files (in `Development/NETA-Data/`)
| File | Description |
|------|-------------|
| `NETA-ATS-2025-equipment-tests.json` | ATS-2025 equipment procedure data (60 sections) |
| `NETA-MTS-2023-equipment-tests.json` | MTS-2023 equipment procedure data (60 sections) |
| `NETA-ATS-2025-tables-extracted.json` | ATS table acceptance values |
| `NETA-MTS-2023-tables-extracted.json` | MTS table acceptance values |
| `NETA-Equipment-Category-Standard.md` | Authoritative 72-entry category catalog (remains in `Development/`) |

### Pipeline Scripts (in `Development/`)
| Script | Input | Output | Notes |
|--------|-------|--------|-------|
| `rebuild_master.py` | 8 source files | `NETA-Data/NETA-Master-Equipment-Table-Enhanced.json` | Canonical rebuild; always run first |
| `build_compact.py` | Master JSON | `NETA-Data/neta-equipment-compact.json` | Flattened for apps |
| `build_reference_app.py` | Compact JSON | `NETA-Equipment-Test-Reference.html` | Self-contained HTML app |
| `build_searchable_index.py` | Compact JSON | `NETA-Data/NETA-Searchable-Index.json` | KSA-tagged keyword index |
| `build_keyword_db.py` | Compact JSON | `NETA-Data/NETA-Keyword-Enhancement-DB.json` | Keyword enhancement |
| `_extract_tables.py` | Excel workbooks | Source JSONs | Run when source data changes |

### Pipeline Outputs (in `Development/NETA-Data/`)
| File | Size | Contents |
|------|------|----------|
| `NETA-Master-Equipment-Table-Enhanced.json` | ~1.7 MB | 72 entries, 27 categories, full detail |
| `neta-equipment-compact.json` | ~600 KB | 72 entries, flat arrays, app-optimized |
| `NETA-Searchable-Index.json` | ~1.1 MB | 66 keywords, KSA-tagged |
| `NETA-Keyword-Enhancement-DB.json` | ~17 KB | Keyword database |
| `discovery-scan-report.json` | ~1.0 MB | KSA discovery scan results |

*Note: `NETA-Equipment-Test-Reference.html` remains in `Development/` (rendered output, not data).*
*See `Development/NETA-Data/README.md` for full index and usage guide.*

### Re-Running the Pipeline
If source data changes (new extractions from PDFs), run scripts in order:
```powershell
cd "c:\APEX Platform\source-domains\neta-ett-study-material"
.venv\Scripts\python.exe Development\rebuild_master.py
.venv\Scripts\python.exe Development\build_compact.py
.venv\Scripts\python.exe Development\build_reference_app.py
.venv\Scripts\python.exe Development\build_searchable_index.py
.venv\Scripts\python.exe Development\build_keyword_db.py
```

---

## 🗂️ EQUIPMENT TAXONOMY STANDARD
*Added v3.0 — February 2026*

### Key Facts
- **72 sections** following ANSI/NETA ATS-2025 / MTS-2023 section numbers
- **27 equipment categories** as defined in `Development/NETA-Equipment-Category-Standard.md`
- Section numbers are the **primary key** — always use NETA standard sections (e.g., `7.3.1.1`)

### Section Numbering Conventions
| Convention | Example | Notes |
|------------|---------|-------|
| Standard section | `7.3.1` | Most entries |
| Split section | `7.6.1.1.1`, `7.6.1.1.2` | 7.6.1.1 split into LV/MV |
| MTS-only | `7.12.1.2`, `7.20.4` | Not in ATS |
| ATS-only | `7.23` | Not in MTS |
| Reserved | 7 sections | Future standards use |

### Key Decisions
| Decision | Rationale |
|----------|----------|
| 7.6.1.1 SPLIT into .1 (LV) and .2 (MV) | Different test values, combined in sources |
| Table 100.21 WITHDRAWN from catalog | Removed from ATS-2025 standard |
| 7 RESERVED sections retained | Placeholder for standards evolution |
| Category Standard is authoritative | Never add/remove categories without updating Standard |

---

## 🚫 DEPRECATED - DO NOT USE

The following patterns are deprecated and should not be created:

| Deprecated | Replacement |
|------------|-------------|
| Working/ folder in NETA-X/ | Development/NETA-X/ |
| Archive-Original-Files/ in NETA-X/ | Archive/NETA-X-Original/ |
| Loose .md files in NETA-X/ | Development/NETA-X/ |
| PDFs in NETA-X/ | Resources/Source-PDFs/ |
| Scripts/ in NETA-X/ | Development/NETA-X/Scripts/ |
| Multiple tracker documents | Task docs + EXECUTION-TASKS-CURRENT.md |
| Unnamed session docs | GOVERNANCE-SESSION-RESUME.md |

---

## 📊 VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 3.5 | Mar 21, 2026 | Added a document-status model (`Active`, `Reference`, `Historical`, `Archived`), made the checked-in multi-root workspace the standard daily entry artifact, updated content-framework references to `CONTENT-FORMAT-SPEC-v2.3.md`, and clarified active audit-guide location wording. |
| 1.0 | Dec 18, 2025 | Initial standards established |
| 1.1 | Dec 18, 2025 | Added: Asset Storage, File Lifecycle, Cross-linking Policy, Backup/Recovery (VS Code review feedback) |
| 1.2 | Dec 18, 2025 | Added: Platform Migration Readiness section (RESA Platform integration planning) |
| 2.0 | Dec 21, 2025 | **Major Update:** Replaced line-count quality metrics with Six Quality Dimensions framework; Added comprehensive audit guides for Practice Tests, Study Guides, and Reference Sheets; Integrated safety audit requirements; Added authoritative source citation standards |
| 2.1 | Dec 26, 2025 | Added governance framework reference; Deprecated VS-CODE-AI-INSTRUCTIONS.md in favor of GOVERNANCE-FRAMEWORK.md |
| 3.0 | Feb 2026 | **Major Update:** Added Data Infrastructure & Build Pipeline section (72-entry equipment taxonomy, 5 pipeline scripts, 8 source files); Added Equipment Taxonomy Standard; Updated folder structure to reflect Archive/ reorganization (7 subdirs, 60+ files archived); Updated Cross-Instance Protocol to task doc model (removed CLAUDE-COMMUNICATION.md pattern); Updated Resources/Extractions to include NotebookLM-Curated; Removed stale references to CLAUDE-COMMUNICATION.md per level |
| 3.1 | Mar 2026 | Updated Development folder standards to reflect post-cleanup state (Pipeline/, staging/, NETA-Data/ active; legacy NETA-X/ dirs mostly archived); Updated document hierarchy; Corrected cross-instance protocol references; Updated workflow standards to New Material Pipeline |
| 3.3 | Mar 21, 2026 | Added a workspace-level visual for the two-repository operating model, clarified integration versus segregation rules, and updated the master/development structure sections to reflect the current active `Development/` namespaces and checked-in multi-root workspace. |
| 3.4 | Mar 21, 2026 | Replaced model-specific collaboration nomenclature with role-based terms (`Governance Lead`, `Execution Lead`, `Batch Executor`, `Specialist Support`) so the workspace contract remains tolerant of different models, toolsets, and future handoff patterns. |
| 3.2 | Mar 15, 2026 | Added Extraction Quality Standards section (lifecycle states, quality gate, format authority). Updated extraction folder listing to reflect 28 current folders. Updated platform status counts (791 content, 17,486 links, 21 guides). |

---

## ✍️ APPROVAL

This document is approved and effective as of December 18, 2025.

All existing content will be migrated to comply with these standards.
All new content must follow these standards.

---

*End of Master Standards Guide*
