# Ops Chip 3 — Recognition Ledger Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (or executing-plans) to implement the plan derived from this spec, task-by-task.

**Goal:** Add an append-only, apparatus-grain revenue-recognition ledger to the clean `ops.*` substrate so that a tech-lead's *approval* of a completed apparatus produces a durable recognized-revenue event, honoring the recognition firewall (frozen `quoted_*` stays on the apparatus; recognized $ exist only as events).

**Architecture:** One numbered SQL migration on the existing lane rails — `infra/database/migrations/ops/005_recognition_ledger.sql` (+ `_down` + `test_005_recognition_ledger.py`), TDD on a throwaway `ops_test`. It adds: two enums, one append-only ledger table, two gated PL/pgSQL functions, four rollup/queue views, one narrow integrity guard, and supporting constraints/indexes. No new package, no app, no prod. The lead-review UI, the records datasheet live-verification, and the CxAlloy integration are explicitly **later bridge packets** — Chip 3 is the engine they will call.

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
| `quoted_hours` | numeric | YES | basis snapshot at recognition |
| `blended_rate` | numeric | YES | basis snapshot (from `scope_quote.blended_rate`) |
| `basis_frozen_at` | timestamptz | YES | the `scope_quote.frozen_at` the recognition was based on |
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
  - `recognized` ⇒ `recognized_amount > 0` AND `reverses_event_id IS NULL` AND `datasheet_clearance IS NOT NULL` AND `cx_clearance IS NOT NULL`
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
1. `SELECT scope_id, status, quoted_hours, quoted_revenue, assessment INTO … FROM ops.apparatus WHERE id = p_apparatus_id FOR UPDATE`. Not found → raise. *(The row lock serializes concurrent approvals — race guard.)*
2. `status <> 'Complete'` → raise (`apparatus not testing-complete`).
3. Basis gate: fetch `ops.scope_quote` for the scope; require `is_frozen = true` AND `frozen_at IS NOT NULL`; else raise.
4. Require `quoted_hours > 0` AND `quoted_revenue IS NOT NULL AND quoted_revenue > 0`; else raise (`invalid quote basis`).
5. Require `p_datasheet_clearance IS NOT NULL` AND `p_cx_clearance IS NOT NULL`; else raise (`both clearances required`). (`provided`⇒ref enforced by table CHECK; surface a clear message here too.)
6. Idempotency: `SELECT COALESCE(SUM(recognized_amount),0) FROM ops.revenue_recognition_event WHERE apparatus_id = p_apparatus_id`; if `> 0` → raise (`already recognized`).
7. Resolve `project_id` from `ops.scopes`.
8. INSERT one `recognized` row: `recognized_amount = quoted_revenue`; snapshot `quoted_hours`, `blended_rate`, `basis_frozen_at = scope_quote.frozen_at`, `assessment`; `actor_person_id = p_actor_person_id`; the two clearances + refs. RETURN its `id`.

### `ops.reverse_recognition(p_event_id uuid, p_actor_person_id uuid, p_reason text) → uuid`

1. `p_reason` blank → raise.
2. `SELECT … FROM ops.revenue_recognition_event WHERE id = p_event_id FOR UPDATE`. Not found → raise; `event_type <> 'recognized'` → raise (`can only reverse a recognized event`).
3. Lock the apparatus row (`SELECT 1 FROM ops.apparatus WHERE id = <apparatus_id> FOR UPDATE`) to coordinate with `approve_and_recognize`.
4. Already reversed (`EXISTS reversal WHERE reverses_event_id = p_event_id`) → raise. *(Belt-and-suspenders to `uq_revrec_one_reversal`.)*
5. INSERT a `reversal` row: `recognized_amount = -original.recognized_amount`, `reverses_event_id = p_event_id`, `reason`, `actor_person_id`, copying `apparatus_id/scope_id/project_id`. RETURN its `id`.

## Component 4 — Integrity guard (narrow)

```sql
CREATE TRIGGER apparatus_block_uncomplete BEFORE UPDATE OF status ON ops.apparatus …
```
Behavior: if `OLD.status = 'Complete'` AND `NEW.status <> 'Complete'` AND net recognized for the row `> 0` → raise (`reverse recognition before un-completing`). Only this narrow transition is blocked; everything else is untouched. (Softer `v_recognition_anomalies` view deferred unless useful later.)

## Component 5 — Views

- **`ops.v_recognition_review_queue`** — `apparatus WHERE status = 'Complete'` AND net recognized `<= 0`. The lead's queue (what the future UI renders). Columns: apparatus id/designation, scope_id, project_id, quoted_revenue, quoted_hours, date_due, assessment.
- **`ops.v_apparatus_recognition`** — per apparatus: net_recognized, is_recognized, the open recognized event (id, actor, recognized_at, both clearances + refs, basis), status, quoted_revenue.
- **`ops.v_scope_recognition`** — per scope: `recognized_total` (Σ events), `apparatus_ceiling` (Σ `apparatus.quoted_revenue` in scope), `scope_adjusted_total` (`scope_quote.adjusted_total` = P4), **`residual = scope_adjusted_total - apparatus_ceiling`**, `pct_of_ceiling`, `pct_of_scope`. Surfaces the scope-grain residual explicitly.
- **`ops.v_project_recognition`** — per project rollup of the above (Σ recognized, Σ ceiling, Σ adjusted_total, residual, pct).

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
16. **scope residual surfaced** — `v_scope_recognition.residual = adjusted_total - apparatus_ceiling > 0` for a Miner MV scope; `recognized_total` never exceeds `apparatus_ceiling`.
17. **rollup revenue identity** — recognizing all apparatus in a scope → `recognized_total == apparatus_ceiling` (`< adjusted_total` by the residual).
18. **migration reversibility** — up → down → up clean; `_down` leaves Chips 1/2 + `ops.persons` intact (verify their objects still present).

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
