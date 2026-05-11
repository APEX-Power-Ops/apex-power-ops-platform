# APEX Platform - Project Status

> **Last Updated**: January 7, 2026  
> **Phase**: Safety Documentation Schema Complete, Operations Views Ready  
> **See Also**: `PROJECT_OVERVIEW.md` for system architecture, `STRATEGIC_VISION.md` for business roadmap

---

## 🎯 Executive Summary

APEX Platform is a comprehensive project management and field operations system for electrical testing companies. Built on Supabase (PostgreSQL), it integrates project management, NETA standards compliance, safety documentation, and technical resources into a unified platform.

**Core Philosophy**: Apparatus-centric resource model — everything links to equipment types, so field technicians automatically get relevant procedures, safety docs, and reference materials when assigned work.

| Milestone | Status | Date |
|-----------|--------|------|
| Supabase Schema Design | ✅ Complete | Dec 2025 |
| Database Deployment | ✅ Complete | Dec 2025 |
| NETA Procedures Import (ATS) | ✅ Complete | Dec 2025 |
| Operations Visibility Schema | ✅ Ready | Dec 2025 |
| UI Specification | ✅ Complete | Dec 2025 |
| **SOP/AHA Safety Schema** | ✅ Complete | Jan 7, 2026 |
| **NFPA 70E Lookup Tables** | ✅ Complete | Jan 7, 2026 |
| MOP Template System | 🔄 In Progress | NETA-Forms |
| Production Deployment | 🔜 Planned | Q1 2026 |

---

## 🔥 Latest Updates (January 7, 2026)

### SOP/AHA Safety Documentation Schema — DEPLOYED

Complete schema for NFPA 70E-compliant safety documentation:

| Table | Purpose | Records |
|-------|---------|---------|
| `sops_v2` | Standard Operating Procedures (Library) | Ready |
| `sop_task_steps` | Detailed procedure steps with hazards/controls | Ready |
| `ahas` | Activity Hazard Analysis (Project-specific) | Ready |
| `aha_task_steps` | Project execution steps (inherited from SOP) | Ready |
| `aha_crew_signoffs` | Daily crew acknowledgment tracking | Ready |
| `nfpa_70e_tables` | Lookup tables for auto-calculation | 7 tables |
| `sop_apparatus_types` | Links SOPs to equipment types | Ready |

### NFPA 70E Lookup Tables Populated

| Table Number | Content |
|--------------|---------|
| 130.4(E)(a) | AC Shock Approach Boundaries (14 voltage ranges) |
| 130.4(E)(b) | DC Shock Approach Boundaries (11 voltage ranges) |
| 130.7(C)(15)(a) | AC Arc-Flash PPE Categories by equipment |
| 130.7(C)(15)(b) | DC Arc-Flash PPE Categories |
| 130.5(G) | PPE Requirements by Category (1-4) + Glove Classes |
| 120.5 | ESWC 6-Step Process |
| RAC-Matrix | Risk Assessment Code Matrix with definitions |

**Key Capability**: System can now auto-calculate approach boundaries and PPE requirements from voltage input.

---

## 📊 Database Statistics (January 7, 2026)

### Table Summary

| Category | Tables | Key Tables |
|----------|--------|------------|
| Core | 5 | clients, projects, scopes, tasks, apparatus |
| Hierarchy | 4 | locations, sites, apparatus_types |
| Financial | 4 | apparatus_revenue, scope_labor_details |
| Resources | 3 | neta_procedures, neta_test_items, apparatus_type_resources |
| **Safety** | 7 | sops_v2, sop_task_steps, ahas, aha_task_steps, aha_crew_signoffs, nfpa_70e_tables, sop_apparatus_types |
| PSS Portal | 6 | pss_documents, pss_document_templates |
| Reference | 2 | employees, estimators |
| **Total** | **37+** | |

### Record Counts

