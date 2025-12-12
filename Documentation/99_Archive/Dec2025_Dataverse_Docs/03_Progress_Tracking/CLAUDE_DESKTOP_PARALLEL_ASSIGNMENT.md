# Claude Desktop Parallel Assignment
## December 2, 2025 - Independent Work Items

**Context:** While Copilot works on the core revenue recognition flow and import pipeline, these items can be built in parallel as they have no dependencies on that workflow.

**Environment:** `org7bdbc942.crm.dynamics.com` (Developer)  
**Publisher Prefix:** `cr950_`

---

## 🎯 YOUR ASSIGNMENT: 3 Independent Tables

These tables are **NOT** part of the revenue recognition flow and can be built independently:

---

### 📊 Task 1: ApparatusTypeMaster Table (PRIORITY: HIGH)

**Purpose:** NETA standard hours lookup table for estimating apparatus testing time

**Why Independent:** This is a reference/lookup table. The import process will query it later, but it can exist before the import pipeline is built.

**Table Specification:**

| Field Name | Display Name | Data Type | Required | Notes |
|------------|--------------|-----------|----------|-------|
| `cr950_apparatustypemasterid` | ID | GUID | Auto | Primary Key |
| `cr950_apparatustypename` | Apparatus Type Name | String(200) | Yes | Primary Name, e.g. "Switchgear - Medium Voltage" |
| `cr950_atshours` | ATS Hours | Decimal | No | NETA ATS standard hours per unit |
| `cr950_mtshours` | MTS Hours | Decimal | No | NETA MTS standard hours per unit |
| `cr950_apparatussection` | Section | String(200) | No | Category grouping, e.g. "Power Distribution" |
| `cr950_apparatuscode` | Type Code | String(50) | No | Short code for quick reference |
| `cr950_apparatustypedescription` | Description | Memo | No | Detailed description |
| `cr950_apparatustypeactive` | Active | Boolean | No | Default true |

**Sample Data to Load:**
```
Switchgear - Medium Voltage, ATS: 2.5, MTS: 3.0, Section: Power Distribution
Switchgear - Low Voltage, ATS: 2.0, MTS: 2.5, Section: Power Distribution  
Transformer - Dry Type, ATS: 1.5, MTS: 2.0, Section: Transformers
Transformer - Liquid-Filled, ATS: 2.0, MTS: 2.5, Section: Transformers
Circuit Breaker - Air, ATS: 1.0, MTS: 1.5, Section: Protective Devices
Circuit Breaker - Vacuum, ATS: 1.5, MTS: 2.0, Section: Protective Devices
Relay - Protective, ATS: 1.0, MTS: 1.5, Section: Protective Devices
Motor Starter, ATS: 0.75, MTS: 1.0, Section: Motor Control
VFD/Drive, ATS: 1.0, MTS: 1.5, Section: Motor Control
ATS - Automatic Transfer Switch, ATS: 1.5, MTS: 2.0, Section: Transfer Equipment
UPS System, ATS: 2.0, MTS: 2.5, Section: Power Quality
Cable - Medium Voltage, ATS: 0.5, MTS: 0.75, Section: Cables
Cable - Low Voltage, ATS: 0.25, MTS: 0.5, Section: Cables
```

---

### 📊 Task 2: Employee Table (PRIORITY: MEDIUM)

**Purpose:** Track technicians, certifications, and resource availability for work assignment

**Why Independent:** Employee assignment is Phase 5A, completely separate from revenue recognition (Phase 5E).

**Table Specification:**

