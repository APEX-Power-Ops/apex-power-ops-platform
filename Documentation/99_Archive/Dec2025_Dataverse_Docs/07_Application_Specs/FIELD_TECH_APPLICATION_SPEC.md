# FIELD TECH APPLICATION SPECIFICATION

**Purpose:** Define the mobile-first application interface for field technicians performing apparatus testing  
**Created:** November 15, 2025  
**Last Updated:** November 16, 2025  
**Version:** 1.0 - Initial mobile UX design with decision framework  
**Status:** Draft - Pending stakeholder decisions on work assignment model  
**User:** Field technicians (electrical testing specialists)  
**Context:** On-site at customer facilities, working with test equipment  
**Device:** Mobile phone or tablet (iOS/Android via PowerApps Mobile)

---

## ⚠️ ARCHITECTURAL DECISIONS REQUIRED

**This specification shows THREE possible designs based on decisions that need stakeholder input.**

### **DECISION IMPACT MATRIX**

| If You Choose... | Mobile App Shows... | Database Fields Needed | PM Workload | Field Flexibility |
|-----------------|---------------------|----------------------|-------------|------------------|
| **Individual Assignment** | "MY TASKS (15)" - Only Jake's assigned work | `Assigned_To` (single) | HIGH (assign every apparatus) | LOW (can't grab others' work) |
| **Team Pool** | "OUR WORK (45)" - Whole project, grab anything | `Project.Assigned_Team` (multi), `Completed_By` | LOW (assign team to project) | HIGH (self-organizing) |
| **Hybrid (Rec.)** | "MY TASKS (5)" + "TEAM POOL (30)" + "IN PROGRESS (10)" | `Assigned_To_Primary` (optional) + `Project.Team` + `Completed_By` | MEDIUM (assign critical items) | HIGH (planned + flexible) |

**Key Questions for Stakeholders**:

1. **WHO assigns apparatus to techs?**
   - PM only? Tech lead? Self-assign from pool?
   - **Impact**: Determines if we need `Assigned_To` field or just `Project.Team`

2. **How often do techs work in pairs/teams?**
   - Rarely? → Individual assignment works
   - Often? → Need team pool or multi-person tracking
   - **Impact**: Determines if we need `Worked_By` (multi-select) or just `Completed_By`

3. **Should techs see other techs' work?**
   - No (focused) → "My Tasks" only
   - Yes (collaborative) → "Team Tasks" visible
   - **Impact**: View filters and security roles

4. **Who gets credit when apparatus is completed?**
   - Assigned person (even if someone else finished it)?
   - Person who clicked "Complete"?
   - All contributors (split hours)?
   - **Impact**: Utilization reporting, performance reviews

5. **Can Phoenix techs work on Vegas projects?**
   - No (strict location boundaries) → Simple security
   - Yes (travel/help) → Need location-aware access
   - **Impact**: Security model complexity

---

### **DESIGN SCENARIOS (Pick One to Implement)**

---

## 🎯 DESIGN PRINCIPLES

### **1. Mobile-First**
- Thumb-friendly tap targets (minimum 48x48 pixels)
- Minimal scrolling (key actions above fold)
- Works in portrait orientation (phone in one hand)
- Offline capable (sync when signal available)

### **2. Speed-Optimized**
- **< 30 seconds** to complete one apparatus
- **< 5 taps** from open app to submit
- Auto-save as you type
- Smart defaults (reduce data entry)

### **3. Context-Aware**
- Show only MY assigned work
- Pre-populate equipment details
- Remember last selections
- GPS-tagged submissions

### **4. Error-Proof**
- Required fields clearly marked
- Validation before submit
- Can't mark complete without quality check
- Undo last submission

---

## 📱 APPLICATION SCREENS

### **SCREEN 1: Today's Work Queue**

**Purpose**: Show field tech what they need to work on today

