# APEX PM Lane 411 - Project Miner Temp Power Apparatus Completion Revenue Recognition No-Live Design Packet

Date: 2026-05-20

Status: Documentation-only no-live design packet for apparatus-completion-triggered revenue recognition, classified from the PM Lane 352 remaining finance/source answer-card family under `OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED`

Decision label:

`PROJECT_MINER_TEMP_POWER_APPARATUS_COMPLETION_REVENUE_RECOGNITION_NO_LIVE_DESIGN_NO_OUTPUT_WRITE`

## Purpose

PM Lane 411 converts the current apparatus-completion revenue-recognition proposal into a bounded no-live design surface.

The proposal is correctly classified under PM Lane 352's return label `OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED` because it describes future revenue-recognition writes, scope-financial derivations, and a status-mutation side effect. This lane does not admit those writes. It authors the contract, schema, derivation, and gating design required before any later schema or live-write packet can be considered.

This lane ports the preserved public reference pattern into `seam.*` under the insert-only discipline already used by PM Lanes 281 through 284:

| Preserved reference | Proposed seam design |
| --- | --- |
| `public.scope_labor_details` | `seam.scope_labor_details` |
| `public.projects.contract_value` | `seam.project_contract_snapshots` |
| `public.apparatus.quoted_hours`, `quoted_revenue` | new columns on `seam.apparatus` |
| `public.apparatus_revenue` | `seam.apparatus_revenue_events` |
| `public.v_scope_financials` | `seam.v_scope_financials` |

This lane is documentation-only. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, live revenue event, billing export, payroll export, invoice, accounting post, customer billing delivery, external finance sync, source workbook/PDF writeback, workbook macro, change-order admission, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`APPARATUS_COMPLETION_REVENUE_RECOGNITION_DESIGN_READY_NO_LIVE`

Meaning:

1. The recognition model is fixed to project-level contract revenue recognized by apparatus completion through one frozen hours-weighted rate.
2. The four estimator pools remain separate imported metadata for cost analysis and reporting, not separate recognition engines.
3. The import-side amendment and the apparatus-status mutation extension are defined, but neither is admitted live.
4. Change-order-ready snapshoting is designed now without requiring future snapshot-kind enum migrations.
5. All live revenue output, finance output, public schema writes, source writeback, and change-order execution remain separately blocked.

## Recognition Model

Project-level recognition rate, frozen at contract sign or import snapshot creation:

```text
recognition_rate_per_hour
  = project_contract_snapshot.contract_value
  / project_contract_snapshot.total_quoted_hours
  = SUM(scope_labor_details.quoted_amount)
  / SUM(apparatus.quoted_hours)
```

Per-apparatus quoted revenue, computed at import time and then frozen against the chosen snapshot:

```text
apparatus.quoted_revenue
  = apparatus.quoted_hours * snapshot.recognition_rate_per_hour
```

Recognition event on PM disposition of apparatus status to `Complete`:

```text
recognized_amount = apparatus.quoted_revenue
recognition_percent = 100
```

Pool-level recognition is derived only in the scope-financial view:

```text
pool_recognized
  = SUM(apparatus_revenue_events.recognized_amount)
    * (pool.quoted_amount / snapshot.contract_value)
```

Mixed-rate projects need no special case. The estimator workbook already blends 10-hour, 12-hour, OT, and DT labor rates into the quoted pool totals. The recognition rate inherits that blend automatically because it is derived from total adjusted contract value divided by total quoted hours.

## Snapshot Strategy And Design Correction

The current design must preserve a visible `snapshot_kind` field while also allowing future `change_order_N` values without forcing new enum migrations.

Because a literal PostgreSQL enum cannot support an unbounded family such as `change_order_1`, `change_order_2`, and so on without later DDL, the recommended design is:

```text
snapshot_kind TEXT NOT NULL
CHECK (
  snapshot_kind = 'original'
  OR snapshot_kind ~ '^change_order_[1-9][0-9]*$'
)
```

This keeps the public contract name `snapshot_kind` while preserving the requirement that later change orders fit the same table without migration churn.

