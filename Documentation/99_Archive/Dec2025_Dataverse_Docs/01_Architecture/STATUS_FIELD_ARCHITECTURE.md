# CHOICE FIELD ARCHITECTURE & STATUS WORKFLOWS

**Version:** 1.0  
**Date:** November 19, 2025  
**Solution Version:** v1.3.0.4  
**Purpose:** Document all choice field values, state transitions, and business rules

---

## 📋 OVERVIEW

This document catalogs all choice (dropdown) fields across the RESA Power solution, including:
- Exact values as implemented in v1.3.0.4
- User customizations made vs original specification
- State transition workflows
- Business rules governing status changes
- Integration points with automation

**Note:** Values documented here reflect ACTUAL implementation, which may differ from original specifications.

---

## 🎯 QUICK REFERENCE

### **Choice Fields by Table**

| Table | Choice Fields | Purpose |
|-------|--------------|---------|
| **Projects** | Project_Status | Track project lifecycle |
| **ProjectScope** | NETA_Standard | ATS vs MTS testing |
| **Tasks** | Task_Status | Track task progress |
| **Apparatus** | Completion_Status | Track individual apparatus completion |
| **Apparatus** | Apparatus_Assessment | Quality assessment result |
| **Apparatus** | Witness_Test | NETA testing standard applied |
| **ApparatusRevenue** | Revenue_Status (planned) | Revenue recognition state |

---

## 1. PROJECT_STATUS

### **Table:** cr950_Projects  
### **Field Name:** Project_Status  
### **Schema Name:** cr950_project_status

### **Choice Values:**

| Value | Label | Integer | Color | When Used |
|-------|-------|---------|-------|-----------|
| 1 | Quoted | 1 | Gray | Project estimated, awaiting client decision |
| 2 | Planning | 2 | Yellow | Awarded, planning/scheduling phase |
| 3 | Active | 3 | Green | Work in progress |
| 4 | Completed | 4 | Blue | All work finished |

### **Default Value:** Quoted

### **State Transition Workflow:**

```
┌─────────┐      Award      ┌──────────┐     Work        ┌────────┐      Final      ┌───────────┐
│ QUOTED  │ ─────────────→  │ PLANNING │ ─────Starts───→ │ ACTIVE │ ──Completion──→ │ COMPLETED │
└─────────┘                 └──────────┘                 └────────┘                 └───────────┘
     ↑                            ↓                           ↓                           ↑
     └───────────────────────────┴───────────────────────────┴───────────────────────────┘
                           (Manual status changes allowed)
```

### **Business Rules:**

1. **Quoted → Planning:**
   - Triggered when: Project awarded, begin planning
   - Prerequisites: None
   - Actions: None

2. **Planning → Active:**
   - Triggered when: First scope/apparatus work begins
   - Prerequisites: At least one scope created (recommended)
   - Actions: Set Project_Start_Date (recommended)

3. **Active → Completed:**
   - Triggered when: All work finished
   - Prerequisites: All scopes complete (should validate)
   - Actions: Set Project_End_Date
   - Validation: Warn if incomplete apparatus exist

4. **Backward Transitions:**
   - Allowed: Yes (manual override capability)
   - Use case: Corrections, reopening projects
   - Warning: Should prompt for confirmation

### **Integration Points:**
- **Dashboards:** Filtered views by status
- **Reports:** Project status distribution
- **Notifications:** Could trigger alerts on status change
- **KPIs:** Count by status, time in each status

### **User Customizations (vs Original Spec):**
- ✅ Original spec suggested: "Not Started" → "In Progress" → "Complete"
- ✅ Actual implementation: "Quoted" → "Planning" → "Active" → "Completed"
- **Rationale:** Better reflects electrical contracting lifecycle (estimating → award → execution)

---

## 2. NETA_STANDARD

### **Table:** cr950_ProjectScope  
### **Field Name:** NETA_Standard  
### **Schema Name:** cr950_neta_standard

### **Choice Values:**

| Value | Label | Integer | When Used |
|-------|-------|---------|-----------|
| 1 | ATS | 1 | Acceptance Testing Specifications (new installations) |
| 2 | MTS | 2 | Maintenance Testing Specifications (existing equipment) |

