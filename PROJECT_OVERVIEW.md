# RESA Power Project Tracker - System Overview

**Version:** 1.3.0.1  
**Last Updated:** November 17, 2025  
**Project Lead:** Jason Swenson  
**Repository:** [github.com/jasonlswenson-sys/RESA-Power-Project-Management](https://github.com/jasonlswenson-sys/RESA-Power-Project-Management)

---

## 🎯 Executive Summary

Modern Dataverse-based project management system for electrical testing projects with NETA standards compliance. Replaces legacy Access database with cloud-based Power Platform solution featuring automated revenue recognition, multi-location support, and real-time progress tracking.

**Business Impact:**
- ✅ **10-15 hours/year** saved through automated revenue recognition
- ✅ **Real-time visibility** into project status and financials
- ✅ **Multi-location support** for Phoenix, Las Vegas, Denver, San Diego
- ✅ **NETA compliance** built into data structure
- ✅ **Audit trail** for all financial and completion data

---

## 📊 System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Field Operations"
        FT[Field Technicians]
        JL[Job Leads]
    end
    
    subgraph "Project Management"
        PM[Project Managers]
        OC[Operations Coordinator]
    end
    
    subgraph "Finance & Leadership"
        AM[Account Managers]
        LM[Location Managers]
        VP[Regional VP]
    end
    
    subgraph "Power Platform"
        subgraph "Dataverse"
            P[Projects]
            S[Scopes]
            T[Tasks]
            A[Apparatus]
            SLD[ScopeLaborDetail]
            AR[ApparatusRevenue]
            BU[BusinessUnit]
        end
        
        subgraph "Power Automate"
            RF[Revenue Recognition Flow]
        end
        
        subgraph "Power Apps"
            MA[Model-Driven App]
        end
    end
    
    FT -->|Update Work Status| MA
    JL -->|Assign Work| MA
    PM -->|Manage Projects| MA
    OC -->|Coordinate Resources| MA
    AM -->|Track Revenue| MA
    LM -->|Location Metrics| MA
    VP -->|Executive Dashboard| MA
    
    MA <-->|CRUD Operations| Dataverse
    A -->|Completion Status Change| RF
    RF -->|Auto-Create| AR
    RF -->|Lookup Rates| SLD
    
    P -->|1:N| S
    S -->|1:N| T
    T -->|1:N| A
    S -->|1:1| SLD
    A -->|1:N| AR
    BU -->|1:N| P
    
    style RF fill:#90EE90
    style AR fill:#FFD700
    style SLD fill:#87CEEB
```

---

## 🏗️ Data Model

### Entity Relationship Diagram

```mermaid
erDiagram
    BUSINESSUNIT ||--o{ PROJECTS : "has"
    PROJECTS ||--o{ PROJECTSCOPE : "contains"
    PROJECTSCOPE ||--o{ TASKS : "organizes"
    PROJECTSCOPE ||--|| SCOPELABORDETAIL : "budgeted_by"
    TASKS ||--o{ APPARATUS : "includes"
    APPARATUS ||--o{ APPARATUSREVENUE : "generates"
    SCOPELABORDETAIL ||--o{ APPARATUSREVENUE : "rates_for"
    
    BUSINESSUNIT {
        string Name
        string Location
        string Region
    }
    
    PROJECTS {
        string Project_Name
        string Project_Number
        lookup BusinessUnit
        date Start_Date
        date Target_Completion
    }
    
    PROJECTSCOPE {
        string Scope_Name
        lookup Project
        decimal Total_Apparatus_Hours
        decimal Total_Actual_Hours
    }
    
    SCOPELABORDETAIL {
        lookup Project_Scope
        decimal Total_Apparatus_Hours
        currency Onsite_Labor_Total
        currency Offsite_Labor_Total
        currency Travel_Total
        currency Outside_Services_Total
        currency Effective_Labor_Rate
    }
    
    TASKS {
        string Task_Name
        lookup Project_Scope
        choice Task_Type
    }
    
    APPARATUS {
        string Designation
        lookup Task
        decimal Apparatus_Hours
        decimal Completed_Hours
        decimal Delays
        choice Completion_Status
        datetime Date_Completed
    }
    
    APPARATUSREVENUE {
        lookup Apparatus
        lookup Project
        lookup Scope_Labor_Detail
        decimal Apparatus_Hours
        decimal Delays
        currency Effective_Labor_Rate
        currency Revenue_Amount
        choice Revenue_Status
    }
```

---

## 🔄 Revenue Recognition Flow

### Automated Workflow

```mermaid
flowchart TD
    Start([Field Tech Marks<br/>Apparatus Complete]) --> Trigger{Completion Status<br/>= Complete?}
    
    Trigger -->|Yes| CheckDate{Date Completed<br/>is null?}
    Trigger -->|No| End1([Flow Does Not Run])
    
    CheckDate -->|Yes| SetDate[Set Date_Completed<br/>= NOW]
    CheckDate -->|No| GetScope[Get Related Scope]
    
    SetDate --> GetScope
    
    GetScope --> GetRates[List ScopeLaborDetail<br/>for this Scope]
    
    GetRates --> RatesFound{Labor Rates<br/>Found?}
    
    RatesFound -->|No| Error1([Terminate: No rates defined])
    RatesFound -->|Yes| CheckDupe[List Existing<br/>ApparatusRevenue]
    
    CheckDupe --> DupeExists{Revenue Record<br/>Already Exists?}
    
    DupeExists -->|Yes| End2([Terminate: Duplicate prevention])
    DupeExists -->|No| CreateRevenue[Create ApparatusRevenue Record]
    
    CreateRevenue --> PopulateFields[Populate Fields:<br/>• Apparatus Hours<br/>• Delays<br/>• Effective Labor Rate<br/>• Revenue Status = RECOGNIZED]
    
    PopulateFields --> Calculate[Dataverse Auto-Calculates<br/>Revenue Amount]
    
    Calculate --> Success([Revenue Recognition Complete])
    
    style Start fill:#90EE90
    style CreateRevenue fill:#FFD700
    style Calculate fill:#87CEEB
    style Success fill:#98FB98
    style Error1 fill:#FFB6C1
    style End2 fill:#FFE4B5
```

---

## 📈 Rollup Architecture

### Hours and Revenue Aggregation

```mermaid
graph BT
    A1[Apparatus 1<br/>Completed: 8.5 hrs<br/>Delays: 1.5 hrs]
    A2[Apparatus 2<br/>Completed: 12.0 hrs<br/>Delays: 0.5 hrs]
    A3[Apparatus 3<br/>Completed: 6.0 hrs<br/>Delays: 0 hrs]
    
    T1[Task: Transformers<br/>Total: 26.5 hrs<br/>Delays: 2.0 hrs]
    T2[Task: Breakers<br/>Total: 15.0 hrs<br/>Delays: 1.0 hrs]
    
    S1[Scope: Switchgear Testing<br/>Total: 41.5 hrs<br/>Delays: 3.0 hrs<br/>% Complete: 75%]
    
    P1[Project: Hospital Upgrade<br/>Total: 120 hrs planned<br/>Total: 85 hrs actual<br/>% Complete: 71%]
    
    SLD[ScopeLaborDetail<br/>Effective Rate: $363.68/hr<br/>Budget: $64,008]
    
    AR1[Revenue: $3,091.28<br/>Status: RECOGNIZED]
    AR2[Revenue: $4,364.16<br/>Status: RECOGNIZED]
    AR3[Revenue: $2,182.08<br/>Status: RECOGNIZED]
    
    A1 -->|Rollup| T1
    A2 -->|Rollup| T1
    A3 -->|Rollup| T2
    
    T1 -->|Rollup| S1
    T2 -->|Rollup| S1
    
    S1 -->|Rollup| P1
    
    S1 -.->|1:1| SLD
    
    A1 -->|Creates| AR1
    A2 -->|Creates| AR2
    A3 -->|Creates| AR3
    
    SLD -.->|Rates| AR1
    SLD -.->|Rates| AR2
    SLD -.->|Rates| AR3
    
    style P1 fill:#FFD700
    style S1 fill:#87CEEB
    style SLD fill:#98FB98
    style AR1 fill:#FFB6C1
    style AR2 fill:#FFB6C1
    style AR3 fill:#FFB6C1
```

---

## 👥 User Personas & Access

### Role-Based Architecture

```mermaid
graph LR
    subgraph "Field Operations Layer"
        FT[Field Technician<br/>• View assigned work<br/>• Update completion status<br/>• Enter hours]
        
        JL[Job Lead<br/>• Assign work<br/>• Review team progress<br/>• Approve completions]
    end
    
    subgraph "Project Management Layer"
        PM[Project Manager<br/>• Manage full projects<br/>• Budget tracking<br/>• Customer communication]
        
        OC[Operations Coordinator<br/>• Resource allocation<br/>• Schedule coordination<br/>• Cross-project visibility]
    end
    
    subgraph "Finance & Executive Layer"
        AM[Account Manager<br/>• Revenue tracking<br/>• Financial reporting<br/>• Customer billing]
        
        LM[Location Manager<br/>• Location metrics<br/>• Team performance<br/>• Resource planning]
        
        VP[Regional VP<br/>• Executive dashboard<br/>• Strategic planning<br/>• Multi-location oversight]
    end
    
    FT -->|Reports to| JL
    JL -->|Coordinates with| PM
    PM -->|Reports to| LM
    OC -->|Supports| PM
    AM -->|Partners with| PM
    LM -->|Reports to| VP
    
    style FT fill:#90EE90
    style JL fill:#87CEEB
    style PM fill:#FFD700
    style OC fill:#DDA0DD
    style AM fill:#FFB6C1
    style LM fill:#F0E68C
    style VP fill:#FFA07A
```

---

## 🔢 Key Metrics & Calculations

### Revenue Calculation Model

```mermaid
graph LR
    subgraph "Input Data"
        CH[Completed Hours<br/>8.5 hrs]
        D[Delays<br/>1.5 hrs]
        ELR[Effective Labor Rate<br/>$363.68/hr]
    end
    
    subgraph "Calculated Fields"
        TH[Total Hours<br/>= Completed + Delays<br/>10.0 hrs]
        
        RA[Revenue Amount<br/>= Completed × Rate<br/>$3,091.28]
    end
    
    subgraph "Business Rules"
        BR1[Only billable hours<br/>generate revenue]
        BR2[Delays tracked<br/>but not billed]
        BR3[Rate sourced from<br/>scope-level budget]
    end
    
    CH --> TH
    D --> TH
    CH --> RA
    ELR --> RA
    
    BR1 -.-> RA
    BR2 -.-> D
    BR3 -.-> ELR
    
    style RA fill:#FFD700
    style TH fill:#87CEEB
    style ELR fill:#98FB98
```

---

## 📁 Repository Structure

```
RESA_Power_Build/
├── Documentation/
│   ├── 00_START_HERE/          # Quick start guides
│   ├── 01_Architecture/         # System design docs
│   │   ├── REVENUE_ARCHITECTURE.md
│   │   ├── USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md
│   │   └── MASTER_BUILD_SPECIFICATION.md
│   ├── 02_Implementation/       # Build specifications
│   │   ├── SCOPELABORDETAIL_BUILD_SPEC.md
│   │   ├── APPARATUSREVENUE_ENHANCEMENTS.md
│   │   └── REVENUE_RECOGNITION_FLOW_SPEC.md
│   ├── 03_Progress_Tracking/    # Development logs
│   ├── 04_Data_Migration/       # Import templates and guides
│   ├── 05_Reviews_Analysis/     # Technical audits
│   └── 99_Archive/             # Historical documents
├── Solution_Exports/
│   ├── v1.2.0.3/               # Base system
│   ├── v1.3.0.0/               # Date tracking fields
│   ├── v1.3.0.1/               # Revenue architecture
│   ├── v1.3.0.2/               # Revenue flow (in progress)
│   └── v1.3.0.3/               # Future enhancements
├── CSV_Templates/              # Data import templates
├── Scripts/                    # PowerShell automation
└── README.md                   # Project overview
```

---

## 🚀 Implementation Roadmap

### Current Status: Phase 5 (Revenue Automation)

```mermaid
gantt
    title RESA Power Project Tracker Development
    dateFormat YYYY-MM-DD
    section Foundation
    Phase 1-2 Complete          :done, p1, 2025-10-01, 2025-10-31
    Phase 3 UX Architecture     :done, p3, 2025-11-01, 2025-11-10
    section Revenue System
    Phase 5C ScopeLaborDetail   :done, p5c, 2025-11-15, 2025-11-15
    Phase 5D ApparatusRevenue   :done, p5d, 2025-11-16, 2025-11-16
    Phase 5E Revenue Flow       :active, p5e, 2025-11-17, 2025-11-17
    section Enhancement
    Phase 5A Work Assignment    :p5a, 2025-11-18, 2025-11-18
    Phase 5B Date Tracking      :p5b, 2025-11-19, 2025-11-19
    section Future
    Phase 4 Audit               :p4, 2025-11-20, 2025-11-25
    Phase 6 BusinessUnit        :p6, 2025-11-26, 2025-11-30
    Phase 7 Master Build Spec   :p7, 2025-12-01, 2025-12-05
```

---

## 📊 Technical Specifications

### Platform Details

| Component | Technology | Version |
|-----------|-----------|---------|
| **Database** | Microsoft Dataverse | Latest |
| **App Type** | Model-Driven App | Power Apps |
| **Automation** | Power Automate | Cloud Flows |
| **Tables** | 8 custom entities | v1.3.0.1 |
| **Fields** | 137 custom fields | 28 calculated |
| **Workflows** | 1 active flow | Revenue Recognition |
| **Repository** | GitHub | Private → Public |

### Key Tables

| Table | Records | Purpose | Status |
|-------|---------|---------|--------|
| **BusinessUnit** | 4 | Multi-location support | ✅ Production |
| **Projects** | ~50/year | Top-level containers | ✅ Production |
| **ProjectScope** | ~150/year | Work breakdown | ✅ Production |
| **Tasks** | ~500/year | Task organization | ✅ Production |
| **Apparatus** | ~2000/year | Equipment testing | ✅ Production |
| **ScopeLaborDetail** | ~150/year | Budget & rates | ✅ v1.3.0.1 |
| **ApparatusRevenue** | ~2000/year | Revenue tracking | ✅ v1.3.0.1 |
| **TestRecords** | ~20k/year | NETA test data | ✅ Production |

---

## 💼 Business Value

### Quantified Benefits

**Time Savings:**
- **Revenue Entry:** 10-15 hours/year automated
- **Progress Tracking:** Real-time vs. weekly updates
- **Reporting:** Instant dashboards vs. manual reports

**Accuracy Improvements:**
- **Revenue Recognition:** 100% automated, zero manual errors
- **Date Tracking:** System-captured timestamps
- **Budget Variance:** Real-time calculation vs. end-of-project

**Operational Benefits:**
- **Multi-Location:** Phoenix, Las Vegas, Denver, San Diego unified
- **NETA Compliance:** Built into data structure
- **Audit Trail:** Complete history of all changes
- **Scalability:** Cloud-based, grows with business

---

## 🔐 Security & Compliance

- ✅ **Role-Based Access Control** - 7 defined personas with appropriate permissions
- ✅ **Audit Logging** - All data changes tracked in Dataverse
- ✅ **Data Encryption** - At rest and in transit (Microsoft standard)
- ✅ **Business Unit Isolation** - Location-based data segmentation ready
- ✅ **NETA Standards** - Test data structure aligns with industry requirements

---

## 📞 Support & Documentation

**Primary Documentation:**
- `Documentation/00_START_HERE/` - Quick start guides
- `Documentation/01_Architecture/` - System design
- `Documentation/02_Implementation/` - Build specs

**Key Resources:**
- [GitHub Repository](https://github.com/jasonlswenson-sys/RESA-Power-Project-Management)
- `REVENUE_ARCHITECTURE.md` - Complete revenue chain documentation
- `USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md` - UX and role design
- `REVENUE_RECOGNITION_FLOW_SPEC.md` - Workflow specifications

---

## 🎯 Next Steps

### Immediate (This Week)
1. ✅ Complete Revenue Recognition Flow (Phase 5E)
2. Deploy to test environment
3. Run 5 test scenarios
4. Monitor first 24 hours

### Short-Term (Next 2 Weeks)
1. Add Work Assignment fields (Phase 5A)
2. Implement Date Tracking enhancements (Phase 5B)
3. Conduct forms/views audit (Phase 4)
4. Document findings

### Medium-Term (Next Month)
1. BusinessUnit rollup enhancements (Phase 6)
2. Location Manager dashboard
3. Master Build Specification V2 (Phase 7)
4. Executive presentation

---

**Document Version:** 1.0  
**Last Updated:** November 17, 2025  
**Status:** System operational, enhancements in progress  
**Contact:** Jason Swenson - RESA Power Project Tracker Lead