V1 writes exactly one snapshot per project with `snapshot_kind = 'original'`.

Future change orders use new snapshot rows, not updates in place.

## Named Multi-Scope Allocation Assumption

This lane makes one explicit normalization assumption for multi-scope projects:

```text
scope_pool_amount = project_pool_amount * (scope_hours / project_hours)
```

That rule is not incidental implementation detail. It is the governing design assumption behind:

1. Lane 278's pool-to-scope import allocation,
2. apparatus-level quoted revenue reconciliation back to the project snapshot,
3. scope-level `v_scope_financials` pool-recognition derivation.

If a future project wants travel, outside services, or any other pool allocated by a different rule such as equal split, apparatus count, fixed scope assignment, or manual override, that is a separate design argument and not silent variation inside this lane.

## Lane 278 Sibling Import Contract Support Packet

Lane 278 remains historically closed as the bounded core import mutation lane. The selected follow-on is PM Lane 412, a sibling import-contract-support packet that isolates project snapshoting, scope-pool allocation, and apparatus quote-field population from the later Lane 280 status-mutation branch.

Required additional extractors:

1. Four adjusted estimator pools into `seam.scope_labor_details`:
   - `Onsite Labor Total (adjusted)` -> `labor_category = 'Onsite Labor'`, includes `quoted_hours`
   - `Offsite Labor Total (adjusted)` -> `labor_category = 'Offsite Labor'`, includes `quoted_hours`
   - `Travel Total` -> `labor_category = 'Travel'`, `quoted_hours = null`
   - `Outside Services Total` -> `labor_category = 'Outside Services'`, `quoted_hours = null`
2. Per-apparatus `Hrs/Line` into `seam.apparatus.quoted_hours`
3. One original project contract snapshot:
   - `contract_value = SUM(four pool totals) = Total Sheet $$$ Adjusted`
   - `total_quoted_hours = SUM(apparatus.quoted_hours)`
   - `recognition_rate_per_hour = contract_value / total_quoted_hours`
   - `effective_date = import date or contract sign date if extractable`
4. Frozen per-apparatus quoted revenue:
   - `quoted_revenue = quoted_hours * recognition_rate_per_hour`

For multi-scope projects, pool totals allocate to scopes by `scope_hours / project_hours` at import time so the sum of scope-level pool rows still reconciles exactly to the project snapshot's `contract_value`.

Required import no-go checks:

1. `contract_value > 0`
2. `total_quoted_hours > 0`
3. every imported apparatus row has `quoted_hours >= 0`
4. the sum of all scope-level pool amounts equals the snapshot `contract_value`
5. the sum of all apparatus-level `quoted_revenue` values reconciles to the same snapshot `contract_value` within documented rounding tolerance

## Proposed Schema Shapes

## `seam.project_contract_snapshots`

Recommended shape:

```text
id UUID PRIMARY KEY
project_id UUID NOT NULL REFERENCES seam.projects(id)
snapshot_kind TEXT NOT NULL
contract_value NUMERIC(14,2) NOT NULL CHECK (contract_value >= 0)
total_quoted_hours NUMERIC(14,2) NOT NULL CHECK (total_quoted_hours > 0)
recognition_rate_per_hour NUMERIC(14,6) NOT NULL CHECK (recognition_rate_per_hour >= 0)
effective_date DATE NOT NULL
source_fingerprint TEXT NOT NULL
mutation_authority TEXT NOT NULL DEFAULT 'not_admitted'
revenue_recognition_authority TEXT NOT NULL DEFAULT 'not_admitted'
billing_export_authority TEXT NOT NULL DEFAULT 'not_admitted'
invoice_authority TEXT NOT NULL DEFAULT 'not_admitted'
accounting_authority TEXT NOT NULL DEFAULT 'not_admitted'
external_finance_sync_authority TEXT NOT NULL DEFAULT 'not_admitted'
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
created_by TEXT NOT NULL
audit_event_id TEXT NOT NULL
mutation_id TEXT NOT NULL
CHECK (
  ABS(recognition_rate_per_hour - (contract_value / NULLIF(total_quoted_hours, 0))) < 0.001
)
CHECK (
  snapshot_kind = 'original'
  OR snapshot_kind ~ '^change_order_[1-9][0-9]*$'
)
```

