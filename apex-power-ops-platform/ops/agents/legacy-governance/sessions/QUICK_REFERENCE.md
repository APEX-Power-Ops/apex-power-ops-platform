# RESA Power - Quick Reference Card

*Print this or keep it handy for fast reference*

---

## 🚀 Session Start
```
READ: C:\RESA_Power_Build\Sessions\CURRENT_STATE.md
CHECK: C:\RESA_Power_Build\Sessions\HANDOFF.md
```

## 🛑 Session End
```
UPDATE: C:\RESA_Power_Build\Sessions\CURRENT_STATE.md
UPDATE: C:\RESA_Power_Build\Sessions\HANDOFF.md (if needed)
ADD: Entry to SESSION_LOG.md
```

---

## 🔗 Environment

| Setting | Value |
|---------|-------|
| Dataverse | https://org7bdbc942.crm.dynamics.com |
| Prefix | cr950_ |
| Tenant | 270d5723-4b30-4f3b-b9cb-6527be741b42 |

---

## 📊 Entity Names (V2)

| Friendly | EntitySetName |
|----------|---------------|
| Projects | cr950_projects |
| Clients | cr950_clients |
| Sites | cr950_sites |
| Scopes | cr950_scopes |
| Tasks | cr950_tasks |
| Apparatus | cr950_apparatuses |
| ScopeLaborDetails | cr950_scopelabordetails |
| Estimators | cr950_estimators |
| Locations | cr950_locations |

---

## 📁 Key Paths

| Purpose | Path |
|---------|------|
| Session State | `Sessions\CURRENT_STATE.md` |
| Handoffs | `Sessions\HANDOFF.md` |
| Templates | `Sessions\Templates\` |
| Docs | `Documentation\` |
| Archive | `Documentation\99_Archive\` |

---

## 🏷️ Status Tags

| Tag | Meaning |
|-----|---------|
| 🔴 | BLOCKED |
| 🟡 | IN PROGRESS |
| 🟢 | COMPLETE |
| ⚪ | NOT STARTED |
| 🔵 | WAITING |

---

## ⚡ Common Commands

**Query Dataverse:**
```
resa-dataverse:query_dataverse
entityName: "cr950_projects"
select: "cr950_projectname,cr950_projectnumber"
filter: "cr950_projectactive eq true"
```

**Read File:**
```
filesystem:read_text_file
path: "C:\RESA_Power_Build\Sessions\CURRENT_STATE.md"
```

**PowerShell:**
```
windows:Powershell-Tool
command: "Get-Date"
```

---

## 🔄 Hierarchy

```
Client
  └── Site
       └── Project
            └── Scope
                 ├── ScopeLaborDetail (1:1)
                 └── Task
                      └── Apparatus
                           └── ApparatusRevenue (future)
```

---

## ⚠️ Remember

1. ✅ Read CURRENT_STATE.md first
2. ✅ Update CURRENT_STATE.md last
3. ✅ Use V2 entity names
4. ✅ Archive, don't delete
5. ✅ One source of truth

---

*Quick Reference v1.0 - December 2025*
