# Ops Chip 4 — Progress Billing (design spec)

> **Lane SSoT:** `reference/ops/00-MASTER-INDEX.md` (§5 revenue/progress-billing model; D-OPS-3).
> **Builds on:** Chip 1 (`001` identity), Chip 2 (`002` quote model), the person anchor (`004`),
> and **Chip 3 (`005` recognition ledger)** — this migration FKs into `ops.revenue_recognition_event`.
> **Migration:** `006_progress_billing.sql` (+ `_down` + `test_006_progress_billing.py`).
> **Dev only.** TDD on throwaway `ops_test`; gated apply to `ops_dev`. Nothing applied to prod.
> **Status:** design — approved direction (operator audit, 2026-06-21); awaiting spec sign-off.

---

## 1. Goal

Record what RESA accounting has **invoiced** against recognized work, and track **billable hours**,
without becoming the system of record for accounting. The platform's value is the **reconciliation
view** — recognized-to-date vs invoiced-to-date vs still-unbilled, plus retainage held — kept
**isolated from RESA's AR/GL**. Chip 4 does **not** generate the customer invoice or post to a ledger;
it records the fact that an invoice was raised and which recognized apparatus it covered.

## 2. Where it sits — the two-stage money pipeline

Chip 3 *earns* revenue (recognition); Chip 4 records the *invoicing* of it. The two are deliberately
decoupled: recognition fires continuously as apparatus complete; billing is periodic (a pay-app cadence).

```
RECOGNIZED  (Chip 3 — immutable, append-only events)        per apparatus, signed
        │     recognized +X   /   reversal −X
        ▼
UNBILLED    = the precise two-branch set in §5            → ops.v_unbilled_recognition (the backlog)
        │
        │   record_billing_application(project, actor, period_through,
        │       invoice_ref?, exclude[], retainage…)        sweeps unbilled ≤ period_through − excludes
        ▼
BILLING APPLICATION  (header + one line per swept event)   draft → issued → voided
        │   gross Σamount · billable hours Σhours · retainage_withheld · net_invoiced
        │   void_billing_application(…)  → releases its lines back to UNBILLED
        ▼
RECONCILIATION   recognized-to-date vs billed-to-date vs unbilled vs retainage-held
                                                          → ops.v_project_billing (isolated from RESA)
```

## 3. Laws honored

- **Law 3 — recognition firewall (extended).** Recognized $ live ONLY in the Chip 3 event ledger.
  Chip 4 **references** recognition events (FK + snapshot copies on its lines); it **never mutates**
  them. There is no `billed` column on the event — the membership line *is* the billed marker.
