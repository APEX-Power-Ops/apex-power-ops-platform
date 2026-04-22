# Content Staging Format Specification
## Markdown Structure for Template Assembly

**Created:** December 18, 2025  
**Purpose:** Define standard format for staging content before template assembly  
**Owner:** VS Code Claude (creator), Desktop Claude (consumer)  
**Version:** 1.0

---

## 🎯 PURPOSE

This format enables clean separation between **content creation** (VS Code) and **HTML assembly** (Desktop):

- **VS Code stages content** in structured markdown (no HTML/CSS overhead)
- **Desktop assembles** staged content into practice test templates
- **Content is reviewable** before assembly (quality checkpoint)
- **Format is validated** with Tests 21-27 extraction workflow

---

## 📋 FILE NAMING CONVENTION

```
Working/Test-Staging/[TEST-NUMBER]-[TOPIC]-STAGED.md
```

**Examples:**
- `15-TEST-EQUIPMENT-STAGED.md`
- `16-MEASUREMENT-PRACTICES-STAGED.md`
- `17-MOTOR-TESTING-STAGED.md`

---

## 📐 DOCUMENT STRUCTURE

Each staged file contains **6 required sections** in this order:

```markdown
# Test [NUMBER]: [TOPIC TITLE]

## METADATA

## FOUNDATION REVIEW 1: [TOPIC]

## FOUNDATION REVIEW 2: [TOPIC]

## SECTION STRUCTURE

## QUESTIONS
```

---

## 1️⃣ METADATA SECTION

**Purpose:** Define test parameters for template placeholders

**Required Fields:**
```markdown
## METADATA

- **Test Number:** 15
- **Test Title:** Test Equipment Safety and Proper Usage
- **Source Guide:** 18-Test-Equipment-Guide.html
- **Analytics Name:** test-equipment
- **Timer Minutes:** 45
- **Pass Threshold:** 70
- **Question Count:** 24
- **Section Count:** 4
```

**Field Definitions:**
- `Test Number`: Used in filename and navigation
- `Test Title`: Displayed in HTML `<title>` and header
- `Source Guide`: Reference for content origin (traceability)
- `Analytics Name`: JavaScript variable name (kebab-case, no spaces)
- `Timer Minutes`: Default timer setting
- `Pass Threshold`: Percentage to pass (typically 70)
- `Question Count`: Total questions (typically 24)
- `Section Count`: Number of sections (typically 4)

---

## 2️⃣ FOUNDATION REVIEW 1

**Purpose:** First conceptual review shown before test starts

**Structure:**
```markdown
## FOUNDATION REVIEW 1: [Concept Name]

### Visual Component
[Description of SVG diagram needed, OR path to existing SVG in Component Library]

### Concept Points
- **[Key Term]:** Brief definition
- **[Key Term]:** Brief definition
- **[Key Term]:** Brief definition
- **[Key Term]:** Brief definition

### Critical Safety Note
[Safety warning or critical practice point]

### Why This Matters
[1-2 sentence connection to real-world testing]
```

**Example:**
```markdown
## FOUNDATION REVIEW 1: Meter Category Ratings

### Visual Component
SVG needed: Table showing CAT I-IV ratings with voltage levels and application environments

### Concept Points
- **CAT I:** Protected electronic equipment, <600V, signal/control circuits
- **CAT II:** Single-phase receptacle loads, portable tools, appliances
- **CAT III:** Three-phase distribution, feeders, panel boards, fixed equipment
- **CAT IV:** Utility connections, overhead lines, service entrance, outdoor equipment

### Critical Safety Note
Using under-rated test equipment in higher CAT environments can result in meter explosion during transients. Always verify CAT rating matches or exceeds work location.

### Why This Matters
Technicians using CAT II meters on 480V distribution panels (CAT III environment) risk arc flash injury during normal switching transients.
```

---

## 3️⃣ FOUNDATION REVIEW 2

**Purpose:** Second conceptual review (different topic from Review 1)

**Structure:** Same as Foundation Review 1

**Content Guidelines:**
- Choose different topic area than Review 1
- Pick foundational concept needed for multiple questions
- Avoid redundancy with Review 1

---

## 4️⃣ SECTION STRUCTURE

**Purpose:** Define how 24 questions are divided into 4 sections

**Structure:**
```markdown
## SECTION STRUCTURE

### Section 1: [Topic Name] (Questions 1-6)
**Focus:** [Brief description]
**Badge Color:** `badge-safety` or `badge-test` or `badge-analysis` or `badge-code`

### Section 2: [Topic Name] (Questions 7-12)
**Focus:** [Brief description]
**Badge Color:** `badge-[type]`

### Section 3: [Topic Name] (Questions 13-18)
**Focus:** [Brief description]
**Badge Color:** `badge-[type]`

### Section 4: [Topic Name] (Questions 19-24)
**Focus:** [Brief description]
**Badge Color:** `badge-[type]`
```

