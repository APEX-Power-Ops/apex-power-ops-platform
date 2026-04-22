# Resource Extraction Guide
## Processing Source Materials for NETA ETT Content
### Version 2.1 | March 25, 2026

> **V2.0 is a complete rewrite.** V1.0 (December 2025) predated the Supabase pipeline,
> the curated extraction format, and the governance lessons from the Mar 15 CC incident.
> This version is the authoritative standard for all extraction work going forward.
> If you are following a task document that references extraction procedures,
> this document takes precedence over any conflicting guidance.

---

## 1. Purpose

This guide defines how to extract content from source documents (PDFs, standards,
reference books, manufacturer manuals) into structured, study-ready markdown files
that feed the NETA ETT content pipeline.

This guide is governed together with:

- `MASTER-STANDARDS.md`
- `Development/RESOURCE-GOVERNANCE-AUDIT.md`
- `Development/RESOURCE-PATH-STATUS.md`
- `Development/RESOURCE-PATH-REMEDIATION.md`

A good extraction is **curated, not dumped.** It transforms a raw PDF into organized,
searchable, traceable content that any instance can use to author study guides,
build practice tests, or populate reference sheets — without re-reading the source.

### What This Guide Covers

- **Curated extraction format** — the mandatory structure for all extraction files
- **Extraction process** — step-by-step from PDF to disk to Supabase
- **Quality standards** — what makes an extraction good vs. unusable
- **OCR pipeline** — handling scanned/image-only PDFs
- **Governance guardrails** — scope boundaries for delegated extraction tasks
- **Supabase integration** — how extractions enter the deployed platform

### What This Guide Does NOT Cover

- Study guide authoring (see `Development/CONTENT-FORMAT-SPEC-v2.3.md`)
- Pipeline automation (see `Development/PIPELINE-V2-FRAMEWORK.md`)
- Multi-instance coordination (see `GOVERNANCE-FRAMEWORK.md`)

---

## 2. Core Principles

### 2.1 Curate, Don't Dump

**This is the single most important principle in this document.**

A raw page-by-page text extraction (fitz dump, OCR page output, copy-paste with
page markers) is **not** an extraction. It is unusable input that someone else will
have to re-process from scratch. If the output requires a human to re-read the
original PDF to make sense of it, the extraction has failed.

A curated extraction:
- Organizes content by topic, not by page number
- Uses descriptive section headings (not "Page 1", "Page 2")
- Reconstructs tables into clean markdown
- Strips boilerplate (copyright, committee lists, watermarks)
- Preserves page references `[p.XX]` for traceability
- Reads like a study-ready reference document

**Test:** Could a technician learn from this extraction without ever opening the
source PDF? If yes, it's curated. If no, it's a dump.

### 2.2 Calcium Andite Rule

> **Never invent technical claims not found in the source document.**

This rule means: if a value, rating, threshold, or technical claim is not explicitly
stated in the source material or a referenced authoritative standard, do not include
it in the extraction. If a value is unclear (especially from OCR), mark it with
`<!-- TODO: Verify — OCR artifact -->` rather than guessing.

**What this rule does NOT mean:** "Copy everything verbatim." Curation requires
judgment — reorganizing content, writing descriptive headings, summarizing context.
The rule constrains **technical claims and numerical values**, not editorial structure.

**Origin:** Named after an incident where an AI instance fabricated a mineral name
("calcium andite") that doesn't exist, embedded in otherwise-accurate technical
content. The invented claim was indistinguishable from real content without expert
review. This is the failure mode we guard against.

### 2.3 Extract Once, Curate Well, Reuse Often

Source documents contain information applicable to multiple certification levels,
multiple guides, and multiple content types. A well-curated extraction gets
referenced dozens of times across the platform. Investment in quality here has
compound returns.

### 2.4 Selective Extraction for Large Documents

Not every page of a 500-page standard is relevant to NETA ETT testing. Large
documents (>100 pages) should be extracted **selectively** — focused on chapters
and sections that contain:

- Test procedures and acceptance criteria
- Equipment ratings, thresholds, tolerances
- Definitions relevant to field testing
- Safety requirements
- Maintenance intervals and inspection criteria

Always document what was extracted AND what was skipped (with rationale) in the
extraction header. This prevents future extractors from re-doing work or
wondering if content was missed.

