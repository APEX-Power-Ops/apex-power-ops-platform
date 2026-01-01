# RESA Power Platform - Open Decisions

**Purpose**: Capture all questions, discussions, and decisions needed before moving forward.  
**Status**: REVIEWED - Decisions Made 2025-12-05  
**Created**: 2025-12-05  
**Last Updated**: 2025-12-05 by Desktop Claude

---

## How to Use This Document

1. Review each section
2. Decisions marked: ✅ Decided | ❌ Rejected | ⏳ Deferred | ❓ Needs Discussion
3. Both Desktop and VS Code Claude should review before major work
4. User has final say on any decision marked ❓

---

## 1. DEPLOYMENT STATUS

### 1.1 Current State
| Item | Status | Notes |
|------|--------|-------|
| Schema (00-05) | ✅ Deployed | 7 migrations applied |
| Seed Data (10) | ✅ Loaded | locations, apparatus_types, estimators, templates |
| Test Data (11) | ✅ Loaded | LASNAP16 project, 47 apparatus |
| PSS Test Data (12) | ⏳ Optional | Can load if PSS testing needed |

### 1.2 Decisions Made
| Question | Decision | Rationale |
|----------|----------|-----------|
| Load test data to production? | ✅ **Separate instances** | Current = Dev, create Prod later |
| Keep predictable UUIDs in prod? | ✅ **No** | Supabase default for prod, predictable for test only |
| Verify triggers after data load? | ✅ **Spot check** | VS Code Claude verified rollup triggers work |

---

## 2. DATA ARCHITECTURE

### 2.1 Source Data Decisions
| Question | Decision | Rationale |
|----------|----------|-----------|
| Dataverse data migration needed? | ✅ **No** | User confirmed "Dataverse was a shell" |
| Historical data to import? | ✅ **From Excel trackers** | 4-7 active project trackers |
| Data validation on import? | ✅ **Lenient with logging** | Get data in, fix issues iteratively |

### 2.2 UUID Strategy
| Question | Decision | Rationale |
|----------|----------|-----------|
| Production UUID generation | ✅ **Supabase default** | gen_random_uuid() |
| Cross-reference old IDs? | ✅ **None needed** | No legacy system to map |

### 2.3 Multi-tenancy
| Question | Decision | Rationale |
|----------|----------|-----------|
| Single tenant or multi? | ✅ **Single tenant** | RESA Power only, simplifies everything |
| If multi: isolation method | N/A | Single tenant decision |

---

## 3. SECURITY

### 3.1 Row Level Security (RLS)
| Question | Decision | Rationale |
|----------|----------|-----------|
| Enable RLS? | ⏳ **Deferred** | Enable when auth is implemented |
| RLS policy scope | ⏳ **Deferred** | Likely by location + role |
| Anonymous access allowed? | ✅ **Yes for dev** | anon key for internal dev/testing |

### 3.2 Authentication
| Question | Decision | Rationale |
|----------|----------|-----------|
| Auth provider | ✅ **Phased approach** | Phase 1: anon key, Phase 2: Supabase Auth, Phase 3: optional MSAL SSO |
| Link to employees table? | ✅ **Yes** | auth.users.id → employees.auth_user_id |
| Role management | ✅ **Use existing ENUM** | role_type ENUM already defined |

**Auth Implementation Plan**:
1. **Now**: Use Supabase anon key (no login required) for internal dev
2. **Week 2-3**: Add Supabase Auth with email/password for field techs
3. **Later**: Consider MSAL integration for corporate SSO (optional)

### 3.3 API Security
| Question | Decision | Rationale |
|----------|----------|-----------|
| Expose all tables via API? | ✅ **Allowlist via RLS** | When RLS enabled, controls access |
| Rate limiting | ✅ **Supabase default** | Sufficient for internal app |
| Audit logging | ✅ **pss_activity_log + triggers** | Activity log exists, triggers log key actions |

---

## 4. APPLICATION ARCHITECTURE