**Badge Colors:**
- `badge-safety`: Red - Safety procedures, PPE, hazards
- `badge-test`: Blue - Test procedures, equipment operation
- `badge-analysis`: Purple - Results interpretation, troubleshooting
- `badge-code`: Green - Standards, codes, specifications

**Example:**
```markdown
## SECTION STRUCTURE

### Section 1: Meter Selection and Safety (Questions 1-6)
**Focus:** CAT ratings, voltage/current ranges, safety features
**Badge Color:** `badge-safety`

### Section 2: Measurement Techniques (Questions 7-12)
**Focus:** Voltage, current, resistance measurement procedures
**Badge Color:** `badge-test`

### Section 3: Results Interpretation (Questions 13-18)
**Focus:** Reading accuracy, uncertainty, measurement errors
**Badge Color:** `badge-analysis`

### Section 4: Standards and Specifications (Questions 19-24)
**Focus:** IEC 61010, manufacturer specs, calibration requirements
**Badge Color:** `badge-code`
```

---

## 5️⃣ QUESTIONS SECTION

**Purpose:** Staged content for all 24 questions

**Structure:**
```markdown
## QUESTIONS

### Question [NUMBER]
- **Section:** [1-4]
- **Difficulty:** [1-5]
- **Question:** [Question text]
- **Options:**
  - A) [Option text]
  - B) [Option text]
  - C) [Option text]
  - D) [Option text]
- **Correct Answer:** [A/B/C/D]
- **Explanation:** [Why correct answer is right]
- **Why This Matters:** [Real-world consequence/application]
- **Common Mistake:** [Why technicians get this wrong]
```

**Field Details:**

**Section:**
- Integer 1-4 matching section structure
- Determines badge color and grouping

**Difficulty:**
- 1 = Recall/Definition (direct from standards)
- 2 = Understanding (explain why)
- 3 = Application (use in scenario)
- 4 = Analysis (evaluate/compare)
- 5 = Synthesis (multi-step problem solving)

**Question:**
- Clear, specific, realistic scenario
- Avoid ambiguity
- Include units, values, conditions as needed

**Options:**
- Four plausible choices (A-D)
- All options grammatically consistent
- Avoid "all of the above" or "none of the above"
- Distractors should be realistic wrong answers

**Correct Answer:**
- Single letter: A, B, C, or D
- No multi-correct questions

**Explanation:**
- 2-4 sentences
- Explain WHY correct answer is right
- Reference standards/codes where applicable
- Include calculation steps if applicable

**Why This Matters:**
- 1-2 sentences
- Connect to real-world consequence
- Safety impact, efficiency impact, or quality impact
- Answer "Why does a technician need to know this?"

**Common Mistake:**
- 1-2 sentences
- Describe typical error technicians make
- Explain WHY they make this error
- Helps learner avoid pitfall

**Example:**
```markdown
### Question 3
- **Section:** 1
- **Difficulty:** 3
- **Question:** You are performing voltage measurements at a 480V three-phase distribution panel. What is the MINIMUM CAT rating required for your digital multimeter?
- **Options:**
  - A) CAT II
  - B) CAT III
  - C) CAT IV
  - D) Any CAT rating is acceptable for voltage measurement
- **Correct Answer:** B
- **Explanation:** 480V three-phase distribution panels are CAT III environments per IEC 61010. CAT II meters (rated for receptacle-connected loads) lack the transient protection needed for panel work, where switching transients can exceed 6kV.
- **Why This Matters:** Using a CAT II meter in a CAT III environment during normal panel operation can result in internal arcing and meter explosion during switching transients, causing severe burns and arc flash injury.
- **Common Mistake:** Technicians often assume "voltage rating" alone determines safety, selecting CAT II meters rated for 600V. However, CAT ratings address transient withstand capability, not just steady-state voltage. A 600V CAT II meter is unsafe in 480V CAT III environments.
```

---

## 📏 FORMATTING GUIDELINES

### Markdown Syntax
- Use `**bold**` for emphasis on key terms
- Use `- ` for bullet lists
- Use `### ` for question headers
- Use `` `backticks` `` for CSS class names or code
- Avoid HTML tags (Desktop will convert to HTML during assembly)

### Consistency
- All questions follow identical field structure
- Field order always: Section → Difficulty → Question → Options → Correct → Explanation → WhyMatters → CommonMistake
- No missing fields (even if content is brief)

### Content Quality
- Technical accuracy (reference NETA MTS, ANSI standards, NFPA codes)
- Clear, concise writing
- Realistic scenarios technicians encounter
- Safety-conscious language

