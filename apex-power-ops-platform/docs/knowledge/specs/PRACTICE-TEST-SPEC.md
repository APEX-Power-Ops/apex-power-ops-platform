# Practice Test Specification
## Gold Standard Content and Format Requirements
### Version 1.0 | December 19, 2025

---

## Purpose

This specification defines requirements for NETA ETT practice tests across all levels. Following this spec ensures consistent quality, proper exam alignment, and effective learning outcomes.

---

## Quick Reference: Gold Standard Minimums

| Requirement | Minimum | Gold Standard |
|-------------|---------|---------------|
| Total Questions | 20 | 24+ |
| Line Count | 600 | 1000+ |
| Sections | 2 | 4+ |
| Timer | Required | Required |
| Analytics | Optional | Required |
| Enhanced Feedback | Optional | Required |
| Foundation Review | Optional | Required |

---

## File Structure

### Naming Convention
```
##-Topic-Name-Practice.html
```
- Two-digit prefix for ordering
- Descriptive topic name (use hyphens)
- Always ends with `-Practice.html`

### Location
```
NETA-[X]/04-Practice-Tests/
```

---

## HTML Structure

### Required Sections

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>[Topic] Practice Test | NETA Level [X]</title>
    <style>/* CSS */</style>
</head>
<body>
    <!-- 1. Header with Timer -->
    <header>
        <h1>[Test Title]</h1>
        <div id="timer">Time: 00:00</div>
        <div id="progress">Question 1 of 24</div>
    </header>
    
    <!-- 2. Foundation Review (Gold Standard) -->
    <section class="foundation-review">
        <h2>📚 Foundation Review</h2>
        <!-- Key concepts, formulas, reminders -->
    </section>
    
    <!-- 3. Question Sections -->
    <section class="question-section" data-section="1">
        <h2>Section 1: [Topic Focus]</h2>
        <!-- Questions 1-6 -->
    </section>
    
    <section class="question-section" data-section="2">
        <h2>Section 2: [Topic Focus]</h2>
        <!-- Questions 7-12 -->
    </section>
    
    <!-- Continue sections... -->
    
    <!-- 4. Results Display -->
    <section id="results" class="hidden">
        <h2>Test Results</h2>
        <div id="score"></div>
        <div id="pass-fail"></div>
        <div id="answer-review"></div>
    </section>
    
    <!-- 5. JavaScript -->
    <script>
        // Analytics config
        // Timer functionality
        // Scoring logic
        // Question data
    </script>
