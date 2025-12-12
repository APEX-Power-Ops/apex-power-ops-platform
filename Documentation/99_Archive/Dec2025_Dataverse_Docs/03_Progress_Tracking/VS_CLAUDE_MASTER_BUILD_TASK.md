# MASTER BUILD SPECIFICATION UPDATE - VS Claude Task Brief

**Date:** November 27, 2025  
**Assigned To:** VS Claude  
**Estimated Effort:** 3-4 hours  
**Priority:** P1 - Critical Documentation Debt

---

## OBJECTIVE

Update `MASTER_BUILD_SPECIFICATION.md` from its current v1.3.0.4 alignment to match the deployed v1.5.0.0 solution. This is a comprehensive documentation update, not a system change.

---

## CURRENT STATE

**Document Location:** `C:\RESA_Power_Build\Documentation\01_Architecture\MASTER_BUILD_SPECIFICATION.md`

**Document Claims:**
- Version 2.0 (document version)
- Aligned with solution v1.3.0.4
- "350+" fields
- 8 core tables

**Reality (v1.5.0.0):**
- 16 tables (8 original + 6 new in v1.4.0.0 + 2 financial summary)
- 649 custom fields
- 65 rollup/formula fields added in v1.5.0.0
- Multiple relationship additions

---

## WHAT'S MISSING FROM CURRENT DOC

### 1. Six New Tables (Added v1.4.0.0)

| Table | Logical Name | Purpose | Fields |
|-------|--------------|---------|--------|
| Client | cr950_client | Customer master data | 43 |
| Site | cr950_site | Physical locations | 39 |
| Employee | cr950_employee | Technician/staff records | 40 |
| Quote | cr950_quote | Pre-project estimates | 54 |
| Resource Assignment | cr950_resourceassignment | Project staffing | 35 |
| Equipment | cr950_equipment | Test equipment tracking | 42 |

### 2. Two Financial Summary Tables (Added v1.5.0.0)

| Table | Logical Name | Purpose | Fields |
|-------|--------------|---------|--------|
| Project Financial Summary | cr950_projectfinancialsummary | Project-level rollups | 30 |
| Scope Financial Summary | cr950_scopefinancialsummary | Scope-level rollups | 30 |

### 3. Rollup Field Expansion (v1.5.0.0)

65 rollup and calculated fields were added across:
- Projects table: apparatus counts, hour totals, completion percentages
- ProjectScope table: task counts, apparatus aggregations
- Tasks table: apparatus rollups
- ScopeLaborDetail: financial calculations

### 4. New Relationships

- Client → Projects (1:N)
- Client → Sites (1:N)
- Site → Projects (1:N)
- Client → Quotes (1:N)
- Employee → Resource Assignments (1:N)
- Projects → Resource Assignments (1:N)
- Equipment → Employee (N:1)
- Equipment → Projects (N:1)

---

## SOURCE OF TRUTH FILES

### Primary (Use These)

1. **Solution Export XML** - THE authoritative source
   ```
   C:\RESA_Power_Build\Solution_Exports\v1.5.0.0_extracted\customizations.xml
   ```

2. **VERSION_HISTORY.md** - Accurate version progression
   ```
   C:\RESA_Power_Build\Documentation\03_Progress_Tracking\VERSION_HISTORY.md
   ```

3. **Session Summary - Six New Tables** - Details on v1.4.0.0 additions
   ```
   C:\RESA_Power_Build\Documentation\03_Progress_Tracking\SESSION_SUMMARY_NOV22_2025_SIX_NEW_TABLES.md
   ```

4. **Session Summary - Rollup Completion** - Details on v1.5.0.0 rollups
   ```
   C:\RESA_Power_Build\Documentation\03_Progress_Tracking\SESSION_SUMMARY_20251123_ROLLUP_COMPLETION.md
   ```

### Secondary (Cross-Reference)

5. **Revenue Architecture** - Financial table relationships (but outdated to v1.3.0.0)
   ```
   C:\RESA_Power_Build\Documentation\01_Architecture\REVENUE_ARCHITECTURE.md
   ```

