# Ops Chip 3 — Recognition Ledger Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (or executing-plans) to implement the plan derived from this spec, task-by-task.

**Goal:** Add an append-only, apparatus-grain revenue-recognition ledger to the clean `ops.*` substrate so that a tech-lead's *approval* of a completed apparatus produces a durable recognized-revenue event, honoring the recognition firewall (frozen `quoted_*` stays on the apparatus; recognized $ exist only as events).

**Architecture:** One numbered SQL migration on the existing lane rails — `infra/database/migrations/ops/005_recognition_ledger.sql` (+ `_down` + `test_005_recognition_ledger.py`), TDD on a throwaway `ops_test`. It adds: two enums, one append-only ledger table (append-only + invariant-enforcing insert triggers), two gated PL/pgSQL functions, four rollup/queue views, recognition-protection guards across apparatus/scope/project + a frozen-basis immutability guard, and supporting constraints/indexes. No new package, no app, no prod. The lead-review UI, the records datasheet live-verification, and the CxAlloy integration are explicitly **later bridge packets** — Chip 3 is the engine they will call.

**Tech Stack:** PostgreSQL 17 (host `ops_dev` / `ops_test`), PL/pgSQL, pytest via `uv run --with "psycopg[binary]" --with pytest`.

**Lane:** branch `ops/chip3-recognition-ledger`, host worktree `/home/olares/code/apex/apex-ops-chip3`, off `main@629fa735`. Dev-only; merge to `main` is **operator-gated**. SSoT: `reference/ops/00-MASTER-INDEX.md`.

## Global Constraints (from the SSoT laws + this lane's rulings)

- **Law 3 — recognition firewall:** NO recognized-$ columns on any existing table. Recognized revenue lives ONLY in the new event ledger. The frozen quote (`ops.apparatus.quoted_hours/quoted_revenue`, `ops.scope_quote.*`) is read, never mutated by Chip 3.
- **Apparatus is the recognition unit** (`001_identity_skeleton.sql`). Recognition is **gated by `apparatus.status = 'Complete'`** (testing done) and is decoupled only from *assessment outcome* and *external verification* — not from status.
- **The gate is the tech-lead's approval.** Recognition is a deliberate authorized act (`ops.approve_and_recognize`), never an auto-trigger on status.
- **Assessment-independent:** `Pass`/`Fail`/`Marginal` is stamped on the event for audit but never blocks recognition (binary completion = the sole driver, D-OPS-8).
- **Hard person FK (ruling A):** the ledger actor is a domain signer on a financial row → `actor_person_id uuid NOT NULL REFERENCES ops.persons(person_id)`. D6's provenance-column carve-out (`created_by`/`updated_by`/`approved_by` stay FK-less) does NOT apply to a financial-ledger signer. Login traceability, if ever needed, is a *separate* future soft `actor_auth_user_id uuid` — not built here.
- **Both obligations cleared, explicitly (ruling B):** recognition requires the lead to clear BOTH the datasheet and the CxAlloy obligation, modeled as explicit dispositions — NOT hidden inside a boolean. Live verification of the underlying systems stays out of scope.
- **Reversible `_down`**; validation gate = up → down → up clean + the `test_005_*.py` invariant suite. `_down` drops ONLY Chip-3 objects; never the `ops` schema or prior chips.
- All numeric money compares use the frozen quote as the basis; missing/unfrozen basis must **raise**, never silently recognize (field-trust rule).
- **Active-row only (pinned — no inactive/cancelled recognition):** recognition requires the apparatus AND its parent scope AND project to all be `is_active = true` and not `Cancelled`. Inactive/cancelled objects never recognize; the review queue and rollup views exclude them; **and a row with descendant open recognition cannot be deactivated or cancelled until reversed** (Component 4 protection guards). (`ops.{projects,scopes,apparatus}` each carry `is_active boolean DEFAULT true`; `project_status`/`scope_status` each include `Cancelled`.)
- **Frozen basis is immutable:** once `ops.scope_quote.is_frozen = true`, the quote/basis columns are locked by a guard trigger (Component 5) so recognized totals stay reconcilable against the snapshot. Chip 3 supplies the enforcement Chip 2 declared but left open (`002_quote_model.sql` leaves `scope_quote` + apparatus quote columns mutable).

