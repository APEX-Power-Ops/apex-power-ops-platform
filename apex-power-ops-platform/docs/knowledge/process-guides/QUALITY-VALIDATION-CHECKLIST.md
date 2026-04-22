# Quality Validation Checklist
## Pre-Commit Quality Gates for NETA ETT Content
### Version 1.0 | December 19, 2025

---

## Purpose

Use this checklist before committing any content to ensure consistent quality. Check all applicable items for your content type.

---

## Universal Checks (All Content)

### File Basics
- [ ] File in correct folder per MASTER-STANDARDS.md
- [ ] Filename follows naming convention
- [ ] File extension correct (.html for production, .md for staging)
- [ ] No spaces in filename (use hyphens)

### Content Quality
- [ ] No placeholder text remaining (search for `[`, `TODO`, `FIXME`)
- [ ] No Lorem ipsum or sample content
- [ ] All formulas verified against source documents
- [ ] Spelling and grammar checked
- [ ] Technical terminology consistent throughout

### References
- [ ] NETA ATS/MTS standards cited where applicable
- [ ] IEEE standards referenced for technical depth
- [ ] Page/section numbers included for traceability

---

## Study Guide Checks

### Structure
- [ ] Title clearly states topic and level
- [ ] Table of contents present and accurate
- [ ] Logical section progression (basics → advanced)
- [ ] Level badges (II/III/IV) where content spans levels

### Content Depth
| Level | Minimum Lines | Depth Requirements |
|-------|--------------|---------------------|
| II | 400 | Foundational concepts, basic procedures |
| III | 600 | NETA ATS procedures, calculations, troubleshooting |
| IV | 800 | System-level analysis, coordination, advanced diagnostics |

- [ ] Meets minimum line count for level
- [ ] Includes worked calculation examples
- [ ] "Common Mistakes" or "Field Tips" section present
- [ ] Real-world applications explained

### KSA Coverage
- [ ] KSA tags identified in metadata or comments
- [ ] Content addresses stated KSAs
- [ ] Cross-references to related guides where helpful

### Browser Test
- [ ] Opens without errors in Chrome
- [ ] CSS renders correctly
- [ ] Navigation links work
- [ ] Print view acceptable (if applicable)

---

## Practice Test Checks

### Structure
- [ ] Minimum 24 questions (Gold Standard)
- [ ] Questions organized into sections (4+ sections ideal)
- [ ] Foundation Review section present
- [ ] Clear section headers with topic focus

### Question Quality
For EACH question verify:
- [ ] Clear, unambiguous question stem
- [ ] Four plausible answer options
- [ ] Only ONE clearly correct answer
- [ ] Correct answer marked properly
- [ ] Explanation provided

Enhanced Feedback (Gold Standard):
- [ ] `whyMatters` field explains real-world relevance
- [ ] `commonMistake` field warns of typical errors
- [ ] KSA tag assigned to question

### Functionality
- [ ] Timer starts and displays correctly
- [ ] Progress indicator updates
- [ ] Question navigation works
- [ ] Submit button functions
- [ ] Score calculates correctly
- [ ] Pass/fail threshold correct (typically 70%)
- [ ] Answer review shows all questions with explanations

### Analytics Integration
- [ ] `ANALYTICS_CONFIG` present with correct test name
- [ ] `WEB_APP_URL` points to valid endpoint (or placeholder noted)
- [ ] Session tracking functions included
- [ ] Question timing captured

### Line Count
| Type | Target |
|------|--------|
| Basic Test | 600-800 lines |
| Standard Test | 800-1000 lines |
| Gold Standard | 1000+ lines |

- [ ] Meets appropriate line count target

### Browser Test
- [ ] Opens without JavaScript errors (check console)
- [ ] Timer displays and counts down
- [ ] All questions render correctly
- [ ] Scoring works on completion
- [ ] Results display properly
- [ ] Mobile responsive (if applicable)

---

## Reference Sheet Checks

### Structure
- [ ] Single-page or logical sections
- [ ] Scannable format (tables, clear headings)
- [ ] Most critical info prominent

### Content
- [ ] Formulas correct and complete
- [ ] Units specified for all values
- [ ] Acceptance criteria from NETA ATS included
- [ ] "PROVIDED" vs "MEMORIZE" distinction (for exam formulas)

### Usability
- [ ] Print-friendly layout
- [ ] Text readable at typical sizes
- [ ] High contrast for field use

---

## Flashcard Deck Checks

### Content
- [ ] Front/back clearly distinguished
- [ ] Answers match authoritative sources
- [ ] Difficulty progression logical
- [ ] Categories/tags applied

### Functionality
- [ ] Shuffle works
- [ ] Show/hide answer works
- [ ] Navigation between cards works
- [ ] Progress tracking (if applicable)

---

## Infrastructure Document Checks

### Accuracy
- [ ] File paths and references verified
- [ ] Cross-references to other docs accurate
- [ ] Version number appropriate

### Completeness
- [ ] All sections filled (no TBD without explanation)
- [ ] Examples provided where helpful
- [ ] Edge cases addressed

### Maintenance
- [ ] "Last Updated" date current
- [ ] Clear ownership/update responsibility
- [ ] Living document note if applicable

---

## Commit Checks

### Git Hygiene
- [ ] Logical unit of work (not mixing unrelated changes)
- [ ] Commit message follows format: `[AREA] Brief description`
- [ ] Description includes key details in body
- [ ] No sensitive data committed

### State Updates
- [ ] Active tracker, resume doc, or task record reflects work done
- [ ] Trackers updated (if applicable)
- [ ] Coordination files updated (if handoff needed)

### Post-Push
- [ ] Verify push succeeded
- [ ] Check GitHub/remote if uncertain

---

## Quick Reference: Minimum Standards

| Content Type | Min Lines | Key Requirements |
|--------------|-----------|------------------|
| Study Guide (II) | 400 | Concepts + procedures |
| Study Guide (III) | 600 | + NETA ATS + calculations |
| Study Guide (IV) | 800 | + system analysis + coordination |
| Practice Test | 600 | 20+ questions, timer, scoring |
| Practice Test (Gold) | 1000 | 24+ Qs, sections, enhanced feedback, analytics |
| Reference Sheet | 150 | Accurate, scannable, print-ready |
| Flashcard Deck | 200 | Interactive, categorized |

---

## Validation Shortcut

For quick validation, check these 5 things:
1. **Filename** - Correct folder and convention?
2. **Placeholders** - Search for `[` returns nothing?
3. **Line count** - Meets minimum for type?
4. **Browser** - Opens and functions correctly?
5. **Commit message** - Follows `[AREA]` format?

If all 5 pass, content is likely ready.

---

*This checklist supports, not replaces, careful review.*
