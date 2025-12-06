# Supabase Swap Guide for VS Code Claude

**Purpose**: Step-by-step instructions to connect the Next.js app to Supabase  
**Created**: 2025-12-05 by Desktop Claude  
**Priority**: HIGH - Do this first

---

## Overview

**Current State**: App connects to Dataverse via MSAL + `src/lib/dataverse.ts`  
**Target State**: App connects to Supabase via `src/lib/supabase.ts`

**Estimated Time**: 30-45 minutes

---

## Prerequisites

Before starting, confirm you have:
- [ ] Access to `C:\Users\jjswe\Projects\resa-web-app`
- [ ] Terminal/command line access
- [ ] Supabase anon key (get from dashboard or SUPABASE_CREDENTIALS.md)

**Supabase Credentials Location**: `C:\RESA_Power_Build\.secrets\SUPABASE_CREDENTIALS.md`

---

## Step 1: Install Supabase JS Client

```bash
cd C:\Users\jjswe\Projects\resa-web-app
npm install @supabase/supabase-js
```

**Verify**: Check package.json includes `"@supabase/supabase-js": "^2.x.x"`

---

## Step 2: Copy Supabase Client Library

**Source**: `C:\RESA_Power_Build\Supabase\lib\supabase.ts`  
**Destination**: `C:\Users\jjswe\Projects\resa-web-app\src\lib\supabase.ts`

This file contains:
- Supabase client initialization
- All CRUD functions matching Dataverse patterns
- Dashboard view queries
- PSS Portal functions (for later)

---

## Step 3: Add Environment Variables

Edit `C:\Users\jjswe\Projects\resa-web-app\.env.local`

**Add these lines** (keep existing MSAL vars for now):

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://fxoyniqnrlkxfligbxmg.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<get from SUPABASE_CREDENTIALS.md>
```

**Note**: The anon key is in `C:\RESA_Power_Build\.secrets\SUPABASE_CREDENTIALS.md`

---

## Step 4: Update Main Page

Edit `C:\Users\jjswe\Projects\resa-web-app\src\app\page.tsx`

### 4a. Change Imports

**Find** (near top of file):
```typescript
import { dataverse } from '@/lib/dataverse'
```

**Replace with**:
```typescript
import { getProjects, getProjectDashboard } from '@/lib/supabase'
```

### 4b. Update Data Fetching

The Dataverse client used a class pattern. Supabase uses direct functions.

**Dataverse pattern** (old):
```typescript
const projects = await dataverse.getProjects()
```

**Supabase pattern** (new):
```typescript
const projects = await getProjects()
```

### 4c. Handle Response Shape Differences

**Dataverse returns**: `{ value: [...], '@odata.count': N }`  
**Supabase returns**: `[...]` (direct array)

**Example conversion**:
```typescript
// OLD (Dataverse)
const response = await dataverse.getProjects()
const projects = response.value

// NEW (Supabase)
const projects = await getProjects()
// Already an array, no .value needed
```

---

## Step 5: Update Dashboard Page

Edit `C:\Users\jjswe\Projects\resa-web-app\src\app\dashboard\page.tsx`

Apply same patterns as Step 4:
1. Update imports
2. Change function calls
3. Adjust response handling

**Bonus**: Use the pre-built dashboard view:
```typescript
import { getProjectDashboard } from '@/lib/supabase'

// This returns aggregated data - total hours, completion %, etc.
const dashboardData = await getProjectDashboard()
```

---

## Step 6: Test the Connection

### 6a. Start the Dev Server

```bash
cd C:\Users\jjswe\Projects\resa-web-app
npm run dev
```

### 6b. Open Browser

Go to `http://localhost:3000`

### 6c. Check Console

Open browser DevTools (F12) → Console tab

**Expected**: No Supabase errors  
**If Error**: Check env variables are set correctly

### 6d. Verify Data

You should see:
- LASNAP16 project (from test data)
- 4 scopes (IPS, NWWRP, GWRP, SEWRP)
- 47 apparatus items

---

## Step 7: Test Key Functions

### Test 1: Project List
- Navigate to home/dashboard
- Verify projects display
- Check project stats (if shown)

### Test 2: Scope Drill-down (if page exists)
- Click a project
- Verify scopes load
- Check apparatus counts

### Test 3: Apparatus Update (if page exists)
- Find an apparatus
- Change status to "COMPLETE"
- Verify it saves
- Check if revenue record was created (trigger test)

---

## Field Name Mapping Reference

When updating components, use this mapping:

| Dataverse Field | Supabase Column | Notes |
|-----------------|-----------------|-------|
| `cr950_projectname` | `name` | |
| `cr950_projectnumber` | `project_number` | |
| `cr950_status` | `status` | |
| `cr950_projecttype` | `project_type` | |
| `_cr950_client_value` | `client_id` | FK |
| `cr950_scopename` | `scope_name` | |
| `cr950_completion_status` | `completion_status` | ENUM |
| `cr950_labor_hours` | `quoted_hours` | |
| `cr950_actual_hours` | `actual_hours` | |
| `cr950_apparatus_assessment` | `assessment` | ENUM |

---

## Common Issues & Solutions

### Issue: "Invalid API key"
**Solution**: Check NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local

### Issue: "relation does not exist"
**Solution**: Table name might be wrong. Use exact names: `projects`, `scopes`, `apparatus`

### Issue: "TypeError: response.value is undefined"
**Solution**: Supabase returns arrays directly, not `{value: []}`. Remove `.value`

### Issue: "CORS error"
**Solution**: Shouldn't happen with Supabase. Check URL is correct.

### Issue: MSAL still trying to authenticate
**Solution**: For now, you can comment out MSAL provider in layout.tsx or keep it (it won't conflict with Supabase)

---

## What to Keep vs Remove

### Keep (for now):
- MSAL config files (may use later for SSO)
- Dataverse types (reference for field names)
- Existing page layouts and UI components

### Remove/Replace:
- Direct calls to `dataverse.getX()` functions
- OData query patterns
- Bearer token handling (Supabase handles auth internally)

---

## After Completing This Guide

1. **Update COORDINATION.md** with completion status
2. **Test all existing pages** to ensure they work
3. **Note any pages that need more work**
4. **Inform Desktop Claude** what's working/broken

---

## Next Steps After Swap

Once connected, we can:
1. Import real project data (Garney 677562)
2. Build Field Tech views from the spec
3. Add real-time subscriptions for live updates
4. Enable Supabase Auth when ready

---

## Questions?

If anything is unclear or you hit a blocker:
1. Update COORDINATION.md with the issue
2. Desktop Claude will see it next session
3. Or ask the user to relay the question

---

**Document Owner**: Desktop Claude  
**For**: VS Code Claude  
**Status**: Ready to execute
