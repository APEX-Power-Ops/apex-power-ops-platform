# RESA Power - Power Apps Implementation Checklist

## Pre-Implementation Setup

### Environment & Licensing
- [ ] Request Power Apps environment from IT
- [ ] Provision Dataverse database
- [ ] Assign Power Apps licenses to users
- [ ] Assign Power Automate licenses (if separate)
- [ ] Assign Power BI licenses for report creators
- [ ] Set up development, test, and production environments
- [ ] Configure Azure AD security groups

### Team & Governance
- [ ] Identify project sponsor (executive level)
- [ ] Assign project manager
- [ ] Identify Power Platform developer(s)
- [ ] Select key users from each role for testing
- [ ] Form steering committee
- [ ] Create communication plan
- [ ] Define change management approach

---

## Phase 1: Foundation (Weeks 1-2)

### Dataverse Setup
- [ ] Design complete data model (review ERD)
- [ ] Create all tables in Dataverse
  - [ ] Locations (master table)
  - [ ] Apparatus_Type_Master (with ATS/MTS specifications) ⭐
  - [ ] Projects
  - [ ] Scopes (with NETA_Standard choice field: ATS/MTS) ⭐
  - [ ] Tasks (IMMEDIATE IMPLEMENTATION - manual creation, not imported) ⭐
  - [ ] Apparatus
  - [ ] Scope_Financial_Configuration (financial rates, restricted access) ⭐
- [ ] Configure column types and properties
- [ ] Set up table relationships
- [ ] Create choice columns (Status, Priority, **NETA_Standard: ATS/MTS**) ⭐
- [ ] Configure calculated and rollup fields
- [ ] Set up business rules
  - [ ] NETA_Standard inheritance from Scope to Tasks/Apparatus ⭐
- [ ] Create alternate keys where needed

### Security Configuration
- [ ] Define security roles (Admin, PM, Technician, Billing, Executive)
- [ ] Configure field-level security
- [ ] Set up teams
- [ ] Configure sharing permissions
- [ ] Test security with sample users
- [ ] Document security model

### Sample Data
- [ ] Create 3-5 sample projects
- [ ] Add 20-30 sample tasks
- [ ] Create 5-10 apparatus items
- [ ] Add reference list values
- [ ] Create sample scopes
- [ ] Test data relationships

---

## Phase 2: Data Migration (Weeks 3-4)

### Data Preparation
- [ ] Export all Excel data to CSV
- [ ] Clean data (remove nulls, fix formats)
- [ ] Create data mapping document
- [ ] Validate data quality
- [ ] Identify and fix data issues
- [ ] Handle duplicate records
- [ ] Prepare lookup value mappings

### Migration Execution
- [ ] Import reference data (dropdowns, NETA Standard choices) ⭐
- [ ] Import apparatus catalog (Apparatus_Type_Master with ATS/MTS specs) ⭐
- [ ] Import projects
- [ ] Import scopes (with NETA_Standard from Excel Cell C3) ⭐
- [ ] Import scope financial configurations (restricted data) ⭐
- [ ] Import apparatus (expand quantities, link to NETA_Standard) ⭐
- [ ] **SKIP Tasks import** (Excel has no task structure - PMs create manually) ⭐
- [ ] Import historical time entries
- [ ] Import historical billing data

### Data Validation
- [ ] Verify record counts match source
- [ ] Check relationship integrity
- [ ] Validate calculations
- [ ] Test data in views
- [ ] User acceptance of migrated data
- [ ] Fix any data issues
- [ ] Create migration report

### Manual Task Creation ⭐ NEW
- [ ] Train PMs on task creation process
  - [ ] Review apparatus grouping strategies
  - [ ] Define task naming conventions
  - [ ] Establish task assignment workflows
- [ ] PM reviews imported scopes and apparatus
- [ ] PM creates tasks to organize apparatus
  - [ ] Group similar apparatus types
  - [ ] Consider physical location grouping
  - [ ] Balance workload across technicians
  - [ ] Account for equipment dependencies