```
┌────────────────────────────────────────┐
│  ☰  RESA Power Field      🔔 👤 Jake   │
├────────────────────────────────────────┤
│                                        │
│  📍 LASNAP16 - Las Vegas NAP          │
│  Today: Friday, Nov 15, 2025          │
│                                        │
│  [──────────────────] 8/15 Complete   │
│  53% Done  |  7 remaining             │
│                                        │
├────────────────────────────────────────┤
│  ASSIGNED TO ME                        │
├────────────────────────────────────────┤
│                                        │
│ ☑️ TX-01 | Transformer #1            │
│    ✓ Completed 9:45 AM | 4.0 hrs      │
│    Acceptable ✓                        │
│                                        │
│ ⏸  CB-01 | Breaker Panel 1A           │
│    In Progress... | 1.2 / 2.5 hrs     │
│    [RESUME →]                          │
│                                        │
│ ⬜ CB-02 | Breaker Panel 1B           │
│    Not Started | Est: 2.5 hrs         │
│    [START →]                           │
│                                        │
│ ⬜ CB-03 | Breaker Panel 1C           │
│    Not Started | Est: 2.5 hrs         │
│    [START →]                           │
│                                        │
│ ⬜ SW-01 | Switchgear Unit A          │
│    Not Started | Est: 6.0 hrs         │
│    [START →]                           │
│                                        │
│ [+ VIEW ALL 7 REMAINING]               │
│                                        │
├────────────────────────────────────────┤
│  QUICK STATS                           │
│  Today: 8 done | 7 to go              │
│  Hours: 22.5 actual / 38.5 estimated  │
└────────────────────────────────────────┘
```

**Key Elements**:
- **Project context** at top (which site am I at?)
- **Progress bar** (visual motivation)
- **Status icons** (✓ = done, ⏸ = working, ⬜ = not started)
- **One-tap actions** [START] or [RESUME]
- **Hour tracking** (actual vs. estimated)
- **Completed items** stay visible (sense of accomplishment)

**Data Sources** (v1.2.0.3 fields):
- Filter: `Apparatus.Assigned_To = Current User` ← **MISSING FIELD**
- Filter: `Apparatus.Project = Current Project` ← EXISTS
- Status: `Apparatus.Completion_Status` ← EXISTS
- Hours: `Apparatus.Labor_Hours` (estimated) ← EXISTS
- Hours: `Apparatus.Actual_Hours` (calculated) ← EXISTS

**Critical Gap**: 
❌ **Apparatus.Assigned_To field does NOT exist** - Cannot filter "my work"  
❌ **Apparatus.Assignment_Date** - Don't know when work was assigned

---

### **SCREEN 2: Apparatus Detail / Work Entry**

**Purpose**: Quick data capture when starting or completing apparatus

**Accessed**: Tap [START] or apparatus name from work queue

```
┌────────────────────────────────────────┐
│  ← Back          CB-01          ✓ Done │
├────────────────────────────────────────┤
│                                        │
│  📋 Breaker Panel 1A                  │
│  Circuit Breaker | Zone: East Wing    │
│                                        │
├────────────────────────────────────────┤
│  EQUIPMENT INFO                        │
├────────────────────────────────────────┤
│  Manufacturer:  Square D               │
│  Serial Number: SQ-12345-2024          │
│  Apparatus #:   CB-01                  │
│                                        │
├────────────────────────────────────────┤
│  WORK TRACKING                         │
├────────────────────────────────────────┤
│                                        │
│  Status:                               │
│  ⬜ Not Started                        │
│  ☑️ In Progress    ← Currently         │
│  ⬜ Complete                           │
│                                        │
│  Hours Estimated:  [2.5] hrs           │
│  Hours Actual:     [1.5] hrs           │
│  Delays/Issues:    [0.5] hrs           │
│    (if any extra time)                 │
│                                        │
│  Started:  10:15 AM  (auto-captured)   │
│                                        │
├────────────────────────────────────────┤
│  QUALITY ASSESSMENT *                  │
├────────────────────────────────────────┤
│                                        │
│  Equipment Condition:                  │
│  🟢 Acceptable                         │
│  🟡 Minor Deficiency                   │
│  🔴 Non-Serviceable                    │
│                                        │
│  Test Standard:                        │
│  ATS ✓ | MTS | ECS | Spec | Other     │
│                                        │
│  Datasheet Complete?                   │
│  ✓ Yes  |  No                          │
│                                        │
├────────────────────────────────────────┤
│  NOTES & PHOTOS                        │
├────────────────────────────────────────┤
│                                        │
│  [+ Add Note]  [📷 Take Photo]        │
│                                        │
│  • Minor corrosion on panel B         │
│    (Added 10:45 AM)                    │
│                                        │
├────────────────────────────────────────┤
│                                        │
│       [SAVE & CONTINUE]                │
│       [COMPLETE APPARATUS →]           │
│                                        │
└────────────────────────────────────────┘

* Required when marking Complete
```