Recommended constraints and indexes:

1. unique one `original` snapshot per project
2. unique `project_id + snapshot_kind`
3. unique `mutation_id`
4. unique `audit_event_id`
5. stored `recognition_rate_per_hour` must reconcile to `contract_value / total_quoted_hours` within tolerance
6. route must set any admitted revenue-recognition authority explicitly at insert time instead of inheriting it from a claiming default
7. insert-only trigger; reject update/delete
8. RLS on; `anon` and `authenticated` revoked

## `seam.scope_labor_details`

Recommended shape:

```text
id UUID PRIMARY KEY
scope_id UUID NOT NULL REFERENCES seam.scopes(id)
contract_snapshot_id UUID NOT NULL REFERENCES seam.project_contract_snapshots(id)
labor_category seam.scope_labor_category NOT NULL
quoted_amount NUMERIC(14,2) NOT NULL CHECK (quoted_amount >= 0)
actual_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (actual_amount >= 0)
quoted_hours NUMERIC(14,2)
rate NUMERIC(14,6)
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
created_by TEXT NOT NULL
audit_event_id TEXT NOT NULL
mutation_id TEXT NOT NULL
```

Recommended enum values for `seam.scope_labor_category`:

1. `Onsite Labor`
2. `Offsite Labor`
3. `Travel`
4. `Outside Services`

Recommended checks:

1. `quoted_hours` required for `Onsite Labor` and `Offsite Labor`
2. `quoted_hours` must be null for `Travel` and `Outside Services`
3. `rate` may be null because the estimator blend is already embedded in the imported totals

## `seam.apparatus` additions

Recommended column additions:

```text
quoted_hours NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (quoted_hours >= 0)
quoted_revenue NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (quoted_revenue >= 0)
contract_snapshot_id UUID REFERENCES seam.project_contract_snapshots(id)
```

Quoted revenue is frozen when the import snapshot is created. Later change orders do not rewrite earlier apparatus rows in place; they either add new apparatus under a later snapshot or use later admitted change-order logic to point new revenue recognition to the new snapshot.

V1 rollout rule: a recognition event is allowed only when `apparatus.contract_snapshot_id` is already non-null. This lane does not assume a silent backfill for legacy apparatus rows; the later implementation packet must either backfill them explicitly or keep event creation gated until the snapshot link exists.

## `seam.apparatus_revenue_events`

Recommended shape:

```text
id UUID PRIMARY KEY
record_kind seam.apparatus_revenue_event_kind NOT NULL
apparatus_id UUID NOT NULL REFERENCES seam.apparatus(id)
scope_id UUID NOT NULL REFERENCES seam.scopes(id)
project_id UUID NOT NULL REFERENCES seam.projects(id)
contract_snapshot_id UUID NOT NULL REFERENCES seam.project_contract_snapshots(id)
recognized_amount NUMERIC(14,2) NOT NULL
recognition_percent NUMERIC(5,2) NOT NULL CHECK (recognition_percent >= 0 AND recognition_percent <= 100)
recognition_date DATE NOT NULL
reverses_event_id UUID REFERENCES seam.apparatus_revenue_events(id)
source_status_from TEXT
source_status_to TEXT
revenue_recognition_authority TEXT NOT NULL DEFAULT 'not_admitted'
billing_export_authority TEXT NOT NULL DEFAULT 'not_admitted'
invoice_authority TEXT NOT NULL DEFAULT 'not_admitted'
accounting_authority TEXT NOT NULL DEFAULT 'not_admitted'
external_finance_sync_authority TEXT NOT NULL DEFAULT 'not_admitted'
idempotency_key TEXT NOT NULL
mutation_id TEXT NOT NULL
audit_event_id TEXT NOT NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
created_by TEXT NOT NULL
```

Recommended fixed event kinds:

1. `apparatus_revenue_zero_baseline`
2. `apparatus_revenue_recognized`
3. `apparatus_revenue_reversed`

