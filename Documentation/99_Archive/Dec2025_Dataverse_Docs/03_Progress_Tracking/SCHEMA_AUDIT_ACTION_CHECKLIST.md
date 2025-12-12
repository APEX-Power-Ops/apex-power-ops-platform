# Schema Audit Action Checklist

**Created:** December 3, 2025  
**Reference:** SCHEMA_GAP_REPORT_v1.0.0.5_vs_v1.5.1.3.md

---

## 🎯 Critical Path to Revenue Flow

These tasks must be completed IN ORDER before the Revenue Recognition Flow can work:

### Step 1: Add P1 Lookups (15 min)
**Location:** make.powerapps.com → Tables → [Table] → Columns → + New Column

- [ ] **ApparatusRevenue → Apparatus**
  - Column name: `Apparatus`
  - Type: Lookup
  - Related table: `cr950_apparatus`
  
- [ ] **ApparatusRevenue → Project**
  - Column name: `Project`
  - Type: Lookup
  - Related table: `cr950_project`
  
- [ ] **ApparatusRevenue → ScopeLaborDetail**
  - Column name: `Scope Labor Detail`
  - Type: Lookup
  - Related table: `cr950_scopelabordetail`

### Step 2: Add Calculated Fields to ApparatusRevenue (30 min)

- [ ] **Total Hours** (calculated)
  - Formula: `Planned Hours + Delay Hours`
  - Field name: `cr950_totalhours`
  
- [ ] **Revenue Amount** (calculated)
  - Formula: `Planned Hours × Labor Rate Applied`
  - Field name: `cr950_revenueamount`

### Step 3: Extract Flow Logic (Claude Task)
- [ ] Parse `RevenueRecognitiononApparatusCompletion-*.json`
- [ ] Document trigger conditions
- [ ] Document field mappings with new names
- [ ] Create `REVENUE_FLOW_LOGIC_REFERENCE.md`

### Step 4: Build Revenue Recognition Flow
- [ ] Create trigger on Apparatus completion status change
- [ ] Look up ScopeLaborDetail for rate
- [ ] Create ApparatusRevenue record
- [ ] Test with sample data

---

## 📋 P2 Lookups (For Rollup Aggregation)

These enable the financial summary rollups but aren't blocking flow development:

- [ ] **ApparatusRevenue → ScopeFinancialSummary**
- [ ] **ApparatusRevenue → ProjectFinancialSummary**
- [ ] **ScopeFinancialSummary → Scope**
- [ ] **ProjectFinancialSummary → Project**

---

## 📊 Rollup Fields (65 Total - Can Be Phased)

### Phase 1: ApparatusRevenue Calculated (3 fields)
Required for revenue calculation.

### Phase 2: ScopeLaborDetail Calculated (10 fields)
Rate calculations - may already work if renamed correctly.

### Phase 3: Financial Summary Rollups (20 fields)
Aggregate revenue metrics.

### Phase 4: Operational Rollups (32 fields)
Project/Scope/Task progress tracking.

---

## ⚠️ Decisions Needed

1. **8 Missing Tables** - Which to recreate?
   - `cr950_apparatustypemaster` - Likely needed (standard hours)
   - `cr950_businessunit` - Likely needed (multi-location)
   - Others - Evaluate based on current workflow needs

2. **Sync/Audit Fields** - Keep or discard?
   - Old version had: `datasource`, `syncstatus`, `lastsyncdate`, `isdeleted`
   - New version omits these - intentional simplification?

---

## ✅ Verification Checklist

After adding lookups, verify they work:

```
# Test query via MCP
query_dataverse({
  entityName: "cr950_apparatusrevenues",
  select: "cr950_name,_cr950_apparatus_value,_cr950_project_value",
  top: 1
})
```

Expected: No errors, lookup fields visible.

---

*Check off items as completed. Update CLAUDE_NOTES.md when done.*
