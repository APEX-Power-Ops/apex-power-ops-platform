# RESA Power - Architecture Diagrams

## System Architecture Overview

```mermaid
graph TB
    subgraph "User Layer"
        Mobile[Mobile Users<br/>Field Technicians]
        Desktop[Desktop Users<br/>Project Managers]
        Exec[Executives<br/>Leadership]
    end
    
    subgraph "Application Layer"
        Canvas[Canvas App<br/>Field Tracker]
        ModelDriven[Model-Driven App<br/>PM Portal]
        PowerBI[Power BI<br/>Dashboards]
    end
    
    subgraph "Integration Layer"
        PowerAutomate[Power Automate<br/>Workflows]
        Connectors[Connectors<br/>APIs]
    end
    
    subgraph "Data Layer"
        Dataverse[(Dataverse<br/>Database)]
    end
    
    subgraph "Microsoft 365 Services"
        Teams[Teams]
        SharePoint[SharePoint]
        Outlook[Outlook]
        OneDrive[OneDrive]
    end
    
    Mobile --> Canvas
    Desktop --> ModelDriven
    Desktop --> PowerBI
    Exec --> PowerBI
    
    Canvas --> Dataverse
    ModelDriven --> Dataverse
    PowerBI --> Dataverse
    
    PowerAutomate --> Dataverse
    PowerAutomate --> Teams
    PowerAutomate --> SharePoint
    PowerAutomate --> Outlook
    
    Dataverse --> SharePoint
    ModelDriven --> Teams
    
    style Dataverse fill:#0078D4,color:#fff
    style Canvas fill:#742774,color:#fff
    style ModelDriven fill:#742774,color:#fff
    style PowerBI fill:#F2C811,color:#000
    style PowerAutomate fill:#0066FF,color:#fff
```

## Dataverse Entity Relationship Diagram

**Version:** 3.0 (Updated November 28, 2025)  
**Tables:** 19 (16 existing + 3 new NETA tables)  
**Status:** Reflects v1.6.0.0 architecture with NETA Checklists

```mermaid
erDiagram
    %% Core Project Management Tables
    BUSINESSUNIT ||--o{ PROJECT : "manages"
    CLIENT ||--o{ PROJECT : "contracts"
    SITE ||--o{ PROJECT : "located_at"
    CLIENT ||--o{ SITE : "owns"
    CLIENT ||--o{ QUOTE : "requests"
    SITE ||--o{ QUOTE : "for_location"
    QUOTE ||--o| PROJECT : "converts_to"
    
    PROJECT ||--o{ SCOPE : "has many"
    PROJECT ||--o{ TASK : "contains"
    PROJECT ||--o{ APPARATUS_REVENUE : "recognizes"
    PROJECT ||--o{ RESOURCE_ASSIGNMENT : "staffed_by"
    PROJECT ||--o{ EQUIPMENT : "uses"
    
    SCOPE ||--o{ TASK : "includes"
    SCOPE ||--|| SCOPE_LABOR_DETAIL : "budgeted_by"
    SCOPE ||--o{ APPARATUS_REVENUE : "bills"
    
    TASK ||--o{ APPARATUS : "tests"
    
    APPARATUS }o--|| APPARATUS_TYPE_MASTER : "classified_as"
    APPARATUS ||--o{ APPARATUS_REVENUE : "generates"
    
    %% NEW v1.6.0.0: NETA Checklist System
    APPARATUS_TYPE_MASTER ||--o{ NETA_TEST_TEMPLATE : "defines_tests_via_section"
    APPARATUS ||--o{ APPARATUS_TEST_CHECKLIST : "has_checklist"
    NETA_TEST_TEMPLATE ||--o{ APPARATUS_TEST_CHECKLIST : "template_for"
    APPARATUS ||--o{ APPARATUS_SUBMISSION : "submitted_via"
    
    %% Resource Management
    EMPLOYEE ||--o{ RESOURCE_ASSIGNMENT : "assigned_via"
    EMPLOYEE ||--o{ EQUIPMENT : "uses"
    
    %% v1.6.0.0 NEW TABLES
    NETA_TEST_TEMPLATE {
        guid id PK
        string test_description
        string neta_section "e.g. 7.6.3"
        choice test_type "Visual or Electrical"
        choice neta_standard "ATS or MTS"
        bool requires_value
        int sort_order
        bool active
    }
    
    APPARATUS_TEST_CHECKLIST {
        guid id PK
        lookup apparatus FK
        lookup test_template FK
        choice status "Not Started/Complete/N-A/Failed"
        bool is_complete
        string recorded_value
        string notes
        datetime completed_date
    }
    
    APPARATUS_SUBMISSION {
        guid id PK
        lookup apparatus FK
        datetime submitted_date
        choice review_status "Pending/Approved/Rejected"
        datetime reviewed_date
        string rejection_reason
    }
```

