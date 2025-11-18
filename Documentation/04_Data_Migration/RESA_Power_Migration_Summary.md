# RESA Power - Excel to Power Apps Migration Project
## Session Summary & Resume Instructions

**Date:** November 8, 2025  
**Project Lead:** Jason Swenson  
**Company:** RESA Power (Phoenix Office)

---

## 🎯 PROJECT GOAL

Migrate RESA Power's Excel-based project tracking system to Microsoft Power Apps (Model-Driven App) to enable:
- Real-time field tech data entry (mobile-first)
- Automated progress calculations
- Executive visibility across all projects
- Scalable, modern project management

---

## 🔑 CRITICAL BREAKTHROUGH DECISIONS

### 1. **Model-Driven App > Canvas App**
**Reason:** Field techs primarily use laptops, not mobile devices
**Impact:** 1-2 week build time vs 4-6 weeks for Canvas
**Architecture:** Model-Driven App for desktop + optional Canvas app for mobile later

### 2. **Tech Daily Entry is NON-NEGOTIABLE**
**Core Requirement:** Field techs MUST enter daily updates themselves
**Jason's Quote:** "I DO NOT WANT TO BUILD ANYTHING THAT REQUIRES MY CONSTANT INVOLVEMENT"
**Design Principle:** 45-second daily entry, impossible to break, mobile-accessible

### 3. **Data Collection > Everything Else**
**Philosophy:** "If you don't have the data, what can you do? NOTHING!!!!"
**Priority Order:**
1. Get techs entering data daily (90%+ compliance)
2. Auto-calculate everything from that data
3. Build analytics/reporting on top

### 4. **Accept UKG Parallel Reality**
- UKG (payroll): Techs enter hours → Job number
- Power Apps (tracking): Techs enter hours → Tasks completed
- Weekly reconciliation optional, don't fight the payroll system

---

## 📊 CURRENT STATE ANALYSIS

### **Excel Tracking System (Current)**