- [ ] PM assigns tasks to technicians
  - [ ] Match skills to apparatus types
  - [ ] Balance technician workloads
  - [ ] Consider schedule constraints
- [ ] Verify NETA section references match Scope's NETA_Standard ⭐
- [ ] Document task organization rationale

---

## Phase 3: Canvas App Development (Weeks 5-7)

### App Structure
- [ ] Create new Canvas app in solution
- [ ] Design home screen layout
- [ ] Create navigation menu
- [ ] Build reusable components
- [ ] Implement color scheme and branding
- [ ] Set up responsive design

### Core Screens
- [ ] Home dashboard screen
  - [ ] My tasks today widget
  - [ ] Overdue alerts
  - [ ] Quick actions
  - [ ] Recent projects list
  
- [ ] Task entry screen
  - [ ] Project/scope lookup
  - [ ] Apparatus selection dropdown
  - [ ] Status update controls
  - [ ] Photo capture for datasheet
  - [ ] Notes field
  - [ ] Save functionality
  
- [ ] Task list screen
  - [ ] Filter by project/status
  - [ ] Search functionality
  - [ ] Sort options
  - [ ] Bulk actions
  
- [ ] Time entry screen
  - [ ] Date picker
  - [ ] Task lookup
  - [ ] Hours entry
  - [ ] Labor type selector
  - [ ] Submit for approval
  
- [ ] Project lookup screen
  - [ ] Search by job #, client
  - [ ] Project details view
  - [ ] Task summary
  - [ ] Navigation to tasks

### Functionality
- [ ] Implement data connections to Dataverse
- [ ] Create data collections for offline
- [ ] Add form validation
- [ ] Implement error handling
- [ ] Add confirmation dialogs
- [ ] Create loading indicators
- [ ] Test on mobile devices
- [ ] Implement offline capability

### Testing
- [ ] Unit test each screen
- [ ] Test all workflows end-to-end
- [ ] Test on iOS devices
- [ ] Test on Android devices
- [ ] Test offline scenarios
- [ ] Performance testing
- [ ] User acceptance testing

---

## Phase 4: Model-Driven App Development (Weeks 8-10)

### App Foundation
- [ ] Create new Model-Driven app in solution
- [ ] Design site map (navigation)
- [ ] Create app modules
- [ ] Configure app settings
- [ ] Add branding (logo, colors)

### Forms
- [ ] Design Project form (multi-tab)
  - [ ] General info tab
  - [ ] Scopes tab (subgrid)
  - [ ] Tasks tab (subgrid)
  - [ ] Billing tab
  - [ ] Documents tab
  - [ ] Timeline
  
- [ ] Design Task form (multi-tab)
  - [ ] Details tab
  - [ ] Time entries subgrid
  - [ ] Billing subgrid
  - [ ] Related tasks
  - [ ] Notes tab
  
- [ ] Design other entity forms
  - [ ] Scope form
  - [ ] Time Entry form
  - [ ] Billing Line form
  - [ ] Apparatus form

### Views
- [ ] Create system views for each entity
  - [ ] Active Projects
  - [ ] All Projects
  - [ ] My Projects
  - [ ] Completed Projects
  - [ ] My Tasks
  - [ ] All Tasks
  - [ ] Overdue Tasks
  - [ ] Tasks by Status
  - [ ] Recent Time Entries
  - [ ] Pending Approvals
  
- [ ] Configure view columns
- [ ] Add filters and sorting
- [ ] Create charts on views
- [ ] Configure quick find

### Business Process Flows
- [ ] Create Project Lifecycle BPF
  - [ ] Setup stage
  - [ ] Scoping stage
  - [ ] Execution stage
  - [ ] Billing stage
  - [ ] Closeout stage
  
