# Ops Chip 4 — Progress Billing (design spec, v5)

> **Lane SSoT:** `reference/ops/00-MASTER-INDEX.md` (§5 revenue/progress-billing model; D-OPS-3).
> **Builds on:** Chip 1 (`001` identity), Chip 2 (`002` quote model), the person anchor (`004`),
> and **Chip 3 (`005` recognition ledger)** — FKs into `ops.revenue_recognition_event`.
> **Migration:** `006_progress_billing.sql` (+ `_down` + `test_006_progress_billing.py`).
> **Dev only.** TDD on throwaway `ops_test`; gated apply to `ops_dev`. Nothing applied to prod.
> **Status:** design v5 — hardened across five adversarial passes (four operator audits + three review
> workflows, 2026-06-21); posture ratified (Option 1: function-owned write API + trigger backstop).
> Awaiting operator sign-off.

---

## 1. Goal

Record what RESA accounting has **invoiced** against recognized work, and track **billable hours**,
without becoming the system of record for accounting. The platform's value is the **reconciliation
view** — recognized-to-date vs invoiced-to-date vs still-unbilled, plus retainage held — kept
**isolated from RESA's AR/GL**. Chip 4 does **not** generate the customer invoice or post to a ledger;
it records that an invoice was raised, which recognized apparatus it covered, and the retainage on it.

## 2. The two-stage money pipeline

Chip 3 *earns* revenue (recognition); Chip 4 records the *invoicing* of it. They are decoupled —
recognition fires continuously as apparatus complete; billing is periodic.

```
RECOGNIZED  (Chip 3 — immutable, append-only events)        per apparatus, signed
        │     recognized +X   /   reversal −X
        ▼
UNBILLED    = the two-branch set in §5 (active line ≡ an ISSUED line)   → ops.v_unbilled_recognition
        │
        │   record_billing_application(project, actor, period_through, invoice_ref?, exclude[], draw?)
        │      • invoice_ref given  → ISSUE now (sweep → header + lines + number)
        │      • invoice_ref null   → save a DRAFT (intent only — no lines, no number, no totals)
        ▼
BILLING APPLICATION  (ops.billing_application — only ever issued | voided; always lines + aggregates)
        │   header aggregates = Σ lines · retainage at LINE grain · cumulative to-date DERIVED in views
        │   void_billing_application(…)  → flips lines, releases events  (blocked if a later app depends on it)
        ▼
RECONCILIATION   recognized-to-date vs billed-to-date vs unbilled vs retainage-held
                                                          → ops.v_project_billing (isolated from RESA)
```

## 3. Laws honored

- **Law 3 — recognition firewall (extended).** Recognized $ live ONLY in the Chip 3 event ledger.
  Chip 4 **references** events (FK + signed snapshot copies on its lines); it **never mutates** them.
  The membership line *is* the billed marker — no `billed` column on the event.
- **Isolation from RESA accounting.** Records `external_invoice_ref` + hours/amounts/retainage; never
  drives AR/GL. No payment receipt / cash application in this chip.
- **Header is a pure rollup of its lines.** Every financial aggregate on `billing_application` equals
  the sum over its active lines (deferred constraint, §8.5). Retainage is allocated at **line grain**.
