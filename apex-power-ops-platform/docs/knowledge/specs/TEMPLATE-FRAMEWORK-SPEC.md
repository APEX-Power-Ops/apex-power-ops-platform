# Template Standards Framework v2.0
## Governing Specifications for NETA Study Material Templates
### Created: December 22, 2025

---

## 🎯 PURPOSE

This document defines the **exact specifications** for study guide and practice test templates aligned with MASTER-STANDARDS v2.0. It serves as the acceptance criteria for all template work.

**Philosophy:** Templates are infrastructure. Clear specifications prevent rework and ensure consistency across all 100+ content files that will be built from these templates.

---

## 📐 THE SIX QUALITY DIMENSIONS

Every template component must support at least one quality dimension:

| # | Dimension | Definition | Template Component |
|---|-----------|------------|-------------------|
| 1 | **Theoretical Foundation** | The "why" behind concepts | Concept sections, Foundation Reviews |
| 2 | **Practical Application** | Field-applicable procedures | Procedure sections, Step-by-step guides |
| 3 | **Authoritative Sources** | Citations to Paul Gill/IEEE/NETA | **Source panels, Source chips** |
| 4 | **Common Mistakes** | Specific errors + consequences | Mistake callouts, Warning boxes |
| 5 | **Why It Matters** | Safety/cost/career impact | **Impact grid sections** |
| 6 | **Progressive Depth** | Level II→III→IV progression | **Level badges, Preview sections** |

**Bold = New components needed in templates**

---

# PART 1: STUDY GUIDE TEMPLATE SPECIFICATIONS

## 1.1 Source Citation Panel

### Purpose
Display authoritative sources that validate the guide content. Reinforces that content is standards-based, not opinion.

### Required Structure
```html
<aside class="sources-panel">
    <h4>📚 Authoritative Sources</h4>
    <p class="sources-intro">This guide references these industry standards:</p>
    <ul class="source-list">
        <!-- Repeat for each source -->
        <li>
            <span class="source-tag source-[TYPE]">[SOURCE NAME]</span>
            <span class="source-detail">[REFERENCE] - [TOPIC]</span>
        </li>
    </ul>
</aside>
```

### Source Tag Types (6 Required)

| Class Name | Display Text | Background | Text Color | Use For |
|------------|--------------|------------|------------|---------|
| `source-gill` | Paul Gill | `#fef3c7` | `#92400e` | EPEMT textbook |
| `source-neta` | NETA | `#dcfce7` | `#166534` | ATS, MTS, ETT standards |
| `source-ieee` | IEEE | `#dbeafe` | `#1e40af` | IEEE standards |
| `source-nfpa` | NFPA | `#fee2e2` | `#991b1b` | NFPA 70E, NFPA 70B |
| `source-nec` | NEC | `#f3e8ff` | `#7c3aed` | NEC (NFPA 70) |
| `source-osha` | OSHA | `#fce7f3` | `#9d174d` | OSHA regulations |

### CSS Requirements
```css
.sources-panel {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 2px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin: 25px 0;
}

.source-tag {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    min-width: 70px;
    text-align: center;
}

.source-list li {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
}
```

### Validation Criteria
- [ ] Panel has gradient background (not flat color)
- [ ] Each source has colored tag + detail text
- [ ] All 6 source-tag classes defined in CSS
- [ ] List items have consistent spacing
- [ ] Works on mobile (stacks vertically under 768px)

---

## 1.2 Level Badge System

### Purpose
Visual indicator showing which certification level(s) the content applies to. Helps users understand progression.

### Required Structure
```html
<div class="level-badges">
    <span class="level-badge level-ii" title="Level II Foundation">II</span>
    <span class="level-badge level-iii active" title="Level III Primary">III</span>
    <span class="level-badge level-iv" title="Level IV Preview">IV</span>
</div>
```

### Badge Specifications