Recommended checks:

1. zero baseline requires `recognized_amount = 0`, `recognition_percent = 0`, and `reverses_event_id is null`
2. recognized events require `recognized_amount > 0`, `recognition_percent = 100.00`, and `reverses_event_id is null` for V1
3. reversed events require `recognized_amount < 0` and `reverses_event_id is not null`
4. only reversed events may carry `reverses_event_id`
5. downstream finance authority columns remain `not_admitted`

Required cross-row trigger rules:

1. `reverses_event_id` must reference an original `apparatus_revenue_recognized` row, not a zero-baseline row and not another reversal row
2. reversal `contract_snapshot_id` must equal the original event `contract_snapshot_id`
3. V1 disallows double reversal; an already-reversed recognized row may not be reversed again

Recommended indexes:

1. unique `idempotency_key`
2. unique `mutation_id`
3. unique `audit_event_id`
4. index `(apparatus_id, contract_snapshot_id, recognition_date)`
5. partial index for unreversed recognized rows
6. index on `reverses_event_id`

Recommended governance:

1. insert-only trigger; reject update/delete
2. RLS on; `anon` and `authenticated` revoked
3. same-payload replay returns `idempotent_hit`

## `seam.v_scope_financials`

Recommended derived columns:

1. `scope_id`
2. `project_id`
3. `contract_snapshot_id`
4. `total_quoted_revenue`
5. `total_recognized_revenue`
6. `revenue_recognition_percent`
7. `total_labor_cost`
8. `gross_margin`
9. `gross_margin_percent`
10. `onsite_labor_recognized_revenue`
11. `offsite_labor_recognized_revenue`
12. `travel_recognized_revenue`
13. `outside_services_recognized_revenue`

Representative view shape:

```sql
CREATE OR REPLACE VIEW seam.v_scope_financials AS
WITH scope_pool_totals AS (
  SELECT
    sld.scope_id,
    sld.contract_snapshot_id,
    SUM(sld.quoted_amount) AS total_scope_pool_amount,
    SUM(COALESCE(sld.actual_amount, 0)) AS total_labor_cost,
    SUM(CASE WHEN sld.labor_category = 'Onsite Labor' THEN sld.quoted_amount ELSE 0 END) AS onsite_pool_amount,
    SUM(CASE WHEN sld.labor_category = 'Offsite Labor' THEN sld.quoted_amount ELSE 0 END) AS offsite_pool_amount,
    SUM(CASE WHEN sld.labor_category = 'Travel' THEN sld.quoted_amount ELSE 0 END) AS travel_pool_amount,
    SUM(CASE WHEN sld.labor_category = 'Outside Services' THEN sld.quoted_amount ELSE 0 END) AS outside_services_pool_amount
  FROM seam.scope_labor_details sld
  GROUP BY sld.scope_id, sld.contract_snapshot_id
), scope_event_totals AS (
  SELECT
    are.scope_id,
    are.contract_snapshot_id,
    SUM(CASE WHEN are.record_kind = 'apparatus_revenue_zero_baseline' THEN 0 ELSE are.recognized_amount END) AS total_recognized_revenue
  FROM seam.apparatus_revenue_events are
  GROUP BY are.scope_id, are.contract_snapshot_id
), scope_quoted AS (
  SELECT
    a.scope_id,
    a.contract_snapshot_id,
    SUM(a.quoted_revenue) AS total_quoted_revenue
  FROM seam.apparatus a
  GROUP BY a.scope_id, a.contract_snapshot_id
)
SELECT
  sc.id AS scope_id,
  sc.project_id,
  pcs.id AS contract_snapshot_id,
  COALESCE(sq.total_quoted_revenue, 0) AS total_quoted_revenue,
  COALESCE(sett.total_recognized_revenue, 0) AS total_recognized_revenue,
  CASE
    WHEN COALESCE(sq.total_quoted_revenue, 0) = 0 THEN 0
    ELSE ROUND((COALESCE(sett.total_recognized_revenue, 0) / sq.total_quoted_revenue) * 100, 2)
  END AS revenue_recognition_percent,
  COALESCE(spt.total_labor_cost, 0) AS total_labor_cost,
  COALESCE(sett.total_recognized_revenue, 0) - COALESCE(spt.total_labor_cost, 0) AS gross_margin,
  CASE
    WHEN COALESCE(sett.total_recognized_revenue, 0) = 0 THEN 0
    ELSE ROUND(((COALESCE(sett.total_recognized_revenue, 0) - COALESCE(spt.total_labor_cost, 0)) / sett.total_recognized_revenue) * 100, 2)
  END AS gross_margin_percent,
  COALESCE(sett.total_recognized_revenue, 0) * (COALESCE(spt.onsite_pool_amount, 0) / NULLIF(spt.total_scope_pool_amount, 0)) AS onsite_labor_recognized_revenue,
  COALESCE(sett.total_recognized_revenue, 0) * (COALESCE(spt.offsite_pool_amount, 0) / NULLIF(spt.total_scope_pool_amount, 0)) AS offsite_labor_recognized_revenue,
  COALESCE(sett.total_recognized_revenue, 0) * (COALESCE(spt.travel_pool_amount, 0) / NULLIF(spt.total_scope_pool_amount, 0)) AS travel_recognized_revenue,
  COALESCE(sett.total_recognized_revenue, 0) * (COALESCE(spt.outside_services_pool_amount, 0) / NULLIF(spt.total_scope_pool_amount, 0)) AS outside_services_recognized_revenue
FROM seam.scopes sc
JOIN seam.project_contract_snapshots pcs ON pcs.project_id = sc.project_id
LEFT JOIN scope_pool_totals spt ON spt.scope_id = sc.id AND spt.contract_snapshot_id = pcs.id
LEFT JOIN scope_event_totals sett ON sett.scope_id = sc.id AND sett.contract_snapshot_id = pcs.id
LEFT JOIN scope_quoted sq ON sq.scope_id = sc.id AND sq.contract_snapshot_id = pcs.id;
```

