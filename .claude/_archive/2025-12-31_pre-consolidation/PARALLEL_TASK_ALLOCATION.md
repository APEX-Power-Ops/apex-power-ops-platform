# Parallel Task Allocation - Spec-First Build

**Created:** December 5, 2025  
**Status:** APPROVED - Ready for Execution  
**Coordination File:** Both Claudes reference this document

---

## Environment & Strengths Analysis

### Desktop Claude
| Capability | Strength | Best For |
|------------|----------|----------|
| Long-form generation | ⭐⭐⭐⭐⭐ | Large documents, complete schemas |
| Context window | ⭐⭐⭐⭐⭐ | Holding full spec in memory |
| File creation | ⭐⭐⭐⭐ | New documents from scratch |
| Dataverse knowledge | ⭐⭐⭐⭐⭐ | Has v1.5.1.3 context loaded |
| Multi-file coherence | ⭐⭐⭐⭐⭐ | Ensuring consistency across files |

### VS Code Claude
| Capability | Strength | Best For |
|------------|----------|----------|
| File system access | ⭐⭐⭐⭐⭐ | Reading existing files, validation |
| Terminal commands | ⭐⭐⭐⭐⭐ | Running scripts, git operations |
| Workspace search | ⭐⭐⭐⭐⭐ | Finding field names in exports |
| Incremental edits | ⭐⭐⭐⭐⭐ | Reviewing and fixing issues |
| MCP Dataverse access | ⭐⭐⭐⭐ | Querying live schema if needed |
| Test data generation | ⭐⭐⭐⭐ | Creating realistic sample records |

---

## Phase 0: Spec Creation (3-4 hours)

### Parallel Track A: Desktop Claude (Primary Author)

| Task | Est. Time | Output | Status |
|------|-----------|--------|--------|
| Create `spec/` folder structure | 5 min | Folders created | ⬜ |
| DATA_DICTIONARY.md | 90 min | All 25 tables documented | ⬜ |
| ENUM_DEFINITIONS.md | 30 min | All 15+ enums with transitions | ⬜ |
| ENTITY_RELATIONSHIPS.md | 30 min | Complete ERD | ⬜ |
| TRIGGER_FLOWS.md | 30 min | All triggers documented | ⬜ |
| VIEW_DEFINITIONS.md | 20 min | All 7 views documented | ⬜ |

**Total Desktop:** ~3.5 hours

### Parallel Track B: VS Code Claude (Validation & Support)

| Task | Est. Time | Output | Status |
|------|-----------|--------|--------|
| Extract field names from v1.5.1.3 export | 20 min | Field reference list | ⬜ |
| Create `spec/SPEC_VERSION.md` | 10 min | Version tracking file | ⬜ |
| Review DATA_DICTIONARY.md (as completed) | 20 min | Validation notes | ⬜ |
| Review ENUM_DEFINITIONS.md | 10 min | Validation notes | ⬜ |
| Review ENTITY_RELATIONSHIPS.md | 10 min | Validation notes | ⬜ |
| Cross-reference triggers vs Dataverse rollups | 15 min | Gap analysis | ⬜ |
| Prepare test data templates | 30 min | CSV/structure ready | ⬜ |

**Total VS Code:** ~2 hours (overlapping with Desktop)

---

## Phase 1: Schema Generation (2-3 hours)

### Desktop Claude (Primary Generator)

| Task | Est. Time | Dependencies | Status |
|------|-----------|--------------|--------|
| 00_enums.sql | 15 min | ENUM_DEFINITIONS.md | ⬜ |
| 01_core_schema.sql | 45 min | DATA_DICTIONARY.md | ⬜ |
| 02_pss_schema.sql | 30 min | DATA_DICTIONARY.md | ⬜ |
| 03_triggers_functions.sql | 30 min | TRIGGER_FLOWS.md | ⬜ |
| 04_views.sql | 20 min | VIEW_DEFINITIONS.md | ⬜ |
| 05_rls_policies.sql | 15 min | DATA_DICTIONARY.md | ⬜ |

**Total Desktop:** ~2.5 hours

### VS Code Claude (Parallel Validation)

| Task | Est. Time | Dependencies | Status |
|------|-----------|--------------|--------|
| Validate 00_enums.sql syntax | 10 min | File complete | ⬜ |
| Validate 01_core_schema.sql FKs | 15 min | File complete | ⬜ |
| Validate 02_pss_schema.sql FKs | 10 min | File complete | ⬜ |
| Review trigger logic | 15 min | File complete | ⬜ |
| Validate view joins | 10 min | File complete | ⬜ |
| Create deployment checklist | 15 min | All schema files | ⬜ |

**Total VS Code:** ~1.25 hours (overlapping)

---

