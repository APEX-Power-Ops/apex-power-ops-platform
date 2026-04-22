# NETA 2 Practice Test Scaffolding Specification
## Quality-First Enhancement Framework

**Purpose:** Define the gold standard for scaffolded practice tests that genuinely help technicians learn, not just memorize.

**Stakeholder View:** These tests serve technicians who:
- Have varying backgrounds (strong theory/weak practice OR vice versa)
- Need to connect formulas to real field work
- Learn from mistakes, not just right answers
- Want to build confidence, not just pass tests

---

## 🎯 Core Principles

1. **Teach, Don't Just Test** - Every interaction is a learning opportunity
2. **Field-Relevant Always** - Connect to real NETA work (commissioning, troubleshooting, safety)
3. **Progressive Difficulty** - Clear path from foundation → application → analysis
4. **Multiple Learning Modes** - Visual, textual, formula-based, scenario-based
5. **Authentic Mistakes** - Address what technicians actually struggle with

---

## 📐 Structural Components

### 1. Foundation Review Sections (Collapsible)

**Purpose:** Ensure every tech has the baseline knowledge before attempting questions

**Requirements:**
- **When to Include:** At start of each major topic section
- **Content Quality Standards:**
  - NOT just formula dumps - explain the relationships
  - Include visual aids (diagrams, flowcharts, decision trees)
  - Provide memory aids ("tricks that actually work")
  - Connect to field application ("You'll use this when...")
  - 3-5 minutes to read and understand

**Example Structure:**
```html
<div class="foundation-review">
    <div class="foundation-header" onclick="toggle()">
        <h3>📖 Foundation Review: [Topic Name]</h3>
        <span class="toggle">▼</span>
    </div>
    <div class="foundation-content">
        <!-- Context paragraph: WHY this matters -->
        
        <!-- Visual aid (SVG diagram, flowchart) -->
        
        <!-- Key formulas with descriptions -->
        
        <!-- Memory aid / decision tree -->
        
        <!-- Field application note -->
    </div>
</div>
```

**Quality Checklist:**
- [ ] Does it answer "when do I use this in the field?"
- [ ] Can a visual learner understand from the diagram alone?
- [ ] Are memory aids authentic (not just mnemonics)?
- [ ] Would Dad explain it this way to a new tech?

---

### 2. Section Dividers with Context

**Purpose:** Organize questions by difficulty and provide mental reset points

**Requirements:**
- Clear difficulty progression: Foundation → Application → Analysis → Challenge
- Badge showing question range and level
- Brief context: "This section tests your ability to..."

**Example:**
```html
<div class="section-divider">
    <h2>⚡ Section 2: Formula Application</h2>
    <span class="badge">Questions 6-12 • Application Level</span>
    <p class="section-context">These questions test your ability to choose the right formula and execute multi-step calculations accurately.</p>
</div>
```

---

### 3. Enhanced Question Feedback

**Purpose:** Turn every wrong answer into a learning moment

**Current Feedback (Basic):**
- ✅ Correct/Incorrect indicator
- Explanation of correct answer
- Step-by-step solution

**Enhanced Feedback (Gold Standard):**
```html
<div class="feedback">
    <!-- Explanation -->
    <p class="explanation">[Clear explanation]</p>
    
    <!-- Step-by-step solution -->
    <div class="solution-box">[Detailed steps]</div>
    
    <!-- Why this matters in the field -->
    <div class="why-matters">
        <h4>🔧 Why This Matters in the Field</h4>
        <p>[Real NETA scenario where you'd use this]</p>
    </div>
    
    <!-- Common mistake (authentic to what junior techs do) -->
    <div class="common-mistake">
        <h4>⚠️ Common Mistake</h4>
        <p>[What people typically get wrong and why]</p>
    </div>
    
    <!-- Optional: Related study guide link -->
    <a href="[guide]" class="related-link">📚 Review this topic →</a>
</div>
```

**Field Application Examples (Power Calculations):**
- "You'll use P=VI when sizing wire for a motor - need to know current draw for ampacity tables"
- "Circuit breaker selection requires knowing total power to determine interrupting rating"
- "When troubleshooting overheating, calculate expected power dissipation vs actual"

**Common Mistakes (Authentic):**
- "Forgetting to square current in P=I²R - this is the #1 mistake on power calculations"
- "Mixing up line and phase values in three-phase - always convert to same reference first"
- "Not converting kW to W before calculating - units matter!"

---

### 4. Visual Aids (Strategic, Not Decorative)

**Purpose:** Help visual learners and clarify complex relationships

