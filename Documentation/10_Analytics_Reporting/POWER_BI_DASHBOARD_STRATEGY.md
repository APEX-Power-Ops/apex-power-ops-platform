# Power BI Dashboards & Analytics

**Version:** 1.0  
**Status:** 🚧 IN DEVELOPMENT  
**Last Updated:** November 17, 2025

---

## 🎯 Overview

Enterprise-grade Power BI reporting suite providing real-time visibility into project performance, revenue tracking, and operational metrics across 40+ business units.

---

## 📊 Dashboard Portfolio

### **Executive Dashboard (Regional VP)**
**Target Audience:** C-Suite, Regional VPs, PE Operating Partners  
**Update Frequency:** Real-time  
**Status:** 📅 Planned Q2 2026

**Key Metrics:**
- Portfolio revenue (recognized vs. projected)
- EBITDA by business unit
- Project margin analysis (budget vs. actual)
- Resource utilization by location
- Capacity planning heat map
- Top 10 projects by revenue
- Monthly revenue trend (12-month rolling)

**Visualizations:**
- 📊 Revenue waterfall (budget → actual → variance)
- 🗺️ Geographic heat map (location performance)
- 📈 Trend lines (revenue, hours, margin)
- 🎯 KPI scorecards (YTD vs. target)

**Data Sources:**
- Dataverse (Projects, Scopes, ApparatusRevenue)
- ScopeLaborDetail (budget/rate data)
- BusinessUnit (location segmentation)

---

### **Location Manager Dashboard**
**Target Audience:** Location Managers (Phoenix, Vegas, Denver, San Diego)  
**Update Frequency:** Real-time  
**Status:** 📅 Planned Q1 2026

**Key Metrics:**
- Active projects by status
- Team utilization rate (hours worked vs. capacity)
- Revenue by project manager
- Average project margin
- Completion rate (apparatus completed vs. planned)
- Delays by project (impact analysis)
- Top customers by revenue

**Visualizations:**
- 📊 Project pipeline (funnel chart)
- 👥 Team capacity gauge charts
- 📅 Gantt chart (project timelines)
- 🔴 Alert cards (at-risk projects)

**Data Sources:**
- Dataverse (Projects, Scopes, Tasks, Apparatus)
- BusinessUnit (location filter)
- Work assignment fields (Assigned_To)

---

### **Project Manager Dashboard**
**Target Audience:** Project Managers  
**Update Frequency:** Real-time  
**Status:** 🚧 In Design (Priority)

**Key Metrics:**
- My active projects (status overview)
- Budget vs. actual by project
- Apparatus completion rate
- Hours variance (estimated vs. actual)
- Revenue recognized to date
- Upcoming milestones
- Overdue apparatus

**Visualizations:**
- 📋 Project list (filterable table)
- 📊 Budget variance charts
- ⏱️ Hours tracking (stacked bar: onsite/offsite/travel)
- 🎯 Completion progress (circular gauges)

**Data Sources:**
- Dataverse (all entities filtered by PM)
- ScopeLaborDetail (budget comparison)
- ApparatusRevenue (financial tracking)

**Drill-Through Capabilities:**
- Click project → see all scopes
- Click scope → see all tasks
- Click task → see all apparatus
- Click apparatus → see revenue details

---

### **Field Operations Dashboard**
**Target Audience:** Job Leads, Operations Coordinators  
**Update Frequency:** Real-time  
**Status:** 📅 Planned Q1 2026

**Key Metrics:**
- Work assignments by technician
- Apparatus completion rate by tech
- Daily/weekly hours by technician
- Overdue apparatus (workload management)
- Completion delays by reason code
- Crew availability calendar

**Visualizations:**
- 👥 Resource allocation matrix
- 📅 Work calendar (by tech/day)
- 🔴 Alert cards (overdue work)
- 📊 Completion velocity (trend)

**Data Sources:**
- Apparatus (with Assigned_To fields)
- Date tracking fields (Start_Date, Target_Date)
- Completion_Status tracking

---

### **Financial Dashboard (Revenue Recognition)**
**Target Audience:** Account Managers, CFO, Finance Team  
**Update Frequency:** Real-time  
**Status:** 🚧 High Priority - Phase 5E Dependency

**Key Metrics:**
- Revenue recognized (MTD, QTD, YTD)
- Revenue by scope (detail view)
- Revenue by customer
- Effective labor rate analysis
- Budget variance (scope-level detail)
- Unbilled work (apparatus complete but not invoiced)

**Visualizations:**
- 📊 Revenue waterfall by project
- 💰 Revenue by month (trend)
- 🎯 Budget vs. actual scatter plot
- 📋 Detailed revenue line items (table)

**Data Sources:**
- ApparatusRevenue (all revenue records)
- ScopeLaborDetail (rate and budget data)
- Projects (customer information)

**Export Capabilities:**
- Excel export for accounting system import
- PDF export for customer billing support
- CSV export for ERP integration

---

## 🛠️ Technical Architecture

### **Data Connectivity**
- **Primary Source:** Dataverse (Power Platform connector)
- **Refresh Frequency:** Real-time (DirectQuery) or 15-min incremental refresh
- **Authentication:** Azure AD / Power BI Service Principal

