# Study Guide Specification
## Content and Format Requirements for NETA ETT Study Guides
### Version 1.0 | December 19, 2025

---

## Purpose

This specification defines requirements for NETA ETT study guides across all certification levels. Following this spec ensures consistent quality, appropriate depth progression, and effective learning outcomes.

---

## Quick Reference: Requirements by Level

| Requirement | Level II | Level III | Level IV |
|-------------|----------|-----------|----------|
| Minimum Lines | 400 | 600 | 800 |
| NETA ATS References | Required | Required | Required |
| IEEE References | Optional | Required | Required |
| Worked Calculations | Basic | Intermediate | Advanced |
| Troubleshooting | Basic | Decision trees | System analysis |
| Level Badges | Single | II + III | II + III + IV |

---

## File Structure

### Naming Convention
```
##-Topic-Name-Guide.html
```
- Two-digit prefix for ordering
- Descriptive topic name (use hyphens)
- Always ends with `-Guide.html`

### Location
```
NETA-[X]/03-Study-Guides/
```

---

## HTML Structure

### Required Sections

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>[Topic] Study Guide | NETA Level [X]</title>
    <style>/* CSS */</style>
</head>
<body>
    <!-- 1. Header -->
    <header>
        <h1>[Full Topic Title]</h1>
        <div class="level-badges">
            <span class="badge level-2">Level II</span>
            <span class="badge level-3">Level III</span>
        </div>
        <div class="ksa-coverage">
            KSAs: [list covered KSA codes]
        </div>
    </header>
    
    <!-- 2. Table of Contents -->
    <nav class="toc">
        <h2>Contents</h2>
        <ul>
            <li><a href="#section-1">Section 1 Title</a></li>
            <li><a href="#section-2">Section 2 Title</a></li>
            <!-- ... -->
        </ul>
    </nav>
    
    <!-- 3. Learning Objectives -->
    <section class="objectives">
        <h2>🎯 Learning Objectives</h2>
        <p>After completing this guide, you will be able to:</p>
        <ul>
            <li>Objective 1</li>
            <li>Objective 2</li>
        </ul>
    </section>
    
    <!-- 4. Content Sections -->
    <section id="section-1">
        <h2>Section 1: [Title]</h2>
        <!-- Content with level badges where appropriate -->
    </section>
    
    <!-- 5. Worked Examples -->
    <section class="examples">
        <h2>📝 Worked Examples</h2>
        <!-- Step-by-step calculation examples -->
    </section>
    
    <!-- 6. Common Mistakes -->
    <section class="common-mistakes">
        <h2>⚠️ Common Mistakes</h2>
        <!-- Typical errors and how to avoid them -->
    </section>
    
    <!-- 7. Field Tips -->
    <section class="field-tips">
        <h2>🔧 Field Tips</h2>
        <!-- Practical advice from real-world experience -->
    </section>
    
    <!-- 8. Key Takeaways -->
    <section class="takeaways">
        <h2>✅ Key Takeaways</h2>
        <ul>
            <li>Most important point 1</li>
            <li>Most important point 2</li>
        </ul>
    </section>
    
    <!-- 9. References -->
    <footer class="references">
        <h2>📚 References</h2>
        <ul>
            <li>NETA ATS-2025, Section X.X</li>
            <li>IEEE Standard XXXX-YYYY</li>
        </ul>
    </footer>
    
    <!-- 10. Navigation -->
    <nav class="guide-nav">
        <a href="[previous-guide].html">← Previous</a>
        <a href="00-Study-Guide-Index.html">Index</a>
        <a href="[next-guide].html">Next →</a>
    </nav>
