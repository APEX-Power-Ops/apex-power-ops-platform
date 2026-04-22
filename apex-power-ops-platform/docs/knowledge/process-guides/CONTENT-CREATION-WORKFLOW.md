> ⚠️ **DEPRECATED — March 2026**
>
> This document is V1.0 from December 2025 and does not reflect the current
> content pipeline. The authoritative references are now:
>
> - **Study guide authoring:** `Development/CONTENT-FORMAT-SPEC-v2.3.md`
> - **Pipeline automation:** `Development/PIPELINE-V2-FRAMEWORK.md`
> - **Extraction format:** `Process-Guides/RESOURCE-EXTRACTION-GUIDE.md` (V2.0)
> - **Multi-instance coordination:** `GOVERNANCE-FRAMEWORK.md`
> - **Session state:** `Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md`
>
> This file is retained for historical reference only. Do not follow these
> procedures for new work.

---

# Content Creation Workflow
## From Source Material to Production Content
### Version 1.0 | December 19, 2025

---

## Overview

This document defines the complete pipeline for creating NETA ETT educational content. Following this workflow ensures consistent quality, proper documentation, and efficient use of extracted resources.

```
SOURCE PDF → EXTRACTION → STAGING → ASSEMBLY → FINAL → COMMIT
```

---

## Pipeline Stages

### Stage 1: SOURCE PDF
**Location:** `Resources/Source-PDFs/` (if tracked) or external reference

**Source Materials:**
| Document | Use For | Priority |
|----------|---------|----------|
| ANSI/NETA ETT-2022 | KSA requirements, exam weights | Critical |
| ANSI/NETA ATS-2025 | Testing procedures, acceptance criteria | Critical |
| ANSI/NETA MTS-2023 | Maintenance testing specs | High |
| IEEE Color Books | Technical depth, calculations | High |
| NFPA 70E | Safety content | High |
| NEC (NFPA 70) | Code requirements | Medium |

**Actions at this stage:**
- Identify relevant sections for target content
- Note page numbers and section references
- Check if extraction already exists in Resources/

---

### Stage 2: EXTRACTION
**Location:** `Resources/Extractions/[SOURCE]/`

**Purpose:** Extract content ONCE, tag it, reuse across levels.

**Extraction Format:**
```markdown
# [Topic Name] - Extracted Content
## Source: [Document Name], Section [X.X], Pages [XX-XX]
## Extracted: [Date]
## Extractor: [Claude instance]

---

## KSA Tags
- Level II: [KSA codes if applicable]
- Level III: [KSA codes if applicable]  
- Level IV: [KSA codes if applicable]

---

## Content

[Extracted text, formulas, tables, procedures]

---

## Notes
[Any clarifications, cross-references, or context]
```

**Quality Checklist:**
- [ ] Source clearly identified
- [ ] KSA tags applied from crosswalk
- [ ] Content is factual extraction (not interpretation)
- [ ] Formulas verified against source
- [ ] Tables preserved in usable format

---

### Stage 3: STAGING
**Location:** `Development/NETA-[X]/Staging/`

**Purpose:** Transform extracted content into structured draft ready for assembly.

**Naming Convention:** `##-TOPIC-STAGED.md`

**Staging Format:**
```markdown
# [Full Title] - STAGED
## Target: [Study Guide | Practice Test | Reference Sheet]
## Level: [II | III | IV]
## Status: STAGED - Ready for Assembly

---

## Metadata
- **Target File:** [final filename]
- **Est. Lines:** [target line count]
- **KSAs Covered:** [list]
- **Prerequisites:** [list any required prior content]

---

## Content Sections

### Section 1: [Name]
[Content with formatting notes]

### Section 2: [Name]
[Content with formatting notes]

...

---

## Questions (if practice test)

### Q1
- **Question:** [text]
- **A:** [option]
- **B:** [option]
- **C:** [option]
- **D:** [option]
- **Correct:** [letter]
- **Explanation:** [why correct]
- **WhyMatters:** [real-world relevance]
- **CommonMistake:** [typical error]
- **KSA:** [code]

...

---

## Assembly Notes
[Any special instructions for HTML assembly]
```

**Quality Checklist:**
- [ ] All sections complete (no placeholders)
- [ ] Follows Build-Spec for content type
- [ ] KSA tags match crosswalk
- [ ] Level-appropriate depth verified
- [ ] Ready for direct assembly (no research needed)

---

### Stage 4: ASSEMBLY
**Location:** Working directory, then move to final location

**Purpose:** Combine staged content with master template to produce production HTML.

**Master Template Elements:**

#### Study Guide Template
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>[TITLE] | NETA Level [X] Study Guide</title>
    <style>
        /* Standard study guide CSS */
    </style>
</head>
<body>
    <header>
        <h1>[TITLE]</h1>
        <div class="level-badge">[LEVEL]</div>
        <div class="ksa-tags">[KSA CODES]</div>
    </header>
    
    <nav class="toc">
        <!-- Auto-generated TOC -->
    </nav>
    
    <main>
        <!-- Content sections -->
    </main>
    
    <footer>
        <div class="references">
            <!-- NETA ATS, IEEE references -->
        </div>
    </footer>