### **Default Value:** ATS

### **Business Context:**

**ATS (Acceptance Testing Specifications):**
- Used for: NEW equipment installations and commissioning
- Standard: NETA '25 ATS
- Testing focus: Initial acceptance, baseline performance
- More comprehensive testing requirements
- Typical projects: New substations, facility commissioning, greenfield installations

**MTS (Maintenance Testing Specifications):**
- Used for: EXISTING equipment and ongoing maintenance
- Standard: NETA '23 MTS
- Testing focus: Preventive maintenance, condition assessment
- Periodic testing protocols
- Typical projects: Annual maintenance, condition-based testing, troubleshooting

### **Impact on System:**

When NETA_Standard is set on a Scope:
1. **Apparatus Type Lookup:** System references appropriate column
   - ATS scope → uses ApparatusTypeMaster.NETA_ATS_Labor_Hours
   - MTS scope → uses ApparatusTypeMaster.NETA_MTS_Labor_Hours

2. **Section References:** Different NETA manual sections
   - ATS scope → uses NETA_ATS_Section_Reference
   - MTS scope → uses NETA_MTS_Section_Reference

3. **Labor Estimation:** Default hours vary by standard
   - Same equipment type may have different hour estimates
   - Example: Transformer testing - ATS: 12 hrs, MTS: 8 hrs

### **Business Rules:**
- Required field (cannot be null)
- Should be set during scope creation
- **WARNING:** Changing NETA_Standard after apparatus created may cause hour discrepancies
- Recommended: Lock field after first apparatus added to scope

### **Integration Points:**
- **Estimating:** Determines which labor hours used from master list
- **Reporting:** Group projects by ATS vs MTS work
- **Quality:** Different testing procedures/checklists

---

## 3. TASK_STATUS

### **Table:** cr950_Tasks  
### **Field Name:** Task_Status  
### **Schema Name:** cr950_task_status

### **Choice Values (Estimated):**

| Value | Label | Integer | Color | When Used |
|-------|-------|---------|-------|-----------|
| 1 | Not Started | 1 | Gray | Task created, no work begun |
| 2 | In Progress | 2 | Yellow | Some apparatus completed |
| 3 | Complete | 3 | Green | All apparatus in task finished |
| 4 | Blocked | 4 | Red | Work cannot proceed |

### **Default Value:** Not Started

### **Status Determination:**

Tasks typically don't have manually-set status. Instead, status is CALCULATED based on apparatus:

```
IF (Completed_Apparatus_Count = 0) THEN "Not Started"
ELSE IF (Completed_Apparatus_Count = Total_Apparatus_Count) THEN "Complete"
ELSE IF (Task_Blocked_Field = Yes) THEN "Blocked"
ELSE "In Progress"
```

### **Business Rules:**
- Status auto-updates based on apparatus completion
- "Blocked" status may require manual intervention
- Cannot manually set to "Complete" if incomplete apparatus exist

### **User Customizations:**
- **Verification Needed:** Confirm if Task_Status field exists and exact values
- Original spec assumed manual status, actual may be calculated

---

## 4. COMPLETION_STATUS (Apparatus)

### **Table:** cr950_Apparatus  
### **Field Name:** Completion_Status  
### **Schema Name:** cr950_completion_status

### **Choice Values:**

| Value | Label | Integer | Color | When Used |
|-------|-------|---------|-------|-----------|
| 1 | Not Started | 1 | Gray | Apparatus not yet tested |
| 2 | In Progress | 2 | Yellow | Testing underway but not complete |
| 3 | Complete | 3 | Green | Testing finished, passed |
| 4 | On Hold | 4 | Orange | Paused (waiting for parts, access, etc.) |
| 5 | Cancelled | 5 | Red | Not to be tested (scope change) |

### **Default Value:** Not Started

### **State Transition Workflow:**

```
┌─────────────┐
│ NOT STARTED │ ────────┐
└─────────────┘         │
                        ↓
                  ┌─────────────┐      Complete      ┌──────────┐
                  │ IN PROGRESS │ ──────Testing────→  │ COMPLETE │
                  └─────────────┘                     └──────────┘
                        ↕                                   ↓
                  ┌─────────────┐                    [Revenue
                  │   ON HOLD   │                     Recognition
                  └─────────────┘                      Triggered]
                        
┌───────────┐
│ CANCELLED │ (Terminal state)
└───────────┘
```