| Class | Background | Text | State |
|-------|------------|------|-------|
| `.level-ii` | `#dcfce7` | `#166534` | Green family |
| `.level-iii` | `#dbeafe` | `#1e40af` | Blue family |
| `.level-iv` | `#fef3c7` | `#92400e` | Amber family |
| `.active` | — | — | `opacity: 1`, `transform: scale(1.1)`, shadow |
| (inactive) | — | — | `opacity: 0.35` |

### CSS Requirements
```css
.level-badges {
    display: flex;
    gap: 8px;
    margin: 15px 0;
}

.level-badge {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    font-weight: 700;
    font-size: 0.85rem;
    opacity: 0.35;
    cursor: help;
    transition: all 0.2s;
}

.level-badge.active {
    opacity: 1;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    transform: scale(1.1);
}
```

### Validation Criteria
- [ ] Badges are circular (equal width/height)
- [ ] Inactive badges are visually muted (opacity 0.35)
- [ ] Active badge has shadow and slight scale
- [ ] Title attribute provides tooltip text
- [ ] Colors match specification exactly

---

## 1.3 Enhanced "Why It Matters" Section

### Purpose
Connect technical content to real-world consequences across safety, equipment, and cost dimensions.

### Required Structure
```html
<div class="why-it-matters">
    <h4>⚡ Why This Matters</h4>
    <div class="impact-grid">
        <div class="impact-item">
            <span class="impact-icon">🛡️</span>
            <div class="impact-content">
                <strong>Safety Impact:</strong>
                <p>[Specific safety consequence]</p>
            </div>
        </div>
        <div class="impact-item">
            <span class="impact-icon">⚙️</span>
            <div class="impact-content">
                <strong>Equipment Impact:</strong>
                <p>[Specific equipment consequence]</p>
            </div>
        </div>
        <div class="impact-item">
            <span class="impact-icon">💰</span>
            <div class="impact-content">
                <strong>Cost Impact:</strong>
                <p>[Specific cost consequence]</p>
            </div>
        </div>
    </div>
</div>
```

### Visual Specifications
- Container: Warning color gradient background, warning border
- Impact items: White background cards with left border accent
- Icons: 1.5rem size, flexbox aligned
- Grid: Stacks on mobile, 3-column on desktop optional

### Validation Criteria
- [ ] All three impact types present (Safety, Equipment, Cost)
- [ ] Each has icon + label + description
- [ ] Cards have left border accent
- [ ] Responsive: stacks on narrow screens

---

## 1.4 Level Preview Section

### Purpose
Show what content exists at the next certification level, encouraging progression.

### Required Structure
```html
<section class="level-preview">
    <div class="preview-header">
        <h3>🔮 Level IV Preview</h3>
        <span class="preview-badge">Advanced Topics</span>
    </div>
    <p class="preview-intro">At Level IV, you'll expand this knowledge to include:</p>
    <ul class="preview-topics">
        <li><span class="topic-badge">Advanced</span> [Topic description]</li>
        <li><span class="topic-badge">Advanced</span> [Topic description]</li>
        <li><span class="topic-badge">Advanced</span> [Topic description]</li>
    </ul>
    <p class="preview-cta">
        <a href="#">→ Ready to advance? See Level IV materials</a>
    </p>
</section>
```

### Validation Criteria
- [ ] Header with icon and badge
- [ ] Intro text explaining purpose
- [ ] 3-5 topic items with badges
- [ ] Call-to-action link at bottom
- [ ] Visually distinct from main content (lighter background)

---

# PART 2: PRACTICE TEST QUESTION SCHEMA

## 2.1 Question Object Schema (v2)

### Complete Field Specification

