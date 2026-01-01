# RESA Power - Parallel Task Execution Plan

**Created:** December 5, 2025  
**Purpose:** Optimize parallel work between Desktop Claude and VS Code Claude  
**Status:** PENDING APPROVAL

---

## Environment & Strengths Assessment

### Desktop Claude (Claude.ai)
| Capability | Strength | Use For |
|------------|----------|---------|
| Long-form generation | ⭐⭐⭐⭐⭐ | Spec documents, complex SQL |
| Schema design | ⭐⭐⭐⭐⭐ | Triggers, computed columns, ENUMs |
| Web search | ⭐⭐⭐⭐ | Research, validation |
| File operations | ⭐⭐⭐⭐ | Desktop Commander access |
| Context window | ⭐⭐⭐⭐ | Hold full schema in memory |

**Best at:** Architecture, automation logic, comprehensive documentation

### VS Code Claude
| Capability | Strength | Use For |
|------------|----------|---------|
| Code editing | ⭐⭐⭐⭐⭐ | Modular file creation |
| Terminal access | ⭐⭐⭐⭐ | Testing, validation |
| Developer focus | ⭐⭐⭐⭐⭐ | README, examples, DX |
| Realistic data | ⭐⭐⭐⭐⭐ | Test data with real patterns |
| Quick iteration | ⭐⭐⭐⭐ | Fast file updates |

**Best at:** Implementation details, test data, developer documentation, validation

---

## Parallel Execution Timeline

```
HOUR    DESKTOP CLAUDE                      VS CODE CLAUDE
════    ══════════════════════════════      ══════════════════════════════

        PHASE 0: SPEC CREATION
────    ──────────────────────────────      ──────────────────────────────
0:00    📝 Create spec/ folder              📁 Archive old files
        📝 Start DATA_DICTIONARY.md         📁 Organize workspace
                                            📝 Create CONVENTIONS.md

0:30    📝 DATA_DICTIONARY (continued)      👀 Review DATA_DICTIONARY draft
        Tables: locations → projects        📝 Prep test data UUIDs list
                                            📝 Collect realistic values (names, etc.)

1:00    📝 DATA_DICTIONARY (continued)      👀 Review + flag issues
        Tables: scopes → apparatus          📋 Create test data mapping doc
                                            (which test records for which tables)

1:30    📝 DATA_DICTIONARY (finish)         👀 Final review DATA_DICTIONARY
        📝 Start ENUM_DEFINITIONS.md        ✅ Approve or request fixes

2:00    📝 ENUM_DEFINITIONS (finish)        👀 Review ENUM_DEFINITIONS
        📝 Start ENTITY_RELATIONSHIPS.md    📝 Map test data to ENUMs
                                            (which status values to use)

2:30    📝 ENTITY_RELATIONSHIPS (finish)    👀 Review ERD
        📝 Start TRIGGER_FLOWS.md           📝 Document test scenarios
                                            (what triggers should fire)

3:00    📝 TRIGGER_FLOWS (finish)           👀 Review TRIGGER_FLOWS
        📝 Start VIEW_DEFINITIONS.md        📝 Prep expected view outputs
                                            (what dashboard should show)

3:30    📝 VIEW_DEFINITIONS (finish)        👀 Final spec review
        ✅ SPEC COMPLETE                    ✅ SPEC APPROVED

────    ──────────────────────────────      ──────────────────────────────
        PHASE 1: SCHEMA GENERATION
────    ──────────────────────────────      ──────────────────────────────
3:30    📝 00_enums.sql                     📝 README.md skeleton
        (from ENUM_DEFINITIONS.md)          (structure, placeholders)

3:45    📝 01_core_schema.sql               📝 QUICK_START.md skeleton
        (from DATA_DICTIONARY.md)           📋 Finalize test data plan

4:15    📝 01_core_schema.sql (cont.)       👀 Review 00_enums.sql
                                            👀 Review 01_core_schema.sql (partial)

4:30    📝 02_pss_schema.sql                📝 11_test_data.sql (start)
        (from DATA_DICTIONARY.md)           Core: locations, clients, sites

5:00    📝 03_triggers_functions.sql        📝 11_test_data.sql (cont.)
        (from TRIGGER_FLOWS.md)             Projects, scopes, tasks

5:30    📝 04_views.sql                     📝 11_test_data.sql (cont.)
        (from VIEW_DEFINITIONS.md)          Apparatus, revenue records

5:45    📝 05_rls_policies.sql              👀 Review 02-05 SQL files
        📝 10_seed_data.sql                 Flag any spec deviations

6:00    ✅ SCHEMA COMPLETE                  📝 11_test_data.sql (finish)

────    ──────────────────────────────      ──────────────────────────────
        PHASE 2: TEST DATA & DOCS
────    ──────────────────────────────      ──────────────────────────────
6:00    👀 Review 11_test_data.sql          📝 12_pss_test_data.sql
        Verify FK compliance                PSS studies, documents, RFIs

6:30    📝 Fix any schema issues found      📝 12_pss_test_data.sql (finish)
        👀 Review 12_pss_test_data.sql      📝 README.md (complete)

7:00    👀 Final review all files           📝 QUICK_START.md (complete)
        📝 SCHEMA_REFERENCE.md              ✅ DOCS COMPLETE

7:30    ✅ Cross-review complete            ✅ Cross-review complete
        📋 READY FOR DEPLOYMENT             📋 READY FOR DEPLOYMENT

════    ══════════════════════════════      ══════════════════════════════
        TOTAL: ~7.5 hours parallel          TOTAL: ~7.5 hours parallel
        ACTUAL WALL TIME: ~4 hours          (running simultaneously)
```

