# Schema Gap Report: v1.0.0.5 vs v1.5.1.3

**Created:** December 3, 2025  
**Author:** Claude Desktop (Schema Audit Task)  
**Status:** Layer 1-3 Complete | Layer 4-5 Pending

---

## Executive Summary

| Metric | v1.5.1.3 (Old) | v1.0.0.5 (New) | Gap |
|--------|----------------|----------------|-----|
| **Tables** | 20 | 12 | -8 tables |
| **Fields (mapped tables)** | 469 | 431 | -38 fields |
| **Calculated Fields** | 18 | 0 | **-18 critical** |
| **Rollup Fields** | 47 | 0 | **-47 critical** |
| **Missing Lookups** | - | - | **7 required** |

### Critical Gaps Blocking Flow Development
1. **7 lookup fields** must be added manually via Power Apps UI
2. **65 calculated/rollup fields** need to be recreated
3. **8 tables** missing (evaluate need before recreating)

---

## Part A: Table Comparison

### Tables in Both Versions (Name Mapping)

| Display Name | Old Schema Name | New Schema Name | Old Fields | New Fields | Delta |
|--------------|-----------------|-----------------|------------|------------|-------|
| Apparatus | cr950_apparatus | cr950_apparatus | 51 | 49 | -2 |
| Apparatus Revenue | cr950_apparatusrevenue | cr950_apparatusrevenue | 39 | 29 | **-10** |
| Client | cr950_client | cr950_client | 43 | 29 | **-14** |
| Estimator | cr950_estimator | cr950_estimator | 40 | 37 | -3 |
| Project | cr950_projects | **cr950_project** | 57 | 37 | **-20** |
| Project Financial Summary | cr950_projectfinancialsummary | cr950_projectfinancialsummary | 30 | 32 | +2 |
| Scope | cr950_projectscope | **cr950_scope** | 46 | 37 | **-9** |
| Scope Financial Summary | cr950_scopefinancialsummary | cr950_scopefinancialsummary | 30 | 32 | +2 |
| Scope Labor Detail | cr950_scopelabordetails | **cr950_scopelabordetail** | 50 | 52 | +2 |
| Site | cr950_site | cr950_site | 39 | 30 | -9 |
| Task | cr950_tasks | **cr950_task** | 43 | 41 | -2 |

### Tables Only in OLD (Missing from New) - 8 Tables

| Table | Display Name | Fields | Recommendation |
|-------|--------------|--------|----------------|
| cr950_apparatussubmission | Apparatus Submission | 25 | ⚠️ Evaluate - workflow support |
| cr950_apparatustestchecklist | Apparatus Test Checklist | 25 | ⚠️ Evaluate - NETA compliance |
| cr950_apparatustypemaster | Apparatus Type Master | 28 | ✅ **Needed** - standard hours lookup |
| cr950_businessunit | Business Unit | 33 | ✅ **Needed** - multi-location support |
| cr950_employee | Employee | 40 | ⚠️ Evaluate - resource management |
| cr950_equipment | Equipment | 42 | ⚠️ Evaluate - asset tracking |
| cr950_netatesttemplate | NETA Test Template | 27 | ⚠️ Evaluate - test form support |
| cr950_quote | Quote | 60 | ⚠️ Evaluate - sales pipeline |
| cr950_resourceassignment | Resource Assignment | 35 | ⚠️ Evaluate - scheduling |

### Tables Only in NEW (Not in Old) - 1 Table

| Table | Display Name | Fields | Notes |
|-------|--------------|--------|-------|
| cr950_location | Location | 26 | New addition for location tracking |

---

## Part B: Priority Table Field Analysis

### B1. Apparatus Revenue (`cr950_apparatusrevenue`)

**Purpose:** Records revenue when apparatus completion is triggered

#### Missing Business Fields (from OLD)
| Field | Type | Purpose | Action Required |
|-------|------|---------|-----------------|
| cr950_apparatus | lookup | Link to source apparatus | **ADD via UI** |
| cr950_project | lookup | Link to project | **ADD via UI** |
| cr950_projectfinancialsummary | lookup | Link to project rollup | **ADD via UI** |
| cr950_scopefinancialsummary | lookup | Link to scope rollup | **ADD via UI** |
| cr950_scopelabordetail | lookup | Link to rate source | **ADD via UI** |
| cr950_apparatushours | decimal | Hours from apparatus | Rename: cr950_plannedhours |
| cr950_delays | decimal | Delay hours | Rename: cr950_delayhours ✓ |
| cr950_effectivelaborrate | money | Rate from ScopeLaborDetail | Rename: cr950_laborrateapplied ✓ |
| cr950_totalhours | decimal | CALC: Hours + Delays | **Need CALC field** |
| cr950_revenueamount | money | CALC: Hours × Rate | **Need CALC field** |
| cr950_revenue_record_id | string | Auto-generated ID | Optional |
| cr950_revenuerecognitiondate | datetime | When recognized | Rename: cr950_recognitiondate ✓ |