```javascript
{
    // ═══════════════════════════════════════════════════════════════
    // REQUIRED FIELDS (v1 - existing)
    // ═══════════════════════════════════════════════════════════════
    
    id: Number,           // Sequential: 1, 2, 3...
    question: String,     // Question text (can include HTML)
    options: Array,       // ["A) text", "B) text", "C) text", "D) text"]
    correct: Number,      // 0-indexed: 0=A, 1=B, 2=C, 3=D
    explanation: String,  // Technical explanation of correct answer
    whyMatters: String,   // Real-world significance
    commonMistake: String, // What people get wrong
    guideRef: {           // Link to study guide
        file: String,     // Filename: "16-Insulation-Resistance.html"
        title: String     // Display: "Insulation Resistance Deep Dive"
    },
    
    // ═══════════════════════════════════════════════════════════════
    // NEW FIELDS (v2 - add these)
    // ═══════════════════════════════════════════════════════════════
    
    sourceRef: Array,     // Authoritative sources (optional)
    // Format: [{ source: String, section: String, topic: String }]
    // Example: [
    //   { source: "Paul Gill EPEMT", section: "§ 6.4.2", topic: "VLF Testing" },
    //   { source: "NETA ATS 2025", section: "Table 100.18", topic: "Acceptance" }
    // ]
    
    levelTag: String,     // "II", "III", or "IV"
    
    ksa: String,          // KSA code for platform migration
    // Format: "[DOMAIN]-[NUMBER]"
    // Domains: ET (Electrical Theory), SF (Safety), CT (Component Testing),
    //          SC (Systems/Commissioning), TE (Test Equipment)
    // Example: "CT-024"
    
    difficulty: String    // "foundation", "core", "advanced", "challenge"
    // Note: This is already implicit in question position, now explicit
}
```

### Field Validation Rules

| Field | Required | Type | Validation |
|-------|----------|------|------------|
| `id` | ✅ Yes | Number | Sequential, no gaps |
| `question` | ✅ Yes | String | Non-empty |
| `options` | ✅ Yes | Array | Exactly 4 items |
| `correct` | ✅ Yes | Number | 0, 1, 2, or 3 |
| `explanation` | ✅ Yes | String | Min 50 chars |
| `whyMatters` | ✅ Yes | String | Min 30 chars |
| `commonMistake` | ✅ Yes | String | Min 30 chars |
| `guideRef` | ✅ Yes | Object | Both file and title |
| `sourceRef` | ⚪ Optional | Array | If present, valid format |
| `levelTag` | ⚪ Optional | String | "II", "III", or "IV" only |
| `ksa` | ⚪ Optional | String | Format: XX-### |
| `difficulty` | ⚪ Optional | String | One of 4 values |

---

## 2.2 Source Display in Feedback

### Required HTML Structure
```html
<div class="feedback-sources">
    <strong>📚 Sources:</strong>
    <div class="source-chips">
        <span class="source-chip chip-gill">Paul Gill EPEMT § 6.4.2</span>
        <span class="source-chip chip-neta">NETA ATS Table 100.18</span>
    </div>
</div>
```

### Chip Class Mapping

| Source Contains | Chip Class | Colors |
|-----------------|------------|--------|
| "Gill" | `chip-gill` | Amber |
| "NETA" | `chip-neta` | Green |
| "IEEE" | `chip-ieee` | Blue |
| "NFPA" or "70E" | `chip-nfpa` | Red |
| (default) | `chip-default` | Gray |

### CSS Requirements
```css
.feedback-sources {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px dashed rgba(0,0,0,0.15);
}

.source-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 8px;
}

.source-chip {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 15px;
    font-size: 0.8rem;
    font-weight: 500;
}

.chip-gill { background: #fef3c7; color: #92400e; }
.chip-neta { background: #dcfce7; color: #166534; }
.chip-ieee { background: #dbeafe; color: #1e40af; }
.chip-nfpa { background: #fee2e2; color: #991b1b; }
.chip-default { background: #f1f5f9; color: #64748b; }
```

### JavaScript Rendering Function
```javascript
function renderSourceChips(sourceRef) {
    // Handle null/undefined gracefully
    if (!sourceRef || !Array.isArray(sourceRef) || sourceRef.length === 0) {
        return '';
    }
    
    const getChipClass = (source) => {
        const s = source.toLowerCase();
        if (s.includes('gill')) return 'chip-gill';
        if (s.includes('neta')) return 'chip-neta';
        if (s.includes('ieee')) return 'chip-ieee';
        if (s.includes('nfpa') || s.includes('70e')) return 'chip-nfpa';
        return 'chip-default';
    };
    
    const chips = sourceRef.map(ref => 
        `<span class="source-chip ${getChipClass(ref.source)}">${ref.source} ${ref.section}</span>`
    ).join('');
    
    return `
        <div class="feedback-sources">
            <strong>📚 Sources:</strong>
            <div class="source-chips">${chips}</div>
        </div>
    `;
}
```