---

## Detailed Task Assignments

### Phase 0: Spec Creation (3.5 hours)

#### Desktop Claude Tasks
| Task | File | Est. | Deliverable |
|------|------|------|-------------|
| Create folder | `spec/` | 2 min | Directory exists |
| Data dictionary | `spec/DATA_DICTIONARY.md` | 90 min | All 25 tables documented |
| Enum definitions | `spec/ENUM_DEFINITIONS.md` | 30 min | All 18 enums with rules |
| Entity relationships | `spec/ENTITY_RELATIONSHIPS.md` | 30 min | Visual ERD |
| Trigger flows | `spec/TRIGGER_FLOWS.md` | 30 min | All 10 triggers documented |
| View definitions | `spec/VIEW_DEFINITIONS.md` | 20 min | All 8 views documented |

#### VS Code Claude Tasks (Parallel)
| Task | File | Est. | Deliverable |
|------|------|------|-------------|
| Archive old files | `archive/2025-12-05_pre-merge/` | 15 min | Clean workspace |
| Create conventions | `.claude/CONVENTIONS.md` | 20 min | Standards extracted |
| Prep UUID mapping | `spec/TEST_DATA_PLAN.md` | 30 min | UUID scheme documented |
| Collect test values | (working doc) | 30 min | Realistic names, numbers |
| Review specs | (ongoing) | 90 min | Issues flagged in real-time |
| Test scenario doc | `spec/TEST_SCENARIOS.md` | 30 min | Expected trigger behaviors |

---

### Phase 1: Schema Generation (2.5 hours)

#### Desktop Claude Tasks
| Task | File | Est. | Input Spec |
|------|------|------|------------|
| ENUMs | `Supabase/schema/00_enums.sql` | 15 min | ENUM_DEFINITIONS.md |
| Core tables | `Supabase/schema/01_core_schema.sql` | 45 min | DATA_DICTIONARY.md |
| PSS tables | `Supabase/schema/02_pss_schema.sql` | 30 min | DATA_DICTIONARY.md |
| Triggers | `Supabase/schema/03_triggers_functions.sql` | 30 min | TRIGGER_FLOWS.md |
| Views | `Supabase/schema/04_views.sql` | 20 min | VIEW_DEFINITIONS.md |
| RLS policies | `Supabase/schema/05_rls_policies.sql` | 15 min | DATA_DICTIONARY.md |
| Seed data | `Supabase/data/10_seed_data.sql` | 15 min | DATA_DICTIONARY.md |

#### VS Code Claude Tasks (Parallel)
| Task | File | Est. | Dependency |
|------|------|------|------------|
| README skeleton | `Supabase/docs/README.md` | 20 min | None |
| Quick start skeleton | `Supabase/docs/QUICK_START.md` | 15 min | None |
| Test data - core | `Supabase/data/11_test_data.sql` | 60 min | 01_core_schema.sql |
| Review schema files | (ongoing) | 45 min | As files complete |

---

### Phase 2: Test Data & Docs (1.5 hours)

#### Desktop Claude Tasks
| Task | File | Est. | Purpose |
|------|------|------|---------|
| Review test data | 11, 12 SQL files | 30 min | Verify FK compliance |
| Schema reference | `Supabase/docs/SCHEMA_REFERENCE.md` | 30 min | Quick lookup doc |
| Final cross-review | All files | 30 min | Catch inconsistencies |

#### VS Code Claude Tasks (Parallel)
| Task | File | Est. | Dependency |
|------|------|------|------------|
| PSS test data | `Supabase/data/12_pss_test_data.sql` | 40 min | 02_pss_schema.sql |
| Complete README | `Supabase/docs/README.md` | 30 min | Schema complete |
| Complete Quick Start | `Supabase/docs/QUICK_START.md` | 20 min | Schema complete |
| Final cross-review | All files | 30 min | Desktop review done |

