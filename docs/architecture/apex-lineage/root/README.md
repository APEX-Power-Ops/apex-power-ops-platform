# RESA Power - Project Management Platform

> Strategic redesign note: future-state platform authority entry now starts in `apex-power-ops-platform/docs/authority/README.md`.
> Use that repo-owned index first, then consult the linked inherited blueprint documents when making repo-topology, schema, multi-agent, or platform-boundary decisions.

> **Modern PostgreSQL-based project tracking for electrical testing operations**  
> Migrated from Microsoft Dataverse to Supabase in December 2025

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](./PROJECT_STATUS.md)
[![Platform](https://img.shields.io/badge/platform-Supabase-green.svg)](https://supabase.com)
[![Framework](https://img.shields.io/badge/framework-Next.js%2016-black.svg)](https://nextjs.org)
[![License](https://img.shields.io/badge/license-Private-red.svg)]()

---

## 🎯 Overview

Full-stack project management system for RESA Power's electrical field testing operations. Tracks apparatus-level work (switchgear, transformers, breakers) through the complete project lifecycle with automated revenue recognition, NETA standards compliance, and Power System Studies (PSS) portal.

```mermaid
graph LR
    subgraph "RESA Power Platform"
        A[📱 Next.js App] --> B[🔌 Supabase API]
        B --> C[(PostgreSQL)]
        C --> D[⚡ Triggers]
        D --> E[📊 Views]
    end
    
    style A fill:#000,color:#fff
    style B fill:#3ecf8e,color:#fff
    style C fill:#336791,color:#fff
```

**Key Capabilities:**
- 🏗️ **Project Hierarchy**: Projects → Scopes → Tasks → Apparatus
- 💰 **Revenue Recognition**: Automatic calculation on apparatus completion
- 📋 **NETA Compliance**: 33+ test procedures with checklists
- ⚡ **PSS Portal**: Power System Studies tracking with document management
- 👥 **Multi-Role Access**: Executive, PM, Estimator, Field Tech, Admin views
- 🔄 **Real-Time Updates**: Supabase subscriptions for live dashboards

---

## 📊 System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[🖥️ Next.js 16 Web App<br/>React 19 + shadcn/ui]
        MOBILE[📱 Mobile PWA<br/>Future]
    end
    
    subgraph "Supabase Platform"
        API[REST API]
        RT[Real-time<br/>Subscriptions]
        AUTH[Auth<br/>Planned]
        
        subgraph "PostgreSQL Database"
            TABLES[30 Tables]
            ENUMS[38+ ENUMs]
            TRIGGERS[12+ Triggers]
            VIEWS[15+ Views]
        end
    end
    
    WEB --> API
    WEB --> RT
    MOBILE --> API
    API --> TABLES
    TRIGGERS --> TABLES
    
    style WEB fill:#000,color:#fff
    style TABLES fill:#336791,color:#fff
    style TRIGGERS fill:#22c55e,color:#fff
```

### Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Database** | PostgreSQL via Supabase | 17.x |
| **Backend** | Supabase REST + Realtime | Latest |
| **Frontend** | Next.js (App Router) | 16.0.5 |
| **UI Components** | shadcn/ui + Radix | Latest |
| **Styling** | Tailwind CSS | 4.x |
| **Language** | TypeScript | 5.x |

---

## 🗄️ Database Schema

### Table Summary (30 Tables)

| Category | Tables | Description |
|----------|--------|-------------|
| **Organization** | 5 | Locations, Clients, Sites, Employees, Estimators |
| **Project Hierarchy** | 4 | Projects, Scopes, Tasks, Apparatus |
| **Equipment** | 3 | Apparatus Types, Equipment, Assignments |
| **Financial** | 4 | Revenue, Labor Details, Financial Summaries |
| **Resource Mgmt** | 1 | Resource Assignments |
| **PSS Portal** | 6 | Studies, Documents, RFIs, Engineers, Templates, Activity Log |
| **NETA/Resources** | 7 | Procedures, Test Items, Templates, SOPs, Safety, Datasheets |

### Core Data Model

```mermaid
erDiagram
    PROJECTS ||--o{ SCOPES : contains
    SCOPES ||--o{ TASKS : organizes
    SCOPES ||--o{ APPARATUS : includes
    APPARATUS }o--|| APPARATUS_TYPES : classified_as
    APPARATUS ||--o{ APPARATUS_REVENUE : generates
    
    APPARATUS_TYPES ||--o{ NETA_PROCEDURES : references
    NETA_PROCEDURES ||--o{ NETA_TEST_ITEMS : contains
    
    PROJECTS ||--o{ PSS_STUDIES : includes
    PSS_STUDIES ||--o{ PSS_DOCUMENTS : produces
```

### Automated Workflows (Triggers)

```mermaid
flowchart LR
    A[✅ Apparatus Complete] --> B[Create Revenue Record]
    A --> C[Update Task Count]
    C --> D[Update Scope Count]
    D --> E[Update Project Count]
    B --> F[Recalculate Scope Financials]
    F --> G[Recalculate Project Financials]
    
    style A fill:#22c55e,color:#fff
    style G fill:#3b82f6,color:#fff
```

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn
- Supabase account (or use existing project)

### 1. Clone Repository

```bash
git clone https://github.com/jasonlswenson-sys/RESA-Power-Project-Management.git
cd RESA-Power-Project-Management
```

### 2. Database Setup (Supabase)

```bash
# Option A: Use existing project
# Project ref: fxoyniqnrlkxfligbxmg

# Option B: Deploy to new project
# Run in Supabase SQL Editor:
cat Supabase/DEPLOY_ALL.sql | supabase db push
```

### 3. Web App Setup

```bash
cd ../../apps/operations-web

# Install dependencies
pnpm install

# Run the governed browser app
pnpm dev

# Start development server
npm run dev
```

### 4. Access Application

Open [http://localhost:3000](http://localhost:3000)

---

## 📁 Repository Structure

```
RESA_Power_Build/
├── 📄 README.md                    # This file
├── 📄 PROJECT_OVERVIEW.md          # Architecture + diagrams
├── 📄 PROJECT_STATUS.md            # Current status + roadmap
│
├── 📂 Supabase/
│   ├── schema/                     # SQL schema files (00-07)
│   │   ├── 00_enums.sql           # 38+ ENUM types
│   │   ├── 01_tables.sql          # Core tables
│   │   ├── 02_relationships.sql   # Foreign keys
│   │   ├── 03_triggers.sql        # 12+ trigger functions
│   │   ├── 04_views.sql           # Dashboard views
│   │   └── 05_indexes.sql         # Performance indexes
│   ├── data/
│   │   ├── 10_seed_data.sql       # Reference data
│   │   ├── 11_test_data.sql       # LASNAP16 test project
│   │   └── 20_neta_procedures.sql # NETA standards
│   ├── scripts/
│   │   └── NETA_IMPORT_HANDOFF.md # Import instructions
│   ├── lib/supabase.ts            # Client library
│   ├── SCHEMA_REFERENCE.md        # Quick reference
│   └── DEPLOY_ALL.sql             # Single-file deployment
│
├── 📂 .claude/
│   ├── STATE.md                   # Session state
│   ├── COORDINATION.md            # Task allocation
│   └── OPEN_DECISIONS.md          # Architecture decisions
│
├── 📂 Documentation/
│   ├── 07_Application_Specs/      # ⭐ UI Specifications
│   │   ├── UI_SPECIFICATION_GUIDE.md    # Design system (927 lines)
│   │   ├── ROLE_DEMO_PROMPT.md          # v0.dev prototype (1193 lines)
│   │   ├── REPORT_GENERATOR_DEMO_PROMPT.md
│   │   └── FIELD_TECH_APPLICATION_SPEC.md
│   └── [other documentation folders]
│
├── 📂 Reference_Files/
│   └── NETA/Extracted/            # NETA JSON source files
│       ├── ANSI_NETA_ATS-2025_Final_v2.json
│       ├── ANSI_NETA_MTS-2023_FINAL_v2.json
│       ├── ANSI_NETA_ECS-2024_v2.json
│       └── ANSI_NETA_ETT-2022_FINAL_v2.json
│
└── 📂 CSV_Templates/              # Import templates
```

---

## 🎨 UI Features

### Role-Based Dashboards

```mermaid
mindmap
  root((RESA Power))
    Executive
      Revenue KPIs
      Project Pipeline
      Multi-location
    Project Manager
      Active Projects
      Budget vs Actual
      Resource Allocation
    Estimator
      Quote Pipeline
      Win Rate
      Historical Data
    Field Technician
      My Assignments
      NETA Procedures
      Quick Entry
    Admin
      User Management
      System Config
      Reports
```

### Feature Highlights

| Feature | Status | Description |
|---------|--------|-------------|
| Project Dashboard | ✅ Ready | Overview with KPIs and project list |
| Apparatus Tracking | ✅ Ready | Status, hours, completion workflow |
| Revenue Recognition | ✅ Ready | Auto-calculation via triggers |
| NETA Procedures | ⚠️ Loading | 33 ATS procedures imported |
| PSS Portal | 📋 Schema Ready | Studies, documents, RFIs |
| Report Generator | 📋 Specified | Auto-generate PDF reports |
| Mobile Field App | 🔜 Planned | PWA for field technicians |

### UI Specification Documents

Historical parent-root location: preserved from `Documentation/07_Application_Specs/` and summarized here.

| Document | Lines | Purpose |
|----------|-------|---------|
| `UI_SPECIFICATION_GUIDE.md` | 927 | Complete design system |
| `ROLE_DEMO_PROMPT.md` | 1193 | v0.dev interactive prototype |
| `REPORT_GENERATOR_DEMO_PROMPT.md` | ~300 | Report flow specification |
| `FIELD_TECH_APPLICATION_SPEC.md` | ~400 | Mobile app requirements |

---

## 📈 Current Status

### Database Statistics

| Metric | Count |
|--------|-------|
| **Tables** | 30 |
| **ENUM Types** | 38+ |
| **Triggers** | 12+ |
| **Views** | 15+ |
| **Indexes** | ~50 |
| **NETA Procedures** | 33 (ATS-2025) |
| **Test Items** | 77+ |

### Test Data (LASNAP16 Project)

| Table | Records |
|-------|---------|
| Apparatus | 47 |
| Tasks | 12 |
| Scopes | 4 |
| Employees | 5 |
| Apparatus Types | 15 |

### Implementation Progress

```mermaid
pie title Completion Status
    "Complete" : 75
    "In Progress" : 15
    "Planned" : 10
```

---

## 🗺️ Roadmap

```mermaid
gantt
    title Development Roadmap
    dateFormat YYYY-MM-DD
    
    section Phase 1 - Foundation
    Schema + Data           :done, 2025-12-01, 10d
    UI Specification        :done, 2025-12-11, 1d
    
    section Phase 1.6 - NETA
    Import Procedures       :active, 2025-12-11, 4d
    Type Mapping           :2025-12-15, 2d
    
    section Phase 1.7 - Field App
    Project Detail UI      :2025-12-17, 3d
    Apparatus Completion   :2025-12-20, 2d
    
    section Phase 2 - Auth
    Supabase Auth          :2025-12-28, 5d
    PSS Portal UI          :2026-01-06, 7d
```

---

## 🔐 Security

### Planned Authentication

1. **Phase 1** (Current): Development with anon key
2. **Phase 2**: Supabase Auth with email/password
3. **Phase 3**: Row-Level Security (RLS) policies
4. **Phase 4**: Optional Azure AD SSO

### Role-Based Access

| Role | Scope |
|------|-------|
| Field Tech | Own assignments only |
| Lead Tech | Team assignments |
| Project Manager | Full project access |
| Estimator | Quotes + project creation |
| Admin | Full system access |
| Executive | Read-only dashboards |

---

## 📚 Documentation

### Essential Reading

| Document | Description |
|----------|-------------|
| [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) | Architecture diagrams and data model |
| [PROJECT_STATUS.md](./PROJECT_STATUS.md) | Historical status snapshot with Mermaid charts |
| [../knowledge-domain/apex-resa/SCHEMA_REFERENCE.md](../knowledge-domain/apex-resa/SCHEMA_REFERENCE.md) | Repo-owned schema reference for the preserved lineage import set |
| [../../../../PROJECT_STATUS.md](../../../../PROJECT_STATUS.md) | Canonical current execution status superseding the old session-state surface |

### Technical Specifications

| Document | Location |
|----------|----------|
| UI Design System | Historical parent-root `Documentation/07_Application_Specs/` design system |
| Role Demo Prompt | Historical parent-root `Documentation/07_Application_Specs/` role-demo prompt |
| Report Workflow | [../automation-reporting/SUPABASE_REPORT_WORKFLOW.md](../automation-reporting/SUPABASE_REPORT_WORKFLOW.md) |

---

## 🤝 Development

### Claude AI Coordination

This project uses a dual-Claude workflow:
- **Desktop Claude**: Database schema, SQL, architecture decisions
- **VS Code Claude**: Application code, UI development

Session state is maintained in `.claude/STATE.md` and `.claude/COORDINATION.md`.

### Key Commands

```bash
# View current session state
cat .claude/STATE.md

# Deploy schema to Supabase
psql $DATABASE_URL < Supabase/DEPLOY_ALL.sql

# Run web app
pnpm --dir ../../ --filter @apex/operations-web dev
```

---

## 📞 References

| Resource | Link |
|----------|------|
| **Supabase Dashboard** | [supabase.com/dashboard](https://supabase.com/dashboard) |
| **Project API** | `https://fxoyniqnrlkxfligbxmg.supabase.co` |
| **Next.js Docs** | [nextjs.org/docs](https://nextjs.org/docs) |
| **shadcn/ui** | [ui.shadcn.com](https://ui.shadcn.com) |

---

## 🔄 Migration History

**December 2025**: Migrated from Microsoft Dataverse to Supabase

| Aspect | Before (Dataverse) | After (Supabase) |
|--------|-------------------|------------------|
| Tables | 8 | **30** |
| Triggers | 1 Power Automate | **12+ PostgreSQL** |
| UI | Power Apps | **Next.js 16** |
| Cost | Power Platform licensing | **$25/month** |
| Flexibility | Limited | **Full SQL access** |

---

## 📄 License

Private repository - RESA Power internal use only.

---

**Version:** 2.2.0  
**Last Updated:** December 11, 2025  
**Maintainer:** Jason Swenson
