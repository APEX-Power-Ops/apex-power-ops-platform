# Archive Notice

These files/folders are from the **Dataverse era** (pre-December 2025) and are no longer actively used.

The project has migrated to **Supabase** as the database backend.

## Files to Archive

### Can Remove
| File/Folder | Reason |
|-------------|--------|
| `MCP_Servers/` | Dataverse MCP server no longer needed |
| `Solution_Exports/` | Dataverse solution exports |
| `RESA_Power_Build.cdsproj` | Dataverse project file |
| `MASTER_SCHEMA.md` | Replaced by `Supabase/SCHEMA_REFERENCE.md` |
| `WORKSPACE_SYSTEM.md` | Replaced by `PROJECT_STATUS.md` |
| `COORDINATED_TASK_LIST.md` | Replaced by `PROJECT_STATUS.md` |
| `PROJECT_CONTEXT.json` | Dataverse-era environment snapshot moved behind archive boundary |
| `RESA_BLUE_SKY_ARCHITECTURE.md` | Legacy RESA-era strategy doc moved out of active root lane |
| `resa-blue-sky-architecture.jsx` | Legacy RESA-era prototype moved out of active root lane |

### Keep for Reference
| File/Folder | Reason |
|-------------|--------|
| `Documentation/` | Still relevant (specs, guides) |
| `Reference_Files/` | Excel trackers, PDFs needed |
| `CSV_Templates/` | Import templates still useful |
| `_archive/Dec2025_Dataverse/Root_Legacy/` | Root-level legacy context and prototype files retained for traceability |

## Current Active Files

| File | Purpose |
|------|---------|
| `PROJECT_STATUS.md` | **Start here** - Overall status |
| `PROJECT_OVERVIEW.md` | System architecture and platform intent |
| `README.md` | Unified repo entrypoint |
| `WORKSPACE_PROTOCOL.md` | Active repo operating rules |
| `WORKSPACE_DESIGN.md` | Workspace design reference |
| `.github/copilot-instructions.md` | Copilot context |
| `.claude/COORDINATION.md` | Claude session handoffs |
| `Supabase/` | All database schema and data |

---

## Root Legacy Archive

Historical root-level Dataverse-era context files and prototypes should be moved under `_archive/Dec2025_Dataverse/Root_Legacy/` rather than kept at the repository root.

This keeps the active root lane focused on current governance, status, architecture, and platform delivery materials.

---

*Created: December 5, 2025*
