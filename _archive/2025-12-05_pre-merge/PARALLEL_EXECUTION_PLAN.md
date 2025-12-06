# RESA Database Schema - Parallel Execution Plan

**Date:** December 5, 2025  
**Stakeholders:** Jason Swenson (Decision Maker), Desktop Claude (Automation), VS Code Claude (DX/Documentation)

---

## Execution Strategy: Parallel Workstreams

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: SCHEMA BUILD                                │
│                         Target: 2-3 Hours                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DESKTOP CLAUDE                         VS CODE CLAUDE                      │
│  (Automation Expert)                    (DX Expert)                         │
│                                                                             │
│  ┌─────────────────────┐               ┌─────────────────────┐              │
│  │ 00_enums.sql        │               │ README.md           │              │
│  │ 01_core_schema.sql  │               │ (Enhanced setup     │              │
│  │ 03_triggers.sql     │               │  guide with API     │              │
│  │ 04_views.sql        │               │  examples)          │              │
│  │ 05_rls_policies.sql │               │                     │              │
│  └─────────────────────┘               └─────────────────────┘              │
│           │                                     │                           │
│           ▼                                     ▼                           │
│  ┌─────────────────────┐               ┌─────────────────────┐              │
│  │ 02_pss_schema.sql   │               │ 11_test_data.sql    │              │
│  │ (with pss_* prefix) │               │ (LASNAP16 project)  │              │
│  │                     │               │                     │              │
│  │ 10_seed_data.sql    │               │ 12_pss_test_data.sql│              │
│  │ (apparatus types,   │               │ (SWA Tech Ops, etc) │              │
│  │  locations, etc)    │               │                     │              │
│  └─────────────────────┘               └─────────────────────┘              │
│           │                                     │                           │
│           └──────────────┬──────────────────────┘                           │
│                          ▼                                                  │
│                 ┌─────────────────────┐                                     │
│                 │   JASON: REVIEW     │                                     │
│                 │   Quick validation  │                                     │
│                 │   before deploy     │                                     │
│                 └─────────────────────┘                                     │
│                          │                                                  │
└──────────────────────────┼──────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 2: DEPLOYMENT                                  │
│                         Target: 30 Minutes                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  JASON (Stakeholder)                                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │ 1. Create Supabase project at supabase.com                  │            │
│  │ 2. Run SQL files in order (00 → 05 → 10 → 12)              │            │
│  │ 3. Verify tables in Table Editor                            │            │
│  │ 4. Test sample queries                                      │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                             │
│  EITHER CLAUDE (Support)                                                    │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │ • Troubleshoot any SQL errors                               │            │
│  │ • Validate trigger execution                                │            │
│  │ • Verify test data relationships                            │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Task Assignment

### DESKTOP CLAUDE - Automation Track

| Task | File | Description | Dependencies | Est. Time |
|------|------|-------------|--------------|-----------|
| DC-1 | `00_enums.sql` | All 15 PostgreSQL ENUMs | None | 10 min |
| DC-2 | `01_core_schema.sql` | Core tables with computed columns, add `equipment`, `neta_test_templates`, `resource_assignments` | DC-1 | 30 min |
| DC-3 | `02_pss_schema.sql` | PSS tables with `pss_*` prefix | DC-1 | 20 min |
| DC-4 | `03_triggers_functions.sql` | Rollup cascades, revenue recognition, status tracking | DC-2, DC-3 | 25 min |
| DC-5 | `04_views.sql` | 7 dashboard views | DC-2, DC-3 | 15 min |
| DC-6 | `05_rls_policies.sql` | Row Level Security policies | DC-2, DC-3 | 10 min |
| DC-7 | `10_seed_data.sql` | Apparatus types, locations, document templates | DC-2 | 15 min |

**Desktop Claude Total:** ~2 hours

---

### VS CODE CLAUDE - Developer Experience Track

| Task | File | Description | Dependencies | Est. Time |
|------|------|-------------|--------------|-----------|
| VC-1 | `README.md` | Enhanced setup guide with Supabase, NocoDB, API examples | None | 30 min |
| VC-2 | `11_test_data.sql` | LASNAP16 project (6 scopes, 7 tasks, 14 apparatus) | DC-2 schema | 25 min |
| VC-3 | `12_pss_test_data.sql` | PSS studies (SWA Tech Ops, Hydro, etc.) | DC-3 schema | 20 min |
| VC-4 | Validation | Review Desktop Claude's files for consistency | DC-1 through DC-7 | 15 min |
| VC-5 | `QUICK_START.md` | 5-minute deployment guide | VC-1 | 10 min |

**VS Code Claude Total:** ~1.5 hours

---

### JASON - Stakeholder Track

| Task | Description | Dependencies | Est. Time |
|------|-------------|--------------|-----------|
| JS-1 | Review task plan | This document | 5 min |
| JS-2 | Approve/modify assignments | JS-1 | 5 min |
| JS-3 | Create Supabase project | None (can do anytime) | 5 min |
| JS-4 | Run schema deployment | All DC + VC tasks | 15 min |
| JS-5 | Validate in Table Editor | JS-4 | 10 min |
| JS-6 | Test queries in SQL Editor | JS-5 | 10 min |
| JS-7 | Connect NocoDB (optional) | JS-5 | 15 min |

