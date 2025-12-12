# v1.2.0.3 CHOICE FIELDS (OPTION SETS) DOCUMENTATION

**Generated**: November 15, 2025  
**Source**: Solution_Exports/v1.2.0.3/customizations.xml (optionsets section)  
**Total Option Sets**: 8  
**Status**: ✅ COMPLETE EXTRACTION

---

## 📊 SUMMARY

### **Custom Option Sets**

| Option Set Name | Used By | Values | Purpose |
|-----------------|---------|--------|---------|
| cr950_apparatusassessment | Apparatus.Apparatus_Assessment | 3 | Quality assessment |
| cr950_workstatus | Apparatus.Completion_Status | 5 | Completion tracking |
| cr950_projectstatus | Projects.Project_Status | 6 | Project lifecycle |
| cr950_taskstatus | Tasks.Task_Status | 4 | Task progress |
| cr950_scopestatus | *(unused?)* | 4 | Scope status (not found in fields) |
| cr950_testing_standard | Apparatus.Witness_Test | 5 | Testing standard type |
| cr950_availability | *(unused?)* | 4 | Availability status (not found) |
| cr950_priority | *(unused?)* | 4 | Priority level (not found) |

**Note**: Some option sets may be defined but not actively used in current schema.

---

## 🎯 ACTIVE CHOICE FIELDS

---

### **1. cr950_apparatusassessment** - Apparatus Assessment

**Used By**: `cr950_Apparatus.cr950_apparatus_assessment`  
**Field Name**: Apparatus_Assessment  
**Required**: Recommended  
**Introduced**: v1.2.0.2  
**Purpose**: Quality assessment outcome for apparatus

#### **Values**

| Value | Label | Description |
|-------|-------|-------------|
| 0 | **Acceptable** | Apparatus meets all requirements, no issues found |
| 1 | **Minor Deficiency** | Small issues identified, does not affect operation significantly |
| 2 | **Non-Serviceable** | Major issues, apparatus cannot be used or requires significant repairs |

#### **Usage Context**
- Part of quality tracking enhancement in v1.2.0.2
- Used during or after apparatus testing/commissioning
- Helps identify which apparatus need attention
- May trigger follow-up actions or notifications

#### **Business Logic**
- **Acceptable**: Normal completion, apparatus passes all tests
- **Minor Deficiency**: Document issues but apparatus can be used, may need future correction
- **Non-Serviceable**: Critical failures, apparatus must be repaired/replaced before use

---

### **2. cr950_workstatus** - Completion Status

**Used By**: `cr950_Apparatus.cr950_completion_status`  
**Field Name**: Completion_Status  
**Required**: No  
**Purpose**: Track completion state of apparatus work

#### **Values**

| Value | Label | Description |
|-------|-------|-------------|
| 0 | **Not Started** | Work has not begun on this apparatus |
| 1 | **In Progress** | Work is currently underway |
| 2 | **Complete** | **✅ CRITICAL - Revenue Recognition Trigger** |
| 3 | **On Hold** | Work paused temporarily |
| 4 | **Cancelled** | Work will not be completed |

#### **⚠️ CRITICAL FIELD**
This field is the **primary trigger** for revenue recognition!

#### **Revenue Recognition Logic**
```
IF Completion_Status = "Complete" (value 2)
THEN
    - Completed_Hours = Labor_Hours (billable)
    - Trigger: Create ApparatusRevenue record (when flow built)
    - Revenue Earned = Labor_Hours × Labor_Rate
ELSE
    - Completed_Hours = 0 (not billable)
    - No revenue recognition
END IF
```

#### **Status Transition Flow**
```
Not Started (0)
  ↓
In Progress (1)
  ↓
Complete (2) ← Revenue recognized here
  
OR
  ↓
On Hold (3) → Back to In Progress (1)
  
OR
  ↓
Cancelled (4) → No revenue
```

#### **Business Rules**
- **Complete**: Only set when ALL work finished and apparatus tested
- **On Hold**: Use for temporary delays (site access, waiting for parts, etc.)
- **Cancelled**: Use when apparatus removed from scope or work not needed

---

### **3. cr950_projectstatus** - Project Status

**Used By**: `cr950_Projects.cr950_project_status`  
**Field Name**: Project_Status  
**Required**: No  
**Purpose**: Track project lifecycle stage

#### **Values**

| Value | Label | Description |
|-------|-------|-------------|
| 0 | **Quoted** | Project quoted but not yet awarded |
| 1 | **Planning** | Project awarded, planning phase |
| 2 | **Active** | Project in execution phase |
| 3 | **On Hold** | Project paused temporarily |
| 4 | **Completed** | All work finished |
| 5 | **Cancelled** | Project cancelled/lost |