### **Business Rules:**

1. **Not Started → In Progress:**
   - Triggered when: Field tech begins testing
   - Prerequisites: None
   - Actions: Optionally set Actual_Start_Date (if date tracking enabled)
   - Users: Field techs can change

2. **In Progress → Complete:**
   - Triggered when: Testing finished successfully
   - Prerequisites: Labor_Hours should be populated
   - Actions: 
     - Set Date_Completed = NOW() (via Power Automate)
     - Create ApparatusRevenue record (via Power Automate)
     - Update parent rollups (automatic)
   - Users: Field techs can change

3. **In Progress ↔ On Hold:**
   - Bidirectional: Can pause and resume work
   - Triggered when: Waiting for parts, access, client, etc.
   - Actions: None (informational status)

4. **Any → Cancelled:**
   - Triggered when: Scope change, apparatus removed from project
   - Effect: Excluded from rollup calculations
   - Irreversible: Typically terminal state

### **Calculated Field Dependencies:**

When Completion_Status = "Complete":
- **Completed_Hours** = Labor_Hours
- **Remaining_Hours** = 0
- **Date_Completed** auto-set (if date tracking enabled)
- **Parent Rollups** recalculate (Scope, Project Percent_Complete)

When Completion_Status = "Cancelled":
- Excluded from Total_Apparatus_Count rollups
- Excluded from completion percentage calculations

### **Integration Points:**

**Power Automate Flow - Revenue Recognition:**
```
Trigger: Apparatus.Completion_Status changes to "Complete"
Actions:
  1. Set Date_Completed = NOW()
  2. Create ApparatusRevenue record:
     - Link to Apparatus
     - Link to ScopeLaborDetail (for rate)
     - Link to Project (for reporting)
     - Copy Labor_Hours, Delays
     - Set Revenue_Status = "Recognized"
  3. Send notification (optional)
```

### **User Customizations:**
- ✅ Added "On Hold" status (not in original spec)
- ✅ Added "Cancelled" status (not in original spec)
- **Rationale:** Real-world projects need these status options

---

## 5. APPARATUS_ASSESSMENT

### **Table:** cr950_Apparatus  
### **Field Name:** Apparatus_Assessment  
### **Schema Name:** cr950_apparatus_assessment  
### **Added In:** v1.2.0.2 (Quality Tracking Enhancement)

### **Choice Values:**

| Value | Label | Integer | Color | Meaning |
|-------|-------|---------|-------|---------|
| 1 | Acceptable | 1 | Green | Equipment meets standards, no issues |
| 2 | Minor Deficiency | 2 | Yellow | Issues found but equipment operational |
| 3 | Non-Serviceable | 3 | Red | Equipment failed testing, requires repair/replacement |

### **Default Value:** None (field optional)

### **Business Context:**

This field captures the **quality assessment result** from testing:

**Acceptable:**
- Equipment passed all tests
- Within NETA specifications
- No corrective action needed
- Ready for service

**Minor Deficiency:**
- Some test results outside normal range BUT equipment still functional
- May require monitoring or future attention
- Does not prevent operation
- Examples: Slight insulation degradation, minor contact wear
- Recommendation: Schedule follow-up testing

**Non-Serviceable:**
- Equipment failed critical tests
- Safety concern or will not operate correctly
- Requires immediate attention
- Examples: Insulation failure, contact failure, protection relay malfunction
- Recommendation: Repair or replace before energizing

### **Business Rules:**
- Optional field (may be left blank if assessment not applicable)
- Typically set when Completion_Status = "Complete"
- No validation preventing "Complete" + "Non-Serviceable" (real-world scenario: testing IS complete, but equipment failed)

### **Reporting Value:**
- **Pass Rate:** Count "Acceptable" / Total Assessed
- **Deficiency Report:** List all "Minor Deficiency" + "Non-Serviceable"
- **Quality Metrics:** Track equipment failure rates by type, age, manufacturer

---

## 6. WITNESS_TEST

