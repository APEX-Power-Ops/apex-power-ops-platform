# RESA POWER v1.4.0.0 - ROADMAP & PRIORITIES
## Post-Expansion Strategic Plan

**Created**: November 22, 2025  
**Current Version**: v1.4.0.0 (16 Tables, 291+ Fields)  
**Purpose**: Define clear roadmap for completing v1.4.0.0 and planning v1.5.0.0+

---

## 📊 CURRENT STATE SUMMARY

### **What We Have (v1.4.0.0)**

**Core Infrastructure (Complete)** ✅:
- 14 Dataverse tables created
- 291+ fields defined
- 30 automated formulas working
- 1 Power Automate flow (revenue recognition)
- Auditing enabled environment-wide
- Isolated development environment operational

**Table Breakdown**:
- **Original 8** (v1.3.0.5): BusinessUnit, Projects, ProjectScope, Tasks, Apparatus, ApparatusRevenue, ScopeLaborDetail, ApparatusTypeMaster
- **New 6** (v1.4.0.0): Clients, Sites, Employees, Quotes, Resource Assignments, Equipment

### **What's Missing (To Complete v1.4.0.0)**

**Configuration Needed** ⏳:
- 7 lookup relationships not yet configured
- Forms & views for 6 new tables
- Security roles for new tables
- Business rules & validation
- Sample data for testing
- Updated documentation

---

## 🎯 PHASE 1: COMPLETE v1.4.0.0 FOUNDATION
**Target: Next 1-2 Weeks**  
**Goal**: Fully operational 14-table system with proper relationships and UI

### **Priority 1A: Configure Lookups** (1-2 hours)
**Status**: Critical - blocks data entry  
**Effort**: Low  
**Value**: High

**Relationships to Create**:

1. **Sites → Clients** (Many-to-One)
   - Purpose: Link sites to owning clients
   - Behavior: Restrict delete (prevent orphaned sites)
   - Display: Show client name on site forms

2. **Quotes → Clients** (Many-to-One)
   - Purpose: Track which client requested quote
   - Behavior: Restrict delete
   - Display: Client selector on quote form

3. **Quotes → Sites** (Many-to-One)
   - Purpose: Link quote to specific work location
   - Behavior: Restrict delete
   - Display: Site selector filtered by selected client

4. **Projects → Clients** (Many-to-One)
   - Purpose: Link project to customer
   - Behavior: Restrict delete
   - Display: Client name prominent on project forms

5. **Projects → Sites** (Many-to-One)
   - Purpose: Link project to work location
   - Behavior: Restrict delete
   - Display: Site address visible on project

6. **Resource Assignments → Projects** (Many-to-One)
   - Purpose: Link staffing to projects
   - Behavior: Cascade delete (remove assignments if project deleted)
   - Display: Project context on assignment

7. **Resource Assignments → Employees** (Many-to-One)
   - Purpose: Link assignments to specific employees
   - Behavior: Restrict delete
   - Display: Employee details on assignment

8. **Equipment → Employees** (Assigned To, Many-to-One, Optional)
   - Purpose: Track who currently has equipment
   - Behavior: Restrict delete
   - Display: Show employee name on equipment form

9. **Equipment → Projects** (Current Project, Many-to-One, Optional)
   - Purpose: Track equipment usage on projects
   - Behavior: Restrict delete
   - Display: Show project context on equipment

**Implementation Steps**:
1. Open Power Apps maker portal
2. Navigate to Tables → [Table] → Relationships
3. Create each lookup field
4. Configure cascade behaviors
5. Test referential integrity
6. Document relationship rules

**Success Criteria**:
- ✅ All 9 lookups created
- ✅ Cascade behaviors configured appropriately
- ✅ No orphaned records possible
- ✅ Lookups visible in forms

---

### **Priority 1B: Create Forms & Views** (8-12 hours)
**Status**: High Priority - needed for usability  
**Effort**: Medium-High  
**Value**: High

**Forms Needed** (6 main forms):

1. **Client Form**
   - **Tabs**: General, Contact Information, Financial, History
   - **General Tab**: Client Name, Number, Type, Industry, Status, Notes
   - **Contact Tab**: Primary Contact section, Billing Contact section
   - **Financial Tab**: Credit Limit, Payment Terms, Tax ID, Insurance
   - **History Tab**: Related sites, projects, quotes (sub-grids)
   - **Business Rules**: Require insurance expiration if certificate entered