---

## Component 1 — Enums

```sql
CREATE TYPE ops.recognition_event_type AS ENUM ('recognized', 'reversal');
CREATE TYPE ops.obligation_clearance  AS ENUM ('provided', 'not_applicable');
```

`obligation_clearance` is the ruling-B disposition: `provided` = the deliverable exists (and a ref must point to it); `not_applicable` = this obligation legitimately does not apply to this apparatus (ref may be null). Both the datasheet and the CxAlloy obligation carry one.

## Component 2 — The ledger table `ops.revenue_recognition_event`

Single immutable, append-only table; both recognition and corrections are signed rows.

| column | type | null | notes |
|---|---|---|---|
| `id` | uuid | NO | PK, `DEFAULT gen_random_uuid()` |
| `apparatus_id` | uuid | NO | `REFERENCES ops.apparatus(id)` |
| `scope_id` | uuid | NO | `REFERENCES ops.scopes(id)` (denormalized at write, for rollups) |
| `project_id` | uuid | NO | `REFERENCES ops.projects(id)` (denormalized) |
| `event_type` | `ops.recognition_event_type` | NO | `recognized` \| `reversal` |
| `recognized_amount` | numeric | NO | **signed**: `> 0` on recognized, `< 0` on reversal; mirrors `apparatus.quoted_revenue` exactly (unscaled, no rounding of the frozen basis) |
| `quoted_hours` | numeric | YES | basis snapshot; **required `> 0` on `recognized`** (CHECK) |
| `blended_rate` | numeric | YES | basis snapshot (from `scope_quote.blended_rate`); **required on `recognized`** (CHECK) |
| `basis_frozen_at` | timestamptz | YES | the `scope_quote.frozen_at` basis; **required on `recognized`** (CHECK) |
| `assessment` | `ops.apparatus_assessment` | YES | stamped for audit, **non-gating** |
| `actor_person_id` | uuid | NO | `REFERENCES ops.persons(person_id)` — approver on `recognized`, reverser on `reversal` |
| `datasheet_clearance` | `ops.obligation_clearance` | YES | required on `recognized` (see CHECK) |
| `datasheet_ref` | text | YES | soft ref → `records.form_submissions` (no cross-DB FK) |
| `cx_clearance` | `ops.obligation_clearance` | YES | required on `recognized` |
| `cx_ref` | text | YES | CxAlloy/Cx reference |
| `reverses_event_id` | uuid | YES | `REFERENCES ops.revenue_recognition_event(id)`; set on `reversal` |
| `reason` | text | YES | required (non-blank) on `reversal` |
| `recognized_at` | timestamptz | NO | `DEFAULT now()` |
| `created_at` | timestamptz | NO | `DEFAULT now()` |

### Constraints

- **`ck_event_shape`** (CASE by `event_type`):
  - `recognized` ⇒ `recognized_amount > 0` AND `reverses_event_id IS NULL` AND `datasheet_clearance IS NOT NULL` AND `cx_clearance IS NOT NULL` AND `quoted_hours > 0` AND `blended_rate IS NOT NULL` AND `basis_frozen_at IS NOT NULL`
  - `reversal` ⇒ `recognized_amount < 0` AND `reverses_event_id IS NOT NULL` AND `reason IS NOT NULL AND btrim(reason) <> ''`
- **`ck_datasheet_ref`**: `datasheet_clearance IS DISTINCT FROM 'provided' OR (datasheet_ref IS NOT NULL AND btrim(datasheet_ref) <> '')`
- **`ck_cx_ref`**: `cx_clearance IS DISTINCT FROM 'provided' OR (cx_ref IS NOT NULL AND btrim(cx_ref) <> '')`