### Validation Criteria
- [ ] Renders nothing if sourceRef is null/undefined/empty (no errors)
- [ ] Chips wrap on narrow screens
- [ ] Each chip has appropriate color based on source
- [ ] Dashed border separates from other feedback content

---

# PART 3: SOURCE CITATION FORMAT STANDARDS

## 3.1 Citation Format by Source Type

### Paul Gill EPEMT
```
Format: Paul Gill EPEMT § [Chapter].[Section].[Subsection]
Example: Paul Gill EPEMT § 4.3.2
Full: Paul Gill EPEMT § 4.3.2 - Insulation Resistance Testing
```

### NETA Standards
```
ATS Format: NETA ATS-2025 § [Section] or Table [Number]
Example: NETA ATS-2025 Table 100.18

MTS Format: NETA MTS-2023 § [Section] or Table [Number]
Example: NETA MTS-2023 § 7.3.2

ETT Format: NETA ETT-2022 [Section]
Example: NETA ETT-2022 Level III KSA
```

### IEEE Standards
```
Format: IEEE [Number]-[Year] § [Section]
Example: IEEE 43-2013 § 12.2
Example: IEEE C57.104-2019 § 5.1

Common Standards:
- IEEE 43 (Motor Insulation)
- IEEE 81 (Ground Testing)
- IEEE 142 (Grounding - Green Book)
- IEEE 399 (Power System Analysis - Brown Book)
- IEEE 400.x (Cable Testing)
- IEEE 519 (Harmonics)
- IEEE 1584 (Arc Flash)
- IEEE C37.x (Circuit Breakers)
- IEEE C57.x (Transformers)
```

### NFPA
```
Format: NFPA [Number]-[Year] § [Article].[Section]
Example: NFPA 70E-2024 § 130.5(C)
Example: NFPA 70-2023 Article 250
```

---

# PART 4: DELIVERABLE SPECIFICATIONS

## 4.1 Required Files

| # | Filename | Location | Purpose |
|---|----------|----------|---------|
| 1 | `STUDY-GUIDE-TEMPLATE-v2.html` | `Resources/Templates/` | Complete HTML template with all CSS inline |
| 2 | `STUDY-GUIDE-TEMPLATE-v2.md` | `Resources/Templates/` | Markdown specification document |
| 3 | `QUESTION-SCHEMA-v2.md` | `Development/Templates/` | JSON schema documentation |
| 4 | `SOURCE-CITATION-GUIDE.md` | `Development/Templates/` | Citation format reference |

## 4.2 Files to Update

| Filename | Location | Changes |
|----------|----------|---------|
| `STAGING-FRAMEWORK-FOR-AI.md` | `Development/NETA-3/` | Add v2 question format with sourceRef |
| `ASSEMBLY-STANDARD.md` | `Development/NETA-3/` | Add source rendering section |

---

## 4.3 Acceptance Criteria Checklist

### Study Guide Template v2.html
- [ ] Self-contained (all CSS inline, no external dependencies)
- [ ] Opens correctly in browser with no errors
- [ ] Source panel renders with 6 source tag classes
- [ ] Level badges show with correct colors and states
- [ ] Why It Matters section has 3-part impact grid
- [ ] Level Preview section complete
- [ ] Responsive: works on 375px mobile width
- [ ] All CSS variables defined in :root
- [ ] Comments mark each major section

### Question Schema v2.md
- [ ] All fields documented with types
- [ ] Required vs optional clearly marked
- [ ] Validation rules specified
- [ ] Example questions with all fields
- [ ] renderSourceChips() function provided
- [ ] Null handling documented

### Source Citation Guide
- [ ] All 6 source types documented
- [ ] Correct format for each source
- [ ] Real examples (actual Paul Gill chapters, IEEE numbers)
- [ ] Common standards listed with numbers

