# RESA Power System Architecture v2.0

## Core Principles

1. **Anyone can do it** - No technical knowledge required to operate
2. **Optimal first** - Design for ideal, accommodate reality later
3. **No process lock-in** - System adapts to workflow, not the reverse
4. **Reliability** - Works every time, no babysitting

---

## Complete System Overview

```mermaid
flowchart TB
    subgraph EXCEL["📊 EXCEL ESTIMATOR"]
        EST[Switch Estimator.xlsm]
        VBA[DataverseExport.bas v1.1]
        EST --> VBA
        VBA -->|JSON to Clipboard| JSON_OUT((JSON))
    end

    subgraph WEBAPP["🌐 NEXT.JS WEB APP"]
        direction TB
        PASTE[/Paste JSON/]
        CONFIG[Task Configuration]
        SUBMIT[Submit to Dataverse]
        PASTE --> CONFIG --> SUBMIT
    end

    subgraph DATAVERSE["☁️ DATAVERSE"]
        direction TB
        subgraph TABLES["Tables"]
            CLIENT[Client]
            SITE[Site]
            PROJECT[Project]
            SCOPE[Scope]
            TASK[Task]
            APPARATUS[Apparatus]
            LABOR[ScopeLaborDetail]
        end
        
        CLIENT --> SITE --> PROJECT --> SCOPE
        SCOPE --> TASK --> APPARATUS
        SCOPE --> LABOR
    end

    subgraph AUTOMATE["⚡ POWER AUTOMATE"]
        direction TB
        TRIGGER1[On ScopeLaborDetail Create/Update]
        CALC_RATES[Calculate All Rates]
        TRIGGER2[On Apparatus Status Change]
        CALC_REV[Calculate Revenue]
        ROLLUP[Rollup to Scope/Project]
        
        TRIGGER1 --> CALC_RATES
        TRIGGER2 --> CALC_REV --> ROLLUP
    end

    subgraph OUTPUTS["📈 OUTPUTS"]
        VIEWS[Web App Views]
        APPS[Model-Driven Apps]
        BI[Power BI Dashboards]
    end

    JSON_OUT --> PASTE
    SUBMIT -->|OData API| DATAVERSE
    DATAVERSE --> AUTOMATE
    AUTOMATE -->|Updates| DATAVERSE
    DATAVERSE --> OUTPUTS
```

---

## Data Model

```mermaid
erDiagram
    CLIENT ||--o{ SITE : has
    SITE ||--o{ PROJECT : contains
    PROJECT ||--o{ SCOPE : includes
    SCOPE ||--o{ TASK : defines
    SCOPE ||--|| SCOPE_LABOR : "has config"
    TASK ||--o{ APPARATUS : tests

    CLIENT {
        guid id PK
        string client_name
        string client_code
        string client_address
        string client_city
        string client_state
        string client_zip
        string client_phone
        string client_email
        boolean client_active
    }

    SITE {
        guid id PK
        lookup site_client FK
        string site_name
        string site_code
        string site_address
        string site_city
        string site_state
        string site_zip
        string site_contact_name
        string site_contact_phone
        boolean site_active
    }

    PROJECT {
        guid id PK
        lookup project_site FK
        lookup project_client FK
        string project_name
        string project_number
        string project_status
        datetime project_start_date
        datetime project_end_date
        currency project_contract_value
        string project_po_number
        boolean project_active
    }

    SCOPE {
        guid id PK
        lookup scope_project FK
        string scope_name
        string scope_number
        string scope_type
        string scope_status
        datetime scope_due_date
        currency scope_labor_total
        currency scope_revenue_total
        decimal scope_margin_percent
        boolean scope_active
    }

    TASK {
        guid id PK
        lookup task_scope FK
        string task_name
        string task_number
        string task_type
        string task_status
        int task_quantity
        currency task_unit_price
        currency task_total
        decimal task_labor_hours
        int task_sequence
        boolean task_active
    }

    APPARATUS {
        guid id PK
        lookup apparatus_task FK
        string apparatus_name
        string apparatus_type
        string apparatus_section
        int apparatus_quantity
        decimal apparatus_hours_per_unit
        decimal apparatus_total_hours
        string apparatus_manufacturer
        string apparatus_model
        string apparatus_serial
        string apparatus_location
        string apparatus_voltage
        string apparatus_status
        datetime apparatus_test_date
        string apparatus_result
        currency apparatus_revenue
        int apparatus_sequence
        int apparatus_row
        boolean apparatus_active
    }

    SCOPE_LABOR {
        guid id PK
        lookup scopelabor_scope FK
        decimal scopelabor_total_hours
        decimal scopelabor_multiplier
        currency scopelabor_quoted_amount
        currency scopelabor_onsite_total
        currency scopelabor_offsite_total
        currency scopelabor_travel_total
        currency scopelabor_outside_total
        currency scopelabor_onsite_rate
        currency scopelabor_offsite_rate
        currency scopelabor_travel_rate
        currency scopelabor_outside_rate
        currency scopelabor_sum_of_rates
        currency scopelabor_effective_rate
        currency scopelabor_not_adjusted
        currency scopelabor_adjusted
        string scopelabor_source
    }
```

---

## Revenue Calculation Flow