2. **Site Form**
   - **Tabs**: General, Location, Access & Safety, Related
   - **General Tab**: Site Name, Number, Type, Client lookup, Status
   - **Location Tab**: Address fields, GPS coordinates, County, Utility info
   - **Access Tab**: Site contact, access requirements, safety protocols, parking
   - **Related Tab**: Projects at this site, quotes (sub-grids)
   - **Business Rules**: Show GPS when address entered

3. **Employee Form**
   - **Tabs**: General, Skills & Certifications, Rates, Availability, Related
   - **General Tab**: Name, Number, Type, Title, Department, Contact info
   - **Skills Tab**: Skillset, Certifications, License info with expiration
   - **Rates Tab**: Hourly Rate, Overtime Rate, Billing Rate, Travel Rate
   - **Availability Tab**: Status, Home Office, Travel preferences, Emergency contact
   - **Related Tab**: Assignments, equipment (sub-grids)
   - **Business Rules**: Calculate billing rate from hourly rate + markup

4. **Quote Form**
   - **Tabs**: General, Pricing, Approval, Outcome, Related
   - **General Tab**: Quote Number, Client, Site, Type, Status, Dates, Scope
   - **Pricing Tab**: Hours, rates, costs breakdown, margin, total
   - **Approval Tab**: Requested by, Prepared by, Approved by, dates
   - **Outcome Tab**: Won/Lost, Conversion info, Loss reason
   - **Related Tab**: Converted project (if won)
   - **Business Rules**: 
     - Calculate subtotal from components
     - Calculate total from subtotal + tax - discount
     - Require approval for quotes > $50k

5. **Resource Assignment Form**
   - **Tabs**: General, Hours, Logistics
   - **General Tab**: Assignment Number, Project, Employee, Role, Status, Dates
   - **Hours Tab**: Allocated, Actual, Remaining, Percent Complete, Billing Rate
   - **Logistics Tab**: Assignment Type, Shift, Travel needs, Accommodations
   - **Business Rules**: 
     - Calculate remaining hours
     - Prevent end date before start date
     - Validate employee availability

6. **Equipment Form**
   - **Tabs**: General, Calibration, Maintenance, Assignment, Related
   - **General Tab**: Equipment Number, Name, Type, Category, Status, Condition
   - **Asset Tab**: Manufacturer, Model, Serial, Purchase info
   - **Calibration Tab**: Required?, Last date, Next due, Interval, Provider
   - **Maintenance Tab**: Schedule, Last date, Next due
   - **Assignment Tab**: Current Location, Assigned To, Current Project
   - **Related Tab**: Assignment history, project usage
   - **Business Rules**: 
     - Calculate next calibration due from interval
     - Alert if calibration overdue
     - Prevent assignment if overdue

**Views Needed** (30+ views total):

**Client Views**:
- Active Clients
- All Clients
- By Industry
- By Account Status
- Insurance Expiring Soon

**Site Views**:
- Active Sites
- All Sites
- By Client
- By State/City
- Requires Security Clearance

**Employee Views**:
- Active Employees
- All Employees
- By Department
- By Skillset
- Certifications Expiring
- Available for Work

**Quote Views**:
- Active Quotes
- All Quotes
- By Status (Draft, Submitted, Won, Lost)
- Expiring Soon
- By Client
- This Month's Quotes
- Win Rate Analysis

**Resource Assignment Views**:
- Active Assignments
- All Assignments
- By Project
- By Employee
- Upcoming Start Dates
- Ending This Month

**Equipment Views**:
- All Equipment
- Available Equipment
- In Use
- Calibration Due
- Maintenance Due
- By Category
- By Location

**Implementation Approach**:
- Start with "quick create" forms for rapid data entry
- Create main forms for detailed editing
- Design views for common use cases
- Add filtering options
- Configure default views

**Success Criteria**:
- ✅ All 6 main forms created with tabbed layouts
- ✅ Business rules implemented on critical fields
- ✅ 30+ views created for various scenarios
- ✅ Forms tested with sample data
- ✅ User-friendly navigation

---

### **Priority 1C: Security Configuration** (2-3 hours)
**Status**: High Priority - data protection  
**Effort**: Medium  
**Value**: High

**Security Roles Needed**:

1. **Clients Table**:
   - Sales/Account Managers: Full access
   - Project Managers: Read all, write own
   - Field Techs: Read only
   - Finance: Read all

