# RESA Power Data Model Reference

**Version:** 1.0  
**Date:** November 28, 2025  
**Status:** Authoritative Reference  
**Author:** Jason Swenson / Claude AI Assistant

---

## Overview

This document defines the canonical data model for RESA Power project management. It establishes the terminology, relationships, and table structure that all systems (Dataverse, Power Automate, Web App) must follow.

---

## Core Entities & Terminology

### The Three-Way Split: Business Unit vs Client vs Site

| Entity | What It Is | Purpose | Examples |
|--------|------------|---------|----------|
| **Business Unit** | RESA internal office/location | Operational ownership, P&L, resource allocation | Phoenix, Salt Lake City, Houston, Los Angeles |
| **Client** | Billing entity - who pays the invoice | Accounts receivable, contracts, CRM integration | Vulcan Materials, Garney Construction, City of Mesa |
| **Site** | Physical location where work occurs | Field crew logistics, safety, access | Queen Creek Quarry, Mesa WTP North, Marana Wet Plant |

### Why This Matters

- **Business Unit** → "Which RESA office owns this project?" (Internal ops/accounting)
- **Client** → "Who do we invoice?" (Billing contacts - may have many sites)
- **Site** → "Where do we send the crew?" (Physical location details)

These are **not interchangeable**. A single client (Vulcan Materials) may have 15+ sites. A single project may span multiple sites (multi-site scopes). RESA's Phoenix Business Unit may handle projects for clients nationwide.

---

## Table Definitions

### `cr950_businessunits` - Business Units

**Purpose:** RESA internal offices/locations. Used for operational ownership and reporting.

| Field | Type | Description |
|-------|------|-------------|
| `cr950_businessunitid` | Primary Key | Unique identifier |
| `cr950_location_name` | Text | Display name (e.g., "Phoenix") |
| `cr950_address` | Text | Office street address |
| `cr950_city` | Text | City |
| `cr950_state` | Text | State |
| `cr950_zip` | Text | ZIP code |
| `cr950_active` | Yes/No | Is this BU currently active? |
| `cr950_isdeleted` | Yes/No | Soft delete flag |

**Notes:**
- This is a small master list (10-15 records max company-wide)
- Maps to CRM's "RESA Location" field
- Used for filtering projects by region/office

---

### `cr950_clients` - Clients

**Purpose:** Customer billing entities. Who pays the invoices.

| Field | Type | Description |
|-------|------|-------------|
| `cr950_clientid` | Primary Key | Unique identifier |
| `cr950_name` | Text (Required) | Client name (e.g., "Vulcan Materials") |
| `cr950_clientnumber` | Text | CRM customer number |
| `cr950_clienttype` | Choice | Type classification |
| `cr950_billingaddress` | Text | Invoice mailing address |
| `cr950_billingcity` | Text | Billing city |
| `cr950_billingstate` | Text | Billing state |
| `cr950_billingzip` | Text | Billing ZIP |
| `cr950_primarycontact` | Text | AP/Billing contact name |
| `cr950_contactemail` | Email | Contact email |
| `cr950_contactphone` | Phone | Contact phone |
| `cr950_paymentterms` | Text | Net 30, Net 45, etc. |

**Relationships:**
- Has many **Sites** (1:N)
- Has many **Projects** (1:N)

**Notes:**
- Client names must be standardized (avoid duplicates like "Vulcan Materials" vs "Vulcan Materials Company - Birmingham, AL")
- SharePoint folder names in `/Estimators/{Client}/` must exactly match `cr950_name`

---

### `cr950_sites` - Sites

**Purpose:** Physical locations where work is performed. Customer facilities.

| Field | Type | Description |
|-------|------|-------------|
| `cr950_siteid` | Primary Key | Unique identifier |
| `cr950_name` | Text (Required) | Site name (e.g., "Queen Creek Quarry") |
| `cr950_client` | Lookup → Clients | Which client owns this site |
| `cr950_sitenumber` | Text | Client's internal site ID |
| `cr950_sitetype` | Text | Facility type (Quarry, Substation, WTP, etc.) |
| `cr950_address` | Text | Physical address |
| `cr950_city` | Text | City |
| `cr950_state` | Text | State |
| `cr950_zip` | Text | ZIP |
| `cr950_county` | Text | County |
| `cr950_latitude` | Decimal | GPS latitude |
| `cr950_longitude` | Decimal | GPS longitude |
| `cr950_sitecontact` | Text | On-site contact name |
| `cr950_sitecontactemail` | Email | Contact email |
| `cr950_sitecontactphone` | Phone | Contact phone |
| `cr950_parkinginstructions` | Text | Where to park |
| `cr950_accessrequirements` | Multiline | Badge, escort, PPE requirements |
| `cr950_safetyprotocols` | Multiline | Site-specific safety rules |
| `cr950_specialequipment` | Text | Required equipment notes |
| `cr950_notes` | Multiline | General notes |