#### Field Name Mapping (Old → New Convention)
| Old Field | New Field | Status |
|-----------|-----------|--------|
| cr950_apparatushours | cr950_plannedhours | ✅ Exists |
| cr950_delays | cr950_delayhours | ✅ Exists |
| cr950_effectivelaborrate | cr950_laborrateapplied | ✅ Exists |
| cr950_revenuerecognitiondate | cr950_recognitiondate | ✅ Exists |
| cr950_totalhours | - | ❌ Need calculated |
| cr950_revenueamount | - | ❌ Need calculated |

### B2. Scope Labor Detail (`cr950_scopelabordetail`)

**Purpose:** Budget and rate configuration per scope

#### Field Name Mapping (Complete Redesign)
| Old Field | New Field | Status |
|-----------|-----------|--------|
| cr950_effectivelaborrate | cr950_scopelaboreffectiverate | ✅ Exists |
| cr950_onsitelabortotal | cr950_scopelaboronsitetotal | ✅ Exists |
| cr950_offsitelabortotal | cr950_scopelaboroffsitetotal | ✅ Exists |
| cr950_traveltotal | cr950_scopelabortraveltotal | ✅ Exists |
| cr950_outsideservicestotal | cr950_scopelaboroutsidetotal | ✅ Exists |
| cr950_total_apparatus_hours | cr950_scopelabortotalhours | ✅ Exists |
| cr950_projectscope_id | cr950_scopelaborscope | ✅ Exists |

**Assessment:** ScopeLaborDetail is well-covered in new version - just renamed fields.

### B3. Apparatus (`cr950_apparatus`)

**Purpose:** Equipment items being tested

#### Key Trigger Fields Status
| Field | Old Name | New Name | Status |
|-------|----------|----------|--------|
| Completion Status | cr950_completion_status | cr950_completion_status | ✅ Both |
| Date Completed | cr950_datecompleted | cr950_datecompleted | ✅ Both |
| Delay Hours | cr950_delays | cr950_delayhours | ✅ Renamed |

#### Missing Lookups (Naming Convention Changed)
| Old Lookup | New Lookup | Status |
|------------|------------|--------|
| cr950_project | cr950_apparatus_projectid | ✅ Exists |
| cr950_scope | cr950_apparatus_scopeid | ✅ Exists |
| cr950_task | cr950_apparatustask | ✅ Exists |

**Assessment:** Apparatus table is complete for trigger functionality.

### B4. Scope Financial Summary (`cr950_scopefinancialsummary`)

**Purpose:** Aggregated revenue metrics per scope

#### Missing Lookups
| Field | Type | Target | Action |
|-------|------|--------|--------|
| cr950_scope | lookup | cr950_scope | **ADD via UI** |

#### Missing Rollup Fields
| Field | Type | Formula Source |
|-------|------|----------------|
| cr950_apparatusrevenuecount | rollup | COUNT(ApparatusRevenue) |
| cr950_totalbillablehours | rollup | SUM(ApparatusRevenue.Hours) |
| cr950_totaldelayhours | rollup | SUM(ApparatusRevenue.Delays) |
| cr950_totalrevenuerecognized | rollup | SUM(ApparatusRevenue.Amount) WHERE Status=Recognized |
| cr950_totalrevenuepending | rollup | SUM(ApparatusRevenue.Amount) WHERE Status=Pending |
| cr950_averagelaborrate | rollup | AVG(ApparatusRevenue.Rate) |
| cr950_latestrevenuedate | rollup | MAX(ApparatusRevenue.RecognitionDate) |

### B5. Project Financial Summary (`cr950_projectfinancialsummary`)

**Purpose:** Aggregated revenue metrics per project

#### Missing Lookups
| Field | Type | Target | Action |
|-------|------|--------|--------|
| cr950_project | lookup | cr950_project | **ADD via UI** |

#### Missing Rollup Fields
Same pattern as Scope Financial Summary, rolling up from child ScopeFinancialSummary records.

---

## Part C: Missing Lookup Fields Summary (7 Total)

These must be added via Power Apps UI (Web API cannot create lookups):

| # | Table | Lookup Field | Target Table | Priority |
|---|-------|--------------|--------------|----------|
| 1 | ApparatusRevenue | Apparatus | cr950_apparatus | P1 - Flow |
| 2 | ApparatusRevenue | Project | cr950_project | P1 - Flow |
| 3 | ApparatusRevenue | ScopeLaborDetail | cr950_scopelabordetail | P1 - Flow |
| 4 | ApparatusRevenue | ScopeFinancialSummary | cr950_scopefinancialsummary | P2 - Rollup |
| 5 | ApparatusRevenue | ProjectFinancialSummary | cr950_projectfinancialsummary | P2 - Rollup |
| 6 | ScopeFinancialSummary | Scope | cr950_scope | P2 - Rollup |
| 7 | ProjectFinancialSummary | Project | cr950_project | P2 - Rollup |

**Note:** Lookups 1-3 are required for Revenue Recognition Flow. Lookups 4-7 are required for rollup aggregation.

---

## Part D: Calculated & Rollup Field Gaps

