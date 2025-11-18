# RESA Power - Project Tracker

Internal project tracking solution for electrical testing operations. Built on Microsoft Power Platform to replace Excel-based processes.

---

## What This Does

Tracks apparatus-level work through projects (switchgear, transformers, breakers, etc.) with labor hours, costs, and revenue calculation. Replaces manual Excel tracking with real-time Dataverse database.

**Key Features:**
- Project hierarchy: Projects → Scopes → Tasks → Apparatus
- Labor cost tracking (4 categories: Onsite, Offsite, Travel, Outside Services)
- Automatic revenue recognition based on completed hours
- Multi-location support with business unit isolation
- Role-based access for different user types

---

## Why This Was Built

**Problems with old Excel process:**
- Each location maintained separate spreadsheets
- Month-end consolidation took days of manual copying/pasting
- No real-time visibility into project status
- Difficult to track revenue by project manager or equipment type
- High risk of duplicate entries or formula errors

**What this solves:**
- Single source of truth in Dataverse
- Automatic revenue calculation when apparatus marked complete
- Real-time dashboards instead of stale Excel reports
- Standardized process across multiple business units
- Audit trail for all changes

---

## Repository Structure

- **`Documentation/00_START_HERE/`** - Getting started guides and roadmap
- **`Documentation/01_Architecture/`** - Technical design and data models
- **`Documentation/02_Implementation/`** - Build specifications and field definitions
- **`Documentation/03_Progress_Tracking/`** - Development logs and version history
- **`Documentation/04_Data_Migration/`** - Excel templates and import guides
- **`Documentation/05_Reviews_Analysis/`** - Technical audits and recommendations
- **`Documentation/08_Testing_QA/`** - Testing scenarios and validation
- **`Documentation/09_Training_Materials/`** - User training and rollout plans
- **`Documentation/10_Analytics_Reporting/`** - Dashboard designs
- **`Documentation/11_Mobile_Apps/`** - Field app design concepts
- **`Solution_Exports/`** - Power Platform solution packages (.zip files)
- **`PROJECT_OVERVIEW.md`** - Comprehensive overview with diagrams

---

## Current Status

**Version:** v1.3.0.1 (Development Environment)

**What's Built:**
- 8 custom Dataverse tables (BusinessUnit, Projects, Scopes, Tasks, Apparatus, ScopeLaborDetail, ApparatusRevenue, TestRecords)
- 137 custom fields with calculated formulas
- 4 Power Apps (model-driven apps for different user roles)
- Revenue architecture complete (labor rates, cost tracking, revenue calculation)

**Next Steps:**
- Build Power Automate flow for automatic revenue recognition
- User testing with pilot project managers
- Create quick-start training guides
- Deploy to initial business units

---

## Technical Details

**Platform:** Microsoft Power Platform
- Dataverse (database)
- Power Apps (user interface)
- Power Automate (workflows)
- Power BI (reporting - planned)

**Architecture Highlights:**
- Hierarchical project structure (4 levels)
- Calculated fields for revenue recognition
- Business unit security (users only see their location's data)
- Audit logging (all changes tracked with user/timestamp)
- NETA standards compliance (apparatus types, testing workflows)

**Key Calculations:**
- Effective Labor Rate = Total Labor Cost ÷ Total Hours
- Revenue Amount = Apparatus Hours × Effective Labor Rate
- Automatic status changes (Pending → Recognized when apparatus completed)

---

## Implementation Plan

### **Phase 1: Pilot (Q1 2026)**
- Deploy to 4 Phoenix-region business units
- User acceptance testing with 2 project managers
- Create training materials (quick-start guides)
- Gather feedback and iterate

### **Phase 2: Expansion**
- Roll out based on pilot results
- Add Power BI dashboards for reporting
- Build mobile app for field technicians
- Continue refinement based on user needs

---

## Training Approach

Different training for different roles:

- **Field Technicians:** 15 minutes - How to mark apparatus complete
- **Job Leads:** 30 minutes - Work assignment and team coordination
- **Project Managers:** 90 minutes - Full project lifecycle and reporting
- **Operations Staff:** 60 minutes - Data entry and administrative tasks
- **Location Managers:** 60 minutes - Multi-project view and dashboards

Training materials include quick-start PDFs, video tutorials, and hands-on workshops.

See `Documentation/09_Training_Materials/` for details.

---

## Testing

Testing focuses on real-world scenarios:

1. **Revenue Recognition:** Compare automatic calculations to manual Excel
2. **Duplicate Prevention:** Verify apparatus can't be entered twice
3. **Missing Rates:** Handle projects without labor rates defined
4. **Performance:** Test with realistic data volumes
5. **User Acceptance:** Pilot PMs run real projects for 30 days

See `Documentation/08_Testing_QA/` for test scenarios.

---

## Security Model

**Role-Based Access:**
- Field Tech: Can only update assigned apparatus
- Job Lead: Can assign work and view team status
- Project Manager: Full access to their projects
- Operations: Data entry and administrative functions
- Location Manager: View all projects at their business unit

**Business Unit Isolation:**
- Users only see projects from their assigned location(s)
- Regional managers can see multiple locations
- Security enforced by Dataverse at database level

**Audit Trail:**
- All changes logged with user ID and timestamp
- No data deletion (soft deletes only)
- Complete history available for compliance

---

## Documentation

**Start Here:**
- `PROJECT_OVERVIEW.md` - System overview with architecture diagrams
- `Documentation/00_START_HERE/PLATFORM_ROADMAP_STRATEGIC_VISION.md` - Long-term vision

**Technical Details:**
- `Documentation/01_Architecture/REVENUE_ARCHITECTURE.md` - Revenue calculation design
- `Documentation/01_Architecture/USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md` - User roles and workflows
- `Documentation/02_Implementation/` - Build specifications for each component

**For Project Managers:**
- `Documentation/09_Training_Materials/TRAINING_PROGRAM_OVERVIEW.md` - Training details
- `Documentation/04_Data_Migration/` - How to import existing Excel data

---

## Repository Status

🔒 **Private Repository**  
🚧 **Development Phase** (v1.3.0.1)  
📅 **Target Pilot:** Q1 2026

---

*Built to solve real operational problems across multiple business units. Started as a personal initiative to improve inefficient Excel processes.*
