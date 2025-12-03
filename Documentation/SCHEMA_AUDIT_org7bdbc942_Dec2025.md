# RESA Power Dataverse Schema Audit

**Environment:** org7bdbc942.crm.dynamics.com  
**Audit Date:** December 2, 2025  
**Publisher Prefix:** cr950_  
**Auditor:** Claude AI Assistant  

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Tables Expected (per spec)** | 16 |
| **Tables Found** | 9 |
| **Tables Missing** | 7 |
| **Records in System** | 5 |
| **Relationships Verified** | 5/5 ✅ |

**Overall Status:** ⚠️ **PARTIAL DEPLOYMENT** - Core tables exist but financial/resource tables missing

---

## 🏗️ Table Inventory

### ✅ Tables That EXIST (9 Tables)

| EntitySetName | Display Name | Records | Status |
|---------------|--------------|---------|--------|
| `cr950_clients` | Clients | 1 | ✅ Active |
| `cr950_sites` | Sites | 1 | ✅ Active |
| `cr950_projects` | Projects | 1 | ✅ Active |
| `cr950_scopes` | Scopes | 1 | ✅ Active |
| `cr950_scopelabordetails` | Scope Labor Details | 1 | ✅ Active |
| `cr950_tasks` | Tasks | 0 | ✅ Empty |
| `cr950_apparatuses` | Apparatus | 0 | ✅ Empty |
| `cr950_estimators` | Estimators | 1 | ✅ Active |
| `cr950_locations` | Locations | 0 | ✅ Empty |

### ❌ Tables NOT FOUND (7 Tables)

| Expected Table | Purpose | Priority |
|----------------|---------|----------|
| `cr950_apparatusrevenues` | Revenue recognition records | 🔴 CRITICAL |
| `cr950_apparatustypemasters` | NETA standard hours lookup | 🔴 CRITICAL |
| `cr950_employees` | Workforce/technician data | 🟡 HIGH |
| `cr950_quotes` | Pre-project estimates | 🟡 HIGH |
| `cr950_resourceassignments` | Employee-Project assignments | 🟢 MEDIUM |
| `cr950_equipment` | Test equipment tracking | 🟢 MEDIUM |
| `cr950_businessunits` | Location/BU hierarchy | 🟢 MEDIUM |

---

## 🔗 Relationship Verification

### Verified Lookups (All Working ✅)

| Parent Table | Child Table | Lookup Field | Status |
|--------------|-------------|--------------|--------|
| Client | Site | `_cr950_siteclient_value` | ✅ Verified |
| Client | Project | `_cr950_projectclient_value` | ✅ Verified |
| Site | Project | `_cr950_projectsite_value` | ✅ Verified |
| Client | Scope | `_cr950_scope_clientid_value` | ✅ Verified |
| Site | Scope | `_cr950_scope_siteid_value` | ✅ Verified |
| Project | Scope | `_cr950_scopeproject_value` | ✅ Verified |
| Scope | ScopeLaborDetail | `_cr950_scopelaborscope_value` | ✅ Verified |
| Client | Estimator | `_cr950_estimator_clientid_value` | ✅ Verified |

### ⚠️ Unverified Relationships (Empty Tables)

| Parent | Child | Expected Lookup | Cannot Verify |
|--------|-------|-----------------|---------------|
| Scope | Task | `_cr950_task_scope_value` | No Task records |
| Task | Apparatus | `_cr950_apparatus_task_value` | No Apparatus records |

---

## 📋 Detailed Field Schemas

### Table: cr950_clients

| Field Name | Data Type | Sample Value | Required |
|------------|-----------|--------------|----------|
| `cr950_clientid` | GUID (PK) | e80b1ddb-96cf-f011-bbd2-0022480b1662 | Auto |
| `cr950_clientname` | Text | "Garney" | Yes |
| `cr950_clientcode` | Text | (null) | No |
| `cr950_clientemail` | Text | (null) | No |
| `cr950_clientphone` | Text | (null) | No |
| `cr950_clientaddress` | Text | (null) | No |
| `cr950_clientcity` | Text | (null) | No |
| `cr950_clientstate` | Text | (null) | No |
| `cr950_clientzip` | Text | (null) | No |
| `cr950_clientcountry` | Text | (null) | No |
| `cr950_clientwebsite` | Text | (null) | No |
| `cr950_clientactive` | Boolean | (null) | No |
| `cr950_clientnotes` | Text | (null) | No |

