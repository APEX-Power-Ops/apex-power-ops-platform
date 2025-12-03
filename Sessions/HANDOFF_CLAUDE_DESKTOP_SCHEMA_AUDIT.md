# Handoff: Schema Audit Task for Claude Desktop

**Created:** December 3, 2025  
**From:** VS Code Claude  
**To:** Claude Desktop  
**Priority:** P1

---

## 🧠 Your Role First

Before starting, read `C:\RESA_Power_Build\Sessions\CLAUDE_NOTES.md` - especially the "Your Role" section. You're a stakeholder here, not just an executor. If you see a better approach to this audit, say so.

---

## 🎯 Task: Schema Comparison Audit

Compare the **current clean build** (v1.0.0.5) against the **old working build** (v1.5.1.3) to identify all gaps that need to be addressed.

### Why This Matters
We rebuilt on a fresh environment (org7bdbc942). The old environment had working Revenue Recognition flows and more complete schema. We need to know exactly what's missing before building flows.

---

## 📁 Files to Review

### Current Build (What We Have)
```
C:\RESA_Power_Build\Solution_Exports\v1.0.0.5\
├── customizations.xml      ← Current schema definition
├── solution.xml            ← Version info
└── Workflows\
    └── EstimatorImport-*.json
```

### Old Build (Reference - What Worked)
```
C:\RESA_Power_Build\Solution_Exports\Archive\v1.5.1.3\
├── customizations.xml
├── Entities\
│   └── [entity folders]\Entity.xml    ← Field definitions per table
└── Workflows\
    └── RevenueRecognitiononApparatusCompletion-*.json  ← Working flow logic
```

---

## 📋 Deliverables

### 1. Schema Gap Report
Create: `C:\RESA_Power_Build\Documentation\03_Progress_Tracking\SCHEMA_GAP_REPORT_v1.0.0.5_vs_v1.5.1.3.md`

**Include:**

#### A. Table Comparison
| Table | In v1.0.0.5? | In v1.5.1.3? | Notes |
|-------|--------------|--------------|-------|

#### B. Field-by-Field Comparison (Key Tables Only)
Focus on these tables:
- `cr950_apparatus` - Needs completion trigger fields
- `cr950_scopelabordetail` - Rate calculation fields
- `cr950_apparatusrevenue` - Revenue record fields
- `cr950_scopefinancialsummary` - Rollup fields
- `cr950_projectfinancialsummary` - Rollup fields

For each: What fields exist in old but not new?

#### C. Lookup/Relationship Gaps
What relationships exist in v1.5.1.3 that we need to recreate?

#### D. Rollup/Calculated Field Definitions
Extract the formulas from v1.5.1.3 for any rollup or calculated fields we need to recreate.

#### E. Global Option Sets
Are there any choice fields that use global option sets we need?

---

### 2. Flow Logic Extraction
Create: `C:\RESA_Power_Build\Documentation\02_Build_Guides\REVENUE_FLOW_LOGIC_REFERENCE.md`

From `RevenueRecognitiononApparatusCompletion-*.json`, extract:
- Trigger conditions
- Data retrieval steps (what it queries)
- Calculation logic
- Record creation steps
- Field mappings (old field names → document what they do)

This will be the blueprint for rebuilding the flow with new schema names.

---

### 3. Session Protocol Feedback (Optional)
Review the new `Sessions\` folder structure and provide feedback:
- `SESSION_PROTOCOL.md` - Is it clear?
- `CLAUDE_NOTES.md` - Useful format?
- `HANDOFF.md` - Template work well?
- Suggestions for improvement?

---

## ⚠️ Important Context

### Schema Name Changes
The naming conventions changed between versions:

| Concept | Old (v1.5.1.3) | New (v1.0.0.5) |
|---------|----------------|----------------|
| Scope table | `cr950_projectscope` | `cr950_scope` |
| Scope EntitySet | `cr950_projectscopes` | `cr950_scopes` |
| ScopeLaborDetail EntitySet | `cr950_scopelabordetailses` | `cr950_scopelabordetails` |

When documenting gaps, note both the old and new names where applicable.

### What's Already Done
- 3 financial tables created (ApparatusRevenue, ScopeFinancialSummary, ProjectFinancialSummary)
- Apparatus trigger fields added (cr950_completion_status, cr950_delayhours)
- Basic table structure in place

### What's Known to Be Missing
- 7 lookup fields (must add via Power Apps UI)
- 12+ rollup fields
- 3 Power Automate flows
- Possibly calculated fields

---

## 📍 Reference Documents

| Document | Purpose |
|----------|---------|
| `Sessions/CLAUDE_NOTES.md` | Quick context, your role |
| `Documentation/03_Progress_Tracking/BUILD_STATUS_2025-12-02.md` | Current build status |
| `Documentation/03_Progress_Tracking/SESSION_DECISIONS_2025-12-02.md` | Why decisions were made |
| `Documentation/02_Build_Guides/REVENUE_RECOGNITION_BUILD_SPEC.md` | Architecture spec |

---

## ✅ Acceptance Criteria

- [ ] Schema gap report created with table, field, and relationship comparisons
- [ ] Flow logic extracted and documented with clear step-by-step breakdown
- [ ] Old field names mapped to their purpose (so we can map to new names)
- [ ] Rollup/calculated field formulas captured
- [ ] Any blockers or questions documented

---

## 🔄 When Complete

1. Update `Sessions/CLAUDE_NOTES.md` with your findings summary
2. Update `Sessions/HANDOFF.md` to mark this task complete
3. Note any follow-up tasks that VS Code Claude should handle

---

*If you run out of context space, prioritize the Schema Gap Report. The flow logic can be a separate session if needed.*