---

## NETA Checklist Workflow (v1.6.0.0)

```mermaid
flowchart LR
    subgraph Templates["📚 Master Templates"]
        NETA[NETA Test Template<br/>~800 test items]
        ATM[ApparatusTypeMaster<br/>links to NETA sections]
    end
    
    subgraph Execution["👷 Field Execution"]
        APP[Apparatus Created]
        CHK[Test Checklist Generated]
        WORK[Tech Completes Tests]
    end
    
    subgraph Review["✅ Approval"]
        SUB[Submission Created]
        REV[PM Reviews]
        APR{Approved?}
    end
    
    subgraph Complete["🏁 Completion"]
        DONE[Apparatus Complete]
        REV_REC[Revenue Recognition]
    end
    
    NETA --> ATM
    ATM --> APP
    APP -->|Auto-generate| CHK
    CHK --> WORK
    WORK --> SUB
    SUB --> REV
    REV --> APR
    APR -->|Yes| DONE
    APR -->|No| WORK
    DONE --> REV_REC
    
    style Templates fill:#e3f2fd
    style Execution fill:#fff3e0
    style Review fill:#e8f5e9
    style Complete fill:#f3e5f5
```

---

## Legacy Dataverse Entity Relationship Diagram (Pre-v1.6.0.0)

**Version:** 2.0 (November 22, 2025)  
**Tables:** 14 (8 original + 6 new)  
**Status:** Archived - superseded by v3.0 above