---

## 3. Curated Extraction Format

Every extraction file MUST follow this format. No exceptions.

### 3.1 File Header (Required)

```markdown
# [Document Title — descriptive, not just a number]
## Source: [Full citation — e.g., IEEE 1683-2014, Motor Control Centers Guide]
## Content ID: EXT-[ORG]-[NNN]
## Extracted: YYYY-MM-DD
## Pages: [total page count of source]
## Purpose: [Gap Closure | Depth Enhancement | New Coverage]
## KSA Relevance: [Brief — e.g., "CT motor control centers, 7.16 cluster"]
## Extraction Quality: [HIGH | MEDIUM | LOW]
## Extraction Method: [Direct text (fitz) | ocrmypdf + Tesseract | Manual transcription]

---

**Source file:** `Resources/Source-PDFs/[folder]/[filename].pdf`

**KSA gaps addressed:**
- [List specific KSA areas this extraction serves]

**Description:** [2-3 sentence summary of document scope and ETT relevance]

**Chapters extracted:**
- [Chapter/section title] — [page range] — [brief note on what's included]

**Chapters skipped:**
- [Chapter/section title] — [page range] — [rationale for skipping]

---
```

### 3.2 Header Field Definitions

| Field | Required | Values | Notes |
|---|---|---|---|
| **Document Title** | Yes | Descriptive title | Not just "IEEE 1683" — include the subject |
| **Source** | Yes | Full citation with year | Include publisher and standard number |
| **Content ID** | Yes | `EXT-[ORG]-[NNN]` | See Section 7 for ID assignment rules |
| **Extracted** | Yes | ISO date | Date extraction was completed |
| **Pages** | Yes | Integer | Total pages of source document |
| **Purpose** | Yes | Gap Closure / Depth Enhancement / New Coverage | Why this extraction exists |
| **KSA Relevance** | Yes | Brief text | Which KSA areas and NETA sections this serves |
| **Extraction Quality** | Yes | HIGH / MEDIUM / LOW | Based on source PDF quality, not extraction effort |
| **Extraction Method** | Yes | Text enum | How content was extracted from the PDF |
| **Source file** | Yes | Relative path | Path to the source PDF in the repo |
| **Description** | Yes | 2-3 sentences | What the document covers and why it matters |
| **Chapters extracted** | Yes | List | What was included |
| **Chapters skipped** | Conditional | List + rationale | Required if document is >50 pages or if notable sections were excluded |

### 3.3 Extraction Quality Tiers

| Tier | Definition | Source Condition |
|---|---|---|
| **HIGH** | Clean text extraction, all tables readable, no OCR artifacts | Native digital PDF, text-selectable |
| **MEDIUM** | Mostly clean, some OCR artifacts or formatting loss | Scanned PDF with good OCR, or digital PDF with complex tables |
| **LOW** | Significant OCR issues, some values may be unreliable | Poor scan quality, CamScanner, faded copies. Mark uncertain values with `<!-- TODO: Verify -->` |

### 3.4 Body Content Structure (Required)

After the header, organize extraction content following these rules:

1. **Overview section** (2-3 paragraphs) — Document scope, significance to ETT study,
   key takeaways. This is the "why should I care" section.

2. **Organized by chapter/section** — Use the source document's own structure where
   it's logical, but use descriptive headings. Good: `## Chapter 5: Ground-Fault
   System Types`. Bad: `## Page 37`.

3. **Tables reconstructed as clean markdown** — Do not dump raw text that was
   originally a table. Reconstruct into proper `| Column | Column |` format.
   Include the source table number: `*Source: IEEE 1683, Table 4.2, p.28*`

4. **Page references for traceability** — Include `[p.XX]` references inline so
   anyone can find the source. At minimum: one per major section. Ideal: one per
   key claim or table.

5. **Formulas and equations** — Preserve exactly as stated. Use code blocks for
   complex formulas. Define all variables with units.

6. **Cross-references noted** — When the source references other standards (IEEE,
   NFPA, NETA, ASTM), note them explicitly. This enables future extraction gap
   identification.

7. **Bold key values** — Highlight critical thresholds, ratings, and acceptance
   criteria using **bold** markdown. These are the values that end up in study
   guides and quick-reference tables.