| Table | Records | Notes |
|-------|---------|-------|
| nfpa_70e_tables | 7 | NFPA 70E 2024 lookup data |
| neta_procedures | 33 | ATS-2025 sections |
| neta_test_items | 77+ | Test item details |
| apparatus | 47 | LASNAP16 test data |
| apparatus_types | 15 | Equipment categories |

---

## 🗺️ System Architecture

### Document Hierarchy

```
SOP (Standard Operating Procedure) - Library
├── The approved way to perform [task]
├── Permanent, version-controlled
├── Generic steps, hazard types, control framework
└── Referenced by ↓

AHA (Activity Hazard Analysis) - Project Execution
├── How we're executing [SOP] on THIS job
├── Project duration, daily sign-off
├── Actual site values (voltage, boundaries, PPE)
├── Task steps inherited from SOP but editable
└── Referenced by ↓

MOP (Method of Procedure) - Coordination Wrapper
└── Single evolution/event coordination
```

### Apparatus-Centric Resource Model

```
APPARATUS TYPE (e.g., Protective Relay)
    │
    ├── Testing Procedures
    │   ├── NETA ATS 7.9 (Acceptance)
    │   └── NETA MTS 7.9 (Maintenance)
    │
    ├── Safety Procedures
    │   ├── SOP-009 Relay Removal
    │   └── NFPA 70E PPE Requirements
    │
    └── Reference/Learning
        ├── Paul Gill Ch9
        ├── IEEE C37.90
        └── ETT KSAs (II.D.4, III.D.3)
```

---

## 📋 Phase Breakdown

### Phase 1: Foundation ✅ Complete
- Schema design (37+ tables)
- ENUM types (38+)
- Trigger functions (12+)
- Test data (LASNAP16)
- Web app connection

### Phase 1.6: Resource Linking 🔄 In Progress
- [x] NETA ATS procedures imported
- [x] NETA test items loaded
- [x] SOP/AHA schema deployed
- [x] NFPA 70E lookup tables populated
- [ ] MOP schema integration
- [ ] Type-to-resource mapping
- [ ] Resource lookup UI

### Phase 1.7: Safety Documentation 🔄 In Progress
- [x] SOP library structure
- [x] AHA execution structure
- [x] Crew signoff tracking
- [ ] SOP content population
- [ ] AHA form UI
- [ ] PDF export

### Phase 2: Auth & PSS Portal 📋 Planned
- Supabase Auth setup
- RLS policies
- PSS Portal UI
- Document management

### Phase 3: Production 🔜 Planned
- Production deployment
- Real data migration
- User training

---

## 🔗 Related Projects

### NETA-Forms (C:\APEX Platform\source-domains\neta-forms)
HTML/CSS templates for MOP, AHA, SOP documents. Visual design work feeds into APEX web form generation.

### ETT Study Material (C:\APEX Platform\source-domains\neta-ett-study-material)
47,000+ lines of extracted content from NETA standards, IEEE, Paul Gill, NFPA 70E. Tagged with KSAs for apparatus-centric resource linking.

### TCC v5 Backend (C:\APEX Platform\source-domains\tcc_v5_backend)
Time-Current Curve calculator with 2.4M rows of device characteristics. Future integration for protection coordination data.

---

## 🔧 Technical Reference

### Supabase Connection
```
Project:     resa-power-db (APEX Platform)
Ref:         fxoyniqnrlkxfligbxmg
API URL:     https://fxoyniqnrlkxfligbxmg.supabase.co
Environment: Development
```

### Key Directories
| Purpose | Path |
|---------|------|
| Schema Migrations | `Supabase/migrations/` |
| UI Specifications (historical parent-root context) | `README.md` |
| Session Logs | `.claude/` |
| Safety Schema | Migration 001_sop_aha_schema, 002_nfpa_70e_lookup_data |

---

## 🏷️ Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-05 | 1.0.0 | Initial Supabase deployment |
| 2025-12-11 | 1.3.0 | NETA import, UI specification |
| **2026-01-07** | **1.4.0** | SOP/AHA schema, NFPA 70E lookups |

---

*Document Version: 1.4.0 | Last Updated: January 7, 2026*
