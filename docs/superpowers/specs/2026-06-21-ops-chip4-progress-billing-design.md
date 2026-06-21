# Ops Chip 4 — Progress Billing (design spec, v2)

> **Lane SSoT:** `reference/ops/00-MASTER-INDEX.md` (§5 revenue/progress-billing model; D-OPS-3).
> **Builds on:** Chip 1 (`001` identity), Chip 2 (`002` quote model), the person anchor (`004`),
> and **Chip 3 (`005` recognition ledger)** — FKs into `ops.revenue_recognition_event`.
> **Migration:** `006_progress_billing.sql` (+ `_down` + `test_006_progress_billing.py`).
> **Dev only.** TDD on throwaway `ops_test`; gated apply to `ops_dev`. Nothing applied to prod.
> **Status:** design v2 — hardened against two adversarial audits (a 5-lens review workflow +
> two operator audits, 2026-06-21). Awaiting operator sign-off.

---

## 1. Goal

Record what RESA accounting has **invoiced** against recognized work, and track **billable hours**,
without becoming the system of record for accounting. The platform's value is the **reconciliation
view** — recognized-to-date vs invoiced-to-date vs still-unbilled, plus retainage held — kept
**isolated from RESA's AR/GL**. Chip 4 does **not** generate the customer invoice or post to a ledger;
it records that an invoice was raised, which recognized apparatus it covered, and the retainage on it.

## 2. The two-stage money pipeline

Chip 3 *earns* revenue (recognition); Chip 4 records the *invoicing* of it. They are deliberately
decoupled — recognition fires continuously as apparatus complete; billing is periodic.

```
RECOGNIZED  (Chip 3 — immutable, append-only events)        per apparatus, signed
        │     recognized +X   /   reversal −X
        ▼
UNBILLED    = the two-branch set in §5 (active line ≡ an ISSUED line)   → ops.v_unbilled_recognition
        │
        │   record_billing_application(project, actor, period_through, invoice_ref?, exclude[], release?)
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
  The membership line *is* the billed marker — there is no `billed` column on the event.
- **Isolation from RESA accounting.** Records `external_invoice_ref` + hours/amounts/retainage; never
  drives AR/GL. No payment receipt / cash application in this chip.
- **Header is a pure rollup of its lines.** Every financial aggregate on `billing_application` equals
  the sum over its active lines (enforced by a deferred constraint, §8). Retainage is allocated at
  **line grain** so reversals release exactly the retainage attributable to the reversed apparatus.
- **Reverse-first lifecycle (extended to billing).** An application cannot be voided while a later
  issued application depends on it (a credit of its events, or a release of its withheld retainage).

## 4. Operator decisions (ratified 2026-06-21, incl. both audits)

| ID | Decision | Resolution |
|---|---|---|
| **B-1** | Billing model | **Per-project retainage rate.** Track billable hours + record invoicing; isolated from RESA. |
| **B-2** | Line selection | **Auto-sweep unbilled recognized ≤ `period_through`, minus an `exclude[]` apparatus list.** |
| **B-3** | Lifecycle / corrections | **Atomic record + void-to-correct.** Issued applications immutable; correct by void + re-record. |
| **B-4 (v2)** | Draft model | **Draft = saved intent, materialized at issue.** A separate `billing_application_draft` holds only params; it persists no lines, reserves no events, consumes no number, holds no totals. `issue` runs a fresh sweep. *(Supersedes the v1 "draft reserves lines" — the root of three audit findings.)* |
| **B-5** | Retainage release | **Explicit + capped by held-to-date; no auto end-of-job release.** Withholding on **positive gross only**. |
| **B-6** | Credits non-excludable | Reversal credits for already-billed work always sweep; `exclude[]` suppresses positive work only. |
| **B-7** | Reversal-of-billed | **Automatic next-application credit** (§5 credit branch). |
| **B-8 (new)** | Retainage grain + credit | **Line-grain retainage; a credit auto-returns the retainage withheld on the reversed apparatus's original line** (customer net-credited = net originally billed; `held_to_date` decrements). |

### Audit findings folded into v2

**5-lens review workflow** (verdict was *block* on the v1 spec): C-1 void→negative-held, C-2 void→double-credit,
C-3 draft-tamper-promotes, H-1 credit-branch-counts-draft, H-2 credit-skips-retainage, H-3 withheld-cap,
M-1 credit-vs-period, M-2 stale-cumulative, M-3 rounding, M-4 lock-target-doc, M-5 cascade-ambiguity.
**Operator audit #2:** stale-draft-after-reversal, direct-line-writes-lie, header-direct-insert-bypass,
draft-value-vanishes, timezone-dependent cutoff. **Every finding is resolved below**; the draft=intent-only
model (B-4 v2) and line-grain retainage (B-8) dissolve the majority structurally.

## 5. The unbilled set — `ops.v_unbilled_recognition`

**active line ≡ a `billing_application_line` with `is_voided = false` whose application `status='issued'`.**
(Drafts hold no lines, so "active" is simply *issued* — this dissolves H-1 and the stale-draft finding.)

```
positive branch :  recognized event e
                   WHERE e.event_type = 'recognized'
                     AND NOT EXISTS (reversal r : r.reverses_event_id = e.id)   -- not reversed
                     AND NOT EXISTS (active line on e.id)                        -- not already billed
                   line amount  = round(e.recognized_amount, 2)   (> 0)
                   line hours   = e.quoted_hours                  (> 0)

