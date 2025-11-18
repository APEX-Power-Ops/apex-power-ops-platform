# USER EXPERIENCE & SYSTEM ARCHITECTURE SPECIFICATION

**Purpose**: Define the complete user-centric system from field technician to executive leadership  
**Approach**: Top-down (strategic vision) + Bottom-up (daily operations) = Seamless integration  
**Date**: November 15, 2025  
**Version**: 1.0 - Foundation Document

---

## 🎯 EXECUTIVE SUMMARY

**What We're Building**: A complete field-to-executive project management system for RESA Power's Southwest Region (Phoenix, Las Vegas, Denver, San Diego) that makes every user's job easier while providing comprehensive visibility at all organizational levels.

**Why It Matters**: 
- Grew from 3 techs (2021) to 15-18+ techs across 4 locations
- Manual Excel-based tracking cannot scale
- No corporate solution available despite growth
- Regional VP needs multi-location visibility
- Field techs need simple, mobile-friendly tools
- PMs need real-time progress and financial tracking

**Design Philosophy**: 
> "Every field, form, view, and workflow exists to make someone's job easier and contribute to seamless project management across all levels."

---

## 🎯 CRITICAL ARCHITECTURAL DECISIONS

**Purpose**: Document the key decisions that need stakeholder input and their CASCADE EFFECTS across the system.

---

### **DECISION 1: Work Assignment Model**

**Question**: How should apparatus work be assigned to field technicians?

#### **OPTION A: Individual Assignment (One Tech = One Apparatus)**

**What It Means**:
- PM assigns: "Jake, you own CB-01 through CB-15"
- Jake sees HIS 15 apparatus
- Mike sees HIS 20 apparatus
- Each tech responsible for their assigned work

**System Impact**:
```
FIELDS REQUIRED:
✅ Apparatus.Assigned_To (User lookup - single select)
✅ Apparatus.Assignment_Date (Date)

VIEWS REQUIRED:
✅ "My Assigned Work" (filter: Assigned_To = Current User)
✅ "Unassigned Apparatus" (filter: Assigned_To = blank)

SECURITY:
✅ Field tech can ONLY edit their assigned apparatus
✅ Cannot see other techs' assigned work

MOBILE VIEW:
📱 "MY TASKS (15)" - Simple, focused list
```

**Pros**:
- ✅ Clear accountability (Jake owns CB-01, period)
- ✅ Easy utilization tracking (Jake completed 15 apparatus today)
- ✅ Simple security (can only edit your own)
- ✅ Performance reviews straightforward