```mermaid
erDiagram
    %% Core Project Management Tables
    BUSINESSUNIT ||--o{ PROJECT : "manages"
    CLIENT ||--o{ PROJECT : "contracts"
    SITE ||--o{ PROJECT : "located_at"
    CLIENT ||--o{ SITE : "owns"
    CLIENT ||--o{ QUOTE : "requests"
    SITE ||--o{ QUOTE : "for_location"
    QUOTE ||--o| PROJECT : "converts_to"
    
    PROJECT ||--o{ SCOPE : "has many"
    PROJECT ||--o{ TASK : "contains"
    PROJECT ||--o{ APPARATUS_REVENUE : "recognizes"
    PROJECT ||--o{ RESOURCE_ASSIGNMENT : "staffed_by"
    PROJECT ||--o{ EQUIPMENT : "uses"
    
    SCOPE ||--o{ TASK : "includes"
    SCOPE ||--|| SCOPE_LABOR_DETAIL : "budgeted_by"
    SCOPE ||--o{ APPARATUS_REVENUE : "bills"
    
    TASK ||--o{ APPARATUS : "tests"
    
    APPARATUS }o--|| APPARATUS_TYPE_MASTER : "classified_as"
    APPARATUS ||--o{ APPARATUS_REVENUE : "generates"
    
    SCOPE_LABOR_DETAIL ||--o{ APPARATUS_REVENUE : "rates_for"
    
    %% Resource Management
    EMPLOYEE ||--o{ RESOURCE_ASSIGNMENT : "assigned_via"
    EMPLOYEE ||--o{ EQUIPMENT : "uses"
    
    %% Original relationships maintained
    TASK }o--|| APPARATUS_TYPE_MASTER : "specifies"
    
    %% NEW TABLES (Added November 22, 2025)
    CLIENT {
        guid ClientID PK
        string Client_Number
        string Client_Name
        string Client_Type
        string Industry
        string Account_Status
        string Primary_Contact_Name
        string Primary_Contact_Email
        string Primary_Contact_Phone
        string Billing_Contact_Name
        string Billing_Contact_Email
        string Mailing_Address
        string Mailing_City
        string Mailing_State
        string Mailing_ZIP
        string Tax_ID
        string Payment_Terms
        currency Credit_Limit
        string Insurance_Certificate
        date Insurance_Expiration
        string Notes
    }
    
    SITE {
        guid SiteID PK
        string Site_Number
        string Site_Name
        lookup Client FK
        string Site_Type
        string Status
        string Address
        string City
        string State
        string ZIP
        string County
        decimal Latitude
        decimal Longitude
        string Site_Contact
        string Site_Contact_Phone
        string Site_Contact_Email
        string Access_Requirements
        string Safety_Protocols
        string Parking_Instructions
        string Special_Equipment
        string Utility_Company
        string Utility_Account_Number
        string Notes
    }
    
    EMPLOYEE {
        guid EmployeeID PK
        string Employee_Number
        string Full_Name
        string Employee_Type
        string Status
        string Title
        string Department
        string Email
        string Phone
        date Hire_Date
        string Skillset
        string Certifications
        string License_Number
        date License_Expiration
        currency Hourly_Rate
        currency Overtime_Rate
        currency Billing_Rate
        string Availability
        string Emergency_Contact
        string Emergency_Phone
        string Notes
    }
    
    QUOTE {
        guid QuoteID PK
        string Quote_Number
        string Quote_Name
        lookup Client FK
        lookup Site FK
        string Quote_Type
        string Status
        date Quote_Date
        date Expiration_Date
        string Requested_By
        string Requested_Email
        string Prepared_By
        string Approved_By
        date Approval_Date
        string Scope_Description
        decimal Estimated_Hours
        currency Labor_Rate
        currency Labor_Cost
        currency Material_Cost
        currency Equipment_Cost
        currency Other_Costs
        currency Subtotal
        decimal Margin_Percent
        currency Total_Quote
        boolean Converted_To_Project
        date Conversion_Date
        string Loss_Reason
        string Notes
    }
    
    RESOURCE_ASSIGNMENT {
        guid AssignmentID PK
        string Assignment_Number
        lookup Project FK
        lookup Employee FK
        string Role
        string Assignment_Type
        string Status
        date Start_Date
        date End_Date
        decimal Allocated_Hours
        decimal Actual_Hours
        decimal Remaining_Hours
        currency Billing_Rate
        boolean Billable
        string Notes
    }
    
    EQUIPMENT {
        guid EquipmentID PK
        string Equipment_Number
        string Equipment_Name
        string Equipment_Type
        string Category
        string Status
        string Manufacturer
        string Model
        string Serial_Number
        date Purchase_Date
        currency Purchase_Cost
        boolean Calibration_Required
        date Last_Calibration_Date
        date Next_Calibration_Due
        int Calibration_Interval_Days
        string Maintenance_Schedule
        date Last_Maintenance_Date
        date Next_Maintenance_Due
        string Current_Location
        lookup Assigned_To_Employee FK
        lookup Current_Project FK
        string Notes
    }
    
    %% ORIGINAL CORE TABLES (v1.3.0.5)
    BUSINESSUNIT {
        guid BusinessUnitID PK
        string Name
        string Location_Code
        string City
        string State
        string Region
    }
    
    PROJECT {
        guid ProjectID PK
        string Project_Number
        string Project_Name
        lookup BusinessUnit FK
        lookup Client FK
        lookup Site FK
        lookup Converted_From_Quote FK
        date Start_Date
        date Target_Completion
        choice Status
        decimal Total_Apparatus_Count
        decimal Completed_Apparatus_Count
        decimal Total_Apparatus_Hours
        decimal Total_Completed_Hours
        decimal Total_Actual_Hours
        decimal Total_Delays
        decimal Total_Remaining_Hours
        decimal Percent_Complete
    }
    
    SCOPE {
        guid ScopeID PK
        lookup Project FK
        string Scope_Name
        int Scope_Number
        choice NETA_Standard
        choice Status
        decimal Total_Apparatus_Count
        decimal Completed_Apparatus_Count
        decimal Total_Apparatus_Hours
        decimal Total_Completed_Hours
        decimal Total_Actual_Hours
        decimal Total_Delays
        decimal Total_Remaining_Hours
        decimal Percent_Complete
    }
    
    SCOPE_LABOR_DETAIL {
        guid ConfigID PK
        lookup Project_Scope FK "1:1"
        decimal Total_Apparatus_Hours
        currency Offsite_Labor_Total
        currency Onsite_Labor_Total
        currency Travel_Total
        currency Outside_Services_Total
        decimal Offsite_Labor_Percent
        decimal Onsite_Labor_Percent
        decimal Travel_Percent
        decimal Outside_Services_Percent
        currency Equipment_Fixed_Total
        currency Travel_Fixed_Total
        decimal Scope_Multiplier
        currency Effective_Labor_Rate "Calculated"
    }
    
    TASK {
        guid TaskID PK
        lookup Project FK
        lookup ProjectScope FK
        string Task_Name
        choice Task_Type
        choice Status
        decimal Total_Apparatus_Count
        decimal Completed_Apparatus_Count
        decimal Total_Apparatus_Hours
        decimal Total_Completed_Hours
        decimal Total_Actual_Hours
        decimal Total_Delays
        decimal Total_Remaining_Hours
        decimal Percent_Complete
    }
    
    APPARATUS {
        guid ApparatusID PK
        lookup Project FK
        lookup ProjectScope FK
        lookup Task FK
        lookup ApparatusTypeMaster FK
        string Designation
        string Serial_Number
        decimal Apparatus_Hours
        decimal Delays
        decimal Actual_Hours "Calculated"
        decimal Completed_Hours "Calculated"
        decimal Remaining_Hours "Calculated"
        choice Completion_Status
        date Date_Completed
        choice Apparatus_Assessment
        choice Witness_Test
        string Notes
    }
    
    APPARATUS_REVENUE {
        guid RevenueID PK
        lookup Apparatus FK
        lookup Project FK
        lookup Scope_Labor_Detail FK
        decimal Apparatus_Hours
        decimal Delays
        currency Effective_Labor_Rate
        currency Revenue_Amount "Calculated"
        choice Revenue_Status
        datetime Created_On
    }
    
    APPARATUS_TYPE_MASTER {
        guid TypeID PK
        string Apparatus_Type_Name
        string Category
        decimal ATS_Hours
        decimal MTS_Hours
        boolean Is_Active
        string Description
    }
```
    
    PROJECT {
        string ProjectNumber PK
        string JobNumber
        string ProjectName
        lookup Client
        date StartDate
        date EndDate
        string SiteAddress
        string SiteCity
        choice Status
        lookup ProjectLead
    }
    
    SCOPE {
        string ScopeID PK
        lookup Project FK
        string ScopeName
        choice NETAStandard
        int ScopeNumber
        decimal BudgetHours
        decimal ActualHours
        currency BaseRate
        decimal Multiplier
        choice Status
    }
    
    TASK {
        string TaskID PK
        lookup Project FK
        lookup Scope FK
        string TaskName
        choice NETAStandard
        lookup Apparatus FK
        string Designation
        choice Status
        choice Priority
        choice Availability
        decimal QuotedHours
        decimal ActualHours
        decimal PercentComplete
        date DateDue
        date DateCompleted
        lookup AssignedTo FK
    }
    
    APPARATUS {
        string ApparatusID PK
        string ApparatusName
        choice Type
        choice Category
        decimal ATSHours
        decimal MTSHours
        boolean IsActive
    }
    
    TIME_ENTRY {
        string EntryID PK
        lookup Task FK
        lookup Project FK
        lookup User FK
        date WorkDate
        decimal Hours
        choice LaborType
        date WeekEnding
        boolean Submitted
        boolean Approved
    }
    
    BILLING_LINE {
        string LineID PK
        lookup Task FK
        lookup Scope FK
        lookup Project FK
        date WeekEnding
        string BillingPeriod
        decimal BaseHours
        currency BaseLaborAmount
        decimal CommuteHours
        currency CommuteAmount
        decimal PMHours
        currency PMAmount
        decimal TravelHours
        currency TravelAmount
        currency TotalBillableAmount
        choice Status
    }
    
    LABOR_RATE_CONFIG {
        string ConfigID PK
        lookup Scope FK
        currency BaseRate
        decimal CommutePercent
        decimal PMPercent
        decimal TravelPercent
        decimal Multiplier
    }
    
    USER {
        string UserID PK
        string Name
        string Email
        choice Role
        boolean IsActive
    }