2. **Sites Table**:
   - Project Managers: Full access
   - Field Techs: Read all
   - Sales: Read all

3. **Employees Table**:
   - HR/Admin: Full access
   - Managers: Read all
   - Employees: Read own record only
   - Others: Read names only (for lookups)

4. **Quotes Table**:
   - Sales: Full access
   - Project Managers: Read all, write to convert to projects
   - Finance: Read all
   - Others: No access

5. **Resource Assignments**:
   - Project Managers: Full access
   - Employees: Read own assignments
   - Schedulers: Full access

6. **Equipment**:
   - Admin: Full access
   - Field Techs: Read all, update assignment
   - Calibration Manager: Update calibration fields
   - Others: Read only

**Implementation Steps**:
1. Document access requirements by role
2. Create/modify security roles in admin center
3. Assign table permissions
4. Test with different user accounts
5. Document security model

**Success Criteria**:
- ✅ Appropriate access levels configured
- ✅ Sensitive data protected (HR, financial)
- ✅ Users can perform their job functions
- ✅ Audit logging captures changes

---

### **Priority 1D: Sample Data & Testing** (2-4 hours)
**Status**: Medium Priority - validation  
**Effort**: Medium  
**Value**: Medium

**Sample Data Needed**:

**3 Clients**:
- Phoenix Utility Company
- Southwest Industrial Services
- Metro Power Distribution

**5 Sites**:
- Phoenix Main Substation (Phoenix Utility)
- North Valley Switching Station (Phoenix Utility)
- Industrial Park Transformer Yard (Southwest Industrial)
- Downtown Distribution Center (Metro Power)
- Airport Electrical Vault (Phoenix Utility)

**8 Employees**:
- Senior Technicians (2)
- Technicians (4)
- Project Manager (1)
- Scheduler (1)

**5 Quotes**:
- 2 Won (converted to projects)
- 2 Active
- 1 Lost

**10 Resource Assignments**:
- Link employees to existing projects
- Variety of roles and statuses

**6 Equipment Items**:
- Relay test sets (2)
- Megger (1)
- Transformer turns ratio tester (1)
- Power analyzer (1)
- Oscilloscope (1)

**Testing Scenarios**:
1. Create client → Create site for client → Create quote → Win quote → Convert to project
2. Assign employee to project → Track hours
3. Check out equipment to employee → Assign to project → Return
4. Schedule calibration → Mark complete → Calculate next due
5. Test all relationships and cascades
6. Verify calculations and rollups
7. Test security with different user roles

**Success Criteria**:
- ✅ Realistic sample data entered
- ✅ All relationships tested
- ✅ Business rules validated
- ✅ Calculations verified
- ✅ No errors or data integrity issues

---

## 🚀 PHASE 2: v1.5.0.0 - ENHANCED FUNCTIONALITY
**Target: 2-4 Weeks After v1.4.0.0 Complete**  
**Goal**: Add intelligence and automation to the 14-table foundation

### **Priority 2A: Date Tracking Enhancement** (3 hours)
**Status**: Ready to implement (spec complete)  
**Effort**: Low-Medium  
**Value**: High

**Reference**: `DATE_TRACKING_IMPLEMENTATION.md`

**What Gets Added**:
- 3 date fields to Apparatus (Anticipated Start, Actual Start, Date Completed)
- 18 rollup fields (6 per table: Tasks, Scopes, Projects)
- 6 KPI views for schedule management