**Cons**:
- ❌ Doesn't support pair/team work (Jake + Mike on TX-01)
- ❌ Rigid (can't help teammate without reassignment)
- ❌ PM workload (must assign every apparatus)
- ❌ Not how work actually happens?

**Cascade Effects**:
- **Revenue Recognition**: Credit goes to assigned person only
- **Utilization Tracking**: Simple (hours per tech per day)
- **PM Workload**: HIGH (must plan every assignment)
- **Field Flexibility**: LOW (can't grab available work)
- **Reporting**: Easy ("Jake completed 15, Mike completed 20")

---

#### **OPTION B: Team Assignment (Team = Shared Work Pool)**

**What It Means**:
- PM assigns: "Phoenix Team A (Jake, Mike, Carlos) → LASNAP16"
- All three see ALL 45 apparatus for the project
- Anyone can start/complete any apparatus
- Self-organizing (techs balance workload)

**System Impact**:
```
FIELDS REQUIRED:
✅ Project.Assigned_Team (User lookup - MULTI-SELECT)
✅ Apparatus.Completed_By (User lookup - auto-set on complete)
✅ Apparatus.Worked_By (User lookup - MULTI-SELECT for contributors)
❌ NO Apparatus.Assigned_To field needed

VIEWS REQUIRED:
✅ "My Team's Project Work" (filter: Project.Assigned_Team contains Current User)
✅ "Available Work" (status = Not Started, in my team's projects)
✅ "In Progress" (show who's working on what)

SECURITY:
✅ Team members can edit ANY apparatus in their projects
✅ Cannot see other teams' projects

MOBILE VIEW:
📱 "OUR TEAM'S WORK (45)" 
📱 Shows: "⏸ CB-03 (Mike working...)" 
📱 Can grab: "⬜ CB-04 (available)"
```

**Pros**:
- ✅ Supports pair/team work naturally
- ✅ Flexible (grab work as you finish)
- ✅ Less PM workload (assign project, not apparatus)
- ✅ Matches real workflow (experienced techs balance load)
- ✅ Senior can help junior mid-project

**Cons**:
- ❌ Less clear accountability (who's responsible for CB-01?)
- ❌ Utilization tracking complex (need Completed_By tracking)
- ❌ Could cause confusion ("I thought you were doing CB-01?")
- ❌ Risk of duplicate work or gaps

**Cascade Effects**:
- **Revenue Recognition**: Credit to Completed_By person
- **Utilization Tracking**: COMPLEX (need to track who completed what)
- **PM Workload**: LOW (assign team to project, done)
- **Field Flexibility**: HIGH (self-organizing)
- **Reporting**: HARDER (need to aggregate by Completed_By)

---

#### **OPTION C: Hybrid (Pre-Assigned + Pool) [RECOMMENDED]**

**What It Means**:
- PM assigns critical/complex items: "Jake → TX-01, TX-02 (transformers)"
- Rest goes into team pool: "Team → CB-01 through CB-30 (grab as needed)"
- Best of both: Planning + Flexibility

**System Impact**:
```
FIELDS REQUIRED:
✅ Project.Assigned_Team (User lookup - MULTI-SELECT)
✅ Apparatus.Assigned_To_Primary (User lookup - OPTIONAL)
✅ Apparatus.Assigned_To_Team (User lookup - MULTI-SELECT - OPTIONAL)
✅ Apparatus.Completed_By (User lookup - auto-set)
✅ Apparatus.Worked_By (User lookup - MULTI-SELECT)

VIEWS REQUIRED:
✅ "My Assigned Tasks" (filter: Assigned_To_Primary = Current User)
✅ "My Team's Pool" (filter: Assigned_To_Primary = blank AND Project in my team)
✅ "In Progress" (show who's working on what)

SECURITY:
✅ Can edit: (Assigned_To_Primary = me) OR (Project.Team contains me)

MOBILE VIEW:
📱 "MY TASKS (5)" - PM specifically assigned to me
📱 "TEAM POOL (30)" - Available for anyone
📱 "IN PROGRESS (10)" - What teammates are working on
```

**Pros**:
- ✅ Supports both individual + team work
- ✅ PM can plan critical items
- ✅ Field has flexibility for routine work
- ✅ Clear accountability where needed
- ✅ Matches real workflow (mix of assigned + available)

**Cons**:
- ❌ Most complex data model
- ❌ More fields to maintain
- ❌ PM must decide: "Assign this one or put in pool?"
- ❌ Requires training ("When do I grab from pool vs. wait for assignment?")

**Cascade Effects**:
- **Revenue Recognition**: Credit to Completed_By (regardless of assignment)
- **Utilization Tracking**: MEDIUM complexity (track assignments + completions)
- **PM Workload**: MEDIUM (assign critical items, rest is pool)
- **Field Flexibility**: HIGH (grab from pool when done with assigned)
- **Reporting**: MEDIUM (show assigned vs. completed separately)

---

### **DECISION 2: Team Structure Definition**

**Question**: How do we define a "team"?

#### **OPTION A: Formal Crews (Permanent Assignment)**

**What It Means**:
- Phoenix Team A: Jake (lead), Mike, Carlos
- Phoenix Team B: Sarah (lead), Tom, Lisa
- Teams stay together across projects

**System Impact**:
```
NEW ENTITY NEEDED:
✅ "Team" entity
   - Team_Name ("Phoenix Team A")
   - Team_Lead (User lookup)
   - Team_Members (User lookup - multi-select)
   - Location (BusinessUnit lookup)

FIELDS REQUIRED:
✅ Project.Assigned_Team (lookup to Team entity)
✅ User.Primary_Team (lookup to Team entity)

VIEWS REQUIRED:
✅ "My Team's Projects" (all projects assigned to my team)
✅ "Team Performance" (compare Team A vs. Team B)
```

**Pros**:
- ✅ Clear team identity
- ✅ Team performance tracking
- ✅ Consistent collaboration (same people)
- ✅ Team lead accountability

**Cons**:
- ❌ Inflexible (what if Mike is sick?)
- ❌ Requires team entity/management
- ❌ Harder to balance workload across teams

**Cascade Effects**:
- **Scheduling**: Assign projects to teams, not individuals
- **Reporting**: Team-level metrics (Team A completed 50 apparatus this week)
- **Management**: Team leads manage their crew
- **Flexibility**: LOW (can't easily move people between teams)

---

#### **OPTION B: Dynamic Teams (Project-Based Assignment)**

**What It Means**:
- LASNAP16: Jake, Mike, Carlos
- PHXGRID09: Jake, Sarah, Tom
- Teams change based on project needs

**System Impact**:
```
NO NEW ENTITY NEEDED:
✅ Project.Assigned_Team (User lookup - multi-select)
   - Simple list of users per project

VIEWS REQUIRED:
✅ "My Projects" (all projects where I'm in Assigned_Team)
✅ "Available Techs" (users not assigned to active projects)
```

**Pros**:
- ✅ Flexible (match skills to project needs)
- ✅ Simple data model
- ✅ Easy workload balancing
- ✅ No team entity to manage

**Cons**:
- ❌ No team identity/continuity
- ❌ Harder to track "team" performance
- ❌ Less clear leadership structure

**Cascade Effects**:
- **Scheduling**: Assign individuals to each project
- **Reporting**: Individual metrics only (Jake completed X, Mike completed Y)
- **Management**: PM manages individuals, not teams
- **Flexibility**: HIGH (change assignments per project)

---

### **DECISION 3: Visibility Boundaries**

**Question**: What should each field tech see in their mobile app?

#### **OPTION A: Only MY Assigned Work**

**What It Means**:
- Jake sees: 15 apparatus assigned to Jake only
- Cannot see Mike's work, Carlos's work, or unassigned work

**System Impact**:
```
VIEW FILTER:
Assigned_To = Current User AND Completion_Status != Complete

SECURITY:
Field Tech role: Can ONLY read/write own assigned apparatus
```

**Pros**: Simple, focused, no distractions  
**Cons**: Can't see project context, can't help teammates  
**Cascade**: Rigid, requires PM to reassign if help needed

---

#### **OPTION B: MY Team's Project Work**

**What It Means**:
- Jake sees: All 45 apparatus in LASNAP16 (his project)
- Can see what Mike/Carlos are working on
- Can grab unassigned work

**System Impact**:
```
VIEW FILTER:
Project IN (Projects where Current User is in Assigned_Team)

SECURITY:
Field Tech role: Can read/write ANY apparatus in their team's projects
```

**Pros**: Context, collaboration, flexibility  
**Cons**: More data, could be overwhelming  
**Cascade**: Enables self-organizing, requires trust

---

#### **OPTION C: Everything in MY Location**

**What It Means**:
- Jake (Phoenix) sees: ALL Phoenix projects, all teams
- Can see Vegas projects if he's traveling there

**System Impact**:
```
VIEW FILTER:
Project.Location = Current User's BusinessUnit

SECURITY:
Field Tech role: Can read ALL location projects, write only assigned ones
```

**Pros**: Maximum visibility, can help anywhere  
**Cons**: Too much data, security concerns  
**Cascade**: Requires location-based security model

---

### **DECISION 4: Accountability Tracking**

**Question**: When apparatus is completed, who gets credit?

#### **OPTION A: Assigned Person Only**

**What It Means**:
- CB-01 assigned to Jake → Jake gets credit regardless of who completed it
- Utilization = assigned hours

**System Impact**:
```
REPORTING:
Jake's Completed Apparatus = COUNT(Assigned_To = Jake AND Status = Complete)
Jake's Hours = SUM(Assigned_To = Jake, Labor_Hours)
```

**Pros**: Simple, matches assignment  
**Cons**: Inaccurate if Mike helped Jake  
**Cascade**: Utilization reports easy but potentially wrong

---

#### **OPTION B: Completed By (Whoever Marked Complete)**

**What It Means**:
- Jake started CB-01, Mike finished it → Mike gets credit
- Utilization = completed hours

**System Impact**:
```
FIELD REQUIRED:
✅ Apparatus.Completed_By (User lookup - auto-set on status change to Complete)

REPORTING:
Mike's Completed Apparatus = COUNT(Completed_By = Mike)
Mike's Hours = SUM(Completed_By = Mike, Labor_Hours)
```

**Pros**: Accurate for who did the work  
**Cons**: Ignores contributors (Jake helped but Mike finished)  
**Cascade**: Simple tracking, but incomplete picture

---

#### **OPTION C: All Contributors (Multi-Select)**

**What It Means**:
- Jake and Mike both worked on TX-01 → Both get partial credit
- Manually track: "Jake: 3 hrs, Mike: 2 hrs on same apparatus"

**System Impact**:
```
FIELDS REQUIRED:
✅ Apparatus.Worked_By (User lookup - MULTI-SELECT)
✅ ApparatusContributors entity (many-to-many)
   - Apparatus (lookup)
   - User (lookup)
   - Hours_Contributed (Decimal)

REPORTING:
Jake's Hours = SUM(ApparatusContributors where User = Jake, Hours_Contributed)
```

**Pros**: Most accurate, supports pair work  
**Cons**: COMPLEX, requires field techs to split hours  
**Cascade**: High data entry burden, may not be worth accuracy gain

---

### **DECISION 5: Multi-Location Coordination**

**Question**: Can techs work across locations?

#### **OPTION A: Strict Location Boundaries**

**What It Means**:
- Phoenix techs see ONLY Phoenix projects
- Vegas techs see ONLY Vegas projects
- No cross-location visibility

**System Impact**:
```
SECURITY:
Field Tech role: Can only see projects where Project.Location = User.Home_Location
```

**Pros**: Simple, clear boundaries  
**Cons**: Inflexible (if Jake travels to Vegas, must manually change access)  
**Cascade**: Easy to implement, but requires manual overrides for travel

---

#### **OPTION B: Dynamic Location Access**

**What It Means**:
- Jake (Phoenix) can see Vegas projects IF he's assigned to them
- Assignment drives access, not home location

**System Impact**:
```
FIELD REQUIRED:
✅ User.Home_Location (BusinessUnit lookup)
✅ User.Current_Location (BusinessUnit lookup - changes when traveling)

SECURITY:
Field Tech role: Can see projects where:
  - Project.Assigned_Team contains Current User
  OR
  - Project.Location = User.Current_Location (if cross-location help enabled)
```

**Pros**: Flexible, supports travel and cross-location help  
**Cons**: More complex security, requires location tracking  
**Cascade**: Enables resource sharing across locations, but adds complexity

---

## 🎯 RECOMMENDATION MATRIX

| Decision | Recommended Option | Why | Prerequisites |
|----------|-------------------|-----|---------------|
| **Assignment Model** | **Option C: Hybrid** | Matches real workflow (some planned, some flexible) | Project.Assigned_Team + Apparatus.Assigned_To_Primary (optional) |
| **Team Structure** | **Option B: Dynamic** | Start simple, add formal teams later if needed | Project.Assigned_Team (multi-select) only |
| **Visibility** | **Option B: Team's Projects** | Enables collaboration without overwhelming data | Security: Can edit team's projects only |
| **Accountability** | **Option B: Completed By** | Simple + accurate enough for most needs | Apparatus.Completed_By (auto-set) |
| **Multi-Location** | **Option B: Dynamic Access** | Future-proof for regional growth | User.Home_Location + assignment-based access |

**Rationale**: Start with flexibility and simplicity. Can add formal teams, contribution tracking, and location restrictions later if business needs justify the complexity.

---

## 👥 USER PERSONAS & ROLES

**Complete Role Hierarchy**:
```
┌─────────────────────────────────────────┐
│         VP/GM (Regional Executive)      │ ← Strategic oversight, 4 locations
├─────────────────────────────────────────┤
│      Location Manager (Branch Head)     │ ← P&L, resource allocation per location
├─────────────────────────────────────────┤
│  Operations Coordinator (Office Manager)│ ← Day-to-day coordination, scheduling
│  Account Manager (Sales)                │ ← Customer relationships, quotes → projects
│  Project Manager (You)                  │ ← Project execution, scope management
├─────────────────────────────────────────┤
│      Job Lead (Senior Field Tech)       │ ← Field supervision, quality oversight
├─────────────────────────────────────────┤
│      Field Technician (Tester)          │ ← Apparatus testing, data collection
└─────────────────────────────────────────┘
```

---

### **PERSONA 1: Field Technician (Tester)**
**Primary Location**: On-site at customer facilities  
**Device**: Mobile phone or tablet  
**Technical Skill**: Basic (focus on electrical work, not software)  
**Time Available**: Minimal (between apparatus tests)  
**Reports To**: Job Lead

#### **What They Need to SEE**:
```
MY TODAY VIEW (Mobile-Optimized)
┌─────────────────────────────────────┐
│ My Assigned Apparatus (Today)       │
├─────────────────────────────────────┤
│ □ CB-01  |  Breaker Panel 1A        │
│   Est: 2.5 hrs  |  Not Started      │
│                                      │
│ □ CB-02  |  Breaker Panel 1B        │
│   Est: 2.5 hrs  |  Not Started      │
│                                      │
│ ☑ TX-01  |  Transformer #1          │
│   4.0 hrs  |  Completed 2:15 PM     │
└─────────────────────────────────────┘
```

**Key Information Needs**:
- ✅ **What to work on today** (assigned apparatus list)
- ✅ **Equipment details** (manufacturer, serial, description)
- ✅ **Estimated hours** (how long should this take?)
- ✅ **Test standards** (ATS/MTS/ECS requirements)
- ✅ **Quality checklist** (assessment criteria)
- ✅ **Simple status update** (Not Started → In Progress → Complete)

#### **What They Need to DO**:
```
APPARATUS QUICK CAPTURE (30 seconds max)
┌─────────────────────────────────────┐
│ CB-01: Breaker Panel 1A             │
├─────────────────────────────────────┤
│ Status:      [x] Complete           │
│ Hours:       [2.5]  (vs 2.5 est)    │
│ Delays:      [0.5]  (explain why)   │
│ Assessment:  [x] Acceptable         │
│ Witness:     [x] ATS                │
│ Datasheet:   [x] Complete           │
│ Notes:       [Add quick note...]    │
│                                      │
│         [SUBMIT & NEXT →]           │
└─────────────────────────────────────┘
```

**Critical Actions**:
1. **View assigned work** - Filter: My apparatus, Today/This Week
2. **Update status** - One-tap status change (Start/Complete)
3. **Log hours** - Quick entry (actual hours + any delays)
4. **Quality check** - Simple dropdown selections
5. **Add notes** - Voice-to-text for deficiencies
6. **Attach photo** - Equipment datasheet or issues

#### **Success Metrics** (What makes their job easier):
- ⏱️ **< 1 minute** to complete apparatus (from field)
- 📱 **Mobile-first** design (thumb-friendly buttons)
- 🔌 **Offline capable** (sync when back online)
- 🎯 **Clear next action** (no guessing what to do)
- ✅ **Immediate feedback** ("Great! 3 more to go today")

#### **Pain Points to AVOID**:
- ❌ Complex forms with 20+ fields
- ❌ Requiring laptop/desktop access
- ❌ Unclear apparatus descriptions
- ❌ No visibility into "what's next"
- ❌ Manual hour calculations

---

### **PERSONA 2: Job Lead (Senior Field Tech)**
**Primary Location**: On-site (leads field crew)  
**Device**: Mobile phone/tablet (same as techs, but needs more data)  
**Technical Skill**: Advanced (experienced electrician + leadership)  
**Focus**: Field supervision, quality control, team coordination  
**Reports To**: Project Manager

#### **What They Need to SEE**:
```
JOB LEAD MOBILE VIEW
┌─────────────────────────────────────┐
│ LASNAP16 - Las Vegas NAP            │
│ Lead: Jake  |  Crew: Mike, Carlos   │
│ [──────────] 45% Complete           │
├─────────────────────────────────────┤
│ MY CREW'S WORK TODAY                │
├─────────────────────────────────────┤
│ Jake (Me):                          │
│ ☑️ TX-01 Complete (4.0 hrs)         │
│ ⏸  TX-02 In Progress (2.5 / 6 hrs) │
│                                      │
│ Mike:                               │
│ ☑️ CB-01 Complete (2.5 hrs)         │
│ ⏸  CB-02 In Progress (1.0 / 2.5 hrs)│
│                                      │
│ Carlos:                             │
│ ⏸  CB-03 In Progress (0.5 / 2.5 hrs)│
│ ⬜ CB-04 Not Started                │
│                                      │
│ [+ 40 MORE APPARATUS]               │
│                                      │
├─────────────────────────────────────┤
│ ATTENTION NEEDED ⚠️                 │
│ • CB-15: Non-serviceable (review)   │
│ • TX-03: Delayed 2 hrs (check)      │
└─────────────────────────────────────┘
```

**Key Information Needs**:
- ✅ **Whole crew's work** (not just mine)
- ✅ **Who's working on what** (avoid conflicts)
- ✅ **Progress by person** (is Mike falling behind?)
- ✅ **Quality issues** (escalate non-serviceable immediately)
- ✅ **Delays/blockers** (understand why taking longer)
- ✅ **Available work** (what to grab next as a crew)

#### **What They Need to DO**:
1. **Assign work within crew** (if PM assigns project to crew, lead divides work)
2. **Monitor crew progress** (make sure everyone on track)
3. **Quality oversight** (review assessments before finalizing)
4. **Escalate issues** (contact PM for non-serviceable equipment)
5. **Balance workload** (move Carlos to help Mike if CB-02 taking too long)
6. **Update PM** (end-of-day summary or as-needed)
7. **Complete apparatus** (same as tech, but also does leadership work)

#### **Success Metrics**:
- ⏱️ **< 2 minutes** to check entire crew status
- 🎯 **Proactive issue detection** (see problems before they escalate)
- 👥 **Team coordination** (avoid duplicate work, balance load)
- 📱 **Mobile-first** (can't leave the field to use desktop)

#### **Pain Points to AVOID**:
- ❌ Can't see crew's work (blind to what teammates are doing)
- ❌ Manual check-ins ("Jake, where are you on CB-01?")
- ❌ Quality issues discovered too late
- ❌ PM asks "How's the crew doing?" and lead doesn't know

**Critical Question for Stakeholders**:
- **Does Job Lead assign apparatus to techs?** Or just PM?
- **Does Job Lead approve completed apparatus?** Or auto-recognize revenue?
- **How many crews per location?** (1 crew = 1 lead, or multiple crews?)

---

### **PERSONA 3: Project Manager (You)**
**Primary Location**: Office (Phoenix, Vegas, Denver, SD)  
**Device**: Desktop computer, occasional mobile  
**Technical Skill**: Intermediate (understands project management)  
**Focus**: Scope management, progress tracking, customer updates  
**Reports To**: Location Manager or Operations Coordinator

#### **What They Need to SEE**:
```
PROJECT DASHBOARD (Desktop)
┌──────────────────────────────────────────────────┐
│ Project: LASNAP16 - Las Vegas NAP Substation    │
│ Location: Las Vegas  |  Status: Active          │
│ Customer: Nevada Power  |  Start: 10/15/2025    │
├──────────────────────────────────────────────────┤
│ PROGRESS OVERVIEW                                │
│ ████████░░░░░░░░░ 45.2% Complete                 │
│                                                  │
│ 95/210 Apparatus Complete  |  426.5 / 943 hrs   │
│ 12/18 Tasks Complete       |  Est. Finish: 12/1 │
├──────────────────────────────────────────────────┤
│ SCOPE BREAKDOWN                                  │
│ ┌─ Switchgear (Scope 1)      67% │ $45,200      │
│ ├─ Transformers (Scope 2)    34% │ $28,900      │
│ └─ Circuit Breakers (Scope 3) 51% │ $31,100     │
├──────────────────────────────────────────────────┤
│ TODAY'S ACTIVITY                                 │
│ • 4 apparatus completed this morning             │
│ • CB-15 marked complete (Jake, 9:45 AM)         │
│ • TX-08 in progress (Mike, started 10:30 AM)    │
│ • 3 apparatus ready to work (no blockers)       │
├──────────────────────────────────────────────────┤
│ ATTENTION NEEDED                                 │
│ ⚠️ 2 apparatus: Delays reported (review notes)   │
│ ⚠️ 1 apparatus: Non-serviceable (escalate)      │
└──────────────────────────────────────────────────┘
```

**Key Information Needs**:
- ✅ **Project health at a glance** (% complete, on track?)
- ✅ **Scope-level progress** (which areas ahead/behind?)
- ✅ **Real-time activity** (what happened today?)
- ✅ **Financial status** (earned revenue vs. budget)
- ✅ **Resource allocation** (who's working on what?)
- ✅ **Issues/blockers** (what needs attention?)
- ✅ **Customer reporting** (exportable progress reports)

#### **What They Need to DO**:
```
PM KEY ACTIONS
┌─────────────────────────────────────┐
│ 1. Assign apparatus to techs        │
│ 2. Create/modify scopes              │
│ 3. Set scope financial configs       │
│ 4. Review quality assessments        │
│ 5. Approve completed work            │
│ 6. Generate customer reports         │
│ 7. Adjust schedules/priorities       │
│ 8. Escalate issues                   │
└─────────────────────────────────────┘
```

**Critical Actions**:
1. **Create projects** - From RFP/quote to active tracking
2. **Define scopes** - Break project into manageable work packages
3. **Configure rates** - Set labor rates and cost structure per scope
4. **Assign work** - Allocate apparatus to available techs
5. **Monitor progress** - Daily stand-up view of activity
6. **Review quality** - Inspect assessment flags
7. **Approve revenue** - Verify completed work triggers billing
8. **Report to customer** - Export progress summaries

#### **Success Metrics**:
- ⏱️ **< 5 minutes** to get complete project status
- 📊 **Visual progress** (charts, not tables)
- 🚨 **Proactive alerts** (issues surface automatically)
- 💰 **Financial visibility** (revenue earned vs. estimate)
- 📱 **Mobile check-in** (monitor progress from anywhere)

#### **Pain Points to AVOID**:
- ❌ Manually calculating % complete
- ❌ Hunting through tables for issues
- ❌ No real-time updates (stale data)
- ❌ Complex financial configuration
- ❌ Can't answer "how are we doing?" quickly

---

### **PERSONA 4: Operations Coordinator (Office Manager)**
**Primary Location**: Office (typically Phoenix or each location)  
**Device**: Desktop computer, mobile for notifications  
**Technical Skill**: Intermediate (strong operations/logistics focus)  
**Focus**: Scheduling, resource allocation, day-to-day coordination  
**Reports To**: Location Manager

#### **What They Need to SEE**:
```
OPERATIONS DASHBOARD
┌──────────────────────────────────────────────────┐
│ PHOENIX OPERATIONS - Week of Nov 15-22          │
│ Coordinator: [Name]  |  15 Active Techs         │
├──────────────────────────────────────────────────┤
│ RESOURCE ALLOCATION                              │
├──────────────────────────────────────────────────┤
│ Monday 11/18:                                    │
│ • LASNAP16 (Vegas): Jake, Mike, Carlos (travel)  │
│ • PHXGRID09: Sarah, Tom, Lisa                   │
│ • AZPOWER14: Dan, Alex                          │
│ • Available: Kevin, Marcus, Jamie (3 techs)     │
│                                                  │
│ Tuesday 11/19:                                   │
│ • LASNAP16: Jake, Mike, Carlos (still Vegas)    │
│ • PHXGRID09: Sarah, Tom, Lisa                   │
│ • NEW PROJECT START: Kevin, Marcus → NVPOWER22   │
│ • Available: Jamie, Dan, Alex (3 techs)         │
│                                                  │
├──────────────────────────────────────────────────┤
│ TRAVEL LOGISTICS                                 │
│ • Jake crew → Vegas: Depart Mon 6am, return Thu  │
│ • Hotel: Booked (Hilton Garden Inn)             │
│ • Rental: Reserved (Enterprise)                 │
│                                                  │
├──────────────────────────────────────────────────┤
│ PROJECTS NEEDING RESOURCES ⚠️                    │
│ • SDGRID08 (San Diego): Starts 11/20, needs 2   │
│ • DENVOLT12 (Denver): Behind schedule, needs +1 │
│                                                  │
├──────────────────────────────────────────────────┤
│ TECH AVAILABILITY                                │
│ • Kevin: Available starting Tue                  │
│ • Marcus: On PTO Wed-Fri (not available)        │
│ • Sarah: Training Mon AM (available PM)          │
└──────────────────────────────────────────────────┘
```

**Key Information Needs**:
- ✅ **Who's assigned where** (all techs, all projects, daily view)
- ✅ **Tech availability** (PTO, training, travel, available for new work)
- ✅ **Project start dates** (upcoming projects need crew assignments)
- ✅ **Resource conflicts** ("SDGRID08 starts Monday but all techs assigned!")
- ✅ **Travel coordination** (which techs going where, logistics)
- ✅ **Capacity planning** (can we take on new project next week?)

#### **What They Need to DO**:
1. **Assign crews to projects** (coordinate with PM on skill needs)
2. **Schedule travel** (book hotels, flights, rentals for out-of-town work)
3. **Track availability** (who's available, who's on PTO, who's in training)
4. **Balance workload** (don't overload one crew, underutilize another)
5. **Handle conflicts** ("Mike called in sick, need to reassign his work")
6. **Coordinate equipment** (test gear allocation across projects)
7. **Daily stand-up prep** (know status before morning meeting)
8. **New project intake** (from sales/account manager → assign resources)

#### **Success Metrics**:
- ⏱️ **< 10 minutes** to plan entire week's resource allocation
- 🎯 **Zero double-bookings** (no tech assigned to two projects same day)
- 📅 **Proactive scheduling** (know 2 weeks ahead who's where)
- 🚀 **Fast turnaround** (new project assigned to crew within 24 hours)

#### **Pain Points to AVOID**:
- ❌ Manual spreadsheet tracking (Excel hell)
- ❌ "Who's available next Monday?" requires asking 5 people
- ❌ PMs don't know which techs are available (assign someone on PTO)
- ❌ Travel logistics disconnected from project tracking
- ❌ Last-minute scrambles ("Project starts tomorrow, no crew assigned!")

**Critical Fields Needed**:
```
❌ User.Availability_Status (Available/On Project/PTO/Training)
❌ User.Current_Project (lookup - where are they right now?)
❌ User.Available_Date (when will they finish current project?)
❌ Project.Crew_Assignment_Date (when did we assign crew?)
❌ Project.Target_Start_Date (when does project need to start?)
❌ Project.Estimated_Duration (how long will crew be on this project?)
```

---

### **PERSONA 5: Account Manager (Sales)**
**Primary Location**: Office + customer sites (meetings)  
**Device**: Desktop, laptop, mobile (high mobility)  
**Technical Skill**: Basic (sales-focused, not technical)  
**Focus**: Customer relationships, quotes, project handoff to PM  
**Reports To**: Location Manager or VP/GM

#### **What They Need to SEE**:
```
ACCOUNT MANAGER VIEW
┌──────────────────────────────────────────────────┐
│ MY ACCOUNTS & OPPORTUNITIES                      │
│ Account Manager: [Name]                          │
├──────────────────────────────────────────────────┤
│ ACTIVE PROJECTS (My Customers)                   │
├──────────────────────────────────────────────────┤
│ Nevada Power (3 active projects)                 │
│ • LASNAP16: 45% complete, on track ✅            │
│ • NVPOWER22: Starting 11/19 ✅                   │
│ • LVGRID14: 89% complete, finish this week ✅    │
│                                                  │
│ Arizona Public Service (2 active)                │
│ • PHXGRID09: 72% complete, ahead of schedule ✅  │
│ • AZPOWER14: 18% complete, at risk ⚠️            │
│                                                  │
├──────────────────────────────────────────────────┤
│ QUOTES & OPPORTUNITIES                           │
├──────────────────────────────────────────────────┤
│ • SDGRID15 (SDG&E): Quote sent 11/10, pending   │
│ • DENVOLT18 (Xcel Energy): Quote in progress    │
│                                                  │
├──────────────────────────────────────────────────┤
│ CUSTOMER UPDATES NEEDED                          │
│ • AZPOWER14: Behind schedule (call customer)    │
│ • LVGRID14: Completion report ready (send today)│
│                                                  │
├──────────────────────────────────────────────────┤
│ REVENUE SUMMARY (My Portfolio)                   │
│ MTD: $687K  |  QTD: $1.9M  |  YTD: $5.2M        │
│ Pipeline: $1.2M (6 opportunities)                │
└──────────────────────────────────────────────────┘
```

**Key Information Needs**:
- ✅ **My customers' projects** (filtered by account manager)
- ✅ **Project health** (on track, at risk, ahead - customer will ask)
- ✅ **Completion status** (can I tell customer "90% done"?)
- ✅ **Revenue by customer** (track account performance)
- ✅ **Quote-to-project conversion** (which quotes became projects?)
- ✅ **Exportable reports** (send progress updates to customers)

#### **What They Need to DO**:
1. **Monitor my customers' projects** (not ALL projects, just my accounts)
2. **Generate customer reports** (weekly/monthly progress updates)
3. **Create quotes** (from RFP → scope definition → pricing)
4. **Convert quote to project** (won the bid → hand off to PM)
5. **Track pipeline** (opportunities → quotes → projects → revenue)
6. **Escalate issues** (if project at risk, work with PM to resolve before customer notices)
7. **Invoice coordination** (when can we invoice customer? Is work complete?)

#### **Success Metrics**:
- ⏱️ **< 5 minutes** to answer "How's my customer's project?"
- 📊 **Instant reports** (export progress summary for customer meeting)
- 💰 **Revenue visibility** (track my portfolio performance)
- 🎯 **Proactive communication** (know about issues before customer calls)

#### **Pain Points to AVOID**:
- ❌ Can't find my customers' projects (mixed in with everyone's)
- ❌ Asking PM "What's the status?" (should see it myself)
- ❌ Manually creating customer reports (Excel copy-paste hell)
- ❌ Don't know revenue recognized vs. billed (invoicing delays)
- ❌ Quote disconnected from project (can't track conversion)

**Critical Fields Needed**:
```
❌ Project.Account_Manager (User lookup - who sold this project?)
❌ Project.Customer_Name (Text - for account rollup)
❌ Project.Quote_Number (Text - link quote to project)
❌ Project.Contract_Value (Currency - original quote amount)
✅ Project.Revenue (exists via rollup - earned to date)
❌ Project.Invoiced_Amount (Currency - how much billed to customer)
❌ Project.Outstanding_Amount (Calculated: Revenue - Invoiced)
```

---

### **PERSONA 6: Location Manager (Branch Manager)**
**Primary Location**: Branch office (Phoenix, Vegas, Denver, SD)  
**Device**: Desktop computer  
**Technical Skill**: Advanced (business operations focus)  
**Focus**: Location P&L, resource management, performance oversight  
**Reports To**: Regional VP/GM

#### **What They Need to SEE**:
```
LOCATION DASHBOARD (Phoenix Services Example)
┌──────────────────────────────────────────────────┐
│ PHOENIX SERVICES - Location Overview            │
│ Manager: [You]  |  Techs: 15-18  |  Nov 2025    │
├──────────────────────────────────────────────────┤
│ ACTIVE PROJECTS (8)                              │
│ ┌─ LASNAP16    45% │ On Track    │ $105K / $230K│
│ ├─ PHXGRID09   72% │ Ahead       │ $182K / $245K│
│ ├─ AZPOWER14   18% │ At Risk ⚠️  │ $34K / $190K │
│ └─ [+ 5 more...]                                 │
├──────────────────────────────────────────────────┤
│ RESOURCE UTILIZATION                             │
│ Available:  3 techs  │  Assigned: 12 techs       │
│ Utilization: 85%     │  Avg: 7.2 hrs/tech/day    │
├──────────────────────────────────────────────────┤
│ FINANCIAL SUMMARY (MTD)                          │
│ Revenue Earned:    $453,200                      │
│ Revenue Invoiced:  $380,500                      │
│ Outstanding:       $72,700  (approve & invoice)  │
├──────────────────────────────────────────────────┤
│ QUALITY METRICS                                  │
│ Acceptable:        94.2%                         │
│ Minor Deficiency:  4.8%                          │
│ Non-Serviceable:   1.0%  (review cases)          │
└──────────────────────────────────────────────────┘
```

**Key Information Needs**:
- ✅ **All Phoenix projects** (status, health, revenue)
- ✅ **Resource capacity** (who's available, who's overloaded)
- ✅ **Financial performance** (revenue, margin, invoicing)
- ✅ **Quality trends** (equipment assessment patterns)
- ✅ **Operational efficiency** (avg hours per apparatus type)
- ✅ **Customer health** (on-time delivery, satisfaction)

#### **What They Need to DO**:
1. **Allocate resources** across multiple projects
2. **Approve revenue recognition** (verify completed work)
3. **Review financial performance** by project and scope
4. **Identify bottlenecks** (where are delays occurring?)
5. **Escalate quality issues** (non-serviceable equipment)
6. **Plan capacity** (hiring needs, training gaps)
7. **Report to regional VP** (Phoenix performance)

#### **Success Metrics**:
- ⏱️ **Daily standup** < 10 minutes for complete location status
- 💰 **Same-day revenue recognition** (no manual approval delays)
- 📊 **Trend visibility** (improving or declining performance?)
- 🎯 **Resource optimization** (right tech for right work)

---

### **PERSONA 7: Regional VP/GM (Executive)** (Your Boss)
**Primary Location**: Phoenix office + travel to 4 locations  
**Device**: Desktop, tablet, mobile (high mobility)  
**Technical Skill**: Executive (strategic, not tactical)  
**Focus**: Regional performance, growth, strategic decisions  
**Reports To**: Corporate (RESA Power HQ)

#### **What They Need to SEE**:
```
SOUTHWEST REGIONAL DASHBOARD
┌──────────────────────────────────────────────────┐
│ RESA POWER - Southwest Region                   │
│ Regional VP: [Boss]  |  Locations: 4  |  Nov 2025│
├──────────────────────────────────────────────────┤
│ LOCATION PERFORMANCE                             │
│ Phoenix:   8 projects │ 85% util │ $453K MTD    │
│ Las Vegas: 5 projects │ 72% util │ $298K MTD    │
│ Denver:    3 projects │ 68% util │ $156K MTD    │
│ San Diego: 2 projects │ 81% util │ $187K MTD    │
│                                                  │
│ REGIONAL TOTAL: 18 active projects               │
│ MTD Revenue: $1.09M  |  QTD: $3.2M  |  YTD: $9.8M│
├──────────────────────────────────────────────────┤
│ GROWTH METRICS                                   │
│ Tech Count:    35 total (↑ from 3 in 2021)      │
│ Avg Project:   $215K                             │
│ Win Rate:      67% (quotes → projects)           │
├──────────────────────────────────────────────────┤
│ STRATEGIC FOCUS                                  │
│ 🎯 Highest Revenue:   Phoenix ($453K MTD)        │
│ ⚠️ Capacity Concern:  Vegas (need 2 more techs) │
│ ✅ Quality Leader:    Denver (96.8% acceptable)  │
│ 📈 Growth Leader:     Phoenix (+15 techs)        │
└──────────────────────────────────────────────────┘
```

**Key Information Needs**:
- ✅ **Cross-location comparison** (which location performing best?)
- ✅ **Regional financial rollup** (total revenue, margin, growth)
- ✅ **Strategic indicators** (capacity, quality, efficiency)
- ✅ **Risk identification** (projects at risk, quality trends)
- ✅ **Growth opportunities** (where to invest, expand)
- ✅ **Executive reporting** (board-ready metrics)

#### **What They Need to DO**:
1. **Strategic planning** (resource allocation across 4 locations)
2. **Performance review** (location manager accountability)
3. **Investment decisions** (hiring, equipment, expansion)
4. **Risk management** (identify and mitigate regional risks)
5. **Customer relationships** (executive-level engagement)
6. **Corporate reporting** (regional contribution to RESA Power)

#### **Success Metrics**:
- ⏱️ **< 5 minutes** to understand regional health
- 📊 **Executive summary** (board-ready visualizations)
- 🎯 **Actionable insights** (data drives decisions)
- 📱 **Mobile access** (review during travel)

---

## 🔄 DATA FLOW ARCHITECTURE

### **BOTTOM-UP: Field to Executive**

```
TIER 5: APPARATUS LEVEL (Field Tech)
┌─────────────────────────────────────────────┐
│ Apparatus: CB-01 - Breaker Panel 1A         │
│ Status: Complete                            │
│ Hours: 2.5 actual (2.5 estimated)           │
│ Assessment: Acceptable                      │
│ Revenue Trigger: ON (status = complete)     │
└─────────────────────────────────────────────┘
                    ↓
TIER 4: TASK LEVEL (Project Manager)
┌─────────────────────────────────────────────┐
│ Task: Circuit Breakers - East Wing         │
│ Apparatus: 12 total (8 complete)           │
│ Progress: 67% (weighted by hours)          │
│ Status: In Progress                         │
│ Hours: 20.5 / 30 estimated                  │
└─────────────────────────────────────────────┘
                    ↓
TIER 3: SCOPE LEVEL (Project Manager)
┌─────────────────────────────────────────────┐
│ Scope: Switchgear Testing                  │
│ Tasks: 4 (2 complete)                       │
│ Apparatus: 48 total (32 complete)          │
│ Progress: 67%                               │
│ Revenue: $45,200 earned / $68,000 budget    │
│ Financial Config: Scope Labor Detail       │
└─────────────────────────────────────────────┘
                    ↓
TIER 2: PROJECT LEVEL (Location Manager)
┌─────────────────────────────────────────────┐
│ Project: LASNAP16                           │
│ Location: Las Vegas                         │
│ Scopes: 3 (1 complete)                      │
│ Progress: 45%                               │
│ Revenue: $105K earned / $230K budget        │
│ Status: On Track                            │
└─────────────────────────────────────────────┘
                    ↓
TIER 1: BUSINESS UNIT LEVEL (Regional VP)
┌─────────────────────────────────────────────┐
│ Business Unit: Las Vegas Services           │
│ Projects: 5 active                          │
│ Revenue: $298K MTD                          │
│ Utilization: 72%                            │
│ Tech Count: 8                               │
└─────────────────────────────────────────────┘
                    ↓
TIER 0: REGIONAL LEVEL (Executive)
┌─────────────────────────────────────────────┐
│ Region: Southwest (Phoenix/Vegas/Denver/SD) │
│ Projects: 18 active                         │
│ Revenue: $1.09M MTD                         │
│ Locations: 4                                │
│ Techs: 35 total                             │
└─────────────────────────────────────────────┘
```

### **TOP-DOWN: Executive to Field**

```
STRATEGIC PLANNING (Regional VP)
"We need 30% revenue growth in Vegas"
                    ↓
RESOURCE ALLOCATION (Location Manager)
"Assign 2 more techs to Vegas, hire 1 more"
                    ↓
PROJECT ASSIGNMENT (Project Manager)
"LASNAP16 is priority - allocate best techs"
                    ↓
TASK PRIORITIZATION (Project Manager)
"Complete switchgear scope first (customer priority)"
                    ↓
WORK ASSIGNMENT (Project Manager → Field Tech)
"Jake: Complete CB-01 through CB-12 by Friday"
                    ↓
DAILY EXECUTION (Field Tech)
"Working on CB-01 now, will complete CB-12 today"
```

---

## 📊 CRITICAL INTEGRATIONS

### **Integration 1: Revenue Recognition Flow**

```
APPARATUS COMPLETE (Field Tech)
    ↓
Completion_Status = "Complete" (trigger)
    ↓
POWER AUTOMATE FLOW EXECUTES:
    1. Create ApparatusRevenue record
    2. Copy Labor_Hours from Apparatus
    3. Copy Delays from Apparatus
    4. Fetch Labor_Rate from ScopeLaborDetail
    5. Calculate: Revenue_Amount = Labor_Hours × Labor_Rate
    6. Link to Project (for location rollup)
    ↓
REVENUE RECOGNIZED:
    - Apparatus level: Individual revenue record
    - Scope level: Rollup of all apparatus in scope
    - Project level: Rollup of all scopes
    - Business Unit level: Rollup of all projects
    - Regional level: Rollup of all business units
```

**Fields Required** (v1.2.0.3 status):
- ✅ Apparatus.Completion_Status (EXISTS)
- ✅ Apparatus.Labor_Hours (EXISTS)
- ✅ Apparatus.Delays (EXISTS)
- ❌ ApparatusRevenue.Labor_Hours (MISSING - Phase 2d)
- ❌ ApparatusRevenue.Delays (MISSING - Phase 2d)
- ❌ ApparatusRevenue.Actual_Hours (MISSING - Phase 2d)
- ❌ ApparatusRevenue.Labor_Rate (MISSING - Phase 2d)
- ❌ ApparatusRevenue.Revenue_Amount (MISSING - Phase 2d)
- ❌ Power Automate Flow (MISSING - Phase 2d)

---

### **Integration 2: Quality Tracking Flow**

```
APPARATUS ASSESSED (Field Tech)
    ↓
Apparatus_Assessment = "Non-Serviceable" (alert trigger)
    ↓
NOTIFICATION FLOW:
    1. Notify Project Manager (immediate)
    2. Create task: "Review non-serviceable equipment"
    3. Flag apparatus for follow-up
    4. Include in quality metrics dashboard
    ↓
PM REVIEW & ACTION:
    - Review tech notes and photos
    - Escalate to customer if needed
    - Adjust scope/budget if required
```

**Fields Required** (v1.2.0.3 status):
- ✅ Apparatus.Apparatus_Assessment (EXISTS - v1.2.0.2)
- ✅ Apparatus.Witness_Test (EXISTS - v1.2.0.2)
- ❌ Quality alert flow (MISSING - future enhancement)

---

### **Integration 3: Resource Utilization Tracking**

**NOT YET DESIGNED** - Requires additional fields:

**Missing Fields for Resource Management**:
- ❌ Apparatus.Assigned_To (User lookup) - Who's working on this?
- ❌ Apparatus.Start_Date (Date) - When did work begin?
- ❌ Apparatus.Target_Date (Date) - When should it be done?
- ❌ Apparatus.Actual_Start (DateTime) - Real start time
- ❌ Apparatus.Actual_Complete (DateTime) - Real completion time

**Why We Need These**:
- Track tech productivity (apparatus per day)
- Identify bottlenecks (work started but not finished)
- Calculate utilization rates (assigned hours vs. available hours)
- Enable scheduling (who's available for new work?)

---

## 🎯 GAP ANALYSIS: v1.2.0.3 vs. USER NEEDS

### **FIELD TECH NEEDS**

| Need | v1.2.0.3 Status | Gap Analysis |
|------|----------------|--------------|
| View assigned work | ❌ No "Assigned_To" field | **GAP**: Cannot filter "my apparatus" |
| Simple status update | ✅ Completion_Status exists | **OK** - Field ready |
| Log hours | ✅ Labor_Hours, Delays exist | **OK** - Fields ready |
| Quality assessment | ✅ Apparatus_Assessment exists | **OK** - Field ready (v1.2.0.2) |
| Test standards | ✅ Witness_Test exists | **OK** - Field ready (v1.2.0.2) |
| Datasheet tracking | ✅ Datasheet_Completed exists | **OK** - Field ready |
| Mobile form | ❓ Unknown (need forms audit) | **AUDIT NEEDED** |

**Critical Gaps**:
1. ❌ **Assigned_To field** - Cannot assign apparatus to techs
2. ❌ **Mobile-optimized form** - May not exist (verify in audit)
3. ❌ **"My Work" view** - Cannot filter by assigned tech

---

### **PROJECT MANAGER NEEDS**

| Need | v1.2.0.3 Status | Gap Analysis |
|------|----------------|--------------|
| Project overview dashboard | ❓ Unknown (Power BI?) | **AUDIT NEEDED** |
| Scope progress | ✅ Rollup fields exist (8 metrics) | **OK** - Calculated |
| Real-time activity | ❌ No activity log | **GAP**: Need activity feed or audit log |
| Financial status | ✅ ScopeLaborDetail (49 fields) | **OK** - Complex but ready |
| Assign work | ❌ No Assigned_To field | **GAP**: Cannot assign apparatus |
| Approve revenue | ❌ No approval workflow | **GAP**: Revenue auto-triggers (might be OK) |
| Customer reports | ❓ Unknown (Power BI?) | **AUDIT NEEDED** |

**Critical Gaps**:
1. ❌ **Work assignment capability** - Need Assigned_To field
2. ❌ **Activity log** - No audit trail of changes
3. ❓ **Dashboard/reporting** - May exist in Power BI (verify)

---

### **LOCATION MANAGER NEEDS**

| Need | v1.2.0.3 Status | Gap Analysis |
|------|----------------|--------------|
| Location-filtered projects | ✅ Projects.Location exists | **OK** - BusinessUnit lookup ready |
| Resource utilization | ❌ No tech assignment tracking | **GAP**: Need Assigned_To + availability |
| Financial rollup | ✅ Project rollup fields exist | **OK** - But need BusinessUnit rollups |
| Quality metrics | ✅ Apparatus_Assessment exists | **OK** - Need rollup view by location |
| Revenue recognition | ❌ Incomplete (Phase 2d pending) | **GAP**: 5 fields + flow needed |

**Critical Gaps**:
1. ❌ **BusinessUnit rollup fields** - Need revenue/hours by location
2. ❌ **Tech utilization tracking** - Need assignment + time tracking
3. ❌ **Quality dashboard** - Need view/report by location

---

### **REGIONAL VP NEEDS**

| Need | v1.2.0.3 Status | Gap Analysis |
|------|----------------|--------------|
| Cross-location view | ✅ BusinessUnit structure exists | **OK** - Architecture ready |
| Regional financial rollup | ❌ No regional-level rollups | **GAP**: Need aggregation at regional level |
| Performance comparison | ❌ No cross-BU metrics | **GAP**: Need location comparison views |
| Executive dashboard | ❓ Unknown | **AUDIT NEEDED** - Likely Power BI |

**Critical Gaps**:
1. ❌ **Regional-level rollups** - Above BusinessUnit level
2. ❌ **Executive dashboard** - Simplified, high-level view
3. ❌ **Trend analysis** - Historical performance tracking

---

## 🚀 MASTER BUILD SPECIFICATION V2 - ROADMAP

### **PHASE 1: Foundation Complete ✅**
- 8 entities, 137 fields, 28 calculated fields
- Relationships established
- Quality tracking added (v1.2.0.2)
- BusinessUnit architecture validated

### **PHASE 2: Critical Gaps (NEXT - 2-3 hours)**

**2A. Revenue Automation** (45-65 min)
- Add 5 ApparatusRevenue fields
- Build Power Automate flow
- Test end-to-end revenue recognition

**2B. Work Assignment** (30-45 min)
- Add Apparatus.Assigned_To field (User lookup)
- Add Apparatus.Assignment_Date field
- Create "My Work" view for field techs

**2C. Date Tracking** (20-30 min)
- Add Apparatus.Start_Date (Date)
- Add Apparatus.Target_Date (Date)
- Add Apparatus.Actual_Start (DateTime)
- Add Apparatus.Actual_Complete (DateTime)

### **PHASE 3: Enhanced Visibility (3-4 hours)**

**3A. BusinessUnit Rollups**
- Add BU-level calculated fields (total projects, revenue, tech count)
- Create Location Manager dashboard view

**3B. Activity Tracking**
- Enable Dataverse audit log
- Create activity feed view
- PM can see recent changes

**3C. Quality Dashboard**
- Create quality metrics rollup
- Location/Regional quality views

### **PHASE 4: User Experience (4-6 hours)**

**4A. Mobile Forms**
- Optimize Apparatus form for mobile
- Create "Quick Complete" form
- Test on phone/tablet

**4B. PM Dashboard**
- Power BI project overview
- Scope progress visualization
- Real-time activity feed

**4C. Executive Dashboard**
- Regional VP overview
- Location comparison
- Trend analysis

### **PHASE 5: Advanced Features (Future)**

**5A. Scheduling**
- Apparatus scheduling/calendar
- Tech availability tracking
- Workload balancing

**5B. Customer Portal**
- Real-time progress visibility
- Document sharing
- Approval workflows

**5C. Integration**
- QuickBooks revenue export
- Email notifications
- Mobile app (PowerApps)

---

## 📋 DECISION FRAMEWORK

### **For Every Proposed Field/Feature, Ask**:

1. **Which persona needs this?** (Tech/PM/Location Mgr/Regional VP)
2. **What decision does it enable?** (What action can they take with this data?)
3. **How often is it used?** (Daily/Weekly/Monthly/Rarely)
4. **What's the ROI?** (Time saved vs. implementation cost)
5. **Can we calculate it?** (Derived field vs. manual entry)

### **Priority Levels**:

**P0 - BLOCKING**: Cannot operate without this
- Revenue recognition automation
- Apparatus status tracking
- Project/Scope/Task structure

**P1 - HIGH VALUE**: Significant efficiency gain
- Work assignment (Assigned_To field)
- Date tracking (Start/Target/Complete)
- BusinessUnit rollups

**P2 - MEDIUM VALUE**: Nice to have, measurable benefit
- Activity log
- Quality dashboard
- Mobile form optimization

**P3 - LOW VALUE**: Future enhancement
- Advanced scheduling
- Customer portal
- Predictive analytics

---

## ✅ NEXT STEPS

**Immediate Actions**:
1. ✅ Complete forms/views audit (validate current UX)
2. ✅ Build Phase 2 critical gaps (revenue, assignment, dates)
3. ✅ Create Master Build Spec V2 (with this UX foundation)
4. ✅ Prioritize Phase 3-5 enhancements (based on user feedback)

**Success Criteria**:
- Field tech can complete apparatus in < 1 minute
- PM can check project status in < 5 minutes
- Location manager daily standup < 10 minutes
- Regional VP understands regional health in < 5 minutes

---

**STATUS**: Foundation document complete - Ready to guide all future decisions  
**NEXT**: Use this to complete forms audit and finalize Master Build Spec V2