</body>
</html>
```

---

## Content Depth by Level

### Level II Content
**Focus:** Foundational concepts, basic procedures, equipment identification

| Element | Requirement |
|---------|-------------|
| Concepts | Define terms, explain "what" and basic "why" |
| Procedures | Step-by-step with safety emphasis |
| Calculations | Single-step, direct formula application |
| Equipment | Identification, basic operation |
| Standards | NETA ATS acceptance criteria |
| Troubleshooting | Basic symptom → cause → action |

**Example depth:**
> "Insulation resistance testing uses a megohmmeter to apply DC voltage and measure resistance. The test verifies insulation integrity. Acceptable values per NETA ATS Table 100.1 are based on equipment voltage rating."

### Level III Content
**Focus:** Advanced procedures, calculations, analysis, troubleshooting

| Element | Requirement |
|---------|-------------|
| Concepts | Explain "why" in depth, underlying physics |
| Procedures | NETA ATS procedures with variations for conditions |
| Calculations | Multi-step, unit conversions, temperature corrections |
| Equipment | Selection criteria, limitations, calibration |
| Standards | IEEE standards, multiple NETA ATS tables |
| Troubleshooting | Decision trees, diagnostic sequences |

**Example depth:**
> "Polarization Index (PI) measures the ratio of 10-minute to 1-minute insulation resistance readings. This ratio indicates insulation condition:
> - PI > 4.0: Excellent (dry, clean insulation)
> - PI 2.0-4.0: Good (acceptable for service)
> - PI < 2.0: Marginal (investigate further)
> 
> Temperature affects readings—apply correction factor per IEEE 43-2013, Table 3. For every 10°C above reference, resistance approximately halves."

### Level IV Content
**Focus:** System-level analysis, coordination, commissioning, advanced diagnostics

| Element | Requirement |
|---------|-------------|
| Concepts | System interactions, protection philosophy |
| Procedures | Commissioning sequences, integrated testing |
| Calculations | Fault current, coordination, symmetrical components |
| Equipment | System-wide testing strategies |
| Standards | Multiple IEEE, NETA, NFPA integration |
| Troubleshooting | Root cause analysis, failure mode diagnostics |

**Example depth:**
> "Transformer differential protection (87T) must account for:
> 1. CT ratio mismatch compensation
> 2. Tap changer position effects on current ratios
> 3. Magnetizing inrush (2nd harmonic restraint)
> 4. CT saturation during external faults
>
> Slope settings balance sensitivity vs security. Typical settings:
> - Slope 1: 25-30% (low current region)
> - Slope 2: 50-60% (high current region)
> - Minimum pickup: 0.3-0.5 pu"

---

## Level Badge System

### Usage
Apply badges to indicate content appropriate for each certification level.

```html
<div class="level-badge level-2">Level II Foundation</div>
<div class="level-badge level-3">Level III</div>
<div class="level-badge level-4">Level IV Preview</div>
```

### Progression Within Single Guide
Structure content to build from foundational to advanced:

```html
<section>
    <h2>Insulation Testing</h2>
    
    <div class="level-section" data-level="2">
        <span class="badge">Level II</span>
        <p>Basic megohmmeter operation and pass/fail criteria...</p>
    </div>
    
    <div class="level-section" data-level="3">
        <span class="badge">Level III</span>
        <p>PI/DAR analysis, temperature correction, trending...</p>
    </div>
    
    <div class="level-section" data-level="4">
        <span class="badge">Level IV Preview</span>
        <p>Partial discharge correlation, online monitoring integration...</p>
    </div>
</section>
```

---

## KSA Coverage

### Mapping to ETT-2022
Each guide must document which KSAs (Knowledge, Skills, Abilities) it addresses:

```html
<!-- In header or metadata -->
<div class="ksa-coverage">
    <h3>KSAs Covered</h3>
    <ul>
        <li>II.D.1 - Employ methods for basic insulation tests</li>
        <li>II.D.2 - Analyze results from basic insulation tests</li>
        <li>III.B.2 - Transformer insulation testing</li>
    </ul>
</div>
```

### Crosswalk Reference
Verify coverage against `Resources/Crosswalk/KSA-MASTER-CROSSWALK.md`

---

## Required Sections

### Worked Examples (Required for calculation-heavy topics)

```html
<div class="worked-example">
    <h3>Example: Calculate Three-Phase Power</h3>
    
    <div class="problem">
        <strong>Given:</strong> 480V, 52A, PF = 0.85
        <br><strong>Find:</strong> Real power (kW)
    </div>
    
    <div class="solution">
        <strong>Step 1:</strong> Write the formula
        <div class="formula">P = √3 × V × I × PF</div>
        
        <strong>Step 2:</strong> Substitute values
        <div class="formula">P = 1.732 × 480 × 52 × 0.85</div>
        
        <strong>Step 3:</strong> Calculate
        <div class="formula">P = 36,752 W = <strong>36.75 kW</strong></div>
    </div>
    
    <div class="check">
        <strong>Reasonableness check:</strong> ~37 kW for a 52A three-phase load at 480V is reasonable for a medium motor or panel.
    </div>
