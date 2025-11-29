# MCP SERVER FIX - QUICK CHECKLIST
## 30-Minute Express Guide

**Created:** November 23, 2025  
**Time Required:** 1.5 hours (or 30 min if you know what you're doing)  
**Servers to Fix:** 2

---

## ⚡ EXPRESS FIX - resa-docs (20 minutes)

### **Quick Steps:**

```bash
# 1. Navigate to server
cd C:\RESA_Power_Build\MCP_Servers\resa-docs-mcp

# 2. Create templates folder
mkdir build\templates

# 3. Create 4 template files (see full guide for content)
# - table-documentation.hbs
# - erd-diagram.hbs  
# - user-guide.hbs
# - api-docs.hbs

# 4. Rebuild
npm run build

# 5. Restart Claude Desktop and test
```

**Files to Create:** See `MCP_TROUBLESHOOTING_GUIDE.md` for full template contents

**Test Command in Claude Desktop:**
```
Generate table documentation for cr950_projects
```

---

## ⚡ EXPRESS FIX - resa-dataverse-dev (30 minutes)

### **Quick Diagnosis:**

The issue is likely **table name format**. Dataverse OData requires plural form (EntitySetName).

**Wrong:** `cr950_projects`  
**Right:** `cr950_projectses`

### **Quick Fix Option 1: Just Use Correct Names (5 min)**

Test in Claude Desktop with correct table names:

```
Query the cr950_projectses table (note the 'es' suffix)
Query the cr950_apparatuses table
Query the cr950_projectscopes table
```

**If this works → Problem solved! No code changes needed.**

---

### **Quick Fix Option 2: Update Code (30 min)**

If Option 1 doesn't work, update the code:

```bash
cd C:\RESA_Power_Build\MCP_Servers\resa-dataverse-dev
code src\index.ts
```

**Find and fix the query function** - make `select` parameter optional and improve OData URL building.

See `MCP_TROUBLESHOOTING_GUIDE.md` Section 2, Step 3 for exact code.

**After changes:**
```bash
npm run build
# Restart Claude Desktop
# Test queries
```

---

## 📋 FULL REFERENCE

**For complete step-by-step instructions with code samples:**
👉 `C:\RESA_Power_Build\Documentation\06_Implementation_Guides\MCP_TROUBLESHOOTING_GUIDE.md`

**Contains:**
- ✅ Complete template file contents (copy/paste ready)
- ✅ Exact code changes for resa-dataverse-dev
- ✅ Table name reference (all 14 tables)
- ✅ Testing procedures
- ✅ Success criteria

---

## ✅ QUICK SUCCESS CHECK

**resa-docs fixed when:**
- [ ] 4 .hbs files exist in `build\templates\`
- [ ] `npm run build` succeeds
- [ ] Can generate docs in Claude Desktop
- [ ] No "ENOENT" errors

**resa-dataverse-dev fixed when:**
- [ ] Can query `cr950_projectses` table
- [ ] Can query `systemusers` table  
- [ ] No 400 errors
- [ ] Returns actual records

---

## 🎯 AFTER BOTH FIXED

**You'll have:**
- ✅ 4 out of 4 Dataverse MCP servers operational
- ✅ Can generate documentation automatically
- ✅ Can query any Dataverse table
- ✅ Can validate rollup fields
- ✅ Can manage solution deployments

**Total Value:** All critical infrastructure for Weeks 1-5 complete!

---

**Quick Checklist Version:** 1.0  
**Full Guide:** MCP_TROUBLESHOOTING_GUIDE.md  
**Time Saved:** This checklist gets you to the fix in 5 minutes instead of reading 20 pages