### 4.1 Frontend
| Question | Decision | Rationale |
|----------|----------|-----------|
| Frontend framework | ✅ **Next.js 16** | Already built, continue |
| Component library | ✅ **shadcn/ui** | Already integrated, professional look |
| State management | ✅ **React Query** | Best for Supabase, handles caching |
| Hosting | ⏳ **TBD** | Vercel likely, decide at deploy time |

### 4.2 API Patterns
| Question | Decision | Rationale |
|----------|----------|-----------|
| Primary API | ✅ **Supabase JS Client** | supabase.ts ready to use |
| Use database views? | ✅ **Yes for dashboards** | v_project_dashboard, v_pss_dashboard exist |
| Real-time subscriptions | ✅ **Yes for apparatus** | Field updates show instantly |

### 4.3 File Storage
| Question | Decision | Rationale |
|----------|----------|-----------|
| Document storage | ✅ **Supabase Storage** | Simplest, integrated with auth |
| File path strategy | ✅ **Structured folders** | `{project_id}/{document_type}/{filename}` |
| Max file size | ✅ **50MB** | Covers test reports, PDFs |

---

## 5. BUSINESS LOGIC

### 5.1 Revenue Recognition
| Question | Decision | Rationale |
|----------|----------|-----------|
| Auto-create revenue records? | ✅ **On apparatus complete** | Trigger exists and tested |
| Recognition timing | ✅ **Immediate** | When status = COMPLETE |
| Partial recognition allowed? | ✅ **Yes** | recognition_percent field supports this |

### 5.2 Project Workflow
| Question | Decision | Rationale |
|----------|----------|-----------|
| Required status progression? | ✅ **Flexible** | Don't block users, log changes |
| Who can change status? | ✅ **Any authenticated user** | Add restrictions later if needed |
| Notifications on status change? | ⏳ **Deferred** | Nice to have, not MVP |

### 5.3 PSS Portal Workflow
| Question | Decision | Rationale |
|----------|----------|-----------|
| External engineer access? | ⏳ **Deferred** | PSS Portal is Phase 2 |
| Document approval workflow? | ⏳ **Deferred** | PSS Portal is Phase 2 |
| RFI auto-assignment? | ⏳ **Deferred** | PSS Portal is Phase 2 |

---

## 6. INTEGRATIONS

### 6.1 External Systems
| Question | Decision | Rationale |
|----------|----------|-----------|
| Accounting system | ⏳ **Deferred** | No immediate need |
| CRM integration | ⏳ **Deferred** | No immediate need |
| Calendar/scheduling | ⏳ **Deferred** | Consider Google Calendar later |
| Email integration | ⏳ **Deferred** | Add when notifications needed |

### 6.2 Dataverse Relationship
| Question | Decision | Rationale |
|----------|----------|-----------|
| Keep Dataverse running? | ✅ **Retire** | Was a shell, Supabase replaces it |
| If parallel: sync strategy | N/A | Retiring Dataverse |

---

## 7. DOCUMENTATION

### 7.1 What's Complete
- [x] README.md - Schema overview
- [x] QUICK_START.md - Deployment guide
- [x] DATA_DICTIONARY.md - Field definitions
- [x] ENTITY_RELATIONSHIPS.md - FK mappings
- [x] ENUM_DEFINITIONS.md - Value definitions
- [x] TRIGGER_FLOWS.md - Automation logic
- [x] VIEW_DEFINITIONS.md - View purposes
- [x] TEST_DATA_PLAN.md - Test data design
- [x] V1513_FIELD_REFERENCE.md - Dataverse mapping
- [x] supabase.ts - Client library ready
- [x] FIELD_TECH_APPLICATION_SPEC.md - UI/UX design
- [x] REVENUE_RECOGNITION_FLOW_SPEC_V2.md - Business logic

### 7.2 Documentation Gaps
| Document | Priority | Owner | Status |
|----------|----------|-------|--------|
| SUPABASE_SWAP_GUIDE.md | **HIGH** | Desktop Claude | ✅ Creating now |
| API_USAGE.md | Medium | VS Code Claude | After swap |
| SECURITY_SETUP.md | Medium | Desktop Claude | When RLS added |
| DEPLOYMENT_RUNBOOK.md | High | TBD | Before prod |

