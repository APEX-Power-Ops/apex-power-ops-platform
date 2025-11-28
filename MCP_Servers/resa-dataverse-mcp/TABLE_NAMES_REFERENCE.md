# Dataverse Table Names Reference
## RESA Power Project Tracker - Correct OData Table Names

**Created:** November 23, 2025  
**Purpose:** Quick reference for querying Dataverse tables via MCP  
**Environment:** org99cd6c6e (Dev)

---

## ⚠️ CRITICAL: Use Plural EntitySetNames

Dataverse OData API requires **EntitySetName** (plural), not Entity Logical Name (singular).

**❌ WRONG:**
```javascript
query_dataverse("cr950_projects", ...)  // 404 Error!
```

**✅ CORRECT:**
```javascript
query_dataverse("cr950_projectses", ...)  // Works!
```

---

## 📋 RESA Power Tables (Alphabetical)

| Display Name | ❌ Singular (DON'T USE) | ✅ Plural (USE THIS!) |
|--------------|--------------------------|------------------------|
| Apparatus | `cr950_apparatus` | `cr950_apparatuses` |
| Apparatus Revenue | `cr950_apparatusrevenue` | `cr950_apparatusrevenues` |
| Apparatus Type Master | `cr950_apparatustypemaster` | `cr950_apparatustypemasters` |
| Business Unit | `cr950_businessunit` | `cr950_businessunits` |
| Client | `cr950_client` | `cr950_clients` |
| Employee | `cr950_employee` | `cr950_employees` |
| Equipment | `cr950_equipment` | `cr950_equipments` |
| Project Financial Summary | `cr950_projectfinancialsummary` | `cr950_projectfinancialsummaries` |
| Projects | `cr950_projects` | `cr950_projectses` |
| Project Scope | `cr950_projectscope` | `cr950_projectscopes` |
| Quote | `cr950_quote` | `cr950_quotes` |
| Resource Assignment | `cr950_resourceassignment` | `cr950_resourceassignments` |
| Scope Financial Summary | `cr950_scopefinancialsummary` | `cr950_scopefinancialsummaries` |
| Scope Labor Detail | `cr950_scopelabordetail` | `cr950_scopelabordetails` |
| Site | `cr950_site` | `cr950_sites` |
| Tasks | `cr950_tasks` | `cr950_taskses` |

---

## 🔍 Common System Tables

| Table | EntitySetName | Description |
|-------|---------------|-------------|
| Users | `systemusers` | System users |
| Teams | `teams` | Security teams |
| Business Units | `businessunits` | Organizational structure |
| Solutions | `solutions` | Installed solutions |

---

## 💻 Query Examples

### ✅ Correct Queries

```javascript
// Query projects
query_dataverse(
  "cr950_projectses",
  "$select=cr950_projectsid,cr950_name,cr950_projectnumber",
  "$filter=statecode eq 0",
  10
)

// Query apparatus
query_dataverse(
  "cr950_apparatuses",
  "$select=cr950_designation,cr950_completionstatus",
  "$filter=cr950_completionstatus ne null",
  50
)

// Query tasks
query_dataverse(
  "cr950_taskses",
  "$select=cr950_tasksid,cr950_name",
  null,
  25
)
```

### ❌ Common Mistakes

```javascript
// These will all return 404 errors:
query_dataverse("cr950_projects", ...)     // Wrong!
query_dataverse("cr950_apparatus", ...)    // Wrong!
query_dataverse("cr950_tasks", ...)        // Wrong!
```

---

## 🧪 Testing Table Names

Use this diagnostic script to test any table name:

```bash
cd C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp

# Set credentials (get secret from .env file)
$env:AZURE_TENANT_ID='270d5723-4b30-4f3b-b9cb-6527be741b42'
$env:AZURE_CLIENT_ID='9df3350f-b3b4-47c4-97b5-499a8b02acc7'
$env:AZURE_CLIENT_SECRET=$env:AZURE_CLIENT_SECRET  # Load from .env

# Run test
node test-connection.js
```

**Output shows which table names work** ✅ vs fail ❌

---

## 📝 Naming Pattern

Dataverse pluralization follows these rules:

| Singular Ending | Plural Form | Example |
|-----------------|-------------|---------|
| Ends in `s` | Add `es` | `cr950_projects` → `cr950_projectses` |
| Ends in `us` | Change to `uses` | `cr950_apparatus` → `cr950_apparatuses` |
| Most others | Add `s` | `cr950_client` → `cr950_clients` |

**When in doubt:** Use the test script or check Power Apps → Tables → [Table] → Properties → "Plural name"

---

## 🚨 Troubleshooting

### Error: "Resource not found for the segment..."

**Cause:** Using singular form instead of plural

**Solution:** Add `es` or `s` to the table name

**Example:**
```
❌ cr950_projects → 404 Error
✅ cr950_projectses → Success!
```

### Error: "400 Bad Request"

**Possible causes:**
1. Invalid $filter syntax
2. Field name doesn't exist
3. Incorrect data type in filter

**Debug:** Run test-connection.js to verify table name works first

---

## 📚 Additional Resources

- **Power Apps Maker Portal:** https://make.powerapps.com
  - Tables → [Table Name] → Properties → See "Plural name"
  
- **Dataverse Web API Reference:**
  - https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/query-data-web-api

- **Test Script:** `C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp\test-connection.js`

---

**Document Version:** 1.0  
**Last Updated:** November 23, 2025  
**Maintained by:** RESA Power Build Team