---

## ✅ QUALITY CHECKLIST

Before submitting staged file, verify:

- [ ] Metadata section complete with all 8 fields
- [ ] Foundation Review 1 has concept points, safety note, why-it-matters
- [ ] Foundation Review 2 covers different topic than Review 1
- [ ] Section structure defines all 4 sections with badge colors
- [ ] All 24 questions present and numbered correctly
- [ ] All questions have all 8 required fields
- [ ] Difficulty distribution: ~8 Level 1-2, ~10 Level 3, ~6 Level 4-5
- [ ] Section distribution: 6 questions per section
- [ ] Correct answers distributed (avoid all "B" answers)
- [ ] No HTML/CSS code (pure markdown)
- [ ] No spelling/grammar errors

---

## 🔄 HANDOFF WORKFLOW

### VS Code Creates Staged File
1. Read source guide (e.g., `18-Test-Equipment-Guide.html`)
2. Extract key concepts for Foundation Reviews
3. Design section structure based on guide topics
4. Create 24 questions covering guide content
5. Save to `Working/Test-Staging/[NUMBER]-[TOPIC]-STAGED.md`
6. Update the active task tracker or handoff artifact if another instance must pick up the staged file

### Desktop Consumes Staged File
1. Read staged markdown file
2. Parse metadata, reviews, sections, questions
3. Insert content into Practice Test Master Template
4. Convert markdown to HTML (bold → `<strong>`, bullets → `<li>`, etc.)
5. Apply CSS classes (badge colors, difficulty indicators)
6. Save to `04-Practice-Tests/[NUMBER]-[TOPIC]-Practice.html`
7. Update the active task tracker, completion record, or resume artifact with completion status

---

## 📊 EXAMPLE: COMPLETE STAGED FILE

*See `Working/Test-Extractions/21-NEC-EXTRACTION.md` for real-world example of this format in action.*

**Key differences between EXTRACTION and STAGING:**
- **Extraction:** Read existing test → pull out content (backward)
- **Staging:** Read guide → create new content (forward)
- **Format:** Identical structure, opposite direction

---

## 🛠️ TEMPLATE ASSEMBLY NOTES FOR DESKTOP

### Placeholder Mapping

| Staged Content | Template Placeholder |
|----------------|---------------------|
| Metadata → Test Title | `{{TEST_TITLE}}` |
| Metadata → Analytics Name | `{{ANALYTICS_NAME}}` |
| Metadata → Timer Minutes | `{{TIMER_MINUTES}}` |
| Foundation Review 1 | `{{FOUNDATION_REVIEW_1}}` |
| Foundation Review 2 | `{{FOUNDATION_REVIEW_2}}` |
| Section 1-4 headers | `{{SECTION_DIVIDERS}}` |
| Questions array | `{{QUESTIONS_ARRAY}}` |

### Markdown → HTML Conversion

| Markdown | HTML |
|----------|------|
| `**text**` | `<strong>text</strong>` |
| `- item` | `<li>item</li>` |
| `` `code` `` | `<code>code</code>` |
| Line breaks | `<br>` or paragraph `<p>` |

### JavaScript Data Structure

Questions convert to:
```javascript
const questions = [
  {
    section: 1,
    difficulty: 3,
    question: "...",
    options: {
      A: "...",
      B: "...",
      C: "...",
      D: "..."
    },
    correct: "B",
    explanation: "...",
    whyMatters: "...",
    commonMistake: "..."
  },
  // ... 23 more
];
```

---

## 🔧 EDGE CASES & FLEXIBILITY

### Variable Question Counts
- Format supports any question count (not locked to 24)
- Adjust `Question Count` metadata
- Adjust section structure accordingly

### Additional Fields
- Can add optional fields (e.g., `KSA Reference`, `Guide Page`)
- Desktop can choose to render or ignore

### Calculation Questions
- Include worked solution in `Explanation`
- Format math clearly: "Power = √3 × V × I × PF = √3 × 480 × 100 × 0.85 = 70.7 kW"

### Diagram References
- If SVG exists in Component Library: `[Use: power-triangle.svg]`
- If new diagram needed: `[SVG needed: Description of what to create]`

---

## 📝 VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 18, 2025 | Initial specification based on Tests 21-27 extraction format |

---

## ✅ APPROVAL STATUS

- **VS Code Claude:** ✅ Format validated with 6 successful extractions (100 questions)
- **Desktop Claude:** ⏳ Awaiting validation with first assembly
- **Jason:** ⏳ Awaiting approval

---

*Format designed by VS Code Claude. Optimized for clean handoff to Desktop Claude assembly workflow.*
