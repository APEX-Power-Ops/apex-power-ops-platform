# PM Schema Foundation Plan v2 Synthesis - Completion Handoff

**Date:** 2026-05-26 15:48 America/Phoenix  
**Dispatch:** PM_SCHEMA_FOUNDATION_PLAN_V2_HYBRID_SYNTHESIS_2026-05-26  
**Matrix item:** #65  
**Status:** CLOSED WITH FINDINGS  
**Executor:** Codex  
**Commit/push:** Not performed.

## 1. Deliverables

Produced:

1. `C:\APEX Platform\.claude\PLATFORM\PM_SCHEMA_FOUNDATION_PLAN_v2_2026-05-26.md`
2. `C:\APEX Platform\.claude\PLATFORM\PM_SCHEMA_FOUNDATION_PLAN_V2_MATRIX_DELTA_2026-05-26.md`
3. `C:\APEX Platform\apex-power-ops-platform\.claude\HANDOFFS\2026-05-26-1548-pm-schema-foundation-plan-v2-synthesis-completion-handoff.md`

Also created the missing deliverable directory:

- `C:\APEX Platform\apex-power-ops-platform\.claude\HANDOFFS\`

## 2. Summary

The v2 plan reframes the PM schema foundation as a three-input hybrid: live `public.*`, live `seam.*`, and net-new operator-policy substrate. The key recommendation is to preserve `pm_core` as the PM-specific namespace name but narrow it to new evidence/event/decision tables first, rather than replacing or renaming existing public/seam operational tables. Revenue-recognition remains PM-substrate-internal directionally, but implementation should reconcile existing public revenue tables and seam Lane 411 snapshot/event tables, with Lane 411's recognition firewall treated as load-bearing.

## 3. Validation Log

### Files read

| File | Result |
|---|---|
| `C:\APEX Platform\.claude\PLATFORM\SUPABASE_PUBLIC_SCHEMA_REFERENCE.md` | Present; 8,235 lines |
| `C:\APEX Platform\.claude\PLATFORM\PM_SCHEMA_FOUNDATION_PLAN_2026-05-26.md` | Present; 456 lines |
| `C:\APEX Platform\.claude\PLATFORM\OPERATOR_DECISION_MATRIX_2026-05-25.md` | Present; 756 lines |
| `C:\APEX Platform\.claude\PLATFORM\METHODOLOGY_PATTERNS.md` | Present; PATTERN-005 read |
| `C:\APEX Platform\.claude\PLATFORM\STATE.md` | Present; sections 32 and 33 read |
| `C:\APEX Platform\apex-power-ops-platform\PROJECT_STATUS.md` | Present; 2,307 long ledger lines; targeted PM Lane blocks read |
| `C:\APEX Platform\apex-power-ops-platform\PROJECT_OVERVIEW.md` | Present; 401 lines |
| `C:\APEX Platform\.claude\PLATFORM\ESTIMATOR_ARCHITECTURE.md` | Present; 593 lines |
| `C:\APEX Platform\.claude\PLATFORM\TRACKER_ARCHITECTURE.md` | Present; 415 lines |
| `C:\APEX Platform\.claude\PLATFORM\EXCEL_TO_DATABASE_RECONSTRUCTION.md` | Present; 251 lines |

The dispatch's architecture-doc paths under `apex-power-ops-platform\docs\architecture\` were missing. Current copies under `.claude\PLATFORM\` were read and used.

### Supabase read-only queries

Executed read-only queries/tools:

- `list_tables` for schema `seam` with columns: succeeded; 28 tables returned.
- Public/seam base table count SQL: public=125, seam=28.
- Public/seam RLS posture SQL: public RLS disabled=66/enabled=59; seam RLS disabled=11/enabled=17.
- Public core row-count SQL: projects=1, scopes=4, tasks=12, apparatus=47, resource_assignments=8, scope_labor_details=6, apparatus_revenue=0, summaries=0.
- Seam PM row-count SQL: workpackages=7, projects=1, tasks=15, apparatus=184, scopes=0, assignments=184, audit_log=392, idempotency_keys=572, Lane 411 financial tables=0.
- Trigger inventory SQL: public/seam trigger rows returned=92.
- Enum inventory SQL: public enums=43, seam enums=4.
- TCC table-count SQL: public `tcc_%` base tables=62, `*_pre_rebuild` base tables=20.

`list_tables` for public and advisory notices returned connector authorization errors. This did not block synthesis because public reference staleness was checked with read-only SQL and detailed public schema content was available locally.

## 4. What Worked / What Didn't / What Could Be Enhanced

### Live public schema

**What worked:** Broad relational PM spine; non-null apparatus scope binding; rich apparatus workflow fields; 43 typed enums; trigger-maintained rollup/read-model ideas; substantial adjacent reference domains including TCC, study, safety, and PSS.

**What didn't:** RLS disabled on many core tables; public mixes too many domains for one PM substrate; operational rows embed quote/revenue fields; `actual_revenue` conflicts with Lane 411 vocabulary; revenue summary tables are structural but unpopulated.

**Enhancements:** RLS policy lane; domain ownership map; deprecate/reframe actual revenue fields; preserve trigger patterns as read-model support only; add TCC fourth-tier matrix item.

### Live seam schema

**What worked:** Active PM row gravity; idempotency and audit infrastructure; insert-only event patterns; role-separated revenue-recognition design; contract snapshots and event ledger architecture.

**What didn't:** 11 RLS-disabled tables; scopes still empty; Lane 411 financial tables empty; JSONB-heavy older operational tables; implicit public/seam boundary.

**Enhancements:** RLS policies before live expansion; scope insertability repair; require idempotency/audit ids in future PM events; explicitly document seam/public/pm_core responsibilities.

### Foundation plan v1

**What worked:** Estimator-first intake, five-phase workflow, P3/P4/M4/N4 capture, fixed scope binding, PM task flexibility, `pm_core` as useful namespace name.

**What didn't:** Treated public too much like concept, overcommitted to greenfield replacement, invented revenue table names without existing-schema reconciliation, missed RLS and public TCC fourth tier.

**Enhancements:** Convert `pm_core` to new-table overlay first; add security posture as first-class; reconcile revenue with Lane 411 and public tables; add cross-domain boundaries.

### Operator-policy substrate

**What worked:** Matrix preserved enough history to revise without pretending prior closures vanished. #8/#9/#26 remain strong and actionable.

**What didn't:** #4, #33 Q1, and #33 Q6 were closed before full live-substrate inspection. Path drift existed for the three architecture docs.

**Enhancements:** Add a schema-closure verification pattern: for schema-impacting matrix closures, require table count, RLS, trigger, enum, and existing-table reconciliation before SQL authoring is declared unblocked.

## 5. What's Now Actionable

- Operator can review v2 and apply matrix deltas.
- `pm_core` Packet B can be scoped as a new-table intake-envelope packet if operator accepts new-tables-only posture.
- RLS policy design packet can be scoped immediately and arguably should precede live PM admission expansion.
- Revenue-recognition follow-on can be scoped around Lane 411 custody and public `actual_revenue` disposition.

## 6. What's Still Open

- Public/seam RLS policy sequencing.
- Lane 411 table custody: stay in seam, mirror to pm_core, or future rename.
- Public `actual_revenue` disposition.
- Identity source for RLS: seam users/roles versus Supabase Auth/profile.
- Scope correction authority and validation waiver authority.
- Whether any public/seam rows are backfilled into future pm_core tables.

## 7. New Questions Surfaced

1. Should RLS remediation block all future PM SQL packets, or only live-admission packets?
2. Should public TCC Reference be added to matrix #28 as a fourth tier or split into a new item?
3. Is `pm_core` intended to become a replacement namespace eventually, or remain an overlay indefinitely?
4. Should `audit_events` supersede `audit_log`, and if so when?
5. Should trigger-driven public rollups be preserved as views/materialized summaries rather than table writes?

## 8. Methodology Pattern Proposal

Potential PATTERN-006 candidate: **Schema-closure verification before SQL unblocking.**

Trigger: any matrix closure or foundation plan that authorizes schema packet authoring. Required checks: live table count, RLS posture, existing table/function/trigger inventory, row-count gravity, existing domain ownership, and explicit "new vs alter vs rename vs bridge" decision. This packet is the worked example because Q1/Q6 were directionally right but structurally incomplete before live inspection.

## 9. Guardrails Preserved

- No SQL mutation executed.
- No RLS remediation applied.
- No code files modified.
- No `.env` files opened.
- No `.secrets/` recursion.
- No commits, pushes, or staging.
- No prior matrix closures auto-reopened.
- No cross-repo writes outside requested markdown deliverables.
- PATTERN-005 subsection included in both v2 plan and this closeout.

## 10. Push State

Uncommitted local deliverables only. Operator decides commit and push policy separately.