</body>
</html>
```

---

## Question Requirements

### Question Data Structure
```javascript
const questions = [
    {
        id: 1,
        section: 1,
        question: "Clear, specific question text?",
        options: {
            A: "Plausible but incorrect option",
            B: "Correct answer with proper detail",
            C: "Common misconception option",
            D: "Another plausible distractor"
        },
        correct: "B",
        explanation: "Why B is correct with reference to source.",
        whyMatters: "Real-world relevance of this knowledge.",
        commonMistake: "Why technicians often choose wrong answers.",
        ksa: "II.B.2",  // KSA reference
        difficulty: "standard"  // easy, standard, challenge
    },
    // ... more questions
];
```

### Question Quality Criteria

| Element | Requirement |
|---------|-------------|
| Question Stem | Clear, unambiguous, complete scenario |
| Options | 4 plausible choices, only 1 clearly correct |
| Correct Answer | Matches authoritative source (NETA ATS, IEEE, etc.) |
| Explanation | States why correct AND why others are wrong |
| whyMatters | Connects to field work or exam importance |
| commonMistake | Identifies typical error pattern |
| KSA Tag | Maps to ANSI/NETA ETT-2022 knowledge area |

### Question Distribution (24-question test)

| Section | Questions | Focus |
|---------|-----------|-------|
| 1 | Q1-6 | Foundational concepts |
| 2 | Q7-12 | Core procedures |
| 3 | Q13-18 | Calculations & analysis |
| 4 | Q19-24 | Advanced applications & challenge |

### Difficulty Progression
- **Easy (20%)**: Direct recall, basic definitions
- **Standard (50%)**: Application, single-step calculations
- **Challenge (30%)**: Multi-step problems, synthesis, judgment calls

---

## Foundation Review Section

### Purpose
Prime the learner's memory before testing, reducing frustration and improving learning.

### Required Elements

```html
<section class="foundation-review">
    <h2>📚 Foundation Review</h2>
    
    <!-- Key Formulas -->
    <div class="formula-card">
        <h3>Essential Formulas</h3>
        <ul>
            <li>V = IR (Ohm's Law)</li>
            <li>P = VI = I²R = V²/R</li>
        </ul>
    </div>
    
    <!-- Critical Concepts -->
    <div class="concept-card">
        <h3>Remember</h3>
        <ul>
            <li>Key concept 1</li>
            <li>Key concept 2</li>
        </ul>
    </div>
    
    <!-- Common Pitfalls -->
    <div class="warning-card">
        <h3>⚠️ Watch Out For</h3>
        <ul>
            <li>Common mistake 1</li>
            <li>Common mistake 2</li>
        </ul>
    </div>
</section>
```

---

## Timer Functionality

### Requirements
- Countdown timer visible at all times
- Default time based on question count (~2 min/question)
- Warning at 5 minutes remaining
- Auto-submit when time expires (or prompt user)

### Standard Times
| Questions | Time Limit |
|-----------|-----------|
| 20 | 40 minutes |
| 24 | 50 minutes |
| 30 | 60 minutes |
| 75 (mock exam) | 150 minutes |

### Implementation
```javascript
const quizTimer = {
    totalSeconds: 50 * 60,  // 50 minutes
    remaining: 50 * 60,
    interval: null,
    
    start() {
        this.interval = setInterval(() => {
            this.remaining--;
            this.updateDisplay();
            if (this.remaining <= 0) {
                this.stop();
                submitQuiz();
            }
        }, 1000);
    },
    
    stop() {
        clearInterval(this.interval);
    },
    
    updateDisplay() {
        const min = Math.floor(this.remaining / 60);
        const sec = this.remaining % 60;
        document.getElementById('timer').textContent = 
            `Time: ${min}:${sec.toString().padStart(2, '0')}`;
    }
};
```

---

## Scoring & Results

### Pass/Fail Threshold
- **Standard:** 70% (17/24, 14/20)
- **Mock Exam:** 70% (53/75)

### Results Display
```html
<section id="results">
    <h2>Test Complete!</h2>
    
    <div class="score-display">
        <span class="score">18/24</span>
        <span class="percentage">75%</span>
        <span class="status pass">PASS ✓</span>
    </div>
    
    <div class="section-breakdown">
        <h3>Performance by Section</h3>
        <!-- Section-by-section scores -->
    </div>
    
    <div class="answer-review">
        <h3>Review All Questions</h3>
        <!-- Each question with user answer, correct answer, explanation -->
    </div>
    
    <div class="recommendations">
        <h3>Study Recommendations</h3>
        <!-- Based on weak areas -->
    </div>
</section>
```

---

## Analytics Integration

### Configuration
```javascript
const ANALYTICS_CONFIG = {
    WEB_APP_URL: 'https://script.google.com/macros/s/[DEPLOYMENT_ID]/exec',
    ENABLE_TRACKING: true,
    TEST_NAME: 'Test 01: Ohm\'s Law Practice',
    LEVEL: 2
};
```

### Data Captured
| Field | Description |
|-------|-------------|
| sessionId | Unique session identifier |
| testName | Name of practice test |
| startTime | When test began |
| endTime | When test submitted |
| totalTime | Duration in seconds |
| score | Raw score (correct/total) |
| percentage | Score as percentage |
| passed | Boolean pass/fail |
| questionTimes | Time spent on each question |
| answers | User's answer for each question |

### Implementation
```javascript
function submitResults() {
    if (!ANALYTICS_CONFIG.ENABLE_TRACKING) return;
    
    const data = {
        sessionId: getOrCreateSessionId(),
        testName: ANALYTICS_CONFIG.TEST_NAME,
        timestamp: new Date().toISOString(),
        score: calculateScore(),
        // ... other fields
    };
    
    fetch(ANALYTICS_CONFIG.WEB_APP_URL, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}
```

---

## Level-Specific Requirements

### Level II Tests
- Focus on foundational concepts and basic procedures
- Calculations should be single-step or simple multi-step
- Reference NETA ATS acceptance criteria
- Include visual identification (equipment, diagrams)

### Level III Tests
- Include complex calculations with intermediate steps
- Add troubleshooting scenarios
- Include NETA ATS procedure sequences
- Reference IEEE standards for technical depth
- Add "Level IV Preview" questions (1-2 per test)

### Level IV Tests
- System-level analysis required
- Coordination and protection schemes
- Commissioning integration scenarios
- Reference multiple standards (NETA, IEEE, NFPA)
- Include case study style questions

---

## NETA Exam Domain Alignment

### Level II Domains (per ETT-2022)
| Domain | Weight | Focus |
|--------|--------|-------|
| I. Safety | 15% | NFPA 70E, LOTO, PPE, boundaries |
| II. Fundamentals & Theory | 25% | Ohm's law, power, three-phase, measurements |
| III. Component Testing | 55% | Transformers, breakers, cables, relays, motors |
| IV. Systems & Commissioning | 5% | Functional tests, documentation |

### Test-to-Domain Mapping
Each test should document which domain sections it covers:
```javascript
const testMetadata = {
    testName: "Transformer Testing Practice",
    domains: ["III.B.1", "III.B.2", "III.B.3"],
    ksaCoverage: ["III.B.1.a", "III.B.1.b", "III.B.2.a"],
    references: ["NETA ATS Table 100.4", "IEEE C57.12.90"]
};
```

---

## CSS Classes Reference

### Question States
```css
.question { }
.question.current { }
.question.answered { }
.question.correct { }
.question.incorrect { }
.question.skipped { }
```

### Feedback Display
```css
.explanation { }
.why-matters { }
.common-mistake { }
.correct-indicator { }
.incorrect-indicator { }
```

### Foundation Review
```css
.foundation-review { }
.formula-card { }
.concept-card { }
.warning-card { }
```

---

## Validation Checklist

Before committing any practice test:

### Content
- [ ] 24+ questions (or justified exception)
- [ ] 4 sections minimum
- [ ] Foundation review section present
- [ ] All questions have complete data (explanation, whyMatters, commonMistake)
- [ ] KSA tags assigned to each question
- [ ] Difficulty distribution appropriate

### Functionality
- [ ] Timer works correctly
- [ ] Progress indicator updates
- [ ] Scoring calculates correctly
- [ ] Pass/fail displays correctly
- [ ] Answer review shows all questions
- [ ] No JavaScript console errors

### Format
- [ ] 1000+ lines (Gold Standard)
- [ ] Follows naming convention
- [ ] In correct folder

---

## Template Location

Master template available at:
```
Development/Shared/Templates/practice-test-template.html
```

*(To be created as part of infrastructure completion)*

---

*This specification is authoritative for practice test creation. Update version number when modifying.*