(On `reversal` rows the clearances are NULL → both ref checks pass vacuously.)

### Append-only enforcement

```sql
CREATE FUNCTION ops.trg_revrec_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ops.revenue_recognition_event is append-only (% blocked)', TG_OP;
END $$;
CREATE TRIGGER revrec_immutable BEFORE UPDATE OR DELETE ON ops.revenue_recognition_event
  FOR EACH ROW EXECUTE FUNCTION ops.trg_revrec_immutable();
```

### Write integrity (BEFORE INSERT)

Because we chose triggers over role-based function-only grants, a direct `INSERT` outside `approve_and_recognize` must not be able to persist a row the function would have refused. A `BEFORE INSERT` trigger enforces the full invariant set regardless of write path:
- **Lineage (all rows):** `NEW.scope_id` must equal `ops.apparatus(NEW.apparatus_id).scope_id`, and `NEW.project_id` must equal `ops.scopes(NEW.scope_id).project_id` — else raise.
- **`recognized` rows additionally require:** the active chain (apparatus + scope + project `is_active` and non-`Cancelled`); `apparatus.status = 'Complete'`; a frozen basis (`scope_quote.is_frozen` AND `frozen_at IS NOT NULL`); `recognized_amount = apparatus.quoted_revenue`; and the snapshot fields matching the current basis (`quoted_hours = apparatus.quoted_hours`, `blended_rate = scope_quote.blended_rate`, `basis_frozen_at = scope_quote.frozen_at`) — else raise.
- **`reversal` rows require:** `reverses_event_id` references an existing `recognized` event whose `apparatus_id` equals `NEW.apparatus_id`, AND `recognized_amount = -(original.recognized_amount)` — else raise.