| Field Name | Display Name | Data Type | Required | Notes |
|------------|--------------|-----------|----------|-------|
| `cr950_employeeid` | ID | GUID | Auto | Primary Key |
| `cr950_employeename` | Employee Name | String(200) | Yes | Primary Name, full name |
| `cr950_employeenumber` | Employee Number | String(50) | No | HR/payroll ID |
| `cr950_employeeemail` | Email | String(200) | No | Company email |
| `cr950_employeephone` | Phone | String(50) | No | Contact phone |
| `cr950_employeetitle` | Title | String(100) | No | Job title |
| `cr950_employeecertifications` | Certifications | Memo | No | NETA, NICET, etc. |
| `cr950_employeeskillset` | Skillset | Memo | No | Technical specialties |
| `cr950_employeebillingrate` | Billing Rate | Currency | No | Hourly billing rate |
| `cr950_employeecostrate` | Cost Rate | Currency | No | Internal cost rate |
| `cr950_employeeavailability` | Availability | String(50) | No | Full-time, Part-time, Contract |
| `cr950_employeelocation` | Location | Lookup→Location | No | Home base location |
| `cr950_employeestartdate` | Start Date | DateTime | No | Employment start |
| `cr950_employeeactive` | Active | Boolean | No | Default true |
| `cr950_employeenotes` | Notes | Memo | No | Additional info |

**Optional:** Add lookup to Dataverse System User if you want to link to actual Power Platform users.

---

### 📊 Task 3: Quote Table (PRIORITY: MEDIUM)

**Purpose:** Pre-project estimates that can convert to Projects

**Why Independent:** Quote workflow is pre-project, not part of the execution/revenue flow.

**Table Specification:**

| Field Name | Display Name | Data Type | Required | Notes |
|------------|--------------|-----------|----------|-------|
| `cr950_quoteid` | ID | GUID | Auto | Primary Key |
| `cr950_quotename` | Quote Name | String(200) | Yes | Primary Name |
| `cr950_quotenumber` | Quote Number | String(50) | No | Auto-number or manual |
| `cr950_quoteclient` | Client | Lookup→Client | Yes | Customer |
| `cr950_quotesite` | Site | Lookup→Site | No | Work location |
| `cr950_quotedescription` | Description | Memo | No | Scope of work summary |
| `cr950_quotetotalamount` | Total Amount | Currency | No | Quote value |
| `cr950_quotemarginpercent` | Margin % | Decimal | No | Target margin |
| `cr950_quotestatus` | Status | Choice | No | Draft, Sent, Accepted, Rejected, Expired |
| `cr950_quotecreateddate` | Created Date | DateTime | No | When quote was created |
| `cr950_quotesentdate` | Sent Date | DateTime | No | When sent to customer |
| `cr950_quoteexpirationdate` | Expiration Date | DateTime | No | Valid until |
| `cr950_quoteconvertedtoproject` | Converted | Boolean | No | Default false |
| `cr950_quoteproject` | Project | Lookup→Project | No | If converted, link to project |
| `cr950_quoteconverteddate` | Converted Date | DateTime | No | When converted |
| `cr950_quoteactive` | Active | Boolean | No | Default true |
| `cr950_quotenotes` | Notes | Memo | No | Additional info |

**Status Choice Values:**
- 957080000 = Draft
- 957080001 = Sent
- 957080002 = Accepted
- 957080003 = Rejected
- 957080004 = Expired

---

## 📋 Deliverables Checklist

When complete, please provide:

1. **Confirmation** that each table was created in org7bdbc942
2. **EntitySetName** for each table (API name)
3. **Any issues** encountered during creation
4. **Sample data** loaded (if any)

---

## ⚠️ Important Notes

1. **DO NOT** create ApparatusRevenue table - that's being handled as part of the core revenue workflow
2. **Publisher prefix** must be `cr950_` for all fields
3. **Environment URL:** `https://org7bdbc942.crm.dynamics.com`
4. All tables should be **organization-owned** (not user-owned)
5. Tables should be **enabled for activities** if you want to attach notes/tasks

---

## 🔗 Reference Files

- Schema Audit: `Documentation/SCHEMA_AUDIT_org7bdbc942_Dec2025.md`
- Table Names Reference: `MCP_Servers/resa-dataverse-mcp/TABLE_NAMES_REFERENCE.md`
- Project Overview: `PROJECT_OVERVIEW.md`

---

**Assignment Status:** READY FOR WORK  
**Estimated Effort:** 2-3 hours  
**Dependencies:** None - all independent

*Created: December 2, 2025*
