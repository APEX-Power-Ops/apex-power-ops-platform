# RESA Power Technology Platform
## Strategic Vision Document

**Created:** 2025-12-11  
**Author:** Jason Swenson  
**Audience:** Internal / Future PE Presentation  
**Status:** Foundation Built, Demos In Progress

---

## Executive Summary

RESA Power has the opportunity to transform from a service company using licensed third-party tools into a **technology-enabled service company with proprietary operational infrastructure**.

This platform:
- Eliminates 40%+ operational inefficiency company-wide
- Replaces expensive licensed software with purpose-built solutions
- Creates competitive differentiation in the electrical testing market
- Scales automatically with each acquisition
- Adds measurable enterprise value for PE exit

---

## The Problem

### Current State: Disconnected Tools

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│Estimator│   │Schedule │   │ PowerDB │   │Invoicing│   │   PM    │
│ (Excel) │   │(Connec- │   │ (Field) │   │ (D365)  │   │  ???    │
│         │   │ team)   │   │         │   │         │   │         │
└────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘
     │             │             │             │             │
     └──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┘
            │             │             │             │
            ▼             ▼             ▼             ▼
    [MANUAL ENTRY] [MANUAL ENTRY] [MANUAL ENTRY] [DOESN'T EXIST]
```

**Pain Points:**
- Same data entered 3-4 times across systems
- No visibility into operations (projects, scheduling, status)
- PowerDB: Poor sync, no integration, expensive licenses, clunky UI
- PM tracking: Essentially non-existent
- Each acquisition adds more chaos

### What Industry Leaders Say
> "It's PowerDB, so it's good."

### Reality
> "If PowerDB disappeared tomorrow, not one person would rebuild it the same way."

---

## The Solution

### RESA Operations Platform

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     RESA OPERATIONS PLATFORM                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ ESTIMATE │───▶│ PROJECT  │───▶│ SCHEDULE │───▶│  FIELD   │          │
│  │          │    │          │    │          │    │   WORK   │          │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘          │
│       │              │               │                 │                │
│       └──────────────┴───────────────┴─────────────────┤                │
│                                                        ▼                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │    PM    │◀───│ REPORTS  │◀───│ BILLING  │◀───│ COMPLETE │          │
│  │ TRACKING │    │   AUTO   │    │          │    │          │          │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘          │
│                                                                          │
│  ════════════════════════════════════════════════════════════           │
│                    UNIFIED DATABASE (Supabase)                           │
│  ════════════════════════════════════════════════════════════           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**One database. One source of truth. Everything connected.**

---

## Platform Components

### 1. Foundation: Unified Database ✅ BUILT

**Status:** Complete and operational

| Capability | Implementation |
|------------|----------------|
| Database | Supabase (PostgreSQL) |
| Tables | Clients, Sites, Projects, Scopes, Tasks, Apparatus |
| Test Library | 66 NETA procedures, 956 test items |
| Architecture | Modern, API-ready, real-time capable |
| Access | Full database access (no vendor lock-in) |

**Why It Matters:**
- Every other component builds on this foundation
- Data flows automatically between stages
- Single entry point eliminates duplicate work
- Full API access enables any integration

---

### 2. Visibility Dashboard 🎯 MVP

**Status:** In development (v0 demo complete)

**The Core Value Proposition:**
> "Where are all our projects? What needs attention? Who's working on what?"

| Feature | Benefit |
|---------|---------|
| Real-time project status | No more "where are we on this?" calls |
| Scheduling visibility | See tech assignments at a glance |
| Estimate pipeline | Track win rates, expiring quotes |
| Executive rollup | Regional and corporate views |
| Alert system | Proactive notification of issues |

**Target Users:**
- Regional managers (Jason, Brandon)
- Operations leadership
- Executive team

---

### 3. PowerDB Replacement 🎯 DEMO READY

**Status:** Schema mapped, integration path defined

**Current PowerDB Problems:**

| Problem | Cost |
|---------|------|
| Manual job creation | Hours/project |
| Data re-entry (3-4x) | Hours/project |
| Sync failures | Data loss, rework |
| No PM tracking | Missed maintenance contracts |
| Clunky forms | Technician frustration |
| License fees | $XXX,XXX/year |
| No integration | Island of data |

**Platform Replacement:**

| Feature | Implementation |
|---------|----------------|
| Mobile-first forms | Per-apparatus, friendly UI |
| Pre-populated data | Flows from estimate/project |
| Offline capable | Works in the field |
| Real-time sync | No more sync nightmares |
| Auto PM scheduling | Based on test history |
| Template engine | Form data → professional datasheets |
| Full integration | Connected to everything |

**Efficiency Gain:** 40%+ reduction in field admin overhead

**Schema Comparison:**

| PowerDB | RESA Platform |
|---------|---------------|
| 80 tables | Normalized, purpose-built |
| 163 GUIDs (45 enforced) | Proper foreign keys |
| nvarchar(20) "GUIDs" | Real UUIDs |
| Archive tables | Soft deletes with audit |
| VBScript automation | Modern APIs |
| Local sync hell | Real-time cloud sync |

---

### 4. TCC Calculator 🎯 DEMO READY

**Status:** 2.47 million rows, production database

**What It Is:**
Time-Current Curve Calculator for circuit breaker coordination studies.

| Metric | Value |
|--------|-------|
| Data points | 2,475,137 |
| Tables | 33 |
| Coverage | Major manufacturers, all breaker types |
| Stack | Python, FastAPI, PostgreSQL |

**Competitive Value:**
- No competitor has this depth of curve data
- Engineering services differentiator
- Potential SaaS product (client-facing)
- Demonstrates technical capability

---

### 5. Report Automation (Future)

**Capability:** One-click generation of all project deliverables

| Current State | Future State |
|---------------|--------------|
| Manual datasheet creation | Auto-generated from test data |
| Manual report compilation | Template-based assembly |
| Manual delivery | Automated client portal |
| No tracking | Full audit trail |

---

### 6. PM Tracking (Future)

**Capability:** Automatic preventative maintenance scheduling

| Feature | Implementation |
|---------|----------------|
| Test history | Every asset has complete history |
| Auto-scheduling | Next service date calculated |
| Client reminders | Automated outreach |
| Contract management | PM contract tracking |
| Revenue forecasting | Predictable recurring revenue |

**Business Impact:**
- Converts one-time work to recurring contracts
- Increases customer lifetime value
- Predictable revenue stream

---

## Financial Impact

### Cost Reduction

| Item | Annual Savings |
|------|----------------|
| PowerDB licenses | $XXX,XXX |
| Reduced admin hours | XX,XXX hours |
| Eliminated rework | $XXX,XXX |
| **Total** | **$X.XM+** |

### Revenue Enablement

| Item | Revenue Impact |
|------|----------------|
| PM tracking → recurring contracts | $XXX,XXX+ |
| Faster project completion | More throughput |
| TCC services | Engineering revenue |
| Reduced quote time | Higher win rate |

### Efficiency Gain

> **40%+ reduction in dead inefficiency company-wide**

This isn't optimization. This is eliminating work that shouldn't exist.

---

## PE Exit Value

### Kohlberg Timeline: ~4 Years to Exit

**What increases exit multiple:**

| Factor | Impact |
|--------|--------|
| Proprietary technology | ↑ Multiple (tech premium) |
| Reduced OpEx | ↑ EBITDA |
| Scalable with acquisitions | ↑ Growth story |
| "AI/ML investment" delivered | ↑ Multiple |
| Competitive moat | ↑ Defensibility |

### The Narrative for Next PE Buyer

> "RESA isn't just an electrical testing company. RESA has built proprietary technology that:
> - Eliminates 40% of operational overhead
> - Scales automatically with each acquisition  
> - Creates competitive differentiation
> - Enables new revenue streams (PM contracts, TCC services)
> - Reduces dependency on expensive third-party tools"

**This is the story that gets premium multiples.**

---

## Acquisition Scalability

RESA acquires 5-6 companies per year. Each acquisition currently adds:
- Another disconnected system to manage
- More manual data entry
- More sync problems
- More licenses

**With the platform:**
- New acquisition → Onboard to platform
- Immediate visibility into their operations
- Standardized processes from day one
- No additional licensing per location
- PM contracts migrated automatically

---

## Development Investment

### What's Already Built (3-4 Years)

| Asset | Status |
|-------|--------|
| Database schema | ✅ Complete |
| NETA test library | ✅ 66 procedures, 956 items |
| TCC database | ✅ 2.47M rows |
| PowerDB mapping | ✅ Schema documented |
| Technical capability | ✅ Proven |

### What's Needed

| Phase | Timeline | Deliverable |
|-------|----------|-------------|
| MVP Dashboard | Q1 2026 | Visibility for Arizona region |
| PowerDB Demo | Q1 2026 | Proof of concept forms |
| Regional Rollout | Q2 2026 | Arizona fully operational |
| Company-wide | 2026-2027 | All regions on platform |

### The Ask

This platform was built on personal time and investment. The foundation is laid. What's needed now:
- Time allocation to complete MVP
- Stakeholder buy-in for pilot
- Path to company-wide adoption

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| "Why not D365?" | D365 demo failed - couldn't explain scheduling |
| "PowerDB is industry standard" | Industry standard ≠ good |
| "Too ambitious" | Start with visibility, prove value, expand |
| "Vendor support" | Full database access, no lock-in |

---

## Conclusion

RESA has a choice:

**Option A:** Continue with disconnected tools
- Pay for PowerDB forever
- 40% efficiency loss continues
- Each acquisition adds chaos
- No competitive differentiation
- Commodity service company multiple at exit

**Option B:** Complete the platform
- Eliminate PowerDB costs
- 40%+ efficiency gains
- Acquisitions scale seamlessly
- Proprietary technology moat
- Tech-enabled service company premium at exit

The foundation is built. The path is clear. The ROI is measurable.

**The question isn't whether to do this. The question is how fast.**

---

## Appendix: Technical Assets

### Database Schema
- Location: Supabase (fxoyniqnrlkxfligbxmg)
- Documentation: `Supabase/SCHEMA_REFERENCE.md`

### TCC Calculator
- Location: `C:\Users\jjswe\Projects\tcc_v5_backend`
- Database: 2.47M rows, 33 tables
- Stack: Python, FastAPI, PostgreSQL

### PowerDB Analysis
- Location: `Reference_Files/PowerDB/`
- Schema audit: 80 tables, 1,209 columns documented
- Integration path: JobNumber as universal key

### NETA Library
- Procedures: 66 standard test procedures
- Test items: 956 individual test requirements
- Coverage: ATS + MTS specifications

---

*Document maintained in `.claude/PLATFORM_VISION.md`*