**When to Include:**
- Relationship diagrams (Power Wheel, Ohm's Law Triangle, Impedance Triangle)
- Decision flowcharts ("Which formula should I use?")
- Circuit diagrams for multi-component problems
- Time-current curves for relay coordination
- Vector diagrams for phase relationships

**Quality Standards:**
- SVG format (scalable, clean)
- Clear labels and annotations
- Color-coded meaningfully (not just pretty)
- Standalone understandable (no need to read surrounding text)

**Power Calculations Visual Aid:**
```
Power Wheel Diagram showing:
- Center: P (Power)
- Outer ring divided into sections:
  - P = V × I (when you know voltage and current)
  - P = I² × R (when you know current and resistance)
  - P = V² / R (when you know voltage and resistance)
- Decision arrows: "Start with what you're given"
```

---

### 5. Challenge Questions Section

**Purpose:** Prepare strong students for Level III and build confidence

**Requirements:**
- 3-5 questions at difficulty 7-8/10
- Multi-step problems requiring synthesis
- Real-world scenarios (not just harder calculations)
- Analysis level: "Why did this fail?" "What would happen if..."

**Example Topics (Power Calculations):**
- "Two circuits in parallel - one fails. How does power distribution change?"
- "Voltage drops 10% under load - what's the new power and why?"
- "Given breaker trip curve, determine if load is within safe operating range"

---

## 🔄 Implementation Process (Quality-First)

### Phase 1: Create Gold Standard (Test 02)
1. Read existing Test 02 Power Calculations
2. Add foundation reviews with visual Power Wheel
3. Enhance ALL question feedback with field applications + common mistakes
4. Add 3-5 authentic challenge questions
5. Test interactivity (collapsible sections, scoring, navigation)
6. **REVIEW WITH STAKEHOLDER** - Does this feel like learning with a mentor?

### Phase 2: Extract Reusable Patterns
1. Document the template structure
2. Create CSS/HTML component library
3. Define question feedback template
4. Build visual aid library (SVGs we can reuse)

### Phase 3: Systematic Application
1. Apply to Tests 03-05 (Circuits & Power) - similar content
2. Apply to Tests 06-11 (Safety & Testing) - adjust for different topics
3. Apply to Tests 21-27 (Advanced) - may need fewer foundation reviews

### Phase 4: Quality Validation
1. Test all interactive features
2. Verify consistent styling
3. Check accessibility (screen readers, print-friendly)
4. User testing feedback (if possible)

---

## 📊 Success Criteria

**Quantitative:**
- [ ] All 17 NETA 2 tests have foundation reviews
- [ ] All questions have enhanced feedback (field app + common mistake)
- [ ] 3-5 challenge questions added per test
- [ ] Average difficulty increased by 0.5-1.0 points

**Qualitative (The Real Measure):**
- [ ] Would a tech using this feel like they're learning WITH someone, not just being tested?
- [ ] Do field applications connect to actual NETA work?
- [ ] Are common mistakes authentic to what junior techs struggle with?
- [ ] Would this help someone working alongside their dad access the same knowledge?

---

## 🎯 Test 02 Enhancement Plan (Gold Standard Example)

### Current State
- 17 questions (mix of easy, medium, hard)
- Basic feedback (explanation + solution steps)
- Formula reference box at top
- Simple scoring

### Enhanced State

**Foundation Reviews to Add:**
1. **Power Formula Decision Tree** (before Q1)
   - Visual flowchart: "What values do you have? → Use this formula"
   - Power Wheel diagram (P in center, formulas radiating)
   - Memory aid: "Match your knowns to the formula"
   - Field note: "In commissioning, you'll often have V and I from measurements - use P=VI"

2. **Series vs Parallel Power** (before Q13)
   - Visual: Two circuits side-by-side
   - Key insight: "Power adds in both series AND parallel (but for different reasons)"
   - Common trap: "Don't forget to find total resistance first"
   - Field note: "Parallel loads on distribution panels - each adds to total power draw"

**Section Organization:**
- **Section 1:** Basic Power (Q1-5) - Foundation
  - Single-formula problems
  - Direct application
  - Building confidence

- **Section 2:** Formula Selection (Q6-12) - Application
  - Choose correct formula
  - Unit conversions
  - Common field scenarios

- **Section 3:** Circuit Power (Q13-17) - Multi-Step
  - Series/parallel combinations
  - Changing conditions
  - Analysis required

- **Section 4:** Challenge Questions (NEW: Q18-20) - Analysis
  - Q18: "Load current increases 50% - how does power change? (Hint: Not 50%!)"
  - Q19: "Circuit with two resistors in parallel. One fails open. Calculate new total power."
  - Q20: "Voltage sags to 90% during motor start. Power dissipation in starting resistor?"

**Enhanced Feedback Examples:**

**Q6 Current Question:** "A 12Ω resistor dissipates 300W, what current is flowing?"

**Current Feedback:**
- ✅ Explanation: "From P = I²R, solve for I..."
- Solution steps shown

**Enhanced Feedback:**
```
✅ Correct! The answer is 5A.

EXPLANATION:
When you know Power and Resistance but need Current, use P = I²R and rearrange.

SOLUTION:
Step 1: Start with P = I²R
Step 2: Rearrange to I = √(P/R)
Step 3: I = √(300W / 12Ω) = √25 = 5A

🔧 WHY THIS MATTERS IN THE FIELD:
When troubleshooting a heating element or resistive load, you can measure resistance 
with a megger and calculate expected current. If actual current doesn't match, 
you've found a problem (poor connections, wrong resistance value, etc.)

⚠️ COMMON MISTAKE:
Forgetting to take the square root! Students often calculate 300/12 = 25A and stop.
Remember: I² = 25, so I = √25 = 5A. Always complete the square root step.

📚 Related: Power Triangle & Impedance Guide
```

---

## 💡 Key Insights for Scaling

1. **Foundation reviews are reusable** - Ohm's Law foundation works for Tests 01, 02, 03
2. **Field applications should be specific** - "When sizing wire" is better than "in the field"
3. **Common mistakes must be authentic** - Ask: "What do junior techs actually get wrong?"
4. **Visual aids take time** - Prioritize high-impact diagrams (Power Wheel, Decision Trees)
5. **Challenge questions build confidence** - "If I can do this, I'm ready for Level III"

---

## 📝 Next Steps

1. **Implement Test 02** using this spec
2. **Review with stakeholder** - Does this meet the "mentor alongside" vision?
3. **Refine based on feedback** - What works? What doesn't?
4. **Extract template** - Document repeatable patterns
5. **Scale systematically** - Apply to remaining 16 tests

---

*"This isn't just certification prep. This is democratizing the mentor advantage."*