- **Retainage conservation.** `held_to_date = Σwithheld − Σreleased − Σdrawn ≥ 0` always (over
  **issued** apps). A credit returns the retainage **still held** for the reversed apparatus (capped at
  the project's remaining held); retainage already **drawn** (billed) to the customer is not returned
  again — the customer already paid it, so the credit returns full gross instead. A **draw is
  project-grain** (not apparatus-attributed): a bill may be voided while a prior draw stands, as long as
  `held ≥ 0` holds; the residual draw remains valid project retainage already paid (B-5).
- **The four functions are the supported write API; triggers are the invariant backstop.** The billing
  tables are mutated **only** inside the functions (a txn-local context flag the functions set/reset; the
  mutation triggers reject changes made outside that context — §8.0). This gate is a **misuse/invariant
  guard, not a security boundary** — the app role is superuser/BYPASSRLS and the GUC is spoofable, so a
  *determined* operator can still bypass it; the gate's job is to stop *accidental/buggy* direct DML (an
  ORM, a migration, a careless `UPDATE`). On top of it the triggers/constraints assert the **structural
  invariants** on committed state (header=Σlines, held≥0, lineage, branch eligibility, void-cascade), which
  catch structural drift from a function bug. The **canonical credit-release allocation itself is
  function-owned and pinned by tests (§11)** — it is deliberately *not* re-derived in a constraint trigger
  (that would reimplement the billing engine in triggers). This is the chosen posture: a stateful multi-line
  allocation belongs in one code path, not in per-row validation.
- **Reverse-first lifecycle.** An application cannot be voided while a later issued application depends
  on it (a standing credit of its events, or a draw against the **project held pool** the voided app
  contributed to).

## 4. Operator decisions (ratified 2026-06-21, incl. all three adversarial passes)

| ID | Decision | Resolution |
|---|---|---|
| **B-1** | Billing model | **Per-project retainage rate.** Track billable hours + record invoicing; isolated from RESA. |
| **B-2** | Line selection | **Auto-sweep unbilled recognized ≤ `period_through`, minus an `exclude[]` apparatus list.** |
| **B-3** | Lifecycle / corrections | **Atomic record + void-to-correct.** Issued applications immutable; correct by void + re-record. |
| **B-4 (v2)** | Draft model | **Draft = saved intent, materialized at issue.** Separate `billing_application_draft`; persists no lines, reserves no events, no number, no totals; `issue` runs a fresh sweep. |
| **B-5** | Retainage draw | **Explicit + capped by held-to-date; no auto end-of-job draw.** Withholding on **positive gross only**. |
| **B-6** | Credits non-excludable | Reversal credits always sweep; `exclude[]` suppresses positive work only. |
| **B-7** | Reversal-of-billed | **Automatic next-application credit** (§5 credit branch). |
| **B-8 (v3)** | Retainage grain + credit | **Line-grain retainage (per-line rounding is authoritative).** A credit auto-returns `LEAST(the reversed apparatus's original-line withheld, the project's remaining held)` — never returns retainage already drawn. Customer net-credited = net the customer actually paid for that work. |

### Adversarial findings folded in (four operator audits + three review workflows)