**Problems Identified:**
- ✅ 32+ tabs in single project file (Project Alpha example)
- ✅ Techs fear breaking formulas/structure
- ✅ No mobile access
- ✅ Manual rollups and calculations
- ✅ No real-time visibility
- ✅ New projects require 4+ hours of manual setup from estimates
- ✅ Gantt charts unused (techs don't understand/maintain them)

**What Actually Works:**
- ✅ Quantity-driven tracking (19 transformers quoted, 17 completed)
- ✅ Hours per unit estimates (12 hrs/transformer)
- ✅ Apparatus-based structure (specific equipment types)
- ✅ Scope organization (MV, House, Critical Blocks, etc.)

### **Estimator System (Current)**

**File Type:** Excel with VBA (.xlsm)
**Structure:**
- Equipment Reference sheet (labor hours per apparatus type)
- Project Spec sheet (NETA standards, testing requirements)
- Scope sheets (Fitout MV, Fitout House, Critical Block 1-3, etc.)
- Line items: QTY × Apparatus Type × Hrs/Unit = Total Hours

**Pain Point:** 
- Estimates created months/years before project starts
- Manual recreation in tracker when awarded
- Need: Estimate → Project conversion (30 seconds vs 4 hours)

---

## 💎 PROOF OF CONCEPT - LASNAP16 PROJECT

### **Vegas Project Success Story**

**File Analyzed:** RESA_Power_-_LASNAP16_MASTER.xlsm

**Live Data:**
- **Project:** LASNAP LAS16 (Las Vegas)
- **Client:** LASNAP
- **Job #:** 634414
- **Lead:** Brandon Valdavis
- **Status:** ACTIVELY BEING USED ✅

**Data Volume:**
- 1,905 Total Tasks
- 421 Completed Tasks (22% complete)
- $177,027.53 Revenue Tracked
- 27 Scopes (PPM01-24, GDB, HOUSE, MV, RPPs)

**Key Insight:** Vegas team IS using the tracker, data IS being entered, structure WORKS. Only issue: Excel limitations (date formulas, fear of breaking, etc.)

### **Extracted Data Files**

Successfully extracted and prepared for import:

1. **Project_Import.csv**
   - 1 project record (LASNAP16)
   - Fields: Job #, Client, Lead, Location, Status

2. **Scopes_Import.csv**
   - 27 scope records (PPM01-PPM24, GDB, HOUSE, MV, RPPs)
   - Fields: Scope Name, Drawing Ref, Total Hours, Status

3. **Tasks_Import.csv**
   - 1,905 task records
   - Fields: Task Name, Apparatus Type, Qty Quoted, Qty Completed, Hrs/Unit, Total Hrs, Status

**Files Located:** User uploads folder (ready for download)

---

## 🏗️ PROPOSED DATAVERSE STRUCTURE

### **Core Tables**

#### **1. Project** (Container)
```
Fields:
├─ Job Number (text, from UKG)
├─ Project Name (text)
├─ Client (text)
├─ Location (text)
├─ Status (choice: Active/On Hold/Complete)
├─ Start Date (date)
├─ Project Manager (lookup to User)
├─ Lead Technician (lookup to User)
└─ Total Quoted Hours (rollup from Scopes)
```

#### **2. Scope** (Work Phases)
```
Fields:
├─ Project (lookup)
├─ Scope Name (text: "PPM01", "Fitout MV", etc.)
├─ Drawing Reference (text)
├─ Description (text)
├─ Total Quoted Hours (rollup from Tasks)
├─ Actual Hours (rollup from Tasks)
├─ % Complete (calculated)
└─ Status (calculated from tasks)
```

#### **3. Task** (Equipment Line Items)
```
Fields:
├─ Project (lookup)
├─ Scope (lookup)
├─ Task Name (text: "Pad Mount Transformers")
├─ Apparatus Type (text: "Transformer - Pad Mount Oil")
├─ NETA Section (text: "7.2")
│
├─ Quantity Quoted (number)
├─ Quantity Completed (number) ← TECHS UPDATE
├─ Quantity Remaining (calculated)
│
├─ Hours per Unit (decimal)
├─ Total Hours Quoted (calculated: Qty × Hrs/Unit)
├─ Actual Hours (from Time Entries)
├─ Hours Remaining (calculated)
│
├─ % Complete (calculated: Qty Completed / Qty Quoted)
└─ Status (calculated: Not Started/In Progress/Complete)
```

#### **4. Daily Entry** (Tech Submissions)
```
Fields:
├─ Tech (lookup to User)
├─ Date (date)
├─ Project (lookup)
├─ Total Hours (number)
├─ Notes (text, optional)
└─ Status (choice: Draft/Submitted)
```

#### **5. Task Completion** (Daily Entry Details)
```
Fields:
├─ Daily Entry (lookup to parent)
├─ Task (lookup)
├─ Quantity Completed Today (number)
├─ Notes (text, optional)
└─ Photos (file attachments, optional)
```

**Relationship:** One Daily Entry → Many Task Completions

---

## 📱 THREE VIEWS ARCHITECTURE

### **View 1: Tech Mobile App (Canvas App - Future)**

**Purpose:** 45-second daily entry  
**Users:** All field techs  
**Critical Features:**
- Select project (from recent)
- Enter hours
- Check off tasks worked on
- Enter quantities completed
- Submit (syncs even offline)

**Success Metric:** 90%+ daily submission rate

### **View 2: PM Dashboard (Model-Driven App - PRIMARY)**

**Purpose:** Portfolio management, zero manual data entry  
**Users:** Jason, Site Leads, GM  
**Features:**
- All projects view (list/kanban)
- Drill-down to scopes/tasks
- Real-time status updates
- Client report generator
- Estimate import wizard
- Time reconciliation (UKG vs tracked)

**Success Metric:** 60% time savings for PM tasks

### **View 3: Executive Dashboard (Power BI)**

**Purpose:** High-level metrics  
**Users:** GM/VP, Regional leadership  
**Features:**
- Portfolio health (on-track/at-risk/critical)
- Utilization rates
- Budget performance
- Revenue tracking
- Trend analysis

**Success Metric:** Real-time leadership visibility

---

## 🚀 8-WEEK IMPLEMENTATION ROADMAP

### **Phase 1: Foundation (Weeks 1-2)**
- [ ] Create Dataverse environment
- [ ] Build core tables (Project, Scope, Task)
- [ ] Import LASNAP16 data (proof of concept)
- [ ] Test data integrity

### **Phase 2: Model-Driven App Shell (Weeks 3-4)**
- [ ] Create Model-Driven app
- [ ] Build Project list view
- [ ] Build Scope/Task drill-downs
- [ ] Create basic forms
- [ ] Test with Jason

### **Phase 3: Tech Entry Interface (Weeks 4-5)**
- [ ] Build tech entry forms (Model-Driven first)
- [ ] Daily Entry + Task Completion tables
- [ ] Test with 2-3 champion techs
- [ ] Iterate based on feedback

### **Phase 4: Automation & Reports (Weeks 6-7)**
- [ ] Build auto-calculations (rollups, formulas)
- [ ] Create status report templates
- [ ] Build estimate import wizard
- [ ] Test end-to-end workflows

### **Phase 5: Pilot (Week 8)**
- [ ] Full team training
- [ ] One project piloted completely
- [ ] Parallel run with Excel (safety net)
- [ ] Collect feedback, fix bugs

### **Phase 6: Rollout (Week 9+)**
- [ ] Migrate all active projects
- [ ] Excel becomes backup only
- [ ] Monitor compliance
- [ ] Continuous improvement

---

## 📋 NEXT SESSION ACTION ITEMS

### **Immediate Priority: Import LASNAP16 Data**

**Step 1: Download Extracted Files**
Files are ready in uploads folder:
- Project_Import.csv
- Scopes_Import.csv  
- Tasks_Import.csv

**Step 2: Create Dataverse Environment**
```
Power Platform Admin Center:
1. Create new environment: "RESA Power Production"
2. Add Dataverse database
3. Enable Dynamics 365 apps
4. Set security roles
```

**Step 3: Build Tables**
```
Using Table Designer or Solution:
1. Create Project table (schema above)
2. Create Scope table (schema above)
3. Create Task table (schema above)
4. Set up relationships (lookups)
5. Configure rollup fields
```

**Step 4: Import Data**
```
Power Apps Data Import:
1. Import Project_Import.csv → Project table
2. Import Scopes_Import.csv → Scope table
3. Import Tasks_Import.csv → Task table
4. Verify relationships connected
5. Test rollup calculations
```

**Step 5: Build Basic Model-Driven App**
```
App Designer:
1. Create new Model-Driven app
2. Add Project table (Active Projects view)
3. Add Scope table (related to Project)
4. Add Task table (related to Scope)
5. Publish and test
```

---

## 🎯 CRITICAL SUCCESS FACTORS

### **1. Tech Adoption**
- Make daily entry faster than current process
- Make it impossible to break
- Mobile-accessible (even if desktop-first)
- Visible accountability (daily dashboard review)

### **2. Leadership Mandate**
- GM/VP must require daily submissions
- Not optional, core business process
- Public recognition for compliance
- Address non-compliance immediately

### **3. Prove Value Fast**
- Week 4: Show time savings (dashboard vs Excel hell)
- Week 6: Generate client report in 30 seconds
- Week 8: Demonstrate real-time visibility
- Month 3: Show productivity metrics

### **4. Safety Net**
- First 8 weeks: Parallel run with Excel
- Excel becomes backup, not primary
- Build confidence before full cutover
- Can always revert if needed

---

## 💬 KEY QUOTES FROM SESSION

> "I DO NOT WANT TO BUILD ANYTHING THAT REQUIRES MY CONSTANT INVOLVEMENT. Field technicians will provide those details each day themselves."

> "If you don't have the data, what can you do? NOTHING!!!!"

> "There is a genuine fear they will 'break' or mess up the current structure. Formulas overwritten, deleted, etc."

> "The system we should have needs this data to pass along directly into the PM tracker."

> "We're running on systems from the 90's, while everyone else has migrated to cloud based architecture with seamless data transfer."

---

## 🔗 REFERENCE FILES

**Project Files Analyzed:**
1. RESA_Power_-_Project_Data_Entry_MASTER.xlsm (Template/Generator)
2. 1762624613189_Project_Alpha_Tracker_MASTER.xlsx (Phoenix project)
3. 1762625129041_Estimator_-_Goodman_GIC_Soto__Fitout_.xlsm (Estimate example)
4. RESA_Power_-_LASNAP16_MASTER.xlsm (Vegas active project - EXTRACTED)

**Documentation in Project:**
- Desktop_Platform_Strategy.md
- Canvas_App_Build_Guide.md
- Visual_Design_Guide.md
- Implementation_Checklist.md
- Architecture_Diagrams.md
- RESA_Power_Modernization_Guide.md

---

## 📞 RESUME INSTRUCTIONS FOR NEW CHAT

**To Resume This Project, Say:**

"I'm Jason from RESA Power. We were working on migrating our Excel project tracker to Power Apps. I have:

1. Three CSV files ready for import (Project, Scopes, Tasks from LASNAP16)
2. Data model defined for Dataverse
3. Decision to use Model-Driven App (not Canvas)
4. 8-week implementation roadmap
5. Summary document: RESA_Power_Migration_Summary.md

Next step: Help me import the LASNAP16 data into Dataverse and build the first Model-Driven app view."

**Key Context to Provide:**
- I'm the PM/Estimator at RESA Power Phoenix
- We track electrical testing projects
- Field techs need to enter daily progress (quantity-based)
- Current Excel system works but doesn't scale
- LASNAP16 is proof it works (1,905 tasks, actively used)
- Tech daily entry is non-negotiable requirement

---

## ✅ WHAT'S BEEN ACCOMPLISHED

✅ Analyzed current Excel tracking system (3 project files)  
✅ Analyzed estimator structure  
✅ Identified pain points and requirements  
✅ Made critical architecture decision (Model-Driven > Canvas)  
✅ Defined data model (5 tables, relationships)  
✅ Extracted real production data (LASNAP16)  
✅ Created import-ready CSV files  
✅ Designed three-view architecture  
✅ Built 8-week implementation roadmap  
✅ Documented everything for handoff  

---

## 🎯 NEXT MILESTONE

**Goal:** LASNAP16 project fully functional in Power Apps within 2 weeks

**Deliverable:** Model-Driven app showing:
- 1 project (LASNAP16)
- 27 scopes
- 1,905 tasks
- Auto-calculated rollups
- Basic views and forms

**Success Criteria:**
- Jason can navigate project → scopes → tasks
- % complete calculates automatically
- Can see which tasks are done vs pending
- Faster than opening Excel file

---

**Document Created:** November 8, 2025  
**Session Duration:** ~3 hours  
**Status:** Ready to resume in new chat  
**Confidence Level:** HIGH - Clear path forward with real data

---

## 🚀 LET'S BUILD THIS!

The foundation is solid. The data is real. The path is clear.

**Next session: Import → Build → Test → Win.** 🎯
