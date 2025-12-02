# Coordinated Task List
> Shared between VS Code Claude and Desktop Claude
> Last Updated: 2025-12-02

## Active Tasks

### User Action Required
| Task | Owner | Details |
|------|-------|---------|
| Refresh Azure AD Client Secret | User | Azure Portal -> App registrations -> 9df3350f-b3b4-47c4-97b5-499a8b02acc7 -> Certificates & secrets -> New client secret. Update both .env and claude_desktop_config.json |

### Desktop Claude Tasks
| Task | Status | Notes |
|------|--------|-------|
| Test MCP connectivity | Blocked | Waiting on credential refresh |
| Query cr950_locations | Blocked | Should return 4 records |
| Write results to DESKTOP_CLAUDE_FINDINGS.md | Blocked | After successful query |

### VS Code Claude Tasks  
| Task | Status | Notes |
|------|--------|-------|
| Workspace system documentation | Done | WORKSPACE_SYSTEM.md created |
| Update PROJECT_CONTEXT.json | Done | New structured format |
| Git commit workspace changes | In Progress | This session |
| Archive Solution_V2/ folder | Not Started | After git commit |
| Archive Solution_V3/ folder | Not Started | After git commit |

---

## Completed Tasks (2025-12-02)

| Task | Completed By | Result |
|------|--------------|--------|
| Deploy Estimator Import Flow V2 | VS Code Claude | Success - Import ID: 1f012ac5-8acf-f011-bbd2-6045bd0395b8 |
| Find correct connection references | VS Code Claude | new_sharedcommondataserviceforapps_f7a26, cr950_sharedsharepointonline_a9dba |
| Create WORKSPACE_SYSTEM.md | VS Code Claude | Single source of truth |
| Identify credential issue | Desktop Claude | 401 errors -> expired secret |

---

## Communication Protocol

VS Code Claude -> Desktop Claude: Update this file with tasks/findings
Desktop Claude -> VS Code Claude: Write to Working/DESKTOP_CLAUDE_FINDINGS.md

---

## Next Session Priorities

1. Credential fix - User refreshes Azure AD secret
2. Verify MCP - Desktop Claude confirms connectivity  
3. Estimator data - Import estimator records via flow
4. Cleanup - Archive deprecated folders