### Updated Documentation
- [ ] STAGING-FRAMEWORK shows v2 question format
- [ ] ASSEMBLY-STANDARD includes source rendering step
- [ ] Cross-references point to new templates

---

# PART 5: ANTI-PATTERNS TO AVOID

## ❌ Don't Do This

| Anti-Pattern | Why It's Wrong | Do This Instead |
|--------------|----------------|-----------------|
| External CSS files | Breaks offline use | All CSS inline in `<style>` |
| Hardcoded colors | Inconsistent theming | Use CSS variables |
| Missing null checks | JavaScript errors | Always check `if (sourceRef && sourceRef.length)` |
| Fake citations | Undermines credibility | Use real Paul Gill sections, real IEEE numbers |
| Fixed widths | Breaks mobile | Use flexbox/grid, max-width |
| Missing comments | Hard to maintain | Comment each major section |
| Line-count targets | v1.x thinking | Focus on dimension coverage |

---

# PART 6: EXAMPLE IMPLEMENTATIONS

## 6.1 Complete Source Panel Example

```html
<aside class="sources-panel">
    <h4>📚 Authoritative Sources</h4>
    <p class="sources-intro">This guide references these industry standards:</p>
    <ul class="source-list">
        <li>
            <span class="source-tag source-gill">Paul Gill</span>
            <span class="source-detail">EPEMT § 4.3 - Transformer Insulation Testing</span>
        </li>
        <li>
            <span class="source-tag source-neta">NETA</span>
            <span class="source-detail">ATS-2025 Table 100.1 - Transformer Tests</span>
        </li>
        <li>
            <span class="source-tag source-ieee">IEEE</span>
            <span class="source-detail">C57.12.90-2021 § 10 - Insulation Power Factor</span>
        </li>
        <li>
            <span class="source-tag source-ieee">IEEE</span>
            <span class="source-detail">C57.104-2019 § 5 - DGA Interpretation</span>
        </li>
    </ul>
</aside>
```

## 6.2 Complete Question Object Example

```javascript
{
    id: 14,
    question: "During VLF testing of a 15kV XLPE cable, the measured tan delta at 1.5 U₀ is 25% higher than at 1.0 U₀. This 'tip-up' indicates:",
    options: [
        "A) Normal cable behavior within IEEE 400.2 limits",
        "B) Water tree contamination requiring further investigation",
        "C) Improper test connections causing measurement error",
        "D) Cable overheating during the test"
    ],
    correct: 1,
    explanation: "Tan delta tip-up (increase with voltage) is a key indicator of water tree contamination in XLPE cables. Water trees become more conductive under higher electric stress, causing increased dielectric losses. IEEE 400.2 provides tip-up criteria: >25% increase from 1.0 U₀ to 1.5 U₀ warrants investigation.",
    whyMatters: "Water trees in MV cables can progress to electrical trees and cause in-service failures. Early detection through VLF tan delta allows planned replacement before catastrophic failure, which could cause extended outages, safety hazards, and costly emergency repairs.",
    commonMistake: "Confusing tan delta magnitude with tip-up. A cable can have low absolute tan delta but still show concerning tip-up, indicating localized degradation that bulk measurements miss.",
    guideRef: {
        file: "25-Cable-Testing-Modern.html",
        title: "Modern Cable Testing Methods"
    },
    sourceRef: [
        { source: "Paul Gill EPEMT", section: "§ 6.4.2", topic: "VLF Tan Delta Testing" },
        { source: "IEEE 400.2", section: "§ 6.3", topic: "VLF-TD Interpretation" },
        { source: "NETA ATS 2025", section: "Table 100.12", topic: "Cable Test Acceptance" }
    ],
    levelTag: "III",
    ksa: "CT-042",
    difficulty: "advanced"
}
```

---

*Framework Version: 2.0*
*Created: December 22, 2025*
*Governs: All NETA study guide and practice test templates*
*Reference: MASTER-STANDARDS.md v2.0, CONTENT-QUALITY-STANDARDS-v2.md*