#### **Status Transition Flow**
```
Quoted (0)
  ↓
Planning (1) [Project Awarded]
  ↓
Active (2) [Execution Starts]
  ↓
Completed (4) [All Apparatus Complete]

OR
  ↓
On Hold (3) → Back to Active (2)

OR
  ↓
Cancelled (5) [Any Stage]
```

#### **Business Rules**
- **Quoted**: No apparatus or scopes yet (pre-award)
- **Planning**: Setting up scopes, tasks, apparatus
- **Active**: Field work in progress
- **Completed**: All apparatus marked complete, invoicing phase
- **On Hold**: Temporary stop (customer request, waiting for permits, etc.)
- **Cancelled**: Project did not proceed or was terminated

#### **Reporting Uses**
- Filter "Active" projects for current workload
- Track "Completed" projects for historical analysis
- Identify "On Hold" projects needing attention
- Separate "Quoted" from "Active" in pipeline reporting

---

### **4. cr950_taskstatus** - Task Status

**Used By**: `cr950_Tasks.cr950_task_status`  
**Field Name**: Task_Status  
**Required**: No  
**Purpose**: Track task progress

#### **Values**

| Value | Label | Description |
|-------|-------|-------------|
| 0 | **Not Started** | Task not yet begun |
| 1 | **In Progress** | Task underway |
| 2 | **Complete** | Task finished |
| 3 | **Blocked** | Task cannot proceed (waiting on dependency) |

#### **Status Transition Flow**
```
Not Started (0)
  ↓
In Progress (1)
  ↓
Complete (2)

OR
  ↓
Blocked (3) → Back to In Progress (1) [when unblocked]
```

#### **Business Rules**
- **Not Started**: No apparatus work begun yet
- **In Progress**: At least one apparatus in progress
- **Complete**: All apparatus in task marked complete
- **Blocked**: External dependency preventing work (equipment not delivered, permits pending, etc.)

#### **Difference from Apparatus Completion_Status**:
- **Task Status**: Overall task progress (manual or calculated from apparatus)
- **Apparatus Completion_Status**: Individual apparatus work state
- Tasks can have multiple apparatus at different completion states

---

### **5. cr950_testing_standard** - Witness Test / Testing Standard

**Used By**: `cr950_Apparatus.cr950_witness_test`  
**Field Name**: Witness_Test  
**Required**: No  
**Introduced**: v1.2.0.2  
**Purpose**: Identify which testing standard/type applies

#### **Values**

| Value | Label | Full Name | Description |
|-------|-------|-----------|-------------|
| 0 | **ATS** | Acceptance Testing Standard | NETA initial acceptance testing |
| 1 | **MTS** | Maintenance Testing Standard | NETA routine maintenance testing |
| 2 | **ECS** | Electrical Construction Spec | Project-specific construction specs |
| 3 | **Spec** | Specification | Generic project specification testing |
| 4 | **Other** | Other | Non-standard or custom testing |

#### **NETA Standards Context**

**NETA** = InterNational Electrical Testing Association

1. **ATS (Acceptance Testing)**:
   - New equipment commissioning
   - Most comprehensive testing
   - Higher hourly requirements
   - Links to ApparatusTypeMaster.NETA_Standard_ATS_Hours

2. **MTS (Maintenance Testing)**:
   - Existing equipment verification
   - Routine periodic testing
   - Moderate hourly requirements
   - Links to ApparatusTypeMaster.NETA_Standard_MTS_Hours

3. **ECS / Spec / Other**:
   - Project-specific requirements
   - May not follow NETA standards
   - Custom hour estimates

#### **Usage**
- Determines testing rigor and time requirements
- May affect Labor_Hours estimates
- References ApparatusTypeMaster for standard hours
- Part of quality tracking in v1.2.0.2

---

## 🔍 UNUSED OPTION SETS

### **6. cr950_scopestatus** - Scope Status (UNUSED?)

**Defined Values**:
| Value | Label |
|-------|-------|
| 0 | Not Started |
| 1 | In Progress |
| 2 | Complete |
| 3 | On Hold |

**Status**: ⚠️ Defined but field not found in ProjectScope entity

**Hypothesis**: May have been planned but not implemented, or replaced by calculated completion percentage.

**Recommendation**: Either:
- Add to ProjectScope entity if scope-level status tracking needed
- Remove from solution if not needed (cleanup)

---

### **7. cr950_availability** - Availability Status (UNUSED?)

**Defined Values**:
| Value | Label |
|-------|-------|
| 0 | Available |
| 1 | Not Available |
| 2 | Partial Availability |
| 3 | Unknown |

**Status**: ⚠️ Defined but field not found in any entity

**Hypothesis**: May have been planned for resource or apparatus availability tracking but not implemented.