**Key Features**:

1. **Auto-Populated Equipment Info**:
   - Manufacturer, Serial Number, Apparatus # (from Dataverse)
   - Equipment Description
   - No manual typing required

2. **Status Toggle**:
   - Visual buttons (not dropdown)
   - Current status highlighted
   - One-tap to change

3. **Hour Tracking**:
   - Estimated hours (pre-filled from Apparatus.Labor_Hours)
   - Actual hours (manual entry or auto-calculate from start time)
   - Delays (separate field for explaining extra time)

4. **Quality Assessment**:
   - Color-coded buttons (green/yellow/red)
   - Test standard quick-select
   - Datasheet completion toggle
   - **Required before marking Complete**

5. **Notes & Photos**:
   - Voice-to-text for notes
   - Camera integration
   - GPS-tagged timestamps

**Data Mapping** (v1.2.0.3 fields):

| Screen Element | Dataverse Field | Status |
|----------------|----------------|--------|
| Equipment Description | `Apparatus.Equipment_Description` | ✅ EXISTS |
| Manufacturer | `Apparatus.Manufacturer` | ✅ EXISTS |
| Serial Number | `Apparatus.Serial_Number` | ✅ EXISTS |
| Apparatus # | `Apparatus.Apparatus_Number` | ✅ EXISTS |
| Status | `Apparatus.Completion_Status` | ✅ EXISTS (choice) |
| Hours Estimated | `Apparatus.Labor_Hours` | ✅ EXISTS |
| Hours Actual | `Apparatus.Actual_Hours` | ✅ EXISTS (calculated) |
| Delays | `Apparatus.Delays` | ✅ EXISTS |
| Started Time | `Apparatus.Actual_Start` | ❌ **MISSING** |
| Completed Time | `Apparatus.Actual_Complete` | ❌ **MISSING** |
| Equipment Condition | `Apparatus.Apparatus_Assessment` | ✅ EXISTS (v1.2.0.2) |
| Test Standard | `Apparatus.Witness_Test` | ✅ EXISTS (v1.2.0.2) |
| Datasheet Complete | `Apparatus.Datasheet_Completed` | ✅ EXISTS |
| Notes | `Apparatus.Notes` | ✅ EXISTS |

**Critical Gaps**:
❌ **Actual_Start** (DateTime) - Can't auto-calculate actual hours  
❌ **Actual_Complete** (DateTime) - Can't track completion time

---

### **SCREEN 3: Quick Complete Flow**

**Purpose**: Fastest possible path to mark apparatus complete

**Accessed**: Tap [COMPLETE APPARATUS →] from Screen 2

```
┌────────────────────────────────────────┐
│  ← Back      Complete CB-01            │
├────────────────────────────────────────┤
│                                        │
│  ✓ Quick Complete                     │
│  CB-01: Breaker Panel 1A               │
│                                        │
├────────────────────────────────────────┤
│                                        │
│  How long did it take? *               │
│  ┌──────────────────────────┐         │
│  │  [2.5] hours             │         │
│  └──────────────────────────┘         │
│  Estimated: 2.5 hrs ✓ On track        │
│                                        │
│  Any delays or issues?                 │
│  ┌──────────────────────────┐         │
│  │  [0.0] hours             │         │
│  └──────────────────────────┘         │
│  (Leave 0 if no problems)              │
│                                        │
├────────────────────────────────────────┤
│                                        │
│  Equipment Condition? *                │
│  ┌──────────────────────────┐         │
│  │  🟢 Acceptable           │         │
│  └──────────────────────────┘         │
│                                        │
│  Test Standard? *                      │
│  ┌──────────────────────────┐         │
│  │  ATS ✓                   │         │
│  └──────────────────────────┘         │
│                                        │
│  Datasheet Complete? *                 │
│  ┌──────────────────────────┐         │
│  │  ✓ Yes                   │         │
│  └──────────────────────────┘         │
│                                        │
├────────────────────────────────────────┤
│                                        │
│   [✓ COMPLETE & NEXT APPARATUS]        │
│                                        │
│   Completing this will:                │
│   • Mark CB-01 as complete            │
│   • Trigger revenue recognition       │
│   • Move to next apparatus (CB-02)    │
│                                        │
└────────────────────────────────────────┘
```