---

### Table: cr950_sites

| Field Name | Data Type | Sample Value | Required |
|------------|-----------|--------------|----------|
| `cr950_siteid` | GUID (PK) | 0ed8dad2-a4cf-f011-bbd2-0022480b1662 | Auto |
| `cr950_sitename` | Text | "Central Mesa Reuse Plant" | Yes |
| `cr950_sitecode` | Text | (null) | No |
| `cr950_siteaddress` | Text | "3626 E. Thomas Road" | No |
| `cr950_sitecity` | Text | "Mesa" | No |
| `cr950_sitestate` | Text | "AZ" | No |
| `cr950_sitezip` | Text | "85213" | No |
| `cr950_sitecountry` | Text | (null) | No |
| `cr950_sitecontactname` | Text | "Terry Huston" | No |
| `cr950_sitecontactemail` | Text | "terry.huston@garney.com" | No |
| `cr950_sitecontactphone` | Text | (null) | No |
| `cr950_siteactive` | Boolean | True | No |
| `cr950_sitenotes` | Text | (null) | No |
| `_cr950_siteclient_value` | Lookup→Client | e80b1ddb-96cf-... | Yes |

---

### Table: cr950_projects

| Field Name | Data Type | Sample Value | Required |
|------------|-----------|--------------|----------|
| `cr950_projectid` | GUID (PK) | 0fd8dad2-a4cf-f011-bbd2-0022480b1662 | Auto |
| `cr950_projectname` | Text | "Central Mesa Reuse Plant" | Yes |
| `cr950_projectnumber` | Text | "677562" | Yes |
| `cr950_projectdescription` | Text | (null) | No |
| `cr950_projectstatus` | Choice | (null) | No |
| `cr950_projectstartdate` | DateTime | 2025-11-17T00:00:00Z | No |
| `cr950_projectenddate` | DateTime | (null) | No |
| `cr950_projectponumber` | Text | (null) | No |
| `cr950_projectcontractvalue` | Money | (null) | No |
| `cr950_project_lead` | Text | "Phillip Pentecost" | No |
| `cr950_project_business_unit` | Text | (null) | No |
| `cr950_project_quote_date` | DateTime | (null) | No |
| `cr950_project_quote_revision` | Text | (null) | No |
| `cr950_projectactive` | Boolean | True | No |
| `cr950_projectnotes` | Text | (null) | No |
| `_cr950_projectclient_value` | Lookup→Client | e80b1ddb-96cf-... | Yes |
| `_cr950_projectsite_value` | Lookup→Site | 0ed8dad2-a4cf-... | Yes |
| `_cr950_project_locationid_value` | Lookup→Location | (null) | No |

---

### Table: cr950_scopes

| Field Name | Data Type | Sample Value | Required |
|------------|-----------|--------------|----------|
| `cr950_scopeid` | GUID (PK) | 10d8dad2-a4cf-f011-bbd2-0022480b1662 | Auto |
| `cr950_scopename` | Text | "IPS NETA ATS" | Yes |
| `cr950_scopenumber` | Integer | 1 | No |
| `cr950_scopetype` | Choice/Text | "ATS" | Yes |
| `cr950_scopedescription` | Text | (null) | No |
| `cr950_scopestatus` | Choice | (null) | No |
| `cr950_scopeduedate` | DateTime | (null) | No |
| `cr950_scopelabortotal` | Money | (null) | No |
| `cr950_scopematerialtotal` | Money | (null) | No |
| `cr950_scoperevenuetotal` | Money | (null) | No |
| `cr950_scopemarginpercent` | Decimal | (null) | No |
| `cr950_scopeactive` | Boolean | True | No |
| `cr950_scopenotes` | Text | (null) | No |
| `_cr950_scopeproject_value` | Lookup→Project | 0fd8dad2-a4cf-... | Yes |
| `_cr950_scope_siteid_value` | Lookup→Site | 0ed8dad2-a4cf-... | No |
| `_cr950_scope_clientid_value` | Lookup→Client | e80b1ddb-96cf-... | No |