8. **Source attribution** — Use blockquotes for direct source attribution:
   `> Source: IEEE 1683-2014, Section 5.3, p.31`

### 3.5 What to SKIP in Every Extraction

- Copyright notices, legal disclaimers, terms of use
- Foreword and preface (unless it contains technical scope information)
- Committee/participant lists
- Bibliography (note key referenced standards, skip the full list)
- Blank pages, page numbers, running headers/footers
- Watermarks (IEEE Xplore, ResearchGate, CamScanner, "SAMPLE", etc.)
- Publisher metadata, download timestamps, DOI numbers
- Index pages

### 3.6 What to PRESERVE EXACTLY in Every Extraction

- **ALL numerical thresholds, limits, tolerances, ratings** — exact values
- **ALL tables** — reformatted into clean markdown
- **ALL formulas and equations** — exact as stated
- **ALL test procedures and acceptance criteria** — step-by-step
- **ALL definitions** — especially NETA/IEEE/NEC defined terms
- **ALL cross-references** to other standards
- **Safety warnings and cautions** — verbatim or close paraphrase

---

## 4. Extraction Process

### 4.1 Pre-Extraction Checklist

Before starting any extraction:

- [ ] **Check if extraction already exists.** Search `Resources/Extractions/` by
  filename and `EXTRACTION-CATALOG.md` by Content ID. Duplicates waste time.
- [ ] **Identify the source PDF** and confirm it's in `Resources/Source-PDFs/[folder]/`.
   If not, place it in `Resources/Source-PDFs/_Unsorted/` first, then classify it into
   a canonical category before extraction.
- [ ] **Confirm the source path is canonical.** Do not extract from legacy aliases such as
   `IEEE-Standards/`, `IEC-Standards/`, `UL-Standards/`, `NETA-Standards/`,
   `Manufacturer-Docs/`, or `Testing Resources/` unless the task is explicitly historical
   and documented as such.
- [ ] **Determine extraction scope.** For documents >100 pages: identify which
  chapters/sections are relevant to NETA ETT testing. Document the scope decision.
- [ ] **Assign Content ID.** See Section 7 for ID format rules.
- [ ] **Choose extraction method.** See Section 5 for method selection.

### 4.2 Extraction Steps

**Step 1: Extract raw text from PDF**

Use fitz (PyMuPDF) for text-extractable PDFs:
```python
import fitz
doc = fitz.open(pdf_path)
for page in doc:
    text = page.get_text()
```

If `get_text()` returns empty or garbled output, the PDF is image-only — proceed
to Section 5 (OCR Pipeline).

**Step 2: Curate the raw text**

This is where the work happens. Transform raw text output into structured,
study-ready content following the format in Section 3. This means:

- Strip all boilerplate (headers, footers, watermarks, page numbers)
- Identify and reconstruct tables
- Create descriptive section headings
- Add page references
- Bold key values
- Note cross-references to other standards

**Step 3: Write the extraction file**

Create the file at the correct path:
```
Resources/Extractions/[canonical-category-or-governed-exception]/[DESCRIPTIVE-FILENAME].md
```

Use UTF-8 encoding. Follow the header template exactly.

**Step 4: Self-review**

Before committing, verify:
- [ ] Header complete (all required fields)
- [ ] Content organized by topic (no page-number headings)
- [ ] Tables are clean markdown
- [ ] Key values are bold
- [ ] Page references present
- [ ] No OCR artifacts without `<!-- TODO: Verify -->` tags
- [ ] No invented technical claims (Calcium Andite Rule)
- [ ] Chapters extracted/skipped are documented in header

**Step 5: Commit to git (disk only)**

```
git add Resources/Extractions/[ORG]/[filename].md
git commit -m "curated extraction: [Content ID] — [short title]"
```

**Step 6: Update catalog / tracking surfaces** (if not part of a batch task)

Add entry to `Resources/Extractions/EXTRACTION-CATALOG.md`.

### 4.3 Extraction Does NOT Include Supabase Load

Extractions go to **disk only**. Supabase loading is a separate step performed
by VS Code Claude after human review. See Section 8 for the full pipeline.

---

## 5. OCR Pipeline

### 5.1 When OCR Is Needed

