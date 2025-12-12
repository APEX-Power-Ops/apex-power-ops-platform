# resa-dataverse-mcp

**Direct Dataverse CRUD Operations via MCP**

Query, create, update, and delete records in Microsoft Dataverse (Power Apps) directly from Claude Desktop.

---

## ✅ Status: OPERATIONAL

**Last Tested:** November 23, 2025  
**Environment:** org99cd6c6e (Dev)  
**Authentication:** ✅ Working  
**All Tools:** ✅ Functional

---

## 🎯 Purpose

Core MCP server for direct Dataverse operations:
- Query records with OData syntax
- Create new records
- Update existing records
- Delete records

**Use Cases:**
- Querying RESA Power data
- Testing rollup field calculations
- Data validation
- CRUD operations during development

---

## 🔧 Tools Available

| Tool | Purpose | Status |
|------|---------|--------|
| `query_dataverse` | Query records with OData | ✅ Working |
| `create_record` | Create new records | ✅ Working |
| `update_record` | Update existing records | ✅ Working |
| `delete_record` | Delete records | ✅ Working |

---

## 📋 Configuration

### Environment Variables

```bash
DATAVERSE_URL=https://org99cd6c6e.crm.dynamics.com
AZURE_TENANT_ID=270d5723-4b30-4f3b-b9cb-6527be741b42
AZURE_CLIENT_ID=9df3350f-b3b4-47c4-97b5-499a8b02acc7
AZURE_CLIENT_SECRET=<your-secret-here>  # See .env.example
ENVIRONMENT=DEVELOPMENT
```

### Claude Desktop Config

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "resa-dataverse": {
      "command": "node",
      "args": ["C:\\RESA_Power_Build\\MCP_Servers\\resa-dataverse-mcp\\build\\index.js"],
      "env": {
        "DATAVERSE_URL": "https://org99cd6c6e.crm.dynamics.com",
        "AZURE_TENANT_ID": "270d5723-4b30-4f3b-b9cb-6527be741b42",
        "AZURE_CLIENT_ID": "9df3350f-b3b4-47c4-97b5-499a8b02acc7",
        "AZURE_CLIENT_SECRET": "<see .env file>",
        "ENVIRONMENT": "DEVELOPMENT"
      }
    }
  }
}
```

---

## 🚀 Usage Examples

### Query Records

```
Query the cr950_projectses table, select name and project number
```

**Behind the scenes:**
```javascript
query_dataverse(
  "cr950_projectses",
  "$select=cr950_name,cr950_projectnumber",
  null,
  50
)
```

### Create Record

```
Create a new apparatus record with designation "T-001" and status "Not Started"
```

### Update Record

```
Update apparatus record {id} to set completion status to "Complete"
```

### Delete Record

```
Delete the test apparatus record {id}
```

---

## ⚠️ CRITICAL: Table Name Format

Dataverse requires **plural EntitySetNames**, not singular entity names.

**❌ WRONG:**
```
query_dataverse("cr950_projects", ...)  // 404 Error!
query_dataverse("cr950_apparatus", ...) // 404 Error!
```

**✅ CORRECT:**
```
query_dataverse("cr950_projectses", ...)   // Works!
query_dataverse("cr950_apparatuses", ...)  // Works!
```

**📖 Full Reference:** See [`TABLE_NAMES_REFERENCE.md`](./TABLE_NAMES_REFERENCE.md)

---

## 🧪 Testing

### Quick Connection Test

```bash
cd C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp

# Set credentials (from .env file)
$env:AZURE_TENANT_ID='270d5723-4b30-4f3b-b9cb-6527be741b42'
$env:AZURE_CLIENT_ID='9df3350f-b3b4-47c4-97b5-499a8b02acc7'
$env:AZURE_CLIENT_SECRET=$env:AZURE_CLIENT_SECRET  # Load from .env

# Run diagnostic
node test-connection.js
```

**Expected Output:**
```
✅ Token acquired successfully
✅ systemusers - Works
✅ cr950_projectses - Works
✅ cr950_apparatuses - Works
```

### Test in Claude Desktop

```
1. "Query systemusers table, return first record"
2. "Query cr950_projectses, select name and status"
3. "Query cr950_apparatuses, filter by completion status"
```

All should return results without errors.

---

## 🏗️ Build

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run build

# Test standalone
node build/index.js
```

---

## 📁 Project Structure

```
resa-dataverse-mcp/
├── src/
│   └── index.ts          # Main MCP server
├── build/
│   └── index.js          # Compiled output
├── test-connection.js    # Diagnostic script
├── TABLE_NAMES_REFERENCE.md  # Table name guide
├── package.json
├── tsconfig.json
└── README.md
```

---

## 🚨 Troubleshooting

### Error: "Resource not found for the segment..."

**Cause:** Using singular table name instead of plural

**Solution:** Check [`TABLE_NAMES_REFERENCE.md`](./TABLE_NAMES_REFERENCE.md)

```
❌ cr950_projects → ✅ cr950_projectses
❌ cr950_apparatus → ✅ cr950_apparatuses
```

### Error: "Authentication failed"

**Cause:** Missing or incorrect credentials

**Solution:** Verify environment variables match config above

### Error: "400 Bad Request"

**Cause:** Invalid OData syntax in $filter or $select

**Solution:** 
1. Test table name with `test-connection.js` first
2. Verify field names exist in Power Apps
3. Check OData filter syntax

---

## 🔒 Security

### Production Safeguard

Server includes built-in check to prevent accidental production access:

```typescript
if (ENVIRONMENT === "PRODUCTION" && DATAVERSE_URL.includes("org04ad071f")) {
  throw new Error("FATAL: Cannot connect MCP to RESA production!");
}
```

**Production URL blocked:** `org04ad071f.crm.dynamics.com`  
**Dev URL allowed:** `org99cd6c6e.crm.dynamics.com`

### Credential Security

- ✅ Credentials in Claude Desktop config (local machine only)
- ✅ Never commit credentials to Git
- ✅ `.env` files are gitignored
- ✅ App registration has Dev environment permissions only

---

## 📊 Integration with Other Servers

| Server | Uses resa-dataverse-mcp | Purpose |
|--------|------------------------|---------|
| resa-testing-mcp | ✅ Yes | Validation and testing |
| resa-deploy-mcp | ✅ Yes | Solution deployment |
| resa-docs-mcp | ✅ Yes | Schema documentation |

**Design:** `resa-dataverse-mcp` provides foundational CRUD; specialized servers add business logic.

---

## 📚 Related Documentation

- [TABLE_NAMES_REFERENCE.md](./TABLE_NAMES_REFERENCE.md) - Complete table name guide
- [test-connection.js](./test-connection.js) - Connection diagnostic script
- [MCP_ALL_SERVERS_BUILD_SPEC.md](../../Documentation/06_Implementation_Guides/MCP_ALL_SERVERS_BUILD_SPEC.md) - Full MCP architecture

---

## 📝 Change Log

**v1.0.0** - November 23, 2025
- ✅ Initial implementation
- ✅ 4 CRUD tools (query, create, update, delete)
- ✅ OAuth 2.0 token management
- ✅ Production safeguard
- ✅ Connection diagnostics
- ✅ Table names reference guide

---

**Maintained by:** RESA Power Build Team  
**Environment:** org99cd6c6e (Dev)  
**Status:** ✅ Production Ready
