# [Table Name] Build Specification

**Version:** 1.0  
**Created:** [Date]  
**Author:** [Claude instance]  
**Status:** Draft / Review / Approved / Deployed

---

## Overview

**Table Display Name:** [Name]  
**Table Logical Name:** cr950_[name]  
**EntitySetName:** cr950_[plural]  
**Purpose:** [One sentence description]

---

## Fields

### Primary Fields

| Display Name | Logical Name | Type | Required | Notes |
|--------------|--------------|------|----------|-------|
| Name | cr950_name | Text (100) | Yes | Primary field |
| | cr950_ | | | |

### Lookup Fields

| Display Name | Logical Name | Target Table | Required | Notes |
|--------------|--------------|--------------|----------|-------|
| | cr950_ | cr950_ | | |

### Status/Choice Fields

| Display Name | Logical Name | Options | Default | Notes |
|--------------|--------------|---------|---------|-------|
| | cr950_ | | | |

### Calculated Fields

| Display Name | Logical Name | Formula | Notes |
|--------------|--------------|---------|-------|
| | cr950_ | | |

### Rollup Fields

| Display Name | Logical Name | Source | Aggregation | Filter | Notes |
|--------------|--------------|--------|-------------|--------|-------|
| | cr950_ | | SUM/COUNT/MIN/MAX | | |

### Money Fields

| Display Name | Logical Name | Precision | Notes |
|--------------|--------------|-----------|-------|
| | cr950_ | 2 | |

### Date Fields

| Display Name | Logical Name | Format | Notes |
|--------------|--------------|--------|-------|
| | cr950_ | Date Only / Date Time | |

---

## Relationships

### Parent Tables (Many-to-One)

| Related Table | Lookup Field | Required | Cascade |
|---------------|--------------|----------|---------|
| cr950_ | cr950_ | | |

### Child Tables (One-to-Many)

| Related Table | Lookup Field | Notes |
|---------------|--------------|-------|
| cr950_ | | |

---

## Business Rules

1. **Rule Name:** [Description]
   - Trigger: [When this runs]
   - Condition: [If condition]
   - Action: [What happens]

---

## Forms

### Main Form
- Tabs: [List]
- Key sections: [List]

### Quick Create Form
- Fields: [List]

---

## Views

| View Name | Type | Filter | Columns |
|-----------|------|--------|---------|
| Active [Table] | Default | statecode = 0 | |
| All [Table] | All | None | |

---

## Security

| Role | Create | Read | Update | Delete |
|------|--------|------|--------|--------|
| System Admin | ✅ | ✅ | ✅ | ✅ |
| PM | ✅ | ✅ | ✅ | ❌ |
| Technician | ❌ | ✅ | ✅ | ❌ |

---

## Test Cases

| # | Scenario | Expected Result | Status |
|---|----------|-----------------|--------|
| 1 | | | ⚪ |
| 2 | | | ⚪ |

---

## Deployment Checklist

- [ ] Table created in Dataverse
- [ ] All fields added with correct types
- [ ] Relationships configured
- [ ] Business rules created
- [ ] Forms customized
- [ ] Views created
- [ ] Security roles assigned
- [ ] Test cases executed
- [ ] Documentation updated

---

*Specification maintained per SESSION_PROTOCOL.md*