**Workflow**:
1. **Defaults populate** (from started work)
2. **Adjust hours** if needed (numeric keypad)
3. **Select quality** (one tap)
4. **Select test standard** (one tap)
5. **Toggle datasheet** (one tap)
6. **Submit** → Auto-advances to next apparatus

**Success Criteria**: 
- ✅ **< 30 seconds** to complete
- ✅ **5 taps** maximum (hours, condition, standard, datasheet, submit)
- ✅ **Auto-advance** to keep momentum

**What Happens on Submit**:
1. Set `Apparatus.Completion_Status = "Complete"`
2. Save `Apparatus.Actual_Hours` = entered hours
3. Save `Apparatus.Delays` = delay hours
4. Save `Apparatus.Apparatus_Assessment` = condition
5. Save `Apparatus.Witness_Test` = standard
6. Save `Apparatus.Datasheet_Completed` = Yes
7. Set `Apparatus.Actual_Complete` = NOW() ← **MISSING FIELD**
8. **TRIGGER**: Power Automate flow → Create ApparatusRevenue record ← **FLOW MISSING**

---

### **SCREEN 4: Offline Mode**

**Purpose**: Allow work entry even without cellular/WiFi signal

```
┌────────────────────────────────────────┐
│  ☰  RESA Power Field    ⚠️ OFFLINE 👤  │
├────────────────────────────────────────┤
│                                        │
│  ⚠️ Working Offline                   │
│  Changes will sync when reconnected    │
│                                        │
│  📍 LASNAP16 - Las Vegas NAP          │
│                                        │
├────────────────────────────────────────┤
│  PENDING SYNC (3)                      │
├────────────────────────────────────────┤
│                                        │
│  ⏳ CB-01 | Completed 10:45 AM         │
│     Waiting to sync...                 │
│                                        │
│  ⏳ CB-02 | Completed 11:30 AM         │
│     Waiting to sync...                 │
│                                        │
│  ⏳ CB-03 | In Progress                │
│     Waiting to sync...                 │
│                                        │
├────────────────────────────────────────┤
│                                        │
│  You can continue working offline.     │
│  Data is saved locally and will sync   │
│  automatically when signal returns.    │
│                                        │
│  [RETRY SYNC NOW]                      │
│                                        │
└────────────────────────────────────────┘
```

**Technical Requirements**:
- PowerApps offline cache (SQLite)
- Store completed apparatus locally
- Auto-sync when connection restored
- Conflict resolution (if apparatus updated elsewhere)
- Visual indicator (⚠️ OFFLINE)

---

## 🔧 TECHNICAL REQUIREMENTS

### **PowerApps Canvas App Configuration**

**App Type**: PowerApps Mobile Canvas App

**Data Source**: Dataverse (Direct connection)

**Offline Capability**: 
- Enable offline mode
- Cache strategy: Today's assigned apparatus + last 7 days completed
- Auto-sync on connection

**Security**:
- Row-level security: Users see only THEIR assigned apparatus
- Field-level security: Cannot edit apparatus assigned to others
- Role: "Field Technician" (create, read, update on own apparatus)

### **Required Dataverse Fields** (Current + Missing)

**Existing Fields** (v1.2.0.3):
```
Apparatus Entity:
✅ cr950_apparatusid (Primary Key)
✅ cr950_apparatus_designation (Text)
✅ cr950_apparatus_number (Whole Number - WBS)
✅ cr950_equipment_description (Multi-line Text)
✅ cr950_manufacturer (Text)
✅ cr950_serial_number (Text)
✅ cr950_project (Lookup to Projects)
✅ cr950_scope (Lookup to ProjectScope)
✅ cr950_tasks (Lookup to Tasks)
✅ cr950_completion_status (Choice: Not Started/In Progress/Complete)
✅ cr950_labor_hours (Decimal - estimated)
✅ cr950_delays (Decimal - extra hours)
✅ cr950_actual_hours (Calculated: Labor_Hours + Delays)
✅ cr950_apparatus_assessment (Choice: Acceptable/Minor/Non-Serviceable)
✅ cr950_witness_test (Choice: ATS/MTS/ECS/Spec/Other)
✅ cr950_datasheet_completed (Yes/No)
✅ cr950_notes (Multi-line Text)
```