```

## Application Flow Diagram

```mermaid
graph LR
    subgraph "Field Technician Journey"
        A1[Login to<br/>Canvas App] --> A2[View My Tasks]
        A2 --> A3[Select Task]
        A3 --> A4[Update Status]
        A4 --> A5[Enter Hours]
        A5 --> A6[Submit]
        A6 --> A7[Notification Sent]
    end
    
    subgraph "Project Manager Journey"
        B1[Login to<br/>Model-Driven App] --> B2[Create Project]
        B2 --> B3[Add Scopes]
        B3 --> B4[Create Tasks]
        B4 --> B5[Assign Tasks]
        B5 --> B6[Monitor Progress]
        B6 --> B7[Review & Approve<br/>Time Entries]
        B7 --> B8[Generate Reports]
    end
    
    subgraph "Executive Journey"
        C1[Open Power BI] --> C2[View Dashboard]
        C2 --> C3[Filter by Project]
        C3 --> C4[Analyze Metrics]
        C4 --> C5[Export Report]
    end
    
    A7 -.->|Triggers| B6
    B7 -.->|Updates| C2
    
    style A1 fill:#742774,color:#fff
    style B1 fill:#742774,color:#fff
    style C1 fill:#F2C811,color:#000
```

## Power Automate Workflow Architecture

```mermaid
graph TB
    subgraph "Notification Flows"
        NF1[Task Assignment<br/>Notification]
        NF2[Overdue Task<br/>Alert]
        NF3[Status Change<br/>Notification]
    end
    
    subgraph "Approval Flows"
        AF1[Time Entry<br/>Approval]
        AF2[Billing<br/>Approval]
    end
    
    subgraph "Scheduled Flows"
        SF1[Weekly Billing<br/>Report]
        SF2[Daily Status<br/>Digest]
    end
    
    subgraph "Document Flows"
        DF1[Datasheet Upload<br/>to SharePoint]
        DF2[Document Tagging]
    end
    
    subgraph "Triggers"
        T1[Dataverse Change]
        T2[Schedule]
        T3[Manual]
    end
    
    subgraph "Actions"
        AC1[Send Email]
        AC2[Post to Teams]
        AC3[Update Record]
        AC4[Create Document]
    end
    
    T1 --> NF1 & NF3 & AF1 & AF2 & DF1
    T2 --> NF2 & SF1 & SF2
    T3 --> SF1
    
    NF1 & NF2 & NF3 --> AC1 & AC2
    AF1 & AF2 --> AC3
    SF1 & SF2 --> AC4 & AC1
    DF1 & DF2 --> AC3
    
    style NF1 fill:#0066FF,color:#fff
    style NF2 fill:#0066FF,color:#fff
    style NF3 fill:#0066FF,color:#fff
    style AF1 fill:#0066FF,color:#fff
    style AF2 fill:#0066FF,color:#fff
    style SF1 fill:#0066FF,color:#fff
    style SF2 fill:#0066FF,color:#fff
    style DF1 fill:#0066FF,color:#fff
    style DF2 fill:#0066FF,color:#fff