So the function path and any direct-insert path converge on identical invariants; the function adds only friendly error messages and the locked idempotency check. (Idempotency — no second *open* recognition per apparatus — remains the function's responsibility via the `FOR UPDATE` net-check, which a stateless insert trigger cannot serialize.)

### Indexes

- `idx_revrec_apparatus` on `(apparatus_id)` — net-sum lookups.
- `idx_revrec_scope` on `(scope_id)`, `idx_revrec_project` on `(project_id)` — rollups.
- **`uq_revrec_one_reversal`** UNIQUE on `(reverses_event_id) WHERE event_type = 'reversal'` — at most one reversal per recognized event.

**Net recognized per apparatus** = `Σ recognized_amount`. `is_recognized` = `net > 0`. A reversal brings net to 0, after which re-recognition is legal (re-completed apparatus). A simple unique index on recognized rows is therefore intentionally NOT used (it would forbid legal re-recognition); recognition idempotency rides the row lock + net-check below.

## Component 3 — Gated primitives

### `ops.approve_and_recognize(...) → uuid`

Signature:
```
ops.approve_and_recognize(
  p_apparatus_id        uuid,
  p_actor_person_id     uuid,
  p_datasheet_clearance ops.obligation_clearance,
  p_datasheet_ref       text,
  p_cx_clearance        ops.obligation_clearance,
  p_cx_ref              text
) RETURNS uuid
```
Behavior (PL/pgSQL, single transaction):
1. Lock + fetch the apparatus joined to its scope and project:
   `SELECT a.scope_id, a.status, a.is_active, a.quoted_hours, a.quoted_revenue, a.assessment, s.project_id, s.is_active AS scope_active, s.status AS scope_status, p.is_active AS project_active, p.status AS project_status INTO … FROM ops.apparatus a JOIN ops.scopes s ON s.id = a.scope_id JOIN ops.projects p ON p.id = s.project_id WHERE a.id = p_apparatus_id FOR UPDATE OF a`. Not found → raise. *(The apparatus row lock serializes concurrent approvals — race guard.)*
2. `status <> 'Complete'` → raise (`apparatus not testing-complete`).
3. **Active-row gate:** require `a.is_active AND scope_active AND project_active AND scope_status <> 'Cancelled' AND project_status <> 'Cancelled'`; else raise (`inactive/cancelled object cannot recognize`).
4. Basis gate: fetch `ops.scope_quote` for the scope; require `is_frozen = true` AND `frozen_at IS NOT NULL`; else raise.
5. Require `quoted_hours > 0` AND `quoted_revenue IS NOT NULL AND quoted_revenue > 0`; else raise (`invalid quote basis`).
6. Require `p_datasheet_clearance IS NOT NULL` AND `p_cx_clearance IS NOT NULL`; else raise (`both clearances required`). (`provided`⇒ref enforced by table CHECK; surface a clear message here too.)
7. Idempotency: `SELECT COALESCE(SUM(recognized_amount),0) FROM ops.revenue_recognition_event WHERE apparatus_id = p_apparatus_id`; if `> 0` → raise (`already recognized`).
8. INSERT one `recognized` row (`project_id` already resolved from the step-1 join): `recognized_amount = quoted_revenue`; snapshot `quoted_hours`, `blended_rate`, `basis_frozen_at = scope_quote.frozen_at`, `assessment`; `actor_person_id = p_actor_person_id`; the two clearances + refs. RETURN its `id`.

### `ops.reverse_recognition(p_event_id uuid, p_actor_person_id uuid, p_reason text) → uuid`

1. `p_reason` blank → raise.
2. `SELECT … FROM ops.revenue_recognition_event WHERE id = p_event_id FOR UPDATE`. Not found → raise; `event_type <> 'recognized'` → raise (`can only reverse a recognized event`).
3. Lock the apparatus row (`SELECT 1 FROM ops.apparatus WHERE id = <apparatus_id> FOR UPDATE`) to coordinate with `approve_and_recognize`.
4. Already reversed (`EXISTS reversal WHERE reverses_event_id = p_event_id`) → raise. *(Belt-and-suspenders to `uq_revrec_one_reversal`.)*
5. INSERT a `reversal` row: `recognized_amount = -original.recognized_amount`, `reverses_event_id = p_event_id`, `reason`, `actor_person_id`, copying `apparatus_id/scope_id/project_id`. RETURN its `id`.

## Component 4 — Recognition-protection guards

Open recognized revenue must not be silently hidden by a lifecycle transition (the rollups/queue exclude inactive/cancelled rows, so dropping a parent would make recognized $ vanish from view). `BEFORE UPDATE` guards at all three grains raise when a transition would orphan or hide an open recognition; the fix is always **reverse first**. "Open recognition in the subtree" = `EXISTS` an apparatus under the row with net recognized `> 0`.

- **`ops.apparatus`** — raise if the row's net recognized `> 0` AND the update would either move it out of `Complete` (`OLD.status='Complete' AND NEW.status<>'Complete'` — this covers `→ Cancelled`) or deactivate it (`OLD.is_active AND NOT NEW.is_active`).
- **`ops.scopes`** — raise if the update would deactivate (`OLD.is_active AND NOT NEW.is_active`) or cancel (`NEW.status='Cancelled' AND OLD.status<>'Cancelled'`) a scope that has any apparatus with net recognized `> 0`.
- **`ops.projects`** — raise if the update would deactivate or cancel a project that has any apparatus (via its scopes) with net recognized `> 0`.

Only these recognition-hiding transitions are blocked; every other edit is untouched. (Softer `v_recognition_anomalies` view deferred unless useful later.)

## Component 5 — Basis-immutability guard (completes the Chip 2 freeze)

Recognition snapshots the basis on the event, but the rollup views still compare against the *current* `apparatus.quoted_revenue` / `scope_quote.adjusted_total`. Chip 2 froze the quote conceptually (`is_frozen`/`frozen_at`) but left the columns mutable, so a post-recognition quote edit could silently break the revenue identity. Chip 3 closes this with two `BEFORE UPDATE` guard triggers:

- **`ops.scope_quote`** — when `OLD.is_frozen = true`, block changes to the financial inputs (`onsite_labor`, `offsite_labor`, `travel`, `outside_services`, `unit_multiplier`, `pct_adjust`, `total_quoted_hours`) and to `is_frozen`/`frozen_at` themselves → raise (`frozen quote basis is immutable`). The generated columns (`adjusted_total`, `blended_rate`) follow automatically and need no rule.
- **`ops.apparatus`** — when the row's scope quote `is_frozen = true`, block changes to `quoted_hours`, `quoted_revenue`, `quote_line_id` → raise.
- **`ops.scope_quote_line`** — hours-affecting line edits after freeze are blocked *transitively*: the Chip 2 J3 roll-up trigger recomputes `scope_quote.total_quoted_hours`, which the frozen-`scope_quote` guard above then rejects (a test asserts this path). A non-hours field edit on a line is not a basis change and is harmless.

This makes the snapshot and the live values provably equal post-freeze, so the views' ceiling/residual stay correct. Freezing itself (draft → frozen) remains allowed; only edits *after* freeze are blocked. (Un-freezing, if ever needed, becomes a deliberate future controlled action — out of scope here.)

## Component 6 — Views

- **`ops.v_recognition_review_queue`** — `apparatus WHERE status = 'Complete'` AND `is_active` AND its scope+project are active and not `Cancelled` AND net recognized `<= 0`. The lead's queue (what the future UI renders). Columns: apparatus id/designation, scope_id, project_id, quoted_revenue, quoted_hours, date_due, assessment.
- **`ops.v_apparatus_recognition`** — per apparatus: net_recognized, is_recognized, the open recognized event (id, actor, recognized_at, both clearances + refs, basis), status, quoted_revenue.
- **`ops.v_scope_recognition`** — per **active, non-cancelled** scope: `recognized_total` (Σ events), `apparatus_ceiling` (Σ `apparatus.quoted_revenue` for active apparatus in scope), `scope_adjusted_total` (`scope_quote.adjusted_total` = P4), **`residual = scope_adjusted_total - apparatus_ceiling`**, `pct_of_ceiling`, `pct_of_scope`. Surfaces the scope-grain residual explicitly.
- **`ops.v_project_recognition`** — per **active, non-cancelled** project rollup of the above (Σ recognized, Σ ceiling, Σ adjusted_total, residual, pct).

## Scope-residual treatment (boundary, not a fix)

Apparatus-grain `quoted_revenue` sums to **$4,503,706.81**, while the project/scope quote is **$4,692,078.98** — a ~$188k residual that lives at *scope* grain (the 2 Mod-Chiller estimate scopes + non-apparatus-mapped categories). Chip 3 **surfaces** this residual in `v_scope_recognition` / `v_project_recognition` (`residual`, and `pct_of_ceiling` vs `pct_of_scope`). It does NOT allocate or "fix" it. Recognition can never exceed the apparatus-grain ceiling. Whether to push the residual down to apparatus rows is a **Chip 2 data decision**, out of scope here.

## Testing (TDD, `ops_test`)

Run with `uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_005_recognition_ledger.py` (pin `OPS_DEV_DSN`/`OPS_DEV_PGPASSWORD` at `ops_test`, NOT `ops_dev`). Each test seeds a minimal fixture (project → scope → frozen scope_quote → apparatus → person). Cases:

1. **recognize happy path** — Complete apparatus + frozen quote + both clearances → event; `net == quoted_revenue`; basis snapshot populated.
2. **requires Complete** — `status != 'Complete'` → raises.
3. **assessment-independent** — `assessment = 'Fail'` still recognizes.
4. **requires frozen basis** — `is_frozen = false` or `frozen_at NULL` → raises.
5. **requires valid quote** — `quoted_revenue` NULL/0 → raises.
6. **requires both clearances** — NULL clearance → raises.
7. **clearance/ref coherence** — `provided` + blank ref → CHECK violation; `not_applicable` + NULL ref → ok.
8. **actor FK** — `actor_person_id` not in `ops.persons` → FK violation.
9. **idempotent recognition** — second recognize on an open recognition → raises.
10. **reversal** — reverse → net 0; then re-recognize allowed.
11. **reversal requires reason** — blank reason → raises.
12. **one reversal per event** — double-reverse the same event → raises (unique index).
13. **ledger append-only** — UPDATE/DELETE on an event row → raises.
14. **firewall** — `apparatus.quoted_*` unchanged after recognition; assert no recognized-$ columns exist on `ops.apparatus` (Law 3).
15. **guard** — `Complete → In Progress` with open recognition → raises; reverse, then change → ok.
16. **scope residual surfaced (synthetic)** — seed a scope whose `scope_quote.adjusted_total` deliberately exceeds Σ apparatus `quoted_revenue` (a synthetic residual fixture on `ops_test` — NOT the real Miner data); assert `v_scope_recognition.residual > 0` and `recognized_total` never exceeds `apparatus_ceiling`.
17. **rollup revenue identity** — recognizing all apparatus in a scope → `recognized_total == apparatus_ceiling` (`< adjusted_total` by the residual).
18. **migration reversibility** — up → down → up clean; `_down` leaves Chips 1/2 + `ops.persons` intact (verify their objects still present).
19. **active-row gate (initial recognition)** — `approve_and_recognize` raises when the apparatus, its scope, or its project is `is_active = false` or `Cancelled`; the review queue excludes such rows.
20. **basis-immutability guard** — after `scope_quote.is_frozen = true`, an UPDATE of a quote financial input (or of `apparatus.quoted_revenue`) raises; the same edit *before* freeze succeeds.
21. **insert integrity (lineage)** — a direct INSERT whose `scope_id`/`project_id` do not match the apparatus lineage raises; a `reversal` whose `reverses_event_id` points at another apparatus's event raises.
22. **recognition-protection guards** — with an open recognition present, each of these raises: apparatus `is_active → false`; apparatus `→ Cancelled`; scope deactivate; scope cancel; project deactivate; project cancel. After reversing the recognition, each transition then succeeds.
23. **insert business invariants** — a direct INSERT of a `recognized` row that violates any invariant raises: non-`Complete` apparatus, unfrozen basis, inactive/cancelled chain, `recognized_amount ≠ apparatus.quoted_revenue`, or any mismatched snapshot field (`quoted_hours`/`blended_rate`/`basis_frozen_at`); and a `reversal` row with `recognized_amount ≠ -(original)` raises.
24. **post-freeze line edit** — an hours-affecting UPDATE of a `scope_quote_line` after `is_frozen = true` raises (via the J3 roll-up hitting the frozen `scope_quote`).

## Files

- `infra/database/migrations/ops/005_recognition_ledger.sql` (create)
- `infra/database/migrations/ops/005_recognition_ledger_down.sql` (create)
- `infra/database/migrations/ops/test_005_recognition_ledger.py` (create)
- `infra/database/migrations/ops/MANIFEST.md` (modify — add row 005 / Chip 3; remove the recognition ledger from "Deferred")
- `reference/ops/00-MASTER-INDEX.md` (modify — record the **substrate-fork D-OPS decision** [Chip 3 on clean `ops.*`, durable preferred] + the Chip 3 recognition rules: gated by `Complete`, lead-approval gate, clearance model, hard person FK, firewall)

## Out of scope / deferred (later packets)

- Lead-review **UI** (deployed `/pm-review` surface).
- **records** datasheet live-verification (auto-set `datasheet_clearance`/`datasheet_ref` from `records.form_submissions`).
- **CxAlloy/Cx** submission integration (auto-set `cx_clearance`/`cx_ref`).
- `actor_auth_user_id` (login traceability) — soft add if/when needed.
- Scope-residual **data fix** (push residual into apparatus `quoted_revenue`) — a Chip 2 decision.
- Progress **billing** (Chip 4); `public`/`seam`/`schedule` → `ops` **convergence** (Chip N); **prod** application.