**Note:** `cr950_scopetype` stores ATS/MTS as text value "ATS" rather than option set code.

---

### Table: cr950_scopelabordetails

| Field Name | Data Type | Sample Value | Required |
|------------|-----------|--------------|----------|
| `cr950_scopelabordetailid` | GUID (PK) | 11d8dad2-a4cf-f011-bbd2-0022480b1662 | Auto |
| `cr950_scopelaborname` | Text | "IPS NETA ATS - Labor Details" | Yes |
| `cr950_scopelabortotalhours` | Decimal | 333.75 | No |
| `cr950_scopelaborquotedamount` | Money | 61,025.63 | No |
| `cr950_scopelaboreffectiverate` | Money | 182.85 | No |
| `cr950_scopelaboronsitetotal` | Money | 57,822.19 | No |
| `cr950_scopelaboroffsitetotal` | Money | 2,753.44 | No |
| `cr950_scopelabortraveltotal` | Money | 0.00 | No |
| `cr950_scopelaboroutsidetotal` | Money | 450.00 | No |
| `cr950_scopelabormultiplier` | Decimal | 1.0 | No |
| `cr950_scopelaboronsiterate` | Money | (null) | No |
| `cr950_scopelaboroffsiterate` | Money | (null) | No |
| `cr950_scopelabortravelrate` | Money | (null) | No |
| `cr950_scopelaboroutsiderate` | Money | (null) | No |
| `cr950_scopelaborsumofrates` | Money | (null) | No |
| `cr950_scopelaboradjusted` | Money | (null) | No |
| `cr950_scopelabornotadjusted` | Money | (null) | No |
| `cr950_scopelaborsource` | Text | (null) | No |
| `cr950_scopelaboractive` | Boolean | True | No |
| `cr950_scopelabornotes` | Text | (null) | No |
| `_cr950_scopelaborscope_value` | Lookup→Scope | 10d8dad2-a4cf-... | Yes |

---

### Table: cr950_estimators

| Field Name | Data Type | Sample Value | Required |
|------------|-----------|--------------|----------|
| `cr950_estimatorid` | GUID (PK) | 6e13b771-99cf-f011-bbd2-0022480b1662 | Auto |
| `cr950_estimator_name` | Text | (null) | No |
| `cr950_estimator_filename` | Text | "Garney - Central Mesa Reuse _20251128_Rev1.xlsm" | Yes |
| `cr950_estimator_fileurl` | URL | "https://jswensonllc.sharepoint.com/..." | No |
| `cr950_estimator_projectname` | Text | "Central Mesa Reuse" | No |
| `cr950_estimator_estimatedate` | DateTime | 2025-12-02T16:16:00Z | No |
| `cr950_estimator_currentrevision` | Integer | 2 | No |
| `cr950_estimator_totalamount` | Money | (null) | No |
| `cr950_estimator_scopecount` | Integer | (null) | No |
| `cr950_estimator_scopejson` | Text (Multi) | (null) | No |
| `cr950_estimator_convertedtoproject` | Boolean | False | No |
| `cr950_estimator_converteddate` | DateTime | (null) | No |
| `cr950_estimator_lastmodified` | DateTime | (null) | No |
| `cr950_estimator_extractedat` | DateTime | (null) | No |
| `cr950_estimator_notes` | Text | (null) | No |
| `_cr950_estimator_clientid_value` | Lookup→Client | e80b1ddb-96cf-... | No |
| `_cr950_estimator_projectid_value` | Lookup→Project | (null) | No |
| `_cr950_estimator_locationid_value` | Lookup→Location | (null) | No |

---

## 🔴 CRITICAL GAPS

### 1. ApparatusRevenue Table MISSING

**Impact:** Cannot perform automated revenue recognition  
**Required Action:** Deploy ApparatusRevenue table with fields:
- Revenue amount
- Apparatus lookup
- Scope lookup
- ScopeLaborDetail lookup
- Revenue status
- Recognition date

