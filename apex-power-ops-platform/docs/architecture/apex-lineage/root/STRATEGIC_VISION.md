# APEX Platform - Strategic Vision

**Document Version:** 1.0  
**Created:** January 7, 2026  
**Author:** Jason Swenson  
**Classification:** Confidential - Business Strategy

---

## Executive Summary

APEX Platform is a comprehensive field operations and project management system purpose-built for electrical testing and commissioning companies. It addresses systemic gaps in how testing companies manage projects, ensure safety compliance, develop technicians, and deliver value to clients.

**Strategic Timeline:**
- **Year 1 (2026):** Regional deployment under current management
- **Year 2 (2027):** Value demonstration and refinement
- **Year 3 (2028):** Acquisition opportunity at PE turnover

---

## The Problem

Current state at RESA Power (representative of industry):

| Pain Point | Impact |
|------------|--------|
| No centralized visibility | "Fits in your head" breaks at scale (5→15 projects) |
| Scattered resources | Techs hunt for procedures, specs, safety docs |
| Inconsistent quality | Output depends on individual expertise, not system |
| Manual safety documentation | AHAs, MOPs created from scratch each time |
| No knowledge transfer | Expertise leaves when people leave |
| Competitor tools inadequate | Generic project management, not industry-specific |

---

## The Solution

**APEX Platform** — Apparatus-centric resource model where everything connects to equipment types:

```
                            ┌─────────────────┐
                            │   APPARATUS     │
                            │  (The Anchor)   │
                            └────────┬────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
│   OPERATIONS    │        │     SAFETY      │        │    LEARNING     │
├─────────────────┤        ├─────────────────┤        ├─────────────────┤
│ • Test Procedures│        │ • SOPs          │        │ • Study Material│
│ • NETA Standards │        │ • AHAs          │        │ • KSA Mapping   │
│ • Test Forms     │        │ • NFPA 70E PPE  │        │ • IEEE/Industry │
│ • Datasheets     │        │ • MOPs          │        │ • Practice Q&A  │
└─────────────────┘        └─────────────────┘        └─────────────────┘
```

**Result:** When a technician is assigned equipment, everything relevant surfaces automatically. No hunting. No tribal knowledge dependency.

---

## Value Proposition

### For Field Technicians
- Right resources at the right time
- Safety documentation pre-populated
- Professional output regardless of experience level
- Study materials linked to actual work

### For Project Managers
- Real-time visibility across all projects
- Automated progress tracking
- Resource allocation intelligence
- Revenue recognition automation

### For Company Leadership
- Scalable operations (not "fits in your head")
- Reduced liability through consistent safety compliance
- Knowledge retention independent of personnel
- Competitive differentiation

---

## Platform Components

### 1. Operations Core (Supabase)
**Status:** Foundation complete, 37+ tables deployed

- Project/Scope/Task/Apparatus hierarchy
- Financial tracking and revenue recognition
- Resource allocation and scheduling
- Dashboard views and KPIs

### 2. Safety Documentation System
**Status:** Schema complete January 2026

| Document | Purpose | Database |
|----------|---------|----------|
| SOP | Library procedure (how to do X safely) | `sops_v2`, `sop_task_steps` |
| AHA | Project execution (our plan for this job) | `ahas`, `aha_task_steps`, `aha_crew_signoffs` |
| MOP | Event coordination (this specific evolution) | Schema defined, templates complete |

**NFPA 70E Integration:** Auto-calculation of approach boundaries, PPE requirements from voltage input.

### 3. NETA Standards Library
**Status:** ATS-2025 loaded, expansion planned

- 33 procedures imported
- 77+ test items linked
- Apparatus type mapping in progress

### 4. Learning & Development System
**Status:** Content extracted, integration planned

- 47,000+ lines of study material
- 483 KSAs mapped (NETA ETT Levels II/III/IV)
- IEEE, Paul Gill, NFPA 70E extractions
- Apparatus-to-KSA linking enables contextual learning

### 5. TCC v5 (Time-Current Curves)
**Status:** Standalone, future integration

- 2.4 million rows of device characteristics
- Protection coordination calculations
- Links relay/breaker settings to apparatus

---

## Differentiation

### vs. Generic Project Management (Monday, Asana, etc.)
- Industry-specific data model
- NETA standards built-in
- Safety documentation workflow
- Apparatus-centric architecture

### vs. Competitors' Internal Tools
- Modern tech stack (not legacy Access/Excel)
- Mobile-first field interface
- Integrated learning system
- Auto-calculated safety compliance

### vs. Building In-House
- 4 years of domain expertise embedded
- 47,000 lines of curated content
- Production-ready schemas
- Proven template designs

---

## Implementation Roadmap

### Phase 1: Foundation (Complete)
- [x] Supabase schema design
- [x] Core tables deployed
- [x] Test data validated
- [x] UI specifications complete

### Phase 2: Safety System (January 2026)
- [x] SOP/AHA schema deployed
- [x] NFPA 70E lookups populated
- [x] MOP templates complete
- [ ] Web form development
- [ ] PDF export

### Phase 3: Operations Dashboard (Q1 2026)
- [ ] Deploy operations views
- [ ] Real project data import
- [ ] Resource allocation UI
- [ ] Mobile field interface

### Phase 4: Resource Linking (Q2 2026)
- [ ] Apparatus type mapping
- [ ] Study material integration
- [ ] Contextual help system
- [ ] KSA gap analysis

### Phase 5: Production (Q3 2026)
- [ ] Authentication & security
- [ ] Production deployment
- [ ] User training
- [ ] Phased rollout

---

## Business Model

### Phase 1: Internal Tool
- Deploy within current regional management
- Prove value through operational metrics
- Build user adoption and feedback loop

### Phase 2: Expansion
- Document efficiency gains
- Quantify safety compliance improvements
- Demonstrate scalability

### Phase 3: Transaction
- Position for PE turnover (~2028)
- Present to ownership as acquisition opportunity
- Intellectual property secured under LLC

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Time to deploy | Phased approach, MVP focus |
| User adoption | Modern UX, training materials |
| Data migration | Clean slate option, parallel running |
| IP protection | LLC structure, documented ownership |
| Technical debt | Modern stack, clean architecture |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to find resources | -80% | Clicks to resource from apparatus |
| AHA creation time | -60% | Minutes per document |
| Safety compliance | 100% | Required fields enforced |
| Onboarding time | -50% | New tech productivity |
| Project visibility | Real-time | Dashboard accuracy |

---

## Appendix: Related Projects

### Primary Workspace
- **APEX Platform:** `C:\APEX Platform\`
- **NETA-Forms:** `C:\APEX Platform\source-domains\neta-forms\`

### Supporting Projects
- **ETT Study Material:** `C:\APEX Platform\source-domains\neta-ett-study-material\`
- **TCC v5:** `C:\APEX Platform\source-domains\tcc_v5_backend\`

### Reference Materials
- **AES SWPRO Library:** 30+ elite safety procedures
- **NFPA 70E 2024:** Safety standard
- **NETA ATS/MTS/ECS/ETT:** Testing standards

---

*This document represents strategic business planning and intellectual property of Jason Swenson / APEX Platform LLC.*
