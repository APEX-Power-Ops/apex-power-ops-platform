# Reference Sheet Specification
## Canonical Build-Spec Surface For Quick-Lookup Reference Format And Publication Rules

Created: April 4, 2026
Status: Active canonical specification
Purpose: Define the canonical format, naming, printability, and field-use rules for reference sheets in the NETA ETT workspace

---

## Scope

This specification defines how reference sheets should be structured and published.

It covers:

1. the mission and boundaries of quick-lookup reference sheets
2. format, scannability, and printability expectations
3. citation and authority requirements for values, formulas, and procedures
4. naming and placement rules for published reference artifacts
5. quality and field-use validation rules

It does not cover:

1. tutorial-style explanations or full concept teaching
2. study-guide depth requirements
3. practice-test behavior
4. generic staging workflow outside the reference-sheet-specific publication contract

---

## Authority Relationship

This file is the canonical build-spec surface for reference-sheet format and publication behavior.

It should be read together with:

1. `Development/Shared/AUDIT-GUIDE-REFERENCE-SHEETS.md` for quality intent and audit dimensions
2. `Process-Guides/QUALITY-VALIDATION-CHECKLIST.md` for lightweight pre-publication checks
3. `MASTER-STANDARDS.md` for naming and placement conventions
4. `Build-Specs/INFRASTRUCTURE-ROADMAP.md` for the historical planning context that originally called for this artifact

Interpretation:

1. this spec defines the stable canonical contract
2. the audit guide remains a supporting review surface rather than a competing authority source
3. if examples or legacy files drift from this contract, reconcile them explicitly instead of normalizing the drift silently

---

## Mission And Boundary

Reference sheets are quick-lookup field companions.

They should let a technician or learner:

1. find information quickly
2. trust the values and limits
3. apply the information immediately
4. verify acceptance or safety boundaries without reading a long guide

Reference sheets are not:

1. tutorials
2. full study guides
3. long-form concept explanations
4. narrative walkthroughs of an entire topic

If the artifact needs extensive explanation, it should be a study guide instead.

---

## Canonical Publication Form

Published reference sheets should be delivered as HTML artifacts in the appropriate `02-Reference-Sheets/` content folder.

Rules:

1. HTML is the canonical published delivery surface for student-facing reference sheets
2. markdown staging or draft sources may exist during authoring, but the published contract is the rendered reference artifact
3. reference-sheet index pages are related navigation surfaces, not replacements for the per-sheet specification

---

## Required Structural Qualities

Every reference sheet must optimize for speed of lookup.

Required structural traits:

1. clear title and topic identity
2. scannable sections with visible heading hierarchy
3. lookup-friendly structures such as tables, cards, checklists, or compact grouped lists
4. strong contrast and readable spacing
5. print-friendly layout

Anti-patterns to reject:

1. dense paragraphs that bury the actual value or limit
2. long narrative sections before the first usable reference content
3. overly complex multi-column structures that fail on print or mobile

---

## Printability And Field Use Rules

Printability is a first-class requirement, not a nice-to-have.

Required field-use behavior:

1. the sheet must remain readable at normal print scale
2. the page should fit cleanly into a single page or a small logical page set when the topic genuinely requires it
3. print CSS should remove unnecessary navigation or decorative elements when appropriate
4. the sheet should still be readable in bright-light or field conditions through contrast and spacing

Recommended enhancements:

1. explicit print note when the artifact is especially intended for exam or field carry use
2. optional notes space or write-in area where that materially helps field use

---

## Allowed Reference Sheet Types

Canonical reference sheets may include these common categories:

1. formula sheets
2. testing procedure quick references
3. safety and PPE quick references
4. codes and standards quick references
5. equipment or settings quick references
6. acceptance-criteria tables and threshold summaries

The content type can vary, but the quick-lookup mission stays the same.

---

## Citation And Authority Rules

Reference sheets often contain safety-critical and acceptance-critical values.

Required authority behavior:

1. cite the governing standard or source for values and criteria
2. keep edition-sensitive values aligned with the current accepted source edition
3. avoid unattributed “industry standard” claims
4. preserve traceability for formulas, thresholds, and acceptance criteria

When applicable, cite:

1. NETA ATS or MTS
2. IEEE standards
3. NEC or NFPA references
4. other governed source documents used by the workspace

---

## Content Rules By Reference Type

Formula sheets:

1. must show formulas clearly and accurately
2. should distinguish between formulas provided on the exam and formulas that must be memorized when that distinction matters
3. should define variables or units where ambiguity would slow lookup

Testing procedure references:

1. should emphasize steps, setups, acceptance limits, and common test voltages
2. should use tables and short ordered steps instead of long paragraphs

Safety references:

1. should elevate boundaries, PPE, and warning content visually
2. must not bury hazardous limits inside general text

Equipment or standards references:

1. should focus on the values, device mappings, settings, or decision points most likely to be needed quickly

---

## Safety Integration Rules

Where the topic has meaningful safety implications, the sheet must integrate safety visibly.

Examples:

1. warning boxes for hazardous tests
2. PPE reminders
3. approach-boundary or energy-risk callouts
4. stop-and-verify checkpoints before dangerous actions

Safety information should be easy to find at scan speed, not hidden at the bottom of the page.

---

## Naming And Placement Rules

Published reference sheets belong in `02-Reference-Sheets/` under the relevant level package.

Current standard naming rule from `MASTER-STANDARDS.md`:

1. `Topic-Name-Reference.html`

However, the live workspace contains historical filename drift such as:

1. `Testing-Procedures-Quick-Reference.html`
2. `Safety-NFPA70E-Quick-Reference.html`
3. `OFFICIAL-NETA-Formula-Sheet.html`

Canonical rule:

1. new general-purpose reference sheets should normalize toward the `Topic-Name-Reference.html` pattern when practical
2. established historical filenames may remain where renaming would create unnecessary churn
3. explicit special-case names such as an official exam formula sheet are acceptable when the title is part of the artifact’s meaning

---

## Navigation And Discoverability

Reference sheets should be discoverable from the package surfaces that already use them.

Recommended discovery surfaces:

1. the level-specific reference-sheet index page
2. quick-start pages
3. related practice tests or study aids where direct lookup is helpful

This spec governs the reference sheet itself, but it expects reference sheets to participate in the existing index-and-navigation model.

---

## Quality Rules

Every reference sheet should satisfy these quality expectations:

1. information is findable in seconds
2. all formulas, values, and limits are accurate
3. units are specified where needed
4. the layout is printable and readable
5. the sheet is clearly more useful as a lookup aid than as a long narrative document

Anti-patterns to reject:

1. incomplete tables missing common field values
2. no units on critical values
3. citations missing from safety-critical or acceptance-critical content
4. layout that requires zooming or excessive scrolling to find the core answer

---

## Validation Checklist

Use this checklist before treating a reference sheet as complete:

1. the artifact is scannable and quick to use
2. the most critical values or procedures are visually prominent
3. formulas and acceptance criteria are accurate and cited
4. print output is clean and readable
5. the sheet stays within quick-reference scope rather than drifting into a study guide
6. filename and folder placement follow the governed naming rule or a truthful approved exception

---

## Bottom Line

Reference sheets are fast, trustworthy, printable lookup surfaces for formulas, procedures, safety limits, and critical values.

They should prioritize scan speed, citation quality, and field usability over narrative depth.