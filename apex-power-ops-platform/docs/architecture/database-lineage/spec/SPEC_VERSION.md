# Spec Version Tracking

**Purpose:** Track versions of spec documents for change control  
**Owner:** Both Claudes update this file

---

## Current Spec Version

| Document | Version | Status | Last Updated | Updated By |
|----------|---------|--------|--------------|------------|
| DATA_DICTIONARY.md | - | PENDING | - | Desktop Claude |
| ENUM_DEFINITIONS.md | - | PENDING | - | Desktop Claude |
| ENTITY_RELATIONSHIPS.md | - | PENDING | - | Desktop Claude |
| TRIGGER_FLOWS.md | - | PENDING | - | Desktop Claude |
| VIEW_DEFINITIONS.md | - | PENDING | - | Desktop Claude |
| V1513_FIELD_REFERENCE.md | 1.0 | COMPLETE | 2025-12-05 | VS Code Claude |

---

## Version History

### 2025-12-05
- **V1513_FIELD_REFERENCE.md v1.0** - VS Code Claude
  - Created validation reference from Dataverse v1.5.1.3 export
  - Mapped 20 Dataverse entities to PostgreSQL table names
  - Identified 6 PSS tables (new)
  - Identified 3 tables for Phase 2 deferral

---

## Spec Approval Status

| Phase | Status | Approved By | Date |
|-------|--------|-------------|------|
| Phase 0: Spec Creation | IN PROGRESS | - | - |
| Jason Review | PENDING | - | - |
| Phase 1: Schema Build | NOT STARTED | - | - |
| Phase 2: Test Data | NOT STARTED | - | - |

---

## Change Control Rules

1. **Minor changes** (typos, formatting): Update version patch (1.0 → 1.0.1)
2. **Field additions/removals**: Update version minor (1.0 → 1.1)
3. **Breaking changes** (table rename, FK change): Update version major (1.0 → 2.0)
4. **All changes**: Add entry to Version History section

---

*Spec version tracking initialized | December 5, 2025*