6. **Hours Architecture Guide** - Rollup field logic (verify still accurate)
   ```
   C:\RESA_Power_Build\Documentation\01_Architecture\HOURS_ARCHITECTURE_GUIDE.md
   ```

---

## TASK CHECKLIST

### Phase 1: Inventory (30-45 min)

- [ ] Parse `customizations.xml` to extract complete field list per table
- [ ] Document all 16 tables with field counts
- [ ] Identify all relationships from XML
- [ ] List all calculated/rollup fields with their formulas

### Phase 2: Structure Update (45-60 min)

- [ ] Update document header to v1.5.0.0
- [ ] Add sections for 6 new tables (Client, Site, Employee, Quote, ResourceAssignment, Equipment)
- [ ] Add sections for 2 financial summary tables
- [ ] Update table count from 8 to 16
- [ ] Update field count from "350+" to "649"

### Phase 3: Field Documentation (60-90 min)

For each of the 8 NEW tables, document:
- [ ] All fields with logical names, display names, types
- [ ] Required vs optional
- [ ] Lookup relationships
- [ ] Choice field options
- [ ] Calculated field formulas

### Phase 4: Relationship Updates (30 min)

- [ ] Update ERD diagram (if present) or create one
- [ ] Document new 1:N and N:1 relationships
- [ ] Verify existing relationships still accurate

### Phase 5: Rollup Field Documentation (30 min)

- [ ] Document all 65 rollup/calculated fields
- [ ] Include formulas/aggregation logic
- [ ] Note which fields trigger which rollups

### Phase 6: Validation (15 min)

- [ ] Cross-reference against VERSION_HISTORY.md
- [ ] Verify table names match solution export
- [ ] Check field logical names are correct (cr950_ prefix)

---

## FIELD COUNT BY TABLE (Reference)

```
Table                          Fields  Category
------------------------------ ------  --------
cr950_Projects                   54    Core
cr950_ProjectScope               45    Core
cr950_Tasks                      43    Core
cr950_Apparatus                  47    Core
cr950_ApparatusRevenue           39    Core
cr950_ApparatusTypeMaster        25    Core
cr950_BusinessUnit               33    Core
cr950_scopelabordetails          50    Core (Financial)

cr950_Client                     43    New (v1.4.0.0)
cr950_Site                       39    New (v1.4.0.0)
cr950_Employee                   40    New (v1.4.0.0)
cr950_Quote                      54    New (v1.4.0.0)
cr950_ResourceAssignment         35    New (v1.4.0.0)
cr950_Equipment                  42    New (v1.4.0.0)

cr950_projectfinancialsummary    30    New (v1.5.0.0)
cr950_scopefinancialsummary      30    New (v1.5.0.0)
------------------------------ ------
TOTAL                           649
```

---

## OUTPUT REQUIREMENTS

### Deliverable

Updated `MASTER_BUILD_SPECIFICATION.md` that:
1. Accurately reflects v1.5.0.0 solution
2. Documents all 16 tables
3. Documents all 649 fields
4. Documents all relationships
5. Includes rollup field formulas
6. Has updated version header

### Quality Checks

- [ ] Every table in XML is documented
- [ ] Field logical names match XML exactly
- [ ] No references to v1.3.x remain (except in version history section)
- [ ] Diagrams updated or flagged for update

---

## NOTES

1. **Don't change the system** - This is documentation only
2. **XML is truth** - If doc says one thing and XML says another, XML wins
3. **Preserve good content** - The existing structure and explanations are good, just outdated
4. **Flag uncertainties** - If something is unclear, add a `<!-- TODO: Verify -->` comment

---

## QUESTIONS TO RESOLVE

If you encounter these, make a decision and document it:

1. Should the 6 new tables be in a separate section or integrated into the main table list?
2. Should financial summary tables be grouped with ScopeLaborDetail?
3. How detailed should rollup formula documentation be?

---

**Handoff prepared by:** Web Claude  
**Date:** November 27, 2025
