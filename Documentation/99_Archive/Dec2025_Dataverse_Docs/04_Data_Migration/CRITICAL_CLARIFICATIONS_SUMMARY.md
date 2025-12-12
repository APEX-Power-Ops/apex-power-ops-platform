# RESA Power Project Tracker - Critical Clarifications Summary

**Date:** November 10, 2025  
**Version:** 1.1  
**Document Type:** Clarification Record  
**Status:** Resolved and Documented

---

## PURPOSE

This document captures three critical clarifications identified during the project modernization conversation that required updates across all project documentation:

1. Tasks table implementation status
2. NETA Standards architecture (ATS vs MTS)
3. Apparatus_Type_Master table structure updates

These clarifications have been incorporated into all relevant project documents.

---

## CLARIFICATION 1: TASKS TABLE IMMEDIATE IMPLEMENTATION

### Initial Misunderstanding:
- Tasks table was initially marked as "deferred" or lower priority
- Assumption was that tasks would be imported from Excel estimators
- Unclear whether tasks would be created in Phase 1 or later phases

### Clarified Reality:
✅ **Tasks Table is IMMEDIATE IMPLEMENTATION**
- Build Tasks table in Phase 1 alongside Projects, Scopes, and Apparatus
- Tasks are created **manually by Project Managers** in Power Apps
- Tasks are **NOT imported from Excel** estimators

### Reasoning:
- Excel estimators have no task-level structure to import from
- Tasks are a Power Apps organizational construct
- Tasks group apparatus into logical work packages for technician assignment
- Technicians need organized task lists to work effectively from day one

### Implementation Impact:
- Build Tasks table in initial Dataverse setup (Phase 1)
- Skip tasks during Excel import process
- Train PMs on manual task creation workflow:
  1. Review imported scopes and apparatus
  2. Create tasks to group similar apparatus
  3. Assign tasks to technicians
  4. Monitor task completion and progress

### Documentation Updates:
- ✅ Master Build Specification v1.1 - Tasks table marked as "Immediate Implementation"
- ✅ Build Checklist - Tasks table included in Phase 1 build steps
- ✅ Implementation Checklist - Added "Manual Task Creation" workflow section
- ✅ CSV Templates - Tasks template marked as "REFERENCE ONLY, NOT FOR IMPORT"

---

## CLARIFICATION 2: NETA STANDARDS ARCHITECTURE (ATS vs MTS)

### Initial Misunderstanding:
- Single NETA_Spec_Reference field in Apparatus_Type_Master
- Single Default_Labor_Hours field
- Assumption was one standard across all projects
- Unclear how to handle different testing standards

### Clarified Reality:
✅ **Two Distinct NETA Standards with Different Applications**

#### NETA ATS (Acceptance Testing Specifications):
- **Purpose:** New installations and commissioning work
- **Context:** Equipment being tested for the first time after installation
- **Testing Scope:** More comprehensive, includes manufacturer's tests plus acceptance criteria
- **Labor Hours:** Typically higher due to comprehensive testing requirements
- **Current Version:** NETA 2025 standards

#### NETA MTS (Maintenance Testing Specifications):
- **Purpose:** Existing equipment and ongoing maintenance testing
- **Context:** Periodic testing of equipment already in service
- **Testing Scope:** Focused on operational verification and maintenance needs
- **Labor Hours:** Typically lower due to reduced testing scope
- **Current Version:** NETA 2023 standards

### Architecture Implementation:

#### Scope Level (Cell C3 in Excel):
- Each scope sheet has Cell C3 (merged cell) containing "ATS" or "MTS"
- This determines which NETA standard the entire scope follows
- **NO mixing within a scope** - all apparatus in that scope use the same standard
- Data validation in Excel pulls from appropriate columns based on C3 value

#### Apparatus_Type_Master Table (Updated Structure):

**REMOVED Fields:**
- ❌ NETA_Spec_Reference (single column)
- ❌ Default_Labor_Hours (single column)

**ADDED Fields:**
- ✅ NETA_ATS_Section_Reference (Text, 50 chars)
- ✅ NETA_MTS_Section_Reference (Text, 50 chars)
- ✅ NETA_ATS_Labor_Hours (Decimal)
- ✅ NETA_MTS_Labor_Hours (Decimal)