OCR is required when the source PDF is image-only (scanned pages, photographs
of documents, CamScanner output). Test: if `fitz` `get_text()` returns empty
strings or garbled Unicode, the PDF needs OCR.

### 5.2 Tools

| Tool | Purpose | Installation |
|---|---|---|
| **ocrmypdf** | Adds OCR text layer to image-only PDFs | `pip install ocrmypdf` |
| **Tesseract** | OCR engine (used by ocrmypdf) | Pre-installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` |

### 5.3 OCR Procedure

**Step 1: Run ocrmypdf to create searchable PDF**

```python
import subprocess
subprocess.run([
    "ocrmypdf",
    "--tesseract-timeout", "120",
    "--optimize", "0",          # Skip Ghostscript optimization (may not be installed)
    "--output-type", "pdf",
    input_pdf_path,
    output_pdf_path
], check=True)
```

**Key flags:**
- `--optimize 0` — Required if Ghostscript is not installed. Without this flag,
  ocrmypdf will fail on the optimization step.
- `--tesseract-timeout 120` — Generous timeout for complex pages.
- `--skip-text` — Add this flag if the PDF already has a partial text layer
  (prevents double-OCR on pages that already have text).

**Step 2: Extract text from OCR'd PDF using fitz**

```python
import fitz
doc = fitz.open(output_pdf_path)
for page_num, page in enumerate(doc):
    text = page.get_text()
    # Now curate this text per Section 3
