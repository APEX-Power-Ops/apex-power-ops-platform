# Claude Session State

**Last Updated**: 2025-12-05 23:00  
**Current Phase**: APP CONNECTION  
**Status**: Supabase deployed, awaiting app swap

---

## Quick Status

| Component | Status | Next Action |
|-----------|--------|-------------|
| Database Schema | ✅ Deployed | - |
| Seed Data | ✅ Loaded | - |
| Test Data | ✅ Loaded (LASNAP16) | - |
| Node.js App | ✅ Found | Swap to Supabase |
| App ↔ Supabase | ⏳ Pending | VS Code Claude executing |

---

## What's Complete

### Database (Desktop Claude)
- ✅ 7 migrations applied to Supabase
- ✅ 24 tables created
- ✅ All triggers, views, indexes working
- ✅ Seed data: 5 locations, 15 apparatus_types, 6 templates
- ✅ Test data: LASNAP16 project, 4 scopes, 47 apparatus

### Application (VS Code Claude)  
- ✅ App located: `C:\Users\jjswe\Projects\resa-web-app`
- ✅ Framework: Next.js 16 + React 19 + shadcn/ui
- ✅ Structure documented in COORDINATION.md
- ✅ Supabase client library ready: `Supabase/lib/supabase.ts`

### Documentation (Both)
- ✅ OPEN_DECISIONS.md - Key decisions made
- ✅ SUPABASE_SWAP_GUIDE.md - Step-by-step for VS Code Claude
- ✅ COORDINATION.md - Task allocation
- ✅ ACTION_PLAN.md - Overall roadmap

---

## Current Task Allocation

### VS Code Claude - ACTIVE NOW
1. Read OPEN_DECISIONS.md
2. Execute SUPABASE_SWAP_GUIDE.md
3. Test app connects to Supabase
4. Update COORDINATION.md with results

### Desktop Claude - NEXT SESSION
1. Wait for VS Code Claude confirmation
2. Create Garney Excel migration script
3. Add any missing schema fields
4. Help debug app issues if needed

---

## Key Files

| Purpose | Path |
|---------|------|
| Task Coordination | `.claude/COORDINATION.md` |
| Decisions Made | `.claude/OPEN_DECISIONS.md` |
| VS Code Instructions | `.claude/SUPABASE_SWAP_GUIDE.md` |
| Supabase Credentials | `.secrets/SUPABASE_CREDENTIALS.md` |
| Supabase Client | `Supabase/lib/supabase.ts` |
| App Location | `C:\Users\jjswe\Projects\resa-web-app` |

---

## Supabase Project

| Setting | Value |
|---------|-------|
| Project Name | `resa-power-db` |
| Project Ref | `fxoyniqnrlkxfligbxmg` |
| API URL | `https://fxoyniqnrlkxfligbxmg.supabase.co` |
| Environment | Development |

---

## Session Rules Reminder

| Rule | Why |
|------|-----|
| Read STATE.md first | Instant context |
| Read COORDINATION.md | Know task allocation |
| Keep under 50 messages | Quality degrades after |
| Update STATE.md at end | Next session knows where we are |

---

## Resume Prompts

### Desktop Claude
```
Read C:\RESA_Power_Build\.claude\STATE.md and C:\RESA_Power_Build\.claude\COORDINATION.md, then continue RESA Power project.
```

### VS Code Claude
```
Read C:\RESA_Power_Build\.claude\COORDINATION.md and execute C:\RESA_Power_Build\.claude\SUPABASE_SWAP_GUIDE.md to connect the app to Supabase.
```

---

**Status**: Awaiting VS Code Claude to complete Supabase swap