#### Scopes Table (New Field):
- ✅ NETA_Standard (Choice: "ATS" or "MTS", Required, Default: "ATS")
- Determines which specifications apply to all tasks and apparatus in scope
- Sourced from Excel estimator Cell C3 during import

#### Inheritance Flow:
```
Scope.NETA_Standard = "ATS"
    ↓
Tasks inherit ATS context
    ↓
Apparatus pulls NETA_ATS_Section_Reference
Apparatus pulls NETA_ATS_Labor_Hours
    ↓
Revenue calculation uses ATS labor hours
```

### Data Validation in Excel:
- When Cell C3 = "ATS":
  - Dropdowns show NETA '25 (ATS) sections
  - Formulas pull from ATS labor hours column
  
- When Cell C3 = "MTS":
  - Dropdowns show NETA '23 (MTS) sections
  - Formulas pull from MTS labor hours column

### Import Process:
1. Read Excel estimator scope sheet
2. Extract NETA_Standard from Cell C3
3. Create Scope record with NETA_Standard value
4. For each apparatus in scope:
   - Lookup Apparatus_Type_Master
   - Pull labor hours based on NETA_Standard (ATS or MTS)
   - Pull section reference based on NETA_Standard
   - Store in Apparatus record

### Example Comparison:

| Apparatus Type | NETA ATS Section | ATS Hours | NETA MTS Section | MTS Hours |
|----------------|------------------|-----------|------------------|-----------|
| Transformer - Pad Mount Oil | 7.2 | 12.0 | 7.2 | 8.5 |
| Circuit Breaker - Molded Case | 7.4.1 | 2.5 | 7.13.1 | 1.8 |
| Switchgear - Metal Enclosed | 7.9 | 18.0 | 7.11 | 12.0 |

**Key Insight:** Same equipment type has different testing requirements and labor hours depending on whether it's ATS (new installation) or MTS (maintenance).

### Documentation Updates:
- ✅ Master Build Specification v1.1 - Added NETA_Standard architecture section
- ✅ Master Build Specification v1.1 - Updated Apparatus_Type_Master table structure
- ✅ Master Build Specification v1.1 - Added NETA_Standard field to Scopes table ERD
- ✅ Build Checklist - Added NETA_Standard field to Scopes table build steps
- ✅ Build Checklist - Added NETA Standard verification steps
- ✅ CSV Templates - Added NETA_Standard column to 02_Scopes_Template.csv
- ✅ CSV Templates - Updated 04_Apparatus_Template.csv with NETA considerations
- ✅ Implementation Checklist - Added NETA Standards training modules
- ✅ Implementation Checklist - Added NETA validation steps

---

## CLARIFICATION 3: APPARATUS_TYPE_MASTER TABLE STRUCTURE

### Old Structure (Pre-v1.1):
```
Apparatus_Type_Master:
  - Apparatus_Type_ID (PK)
  - Apparatus_Type_Name
  - NETA_Spec_Reference (single value)
  - Default_Labor_Hours (single value)
  - Category
```

### New Structure (v1.1):
```
Apparatus_Type_Master:
  - Apparatus_Type_ID (PK)
  - Apparatus_Type_Name
  - NETA_ATS_Section_Reference (Text 50) ⭐ NEW
  - NETA_MTS_Section_Reference (Text 50) ⭐ NEW
  - NETA_ATS_Labor_Hours (Decimal) ⭐ NEW
  - NETA_MTS_Labor_Hours (Decimal) ⭐ NEW
  - Category
```

### Migration Strategy for Existing Data:
If you have existing data in the old structure:

1. **Identify Current Standard:**
   - Determine if existing NETA_Spec_Reference values are ATS or MTS based
   - Most likely they are ATS (new installation standard)

2. **Data Transformation:**
   ```sql
   -- Assuming existing data is ATS-based
   UPDATE Apparatus_Type_Master
   SET 
     NETA_ATS_Section_Reference = NETA_Spec_Reference,
     NETA_ATS_Labor_Hours = Default_Labor_Hours,
     NETA_MTS_Section_Reference = NULL,  -- Populate separately
     NETA_MTS_Labor_Hours = NULL         -- Populate separately
   ```

3. **MTS Data Population:**
   - Research NETA MTS 2023 standards
   - Populate MTS_Section_Reference and MTS_Labor_Hours for each apparatus type
   - MTS hours typically 60-75% of ATS hours (less comprehensive testing)

