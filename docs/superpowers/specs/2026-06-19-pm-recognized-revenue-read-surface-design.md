# PM Recognized-Revenue Read Surface — Design

**Date:** 2026-06-19
**Lane:** Operations (PM) — execution→billing chain. Bounded packet: the recognized-revenue READ surface.
**Status:** Design for review (brainstorming output). No implementation yet.

**Goal:** Surface recognized + billable revenue per project/scope in the operations-web PM
management end, derived live from apparatus completion × quoted revenue — a read-only bounded
packet that promotes the held `finance-placeholder` branch into a real finance read view.

**Approach (chosen — A):** derive-on-read in the control-plane API. No prod DDL, no writes, no
new authority. The empty `seam.apparatus_revenue_events` ledger is the future durable backing
(Chip 3); this packet derives recognized revenue from the populated base tables.

---

## Reality this is built on (verified in prod 2026-06-19, read-only)
- `public.apparatus` (47 rows) carries `quoted_revenue` (all populated), `status`
  (`apparatus_status` enum; `'Complete'` = done), `scope_id`, `is_active`, `quoted_hours`.
- The recognition tables (`public.apparatus_revenue`, `public.project_financial_summaries`,
  `public.scope_financial_summaries`, `seam.apparatus_revenue_events`,
  `seam.project_contract_snapshots`) EXIST but are EMPTY → recognized revenue is uncomputed and
  must be DERIVED.
- The existing PM rollups (`public.v_master_operations`, `public.v_project_apparatus_summary`)
  already define "completed" as `status = 'Complete'` over
  `projects ⋈ scopes(is_active) ⋈ apparatus(is_active)` with `p.is_active = true`.

## Recognition contract (the core rule)
Reuse the EXACT completion predicate from the existing views so the money view agrees with the
completion counts shown elsewhere.

Per apparatus: `recognized = quoted_revenue WHERE status = 'Complete' ELSE 0` (binary, recognized
at completion — D-OPS-8).

Rollup (scope grain; project totals rolled up in the UI):
- `quoted_revenue      = COALESCE(SUM(a.quoted_revenue), 0)`
- `recognized_revenue  = COALESCE(SUM(a.quoted_revenue) FILTER (WHERE a.status = 'Complete'), 0)`
- `recognition_percent = round(recognized_revenue / NULLIF(quoted_revenue,0) * 100, 2)` (0 when quoted = 0)
- `billable_now        = recognized_revenue - billed_to_date` (billed_to_date = 0 today ⇒ billable = recognized; column retained for the future billing packet)
- context: `total_apparatus`, `completed_apparatus`

Joins/filters: `projects p LEFT JOIN scopes s ON s.project_id = p.id AND s.is_active
LEFT JOIN apparatus a ON a.scope_id = s.id AND a.is_active WHERE p.is_active`
(+ project status ∈ {Active, Won, In Progress} for the project list, matching `v_master_operations`).

## Architecture (3 layers — mirrors the existing PM read path)
1. **Data (read-only):** prod `public.apparatus/scopes/projects` in deploy; a **seeded host dev
   slice** of the same shape on host dev-pg for hermetic tests.
2. **control-plane-api** (`services/ops/`): new read endpoint `GET /api/v1/ops/revenue-recognition`
   returning scope-grain rows; Pydantic `RevenueRecognitionRow`; bounded `limit`; parameterized
   SQL; mirrors the existing ops read endpoints.
3. **operations-web:** `lib/revenue-recognition.ts` typed fetch helper (mirrors
   `project-apparatus-summary.ts`); new route `app/pm-review/finance/page.tsx` (the admitted read
   view); update `finance-placeholder` to record that the finance READ branch is admitted at
   `/pm-review/finance` while all write branches stay held.

## Data flow
browser `/pm-review/finance` → `fetchRevenueRecognition(limit)` →
`GET {controlPlaneBaseUrl}/api/v1/ops/revenue-recognition?limit=N` → control-plane runs the
recognition SQL against its DSN → scope-grain rows → page groups by project and renders project
totals (quoted / recognized / % / billable) + scope breakdown + an honesty note.

## Honesty / labeling (L5 discipline)
The view states plainly: "Recognized = quoted revenue of apparatus marked Complete (binary, at
completion), derived live from apparatus status — not yet a persisted recognition ledger.
Billable = recognized − billed; billing is not yet admitted, so billable = recognized." No
implied authority beyond a read.

## Components (files)
- control-plane-api: `services/ops/router.py` (endpoint + `RevenueRecognitionRow` model + SQL);
  `tests/test_ops_revenue_recognition.py`.
- operations-web: `lib/revenue-recognition.ts`; `app/pm-review/finance/page.tsx`; update
  `app/pm-review/finance-placeholder/page.tsx`; `tests/browser-shell.pm-finance.smoke.spec.ts`
  + a unit test for the pure project-rollup helper.
- dev DB: `infra/database/dev-fixtures/pm_public_slice.sql` — minimal `public` enums
  (`apparatus_status`, `apparatus_availability`) + `projects/scopes/apparatus` tables + a
  deterministic seed for hermetic control-plane tests on host dev-pg.

## Error handling
- Endpoint: bounded `limit`, returns `[]` when no data, standard FastAPI error envelope (mirror
  existing ops endpoints).
- Lib helper: typed `RevenueRecognitionError(status)`; page renders an error state.
- Math: quoted = 0 ⇒ percent 0 (NULLIF guard, matches the views' CASE); no completed apparatus ⇒
  recognized 0 (honest "nothing recognized yet").

## Testing (TDD)
- control-plane: seed deterministic rows (e.g., a scope with 3 apparatus, 2 Complete) → assert
  exact recognized / quoted / percent / billable; edges: zero quoted, inactive scope/apparatus
  excluded, empty project. Hermetic against the host dev slice (NOT prod).
- operations-web: unit-test the pure project-rollup aggregation; browser smoke (route renders,
  shows the numbers + honesty note) mirroring the existing pm smokes.

## Non-goals (held boundaries — bounded admission)
No writes / POST, no recognition-ledger writes, no billing / invoice / payroll / accounting /
export, no customer-facing artifacts, no prod DDL, no new authority. `customer-billing`,
`source-writeback`, `financial-handoff` (write), and finance export all stay held placeholders.

## Future (sets up the next packets; out of scope here)
- Chip 3 (write packet): populate the append-only `seam.apparatus_revenue_events` ledger on
  completion; the endpoint then reads the ledger instead of deriving — the UI contract is unchanged.
- Billing packet: real `billed_to_date` from billing records ⇒ `billable = recognized − billed`.