- [ ] Create Task Completion BPF
  - [ ] Assigned stage
  - [ ] In Progress stage
  - [ ] Review stage
  - [ ] Completed stage

### Dashboards
- [ ] Create Project Overview dashboard
- [ ] Create Task Performance dashboard
- [ ] Create Billing dashboard
- [ ] Create My Work dashboard
- [ ] Add charts to dashboards
- [ ] Configure dashboard filters

### Testing
- [ ] Test all forms and tabs
- [ ] Test all views and filters
- [ ] Test business process flows
- [ ] Test dashboards
- [ ] Test security roles
- [ ] User acceptance testing

---

## Phase 5: Power Automate Workflows (Weeks 11-12)

### Notification Flows
- [ ] Task Assignment Notification
  - [ ] Trigger: On task create/update
  - [ ] Condition: Assigned user changed
  - [ ] Action: Send Teams + Email
  - [ ] Include: Task details, link
  - [ ] Test with multiple users
  
- [ ] Overdue Task Alert
  - [ ] Trigger: Scheduled (daily 8 AM)
  - [ ] Get: Tasks past due date
  - [ ] Action: Notify assigned user + PM
  - [ ] Test scheduled execution

### Approval Flows
- [ ] Time Entry Approval Flow
  - [ ] Trigger: On time entry submit
  - [ ] Action: Request approval from PM
  - [ ] On approve: Update status
  - [ ] On reject: Notify with reason
  - [ ] Test approval scenarios
  
- [ ] Billing Approval Flow
  - [ ] Similar structure for billing

### Automation Flows
- [ ] Weekly Billing Report
  - [ ] Trigger: Schedule (Friday)
  - [ ] Get: Billing lines for week
  - [ ] Generate: PDF report
  - [ ] Send: Email to billing team
  - [ ] Test report generation
  
- [ ] Project Status Update
  - [ ] Trigger: Task status change
  - [ ] Check: All tasks complete?
  - [ ] Update: Scope/project status
  - [ ] Notify: Stakeholders
  - [ ] Test cascading updates

### Document Flows
- [ ] Datasheet Upload to SharePoint
  - [ ] Trigger: File attachment added
  - [ ] Action: Copy to SharePoint
  - [ ] Tag: With metadata
  - [ ] Test file handling

### Error Handling
- [ ] Add try-catch to all flows
- [ ] Configure error notifications
- [ ] Create error log table
- [ ] Test failure scenarios

---

## Phase 6: Power BI Reporting (Weeks 13-14)

### Report Development
- [ ] Create Power BI workspace
- [ ] Connect to Dataverse
- [ ] Build data model in Power BI
- [ ] Create measures and calculations

### Dashboard 1: Project Overview
- [ ] Active projects count card
- [ ] Projects by status chart
- [ ] Total hours gauge
- [ ] Project timeline (Gantt)
- [ ] Top 10 projects table
- [ ] Budget vs Actual chart

### Dashboard 2: Task Performance
- [ ] Tasks by status pie chart
- [ ] Overdue tasks card
- [ ] Completion trend line
- [ ] Task delays analysis
- [ ] Priority distribution

### Dashboard 3: Billing Analytics
- [ ] Weekly billing totals
- [ ] Revenue by project
- [ ] Labor type breakdown
- [ ] Billing forecast
- [ ] Utilization rate

### Dashboard 4: Resource Management
- [ ] Hours by team member
- [ ] Workload distribution
- [ ] Capacity planning
- [ ] Apparatus usage

### Dashboard 5: Quality Metrics
- [ ] Assessment outcomes
- [ ] Deficiency rates
- [ ] Rework analysis
- [ ] Quality trends

### Deployment
- [ ] Publish reports to workspace
- [ ] Configure row-level security
- [ ] Share with user groups
- [ ] Embed in Model-Driven app
- [ ] Create Teams tabs
- [ ] Schedule refresh
- [ ] Test access permissions

---