**Recommendation**: Remove from solution if not needed (cleanup).

---

### **8. cr950_priority** - Priority Level (UNUSED?)

**Defined Values**:
| Value | Label |
|-------|-------|
| 0 | Low |
| 1 | Medium |
| 2 | High |
| 3 | Critical |

**Status**: ⚠️ Defined but field not found in any entity

**Hypothesis**: May have been planned for task or apparatus prioritization but not implemented.

**Recommendation**: Either:
- Add to Tasks or Apparatus if priority tracking needed
- Remove from solution if not needed (cleanup)

---

## 📋 CHOICE FIELD RELATIONSHIPS

### **Quality Tracking Pair** (v1.2.0.2)
- `Apparatus_Assessment` (cr950_apparatusassessment) - What is the quality outcome?
- `Witness_Test` (cr950_testing_standard) - What standard was used?

**Together**: Provide complete quality tracking context

---

### **Status Hierarchy**
```
Project Level: Project_Status (6 values)
  ↓
Scope Level: [No status field - use Percent_Complete]
  ↓
Task Level: Task_Status (4 values)
  ↓
Apparatus Level: Completion_Status (5 values) ← Revenue trigger
```

**Each level**: Progressively more granular status tracking

---

## 🎯 BUSINESS LOGIC IMPLICATIONS

### **1. Revenue Recognition**
**Key Field**: `Completion_Status` = "Complete" (2)
- Only this value triggers revenue recognition
- All other values (0, 1, 3, 4) = $0 revenue
- **Critical**: Don't mark complete unless work is done and apparatus tested

### **2. Quality Tracking**
**Fields**: `Apparatus_Assessment` + `Witness_Test`
- Assessment = outcome quality
- Witness_Test = testing rigor applied
- Together = complete quality record

### **3. Project Lifecycle**
**Stages**: Quoted → Planning → Active → Completed
- **Active** = billable work happening
- **Completed** = all revenue recognized
- Track progression through stages

### **4. Task Management**
**Unique Status**: "Blocked" (3)
- Identifies dependencies
- Helps identify bottlenecks
- Differentiates from "On Hold" (whole project issue vs. task-specific blocker)

---

## ⚠️ RECOMMENDATIONS

### **Immediate Actions**

1. **Verify Unused Option Sets**:
   - Check if `cr950_scopestatus`, `cr950_availability`, `cr950_priority` are needed
   - If not needed: Remove from solution (cleanup)
   - If needed: Add fields to appropriate entities

2. **Document Status Transitions**:
   - Create workflow documentation for when to change statuses
   - Train users on proper status usage
   - Consider automation for some transitions

3. **Revenue Recognition Training**:
   - Emphasize importance of `Completion_Status` = "Complete"
   - Document when it's appropriate to mark complete
   - Consider approval workflow before marking complete

### **Future Enhancements**

1. **Add Scope Status Field**:
   - Consider adding `Scope_Status` using `cr950_scopestatus`
   - Would complement calculated `Percent_Complete`
   - Useful for manual status overrides

2. **Add Priority Fields**:
   - Consider adding priority to Tasks or Apparatus
   - Useful for work prioritization and scheduling
   - Use existing `cr950_priority` option set

3. **Status Change History**:
   - Enable auditing on status fields
   - Track who changed status and when
   - Useful for analyzing project timelines

---

## 📊 OPTION SET USAGE SUMMARY

| Option Set | Field | Entity | Critical? | Version |
|------------|-------|--------|-----------|---------|
| cr950_apparatusassessment | Apparatus_Assessment | Apparatus | ⚠️ Quality | v1.2.0.2 |
| cr950_workstatus | Completion_Status | Apparatus | 🔴 CRITICAL - Revenue | v1.0.0.1 |
| cr950_projectstatus | Project_Status | Projects | ✅ Lifecycle | v1.0.0.1 |
| cr950_taskstatus | Task_Status | Tasks | ✅ Progress | v1.0.0.1 |
| cr950_testing_standard | Witness_Test | Apparatus | ⚠️ Quality | v1.2.0.2 |
| cr950_scopestatus | *(none)* | *(none)* | ❓ Unused | v1.0.0.1 |
| cr950_availability | *(none)* | *(none)* | ❓ Unused | Unknown |
| cr950_priority | *(none)* | *(none)* | ❓ Unused | Unknown |

**Legend**:
- 🔴 CRITICAL - Essential for core business logic
- ✅ Important - Key for operations
- ⚠️ Quality - Part of quality tracking
- ❓ Unused - Defined but not implemented

---

**CHOICE FIELDS DOCUMENTATION STATUS**: ✅ COMPLETE

*All option sets extracted and documented. 5 active, 3 potentially unused.*

---

**END OF CHOICE FIELDS DOCUMENTATION**