```

**Step 3: Assess OCR quality**

Before curating, scan the raw OCR output for:
- Garbled characters (especially in tables with numerical values)
- ALL CAPS text (common with some scan types — convert to proper case during curation)
- Merged/split words
- Missing characters in formulas

Set `Extraction Quality: LOW` or `MEDIUM` in the header based on assessment.
Mark any uncertain values with `<!-- TODO: Verify — OCR artifact -->`.

### 5.4 Image Extraction for Diagram-Heavy Documents

Some source PDFs are primarily diagrams, schematics, or wiring drawings with
minimal extractable text. For these:

1. Extract whatever text descriptions, specifications, and ratings exist
2. Note what diagrams are present: `*[Diagram: Figure 3 — MV bypass isolation
   one-line diagram, p.12]*`
3. If extractable text content is <50 lines, create a **catalog entry** instead
   of a full extraction — header + brief description of what the document contains
4. Use fitz `get_pixmap()` to export key diagrams as PNG if they will be needed
   for the image_assets pipeline (future)

```python
# Export a specific page as PNG
page = doc[page_number]
pix = page.get_pixmap(dpi=200)
pix.save(f"Development/Visual-Assets/{topic}/{asset_id}.png")
```

---

## 6. Source Document Priority

### Tier 1: Critical — Extract Comprehensively

| Document | Content | Extraction Folder |
|---|---|---|
| ANSI/NETA ATS-2025 | Testing procedures, acceptance criteria | `NETA/` or established governed NETA legacy folder |
| ANSI/NETA MTS-2023 | Maintenance testing specs | `NETA/` or established governed NETA legacy folder |
| ANSI/NETA ETT-2022 | KSA requirements, exam weights | `NETA/` or established governed NETA legacy folder |
| NFPA 70E (current) | Safety requirements, PPE, approach boundaries | `NFPA-70E/` governed legacy folder |

### Tier 2: High Priority — Extract Selectively

| Document | Content | Extraction Folder |
|---|---|---|
| IEEE Color Books (141, 142, 241, 242, etc.) | System design principles | `IEEE/` |
| IEEE Equipment Standards (C37.xx, C57.xx, etc.) | Equipment test standards | `IEEE/` |
| NETA Handbooks (Volumes I-IV) | Field procedures and practical guidance | `NETA-Handbooks/` governed legacy folder |
| Paul Gill Textbook | Comprehensive testing reference | `Paul-Gill/CURATED/` governed legacy folder |
| Manufacturer O&M Manuals | Equipment-specific procedures | `Equipment-Manuals/` |

### Tier 3: Reference — Extract Key Sections Only

| Document | Content | Extraction Folder |
|---|---|---|
| NEC (NFPA 70) | Code requirements | `NFPA-70E/` |
| NFPA 99, 101, 110 | Facility-specific requirements | `NFPA-70E/` |
| NEMA Standards (ICS 2, AB 4, etc.) | Equipment classifications | `NEMA/` |
| ASTM Standards | Material testing methods | `ASTM/` |
| IEC Standards | International equivalents | `IEC/` |

---

## 7. Content ID and Naming Conventions

### 7.1 Content ID Format

```
EXT-[ORG]-[NNN]
```

| Component | Values | Examples |
|---|---|---|
| **ORG** | IEEE, NFPA, NETA, NEMA, MFR, IND, TXT, ETT, FLD, CT, IEC, ASTM | Source organization |
| **NNN** | Sequential number within org | 001, 002, ... 999 |

**Valid ORG codes and their use:**

| Code | Organization / Source Type | Example ID |
|---|---|---|
| `IEEE` | IEEE standards and color books | EXT-IEEE-043 |
| `NFPA` | NFPA standards (70, 70E, 99, 101, 110) | EXT-NFPA-003 |
| `NETA` | NETA standards, tables, handbooks | EXT-NETA-003 |
| `NEMA` | NEMA standards | EXT-NEMA-005 |
| `MFR` | Manufacturer documents (Eaton, GE, ASCO, etc.) | EXT-MFR-039 |
| `IND` | Industry guides and white papers | EXT-IND-020 |
| `TXT` | Textbooks (Paul Gill, Kuphaldt, etc.) | EXT-TXT-013 |
| `ETT` | NETA ETT study aids and exam resources | EXT-ETT-005 |
| `FLD` | Field guides and practical references | EXT-FLD-013 |
| `CT` | Component testing specific extractions | EXT-CT-001 |
| `IEC` | IEC international standards | EXT-IEC-003 |
| `ASTM` | ASTM material testing standards | EXT-ASTM-001 |

**ID assignment:** Check `EXTRACTION-CATALOG.md` for the highest existing number in the
org category, then increment. If the catalog is stale, search `study_content` in
Supabase: `SELECT content_id FROM study_content WHERE content_id LIKE 'EXT-[ORG]-%'
ORDER BY content_id DESC LIMIT 1`.

If the source document is historical and no longer exists in the active canonical source
library, do not assign a new extraction ID until the historical-source handling is
explicitly decided.

### 7.2 File Naming Convention

```
[ORG]-[Standard-Number]-[Year]-[Descriptive-Title].md
```

Examples:
- `IEEE-1683-2014-Motor-Control-Centers-Guide.md`
- `NEMA-ICS-2-2000-R2020-Controllers-Contactors.md`
- `EXT-MFR-039-Eaton-GFP-Presentation.md`
- `NFPA-70E-2024-Arc-Flash-Safety.md`

**Rules:**
- Hyphens between words (no spaces, no underscores)
- Include the standard number and year when applicable
- Descriptive title — someone should know what the file contains from the name alone
- UTF-8 encoding always

### 7.3 Folder Structure

```
Resources/Extractions/
├── [canonical categories such as IEEE/, IEC/, NEMA/, Equipment-Manuals/]
├── [governed legacy folders retained for continuity such as NETA-Standards/, NFPA-70E/, Paul-Gill/]
└── EXTRACTION-CATALOG.md
```

**Rules:**

- Prefer canonical source-aligned categories for new work.
- Existing governed legacy extraction folders may remain in use where continuity matters.
- Do NOT create new folders casually. If a new source type does not fit an existing
   governed category or exception, escalate and update governance first.

---

## 8. Supabase Pipeline Integration

### 8.1 Lifecycle

```
Source PDF → [EXTRACT to disk] → [HUMAN REVIEW] → [LOAD to Supabase] → [KSA LINK DISCOVERY]
                  ↓                      ↓                   ↓                      ↓
            Extraction file      Quality verified      study_content row      ksa_content_links
            on disk only         by human/Desktop      created by VS Code     created by script
