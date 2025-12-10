# Desktop ↔ VS Code Claude Coordination

**Purpose**: Share information between Claude sessions  
**Updated**: 2025-12-05 23:15 by VS Code Claude

---

## 🎉 SUPABASE SWAP COMPLETE!

**Status**: ✅ App connected to Supabase and working!
**URL**: http://localhost:3000
**Data showing**: LASNAP16 project with 47 apparatus

---

## ✅ COMPLETED THIS SESSION

| Task | Owner | Status |
|------|-------|--------|
| Locate Node.js app | VS Code Claude | ✅ Found |
| Analyze app structure | VS Code Claude | ✅ Documented |
| Load test data (11) | VS Code Claude | ✅ LASNAP16 loaded |
| Fix trigger bug | VS Code Claude | ✅ Cascade rollup works |
| Review FIELD_TECH_APPLICATION_SPEC | Desktop Claude | ✅ |
| Review REVENUE_RECOGNITION_FLOW_SPEC_V2 | Desktop Claude | ✅ |
| Make architecture decisions | Desktop Claude | ✅ OPEN_DECISIONS.md |
| Create swap guide | Desktop Claude | ✅ SUPABASE_SWAP_GUIDE.md |
| **Install @supabase/supabase-js** | VS Code Claude | ✅ |
| **Copy supabase.ts client** | VS Code Claude | ✅ |
| **Add env variables** | VS Code Claude | ✅ |
| **Update page.tsx for Supabase** | VS Code Claude | ✅ |
| **Fix createClient naming conflict** | VS Code Claude | ✅ |
| **Test connection** | VS Code Claude | ✅ Working! |

---

## 🔄 WHAT'S WORKING NOW

- Dashboard loads at http://localhost:3000
- Shows "1 project loaded from Supabase"
- LASNAP16 project displays with correct data
- Stats cards show: 1 project, 1 in progress, 47 apparatus
- Client name (Louisiana Snap Foods) showing
- Status badge (Active/In Progress) working
- "Supabase Connected" badge in header

## ⚠️ ISSUES FOUND & FIXED

| Issue | Fix Applied |
|-------|-------------|
| `createClient` name conflict | Renamed to `createNewClient` in supabase.ts |

---

## 🔄 NEXT TASKS

### Desktop Claude - NEXT SESSION

| Priority | Task | Depends On |
|----------|------|------------|
| 1 | Create Garney migration script | VS Code confirms app works |
| 2 | Add AVAILABILITY field to schema | If needed for Excel import |
| 3 | Create dashboard SQL queries | After migration script |
| 4 | Document API patterns | After VS Code tests |

---

## 📍 KEY FILE LOCATIONS

### For VS Code Claude (App Development)
| Item | Location |
|------|----------|
| **App Root** | `C:\Users\jjswe\Projects\resa-web-app` |
| **Swap Guide** | `C:\RESA_Power_Build\.claude\SUPABASE_SWAP_GUIDE.md` |
| **Supabase Client** | `C:\RESA_Power_Build\Supabase\lib\supabase.ts` → copy to app |
| **Supabase Credentials** | `C:\RESA_Power_Build\.secrets\SUPABASE_CREDENTIALS.md` |
| **Decisions** | `C:\RESA_Power_Build\.claude\OPEN_DECISIONS.md` |

### For Desktop Claude (Data & Schema)
| Item | Location |
|------|----------|
| **Schema Files** | `C:\RESA_Power_Build\Supabase\schema\` |
| **Data Files** | `C:\RESA_Power_Build\Supabase\data\` |
| **Specs** | `C:\RESA_Power_Build\spec\` |
| **Excel Tracker** | `C:\RESA_Power_Build\Reference_Files\Excel\Garney-_Central_Mesa_Reuse_Tracker__677562.xlsm` |

### Shared Reference
| Item | Location |
|------|----------|
| **Field Tech App Spec** | `Documentation\07_Application_Specs\FIELD_TECH_APPLICATION_SPEC.md` |
| **Revenue Flow Spec** | `Documentation\06_Implementation_Guides\REVENUE_RECOGNITION_FLOW_SPEC_V2.md` |
| **Action Plan** | `.claude\ACTION_PLAN.md` |

---

## 🗄️ SUPABASE INFO

| Item | Value |
|------|-------|
| Project Name | `resa-power-db` |
| Project Ref | `fxoyniqnrlkxfligbxmg` |
| API URL | `https://fxoyniqnrlkxfligbxmg.supabase.co` |
| Environment | **Development** |
| Schema Status | ✅ 7 migrations deployed |
| Test Data | ✅ LASNAP16 project loaded |

---

## 📋 KEY DECISIONS (Summary)

See OPEN_DECISIONS.md for full details.

| Topic | Decision |
|-------|----------|
| Auth Strategy | Phased: anon key → Supabase Auth → optional MSAL |
| Environment | Current = Dev, create Prod later |
| RLS | Deferred until auth implemented |
| Priority | Field tracker first, PSS Portal deferred |
| Dataverse | Retire it, Supabase replaces |
| Data Source | Excel trackers, not Dataverse |
| Multi-tenant | No, RESA only |

---

## 🗺️ FIELD MAPPING (Excel → Supabase)

For both Claudes when working with data:

| Excel Column | Supabase Table.Column | Type |
|--------------|----------------------|------|
| Scope | scopes.scope_name | text |
| Task_ID | tasks.task_number | text |
| Task | tasks.task_name | text |
| Apparatus | apparatus.apparatus_name | text |
| Designation | apparatus.apparatus_designation | text |
| STATUS | apparatus.status | ENUM |
| ASSESSMENT | apparatus.assessment | ENUM |
| % COMPLETION | apparatus.percent_complete | decimal |
| APPARATUS HOURS | apparatus.quoted_hours | decimal |
| ACTUAL HOURS | apparatus.actual_hours | decimal |
| DATE COMPLETED | apparatus.actual_end | date |
| NOTES | apparatus.notes | text |

---

## 📝 HANDOFF NOTES

### From Desktop Claude to VS Code Claude:

1. **The swap is straightforward** - supabase.ts already mirrors dataverse.ts patterns
2. **Key difference**: Supabase returns arrays directly, not `{value: [...]}`
3. **Test data is there** - LASNAP16 project with 47 apparatus should appear
4. **Don't remove MSAL yet** - keep files for potential future SSO
5. **Dashboard views exist** - v_project_dashboard gives aggregated stats

### From VS Code Claude to Desktop Claude:

**Swap Status**: ✅ COMPLETE  
**Pages Working**: Dashboard (/) - shows projects from Supabase  
**Pages Broken**: /projects/[id] - 404 (page not created yet)  
**Issues Found & Fixed**:
- Column names mismatch (`name` vs `client_name`, etc.)
- `createClient` naming conflict with Supabase SDK
- Removed non-existent `contacts` table reference
**Questions**: None - moving to next phase

---

## ✅ SUCCESS CRITERIA

**Phase 1 Progress**:
- [x] App connects to Supabase (no Dataverse calls)
- [x] Projects list loads from Supabase
- [ ] Can view scopes/apparatus ← NEXT
- [ ] Can update apparatus status
- [ ] Garney project data imported
- [ ] Basic dashboard shows stats

---

**Last Updated**: 2025-12-05 23:45 by VS Code Claude  
**Status**: Supabase swap complete, documentation updated