### 2. ApparatusTypeMaster Table MISSING

**Impact:** Cannot look up NETA standard hours per apparatus type  
**Required Action:** Deploy ApparatusTypeMaster table with:
- Apparatus type name
- ATS hours
- MTS hours
- Section reference

### 3. Tasks Table Empty (No Schema Verification Possible)

**Expected Fields:**
- Task name
- Task number
- Scope lookup (required)
- Task status
- Task type

### 4. Apparatus Table Empty (No Schema Verification Possible)

**Expected Required Field:**
- `_cr950_apparatus_task_value` (Lookup to Task)

---

## ⚠️ DISCREPANCIES FROM EXPECTED SCHEMA

| Category | Expected | Actual | Impact |
|----------|----------|--------|--------|
| Scope Type Field | Option Set (ATS=0, MTS=1) | Text ("ATS") | Low - Works but inconsistent |
| Location vs BusinessUnit | BusinessUnit table | Location table | Naming change only |
| Primary Key naming | `cr950_projectsid` | `cr950_projectid` | V2 schema (correct) |
| EntitySet naming | `cr950_projectses` | `cr950_projects` | V2 schema (correct) |

---

## 📝 MCP Server Configuration Update Required

Update `C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp\server.js` ENTITY_MAP:

```javascript
const ENTITY_MAP = {
  // Core tables (V2 naming)
  'projects': 'cr950_projects',
  'clients': 'cr950_clients',
  'sites': 'cr950_sites',
  'scopes': 'cr950_scopes',
  'tasks': 'cr950_tasks',
  'apparatus': 'cr950_apparatuses',
  'scopelabordetails': 'cr950_scopelabordetails',
  'estimators': 'cr950_estimators',
  'locations': 'cr950_locations',
  
  // NOT DEPLOYED YET - Will fail until added:
  // 'apparatusrevenue': 'cr950_apparatusrevenues',
  // 'apparatustypemaster': 'cr950_apparatustypemasters',
  // 'employees': 'cr950_employees',
};
```

---

## ✅ RECOMMENDATIONS

### Immediate Actions (P0)

1. **Deploy ApparatusRevenue table** - Critical for billing workflow
2. **Deploy ApparatusTypeMaster table** - Critical for NETA hours lookup
3. **Verify Task→Scope relationship** - Required for apparatus hierarchy
4. **Verify Apparatus→Task lookup** - Required field for apparatus creation

### Short-Term Actions (P1)

5. **Add Employee table** - For technician assignment tracking
6. **Add Quote table** - For estimate-to-project conversion
7. **Standardize cr950_scopetype** - Consider converting to Option Set

### Nice-to-Have (P2)

8. **Add Equipment table** - For test equipment tracking
9. **Add ResourceAssignment table** - For project staffing

---

## 📊 Comparison: Expected vs Actual

| Table | In Spec | In Environment | Match |
|-------|---------|----------------|-------|
| Client | ✅ | ✅ | ✅ |
| Site | ✅ | ✅ | ✅ |
| Project | ✅ | ✅ | ✅ |
| Scope | ✅ | ✅ | ✅ |
| ScopeLaborDetail | ✅ | ✅ | ✅ |
| Task | ✅ | ✅ | ✅ |
| Apparatus | ✅ | ✅ | ✅ |
| ApparatusRevenue | ✅ | ❌ | ❌ MISSING |
| ApparatusTypeMaster | ✅ | ❌ | ❌ MISSING |
| Estimator | ✅ | ✅ | ✅ |
| Location | ❓ | ✅ | NEW |
| BusinessUnit | ✅ | ❌ | Replaced by Location |
| Employee | ✅ | ❌ | ❌ MISSING |
| Quote | ✅ | ❌ | ❌ MISSING |
| Equipment | ✅ | ❌ | ❌ MISSING |
| ResourceAssignment | ✅ | ❌ | ❌ MISSING |

---

**Audit Complete**  
*Generated: December 2, 2025*  
*Environment: org7bdbc942.crm.dynamics.com*