---

## Handoff Points

### Handoff 1: After DATA_DICTIONARY.md Draft
```
Desktop → VS Code:
"DATA_DICTIONARY.md draft complete. 
Review tables: locations through project_financial_summaries.
Flag any field name concerns or missing columns."
```

### Handoff 2: After Spec Complete
```
Desktop → VS Code:
"All 5 spec documents complete in spec/ folder.
Please do final review before I begin SQL generation.
Specifically check: TRIGGER_FLOWS cascade effects."
```

### Handoff 3: After 01_core_schema.sql
```
Desktop → VS Code:
"Core schema complete. 
You can now start 11_test_data.sql.
Reference: DATA_DICTIONARY.md for exact field names."
```

### Handoff 4: After All Schema Complete
```
Desktop → VS Code:
"All schema files (00-05, 10) complete.
Ready for full test data generation.
I'll begin reviewing your 11_test_data.sql in parallel."
```

### Handoff 5: Final Review
```
Both → Jason:
"All files complete. Cross-reviewed.
Ready for Supabase deployment.
Files in Supabase/schema/, Supabase/data/, Supabase/docs/"
```

---

## Communication Protocol

### Real-Time Sync
- Update `.claude/CURRENT_STATE.md` after each major task
- Flag blocking issues immediately
- Don't wait for handoff if you find a problem

### Review Format
```markdown
## Review: [FILE NAME]
**Reviewer:** [Claude instance]
**Status:** ✅ APPROVED | ⚠️ ISSUES | ❌ BLOCKED

### Issues Found
1. [Issue description] - Line X
2. [Issue description] - Line Y

### Suggested Fixes
1. [Fix for issue 1]
2. [Fix for issue 2]
```

### Blocking Issue Escalation
If either Claude is blocked:
1. Update CURRENT_STATE.md with blocker
2. Explicitly note: "BLOCKED: [reason]"
3. Suggest resolution or request Jason decision

---

## Success Criteria

### Phase 0 Complete When:
- [ ] All 5 spec documents exist in `spec/`
- [ ] VS Code Claude has reviewed and approved all 5
- [ ] No open issues flagged
- [ ] TEST_DATA_PLAN.md ready for Phase 2

### Phase 1 Complete When:
- [ ] All 7 SQL files exist in `Supabase/schema/` and `Supabase/data/`
- [ ] Each file has header block per CONVENTIONS.md
- [ ] VS Code Claude has reviewed for spec compliance
- [ ] No syntax errors (validated)

### Phase 2 Complete When:
- [ ] Test data files (11, 12) complete
- [ ] README.md and QUICK_START.md complete
- [ ] SCHEMA_REFERENCE.md complete
- [ ] Cross-review by both Claudes complete
- [ ] All files ready for Supabase deployment

### Deployment Ready When:
- [ ] Jason has approved all deliverables
- [ ] Supabase project created
- [ ] Connection details documented
- [ ] Test execution successful

---

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|------------|-------|
| Spec paralysis | 4-hour hard cap on Phase 0 | Jason (timekeeper) |
| FK mismatches in test data | Review against DATA_DICTIONARY | Desktop |
| Trigger logic errors | TEST_SCENARIOS.md validation | VS Code |
| Context loss between sessions | CURRENT_STATE.md discipline | Both |
| Naming inconsistencies | CONVENTIONS.md reference | Both |

---

## Quick Reference: Who Does What

| Category | Desktop Claude | VS Code Claude |
|----------|---------------|----------------|
| **Spec docs** | Creates all 5 | Reviews all 5 |
| **Schema SQL** | Creates all 7 | Reviews all 7 |
| **Test data** | Reviews | Creates |
| **README/docs** | SCHEMA_REFERENCE | README, QUICK_START |
| **Workspace** | Spec structure | Archive, cleanup |
| **Validation** | Spec compliance | Realistic data |

---

## Immediate Next Steps

### Upon Jason's Approval:

**Desktop Claude (Me):**
1. Create `spec/` folder
2. Begin `DATA_DICTIONARY.md`
3. Update CURRENT_STATE.md with progress

**VS Code Claude:**
1. Move old files to `archive/2025-12-05_pre-merge/`
2. Create `.claude/CONVENTIONS.md` (extract from WORKSPACE_PROTOCOL.md)
3. Begin `spec/TEST_DATA_PLAN.md`
4. Monitor for DATA_DICTIONARY.md to review

**Jason:**
1. Say "Approved"
2. Stand by for questions
3. Create Supabase project when we reach deployment

---

*Parallel execution plan created by Desktop Claude | December 5, 2025*  
*Ready for VS Code Claude confirmation and Jason approval*