**Relationships:**
- Belongs to **Client** (N:1)
- Has many **Scopes** (1:N) - via scope's site lookup

**Notes:**
- Sites are reusable - same quarry across multiple projects/years
- Field crews use this data for job site logistics
- Different from "Business Unit" which is RESA's internal offices

---

### `cr950_projectses` - Projects

**Purpose:** A contracted job with a Job Number (Order #). The container for all work.

| Field | Type | Description |
|-------|------|-------------|
| `cr950_projectsid` | Primary Key | Unique identifier |
| `cr950_project_name` | Text (Required) | Project display name |
| `cr950_project_number` | Text | CRM Order/Job Number |
| `cr950_client` | Lookup → Clients | Who pays (billing entity) |
| `cr950_client_name` | Text | Denormalized client name |
| `cr950_location` | Lookup → Business Units | Which RESA office owns this |
| `cr950_site` | Lookup → Sites | Primary job site (optional) |
| `cr950_owner` | Text | Project owner (for GC jobs - who the GC is building for) |
| `cr950_status` | Choice | Not Started, In Progress, Complete, On Hold |
| `cr950_start_date` | Date | Planned start |
| `cr950_end_date` | Date | Planned end |
| `cr950_actual_start` | Date | Actual start |
| `cr950_actual_end` | Date | Actual completion |
| `cr950_total_estimated_hours` | Rollup | Sum of scope hours |
| `cr950_total_actual_hours` | Rollup | Sum of actual hours |
| `cr950_total_estimated_revenue` | Rollup | Sum of scope revenue |
| `cr950_customerpurchaseorder` | Text | Customer PO# |
| `cr950_estimator` | Lookup → Estimators | Source estimator document |

**Relationships:**
- Belongs to **Client** (N:1)
- Belongs to **Business Unit** (N:1) via "Location" lookup
- Has many **Scopes** (1:N)
- Optionally linked to **Site** (N:1) for single-site projects

---

### `cr950_projectscopes` - Scopes

**Purpose:** A defined piece of work within a project. Each scope typically has its own site.

| Field | Type | Description |
|-------|------|-------------|
| `cr950_projectscopeid` | Primary Key | Unique identifier |
| `cr950_scope_name` | Text (Required) | Scope description |
| `cr950_scope_number` | Integer | WBS number (1, 2, 3...) |
| `cr950_project` | Lookup → Projects | Parent project |
| `cr950_site` | Lookup → Sites | **Where this scope's work happens** |
| `cr950_testing_standard` | Choice | NETA ATS, NETA MTS, etc. |
| `cr950_sld_reference` | Text | Schematic drawing reference |
| `cr950_status` | Choice | Not Started, In Progress, Complete |
| `cr950_start_date` | Date | Planned start |
| `cr950_end_date` | Date | Planned end |
| `cr950_total_estimated_hours` | Rollup | Sum from tasks/apparatus |
| `cr950_total_actual_hours` | Rollup | Sum of actual hours |
| `cr950_total_revenue` | Currency | Scope revenue |

**Relationships:**
- Belongs to **Project** (N:1)
- Belongs to **Site** (N:1) via `cr950_site` lookup - ✅ **Added 2025-11-28**
- Has many **Tasks** (1:N)
- Has many **Apparatus** (1:N)

**Notes:**
- For single-site projects: All scopes have the same Site
- For multi-site projects (like Garney): Each scope has its own Site
- Site lookup is optional - inherits from Project if not specified

---

## Entity Relationship Diagram

```
                    ┌─────────────────┐
                    │  Business Unit  │
                    │ (RESA Office)   │
                    └────────┬────────┘
                             │ 1:N
                             ↓
┌──────────┐    1:N    ┌──────────┐    1:N    ┌──────────┐
│  Client  │◄──────────│  Project │───────────►│  Scope   │
│ (Billing)│           └────┬─────┘           └────┬─────┘
└────┬─────┘                │                      │
     │                      │                      │
     │ 1:N                  │ N:1 (optional)       │ N:1
     ↓                      ↓                      ↓
┌──────────┐          ┌──────────┐          ┌──────────┐
│   Site   │◄─────────│   Site   │◄─────────│   Site   │
│(Customer │          │ (Project │          │ (Scope   │
│ Facility)│          │ default) │          │ specific)│
└──────────┘          └──────────┘          └──────────┘
                                                   │
                                            ┌──────┴──────┐
                                            │             │
                                       1:N  ↓        1:N  ↓
                                    ┌──────────┐  ┌───────────┐
                                    │   Task   │  │ Apparatus │
                                    └──────────┘  └───────────┘
```

---

## Multi-Site Project Example: Garney Central Mesa Reuse

This example shows how a single project can span multiple physical sites:

```
Project: Garney Central Mesa Reuse (#434469)
├── Business Unit: Phoenix
├── Client: Garney Construction
├── Owner: City of Mesa (who Garney is building for)
│
├── Scope 1: Mesa WTP North Electrical
│   └── Site: Mesa WTP North (123 N Water St, Mesa)
│       └── Apparatus: Switchgear SG-01, Transformer T-01, ...
│
├── Scope 2: Mesa WTP South Electrical  
│   └── Site: Mesa WTP South (456 S Treatment Blvd, Mesa)
│       └── Apparatus: Switchgear SG-02, MCC-01, ...
│
├── Scope 3: Pump Station 14
│   └── Site: Pump Station 14 (789 Industrial Way, Gilbert)
│       └── Apparatus: VFD-01, Motor-01, ...
│
└── Scope 4: Pump Station 22
    └── Site: Pump Station 22 (321 Utility Rd, Chandler)
        └── Apparatus: VFD-02, Motor-02, ...
```

**Key Points:**
- One Job Number (#434469)
- One Client (Garney Construction)
- One Business Unit (Phoenix)
- Four Sites (each scope has its own physical location)
- Client is different from Owner (Garney vs City of Mesa)

---

## SharePoint Folder to Data Model Mapping

```
SharePoint Path:
/Estimators/Vulcan Materials/Queen Creek 2025/estimate_20251128_Rev1.xlsm

Maps To:
┌─────────────────────────────────────────────────────────────────┐
│ Estimator Record                                                │
├─────────────────────────────────────────────────────────────────┤
│ Client:        → Vulcan Materials (lookup to cr950_clients)    │
│ Project Name:  "Queen Creek 2025" (from folder)                │
│ Date:          2025-11-28 (from filename)                      │
│ Revision:      1 (from filename)                               │
│ File URL:      [SharePoint link]                               │
└─────────────────────────────────────────────────────────────────┘

When Converted to Project:
┌─────────────────────────────────────────────────────────────────┐
│ Project Record                                                  │
├─────────────────────────────────────────────────────────────────┤
│ Client:        → Vulcan Materials                               │
│ Site:          → Queen Creek Quarry (if exists, or null)       │
│ Business Unit: → Phoenix (selected by user)                    │
│ Project Name:  "Queen Creek 2025"                              │
│ Job Number:    (from CRM when awarded)                         │
│ Estimator:     → [link to estimator record]                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Model Rules

### 1. Client Naming Standards
- Use clean, standardized names: "Vulcan Materials" not "Vulcan Materials Company - Birmingham, AL"
- One canonical name per client company
- SharePoint folder names must exactly match Dataverse `cr950_clients.cr950_name`

### 2. Site Reusability
- Sites are **master data** - created once, used across projects
- Same quarry visited in 2023, 2024, 2025 = same Site record
- Don't create duplicate sites for the same physical location

### 3. Business Unit Assignment
- Every project must have a Business Unit (required field)
- This determines which RESA office is responsible for P&L
- Maps to CRM's "RESA Location" field

### 4. Scope-Level Sites
- Every scope should have a Site lookup populated
- For single-site projects: all scopes have the same Site
- For multi-site projects: each scope has its own Site
- Site provides address, contact, safety info for field crews

---

## Related Tables (Reference)

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| `cr950_apparatus` | Individual equipment items | Scope (N:1) |
| `cr950_tasks` | Work items within scope | Scope (N:1) |
| `cr950_estimators` | Estimator documents | Client (N:1), Project (1:1) |
| `cr950_apparatustypemaster` | Equipment type catalog | Apparatus (N:1) |
| `cr950_employees` | RESA staff | Projects, Apparatus (assignments) |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-28 | JSwenson/Claude | Initial creation - established Business Unit/Client/Site split |
| 1.1 | 2025-11-28 | JSwenson | Added Scope → Site lookup in Dataverse |

---

*This document is the authoritative reference for RESA Power data model terminology and structure.*