### **Table:** cr950_Apparatus  
### **Field Name:** Witness_Test  
### **Schema Name:** cr950_witness_test  
### **Added In:** v1.2.0.2 (Quality Tracking Enhancement)

### **Choice Values:**

| Value | Label | Integer | When Used |
|-------|-------|---------|-----------|
| 1 | ATS | 1 | NETA Acceptance Testing Specifications |
| 2 | MTS | 2 | NETA Maintenance Testing Specifications |
| 3 | ECS | 3 | Engineering Change Service (post-modification testing) |
| 4 | Spec | 4 | Manufacturer or project specification testing |
| 5 | Other | 5 | Other testing standard or custom procedure |

### **Default Value:** None (inherits from Scope's NETA_Standard, or set manually)

### **Business Context:**

**ATS (Acceptance Testing Specifications):**
- New equipment acceptance testing
- Baseline commissioning tests
- NETA '25 ATS procedures

**MTS (Maintenance Testing Specifications):**
- Preventive maintenance testing
- Condition assessment
- NETA '23 MTS procedures

**ECS (Engineering Change Service):**
- Post-modification or repair testing
- After equipment upgraded or altered
- Verifies changes don't negatively impact performance

**Spec (Specification Testing):**
- Custom testing per manufacturer specs
- Project-specific test procedures
- May exceed NETA minimums

**Other:**
- Catch-all for non-standard testing
- Troubleshooting procedures
- Ad-hoc testing

### **Business Rules:**
- Optional field
- Should align with Scope's NETA_Standard (but can override)
- Use case for override: ATS scope but one apparatus gets MTS testing

### **Integration:**
- Cross-reference with Scope.NETA_Standard
- Reporting: Count tests by standard type
- Quality: Ensure correct procedures followed

---

## 7. REVENUE_STATUS (Planned)

### **Table:** cr950_ApparatusRevenue  
### **Field Name:** Revenue_Status  
### **Schema Name:** cr950_revenue_status  
### **Status:** NOT YET IMPLEMENTED (planned for future enhancement)

### **Proposed Choice Values:**

| Value | Label | Integer | Meaning |
|-------|-------|---------|---------|
| 1 | Recognized | 1 | Revenue earned and recognized in accounting |
| 2 | Pending | 2 | Work complete but not yet recognized |
| 3 | Billed | 3 | Invoice sent to customer |
| 4 | Paid | 4 | Payment received |
| 5 | Disputed | 5 | Customer disputed amount |
| 6 | Void | 6 | Revenue record cancelled/voided |

### **Default Value:** Recognized (when auto-created by flow)

### **State Transition Workflow (Proposed):**

```
                                    ┌──────────────┐
                    Auto-Created    │  RECOGNIZED  │
Apparatus Complete ──────────────→  │ (Revenue     │
                                    │  Earned)     │
                                    └──────┬───────┘
                                           │ Monthly
                                           │ Invoice Run
                                           ↓
                                    ┌──────────────┐       ┌──────────┐
                                    │    BILLED    │ ────→ │   PAID   │
                                    └──────────────┘       └──────────┘
                                           │                      ↑
                                           ↓                      │
                                    ┌──────────────┐             │
                                    │   DISPUTED   │ ────────────┘
                                    └──────────────┘  (Resolution)
```

### **Business Rules (Proposed):**
- Auto-set to "Recognized" when ApparatusRevenue created
- "Billed" set when included in customer invoice
- "Paid" set when payment received
- "Disputed" if customer challenges charge
- "Void" if record needs to be cancelled (correcting errors)

### **Future Enhancement:**
- Track revenue lifecycle beyond recognition
- Integration with QuickBooks or accounting system
- Aging reports (Billed but not Paid)
- Dispute resolution workflow

---

## 8. GLOBAL CHOICES (Used Across Multiple Tables)

### **Priority (Projects, Scopes, Tasks)**

**Schema Name:** cr950_priority  
**Status:** DEFINED BUT UNUSED (per Gap Analysis)

**Proposed Values:**
| Value | Label |
|-------|-------|
| 1 | Low |
| 2 | Medium |
| 3 | High |
| 4 | Critical |

**Decision Needed:** Implement priority fields or remove unused option set