```mermaid
flowchart LR
    subgraph INPUT["📥 FROM ESTIMATOR"]
        ON[Onsite Total<br/>$45,936]
        OFF[Offsite Total<br/>$2,772]
        TR[Travel Total<br/>$5,175]
        OUT[Outside Svc Total<br/>$10,125]
        HRS[Total Hours<br/>176]
        MULT[Multiplier<br/>1.0]
    end

    subgraph CALC["⚡ POWER AUTOMATE CALCULATES"]
        direction TB
        R1[Onsite Rate<br/>$261.00/hr]
        R2[Offsite Rate<br/>$15.75/hr]
        R3[Travel Rate<br/>$29.40/hr]
        R4[Outside Rate<br/>$57.53/hr]
        SUM[Sum of Rates<br/>$363.68/hr]
        EFF[Effective Rate<br/>$363.68/hr]
    end

    subgraph STORED["💾 ALL STORED IN SCOPELABORDETAIL"]
        direction TB
        S_ON[onsite_total + onsite_rate]
        S_OFF[offsite_total + offsite_rate]
        S_TR[travel_total + travel_rate]
        S_OUT[outside_total + outside_rate]
        S_EFF[effective_rate ⭐]
    end

    ON --> R1
    OFF --> R2
    TR --> R3
    OUT --> R4
    HRS --> R1 & R2 & R3 & R4
    R1 & R2 & R3 & R4 --> SUM
    SUM --> EFF
    MULT --> EFF
    
    R1 --> S_ON
    R2 --> S_OFF
    R3 --> S_TR
    R4 --> S_OUT
    EFF --> S_EFF
```

---

## Apparatus Revenue Recognition

```mermaid
flowchart LR
    subgraph APPARATUS["📦 APPARATUS RECORD"]
        APP_HRS[Total Hours: 24]
        APP_STATUS[Status: Complete]
    end

    subgraph LOOKUP["🔍 LOOKUP"]
        SCOPE_RATE[Scope's Effective Rate<br/>$363.68/hr]
    end

    subgraph TRIGGER["⚡ ON STATUS = COMPLETE"]
        CALC[24 hrs × $363.68]
        REV[Revenue: $8,728.32]
    end

    subgraph ROLLUP["📊 ROLLUPS"]
        SCOPE_REV[Scope Revenue Total]
        PROJ_REV[Project Revenue Total]
    end

    APP_HRS --> CALC
    SCOPE_RATE --> CALC
    APP_STATUS -->|triggers| CALC
    CALC --> REV
    REV --> SCOPE_REV --> PROJ_REV
```

---

## Import Flow (User Experience)

```mermaid
sequenceDiagram
    actor User
    participant Excel as Excel Estimator
    participant Web as Web App
    participant DV as Dataverse
    participant PA as Power Automate

    User->>Excel: Open estimator, fill data
    User->>Excel: Click "Export to Dataverse"
    Excel-->>User: "JSON copied to clipboard!"
    
    User->>Web: Open localhost:3000/import
    User->>Web: Paste JSON
    Web->>Web: Parse & show task config
    User->>Web: Review, click Submit
    
    Web->>DV: POST /sites (create)
    Web->>DV: POST /projects (create)
    
    loop For each scope
        Web->>DV: POST /scopes
        Web->>DV: POST /scopelabordetails
        Note over PA: Trigger: Calculate rates
        PA->>DV: UPDATE scopelabordetail (calculated fields)
        
        loop For each task
            Web->>DV: POST /tasks
            loop For each apparatus
                Web->>DV: POST /apparatuses
            end
        end
    end
    
    Web-->>User: "Import complete! View project →"
```

---

## Power Automate Flows

### Flow 1: Calculate Scope Labor Rates
**Trigger:** When ScopeLaborDetail is created or updated

```
IF scopelabor_total_hours > 0 THEN
    onsite_rate = onsite_total / total_hours
    offsite_rate = offsite_total / total_hours
    travel_rate = travel_total / total_hours
    outside_rate = outside_total / total_hours
    
    sum_of_rates = onsite_rate + offsite_rate + travel_rate + outside_rate
    effective_rate = sum_of_rates × multiplier
    
    not_adjusted = onsite_total + offsite_total + travel_total + outside_total
    adjusted = not_adjusted × multiplier
    
    UPDATE ScopeLaborDetail with all calculated values
END IF
```

### Flow 2: Calculate Apparatus Revenue
**Trigger:** When Apparatus status changes to "Complete"

```
GET parent Task
GET parent Scope  
GET ScopeLaborDetail for Scope

apparatus_revenue = apparatus_total_hours × effective_rate

UPDATE Apparatus with revenue

ROLLUP: Update Scope.scope_revenue_total
ROLLUP: Update Project totals (if needed)
```

---

## What Gets Stored vs Calculated

| Field | Stored from Import | Calculated by Power Automate |
|-------|-------------------|------------------------------|
| Onsite Total | ✅ | |
| Offsite Total | ✅ | |
| Travel Total | ✅ | |
| Outside Services Total | ✅ | |
| Total Hours | ✅ | |
| Multiplier | ✅ | |
| Quoted Amount | ✅ | |
| Onsite Rate | | ✅ |
| Offsite Rate | | ✅ |
| Travel Rate | | ✅ |
| Outside Services Rate | | ✅ |
| Sum of Rates | | ✅ |
| Effective Rate | | ✅ |
| Not Adjusted Total | | ✅ |
| Adjusted Total | | ✅ |
| Apparatus Revenue | | ✅ (on status change) |
| Scope Revenue Total | | ✅ (rollup) |

---

## Reporting Possibilities

Because all 4 categories are stored AND their rates calculated:

- **What's our blended rate per project?** → effective_rate
- **What % of cost is travel?** → travel_total / not_adjusted
- **Travel cost per hour across all projects?** → SUM(travel_total) / SUM(total_hours)
- **Which scopes have highest outside services %?** → outside_total / not_adjusted
- **Revenue recognized this month?** → SUM(apparatus_revenue) WHERE status = Complete AND test_date in range

---

*Last Updated: November 30, 2025*
