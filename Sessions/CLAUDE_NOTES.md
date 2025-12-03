# Claude Notes - Quick Context for Next Session

**Read this first.** This tells you where we are and what matters right now.

---

## 🧠 Your Role (Important!)

**You are a stakeholder in this project, not just an executor.**

Jason expects you to:
- **Question decisions** - "Is this the best way forward?"
- **Suggest alternatives** - Don't just implement what's asked; offer better options if you see them
- **Ask why** - Understanding intent leads to better solutions
- **Think like an owner** - This is your project too

**There's no ego here.** Jason wants the best option, not his option. He doesn't care where the idea came from. If you see a better way, say it. The discussions that happen when you push back and challenge assumptions are where the best work gets done.

Don't be passive - be a thinking partner.

---

## 🎯 Right Now (December 2, 2025)

**Environment:** org7bdbc942.crm.dynamics.com (the ONLY correct one)  
**Branch:** clean-main  
**Solution:** RESA_Power_Build_V2 v1.0.0.5

### Where We Are
We just rebuilt the financial architecture. 3 new tables exist but need lookup fields added manually (API can't do it). Jason wants Financial/Operations separation for role-based visibility.

### Recent Side Project: PowerDB Schema Audit
Completed comprehensive audit of PowerDB test form database (80 tables, 1209 columns, 163 GUIDs). Documentation in `Documentation/06_Implementation_Guides/POWERDB_*.md/csv`. Key insight: Use `JobNumber` as natural key for integration - no complex GUID sync needed.

### What's Working
- MCP server at `MCP_Servers/resa-dataverse-mcp/` - use `node build/index.js` to start
- 12 tables in Dataverse (9 core + 3 financial)
- All basic CRUD operations via API

### What's Broken/Blocked
- **7 lookup fields missing** - Must add via Power Apps UI, not API
- **Flows not built yet** - Need lookups first
- Can't import old flows - schema names changed too much

### Jason's Preferences (Important!)
- Wants separation pattern: financial tables separate from operational
- Values "reliability and consistency" over speed
- Likes checkpoint documentation before rushing ahead
- Appreciates decision rationale being captured

---

## 📍 Key Locations

| Need | Location |
|------|----------|
| Current build status | `Documentation/03_Progress_Tracking/BUILD_STATUS_2025-12-02.md` |
| Why decisions were made | `Documentation/03_Progress_Tracking/SESSION_DECISIONS_2025-12-02.md` |
| Revenue architecture spec | `Documentation/02_Build_Guides/REVENUE_RECOGNITION_BUILD_SPEC.md` |
| Old working flow (reference) | `Solution_Exports/Archive/v1.5.1.3/Workflows/RevenueRecognition*.json` |
| Current clean export | `Solution_Exports/v1.0.0.5/customizations.xml` |

---

## ⚠️ Gotchas

1. **Wrong environments exist** - org99cd6c6e and org284447bd are DEPRECATED. Only use org7bdbc942.
2. **Schema names changed** - Old: `cr950_projectscope`, New: `cr950_scope`. Check mapping in BUILD_STATUS doc.
3. **Lookup fields via API = 404** - Dataverse Web API can't create lookups. Don't waste time trying.
4. **Choice field for triggers** - We use `cr950_completion_status` (Choice: 1=Planned, 2=Complete), NOT a string field.

---

## 🔜 Likely Next Steps

1. **If Jason asks about schema review** → Claude Desktop was assigned to compare v1.0.0.5 vs v1.5.1.3
2. **If Jason wants to add lookups** → Guide him through Power Apps UI (make.powerapps.com)
3. **If Jason wants to build flows** → Need lookups first, then start with ScopeLaborDetail rate calculation
4. **If Jason asks about the old build** → Reference `Solution_Exports/Archive/v1.5.1.3/` but don't import - adapt instead

---

## 📝 Last Session Summary (VS Code Claude, Dec 2)

Created 3 financial tables, added trigger fields to Apparatus, documented everything. Session ended at a good checkpoint - all committed to git. Claude Desktop was given schema review task but ran out of context space.

---

*Update this file before ending your session. Keep it short and useful.*