---

### **Availability (Unknown Table)**

**Schema Name:** cr950_availability  
**Status:** DEFINED BUT UNUSED (per Gap Analysis)

**Proposed Values:**
| Value | Label |
|-------|-------|
| 1 | Available |
| 2 | Busy |
| 3 | Out of Office |
| 4 | Do Not Disturb |

**Decision Needed:** Remove unused option set (likely not applicable to project tracking)

---

## 📊 CHOICE FIELD SUMMARY

### **Implementation Status:**

| Choice Field | Table | Status | Customized? |
|--------------|-------|--------|-------------|
| Project_Status | Projects | ✅ Operational | Yes (workflow names) |
| NETA_Standard | ProjectScope | ✅ Operational | No |
| Task_Status | Tasks | ⚠️ Verify | Unknown |
| Completion_Status | Apparatus | ✅ Operational | Yes (added On Hold, Cancelled) |
| Apparatus_Assessment | Apparatus | ✅ Operational | No |
| Witness_Test | Apparatus | ✅ Operational | No |
| Revenue_Status | ApparatusRevenue | ❌ Not Implemented | Planned |
| Priority | Multiple | ❌ Unused | N/A |
| Availability | Unknown | ❌ Unused | N/A |

---

## 🔄 STATE TRANSITION MATRIX

### **Apparatus Completion Status (Most Critical):**

| From \ To | Not Started | In Progress | Complete | On Hold | Cancelled |
|-----------|-------------|-------------|----------|---------|-----------|
| **Not Started** | - | ✅ | ⚠️ Rare | ✅ | ✅ |
| **In Progress** | ⚠️ Rare | - | ✅ | ✅ | ✅ |
| **Complete** | ❌ | ❌ | - | ❌ | ⚠️ Admin Only |
| **On Hold** | ⚠️ Rare | ✅ | ⚠️ Rare | - | ✅ |
| **Cancelled** | ❌ | ❌ | ❌ | ❌ | - |

**Legend:**
- ✅ = Allowed and common
- ⚠️ = Allowed but rare (should prompt confirmation)
- ❌ = Blocked or not recommended

---

## 🎯 BEST PRACTICES

### **For Developers:**
1. **Always validate choice values** before referencing in code
2. **Use integer values** in formulas (not labels - labels can change)
3. **Handle null values** (optional choice fields may be empty)
4. **Test state transitions** in workflows (ensure business rules enforced)

### **For Administrators:**
1. **Never delete choice values** if records exist using them (orphans data)
2. **Add new values to END of list** (maintains integer values)
3. **Document customizations** in this file when made
4. **Test thoroughly** after adding/modifying choice values

### **For Users:**
1. **Completion_Status** directly triggers revenue recognition - set carefully
2. **NETA_Standard** affects labor hour calculations - verify before apparatus creation
3. **Apparatus_Assessment** feeds quality metrics - be consistent in application

---

## 📝 CUSTOMIZATION LOG

| Date | Field | Change | Reason |
|------|-------|--------|--------|
| Nov 2025 | Project_Status | Changed from "Not Started/In Progress/Complete" to "Quoted/Planning/Active/Completed" | Better reflect contracting lifecycle |
| Nov 2025 | Completion_Status | Added "On Hold" and "Cancelled" options | Real-world project needs |
| Oct 2025 | Apparatus_Assessment | Added field with 3 values | v1.2.0.2 quality tracking enhancement |
| Oct 2025 | Witness_Test | Added field with 5 values | v1.2.0.2 quality tracking enhancement |

---

## 🔍 VERIFICATION CHECKLIST

To validate this documentation against live system:

- [ ] Export all option sets from Dataverse
- [ ] Compare integer values (order matters for some integrations)
- [ ] Verify default values set correctly
- [ ] Check color coding in views (if implemented)
- [ ] Test state transitions in Power Automate flows
- [ ] Confirm unused option sets (Priority, Availability) - remove if unused
- [ ] Verify Task_Status field existence and values
- [ ] Document any additional choice fields discovered

---

**END OF CHOICE FIELD ARCHITECTURE DOCUMENTATION**

*This document should be updated whenever choice fields are added, modified, or removed.*