## Phase 7: Testing & Training (Weeks 15-16)

### Testing
- [ ] Unit testing (all components)
  - [ ] Test each screen/form
  - [ ] Test each flow
  - [ ] Test each report
  
- [ ] Integration testing
  - [ ] End-to-end workflows
  - [ ] Cross-app scenarios
  - [ ] Security testing
  
- [ ] Performance testing
  - [ ] Load testing
  - [ ] Response time testing
  - [ ] Mobile performance
  
- [ ] User Acceptance Testing (UAT)
  - [ ] Recruit 5-10 pilot users
  - [ ] Provide test scenarios
  - [ ] Collect feedback
  - [ ] Document issues
  - [ ] Fix critical bugs
  
- [ ] Security testing
  - [ ] Test each role
  - [ ] Verify data access
  - [ ] Test field-level security
  - [ ] Penetration testing

### Training Materials
- [ ] Create admin guide (10-15 pages)
- [ ] Create PM user guide (15-20 pages)
- [ ] Create field user guide (5-10 pages)
- [ ] Create quick reference cards
- [ ] Record video tutorials (5-10 videos)
- [ ] Build FAQ document
- [ ] Create support portal/wiki

### Training Sessions
- [ ] Schedule training sessions
- [ ] Conduct admin training (4 hours)
  - [ ] Data management
  - [ ] User management
  - [ ] Configuration
  - [ ] Troubleshooting
  
- [ ] Conduct PM training (3 hours) ⭐ EXTENDED
  - [ ] Model-driven app walkthrough
  - [ ] **NETA Standards overview (ATS vs MTS)** ⭐ NEW (15 min)
    - [ ] When to use ATS vs MTS
    - [ ] Impact on labor hours and sections
    - [ ] Setting NETA_Standard in Excel Cell C3
  - [ ] Project creation
  - [ ] Import process from Excel estimator ⭐
  - [ ] **Manual task creation workflow** ⭐ NEW (20 min)
    - [ ] Organizing apparatus into tasks
    - [ ] Task assignment best practices
    - [ ] Technician workload balancing
  - [ ] Task management
  - [ ] Billing review
  - [ ] Reporting
  
- [ ] Conduct field user training (2 hours)
  - [ ] Canvas app basics
  - [ ] Task updates
    - [ ] **Understanding NETA section references** ⭐ NEW
    - [ ] Finding correct test procedures
  - [ ] Time entry
  - [ ] Mobile features
  - [ ] Offline mode
  
- [ ] Record training sessions
- [ ] Collect training feedback
- [ ] Create help desk process

---

## Phase 8: Go-Live & Support (Week 17+)

### Pre-Launch
- [ ] Final data migration from Excel
- [ ] Verify all data in production
- [ ] Freeze Excel file (archive)
- [ ] Set up monitoring/analytics
- [ ] Prepare support team
- [ ] Create escalation process
- [ ] Set up help desk email
- [ ] Prepare go-live communication

### Parallel Run (1-2 weeks)
- [ ] Users use both systems
- [ ] Compare outputs daily
- [ ] Fix any discrepancies
- [ ] Build user confidence
- [ ] Collect feedback

### Phased Rollout
- [ ] Week 1: Pilot team (5-10 users)
- [ ] Week 2: Field technicians
- [ ] Week 3: Project managers
- [ ] Week 4: Billing team
- [ ] Week 5: Full organization
- [ ] Monitor adoption at each phase

### Hypercare Support (2 weeks)
- [ ] Daily standup meetings
- [ ] Rapid response to issues
- [ ] On-site support availability
- [ ] Monitor error logs hourly
- [ ] Quick fixes deployed
- [ ] Collect user feedback
- [ ] Create issues log

### Post-Launch Activities
- [ ] Conduct post-launch review
- [ ] Analyze usage analytics
- [ ] Survey user satisfaction
- [ ] Identify optimization needs
- [ ] Plan Phase 2 features
- [ ] Document lessons learned
- [ ] Celebrate success!