```

## Data Migration Flow

```mermaid
graph LR
    subgraph "Source"
        Excel[Excel XLSM<br/>9 Worksheets]
    end
    
    subgraph "Extraction"
        Python[Python Script<br/>Data Extraction]
    end
    
    subgraph "Transformation"
        CSV[CSV Files<br/>Clean & Transform]
    end
    
    subgraph "Validation"
        Review[Manual Review<br/>& Validation]
    end
    
    subgraph "Import"
        Import[Dataverse<br/>Data Import]
    end
    
    subgraph "Target"
        Dataverse[(Dataverse<br/>Tables)]
    end
    
    Excel -->|Read| Python
    Python -->|Generate| CSV
    CSV -->|Review| Review
    Review -->|Approve| Import
    Import -->|Load| Dataverse
    
    style Excel fill:#217346,color:#fff
    style Python fill:#3776AB,color:#fff
    style Dataverse fill:#0078D4,color:#fff
```

## Security Model

```mermaid
graph TB
    subgraph "Security Roles"
        SR1[System Admin]
        SR2[Project Manager]
        SR3[Field Technician]
        SR4[Billing Clerk]
        SR5[Executive]
        SR6[Client External]
    end
    
    subgraph "Permissions"
        P1[Full Access]
        P2[Read/Write Own<br/>Read All]
        P3[Read/Write Assigned]
        P4[Read/Write Billing<br/>Read Projects]
        P5[Read All]
        P6[Read Own Only]
    end
    
    subgraph "Data Access"
        D1[All Data]
        D2[Department Data]
        D3[Assigned Data]
        D4[Public Data]
    end
    
    SR1 --> P1 --> D1
    SR2 --> P2 --> D2
    SR3 --> P3 --> D3
    SR4 --> P4 --> D2
    SR5 --> P5 --> D1
    SR6 --> P6 --> D3
    
    style SR1 fill:#C00000,color:#fff
    style SR2 fill:#0070C0,color:#fff
    style SR3 fill:#00B050,color:#fff
    style SR4 fill:#FFC000,color:#000
    style SR5 fill:#7030A0,color:#fff
    style SR6 fill:#767171,color:#fff