</body>
</html>
```

#### Practice Test Template
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>[TITLE] | NETA Level [X] Practice Test</title>
    <style>
        /* Standard practice test CSS */
    </style>
</head>
<body>
    <div id="quiz-container">
        <header>
            <h1>[TITLE]</h1>
            <div id="timer"></div>
            <div id="progress"></div>
        </header>
        
        <!-- Foundation Review Section -->
        <section class="foundation-review">
            <!-- Key concepts before questions -->
        </section>
        
        <!-- Questions by Section -->
        <section class="questions" data-section="1">
            <!-- Questions with enhanced feedback -->
        </section>
        
        <!-- Results -->
        <section id="results" class="hidden">
            <!-- Score, analytics, answer review -->
        </section>
    </div>
    
    <script>
        // Timer, scoring, analytics integration
        const ANALYTICS_CONFIG = {
            WEB_APP_URL: '[GOOGLE_SHEETS_URL]',
            ENABLE_TRACKING: true,
            TEST_NAME: '[TEST NAME]'
        };
        // ... quiz functionality
    </script>
</body>
</html>
```

**Assembly Process:**
1. Open master template for content type
2. Insert staged content into appropriate sections
3. Apply consistent formatting (CSS classes, structure)
4. Add analytics integration (practice tests)
5. Add navigation links (study guides)
6. Verify all placeholders replaced
7. Test in browser

**Quality Checklist:**
- [ ] Template structure intact
- [ ] All staged content inserted
- [ ] No placeholder text remaining
- [ ] CSS classes properly applied
- [ ] JavaScript functional (if applicable)
- [ ] Browser tested (Chrome recommended)

---

### Stage 5: FINAL
**Location:** `NETA-[X]/[appropriate-folder]/`

**Folder Structure:**
```
NETA-[X]/
├── 00-QUICK-START.html
├── 01-Study-Plan/
├── 02-Reference-Sheets/
├── 03-Study-Guides/
├── 04-Practice-Tests/
├── 05-Flashcards/
├── 06-Mock-Exams/
└── 07-Progress-Tracker/
```

**File Naming Convention:**
- Study Guides: `##-Topic-Name-Guide.html`
- Practice Tests: `##-Topic-Name-Practice.html`
- Reference Sheets: `Topic-Name-Reference.html`

**Pre-Commit Checklist:**
- [ ] File in correct folder
- [ ] Naming follows convention
- [ ] Line count meets minimum (tests: 1000+, guides: 500+)
- [ ] Opens correctly in browser
- [ ] All links/navigation work
- [ ] Timer functions (practice tests)
- [ ] Scoring works (practice tests)

---

### Stage 6: COMMIT
**Location:** Git repository

**Commit Process:**
```bash
git add [path/to/file]
git commit -m "[CONTENT] Add [description]

- [key feature 1]
- [key feature 2]
- KSAs covered: [list]"
git push origin main
```

**Post-Commit:**
- [ ] Update the active tracker, resume doc, or task record
- [ ] Update relevant tracker (if exists)
- [ ] Archive staged file to `Development/NETA-[X]/Archive/Staging/`

---

## Workflow Variations

### Quick Content (< 200 lines)
Skip formal staging. Extract → Assemble directly → Commit.
*Use for: Reference sheets, simple updates, fixes*

### Complex Content (1000+ lines)
Full staging process. May require multiple sessions.
*Use for: Practice tests, comprehensive study guides*

### Enhancement of Existing
Read existing → Identify gaps → Stage additions only → Merge → Commit.
*Use for: Level III/IV enhancements to Level II content*

### Batch Operations
Stage multiple items → Assemble in sequence → Batch commit.
*Use for: Creating series of related content*

---

## Time Estimates

| Content Type | Extraction | Staging | Assembly | Total |
|--------------|------------|---------|----------|-------|
| Reference Sheet | 10 min | 15 min | 20 min | 45 min |
| Study Guide (basic) | 20 min | 30 min | 40 min | 1.5 hrs |
| Study Guide (comprehensive) | 45 min | 60 min | 90 min | 3-4 hrs |
| Practice Test (24 Qs) | 30 min | 60 min | 90 min | 3 hrs |
| Practice Test (Gold Standard) | 60 min | 120 min | 120 min | 5+ hrs |

---

## Common Pitfalls

### Skipping Staging
**Problem:** Jumping from extraction to final HTML
**Result:** Missing content, inconsistent structure, longer debugging
**Solution:** Always stage complex content, even if briefly

### Incomplete Extraction
**Problem:** Not capturing all relevant source content
**Result:** Multiple return trips to source documents
**Solution:** Extract comprehensively, tag for reuse

### Placeholder Amnesia
**Problem:** Forgetting to replace [PLACEHOLDER] text
**Result:** Unprofessional content, broken functionality
**Solution:** Search for "[" and "TODO" before committing

### Skipping Browser Test
**Problem:** Committing without visual verification
**Result:** CSS issues, JavaScript errors, broken layouts
**Solution:** Always open in Chrome before commit

---

## Templates Location

Master templates should be maintained in:
- `Development/Shared/Templates/study-guide-template.html`
- `Development/Shared/Templates/practice-test-template.html`
- `Development/Shared/Templates/reference-sheet-template.html`

*(Templates to be created as part of infrastructure completion)*

---

*This workflow is a living document. Update as process evolves.*