**Jason Total:** ~1 hour (mostly waiting + validation)

---

## Parallel Execution Timeline

```
TIME        DESKTOP CLAUDE              VS CODE CLAUDE              JASON
─────────────────────────────────────────────────────────────────────────────
0:00        DC-1: ENUMs                 VC-1: README                JS-1: Review plan
            │                           │                           │
0:10        DC-2: Core schema ──────────┼───────────────────────────┼─► JS-2: Approve
            │                           │                           │
0:30        │                           │                           JS-3: Create Supabase
            │                           │                           │
0:40        DC-2 complete ──────────────┼─► VC-2: Test data starts  │
            │                           │                           │
0:45        DC-3: PSS schema            │                           │
            │                           │                           │
1:00        DC-3 complete ──────────────┼─► VC-3: PSS test data     │
            │                           │                           │
1:05        DC-4: Triggers              │                           │
            │                           │                           │
1:20        VC-1 complete               │                           │
            │                           │                           │
1:30        DC-4 complete               VC-2, VC-3 complete         │
            DC-5: Views                 VC-4: Validation starts     │
            │                           │                           │
1:45        DC-5 complete               │                           │
            DC-6: RLS                   │                           │
            │                           │                           │
1:55        DC-6 complete               VC-4 complete               │
            DC-7: Seed data             VC-5: Quick start           │
            │                           │                           │
2:10        ALL FILES COMPLETE ─────────┴───────────────────────────┼─► JS-4: Deploy
            │                                                       │
2:25        │                                                       JS-5: Validate
            │                                                       │
2:35        │                                                       JS-6: Test queries
            │                                                       │
2:45        │                                                       JS-7: NocoDB (opt)
            │                                                       │
3:00        ════════════════════ DEPLOYMENT COMPLETE ═══════════════════════
```

---

## File Ownership Matrix

| File | Primary Owner | Reviewer | Source Material |
|------|---------------|----------|-----------------|
| `00_enums.sql` | Desktop Claude | VS Code Claude | Desktop's existing ENUMs |
| `01_core_schema.sql` | Desktop Claude | VS Code Claude | Merge both + new tables |
| `02_pss_schema.sql` | Desktop Claude | VS Code Claude | VS Code's pss_* naming |
| `03_triggers_functions.sql` | Desktop Claude | VS Code Claude | Desktop's automation |
| `04_views.sql` | Desktop Claude | VS Code Claude | Desktop's 7 views |
| `05_rls_policies.sql` | Desktop Claude | VS Code Claude | Desktop's RLS |
| `10_seed_data.sql` | Desktop Claude | VS Code Claude | Merge both |
| `11_test_data.sql` | VS Code Claude | Desktop Claude | VS Code's LASNAP16 |
| `12_pss_test_data.sql` | VS Code Claude | Desktop Claude | VS Code's PSS studies |
| `README.md` | VS Code Claude | Desktop Claude | VS Code's enhanced |
| `QUICK_START.md` | VS Code Claude | Desktop Claude | New |

---

## Success Criteria

### Phase 1 Complete When:
- [ ] All 10 files exist in `Supabase/` folder
- [ ] No SQL syntax errors
- [ ] Cross-file references validated (FKs match PKs)
- [ ] README has complete setup instructions

### Phase 2 Complete When:
- [ ] Supabase project created
- [ ] All SQL files executed successfully
- [ ] 24+ tables visible in Table Editor
- [ ] Test data visible (LASNAP16 project, SWA Tech Ops study)
- [ ] Sample query returns expected results
- [ ] (Optional) NocoDB connected and showing data

---

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|------------|-------|
| SQL syntax errors | Run each file individually, fix before proceeding | Both Claudes |
| FK constraint failures | Ensure seed data runs before test data | Desktop Claude |
| Trigger cascades fail | Test with single record first | Desktop Claude |
| Test data UUID conflicts | Use fixed, predictable UUIDs | VS Code Claude |
| README unclear | Jason tests following only README | VS Code Claude |

---

## Communication Protocol

1. **Desktop Claude** creates files in `Supabase/` folder
2. **VS Code Claude** reviews and creates complementary files
3. **Either Claude** can flag issues to Jason
4. **Jason** makes final deployment decisions

---

## Immediate Next Steps

| Who | Action | When |
|-----|--------|------|
| **Jason** | Approve this plan (or modify) | Now |
| **Desktop Claude** | Start DC-1 (ENUMs) | Upon approval |
| **VS Code Claude** | Start VC-1 (README) | Upon approval |
| **Jason** | Create Supabase project | Anytime before Phase 2 |

---

**Ready to execute on your signal, Jason!**

*Plan created by VS Code Claude | Reviewed by Desktop Claude | December 5, 2025*