**Business Value**:
- Schedule visibility (what's starting next 7 days)
- Overdue tracking
- Duration analysis
- Capacity planning data

**Implementation**: Follow existing spec document

---

### **Priority 2B: Revenue Rollups** (2-4 hours)
**Status**: Needs requirements definition  
**Effort**: Low  
**Value**: High

**Scope**:
- Define revenue KPIs needed
- Create rollup fields at Scope level
- Create rollup fields at Project level
- Build revenue analysis views

**Questions to Answer**:
1. What revenue reports do PMs need?
2. Revenue by status (Recognized vs Pending)?
3. Historical trends needed?
4. Forecasting required?

**Proposed Rollups**:

**At Scope Level** (from ApparatusRevenue):
- Total_Revenue_Recognized (SUM where status = Recognized)
- Total_Revenue_Pending (SUM where status = Pending)
- Total_Billable_Hours (SUM of Apparatus_Hours)
- Average_Labor_Rate (AVG of Effective_Labor_Rate)
- Revenue_Count (COUNT of revenue records)

**At Project Level** (from Scopes):
- Project_Total_Revenue
- Project_Recognized_Revenue
- Project_Pending_Revenue
- Project_Billable_Hours

**Implementation**: 1-2 hours after requirements confirmed

---

### **Priority 2C: Notification Flows** (4-6 hours per flow)
**Status**: Design needed  
**Effort**: Medium  
**Value**: Medium-High

**Proposed Flows**:

1. **Employee Certification Expiration Alert** (2 hours)
   - Trigger: Daily scheduled flow
   - Logic: Find certifications expiring in next 30 days
   - Action: Email HR and employee
   - Value: Compliance management

2. **Equipment Calibration Due Alert** (2 hours)
   - Trigger: Daily scheduled flow
   - Logic: Find equipment with calibration due in next 14 days
   - Action: Email equipment manager and notify techs
   - Value: Compliance and operational readiness

3. **Quote Expiration Reminder** (1.5 hours)
   - Trigger: Daily scheduled flow
   - Logic: Find quotes expiring in next 7 days
   - Action: Email sales rep
   - Value: Sales pipeline management

4. **Resource Assignment Start Alert** (1.5 hours)
   - Trigger: Daily scheduled flow
   - Logic: Find assignments starting in next 3 days
   - Action: Email employee and PM
   - Value: Readiness and coordination

5. **Project Milestone Notifications** (3 hours)
   - Trigger: Dataverse change (Project Status change)
   - Logic: Detect status changes
   - Action: Post to Teams, email stakeholders
   - Value: Stakeholder awareness

**Total Effort**: 10-12 hours for all 5 flows

---

### **Priority 2D: Advanced Calculations** (4-8 hours)
**Status**: Design needed  
**Effort**: Medium  
**Value**: Medium

**Proposed Enhancements**:

1. **Employee Utilization Metrics**
   - Calculate: Hours assigned / Available hours
   - Location: Employee table
   - Value: Capacity planning

2. **Equipment Utilization**
   - Calculate: Days in use / Total days
   - Location: Equipment table
   - Value: Asset management

3. **Quote Win Rate**
   - Calculate: Won quotes / Total quotes by employee
   - Location: Employee table (if sales role)
   - Value: Sales performance

4. **Site Activity Score**
   - Calculate: Active projects at site
   - Location: Site table
   - Value: Site prioritization

5. **Client Value Metrics**
   - Calculate: Total project revenue, project count
   - Location: Client table
   - Value: Account management

**Implementation**: 1-2 hours per calculation set

---

## 📈 PHASE 3: v1.6.0.0 - INTEGRATION & REPORTING
**Target**: 1-2 Months After v1.5.0.0  
**Goal**: Connect to external systems and build comprehensive reporting

### **Priority 3A: QuickBooks Integration** (12-20 hours)
**Status**: Future planning  
**Effort**: High  
**Value**: High

**Scope**:
- Sync clients to QuickBooks customers
- Export invoices based on recognized revenue
- Track payment status
- Reconcile revenue recognized vs cash received

**Prerequisites**:
- External_System_ID fields (from Future-Proofing guide)
- QuickBooks Online API credentials
- Data mapping specification

---

### **Priority 3B: Power BI Dashboards** (16-24 hours)
**Status**: Future planning  
**Effort**: High  
**Value**: High

**Dashboard Types**:

1. **Executive Dashboard** (4-6 hours)
   - Project count by status
   - Revenue trends
   - Resource utilization
   - Geographic heat map

2. **Sales Pipeline Dashboard** (3-4 hours)
   - Quote funnel visualization
   - Win rate analysis
   - Revenue forecasts
   - Conversion metrics

3. **Operations Dashboard** (4-6 hours)
   - Active projects
   - Resource allocation
   - Equipment status
   - Schedule adherence

4. **Financial Dashboard** (3-4 hours)
   - Revenue recognition tracking
   - Billing status
   - Margin analysis
   - Client profitability

5. **Compliance Dashboard** (2-3 hours)
   - Calibration status
   - Certification expiration
   - Insurance tracking
   - Safety compliance

**Prerequisites**:
- 6+ months of operational data
- Power BI Pro licenses
- Report specifications

---

### **Priority 3C: Mobile App Optimization** (20-30 hours)
**Status**: Future planning  
**Effort**: High  
**Value**: Medium-High

**Enhancements**:
- Offline capability for field techs
- Barcode/QR scanning for equipment
- Photo attachments for apparatus
- GPS check-in at sites
- Signature capture

---

## 🎯 IMMEDIATE ACTION PLAN

### **This Week (Nov 22-29)**:

**Day 1-2: Relationships**
- [ ] Configure all 9 lookup relationships
- [ ] Test referential integrity
- [ ] Document relationship behaviors

**Day 3-4: Forms (Priority Tables)**
- [ ] Create Client form
- [ ] Create Site form
- [ ] Create Employee form

**Day 5: Forms (Secondary Tables)**
- [ ] Create Quote form
- [ ] Create Resource Assignment form
- [ ] Create Equipment form

**Weekend: Testing**
- [ ] Enter sample data
- [ ] Test all relationships
- [ ] Validate workflows

### **Next Week (Nov 29 - Dec 6)**:

**Week 2: Views & Security**
- [ ] Create 30+ views across 6 tables
- [ ] Configure security roles
- [ ] Test with different user accounts
- [ ] Document security model

**Week 2: Documentation**
- [ ] Update all architecture docs
- [ ] Create user guides for new tables
- [ ] Update training materials

### **Week 3+ (Dec 6+)**:

**Phase 2 Planning**:
- [ ] Define revenue rollup requirements
- [ ] Plan notification flows
- [ ] Design advanced calculations
- [ ] Prioritize v1.5.0.0 features

---

## 📋 DECISION FRAMEWORK

### **When Considering New Features**:

**Step 1: Categorize**
- Bug/Issue → Fix immediately
- v1.4.0.0 completion → Add to Phase 1
- v1.5.0.0 enhancement → Add to Phase 2
- v1.6.0.0+ → Add to Phase 3

**Step 2: Evaluate**
- Business Value: High/Medium/Low
- Effort: High/Medium/Low
- Dependencies: What blocks this?
- Priority: Critical/High/Medium/Low

**Step 3: Assign**
- Critical + Low Effort → Do now
- High Value + Low Effort → Next batch
- High Effort → Plan thoroughly first
- Low Value → Parking lot

---

## 📊 SUCCESS METRICS

### **v1.4.0.0 Complete When**:
- ✅ All 9 relationships configured
- ✅ All 6 forms created and tested
- ✅ 30+ views operational
- ✅ Security roles configured
- ✅ Sample data validates system
- ✅ Documentation updated
- ✅ Solution exported as v1.4.0.0

### **v1.5.0.0 Complete When**:
- ✅ Date tracking implemented
- ✅ Revenue rollups operational
- ✅ 5 notification flows deployed
- ✅ Advanced calculations active
- ✅ Performance optimized

### **v1.6.0.0 Complete When**:
- ✅ QuickBooks integration live
- ✅ 5 Power BI dashboards deployed
- ✅ Mobile app optimized
- ✅ External data sources integrated

---

## 🎓 LESSONS FROM v1.4.0.0 BUILD

**What Worked**:
1. Template-first approach (Excel before API)
2. Reusable PowerShell functions
3. Comprehensive field planning
4. Sample data validation

**What to Improve**:
1. Earlier relationship planning
2. Forms/views designed alongside tables
3. Security planning from start
4. Incremental testing

**Apply to Future Phases**:
- Design complete before building
- Test incrementally, not all at end
- Document as you go, not after
- Plan for change from start

---

## 📞 QUICK REFERENCE

### **Current Status**:
- **Version**: v1.4.0.0 (tables created, relationships pending)
- **Tables**: 14 (8 original + 6 new)
- **Fields**: 291+
- **Next Milestone**: Complete Phase 1 (relationships, forms, views)

### **Key Documents**:
- This Roadmap (priorities and plan)
- SESSION_SUMMARY_NOV22 (what was built)
- PROJECT_STATUS_TRACKER (overall status)
- Architecture_Diagrams (ERD with new tables)

### **Decision Makers**:
- Relationships: Project team
- Forms/Views: User feedback + best practices
- Security: IT/HR requirements
- Features: Business value analysis

---

**END OF ROADMAP**

*This document provides the strategic plan for completing v1.4.0.0 and evolving to v1.5.0.0 and beyond. Update as priorities change or milestones are achieved.*

**Created**: November 22, 2025  
**Next Review**: December 1, 2025 (after Phase 1 complete)  
**Owner**: Project Team