---

## Ongoing Maintenance Checklist

### Weekly
- [ ] Review error logs
- [ ] Check failed flow runs
- [ ] Monitor system performance
- [ ] Answer user questions
- [ ] Review support tickets
- [ ] Deploy minor fixes

### Monthly
- [ ] Review usage analytics
- [ ] Identify optimization opportunities
- [ ] Plan minor enhancements
- [ ] Update documentation
- [ ] Review security
- [ ] Check storage usage

### Quarterly
- [ ] Major feature release
- [ ] Security review
- [ ] Capacity planning
- [ ] User training refreshers
- [ ] Review integrations
- [ ] Update roadmap

### Annually
- [ ] Strategic review with stakeholders
- [ ] Roadmap planning for next year
- [ ] License optimization
- [ ] Archive old data
- [ ] Security audit
- [ ] Disaster recovery test

---

## Success Metrics Tracking

### Monitor These KPIs

- [ ] User adoption rate (target: 90%)
- [ ] Daily active users
- [ ] Task update frequency
- [ ] Data entry time (target: 50% reduction)
- [ ] Billing cycle time (target: 30% faster)
- [ ] Error rate (target: <5%)
- [ ] User satisfaction (target: 4/5)
- [ ] Mobile usage percentage
- [ ] Report generation time
- [ ] Support ticket volume

### Monthly Reporting
- [ ] Create KPI dashboard
- [ ] Present to leadership
- [ ] Identify trends
- [ ] Plan improvements
- [ ] Share wins with team

---

## Risk Mitigation

### Known Risks & Mitigation Plans

- [ ] **Risk**: Low user adoption
  - [ ] Mitigation: Extensive training, champions program
  - [ ] Mitigation: Make app easier than Excel
  - [ ] Mitigation: Management mandate
  
- [ ] **Risk**: Data quality issues
  - [ ] Mitigation: Data validation rules
  - [ ] Mitigation: Quality checks during migration
  - [ ] Mitigation: Ongoing monitoring
  
- [ ] **Risk**: Performance problems
  - [ ] Mitigation: Follow best practices
  - [ ] Mitigation: Load testing before launch
  - [ ] Mitigation: Optimize as needed
  
- [ ] **Risk**: Integration failures
  - [ ] Mitigation: Test thoroughly
  - [ ] Mitigation: Error handling in flows
  - [ ] Mitigation: Monitoring alerts
  
- [ ] **Risk**: Scope creep
  - [ ] Mitigation: Strict change control
  - [ ] Mitigation: Phase 2 feature list
  - [ ] Mitigation: Focus on MVP first

---

## Budget Tracking

### Licensing Costs
- [ ] Track user license assignments
- [ ] Monitor actual vs. planned costs
- [ ] Optimize license allocation
- [ ] Plan for growth

### Development Costs
- [ ] Track hours spent by phase
- [ ] Monitor vs. budget
- [ ] Document cost savings
- [ ] Calculate ROI

### Ongoing Costs
- [ ] Support team time
- [ ] Enhancement budget
- [ ] Training costs
- [ ] External consultant fees

---

## Appendix: Quick Links

### Documentation
- [ ] Data model ERD
- [ ] Security model diagram
- [ ] User guides
- [ ] Admin guides
- [ ] API documentation

### Training
- [ ] Video library link
- [ ] Training schedule
- [ ] Support portal
- [ ] FAQ page

### Tools
- [ ] Power Apps environment URL
- [ ] Model-driven app URL
- [ ] Canvas app URL
- [ ] Power BI workspace
- [ ] SharePoint site

### Support
- [ ] Help desk email
- [ ] Teams support channel
- [ ] Issue tracker
- [ ] Escalation contacts

---

**Last Updated**: November 7, 2025
**Version**: 1.0
**Owner**: [Project Manager Name]
**Next Review**: [Date]