`total_labor_cost` remains `0` until later actuals/cost lanes populate `actual_amount`; that is acceptable because this lane is only defining the view contract, not claiming live cost-side completeness.

Critical normalization rule: pool-recognized revenue must be normalized inside the scope, not against the full project contract value. Using the project-level denominator would underreport multi-scope pool recognition by the scope-share factor and would remain invisible on single-scope fixtures such as Miner Temp Power.

Implementation requirements for this view:

1. include an explicit multi-scope fixture proving the 60 percent / 40 percent split case so the current single-scope Miner data cannot mask the bug,
2. treat null pool-recognition columns from `NULLIF(spt.total_scope_pool_amount, 0)` as defensive failure, not as silently valid business data,
3. have the consuming UI show `Cost data pending` or suppress gross-margin display until actuals lanes begin populating `actual_amount`, so a mathematically correct but operationally misleading 100 percent margin is not shown as if costs were complete.

## Lane 280 Apparatus Status Mutation Extension Contract

Trigger event:

1. PM-only disposition of apparatus status to `Complete`
2. same transaction updates apparatus status and inserts one recognition event
3. V1 recognition percent fixed to `100.00`

Recommended payload additions to the Lane 280 apparatus status mutation route:

```json
{
  "project_id": "pm-import-project-miner-temp-power",
  "apparatus_id": "<apparatus-id>",
  "target_status": "Complete",
  "contract_snapshot_id": "<original-snapshot-id>",
  "recognition_percent": 100.0,
  "recognition_date": "YYYY-MM-DD",
  "expected_quoted_revenue": 1234.56,
  "expected_current_status": "Ready",
  "mutation_id": "mut-<stable-id>",
  "audit_event_id": "audit-<stable-id>"
}
```

Precondition gates:

1. actor must satisfy PM-only authority
2. apparatus must belong to an admitted imported project and valid scope
3. apparatus must have frozen `quoted_hours`, `quoted_revenue`, and `contract_snapshot_id`
4. referenced snapshot must belong to the same project
5. `recognition_percent = 100.00` for V1
6. no unreversed recognized event may already exist for the same apparatus and snapshot unless the payload is an exact idempotent replay
7. downstream finance authorities remain `not_admitted`