---

## 8. OPERATIONAL

### 8.1 Environments
| Question | Decision | Rationale |
|----------|----------|-----------|
| How many environments? | ✅ **2 (dev + prod)** | Start with dev, create prod for go-live |
| Current Supabase project is | ✅ **Development** | `resa-power-db` = dev |
| Data refresh strategy | ✅ **Synthetic** | Use test data scripts |

### 8.2 Backup & Recovery
| Question | Decision | Rationale |
|----------|----------|-----------|
| Backup frequency | ✅ **Supabase default** | Daily automatic |
| Point-in-time recovery | ⏳ **Evaluate for prod** | May need Pro plan |
| Backup testing | ⏳ **Ad-hoc** | Test before go-live |

### 8.3 Monitoring
| Question | Decision | Rationale |
|----------|----------|-----------|
| Performance monitoring | ✅ **Supabase dashboard** | Built-in, sufficient for now |
| Error alerting | ⏳ **Deferred** | Add when in production |
| Usage tracking | ✅ **Built-in** | Supabase provides this |

---

## 9. TIMELINE & PRIORITIES

### 9.1 Phase Decisions
| Phase | Scope | Target | Status |
|-------|-------|--------|--------|
| **Phase 1** | Field testing tracker + dashboard | This week | 🔄 Active |
| **Phase 2** | Migrate 4-7 Excel trackers | Next 2 weeks | Queued |
| **Phase 3** | Financial module (revenue tracking) | Month 2 | Queued |
| **Phase 4** | PSS Portal | Month 2-3 | Deferred |
| **Phase 5** | Integrations | TBD | Deferred |

### 9.2 Go-Live Criteria (Phase 1 MVP)
| Criterion | Required? | Status |
|-----------|-----------|--------|
| Schema deployed | Yes | ✅ |
| Seed data loaded | Yes | ✅ |
| Test data validated | Yes | ✅ |
| App connected to Supabase | Yes | ⏳ VS Code Claude |
| Project list view working | Yes | ⏳ |
| Apparatus status updates | Yes | ⏳ |
| Basic dashboard | Yes | ⏳ |
| Real project migrated | Yes | ⏳ Garney 677562 |
| RLS enabled | No | Deferred |
| User training | No | Deferred |

---

## 10. IMMEDIATE TASK ALLOCATION

### Desktop Claude - Next Actions
1. ✅ Create SUPABASE_SWAP_GUIDE.md for VS Code Claude
2. ⏳ Create Garney Excel → Supabase migration script
3. ⏳ Add any missing schema fields (AVAILABILITY, PRIORITY)
4. ⏳ Document dashboard SQL queries

### VS Code Claude - Next Actions
1. ⏳ Read SUPABASE_SWAP_GUIDE.md
2. ⏳ Install @supabase/supabase-js
3. ⏳ Copy supabase.ts to app
4. ⏳ Add env variables
5. ⏳ Update page.tsx imports
6. ⏳ Test connection

---

## Decision Log

| Date | Decision | Made By | Notes |
|------|----------|---------|-------|
| 2025-12-05 | Dataverse was shell, no migration | User | Confirmed in chat |
| 2025-12-05 | Build for long-term, not bandaid | User | Quality over speed |
| 2025-12-05 | Continue Next.js app | User | VS Code Claude built it |
| 2025-12-05 | Single tenant (RESA only) | Desktop Claude | Simplifies architecture |
| 2025-12-05 | Phased auth approach | Desktop Claude | Anon → Supabase Auth → MSAL |
| 2025-12-05 | Current Supabase = Dev | Desktop Claude | Create prod instance later |
| 2025-12-05 | PSS Portal deferred | User + Desktop Claude | Field tracker is priority |
| 2025-12-05 | Retire Dataverse | User | Supabase replaces it |

---

**Next Review**: After VS Code Claude completes Supabase swap  
**Document Owner**: Both Claudes + User