```

## Integration Architecture

```mermaid
graph TB
    subgraph "Power Platform"
        PP1[Canvas App]
        PP2[Model-Driven App]
        PP3[Power BI]
        PP4[Power Automate]
        PP5[(Dataverse)]
    end
    
    subgraph "Microsoft 365"
        M1[Teams]
        M2[SharePoint]
        M3[Outlook]
        M4[OneDrive]
        M5[Planner]
    end
    
    subgraph "External Systems"
        E1[Accounting System]
        E2[CRM]
        E3[Document Management]
    end
    
    subgraph "Integration Methods"
        I1[Native Connectors]
        I2[Custom Connectors]
        I3[Power Automate Flows]
        I4[API Calls]
    end
    
    PP1 & PP2 --> PP5
    PP3 --> PP5
    PP4 --> PP5
    
    PP4 --> I1 --> M1 & M2 & M3 & M4
    PP4 --> I3 --> M5
    PP2 --> I1 --> M1
    
    PP4 --> I2 & I4 --> E1 & E2 & E3
    
    style PP5 fill:#0078D4,color:#fff
    style PP1 fill:#742774,color:#fff
    style PP2 fill:#742774,color:#fff
    style PP3 fill:#F2C811,color:#000
    style PP4 fill:#0066FF,color:#fff