credit branch   :  reversal event e
                   WHERE e.event_type = 'reversal'
                     AND EXISTS     (active line on e.reverses_event_id)         -- original IS issued-billed
                     AND NOT EXISTS (active line on e.id)                        -- this credit not billed
                   line amount  = round(e.recognized_amount, 2)   (< 0)
                   line hours   = −(original recognized event).quoted_hours      (< 0)   -- HIGH-2 (signed)
                   line released = (original's issued billing line).retainage_withheld   -- B-8 (auto-return)
```

**Why two branches:** a recognition reversed before it was ever billed never reaches a bill (its `+X` is
excluded as reversed, its `−X` excluded as original-not-billed). A reversal of already-billed work surfaces
as the credit branch, returning both the gross and its line-grain retainage (B-8).

**Period bounds (M-1, timezone fix):** the `record`/`issue` sweep filters the **positive** branch by
`e.recognized_at < (p_period_through + 1)::timestamp AT TIME ZONE 'America/Phoenix'` (explicit billing
timezone — Project Miner is PHX, no DST). **Credit-branch lines are exempt from the upper bound** (a credit
must always sweep onto the next application regardless of the reversal's wall-clock time — mirrors B-6).
`exclude[]` suppresses positive-branch apparatus only.

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
  -- aggregates = Σ over active lines (deferred constraint §8); money is numeric(14,2)
  billable_hours        numeric(14,2) not null,        -- Σ line.billable_hours (signed)
  gross_amount          numeric(14,2) not null,        -- Σ line.amount (signed; < 0 = pure credit application)
  positive_gross        numeric(14,2) not null,        -- Σ line.amount where amount > 0
  retainage_withheld    numeric(14,2) not null default 0,   -- Σ line.retainage_withheld
  retainage_released    numeric(14,2) not null default 0,   -- Σ line.retainage_released (credit auto-returns, B-8)
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
  constraint ck_billapp_withheld_cap check (retainage_withheld <= least(positive_gross, gross_amount)),  -- H-3
  constraint ck_billapp_net check (
    net_invoiced = gross_amount - retainage_withheld + retainage_released + retainage_drawn)
);
```
*Cross-row caps* (`retainage_drawn ≤ held_to_date`, `application_no = max+1`, monotonic `period_through`)
are enforced by the **header insert-integrity trigger** (§8.3) and a **deferred `held_to_date ≥ 0`
constraint** (§8.5) — not column CHECKs. There are **no stored cumulative `*_to_date` columns** (M-2):
the G702-style running totals are **derived in `v_project_billing`** (single source of truth; RESA owns the
actual document).

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
  billable_hours       numeric(14,2) not null,      -- recognized:+quoted_hours | reversal:−orig.quoted_hours
  retainage_withheld   numeric(14,2) not null default 0,  -- positive line: round(amount*pct,2); credit: 0
  retainage_released   numeric(14,2) not null default 0,  -- credit line: orig line's retainage_withheld; positive: 0
  is_voided            boolean not null default false,
  created_at           timestamptz not null default now(),
  constraint ck_billline_retainage_nonneg check (retainage_withheld >= 0 and retainage_released >= 0)
);
create unique index uq_billline_active_event
  on ops.billing_application_line (recognition_event_id) where is_voided = false;   -- PRIMARY no-double-bill guard