**MISSING Fields** (Need to add):
```
❌ cr950_assigned_to (Lookup to User)
   - Purpose: Track who is assigned to this apparatus
   - Required for: "My Work" filtering
   - Default: Blank (PM assigns)

❌ cr950_assignment_date (Date Only)
   - Purpose: When was this assigned?
   - Auto-populate: When Assigned_To is set
   
❌ cr950_actual_start (Date Time)
   - Purpose: When did tech start working?
   - Auto-populate: When status changes to "In Progress"
   
❌ cr950_actual_complete (Date Time)
   - Purpose: When was apparatus completed?
   - Auto-populate: When status changes to "Complete"
   - Revenue trigger timestamp
```

### **Views Required**

**1. My Assigned Apparatus (Active)**
```
Filter: 
  Assigned_To = Current User AND
  Completion_Status != "Complete"
  
Sort: 
  Assignment_Date ASC (oldest first)
  
Columns:
  - Apparatus_Designation
  - Equipment_Description
  - Project (lookup)
  - Completion_Status
  - Labor_Hours (estimated)
  - Actual_Hours (if in progress)
```

**2. My Completed Today**
```
Filter:
  Assigned_To = Current User AND
  Completion_Status = "Complete" AND
  Actual_Complete >= Today
  
Sort:
  Actual_Complete DESC (newest first)
  
Columns:
  - Apparatus_Designation
  - Actual_Complete
  - Actual_Hours
  - Apparatus_Assessment
```

### **Power Automate Flow: Revenue Recognition**

**Trigger**: 
- When Apparatus.Completion_Status = "Complete"

**Actions**:
1. Get related ScopeLaborDetail (via Apparatus.Scope)
2. Create ApparatusRevenue record:
   - Apparatus (lookup)
   - Scope_Labor_Detail (lookup)
   - Project (lookup from Apparatus)
   - Labor_Hours = Apparatus.Labor_Hours ← **MISSING IN ApparatusRevenue**
   - Delays = Apparatus.Delays ← **MISSING IN ApparatusRevenue**
   - Labor_Rate = ScopeLaborDetail.Base_Labor_Rate ← **MISSING IN ApparatusRevenue**
   - Revenue_Amount = Labor_Hours × Labor_Rate ← **MISSING IN ApparatusRevenue**

**Status**: ❌ **FLOW DOES NOT EXIST** (Phase 5C priority)

---

## 📊 SUCCESS METRICS

### **Speed Metrics**:
- **< 30 seconds** to complete one apparatus
- **< 5 taps** from open to submit
- **< 2 seconds** app load time

### **Adoption Metrics**:
- **> 90%** of apparatus completed via mobile (not desktop)
- **< 10%** data entry errors
- **< 5%** apparatus require PM correction

### **Efficiency Metrics**:
- **100%** real-time visibility (no end-of-day batching)
- **< 1 hour** from complete to revenue recognized
- **0 hours** manual data aggregation (automatic rollups)

---

## 🚀 IMPLEMENTATION ROADMAP

### **Phase 1: Missing Fields** (30 min)
1. Add `Assigned_To` (User lookup)
2. Add `Assignment_Date` (Date Only)
3. Add `Actual_Start` (Date Time)
4. Add `Actual_Complete` (Date Time)

### **Phase 2: Revenue Fields** (45 min)
1. Add 5 fields to ApparatusRevenue
2. Build Power Automate flow
3. Test revenue trigger

### **Phase 3: Views** (15 min)
1. Create "My Assigned Apparatus" view
2. Create "My Completed Today" view

### **Phase 4: PowerApps Canvas App** (4-6 hours)
1. Screen 1: Work Queue (2 hrs)
2. Screen 2: Apparatus Detail (2 hrs)
3. Screen 3: Quick Complete (1 hr)
4. Screen 4: Offline Mode (1 hr)
5. Testing & refinement (2 hrs)

### **Phase 5: User Testing** (1 week)
1. Deploy to 2-3 test techs
2. Gather feedback
3. Refine UX
4. Train all techs

---

## ✅ NEXT STEPS

**Immediate**:
1. Review this spec with you (validate design)
2. Add 4 missing Apparatus fields (Phase 1)
3. Complete revenue automation (Phase 2)
4. Create views (Phase 3)
5. Build PowerApps canvas app (Phase 4)

**Success Criteria**:
- Field tech can complete apparatus in < 30 seconds
- PM sees real-time progress without asking
- Revenue recognized automatically on completion

---

**STATUS**: Field Tech App fully spec'd - Ready for implementation  
**NEXT**: Build missing fields → Build app → Test with techs