### **Data Model Design**
```
Projects (Fact)
├── BusinessUnit (Dimension)
├── ProjectScope (Fact)
│   ├── ScopeLaborDetail (Dimension - Budget/Rates)
│   ├── Tasks (Fact)
│   │   └── Apparatus (Fact)
│   │       └── ApparatusRevenue (Fact)
└── Date Table (Dimension - for time intelligence)
```

### **Performance Optimization**
- Aggregations pre-calculated in Dataverse (rollup fields)
- Star schema design for optimal query performance
- Incremental refresh for historical data
- DirectQuery for real-time metrics

---

## 📱 Power BI Mobile Experience

### **Mobile-Optimized Dashboards**
- **Executive Summary:** Single-page KPI view
- **Project Manager:** My projects list + drill-through
- **Field Operations:** Work assignment view

**Status:** 📅 Planned Q3 2026 (after desktop rollout)

---

## 🔐 Security & Access Control

### **Row-Level Security (RLS)**

**By Business Unit:**
- Location Managers see only their location data
- Regional VPs see all locations in their region
- C-Suite sees all data

**By Project Manager:**
- PMs see only projects they manage
- Can view cross-project reports for their location

**Implementation:**
- RLS rules based on BusinessUnit lookup
- User table mapping (email → BusinessUnit)
- Dynamic security based on Power BI user identity

---

## 📈 Advanced Analytics (Future)

### **Predictive Analytics (Phase 2)**
- **Project completion forecasting** (ML model based on historical data)
- **Resource demand prediction** (staffing optimization)
- **Revenue forecasting** (expected completion dates × rates)
- **Anomaly detection** (flag unusual delays, cost overruns)

**Status:** 📅 Planned 2027 (after 12 months of operational data)

### **What-If Analysis**
- **Scenario planning:** "What if we add 2 more PMs?"
- **Rate impact:** "What if labor rates increase 10%?"
- **Capacity modeling:** "Can we take on 5 more projects?"

**Status:** 📅 Planned Q4 2026

---

## 📊 Sample Visualizations

### **Revenue Waterfall Chart:**
```
Budget Revenue:     $1,250,000
├── Completed Work: $  850,000  ✅
├── In Progress:    $  300,000  🟡
├── Not Started:    $  100,000  ⚪
└── Total Variance: $        0
```

### **Location Performance Scorecard:**
```
┌─────────────────┬──────────┬─────────┬────────┐
│ Location        │ Revenue  │ Margin  │ Status │
├─────────────────┼──────────┼─────────┼────────┤
│ Phoenix         │ $425k    │ 18.5%   │ 🟢     │
│ Las Vegas       │ $310k    │ 22.1%   │ 🟢     │
│ Denver          │ $275k    │ 15.8%   │ 🟡     │
│ San Diego       │ $190k    │ 12.3%   │ 🔴     │
└─────────────────┴──────────┴─────────┴────────┘
```

---

## 🚀 Development Roadmap

### **Phase 1: Foundation (Q1 2026)**
- ✅ Data model design complete
- 🚧 Build Project Manager dashboard (MVP)
- 🚧 Build Financial dashboard (Revenue Recognition)
- 📅 Deploy to pilot users

### **Phase 2: Expansion (Q2 2026)**
- 📅 Executive Dashboard
- 📅 Location Manager Dashboard
- 📅 Field Operations Dashboard
- 📅 Row-level security implementation

### **Phase 3: Advanced Features (Q3-Q4 2026)**
- 📅 Mobile optimization
- 📅 What-if analysis tools
- 📅 Advanced drill-through capabilities
- 📅 Custom visual development

### **Phase 4: Predictive Analytics (2027)**
- 📅 Machine learning integration
- 📅 Forecasting models
- 📅 Anomaly detection
- 📅 Optimization recommendations

---

## 📚 Documentation & Training

### **User Guides (Coming Q1 2026):**
- "Power BI Dashboard Quick Start" (all users)
- "Project Manager Dashboard Deep Dive" (PMs)
- "Financial Reporting Guide" (Finance team)
- "Dashboard Customization" (Power Users)

### **Video Tutorials (Coming Q1 2026):**
- "Navigating Your Dashboard" (5 min)
- "Drilling Through to Details" (3 min)
- "Exporting Data for Reports" (4 min)
- "Mobile Dashboard Access" (3 min)

---

## 🎯 Success Metrics

**Target Adoption Rates:**
- Executive Dashboard: 100% (mandatory for leadership)
- PM Dashboard: 95%+ (primary work tool)
- Financial Dashboard: 100% (finance team)
- Field Operations: 80%+ (optional but encouraged)

**Performance Targets:**
- Dashboard load time: <3 seconds
- Query response time: <2 seconds
- Mobile performance: <5 seconds on 4G

---

## 💡 Integration with Power Apps

### **Embedded Analytics:**
- Revenue charts embedded in Project forms
- Completion progress widgets in PM view
- Real-time KPIs in model-driven app

**Status:** 📅 Planned Q2 2026 (after dashboard rollout)

---

## 📁 Related Documentation

- `Documentation/01_Architecture/USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md` - User personas
- `Documentation/01_Architecture/REVENUE_ARCHITECTURE.md` - Data model for financial reports
- `Reference_Files/PowerBI/RESA_Dashboard.pbix` - Current legacy dashboard (reference only)

---

**Document Owner:** Jason Swenson  
**Status:** Architecture designed, development starting Q1 2026  
**Priority:** HIGH - Critical for executive visibility and user adoption
