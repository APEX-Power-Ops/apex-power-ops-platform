# RESA Power - Decisions Log

> All significant decisions with context and rationale.  
> Newest entries at top.

---

## 2025-12-05 - Workspace Structure Established

**Context:** Need consistent environment for multi-Claude collaboration with session continuity.

**Decision:** Create `.claude/` directory with `CURRENT_STATE.md` and `DECISIONS_LOG.md`

**Rationale:** 
- Provides single source of truth for session state
- Enables seamless handoffs between Claude instances
- Documents decisions for future reference

**Stakeholder:** Jason Swenson (approved)

---

## 2025-12-05 - Schema File Organization

**Context:** Desktop Claude had monolithic 2,000-line file; VS Code Claude had 4 modular files.

**Options Considered:**
1. Keep monolithic file - Simple but hard to debug
2. Split by function - `schema/`, `data/`, `docs/` subdirectories
3. Flat with numbered prefixes - All in one folder

**Decision:** Option 2 - Split by function with numbered prefixes within each folder

**Rationale:**
- Clear separation of concerns
- Easier to navigate
- Can run schema vs data independently
- Matches professional PostgreSQL project structure

**Stakeholder:** Both Claudes agreed, Jason approved

---

## 2025-12-05 - PostgreSQL ENUMs vs VARCHAR

**Context:** VS Code Claude used VARCHAR with CHECK constraints; Desktop Claude used proper ENUMs.

**Decision:** Use PostgreSQL ENUMs for all status/type fields

**Rationale:**
- Type safety at database level
- IDE autocomplete support
- Prevents invalid values
- Standard PostgreSQL best practice

**Stakeholder:** Both Claudes agreed

---

## 2025-12-05 - PSS Table Naming Convention

**Context:** Need to distinguish PSS Portal tables from core operations tables.

**Options Considered:**
1. No prefix - All tables in flat namespace
2. `pss_` prefix - Clear visual separation
3. Separate PostgreSQL schema - `pss.studies` vs `public.projects`

**Decision:** Option 2 - Use `pss_` prefix

**Rationale:**
- Simple and clear
- Works with any ORM/query builder
- No schema complexity
- Easy to identify portal tables in queries

**Stakeholder:** VS Code Claude proposed, Desktop Claude agreed

---

## 2025-12-05 - Trigger Cascade Strategy

**Context:** Need to replicate Dataverse V1.5.1.3 rollup fields (apparatus counts, hours rolling up to task → scope → project).

**Options Considered:**
1. Application-level calculation - More control, but inconsistent
2. Database triggers - Automatic, but potential performance concern
3. Materialized views - Good for read, complex for write

**Decision:** Option 2 - Database triggers with cascade

**Rationale:**
- Data always consistent
- No application logic needed
- RESA scale (~hundreds of projects) won't stress triggers
- Can optimize later if needed

**Stakeholder:** Desktop Claude proposed, VS Code Claude agreed

---

## 2025-12-05 - Defer Time Entry & Expenses to Phase 2

**Context:** Both schemas missing time tracking and expense management.

**Decision:** Defer to Phase 2, focus on project/apparatus tracking first

**Rationale:**
- Core project tracking is immediate priority
- Time entry requires more UX design
- Can add tables later without breaking existing functionality
- Reduces Phase 1 complexity

**Stakeholder:** Both Claudes agreed

---

## 2025-12-05 - Add Equipment & NETA Templates Tables

**Context:** VS Code Claude had tables Desktop Claude didn't.

**Decision:** Include both in merged schema

**Tables Added:**
- `equipment` - Company-owned test equipment, calibration tracking
- `neta_test_templates` - Standard test procedures per equipment type

**Rationale:**
- Valuable for RESA operations
- No downside to including now
- Links to existing `apparatus_types` table

**Stakeholder:** VS Code Claude proposed, Desktop Claude agreed

---

## 2025-12-05 - Schema Merge Approach

**Context:** Two parallel schemas with different strengths.

**Decision:** Take best of both:
- Desktop Claude: ENUMs, triggers, computed columns, views, RLS
- VS Code Claude: Documentation, test data, modular structure, `pss_*` naming

**Rationale:**
- Combines technical depth with developer experience
- Neither schema was complete alone
- Cross-review catches errors

**Stakeholder:** Both Claudes agreed, Jason approved

---

*Log maintained by VS Code Claude & Desktop Claude*