### D1. OLD Version - 65 Total Fields

#### Apparatus (2 calculated)
- `cr950_completed_hours` = CALC
- `cr950_remaining_hours` = CALC

#### ApparatusRevenue (3 calculated)
- `cr950_revenueamount` = Hours × EffectiveRate
- `cr950_revenueamount_base` = Base currency
- `cr950_totalhours` = Hours + Delays

#### ScopeLaborDetail (10 calculated)
- `cr950_effectivelaborrate` = Total ÷ Hours
- `cr950_onsitelaborrate` = OnsiteTotal ÷ Hours
- `cr950_offsitelaborrate` = OffsiteTotal ÷ Hours
- `cr950_travelrate` = TravelTotal ÷ Hours
- `cr950_outsideservicesrate` = OutsideTotal ÷ Hours
- (Plus 5 _base currency fields)

#### Project (14 fields: 1 calc, 13 rollup)
- `cr950_percent_complete` = CALC: CompletedCount ÷ TotalCount
- `cr950_total_apparatus_count` = ROLLUP COUNT
- `cr950_completed_apparatus_count` = ROLLUP COUNT WHERE Complete
- `cr950_total_apparatus_hours` = ROLLUP SUM
- `cr950_total_completed_hours` = ROLLUP SUM
- `cr950_total_actual_hours` = ROLLUP SUM
- `cr950_total_delays` = ROLLUP SUM
- `cr950_total_remaining_hours` = ROLLUP SUM
- `cr950_earliest/latest_actualstart` = ROLLUP MIN/MAX
- `cr950_earliest/latest_anticipatedstart` = ROLLUP MIN/MAX
- `cr950_earliest/latest_completiondate` = ROLLUP MIN/MAX

#### Scope (14 fields: 1 calc, 13 rollup)
Same pattern as Project, rolling up from Tasks/Apparatus.

#### Task (14 fields: 1 calc, 13 rollup)
Same pattern as Project, rolling up from Apparatus.

#### ScopeFinancialSummary (10 rollup)
- `cr950_apparatusrevenuecount` = COUNT
- `cr950_totalbillablehours` = SUM
- `cr950_totaldelayhours` = SUM
- `cr950_totalrevenuerecognized` = SUM (filtered)
- `cr950_totalrevenuepending` = SUM (filtered)
- `cr950_averagelaborrate` = AVG
- `cr950_latestrevenuedate` = MAX
- (Plus 3 _base currency fields)

#### ProjectFinancialSummary (10 rollup)
Same pattern as ScopeFinancialSummary.

### D2. NEW Version - 0 Fields

**All 65 calculated/rollup fields need to be recreated.**

---

## Part E: Global Option Sets

### Choice Fields Identified in v1.5.1.3
| Field | Table | Values |
|-------|-------|--------|
| cr950_completion_status | Apparatus | 1=Planned, 2=In Progress, 3=Complete |
| cr950_datasource | Multiple | Data import source |
| cr950_syncstatus | Multiple | Sync tracking |
| cr950_revenuerevenuestatus | ApparatusRevenue | Pending, Recognized, Adjusted |

**Note:** Need to verify if these are global option sets or local choices.

---

## Actionable Task List

### Immediate (Before Flow Development)

| # | Task | Owner | Estimated Time |
|---|------|-------|----------------|
| 1 | Add 3 P1 lookups to ApparatusRevenue | Jason (UI) | 15 min |
| 2 | Add 4 P2 lookups to Financial tables | Jason (UI) | 20 min |
| 3 | Create 3 calculated fields on ApparatusRevenue | Jason (UI) | 30 min |

### Short-Term (After Lookups)

| # | Task | Owner | Estimated Time |
|---|------|-------|----------------|
| 4 | Extract flow logic from v1.5.1.3 (Layer 4) | Claude | 1 session |
| 5 | Create calculated fields on ScopeLaborDetail | Jason (UI) | 45 min |
| 6 | Create rollup fields on Financial tables | Jason (UI) | 1 hour |

### Medium-Term (System Completion)

| # | Task | Owner | Estimated Time |
|---|------|-------|----------------|
| 7 | Create rollup fields on Project/Scope/Task | Jason (UI) | 2 hours |
| 8 | Evaluate 8 missing tables for inclusion | Jason/Claude | 1 session |
| 9 | Build Revenue Recognition Flow | Claude/Jason | 2-3 hours |

---

## Follow-Up Tasks for Next Session

### Layer 4: Flow Logic Extraction (Separate Document)
Create `REVENUE_FLOW_LOGIC_REFERENCE.md` with:
- Trigger conditions from `RevenueRecognitiononApparatusCompletion-*.json`
- Step-by-step workflow breakdown
- Field mappings (old names → purposes)
- Calculation logic

### Layer 5: Formula Extraction (Separate Document)
Create `CALCULATED_ROLLUP_FORMULAS.md` with:
- Exact formulas from XML for each calculated field
- Rollup configurations and filters
- Dependency order for creation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-03 | Initial audit - Layers 1-3 complete |

---

*This document should be updated as gaps are addressed.*