Recommended idempotency derivation:

```text
sha256(
  "apparatus_revenue_recognized|" + project_id + "|" + apparatus_id + "|" +
  target_status + "|" + contract_snapshot_id + "|" +
  expected_quoted_revenue + "|" + recognition_percent + "|" + recognition_date
)
```

Recommended readback contract in the mutation response:

```json
{
  "status": "accepted_or_idempotent_hit",
  "event_id": "<revenue-event-id>",
  "apparatus_id": "<apparatus-id>",
  "target_status": "Complete",
  "contract_snapshot_id": "<snapshot-id>",
  "recognized_amount": 1234.56,
  "recognition_percent": 100.0,
  "recognition_date": "YYYY-MM-DD",
  "current_net_recognized_amount_for_apparatus": 1234.56,
  "unreversed_recognition_event_count": 1,
  "billing_export_authority": "not_admitted",
  "invoice_authority": "not_admitted",
  "accounting_authority": "not_admitted",
  "external_finance_sync_authority": "not_admitted"
}
```

## Reversal Pattern And Netting Examples

Corrections remain insert-only.

Recommended reversal shape:

1. insert a new `apparatus_revenue_reversed` row
2. set `recognized_amount` to the negative of the original recognized row
3. set `reverses_event_id` to the original event
4. copy the original event `contract_snapshot_id`; reversal rows may not cross snapshots
5. leave the original row untouched

Netting query example per apparatus:

```sql
SELECT
  apparatus_id,
  SUM(CASE WHEN record_kind = 'apparatus_revenue_zero_baseline' THEN 0 ELSE recognized_amount END) AS net_recognized_amount
FROM seam.apparatus_revenue_events
GROUP BY apparatus_id;
```

Netting query example per scope and snapshot:

```sql
SELECT
  scope_id,
  contract_snapshot_id,
  SUM(CASE WHEN record_kind = 'apparatus_revenue_zero_baseline' THEN 0 ELSE recognized_amount END) AS net_recognized_amount
FROM seam.apparatus_revenue_events
GROUP BY scope_id, contract_snapshot_id;
```

## Zero-Output Baseline Migration Pattern

The later admitted implementation should seed one zero-output row per apparatus and snapshot before any recognition event exists.

Recommended baseline row shape:

1. `record_kind = 'apparatus_revenue_zero_baseline'`
2. `recognized_amount = 0`
3. `recognition_percent = 0`
4. `recognition_date = effective_date or baseline migration date`
5. one baseline row per `(apparatus_id, contract_snapshot_id)`

Purpose:

1. preserve an explicit insert-only audit baseline matching PM Lanes 281 through 284
2. make readback truthfully distinguish `no recognition yet` from `storage gap`
3. keep later recognition and reversal events append-only

## Boundaries This Lane Does Not Admit

1. no live revenue events written
2. no schema migration applied
3. no `public.*` schema writes
4. no billing, invoice, payroll, accounting, customer billing delivery, or external finance sync
5. no source workbook writeback or macros
6. no change-order admission or execution
7. no autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 411 files.
3. Selected outcome is present.
4. Lane 352 return-label classification is explicit.
5. Multi-scope pool-recognition denominator is scope-level, not project-level.
6. Snapshot-kind design correction is explicit.
7. Stored snapshot-rate consistency check is explicit.
8. Authority defaults are `not_admitted` and explicit route-set authority is required.
9. PM Lane 412 sibling import-contract-support packet is explicit.
10. Lane 280 status-mutation extension contract is explicit.
11. Reversal, zero-baseline, and same-snapshot reversal rules are explicit.
12. Multi-scope implementation fixture requirement is explicit.
13. `git diff --check` passes.
14. Staged diff includes only Lane 411 scoped docs, packet, handoff, closeout, and PM status surface.

## Next Truth

The next truthful move is not live revenue recognition.

The next truthful move is a separate later admission packet against this design if PM wants schema creation, import-contract implementation, apparatus-status mutation extension, baseline seeding, or live apparatus revenue recognition writes.