</div>
```

### Common Mistakes (Required)

```html
<section class="common-mistakes">
    <h2>⚠️ Common Mistakes</h2>
    
    <div class="mistake">
        <h4>❌ Using line voltage in single-phase formula</h4>
        <p><strong>Wrong:</strong> P = 480 × 52 = 24,960W</p>
        <p><strong>Right:</strong> For three-phase, must include √3 factor</p>
        <p><strong>Remember:</strong> Three-phase power = √3 × V_L × I_L × PF</p>
    </div>
    
    <div class="mistake">
        <h4>❌ Forgetting power factor</h4>
        <p>Apparent power (VA) ≠ Real power (W) unless PF = 1.0</p>
    </div>
</section>
```

### Field Tips (Required)

```html
<section class="field-tips">
    <h2>🔧 Field Tips</h2>
    
    <div class="tip">
        <h4>Temperature Matters</h4>
        <p>Insulation resistance drops ~50% for every 10°C rise. 
        Always record ambient temperature and apply correction 
        factors when comparing to baseline readings.</p>
    </div>
    
    <div class="tip">
        <h4>Guard Terminal Use</h4>
        <p>Use the guard terminal to eliminate surface leakage 
        when testing bushings or cable terminations. Connect 
        guard to any surface you want to exclude from measurement.</p>
    </div>
</section>
```

---

## Visual Elements

### Diagrams
- Include diagrams for complex concepts
- SVG preferred for scalability
- Label all components clearly
- Use consistent color coding

### Tables
- Use for acceptance criteria, comparison data
- Include units in headers
- Reference source (e.g., "Per NETA ATS Table 100.1")

### Formulas
- Display prominently with proper formatting
- Define all variables
- Show units
- Distinguish "PROVIDED on exam" vs "MEMORIZE"

```html
<div class="formula-box">
    <div class="formula">P = √3 × V<sub>L</sub> × I<sub>L</sub> × PF</div>
    <div class="variables">
        <p>Where:</p>
        <ul>
            <li>P = Real power (watts)</li>
            <li>V<sub>L</sub> = Line voltage (volts)</li>
            <li>I<sub>L</sub> = Line current (amperes)</li>
            <li>PF = Power factor (decimal)</li>
        </ul>
    </div>
    <div class="exam-note">📋 Formula PROVIDED on NETA exam</div>
</div>
```

---

## Quality Checklist

Before committing any study guide:

### Content
- [ ] Meets minimum line count for level
- [ ] Learning objectives stated
- [ ] Content organized from basic → advanced
- [ ] Level badges applied appropriately
- [ ] KSA coverage documented
- [ ] Worked examples included (if applicable)
- [ ] Common mistakes section present
- [ ] Field tips section present
- [ ] Key takeaways summarized
- [ ] References listed (NETA ATS, IEEE, etc.)

### Technical Accuracy
- [ ] Formulas verified against source documents
- [ ] Acceptance criteria match current NETA ATS
- [ ] IEEE standard citations are current versions
- [ ] No contradictions with other guides

### Format
- [ ] Table of contents present and accurate
- [ ] Navigation links work
- [ ] Follows naming convention
- [ ] In correct folder
- [ ] Browser tested

---

## Cross-References

### Related Guides
Link to related content where helpful:

```html
<div class="see-also">
    <h4>📖 Related Guides</h4>
    <ul>
        <li><a href="08-Insulation-Resistance-Testing-Guide.html">
            Insulation Resistance Testing</a> - Foundation for this topic</li>
        <li><a href="11-Transformer-Oil-Analysis-Guide.html">
            Transformer Oil Analysis</a> - Complementary testing</li>
    </ul>
</div>
```

### Practice Tests
Link to related practice tests:

```html
<div class="practice-link">
    <h4>📝 Test Your Knowledge</h4>
    <a href="../04-Practice-Tests/11-Transformer-Testing-Practice.html">
        Take the Transformer Testing Practice Test
    </a>
</div>
```

---

## Enhancement Guidelines

### When Enhancing Existing Guides

1. **Read entire current content first**
2. **Identify gaps against this spec:**
   - Missing sections?
   - Insufficient depth for level?
   - Missing level badges?
   - No KSA mapping?
3. **Check line count vs. minimum**
4. **Propose specific additions** (don't just expand everything)
5. **Preserve existing good content**
6. **Add Level IV Preview if Level III guide**

### Priority Order for Missing Content
1. Common Mistakes section (high exam value)
2. Worked Examples (learning effectiveness)
3. Field Tips (differentiates from textbooks)
4. Level badges (helps users navigate)
5. KSA mapping (ensures coverage)

---

## Template Location

Master template available at:
```
Development/Shared/Templates/study-guide-template.html
```

*(To be created as part of infrastructure completion)*

---

*This specification is authoritative for study guide creation. Update version number when modifying.*