**Operator audit #1** (design): the original 6 findings + B-rulings (gated approval, clearances, line-grain
intent). **Workflow #1** (v1, *block*): C-1 void→negative-held, C-2 void→double-credit, C-3 draft-tamper,
H-1…H-3, M-1…M-5. **Operator audit #2** (v1): stale-draft-after-reversal, direct-line-writes,
header-direct-insert, draft-value-vanishes, timezone. **Workflow #2** (v2, *block*): `LEAST(.,gross)` cap
rejected all credit apps; bill→draw→reverse wedge; void-guard/lock only in functions; rounding.
**Workflow #3** (v3, *revise*): header-only void strands an event; §8.5 issued-only filter;
recognized_to_date formula; credit-walk order; sub-cent line. **Operator audit #3** (v3): Chip-3 reversal
race (sweep→insert TOCTOU); direct-DML under-release; draw-cap; header DELETE arm; duplicate invoice ref.
**Operator audit #4** (v4): the gate is a misuse-guard not a security boundary (contain the txn-local flag;
deferred assertions flag-independent); soften "catches every function bug" → structural drift + test-pinned
allocation; gate the draft table explicitly; draw = project-grain wording. **Every finding is resolved**
(v5 = audit-#4 honesty/containment hardening atop the v4 enforcement layer).

## 5. The unbilled set — `ops.v_unbilled_recognition`

**active line ≡ a `billing_application_line` with `is_voided = false` whose application `status='issued'`.**
(Drafts hold no lines, so "active" is simply *issued*.)

```
positive branch :  recognized event e
                   WHERE e.event_type = 'recognized'
                     AND NOT EXISTS (reversal r : r.reverses_event_id = e.id)   -- not reversed
                     AND NOT EXISTS (active line on e.id)                        -- not already billed
                   line amount = round(e.recognized_amount, 2)   (> 0)
                   line hours  = round(e.quoted_hours, 2)        (> 0)

credit branch   :  reversal event e
                   WHERE e.event_type = 'reversal'
                     AND EXISTS     (active line on e.reverses_event_id)         -- original IS issued-billed
                     AND NOT EXISTS (active line on e.id)                        -- this credit not billed
                   line amount = round(e.recognized_amount, 2)   (< 0)
                   line hours  = −round((original recognized event).quoted_hours, 2)   (< 0)
```

**All money/hours are rounded to 2dp at the line, then summed** (line-grain rounding is authoritative,
B-8 / M-1). `recognized_amount` and `quoted_hours` are unscaled `numeric` in Chip 3, so the rounding
point is fixed here and every view consumes the per-event rounded value (M-2).

**Why two branches:** a recognition reversed before it was ever billed never reaches a bill. A reversal
of already-billed work surfaces as the credit branch (B-7), returning gross + its line-grain retainage (B-8).

**Period bounds (timezone-explicit):** the sweep filters the **positive** branch by
`e.recognized_at < (p_period_through + 1)::timestamp AT TIME ZONE 'America/Phoenix'` (Project Miner is PHX,
no DST). **Credit-branch lines are exempt from the upper bound** (a credit must always sweep onto the next
application regardless of the reversal's wall-clock time — mirrors B-6). `exclude[]` suppresses positive
apparatus only.

## 6. Data model

### 6a. `ops.projects.retainage_pct` (additive column)
```sql
alter table ops.projects
  add column retainage_pct numeric(6,5) not null default 0
    check (retainage_pct >= 0 and retainage_pct < 1);
```

### 6b. status enum (no draft — drafts are a separate table)
```sql
create type ops.billing_application_status as enum ('issued','voided');
```

### 6c. `ops.billing_application` (the financial record — always issued | voided)
```sql
create table ops.billing_application (
  id                    uuid primary key default gen_random_uuid(),
  project_id            uuid not null references ops.projects(id),
  application_no        int  not null,                 -- assigned at creation; unique per project; burned forever
  status                ops.billing_application_status not null default 'issued',
  period_through        date not null,
  external_invoice_ref  text not null,                 -- the RESA invoice #; required (no issued app without it)
  billable_hours        numeric(14,2) not null,        -- Σ line.billable_hours (signed)
  gross_amount          numeric(14,2) not null,        -- Σ line.amount (signed; < 0 = pure credit application)
  positive_gross        numeric(14,2) not null,        -- Σ line.amount where amount > 0
  retainage_withheld    numeric(14,2) not null default 0,   -- Σ line.retainage_withheld
  retainage_released    numeric(14,2) not null default 0,   -- Σ line.retainage_released (credit auto-return, B-8)
  retainage_drawn       numeric(14,2) not null default 0,   -- header-level explicit end-of-job draw (B-5)
  net_invoiced          numeric(14,2) not null,        -- gross − withheld + released + drawn
  actor_person_id       uuid not null references ops.persons(person_id),
  issued_at             timestamptz not null default now(),
  voided_at             timestamptz,
  voided_by             uuid references ops.persons(person_id),
  void_reason           text,
  created_at            timestamptz not null default now(),

  constraint uq_billapp_project_no unique (project_id, application_no),
  constraint ck_billapp_ref_nonblank check (btrim(external_invoice_ref) <> ''),
  constraint ck_billapp_void_shape check (
    status <> 'voided'
    or (voided_at is not null and voided_by is not null
        and void_reason is not null and btrim(void_reason) <> '')),
  constraint ck_billapp_retainage_nonneg check (
    retainage_withheld >= 0 and retainage_released >= 0 and retainage_drawn >= 0),
  constraint ck_billapp_withheld_cap check (retainage_withheld <= positive_gross),   -- v3: positive basis only
  constraint ck_billapp_net check (
    net_invoiced = gross_amount - retainage_withheld + retainage_released + retainage_drawn)
);
-- no two ISSUED apps may record the same RESA invoice ref for a project (voided refs may be re-used)
create unique index uq_billapp_issued_ref
  on ops.billing_application (project_id, lower(btrim(external_invoice_ref))) where status = 'issued';
```
*Cross-row caps* (`retainage_drawn ≤ held_to_date`, `application_no = max+1`, monotonic `period_through`,
`held_to_date ≥ 0`) are enforced by the **header insert-integrity trigger** under a project lock (§8.3)
and a **deferred `held_to_date ≥ 0` backstop** (§8.5) — not column CHECKs. There are **no stored
cumulative `*_to_date` columns** (M-2): G702-style running totals are **derived in `v_project_billing`**
(single source of truth; RESA owns the actual document).

### 6d. `ops.billing_application_line` (membership marker + line-grain retainage)
```sql
create table ops.billing_application_line (
  id                   uuid primary key default gen_random_uuid(),
  application_id       uuid not null references ops.billing_application(id),
  recognition_event_id uuid not null references ops.revenue_recognition_event(id),
  event_type           ops.recognition_event_type not null,    -- recognized | reversal (mirror)
  apparatus_id         uuid not null references ops.apparatus(id),
  scope_id             uuid not null references ops.scopes(id),
  project_id           uuid not null references ops.projects(id),
  amount               numeric(14,2) not null,      -- round(event.recognized_amount, 2), signed
  billable_hours       numeric(14,2) not null,      -- recognized:+round(quoted_hours,2) | reversal:−round(orig.quoted_hours,2)
  retainage_withheld   numeric(14,2) not null default 0,  -- positive line: round(amount*pct,2); credit: 0
  retainage_released   numeric(14,2) not null default 0,  -- credit line: LEAST(orig line withheld, remaining held); positive: 0
  is_voided            boolean not null default false,
  created_at           timestamptz not null default now(),
  constraint ck_billline_retainage_nonneg check (retainage_withheld >= 0 and retainage_released >= 0)
);
create unique index uq_billline_active_event
  on ops.billing_application_line (recognition_event_id) where is_voided = false;   -- PRIMARY no-double-bill guard
create index ix_billline_app on ops.billing_application_line(application_id);
create index ix_billline_apparatus on ops.billing_application_line(apparatus_id);
create index ix_billline_scope on ops.billing_application_line(scope_id);
```
`uq_billline_active_event` is the **primary** no-double-bill enforcer — statement-order-independent and
holding across the Chip-3/Chip-4 lock-target seam where the project lock does not (§8.6). No-double-bill
does **not** rest on the BEFORE-INSERT cross-checks (which only ever validate against *committed* prior
state — M-5). Lines are created only by `issue` and are never deleted; `void` flips `is_voided`.

### 6e. `ops.billing_application_draft` (saved intent — NOT a financial record)
```sql
create table ops.billing_application_draft (
  id                       uuid primary key default gen_random_uuid(),
  project_id               uuid not null references ops.projects(id),
  period_through           date not null,
  exclude_apparatus_ids    uuid[] not null default '{}',
  retainage_draw_request   numeric(14,2) not null default 0,    -- intended end-of-job draw (capped at issue)
  external_invoice_ref     text,                                -- may be pre-filled; required to issue
  actor_person_id          uuid not null references ops.persons(person_id),
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);
```
A draft holds **no lines, no number, no totals**; its preview is advisory (`v_draft_preview`, §9).
Tampering a draft is harmless: `issue` recomputes the sweep fresh and never reads draft aggregates.

## 7. Functions (the sole mutation path; invariants also asserted by §8 triggers/constraints)

Each of the four functions sets the **txn-local context flag** `set_config('ops.billing_ctx','1',true)` at
entry **and resets it to `'0'` immediately before returning** (so the flag does not linger for the rest of an
explicit transaction — High, audit #3; on an exception the function's subtransaction rollback clears it too).
The billing-table *mutation* triggers (§8.1–8.4) reject any change made without it, so these functions are the
only non-accidental way to create/void a billing application. `record`/`issue`/`void` then take
`select … from ops.projects where id = ? for update` (serialize Chip-4-vs-Chip-4 on a project).

### 7a. `record_billing_application(p_project_id, p_actor_person_id, p_period_through, p_external_invoice_ref default null, p_exclude_apparatus uuid[] default '{}', p_retainage_draw_request numeric default 0) returns uuid`
- `p_external_invoice_ref` non-blank → **issue immediately** (the §7b logic). Else → insert a draft; return its id.

### 7b. `issue_billing_application(…, p_external_invoice_ref, …) returns uuid`
1. Project `FOR UPDATE`; reject if not found / `not is_active` / `status='Cancelled'`. Require non-blank ref.
2. **Monotonic period:** reject if any *issued* app for the project has `period_through > p_period_through`.
3. **Preliminary sweep** of the §5 set → the candidate recognition-event ids.
4. **Lock the candidate events to close the Chip-3 reversal race (High-A):**
   `perform 1 from ops.revenue_recognition_event where id = any(candidate_ids) order by id for update`
   (deterministic order avoids deadlock; the row lock **conflicts with Chip 3's `reverse_recognition`**,
   which `FOR UPDATE`s the event row). Then **re-evaluate §5 eligibility under the lock** — a reversal that
   committed before the lock is now visible and drops the positive event; from here the set is stable.
5. **Build lines.** Positive lines: `retainage_withheld = round(amount*pct,2)`, `retainage_released = 0`.
   Credit lines, walked in the **canonical order `ORDER BY orig-event.recognized_at, recognition_event_id`**
   (so the per-line split is reproducible), each releasing `LEAST(orig-line.retainage_withheld, remaining_held)`
   and decrementing `remaining_held` (starts at `held_before = Σwithheld−Σreleased−Σdrawn over issued apps`).
   The running clamp keeps `held ≥ 0` by construction (B-8 / C-2).
6. `gross/positive_gross/billable_hours/retainage_withheld/retainage_released = Σ` over the lines.
7. Validate `0 ≤ p_retainage_draw_request ≤ held_before − Σ(this app's releases)`; `retainage_drawn = request`.
8. Empty sweep **and** `retainage_drawn = 0` → raise `nothing to bill`. `net = gross − withheld + released + drawn`.
9. `application_no = coalesce(max(application_no),0)+1` (under the project lock; burned forever).
10. Insert the `billing_application` (status `issued`) + its lines atomically; if promoting a draft, delete it.

### 7c. `discard_draft_billing_application(p_draft_id, p_actor_person_id)` — delete a draft.

### 7d. `void_billing_application(p_application_id, p_actor_person_id, p_reason) returns void`
Require non-blank reason; `select … for update` on the app + project; reject if `status <> 'issued'`. The
function sets `status='voided'`, `voided_at/by`, `void_reason`; the **§8.1 trigger** runs the void-dependency
guard **and cascades `is_voided=true` to every line** (so lines always follow the header, even on a direct
void attempt — which the §8.0 gate already blocks). `application_no` stays burned.

## 8. Integrity & triggers (triggers, not grants; superuser/BYPASSRLS app role)

0. **Function-only mutation gate (misuse guard, not a security boundary).** Every *mutation* trigger
   (1–4) first checks `current_setting('ops.billing_ctx', true) = '1'` (the §7 functions set it at entry,
   reset at return) and **raises if absent** — so the three billing tables (`billing_application`,
   `billing_application_line`, **and** `billing_application_draft`) are created/updated/deleted only inside
   the four functions. This makes the function's atomic credit-release allocation the only one that exists
   (closing accidental direct-DML under/over-release — High-B) and blocks an accidental direct header-only
   void. **It is not a security control:** the superuser/BYPASSRLS app role can spoof the GUC; the gate stops
   buggy/accidental DML (ORM, migration, careless `UPDATE`), not a determined operator. **The deferred
   assertion trigger (5) does NOT check the flag** — it always runs (it fires at COMMIT, after the function
   has returned and reset the flag). The triggers catch *structural* drift; the credit-release allocation is
   function-owned and pinned by tests (Medium, audit #3), not re-derived here.
1. **Header immutability + void guard** (`before update **or delete** on ops.billing_application`): DELETE
   blocked; UPDATE permitted only for `issued→voided` (writing exactly `status/voided_at/voided_by/void_reason`).
   On that transition the trigger **(i)** `perform 1 from ops.projects where id = old.project_id for update`
   (serialize); **(ii)** runs the **void-dependency guard** — reject if EXISTS another *issued* application
   with an active (`is_voided=false`) line `L` where `L.recognition_event_id` is a **reversal event** whose
   `reverses_event_id` ∈ {the `recognition_event_id` of THIS app's active lines} (a standing credit — C-2);
   and **(iii) cascades the line-void:** `update ops.billing_application_line set is_voided=true where
   application_id = old.id and is_voided=false` (lines always follow the header — closes the header-only-void
   strand). The held-side dependency (C-1) is caught by the §8.5 `held ≥ 0` backstop.
2. **Line immutability** (`before update or delete on ops.billing_application_line`): DELETE blocked;
   UPDATE permitted only for `is_voided false→true`.
   - **Draft table** (`before insert or update or delete on ops.billing_application_draft`): the §8.0 gate
     only — flag required, no further integrity rules. Drafts are non-financial intent; `issue` re-derives
     the sweep from the draft's params and re-validates every invariant, so a (gate-blocked) draft edit can
     at worst change *which valid set* bills, never break an invariant.
3. **Header insert-integrity** (`before insert on ops.billing_application`): `project FOR UPDATE` (serialize
   concurrent inserters), then `external_invoice_ref` non-blank, `application_no = max(existing)+1`,
   `period_through ≥` every issued app's `period_through`, and `retainage_drawn ≤ held_to_date` (a fast
   upper-bound; the **exact** draw+release interaction is the §8.5 `held≥0` enforcer — Med-C).
4. **Line insert-integrity** (`before insert on ops.billing_application_line`), against **committed** state
   only (M-5): the event exists; `event_type/apparatus_id/scope_id/project_id` match it;
   `amount = round(event.recognized_amount,2)` and (positive line) **`amount > 0`** (skip sub-cent rows that
   round to 0 — they must not consume the no-double-bill slot); `billable_hours = round(quoted_hours,2)`
   (positive) / `−round(orig.quoted_hours,2)` (credit, M-4); `retainage_withheld` matches the §5 positive
   rule; `retainage_released` is `0` (positive) or `≤ orig-line.retainage_withheld` (credit); `project_id` =
   the application's project. **Branch eligibility (High-A):** a positive line's event must still be
   **unreversed** (`not exists` a reversal of it); a credit line's original must still have an **active
   issued** line. No-double-bill rests solely on `uq_billline_active_event`, not on these cross-checks.
5. **Deferred consistency** (`constraint trigger after insert or update on both tables, deferrable initially
   deferred`; DELETE is blocked by 1/2 so the DELETE arm is defensive-only). "Touched application" = DISTINCT
   `application_id` over inserted/updated **line** rows ∪ inserted/updated **header** rows (resolved via
   `line.application_id` so a line-only injection is caught — M-3). For each touched **issued** application,
   re-aggregate and assert
   `gross_amount/positive_gross/billable_hours/retainage_withheld/retainage_released = Σ over its active lines`.
   For each touched **project**, assert `held_to_date = Σ(withheld − released − drawn) over **status='issued'
   apps only** ≥ 0` (the just-voided app drops out — this is the authoritative held + draw-cap enforcer, Med).
   Voided headers retain historical aggregates and are exempt from header=Σlines (their lines are all `is_voided`).
6. **Lock-seam note:** the project lock serializes only Chip-4-vs-Chip-4 on one project. Correctness against
   concurrent Chip-3 reversal rests on the **event-row `FOR UPDATE` taken in `issue` (§7b step 4)** — which
   conflicts with `reverse_recognition`'s event lock — plus `uq_billline_active_event` (the primary
   no-double-bill guard; never weaken it to non-unique).

## 9. Views

- **`ops.v_unbilled_recognition`** — §5 (active line ≡ issued); the backlog feeding the sweep.
- **`ops.v_draft_preview`** — advisory: each draft's would-be sweep (non-binding; recomputed at issue).
- **`ops.v_billing_application_sov`** — per `(application_id, scope_id)` over non-voided lines:
  `apparatus_count, billable_hours, amount, retainage_withheld, retainage_released` (schedule-of-values).
- **`ops.v_project_billing`** — per project, fully derived, isolated from RESA: `contract_value`,
  `recognized_to_date` (= **Σ round(e.recognized_amount,2)** over **ALL** `revenue_recognition_event` rows
  for the project — both `recognized` and `reversal`, signed; a `+X` and its `−X` each round then cancel, so
  this is *not* a reversed-event-filtered subset — same per-event rounding as the lines, so
  `recognized = billed + unbilled` ties to the cent, M-2), `billed_gross_to_date` (Σ gross
  over issued), `net_invoiced_to_date` (Σ net over issued), `retainage_held_to_date`
  (Σwithheld − Σreleased − Σdrawn over issued), `unbilled_recognized` (Σ amount from `v_unbilled_recognition`),
  `open_draft_count`.

## 10. Reversibility

`006_progress_billing_down.sql` — idempotent `drop … if exists` in reverse-dependency order: the 4 views,
triggers + their functions, the 4 PL/pgSQL functions, the 3 tables (line → application → draft), the status
enum, and `alter table ops.projects drop column if exists retainage_pct`. Leaves Chips 1/2/3 intact (never
drops the `ops` schema). Validation gate = up → down → up clean.

## 11. Testing (TDD on `ops_test`)

`test_006_progress_billing.py` chains `001→002→004→005→006` then down-nukes; per-test rollback; `Decimal`
assertions. Coverage (≈ 45 cases):

- **Schema/guards:** retainage_pct bounds; header CHECKs (ref-nonblank, void-shape, **withheld ≤
  positive_gross**, net arithmetic incl. drawn); `uq_billline_active_event` blocks a second active line;
  `uq_billapp_issued_ref` blocks a **duplicate RESA invoice ref** among issued apps (but allows reuse after a
  void); header/line DELETE + illegal-UPDATE blocked; **deferred header=Σlines** fires on a (gate-bypassed)
  line insert into a *pre-existing committed* issued app; **deferred held≥0** fires on a (gate-bypassed) over-release.
- **function-only gate (§8.0):** a direct `INSERT`/`UPDATE`/void on a billing table **without** the
  `ops.billing_ctx` flag is rejected; the four functions (which set it) succeed. **Flag containment:** call a
  function inside an explicit transaction, then attempt direct DML before commit — it is **rejected** (the
  function reset the flag at return). The deferred §8.5 assertion still fires at COMMIT regardless of the flag.
- **credit-bearing apps issue (C-1 fix):** a **pure-credit** application (gross<0) issues; a **mixed** app
  where Σcredits ≥ Σpositives issues; withheld is capped at positive_gross (never blocked by the credit).
- **bill→draw→reverse (C-2 fix):** bill X, draw its retainage, reverse X → the credit issues with
  `released = LEAST(orig, remaining held) = 0`, net = −gross, held stays ≥ 0; no wedge; a later bill on the
  same project still issues.
- **line-grain retainage (B-8):** positive `withheld = round(amount*pct,2)`; a credit (no prior draw)
  `released =` orig line withheld, customer net-credited = net originally billed, held decrements exactly;
  partial reversal (some apparatus of a multi-apparatus app) credits only those.
- **rounding (M-1/M-2):** a multi-apparatus project with non-2dp `quoted_revenue` (hours·rate → .333…)
  proves `recognized_to_date == billed_gross_to_date + unbilled_recognized` exactly; line-grain withheld
  documented/asserted.
- **draft = intent (B-4):** tampering a draft row does not change the issued result; a draft reserves
  nothing (its apparatus stay in `v_unbilled_recognition`); draft→reverse→issue bills only the live set;
  discard removes the draft.
- **period/timezone:** an event recognized after the Phoenix period cutoff is excluded; a credit sweeps even
  when the reversal's `recognized_at` is after `period_through`; monotonic-period rejection.
- **excludes (B-6):** an excluded positive apparatus is held back; a credit for an excluded apparatus still sweeps.
- **unbilled set:** never-billed-then-reversed pair never bills; billed-then-reversed surfaces a credit.
- **void-dependency (trigger layer, H-3):** void releases lines → events return to unbilled; void of an app
  whose event has a **standing issued credit** is rejected by the §8.1 guard; a void that would drive held<0
  is rejected (§8.5); `application_no` stays burned; the §8.1 line-cascade voids every line.
- **Chip-3 reversal race (High-A):** an `issue` whose candidate event is reversed mid-flight re-evaluates
  under the §7b event lock and excludes it (positive) / handles the credit; the §8.4 branch-eligibility check
  rejects a (gate-bypassed) positive line whose event is now reversed.
- **canonical credit order (B-8):** a partial reversal where remaining_held < Σ orig-withheld produces a
  reproducible per-line `released` split under the `ORDER BY orig recognized_at, event_id` walk (and aggregate
  held/customer-net are order-invariant); a sub-cent recognized_amount that rounds to 0.00 is skipped, not billed.
- **draw (B-5):** explicit draw capped by held-to-date (over-draw rejected); a pure-draw app (empty sweep,
  drawn>0) issues.
- **reconciliation:** `v_project_billing` / `v_billing_application_sov` tie out across a multi-app,
  multi-scope project after a mid-ladder void (no stale cumulative).

## 12. Out of scope (deferred)

- Customer-invoice / pay-app document **generation**, AR/GL posting, cash-receipt application (RESA accounting).
- **Automatic** end-of-job retainage draw (draw stays explicit — B-5).
- A header-level `retainage_withheld` **override** (the chip uses line-grain pct as the control; recording a
  RESA actual that differs from pct×amount is a future reconciliation extension).
- Override-with-reason exclusion of credits (credits non-excludable — B-6).
- The `/pm-review` app-bridge surfacing `record`/`issue`/`void` + the views through the control-plane API
  (a later bounded packet).
- Convergence of `ops.*` billing onto the deployed `seam.*` surfaces (Chip N).

## 13. Provenance

- Lane SSoT `reference/ops/00-MASTER-INDEX.md` §5 / §5a + D-OPS-3.
- Chip 3 ledger `005_recognition_ledger.sql` (the immutable event substrate this chip reads).
- Operator ratification (B-1…B-8) + three operator audits + three review workflows, 2026-06-21.