## Phase 2: Test Data & Documentation (1-2 hours)

### VS Code Claude (Primary Generator)

| Task | Est. Time | Dependencies | Status |
|------|-----------|--------------|--------|
| 10_seed_data.sql (reference data) | 20 min | Schema complete | ⬜ |
| 11_test_data.sql (LASNAP16 project) | 40 min | Schema complete | ⬜ |
| 12_pss_test_data.sql (5 PSS studies) | 30 min | Schema complete | ⬜ |
| README.md (deployment guide) | 20 min | All files complete | ⬜ |
| QUICK_START.md | 15 min | README complete | ⬜ |

**Total VS Code:** ~2 hours

### Desktop Claude (Review & Refinement)

| Task | Est. Time | Dependencies | Status |
|------|-----------|--------------|--------|
| Review test data FK integrity | 15 min | Test data complete | ⬜ |
| Review README accuracy | 10 min | README complete | ⬜ |
| Final spec consistency check | 15 min | All files complete | ⬜ |

**Total Desktop:** ~40 min

---

## Handoff Protocol

### During Phase 0
```
Desktop Claude: "DATA_DICTIONARY.md complete. 25 tables documented. 
Ready for VS Code review."

VS Code Claude: *Reads file, validates against v1.5.1.3 export*

VS Code Claude: "Validated. Found 2 minor issues:
- projects.total_revenue should be DECIMAL(15,2) not (10,2)
- Missing index note on apparatus.scope_id
Otherwise approved."

Desktop Claude: *Fixes issues, continues to next file*
```

### During Phase 1
```
Desktop Claude: "01_core_schema.sql complete. Posting to Supabase/schema/"

VS Code Claude: *Reads file, checks FK references*

VS Code Claude: "FK validation passed. All references exist. 
Ready for 02_pss_schema.sql."
```

### During Phase 2
```
VS Code Claude: "11_test_data.sql complete. LASNAP16 with 4 scopes, 
12 tasks, 47 apparatus. Ready for Desktop review."

Desktop Claude: *Reviews FK integrity*

Desktop Claude: "Approved. FK references valid. enum values correct."
```

---

## Communication Checkpoints

| Checkpoint | Trigger | Who Initiates |
|------------|---------|---------------|
| Spec doc complete | Each doc finished | Desktop |
| Validation complete | After review | VS Code |
| Schema file complete | Each SQL file | Desktop |
| Test data complete | Each data file | VS Code |
| Phase complete | All files in phase | Either |
| Blocker found | Any issue | Either |

---

## Resource References

### For Desktop Claude
- `Solution_Exports/Archive/v1.5.1.3/customizations.xml` - Field definitions
- `Supabase/001_complete_schema.sql` - Existing schema draft
- `.claude/SPEC_FIRST_PROPOSAL.md` - Approved approach

### For VS Code Claude
- `MASTER_SCHEMA.md` - Table/field reference
- `CSV_Templates/` - Field name patterns
- MCP Dataverse tools - Live schema queries if needed
- Terminal - For file validation, git operations

---

## Success Criteria

### Phase 0 Complete When:
- [ ] All 5 spec documents created
- [ ] VS Code validation passed on each
- [ ] No unresolved field name questions
- [ ] ERD matches DATA_DICTIONARY

### Phase 1 Complete When:
- [ ] All 6 SQL files created
- [ ] FK validation passed
- [ ] Enum references validated
- [ ] Trigger cascade logic documented

### Phase 2 Complete When:
- [ ] Test data loads without errors
- [ ] LASNAP16 project fully populated
- [ ] 5 PSS studies with documents
- [ ] README deployment tested

---

## Timeline Summary

| Phase | Desktop Claude | VS Code Claude | Calendar Time |
|-------|---------------|----------------|---------------|
| Phase 0 | 3.5 hrs active | 2 hrs (parallel) | ~3.5 hrs |
| Phase 1 | 2.5 hrs active | 1.25 hrs (parallel) | ~2.5 hrs |
| Phase 2 | 0.5 hrs review | 2 hrs active | ~2 hrs |
| **Total** | **6.5 hrs** | **5.25 hrs** | **~8 hrs** |

**With parallel execution: ~6-7 hours total elapsed time**

---

## Immediate Next Actions

### Desktop Claude - START NOW:
1. Create `spec/` folder
2. Begin DATA_DICTIONARY.md
3. Signal VS Code when first doc complete

### VS Code Claude - START NOW:
1. Extract v1.5.1.3 field names for validation reference
2. Create SPEC_VERSION.md
3. Prepare test data templates
4. Monitor for Desktop's first deliverable

---

*Task allocation approved | December 5, 2025*
*Both Claudes: Update status checkboxes as tasks complete*