```

### 8.2 Key Rule: Extraction ≠ Loading

**Extraction creates a file on disk. Loading inserts it into Supabase. These are
separate steps performed by different instances with a human review gate between them.**

An extraction is complete when the curated .md file exists on disk and passes the
quality checklist. It is NOT complete when it's in Supabase — that requires a
separate, authorized loading operation.

### 8.3 Supabase Record Format

When an extraction is loaded to Supabase (by VS Code, after review), it maps to
a `study_content` row with these fields:

| Field | Source | Example |
|---|---|---|
| `content_id` | From extraction header Content ID | `EXT-IEEE-073` |
| `title` | From extraction header Document Title | `IEEE C57.147-2018 DGA Guide for Transformers with Natural Ester` |
| `resource_type` | Always `extraction` | `extraction` |
| `neta_section` | Primary NETA ATS section this extraction serves | `7.10` |
| `domain` | CT or ET or General | `CT` |
| `body_markdown` | Full body of the extraction (everything after the header) | (long text) |
| `quality_tier` | From Extraction Quality field mapped to: `draft` / `complete` | `complete` |
| `metadata` | JSON with additional fields | `{"source_document": "...", "pages": 47, ...}` |
| `status` | `draft` initially, `published` after review | `draft` |
| `tags` | Array of topic tags | `["ieee", "transformers", "dga", "natural-ester"]` |

Additional governance rule:

- `study_content.source_path` must be the canonical repo-relative `Resources/...` path
   of the source document used for the extraction.
- If the original historical source no longer exists in the governed active source
   library, do not guess a remap to a newer edition. Follow the documented
   `historical-source-retired` disposition path instead.

### 8.4 Loading Process (VS Code Only)

1. VS Code reads the curated extraction file from disk
2. Parses the header to populate structured fields
3. Extracts body content (everything after the header separator)
4. Runs `INSERT` or `UPSERT` to `study_content`
5. Runs `discover_ksa_links.py` to create KSA associations
6. Commits updated link counts

**CC does NOT perform any of these steps. CC creates disk files only.**

---

## 9. Governance Guardrails for Delegated Extraction Tasks

When extraction work is delegated to Claude Code (CC) via task documents, the
following guardrails apply. These are mandatory and non-negotiable.

### 9.1 Scope Lock

Every CC extraction task document MUST contain an explicit scope lock:

> **SCOPE LOCK:** Do NOT extract, load, create, modify, or delete anything not
> explicitly listed in this task document. If you discover something that seems
> like it should be done, STOP and note it in the Observations section at the
> bottom. Do not act on it.

### 9.2 No Supabase Writes

CC does NOT write to Supabase. All database operations happen in a separate
human-reviewed task after extraction quality is verified on disk.

> **NO SUPABASE WRITES:** Extractions go to disk only. Do not INSERT or UPSERT
> to study_content or any other table. Do not run discover_ksa_links.py.

### 9.3 No New Folders

CC does NOT create new directories under `Resources/`. All output paths must be
specified in the task document. If a path doesn't exist, that is an error — stop
and report.

### 9.4 Output Format Enforcement

Every CC task document must reference this guide (RESOURCE-EXTRACTION-GUIDE V2.0)
as the authoritative format standard. Task documents may add task-specific guidance
(e.g., which chapters to extract from a specific document) but cannot override or
relax the format requirements defined here.

### 9.5 Commit Protocol

One commit per extraction. Commit message format:
```
curated extraction: [Content ID] — [short descriptive title]
```

### 9.6 Stop Conditions

CC must stop and report (not continue) when:
- Source PDF is too degraded for reliable extraction (OCR quality below usable threshold)
- Content falls outside the KSA areas specified in the task document
- Ambiguous technical content that could violate the Calcium Andite Rule
- File path specified in task document doesn't exist
- Scope boundary reached (all listed items completed)

---

## 10. Quality Checklist

### Before Saving Any Extraction

**Completeness:**
- [ ] Header complete with all required fields (see Section 3.1)
- [ ] All relevant chapters/sections from scope captured
- [ ] Tables reconstructed as clean markdown
- [ ] Formulas preserved exactly
- [ ] Key values bolded
- [ ] Page references included

**Structure:**
- [ ] Organized by topic (no page-number headings)
- [ ] Descriptive section headings
- [ ] Overview section present
- [ ] Chapters extracted/skipped documented in header

**Accuracy:**
- [ ] No invented technical claims (Calcium Andite Rule)
- [ ] OCR artifacts marked with `<!-- TODO: Verify -->`
- [ ] Cross-references to other standards noted
- [ ] Source attribution via blockquotes

**Format:**
- [ ] Standard header template used
- [ ] UTF-8 encoding
- [ ] Proper file naming convention
- [ ] Correct folder location
- [ ] Content ID assigned and unique

---

## 11. Exemplar Extractions

These existing extractions demonstrate the correct curated format. Reference them
when in doubt about structure, depth, or style.

| Content ID | File | Lines | Why It's a Good Example |
|---|---|---|---|
| EXT-NEMA-005 | `NEMA/NEMA-ICS-2-2000-R2020-Controllers-Contactors.md` | 552 | Clean tables, selective extraction, proper skip documentation |
| EXT-IEEE-073 | `IEEE/IEEE-C57.147-2018-natural-ester-acceptance.md` | 273 | Concise, focused, excellent key-value highlighting |
| EXT-IEEE-074 | `IEEE/IEEE-1184-2022-Batteries-UPS-Systems.md` | ~800 | Large standard selectively extracted, good chapter organization |
| EXT-IEEE-1683 | `IEEE/IEEE-1683-2014-Motor-Control-Centers-Guide.md` | 730 | Re-extracted from raw dump — shows before/after quality improvement |

### Anti-Pattern: What a Bad Extraction Looks Like

**Raw dump characteristics (DO NOT produce these):**
- `<!-- Page 1 -->`, `<!-- Page 2 -->` markers throughout
- IEEE Xplore or CamScanner watermarks in the text
- ALL CAPS text from poor OCR
- Tables as unformatted text blobs
- No header or incomplete header
- No organization — just sequential pages
- No page references, no source attribution
- Committee lists, copyright notices, bibliographies included
- Garbled Unicode characters from OCR artifacts

---

## 12. Common Extraction Scenarios

### 12.1 IEEE Standard (100-300 pages, text-extractable)

1. Run fitz `get_text()` to verify text extraction works
2. Focus extraction on: Scope, Definitions, Technical Requirements, Test Procedures,
   Acceptance Criteria, Informative Annexes with practical guidance
3. Skip: Foreword, Participants, Bibliography (note key references), Normative references
   (just list them), Index
4. Expected output: 300-800 lines depending on document length

### 12.2 Manufacturer O&M Manual (20-100 pages, may need OCR)

1. Check text extractability first — many manufacturer PDFs are scanned
2. Focus on: Equipment specifications, test procedures, maintenance intervals,
   troubleshooting, wiring diagrams (note as image references)
3. Skip: Warranty info, ordering information, marketing content
4. Expected output: 150-500 lines

### 12.3 NFPA Standard (200-1000+ pages, text-extractable)

1. Always extract selectively — identify electrical-relevant chapters first
2. Focus on: Definitions, electrical system requirements, testing/inspection chapters,
   emergency power requirements, tables with ratings/thresholds
3. Skip: Non-electrical chapters (plumbing, HVAC, structural), administrative chapters
4. Document chapters extracted vs. skipped with rationale
5. Expected output: 300-1000 lines (from potentially 1000+ page source)

### 12.4 Short Manufacturer Brochure or FAQ (2-10 pages)

1. If the document has <50 lines of extractable technical content, create a
   **catalog entry** — full header + brief description of contents + key specs
2. If it has >50 lines of technical content, create a full curated extraction
3. Expected output: 50-200 lines

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | Dec 19, 2025 | Initial extraction guide (pre-Supabase, generic template) |
| 2.0 | Mar 15, 2026 | **Complete rewrite.** Curated format standard (replaces dump pattern). Added: Supabase pipeline integration, OCR pipeline (Tesseract/ocrmypdf), governance guardrails for CC, Calcium Andite Rule definition, quality tiers, exemplar references, Content ID registry, extraction lifecycle. Elevated format standard from ad-hoc task docs (TASK-CC-REEXTRACT-RAW-DUMPS.md) into permanent governance. Driven by Mar 15 CC unauthorized extraction incident post-mortem. |
| 2.1 | Mar 25, 2026 | Aligned extraction guidance to the canonical resource governance model. Added canonical source-path rules, intake/classification pre-checks, source-path governance for Supabase, and clarified use of canonical categories versus governed legacy extraction folders. |

---

*This guide is authoritative for all extraction procedures. It is referenced by
GOVERNANCE-FRAMEWORK.md and MASTER-STANDARDS.md. Update version number when modifying.*