- **Isolation from RESA accounting.** The platform records `external_invoice_ref` (the RESA invoice #)
  and tracks hours/amounts; it never drives AR/GL. No payment receipt / cash-application in this chip.
- **Law 1 / lifecycle.** Billing never relaxes the Chip-3 reverse-first guards on apparatus/scope/project.
  A reversal of already-billed work flows through as an automatic next-application credit (§5, §8).

## 4. Operator decisions (ratified 2026-06-21, incl. the design audit)

| ID | Decision | Resolution |
|---|---|---|
| **B-1** | Billing model | **Per-project retainage rate.** Platform tracks billable hours + records invoicing; isolated from RESA accounting. |
| **B-2** | Line selection | **Auto-sweep all unbilled recognized up to `period_through`, minus an `exclude[]` apparatus list.** Held apparatus ride a later application. |
| **B-3** | Lifecycle / corrections | **Atomic record + void-to-correct.** Issued applications are immutable; correct by voiding (releases its lines) + re-recording. |
| **B-4** | Draft status | **`external_invoice_ref` is required for `issued`.** To prepare before the RESA invoice exists, a `draft` is allowed (no ref, holds its lines); promoted by `issue_billing_application`. |
| **B-5** | Retainage release | **Explicit only, capped by held-to-date, no auto-release.** Withholding applies to **positive gross only**. |
| **B-6** | Credits non-excludable | **Reversal credits for already-billed work always sweep.** `exclude[]` suppresses positive recognized work only. |
| **B-7** | Reversal-of-billed | **Automatic next-application credit** (§5 credit branch). |

### Audit findings folded in (operator, 2026-06-21)
- **HIGH-1** — `unbilled` is the precise two-branch set (§5), not "events with no active line."
- **HIGH-2** — reversal lines derive **signed hours from the original** event (`−orig.quoted_hours`); reversal events carry NULL `quoted_hours`.
- **HIGH-3** — the sweep is bounded by `recognized_at::date <= period_through`; issued `period_through` is non-decreasing.
- **MED-1** — credits are non-excludable (B-6).
- **MED-2** — void integrity via triggers (immutability + a deferred header↔line consistency constraint); `application_no` burned forever.
- **MED-3** — retainage withheld on positive gross only; release explicit + capped.

## 5. The unbilled set — `ops.v_unbilled_recognition`

The definition that carries the design. **active line** ≡ a `billing_application_line` with
`is_voided = false` whose application `status <> 'voided'` (i.e. a line on a `draft` or `issued`
application — drafts reserve their events).

```
positive branch :  recognized event e
                   WHERE e.event_type = 'recognized'
                     AND NOT EXISTS (reversal r : r.reverses_event_id = e.id)   -- not reversed
                     AND NOT EXISTS (active line on e.id)                        -- not already billed
                   line amount  = e.recognized_amount      (> 0)
                   line hours   = e.quoted_hours           (> 0)

credit branch   :  reversal event e
                   WHERE e.event_type = 'reversal'
                     AND EXISTS     (active line on e.reverses_event_id)         -- original IS billed
                     AND NOT EXISTS (active line on e.id)                        -- this credit not billed
                   line amount  = e.recognized_amount      (< 0)
                   line hours   = −(original recognized event).quoted_hours      (< 0)   -- HIGH-2
```

**Why two branches (HIGH-1):** a recognition reversed *before it was ever billed* must never reach a
bill — its `+X` is excluded (reversed) and its `−X` is excluded (original not billed), so the never-billed
pair silently nets out. A reversal of *already-billed* work *must* surface as a credit — its `−X` is the
credit branch. Verified correct across reverse-then-void and void-then-reverse orderings (a void frees
the original's line ⇒ both events drop out, because the void already credited the customer).

The view exposes: `event_id, event_type, apparatus_id, scope_id, project_id, amount, billable_hours,
recognized_at`. The `record` function applies the `period_through` and `exclude[]` filters on top of it.

## 6. Data model

### 6a. `ops.projects.retainage_pct` (additive column)
```sql
alter table ops.projects
  add column retainage_pct numeric not null default 0
    check (retainage_pct >= 0 and retainage_pct < 1);
comment on column ops.projects.retainage_pct is
  'Per-project expected retainage withholding rate (Chip 4). Snapshotted onto each billing application; 0 = simple invoice.';
```

### 6b. status enum
```sql
create type ops.billing_application_status as enum ('draft','issued','voided');
```

### 6c. `ops.billing_application` (the header — a record of an invoicing event)
```sql
create table ops.billing_application (
  id                      uuid primary key default gen_random_uuid(),
  project_id              uuid not null references ops.projects(id),
  application_no          int,                       -- assigned at ISSUE; null while draft; burned forever once assigned
  status                  ops.billing_application_status not null default 'draft',
  period_through          date not null,             -- the "as of" cutoff; sweep takes recognized_at::date <= this
  external_invoice_ref    text,                      -- the RESA accounting invoice #; required when issued
  billable_hours          numeric not null,          -- Σ line.billable_hours (signed)
  gross_amount            numeric not null,          -- Σ line.amount (signed; may be < 0 = pure credit application)
  positive_gross          numeric not null,          -- Σ line.amount where amount > 0 (retainage basis)
  retainage_pct           numeric not null,          -- snapshot of projects.retainage_pct at record time
  retainage_withheld      numeric not null default 0,
  retainage_released      numeric not null default 0,
  net_invoiced            numeric not null,          -- gross_amount − retainage_withheld + retainage_released
  previous_gross_to_date  numeric not null default 0,-- Σ gross of prior ISSUED apps (snapshot at issue)
  total_gross_to_date     numeric not null,          -- previous_gross_to_date + gross_amount (snapshot)
  actor_person_id         uuid not null references ops.persons(person_id),
  recorded_at             timestamptz not null default now(),
  issued_at               timestamptz,
  voided_at               timestamptz,
  voided_by               uuid references ops.persons(person_id),
  void_reason             text,
  created_at              timestamptz not null default now(),

  constraint uq_billapp_project_no unique (project_id, application_no),     -- NULLs distinct ⇒ many drafts ok
  constraint ck_billapp_issued_ref check (
    status <> 'issued' or (external_invoice_ref is not null and btrim(external_invoice_ref) <> '')),
  constraint ck_billapp_numbered_iff_not_draft check (
    (status = 'draft') = (application_no is null)),
  constraint ck_billapp_issued_at check (
    status = 'draft' or issued_at is not null),
  constraint ck_billapp_void_shape check (
    status <> 'voided'
    or (voided_at is not null and voided_by is not null
        and void_reason is not null and btrim(void_reason) <> '')),
  constraint ck_billapp_retainage_nonneg check (retainage_withheld >= 0 and retainage_released >= 0),
  constraint ck_billapp_withheld_cap   check (retainage_withheld <= positive_gross),
  constraint ck_billapp_net   check (net_invoiced = gross_amount - retainage_withheld + retainage_released),
  constraint ck_billapp_total check (total_gross_to_date = previous_gross_to_date + gross_amount)
);
```
*Note:* `retainage_released <= retainage_held_to_date(project)` is a **cross-row** cap → enforced in the
`record`/`issue` functions and the insert-integrity trigger, not as a column CHECK.

### 6d. `ops.billing_application_line` (the membership / "invoiced" marker)
```sql
create table ops.billing_application_line (
  id                   uuid primary key default gen_random_uuid(),
  application_id       uuid not null references ops.billing_application(id) on delete cascade,  -- cascade serves draft-discard only
  recognition_event_id uuid not null references ops.revenue_recognition_event(id),
  event_type           ops.recognition_event_type not null,   -- mirror of the event (recognized | reversal)
  apparatus_id         uuid not null references ops.apparatus(id),
  scope_id             uuid not null references ops.scopes(id),
  project_id           uuid not null references ops.projects(id),
  amount               numeric not null,            -- snapshot of event.recognized_amount (signed)
  billable_hours       numeric not null,            -- recognized:+quoted_hours | reversal:−orig.quoted_hours
  is_voided            boolean not null default false,
  created_at           timestamptz not null default now()
);
create unique index uq_billline_active_event
  on ops.billing_application_line (recognition_event_id) where is_voided = false;   -- one ACTIVE line per event
create index ix_billline_app       on ops.billing_application_line(application_id);
create index ix_billline_apparatus on ops.billing_application_line(apparatus_id);
create index ix_billline_scope     on ops.billing_application_line(scope_id);
```
`uq_billline_active_event` is the **no-double-bill** invariant — an event can be on at most one active
application — enforced structurally (defense-in-depth atop the function's project lock; the Chip 3
audit lesson: the invariant must hold against direct inserts, not only inside the function). The
`on delete cascade` exists solely so `discard_draft_billing_application` can remove a *draft* and its
lines; issued/voided headers and their lines are DELETE-blocked by trigger (§8).

## 7. Functions (the gated entry points)

All run under `select … from ops.projects where id = p_project_id for update` (or the application row +
its project) so concurrent records/issues/voids serialize — same pattern as Chip 3's `for update of a2`.

### 7a. `record_billing_application`
```
record_billing_application(
  p_project_id          uuid,
  p_actor_person_id     uuid,
  p_period_through      date,
  p_external_invoice_ref text   default null,   -- non-blank ⇒ issue immediately; null ⇒ draft
  p_exclude_apparatus   uuid[]  default '{}',   -- holds positive recognized work back; credits ignore it
  p_retainage_withheld  numeric default null,   -- override; default round(positive_gross * pct, 2)
  p_retainage_released  numeric default 0
) returns uuid
```
1. Lock + load project; reject if not found, `not is_active`, or `status = 'Cancelled'`.
2. **Monotonic period (HIGH-3):** reject if any *issued* application for the project has
   `period_through > p_period_through`.
3. Build the swept set from §5, filtered by `recognized_at::date <= p_period_through`, with
   `p_exclude_apparatus` removing **positive** events only (credits always included — B-6).
4. `gross = Σ amount`; `positive_gross = Σ amount where amount > 0`; `billable_hours = Σ hours`.
5. If the swept set is empty **and** `p_retainage_released = 0` → raise `nothing to bill`.
   (A pure retainage-release record is the one allowed empty-sweep case — B-5.)
6. `retainage_pct = project.retainage_pct`;
   `withheld = coalesce(p_retainage_withheld, round(positive_gross * retainage_pct, 2))`;
   validate `0 <= withheld <= positive_gross`.
7. `held_to_date = Σ retainage_withheld − Σ retainage_released over issued apps`;
   validate `0 <= p_retainage_released <= held_to_date`.
8. `net = gross − withheld + p_retainage_released`.
9. If issuing: `previous_gross_to_date = coalesce(Σ gross over issued apps, 0)`,
   `application_no = coalesce(max(application_no), 0) + 1`, `issued_at = now()`, `status = 'issued'`.
   Else (draft): `previous_gross_to_date = 0`, `application_no = null`, `status = 'draft'`
   (running totals are recomputed at issue).
10. `total_gross_to_date = previous_gross_to_date + gross`.
11. Insert header; insert one line per swept event (`event_type/amount/billable_hours/apparatus_id/
    scope_id/project_id`, `is_voided = false`). Return the header id.

### 7b. `issue_billing_application(p_application_id, p_actor_person_id, p_external_invoice_ref)`
Promotes a `draft → issued`. Locks the application + its project; rejects if `status <> 'draft'`;
requires non-blank ref; **re-checks** the monotonic-period rule and that each line's event still has no
*other* active line (its own draft lines are expected); recomputes `previous_/total_gross_to_date` at
issue time; assigns `application_no = max+1`, sets `issued_at = now()`, `external_invoice_ref`, `status='issued'`.

### 7c. `discard_draft_billing_application(p_application_id, p_actor_person_id)`
Removes a *draft* (pre-financial): rejects if `status <> 'draft'`; deletes the header (lines cascade),
freeing their events back to unbilled. No `application_no` is consumed.

### 7d. `void_billing_application(p_application_id, p_actor_person_id, p_reason)`
Corrects an *issued* application: requires non-blank reason; locks app + project; rejects if
`status <> 'issued'`; sets `status='voided'`, `voided_at/by`, `void_reason`, and flips every line
`is_voided = true` (releasing its events back to unbilled). `application_no` stays burned.

## 8. Integrity & triggers (Chip-3-consistent — triggers, not grants)

On `ops_dev`/`ops_test` the app connects as a superuser (BYPASSRLS), so REVOKE/function-only grants
would not bind it — Chip 3 used triggers for the same reason. Chip 4 follows suit.

1. **Header immutability** (`before update or delete on ops.billing_application`):
   - DELETE blocked when `old.status in ('issued','voided')` (drafts are deletable → discard path).
   - UPDATE permitted only for the legal transitions `draft→issued` and `issued→voided`; any other
     status change, or mutation of a non-draft row's financial columns, raises.
2. **Line immutability** (`before update or delete on ops.billing_application_line`):
   - DELETE blocked when the parent application `status in ('issued','voided')`.
   - UPDATE permitted only for `is_voided false→true`; all other column drift raises.
3. **Line insert-integrity** (`before insert on ops.billing_application_line`) — direct inserts cannot
   bypass invariants (Chip 3 lesson): the event exists; `event_type`, `apparatus_id`, `scope_id`,
   `project_id`, and `amount` match the referenced event; `billable_hours` equals the §5 rule
   (recognized `= e.quoted_hours`; reversal `= −orig.quoted_hours`); `project_id` equals the
   application's project. (No-double-bill is held by `uq_billline_active_event`.)
4. **Void consistency** — a deferred constraint trigger (`after insert or update [or delete]`,
   `deferrable initially deferred`) on both tables asserts, at COMMIT, for each touched application:
   a `voided` header has **zero** `is_voided=false` lines, and a `draft|issued` header has **zero**
   `is_voided=true` lines. This catches one-sided direct manipulation (void a line without its header,
   or a header without its lines — MED-2) regardless of statement order; the `void` function flips both
   in one transaction → consistent at commit.

## 9. Views

- **`ops.v_unbilled_recognition`** — §5 (the backlog feeding the sweep + a "ready to bill" surface).
- **`ops.v_billing_application_sov`** — per `(application_id, scope_id)`: `apparatus_count`,
  `billable_hours`, `amount` over the application's **non-voided** lines = the schedule-of-values
  (G703-style) continuation. The header table itself is the G702-style summary.
- **`ops.v_project_billing`** — per project reconciliation, all isolated from RESA:
  `contract_value` (`projects.contract_value`), `recognized_to_date` (Chip 3 net), `billed_gross_to_date`
  (Σ gross over issued apps), `retainage_held_to_date` (Σ withheld − Σ released over issued),
  `net_invoiced_to_date` (Σ net over issued), `unbilled_recognized` (Σ amount from
  `v_unbilled_recognition`), `draft_count`/`issued_count`.

## 10. Reversibility

`006_progress_billing_down.sql` — idempotent `drop … if exists` in reverse-dependency order: the 4 views,
the triggers + their functions, the 4 PL/pgSQL functions, the two tables, the status enum, and
`alter table ops.projects drop column if exists retainage_pct`. It leaves Chips 1/2/3 intact (drops only
Chip-4 objects; never the `ops` schema). Validation gate = up → down → up clean.

## 11. Testing (TDD on `ops_test`)

`test_006_progress_billing.py` chains `001 → 002 → 004 → 005 → 006` then down-nukes; per-test rollback
fixture; `Decimal` assertions. Coverage (≈ 30 cases):

- **Schema/guards:** retainage_pct CHECK bounds; header CHECKs (issued-needs-ref, numbered-iff-not-draft,
  void-shape, withheld≤positive_gross, net + total arithmetic); `uq_billline_active_event` blocks a second
  active line for one event; header/line DELETE + illegal-UPDATE blocked; deferred void-consistency fires
  on one-sided manipulation.
- **record (happy path):** single-apparatus issue; multi-apparatus sweep; hours + gross + positive_gross
  + net correct; `application_no` sequential; draft when no ref / issued when ref.
- **period (HIGH-3):** an event with `recognized_at > period_through` is excluded; monotonic-period rejection.
- **excludes (B-6):** excluded positive apparatus held back; a credit for an excluded apparatus still sweeps.
- **unbilled set (HIGH-1):** never-billed-then-reversed pair never bills; billed-then-reversed surfaces a
  credit on the next application; reverse-then-void and void-then-reverse leave nothing billable.
- **reversal hours (HIGH-2):** a credit line's `billable_hours = −orig.quoted_hours`.
- **retainage (MED-3/B-5):** withheld = round(positive_gross·pct); a pure-credit application withholds 0;
  release capped by held-to-date (over-release rejected); pure retainage-release record (empty sweep, released>0).
- **lifecycle:** draft → issue → void; discard a draft frees its events; void releases lines → events return
  to `v_unbilled_recognition`; `application_no` stays burned after void.
- **reconciliation:** `v_project_billing` and `v_billing_application_sov` totals tie out across a multi-app,
  multi-scope project (the Project Miner shape).

## 12. Out of scope (deferred)

- Customer-invoice / pay-app document **generation**, AR/GL posting, cash-receipt application (RESA accounting).
- **Automatic** retainage release at completion (release stays explicit — B-5).
- Override-with-reason exclusion of credits (credits are non-excludable in the MVP — B-6).
- The `/pm-review` app-bridge that surfaces `record/void` + the views through the control-plane API
  (a later bounded packet, like the Chip 3 bridge).
- Convergence of `ops.*` billing onto the deployed `seam.*` surfaces (Chip N).

## 13. Provenance

- Lane SSoT `reference/ops/00-MASTER-INDEX.md` §5 / §5a (hours-based binary-completion model) + D-OPS-3.
- Chip 3 ledger `005_recognition_ledger.sql` (the immutable event substrate this chip reads).
- Operator design ratification + adversarial audit, 2026-06-21 (B-1…B-7 + HIGH-1/2/3, MED-1/2/3).