### Example Record Transformation:

**Before (single standard):**
```
Apparatus_Type_Name: "Transformer - Pad Mount Oil"
NETA_Spec_Reference: "7.2"
Default_Labor_Hours: 12.0
```

**After (dual standard):**
```
Apparatus_Type_Name: "Transformer - Pad Mount Oil"
NETA_ATS_Section_Reference: "7.2"
NETA_ATS_Labor_Hours: 12.0
NETA_MTS_Section_Reference: "7.2"
NETA_MTS_Labor_Hours: 8.5
```

### Documentation Updates:
- ✅ Master Build Specification v1.1 - Updated Apparatus_Type_Master table definition
- ✅ Master Build Specification v1.1 - Updated ERD to show 4-column structure
- ✅ Build Checklist - Referenced updated Apparatus_Type_Master structure
- ✅ Implementation Checklist - Added Apparatus_Type_Master with ATS/MTS specs

---

## CROSS-DOCUMENT UPDATE SUMMARY

### Documents Updated to v1.1:

| Document | Filename | Updates |
|----------|----------|---------|
| Master Build Specification | `RESA_Power_Project_Tracker_Master_Build_Specification.md` | ✅ All three clarifications |
| Quick Build Checklist | `Build_Checklist_4_Tables.md` | ✅ All three clarifications |
| Implementation Checklist | `Implementation_Checklist.md` | ✅ All three clarifications |
| CSV Templates | `01-06_*_Template.csv` | ✅ All three clarifications |
| CSV Templates README | `README_CSV_TEMPLATES.md` | ✅ All three clarifications |

### Key Changes by Document:

#### Master Build Specification v1.1:
- Added NETA_Standard field to Scopes table
- Updated Apparatus_Type_Master with 4-column NETA structure
- Clarified Tasks table as "Immediate Implementation"
- Updated import process to read Cell C3 for NETA_Standard
- Enhanced training materials with NETA Standards modules
- Added NETA-specific views and testing scenarios

#### Build Checklist v1.1:
- Added NETA_Standard field build steps to Scopes table
- Updated Tasks table section with "IMMEDIATE IMPLEMENTATION" status
- Added manual task creation workflow notes
- Included NETA Standard verification steps
- Referenced Apparatus_Type_Master with ATS/MTS structure

#### Implementation Checklist v1.1:
- Added Apparatus_Type_Master with ATS/MTS specs to Phase 1
- Clarified Tasks table immediate implementation
- Added "Manual Task Creation" workflow section
- Updated data migration to skip tasks import
- Enhanced PM training with NETA Standards module (15 min)
- Added manual task creation training (20 min)
- Updated field user training with NETA section reference awareness

#### CSV Templates v1.1:
- Added NETA_Standard column to 02_Scopes_Template.csv
- Updated 04_Apparatus_Template.csv with NETA considerations
- Marked 03_Tasks_Template.csv as "REFERENCE ONLY, NOT FOR IMPORT"
- Created 05_Scope_Financial_Config_Template.csv (separate financial data)
- Created 06_Apparatus_Revenue_Template.csv (auto-generated by Power Automate)
- Added comprehensive README_CSV_TEMPLATES.md with all clarifications

---

## BUSINESS IMPACT

### Benefits of These Clarifications:

1. **Tasks Table Immediate Implementation:**
   - ✅ Technicians have organized work lists from day one
   - ✅ PMs can assign and track work effectively
   - ✅ No dependency on Excel task structure that doesn't exist
   - ✅ Flexibility to organize apparatus as needed per project

2. **NETA Standards Architecture:**
   - ✅ Accurate labor hours for both new installations (ATS) and maintenance work (MTS)
   - ✅ Correct NETA section references for field technicians
   - ✅ Proper revenue recognition based on actual testing requirements
   - ✅ Compliance with appropriate NETA standards per project type
   - ✅ Foundation for future standard updates (NETA releases new versions periodically)

3. **Apparatus_Type_Master Structure:**
   - ✅ Single master table supports both ATS and MTS projects
   - ✅ No duplicate apparatus type definitions
   - ✅ Easy to update when NETA standards change
   - ✅ Clear separation between new installation and maintenance testing
   - ✅ Accurate cost estimation for different project types

### Risk Mitigation:

**Without these clarifications:**
- ❌ Tasks import would fail (no source data in Excel)
- ❌ Wrong labor hours used for MTS projects (overpricing)
- ❌ Wrong NETA section references for field techs (wrong test procedures)
- ❌ Revenue miscalculations on maintenance projects
- ❌ Confusion about which testing standards apply

**With these clarifications:**
- ✅ Clear implementation path for all tables
- ✅ Accurate labor hours and revenue for all project types
- ✅ Correct test procedures referenced for field work
- ✅ Proper NETA compliance per project requirements
- ✅ Unified architecture supporting company growth

---

## TRAINING IMPLICATIONS

### Additional Training Required:

#### Project Managers (Add 35 minutes):
1. **NETA Standards Overview** (15 minutes)
   - ATS vs MTS: When to use each
   - Impact on labor hours and pricing
   - Setting NETA_Standard in Excel Cell C3
   - Verifying correct standard during import

2. **Manual Task Creation Workflow** (20 minutes)
   - When to create tasks (after scope/apparatus import)
   - Strategies for grouping apparatus
   - Task assignment best practices
   - Balancing technician workloads

#### Field Technicians (Add 10 minutes):
1. **NETA Section References** (10 minutes)
   - Understanding NETA section numbers
   - Finding correct test procedures
   - ATS vs MTS awareness (context only)
   - Using section references in the field

#### Administrators (Add 35 minutes):
1. **NETA Standards Architecture** (15 minutes)
   - Master table structure with ATS/MTS columns
   - Import process and Cell C3 reading
   - NETA_Standard inheritance through relationships
   - Troubleshooting NETA data issues

2. **Maintaining ATS/MTS Specifications** (20 minutes)
   - Updating Apparatus_Type_Master
   - When NETA publishes new standards
   - Migrating existing projects to new standards
   - Audit procedures for NETA compliance

---

## ACTION ITEMS

### Immediate:
- [x] Update all documentation to v1.1 (COMPLETED)
- [ ] Review updates with project stakeholders
- [ ] Validate Apparatus_Type_Master data has both ATS and MTS values populated
- [ ] Test import process with NETA_Standard from Cell C3
- [ ] Verify revenue calculations work correctly for both ATS and MTS scopes

### Short-term (This Week):
- [ ] Train PMs on manual task creation workflow
- [ ] Create task creation best practices guide
- [ ] Populate any missing MTS values in Apparatus_Type_Master
- [ ] Test full import process with mixed ATS/MTS scopes

### Medium-term (This Month):
- [ ] Conduct updated training sessions with new NETA materials
- [ ] Create NETA Standards reference guide for field techs
- [ ] Document task organization patterns from early projects
- [ ] Build reports showing ATS vs MTS project metrics

---

## LESSONS LEARNED

### What Worked Well:
1. ✅ Detailed conversation about Excel structure revealed NETA standards in Cell C3
2. ✅ Questioning the "Tasks import" assumption exposed Excel's lack of task structure
3. ✅ Recognizing the difference between ATS and MTS early prevents major rework
4. ✅ Comprehensive documentation updates ensure consistency across all materials

### Improvement Opportunities:
1. 🔍 Earlier review of Excel estimator structure could have identified these issues sooner
2. 🔍 More detailed requirements gathering on NETA standards would have clarified ATS/MTS upfront
3. 🔍 Validation of assumptions (like "tasks will be imported") before building architecture
4. 🔍 Regular cross-checks between Excel reality and Power Apps design

### Best Practices for Future:
1. 📋 Always examine source data structure in detail before designing target system
2. 📋 Question all assumptions about import sources
3. 📋 Document industry-specific standards (like NETA) explicitly in requirements
4. 📋 Create comprehensive field-level specifications early in design process
5. 📋 Validate assumptions with domain experts (field technicians, PMs) frequently

---

## APPROVAL & SIGN-OFF

**Clarifications Documented By:** Jason Smith  
**Date:** November 10, 2025  
**Documentation Version:** 1.1  

**Reviewed By:** [Stakeholder Name]  
**Date:** [Review Date]  

**Approved By:** [Project Sponsor]  
**Date:** [Approval Date]  

---

**END OF CLARIFICATIONS SUMMARY**

*This document serves as the official record of critical clarifications made during the project modernization process. All documentation has been updated to v1.1 to reflect these clarifications. Future project decisions should reference these clarifications to ensure alignment with the correct architecture.*