```

## Canvas App Screen Flow

```mermaid
graph TB
    Start([App Launch]) --> Auth{Authenticated?}
    Auth -->|No| Login[Login Screen]
    Auth -->|Yes| Home[Home Dashboard]
    
    Login --> Home
    
    Home --> Tasks[Task List]
    Home --> Time[Time Entry]
    Home --> Projects[Project Lookup]
    Home --> Profile[Profile]
    
    Tasks --> TaskDetail[Task Detail]
    TaskDetail --> EditTask[Edit Task]
    TaskDetail --> AddTime[Add Time Entry]
    
    Time --> TimeForm[Time Entry Form]
    TimeForm --> Submit[Submit]
    Submit --> Confirm[Confirmation]
    
    Projects --> ProjectDetail[Project Detail]
    ProjectDetail --> ProjectTasks[Project Tasks]
    ProjectTasks --> TaskDetail
    
    Profile --> Settings[Settings]
    Profile --> Logout[Logout]
    
    Confirm --> Home
    Logout --> Start
    
    style Home fill:#742774,color:#fff
    style TaskDetail fill:#0078D4,color:#fff
    style TimeForm fill:#00B050,color:#fff
```

## Model-Driven App Sitemap

```mermaid
graph TB
    Root[RESA Power PM Portal]
    
    Root --> Projects[Projects]
    Root --> Tasks[Tasks]
    Root --> Billing[Billing]
    Root --> Resources[Resources]
    Root --> Admin[Administration]
    
    Projects --> P1[Active Projects]
    Projects --> P2[All Projects]
    Projects --> P3[My Projects]
    Projects --> P4[Project Calendar]
    Projects --> P5[Archived Projects]
    
    Tasks --> T1[My Tasks]
    Tasks --> T2[All Tasks]
    Tasks --> T3[Overdue Tasks]
    Tasks --> T4[By Status]
    Tasks --> T5[By Priority]
    
    Billing --> B1[Time Entries]
    Billing --> B2[Billing Lines]
    Billing --> B3[Weekly Billing]
    Billing --> B4[Invoicing]
    Billing --> B5[Rate Configuration]
    
    Resources --> R1[Team Members]
    Resources --> R2[Apparatus Catalog]
    Resources --> R3[Resource Calendar]
    Resources --> R4[Capacity Planning]
    
    Admin --> A1[Users & Teams]
    Admin --> A2[Security Roles]
    Admin --> A3[Reference Data]
    Admin --> A4[System Settings]
    Admin --> A5[Audit Logs]
    
    style Root fill:#742774,color:#fff
    style Projects fill:#0078D4,color:#fff
    style Tasks fill:#00B050,color:#fff
    style Billing fill:#FFC000,color:#000
    style Resources fill:#C00000,color:#fff
    style Admin fill:#767171,color:#fff
```

## Business Process Flow - Project Lifecycle

```mermaid
graph LR
    Stage1[Setup<br/>━━━━━<br/>• Create Project<br/>• Add Details<br/>• Assign PM] --> Stage2[Scoping<br/>━━━━━<br/>• Define Scopes<br/>• Estimate Hours<br/>• Set Rates]
    
    Stage2 --> Stage3[Execution<br/>━━━━━<br/>• Create Tasks<br/>• Assign Work<br/>• Track Progress]
    
    Stage3 --> Stage4[Billing<br/>━━━━━<br/>• Review Hours<br/>• Calculate Costs<br/>• Generate Invoice]
    
    Stage4 --> Stage5[Closeout<br/>━━━━━<br/>• Final Review<br/>• Archive Docs<br/>• Complete Project]
    
    style Stage1 fill:#0078D4,color:#fff
    style Stage2 fill:#00B050,color:#fff
    style Stage3 fill:#FFC000,color:#000
    style Stage4 fill:#C00000,color:#fff
    style Stage5 fill:#767171,color:#fff
```

## Deployment Pipeline

```mermaid
graph LR
    subgraph "Development"
        Dev1[Dev Environment]
        Dev2[Developer Workstation]
    end
    
    subgraph "Testing"
        Test1[Test Environment]
        Test2[UAT Environment]
    end
    
    subgraph "Production"
        Prod1[Production Environment]
    end
    
    subgraph "Solution Package"
        Sol[Solution .zip]
    end
    
    Dev2 -->|Build| Dev1
    Dev1 -->|Export| Sol
    Sol -->|Import| Test1
    Test1 -->|Promote| Test2
    Test2 -->|Deploy| Prod1
    
    style Dev1 fill:#0078D4,color:#fff
    style Test1 fill:#FFC000,color:#000
    style Test2 fill:#FFC000,color:#000
    style Prod1 fill:#00B050,color:#fff