create index ix_billline_app       on ops.billing_application_line(application_id);
create index ix_billline_apparatus on ops.billing_application_line(apparatus_id);
create index ix_billline_scope     on ops.billing_application_line(scope_id);
```
`uq_billline_active_event` is the **primary** no-double-bill enforcer — it holds across the Chip-3/Chip-4
lock-target seam where the project lock does not (§8.6 / M-4). Lines are created only by `issue`/`record`
(atomically with the header) and are never deleted; `void` flips `is_voided`.

### 6e. `ops.billing_application_draft` (saved intent — NOT a financial record)
```sql
create table ops.billing_application_draft (
  id                       uuid primary key default gen_random_uuid(),
  project_id               uuid not null references ops.projects(id),
  period_through           date not null,
  exclude_apparatus_ids    uuid[] not null default '{}',
  retainage_drawn_request  numeric(14,2) not null default 0,   -- intended end-of-job draw (capped at issue)
  external_invoice_ref     text,                                -- may be pre-filled; required to issue
  actor_person_id          uuid not null references ops.persons(person_id),
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);
```
A draft holds **no lines, no number, no totals**. Its preview is advisory (`v_draft_preview`, §9). Tampering
with a draft is harmless: `issue` recomputes the entire sweep fresh and never reads draft aggregates.

## 7. Functions (the gated entry points)

`record`/`issue`/`discard`/`void` all take `select … from ops.projects where id = ? for update` first, so
Chip-4-vs-Chip-4 operations on a project serialize. (Cross-Chip-3 safety rests on §5 live re-evaluation +
`uq_billline_active_event`, **not** lock exclusion — see §8.6 / M-4.)

### 7a. `record_billing_application(p_project_id, p_actor_person_id, p_period_through, p_external_invoice_ref default null, p_exclude_apparatus uuid[] default '{}', p_retainage_drawn_request numeric default 0) returns uuid`
- If `p_external_invoice_ref` is non-blank → **issue immediately** (delegates to the §7b sweep+materialize logic).
- Else → insert a `billing_application_draft` with the params; return the draft id.

### 7b. `issue_billing_application(p_draft_or_project, p_actor_person_id, p_external_invoice_ref, …) returns uuid`
Promotes intent → financial record. (Called by `record` when a ref is supplied, or on a saved draft.)
1. Lock the project; reject if not found / `not is_active` / `status='Cancelled'`. Require non-blank ref.
2. **Monotonic period (HIGH-3):** reject if any *issued* app for the project has `period_through > p_period_through`.
3. **Fresh sweep** of the §5 set: positive branch (≤ period cutoff, Phoenix tz, minus `exclude[]`) + credit
   branch (all, unbounded). For each line compute `amount`, `billable_hours`, `retainage_withheld`
   (positive: `round(amount*pct,2)`; credit: 0), `retainage_released` (positive: 0; credit: the reversed
   event's original issued line's `retainage_withheld`).
4. `gross = Σ amount`; `positive_gross = Σ amount where >0`; `billable_hours = Σ hours`;
   `retainage_withheld = Σ line.retainage_withheld`; `retainage_released = Σ line.retainage_released`.
5. `held_to_date = Σ(retainage_withheld) − Σ(retainage_released) − Σ(retainage_drawn) over issued apps`;
   validate `0 <= p_retainage_drawn_request <= held_to_date`; `retainage_drawn = p_retainage_drawn_request`.
6. If the sweep is empty **and** `retainage_drawn = 0` → raise `nothing to bill`.
7. `net = gross − retainage_withheld + retainage_released + retainage_drawn`.
8. `application_no = coalesce(max(application_no),0)+1` (under the project lock; burned forever).
9. Insert the `billing_application` (status `issued`) + its lines atomically; if promoting a draft, delete it.
   Return the application id.

### 7c. `discard_draft_billing_application(p_draft_id, p_actor_person_id)` — delete a draft (no number consumed, nothing to release).

### 7d. `void_billing_application(p_application_id, p_actor_person_id, p_reason) returns void`
1. Require non-blank reason; lock the app + its project; reject if `status <> 'issued'`.
2. **Void-dependency guard (C-1/C-2):** reject if **either** —
   (a) any other *issued* application has an active line whose `recognition_event_id` is a **reversal of an
   event billed by this application** (its credit is standing — void that first); or
   (b) excluding this application would drive the project's `held_to_date` below 0 (a later release/draw
   depends on this app's withholding — void that first).
3. Set `status='voided'`, `voided_at/by`, `void_reason`; flip every line `is_voided=true` (releasing its
   events back to unbilled). `application_no` stays burned.

## 8. Integrity & triggers (Chip-3-consistent — triggers, not grants; superuser BYPASSRLS app role)

1. **Header immutability** (`before update or delete on ops.billing_application`): DELETE always blocked;
   UPDATE permitted only for the `issued→voided` transition (setting the void columns); any other column
   drift or status change raises.
2. **Line immutability** (`before update or delete on ops.billing_application_line`): DELETE always blocked
   (lines are never deleted — drafts have none; void flips `is_voided`); UPDATE permitted only for
   `is_voided false→true`.
3. **Header insert-integrity** (`before insert on ops.billing_application` — direct inserts cannot bypass
   cross-row rules, the Chip-3 lesson applied to the header / operator audit #2): `external_invoice_ref`
   non-blank; `application_no = max(existing)+1` for the project; `period_through` ≥ every issued app's
   `period_through`; `retainage_drawn ≤ held_to_date`. Raise on violation.
4. **Line insert-integrity** (`before insert on ops.billing_application_line`): the event exists;
   `event_type/apparatus_id/scope_id/project_id/amount` match the referenced event (amount rounded);
   `billable_hours` equals the §5 rule; `retainage_withheld`/`retainage_released` equal the §5 line rule;
   `project_id` equals the application's project. (No-double-bill held by `uq_billline_active_event`.)
5. **Deferred consistency** (`constraint trigger … after insert or update or delete … deferrable initially
   deferred` on both tables; a missing/absent parent application ⇒ "nothing to assert"): at COMMIT, for each
   touched **issued** application, assert `gross_amount/positive_gross/billable_hours/retainage_withheld/
   retainage_released = Σ over its active lines` (header is a pure rollup — H-2 / C-3). Separately assert
   each project's `held_to_date >= 0` (C-1). Voided headers retain historical aggregates and are exempt from
   the header=Σlines check (their lines are all `is_voided`).

## 9. Views

- **`ops.v_unbilled_recognition`** — §5 (active line ≡ issued); the backlog feeding the sweep / a "ready to bill" surface.
- **`ops.v_draft_preview`** — advisory: for each draft, the would-be sweep (positive ≤ period − excludes, plus
  credits) with provisional gross/hours/retainage. Non-binding; recomputed for real at issue.
- **`ops.v_billing_application_sov`** — per `(application_id, scope_id)` over non-voided lines:
  `apparatus_count, billable_hours, amount, retainage_withheld, retainage_released` = the schedule-of-values.
- **`ops.v_project_billing`** — per project reconciliation (all derived, isolated from RESA):
  `contract_value`, `recognized_to_date` (Chip 3 net, rounded), `billed_gross_to_date` (Σ gross over issued),
  `net_invoiced_to_date` (Σ net over issued), `retainage_held_to_date` (Σ withheld − Σ released − Σ drawn over
  issued), `unbilled_recognized` (Σ amount from `v_unbilled_recognition`), `open_draft_count`.

## 10. Reversibility

`006_progress_billing_down.sql` — idempotent `drop … if exists` in reverse-dependency order: the 4 views,
the triggers + their functions, the 4 PL/pgSQL functions, the 3 tables (line → application → draft), the
status enum, and `alter table ops.projects drop column if exists retainage_pct`. Leaves Chips 1/2/3 intact
(never drops the `ops` schema). Validation gate = up → down → up clean.

## 11. Testing (TDD on `ops_test`)

`test_006_progress_billing.py` chains `001→002→004→005→006` then down-nukes; per-test rollback; `Decimal`
assertions. Coverage (≈ 40 cases):

- **Schema/guards:** retainage_pct bounds; header CHECKs (ref-nonblank, void-shape, withheld-cap=LEAST,
  net arithmetic incl. drawn); `uq_billline_active_event` blocks a second active line; header/line DELETE +
  illegal-UPDATE blocked; **header insert-integrity** rejects a direct insert with bad app_no / stale period /
  over-draw; **deferred header=Σlines** fires on a direct line insert into an issued app; **deferred
  held≥0** fires.
- **record/issue (happy path):** single + multi-apparatus issue; aggregates = Σ lines; `application_no`
  sequential; draft saved when no ref; draft promoted on issue with a **fresh** sweep.
- **draft = intent (B-4 v2):** tampering a draft row does not change the issued result; a draft reserves
  nothing (its apparatus stay in `v_unbilled_recognition`); draft-then-reverse-then-issue bills only the
  live set; discard removes the draft.
- **period/timezone (M-1, tz):** an event recognized after the period cutoff (Phoenix) is excluded; a credit
  is swept even when the reversal's `recognized_at` is after `period_through`; monotonic-period rejection.
- **excludes (B-6):** an excluded positive apparatus is held back; a credit for an excluded apparatus still sweeps.
- **unbilled set (HIGH-1):** never-billed-then-reversed pair never bills; billed-then-reversed surfaces a credit.
- **line-grain retainage (B-8):** positive line `withheld = round(amount*pct,2)`; a credit line `released =`
  the original line's `withheld`; customer net-credited = net originally billed; `held_to_date` decrements by
  exactly the reversed apparatus's retainage; a mixed +/− application keeps `withheld ≤ gross` (H-3).
- **retainage draw (B-5):** explicit `retainage_drawn` capped by held-to-date (over-draw rejected); a pure
  draw application (empty sweep, drawn>0) issues.
- **void-dependency (C-1/C-2):** void releases lines → events return to unbilled; void of an app whose event
  has a **standing issued credit** is rejected; void that would drive held<0 is rejected; `application_no`
  stays burned after void.
- **reconciliation (M-2):** `v_project_billing` and `v_billing_application_sov` tie out across a multi-app,
  multi-scope project after a mid-ladder void (no stale cumulative).

## 12. Out of scope (deferred)

- Customer-invoice / pay-app document **generation**, AR/GL posting, cash-receipt application (RESA accounting).
- **Automatic** end-of-job retainage release (release/draw stays explicit — B-5).
- A header-level `retainage_withheld` **override** (v2 uses line-grain pct as the control; recording a
  RESA actual that differs from pct×gross is a future reconciliation extension — flagged for operator).
- Override-with-reason exclusion of credits (credits non-excludable — B-6).
- The `/pm-review` app-bridge surfacing `record`/`issue`/`void` + the views through the control-plane API
  (a later bounded packet, like the Chip 3 bridge).
- Convergence of `ops.*` billing onto the deployed `seam.*` surfaces (Chip N).

## 13. Provenance

- Lane SSoT `reference/ops/00-MASTER-INDEX.md` §5 / §5a (hours-based binary-completion model) + D-OPS-3.
- Chip 3 ledger `005_recognition_ledger.sql` (the immutable event substrate this chip reads).
- Operator design ratification (B-1…B-8) + two adversarial audits + a 5-lens review workflow, 2026-06-21.