```

## Power BI Report Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        DS1[(Dataverse)]
    end
    
    subgraph "Power BI Service"
        PBI1[Dataset]
        PBI2[Dataflow]
    end
    
    subgraph "Reports"
        R1[Project Overview]
        R2[Task Performance]
        R3[Billing Analytics]
        R4[Resource Management]
        R5[Quality Metrics]
    end
    
    subgraph "Distribution"
        D1[Web Portal]
        D2[Mobile App]
        D3[Teams Tab]
        D4[Email Subscription]
        D5[Embedded in App]
    end
    
    DS1 --> PBI1
    DS1 --> PBI2
    PBI1 --> R1 & R2 & R3 & R4 & R5
    
    R1 & R2 & R3 & R4 & R5 --> D1 & D2 & D3 & D4 & D5
    
    style DS1 fill:#0078D4,color:#fff
    style PBI1 fill:#F2C811,color:#000
    style PBI2 fill:#F2C811,color:#000
    style R1 fill:#0078D4,color:#fff
    style R2 fill:#0078D4,color:#fff
    style R3 fill:#0078D4,color:#fff
    style R4 fill:#0078D4,color:#fff
    style R5 fill:#0078D4,color:#fff
```

## Timeline - Implementation Phases

```mermaid
gantt
    title RESA Power Implementation Timeline
    dateFormat  YYYY-MM-DD
    
    section Foundation
    Environment Setup           :done, f1, 2025-11-08, 7d
    Data Model Design          :done, f2, 2025-11-08, 7d
    Security Configuration     :active, f3, 2025-11-15, 7d
    
    section Data Migration
    Data Preparation           :m1, 2025-11-22, 7d
    Migration Execution        :m2, 2025-11-29, 7d
    Data Validation           :m3, 2025-12-06, 7d
    
    section Canvas App
    App Structure             :c1, 2025-12-13, 7d
    Core Screens             :c2, 2025-12-20, 7d
    Testing                  :c3, 2025-12-27, 7d
    
    section Model-Driven App
    App Foundation           :md1, 2026-01-03, 7d
    Forms & Views            :md2, 2026-01-10, 7d
    Business Processes       :md3, 2026-01-17, 7d
    
    section Automation
    Notification Flows       :a1, 2026-01-24, 7d
    Approval Flows          :a2, 2026-01-31, 7d
    
    section Reporting
    Power BI Development    :r1, 2026-02-07, 7d
    Dashboard Deployment    :r2, 2026-02-14, 7d
    
    section Launch
    UAT Testing            :l1, 2026-02-21, 7d
    Training               :l2, 2026-02-28, 7d
    Go-Live                :milestone, l3, 2026-03-07, 1d
    Hypercare Support      :l4, 2026-03-07, 14d
```

---

## How to Use These Diagrams

### Viewing Mermaid Diagrams

These diagrams use Mermaid syntax and can be viewed in:

1. **GitHub/GitLab**: Renders automatically in markdown files
2. **VS Code**: Install "Markdown Preview Mermaid Support" extension
3. **Online**: Copy to https://mermaid.live for interactive viewing
4. **Documentation sites**: Most modern doc platforms support Mermaid
5. **Export**: Use mermaid-cli to export as PNG/SVG

### Editing Diagrams

- Modify the text between \`\`\`mermaid and \`\`\` blocks
- Use Mermaid documentation: https://mermaid.js.org/
- Test changes at https://mermaid.live before committing

### Printing Diagrams

1. Open in mermaid.live
2. Click "Actions" → "Export PNG/SVG"
3. Use in presentations or documentation

---

*Document Version: 2.0*  
*Created: November 7, 2025*  
*Updated: November 28, 2025 - Added v1.6.0.0 NETA Checklist ERD and workflow*  
*For: RESA Power Architecture Documentation*
