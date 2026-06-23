# Ops Recognition Bridge — Slice 1: Completion Attestation → Recognize

**Date:** 2026-06-23
**Lane:** `ops/recognition-bridge` (host worktree `~/code/apex/apex-ops-recognition`, off `main @ 1c07d7ca`)
**Status:** DESIGN — round-3 (post-IRP). Operator ratified D1–D4 + the predicate-transition guard 2026-06-23; pending final operator glance before `writing-plans`.
**Migration:** ops `009`.
**Review trail:** R1/R2 operator audits + the Deep IRP (`docs/review/IRP_RECOGNITION_BRIDGE_SPEC_2026-06-23.md`, 3 engines).

---

## 0. Resume pointer
First slice of the `/pm-review` app-bridge: make the built Chip-3 recognition engine reachable + live through the PM UI by introducing a **governed completion-for-recognition attestation** as the explicit, audited source of "Complete." Recognition only. Dev-only on `ops_dev`; **no prod DDL**. Layers behind one migration: `009` (DB authority) → `packages/ops-intake` wrappers (seam) → `recognition_router.py` (host-gated API) → `/pm-review/recognition` (UI).

## 1. Goal & value
The Chip-3 recognition ledger (mig `005`) and Chip-4 billing (mig `006`) are durable on `ops.*` but **inert**: nothing drives `ops.apparatus.status → 'Complete'`, so `approve_and_recognize` can never fire and recognized revenue stays 0. This slice supplies the missing completion authority — an honest, bounded **PM attestation** (not production tracking) — and surfaces attest → recognize → reverse → revoke → rollups through the PM UI. It turns a built-but-dark engine into demonstrable value on the live $4.69M Miner dataset.

## 2. Scope & boundaries (non-negotiable)
**In:** attest completion, recognize, reverse recognition, revoke attestation, read worklist/rollup.
**Out (hard):** **no billing** (no Chip-4 issue/draft/promotion/void path); no quantity/labor/production metrics; no customer-facing production status; **not** the records-datasheet production-tracking authority (a *future* completion source that supersedes this via a new `provenance` value — §10).

## 3. Grounding (verified live on the host, 2026-06-23 + IRP)
- `ops.apparatus.status` enum `ops.apparatus_status` = {Not Started, In Progress, Pending Review, Complete, Cancelled}, default `Not Started`. **No migration writes `'Complete'` today** — the gap this slice fills.
- **Eligibility key = `provenance_status='approved'`, NOT `source` (CRITICAL/D1, live-grounded).** All 5,344 live Miner apparatus are `provenance_status='approved'`, `is_active`, frozen-basis, `quoted_revenue>0`, but `source='miner_rev10.xlsm'` (intentionally foreign / no-backfill). The go-forward intake also stamps `provenance_status='approved'`. So `source='ops-intake'` would match **0** Miner rows; `provenance_status='approved'` matches all live + future. `provenance_status` and `source` are both mutable `text` on `ops.apparatus` (001) → the guard (§5.7) defends the *state*, not the column.
- `ops.approve_and_recognize(p_apparatus_id uuid, p_actor_person_id uuid, p_datasheet_clearance ops.obligation_clearance, p_datasheet_ref text, p_cx_clearance ops.obligation_clearance, p_cx_ref text) returns uuid`. Gates: found; `status='Complete'`; active+non-cancelled chain; `scope_quote.is_frozen`+`frozen_at`; `quoted_hours/quoted_revenue`>0; both clearances NOT NULL; net recognition=0. `SELECT ... FOR UPDATE of apparatus`.
- `ops.obligation_clearance` enum values = **`('provided','not_applicable')`** (005:8).
- `ops.reverse_recognition(p_event_id uuid, p_actor_person_id uuid, p_reason text) returns uuid` — reason required; locks event then apparatus FOR UPDATE; rejects double-reverse; inserts `'reversal'` (recognized_amount=-orig) **without naming `completion_attestation_id`** (relies on the new column's NULL default — coupling, §5.6).
- Existing `BEFORE UPDATE ON ops.apparatus`: `apparatus_protect_recognition` (raises on `Complete→non-Complete` OR `is_active→false` while net>0) and `apparatus_freeze_guard` (locks `quoted_*`/`quote_line_id` when frozen; **does not touch `status`/`provenance_status`/`source`**). The ledger is append-only via `revrec_immutable` (blocks UPDATE/DELETE on `revenue_recognition_event`).
- `005_recognition_ledger_down.sql` **DROPs** `approve_and_recognize` + `trg_revrec_insert_integrity` (there is no reusable "005 body" to restore — §5.9).
- Views: `v_recognition_review_queue` (Complete+unrecognized only); `v_apparatus_recognition` (status, net_recognized, is_recognized, recognized_event_id — `recognized_event_id` goes NULL once an event is reversed). `v_scope_recognition`/`v_project_recognition` carry ids, not `project_number`.
- `ops.persons(person_id)` = actor anchor (mig `004`).

## 4. Architecture
A new **host-gated `ops_dev` router** (sibling to `intake_router.py`), registered only when `OPS_DEV_DSN` is set, **distinct** from the prod/public derive-on-read `GET /api/v1/ops/revenue-recognition`. All state changes flow through `009` DB functions (sole-writer discipline).

---

## 5. Migration `009` — completion authority + recognition trace

### 5.1 Table `ops.completion_attestation` + immutability guard
```sql
create table ops.completion_attestation (
  id            uuid primary key default gen_random_uuid(),          -- API addresses it: /completion/{id}/revoke
  apparatus_id  uuid not null references ops.apparatus(id),
  attested_by   uuid not null references ops.persons(person_id),
  reason        text not null check (btrim(reason) <> ''),
  provenance    text not null default 'pm_recognition_attestation'
                  check (provenance in ('pm_recognition_attestation')),  -- extends to 'production_tracking' (§10)
  prior_status  ops.apparatus_status not null,                       -- captured at attest; restored on revoke
  attested_at   timestamptz not null default now(),
  revoked_at    timestamptz,
  revoked_by    uuid references ops.persons(person_id),
  revoke_reason text
);
create unique index uq_completion_attestation_active
  on ops.completion_attestation (apparatus_id) where revoked_at is null;  -- one ACTIVE attestation per apparatus
comment on table ops.completion_attestation is
  'Governed PM attestation that an apparatus is testing-complete FOR RECOGNITION. NOT production truth, NOT customer-facing. Sole sanctioned writer of ops.apparatus.status=Complete for approved apparatus. A future production-tracking authority supersedes via provenance=production_tracking.';
```
**Immutability (IRP-B2 — mandatory: this row is the ledger's completion proof).**
```sql
create function ops.trg_completion_attestation_immutable() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' then raise exception 'ops.completion_attestation is append-only (DELETE blocked)'; end if;
  if new.id is distinct from old.id or new.apparatus_id is distinct from old.apparatus_id
     or new.attested_by is distinct from old.attested_by or new.reason is distinct from old.reason
     or new.provenance is distinct from old.provenance or new.prior_status is distinct from old.prior_status
     or new.attested_at is distinct from old.attested_at then
    raise exception 'ops.completion_attestation core fields are immutable (id %)', old.id;
  end if;
  if old.revoked_at is not null then raise exception 'ops.completion_attestation % already revoked', old.id; end if;
  return new;  -- only the single NULL->value revoke transition (revoked_at/by/reason) is permitted
end; $$;
create trigger completion_attestation_immutable before update or delete on ops.completion_attestation
  for each row execute function ops.trg_completion_attestation_immutable();
```

### 5.2 Recognition-event trace column (sub-decision a)
```sql
alter table ops.revenue_recognition_event
  add column completion_attestation_id uuid references ops.completion_attestation(id);
```
Populated by `approve_and_recognize` from the apparatus's active attestation; **required on `recognized` rows**, NULL on `reversal` rows (enforced §5.6).
**Invariant precision (IRP-B5):** the trace is **active-at-write** — it records the attestation active *when the recognized row was inserted*, and stays historically valid even after that attestation is later revoked via the sanctioned reverse→revoke cycle. It is NOT a claim the attestation is *still* active.

### 5.3 Function `ops.attest_apparatus_complete(p_apparatus_id uuid, p_attested_by uuid, p_reason text) returns uuid`
1. Reason not blank; `p_attested_by` in `ops.persons` (else clean error → API 400).
2. Load apparatus `FOR UPDATE` joined scope/project; verify: found; **`provenance_status='approved'` (D1)**; `is_active` + active non-cancelled scope/project chain; `status NOT IN ('Complete','Cancelled')`; `scope_quote.is_frozen` + `frozen_at NOT NULL`; `quoted_hours>0` and `quoted_revenue>0` (positive basis — same gate `approve_and_recognize` enforces).
3. Capture `prior_status := apparatus.status`.
4. `perform set_config('ops.completion_ctx','1', true);` (txn-local — opens the §5.7 **misuse** guard; not the security boundary, §5.11).
5. `update ops.apparatus set status='Complete', updated_at=now() where id=p_apparatus_id;`
6. Insert the attestation (provenance default, `prior_status`); the partial-unique index makes a second active attestation a unique violation → API 409.
7. Return attestation id.

### 5.4 Function `ops.revoke_completion_attestation(p_attestation_id uuid, p_revoked_by uuid, p_reason text) returns uuid`
1. Reason not blank; actor in `ops.persons`.
2. Load the **active** attestation (`revoked_at is null`) by id `FOR UPDATE`; not found → error.
3. **Lock the apparatus (IRP-M1):** `perform 1 from ops.apparatus where id = <attestation.apparatus_id> for update;` BEFORE the net-gate — makes the net read deterministic, closes the revoke/recognize TOCTOU + the `prior_status` clobber, and pins the lane lock order "apparatus before ledger rows" (D-OPS-12). Revoke must NOT row-lock `revenue_recognition_event` rows.
4. **Net-recognition gate:** if `sum(recognized_amount) for apparatus > 0` → raise `'apparatus has open recognition; reverse first'`. (`apparatus_protect_recognition` is the hard backstop; intake re-approval stays stricter on any history — `approve.py:140` — unchanged.)
5. `perform set_config('ops.completion_ctx','1', true);`
6. `update ops.apparatus set status=(attestation.prior_status), updated_at=now() where id=attestation.apparatus_id;`
7. `update ops.completion_attestation set revoked_at=now(), revoked_by=p_revoked_by, revoke_reason=p_reason where id=p_attestation_id;` (the §5.1 immutability trigger permits exactly this transition).
8. Return attestation id.

### 5.5 Modify `ops.approve_and_recognize` (the one Chip-3 touch)
After the existing gates (all unchanged), resolve the active attestation:
```sql
select id into v_att from ops.completion_attestation where apparatus_id = p_apparatus_id and revoked_at is null;
if not found then raise exception 'apparatus % has no active completion attestation', p_apparatus_id; end if;
```
Add `completion_attestation_id => v_att` to the `recognized`-event insert. All other behavior identical.
**Note:** as written the function stays **INVOKER**; under the §5.11 role boundary it (and `attest`/`revoke`) become **SECURITY DEFINER** with `search_path = ops, pg_temp`.

### 5.6 Modify `ops.trg_revrec_insert_integrity` (firewall touch — **FOCUSED REVIEW**)
- On `event_type='recognized'`: in addition to all existing checks, require `new.completion_attestation_id IS NOT NULL` referencing an attestation with `revoked_at IS NULL` and `apparatus_id = new.apparatus_id`; else raise.
- On `event_type='reversal'`: require `new.completion_attestation_id IS NULL`.
**Coupling note:** `reverse_recognition` (unmodified by 009) omits the column from its insert list, relying on the new column's NULL default to satisfy the reversal arm. Correct today, fragile — a future non-null default would break every reversal. Documented so it is not silently changed.

### 5.7 Completion guard — predicate-transition aware (IRP-B1 + D1 + operator tweak — REQUIRED)
Protects the **governed-complete state** `g := (status='Complete' AND provenance_status='approved')`. It must fire whenever a row *enters or leaves* `g` — by ANY field change, on INSERT or UPDATE — without the function context. (A status-only guard is bypassable via `INSERT status='Complete', provenance_status='draft'` then `UPDATE provenance_status='approved'`.)
```sql
create function ops.trg_apparatus_completion_guard() returns trigger language plpgsql as $$
declare
  new_g boolean := (new.status='Complete' and new.provenance_status='approved');
  old_g boolean;
begin
  if tg_op = 'INSERT' then
    if new_g and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may be entered only via attest', new.id;
    end if;
  else  -- UPDATE
    old_g := (old.status='Complete' and old.provenance_status='approved');
    if (new_g is distinct from old_g) and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may change only via attest/revoke', new.id;
    end if;
  end if;
  return new;
end; $$;
create trigger apparatus_completion_guard before insert or update on ops.apparatus
  for each row execute function ops.trg_apparatus_completion_guard();
```
Closes the direct-INSERT-as-Complete bypass AND the draft-Complete→flip-provenance bypass. Normal intake INSERT (`status='Not Started'`, `provenance_status='approved'`) is not `g` → allowed; `attest`/`revoke` set ctx → allowed. **This + the GUC are a defense-in-depth *misuse* guard, not a security boundary (§5.11); the role boundary must also `REVOKE INSERT`.**

### 5.8 Read models — worklist + rollup
**`ops.v_completion_recognition_worklist`** — per **eligible** apparatus (`provenance_status='approved'` (D1), `is_active`, active non-cancelled scope/project, `scope_quote.is_frozen`):
- `apparatus_id, apparatus_designation, scope_id, project_id, project_number, status, quoted_hours, quoted_revenue`
- active attestation (LEFT JOIN where `revoked_at is null`): `attestation_id, attested_by, attested_at, attest_reason`
- from `v_apparatus_recognition`: `net_recognized, is_recognized, recognized_event_id`
- flags: `can_attest` (status NOT IN Complete/Cancelled AND no active attestation AND `quoted_hours>0` AND `quoted_revenue>0`), `can_recognize` (`status='Complete'` AND active attestation AND positive basis AND NOT `is_recognized`), `can_revoke` (active attestation AND NOT `is_recognized`), `can_reverse` (`is_recognized`).
**Post-reversal state (IRP-B5):** flags compute from live state, so each cycle stage reads coherently — after `reverse_recognition`, `is_recognized=false` and `recognized_event_id=NULL`; an apparatus still holding an active attestation then shows `can_recognize` (re-recognize) + `can_revoke`; after `revoke`, no active attestation + `status=prior_status` → `can_attest`. (§5.10 tests the full cycle.)

**`ops.v_completion_recognition_rollup`** (IRP-M2 — the `/rollup` source, previously undefined): per `(project_number, scope_id, project_id)`, `sum(net_recognized)` as recognized $, count of recognized apparatus, count of eligible apparatus — built on `v_apparatus_recognition` joined to `ops.scopes` + `ops.projects` (the latter for `project_number`, which `v_scope_recognition`/`v_project_recognition` lack).

### 5.9 Down migration (IRP-B4 — verbatim, not "restore")
`005_recognition_ledger_down.sql` **DROPs** `approve_and_recognize` + `trg_revrec_insert_integrity`; there is no body to "restore." The 009 down must `create or replace` BOTH back to their **verbatim 005 UP definitions, embedded in the down script**, preserving the review-fixed `is distinct from` null-safety and the `for update of a2` serialization. Order: drop `v_completion_recognition_rollup` + `v_completion_recognition_worklist`; drop `apparatus_completion_guard` + `completion_attestation_immutable` triggers/fns; `create or replace` the two 005 functions verbatim; drop the `completion_attestation_id` column; drop the revoke fn; drop the attest fn; drop `completion_attestation`. Leaves `001`–`008` + all original `005` objects intact.
**Down test (IRP-B4):** after down, **source-diff** the restored function bodies — `pg_get_functiondef` of `approve_and_recognize` + `trg_revrec_insert_integrity` must equal the `005`-up definitions — NOT merely a happy-path recognize (which cannot catch a transcription regression of the null-safe/serialization guards).

### 5.10 pytest on throwaway `ops_test`
- **mig up/down:** down source-diffs the restored 005 functions (B4); idempotent.
- **attest:** success → `status='Complete'` + attestation + `prior_status` captured; rejects non-`approved` `provenance_status`, inactive/cancelled chain, already-Complete, unfrozen basis, non-positive basis, unknown actor, blank reason; second active attest → conflict (unique).
- **completion guard (B1 + predicate-transition):** direct `update … status='Complete'` (no ctx) **fails** on an approved apparatus; **`insert … status='Complete', provenance_status='approved'`** (no ctx) **fails**; **`insert … status='Complete', provenance_status='draft'` then `update … provenance_status='approved'`** (no ctx) **fails** on the second statement; normal intake-style `insert … status='Not Started', provenance_status='approved'` **succeeds**; attest path (ctx) succeeds.
- **attestation immutability (B2):** UPDATE of any core field fails; DELETE fails; the single revoke transition succeeds; a second revoke (already-revoked) fails.
- **recognize:** populates `completion_attestation_id`; integrity trigger rejects a hand-inserted `recognized` row with NULL / foreign / **revoked** / **cross-apparatus** `completion_attestation_id`; `approve_and_recognize` with no active attestation → rejected (§5.5 branch).
- **firewall regression (B4/M4):** after 009, ALL original 005 `recognized`-integrity checks still raise — lineage, active/non-cancelled, `status='Complete'`, frozen basis, `recognized_amount = quoted_revenue`, basis-snapshot match, open-net idempotency.
- **revoke:** blocked iff net>0 (recognize→revoke fails; reverse→revoke succeeds, restores `prior_status`, marks `revoked_*`); apparatus FOR UPDATE present (M1); unknown actor / blank reason rejected.
- **post-reversal cycle (B5):** attest→recognize(E1→A)→reverse(E1)→revoke(A): assert `is_recognized=false`, `recognized_event_id=NULL`, E1 still carries `completion_attestation_id=A`, the reversal row carries NULL, A is revoked, status restored; worklist flags correct at each step.
- **partial-unique race (M5):** two concurrent attests on one apparatus → exactly one wins (the unique index, not just the sequential status-gate).
- **rollup view (M2):** recognized-$ sums per scope/project resolve `project_number`.

### 5.11 Security boundary vs misuse guards (IRP-B3 + B6)
The §5.7 trigger + the `ops.completion_ctx` GUC are **defense-in-depth misuse guards** — any session with direct write rights can set the same GUC, so they are **not** the security boundary. Two layers:
- **Interim (this dev slice):** host-gating — the `ops_dev` router is reachable only on the mesh host via `OPS_DEV_DSN`, like `intake_router`; the misuse guards + trigger gates prevent in-band mistakes.
- **Target (the real boundary):** a least-privilege `ops_app` role the API/package/tests connect as, with **`REVOKE INSERT, UPDATE (status, source, provenance_status) ON ops.apparatus`** + no direct DML on `ops.completion_attestation` or the recognition ledger; the mutation functions become **`SECURITY DEFINER`** owned by the object owner with **`set search_path = ops, pg_temp`** (NOT `public` — including `public` is a privilege-escalation hole, IRP-B3) + **`REVOKE CREATE ON SCHEMA public FROM PUBLIC`**; tests run **as `ops_app`** and prove a direct `UPDATE … status='Complete'` / `INSERT` raises *permission denied* while the function path succeeds.

**RELEASE GATE (IRP-B6 — hard):** 009 may merge + apply to **`ops_dev`** on the interim posture. 009 (and any `ops.*` recognition path) **MUST NOT reach prod until the `ops_app` role boundary above is applied** — the ctx-guard is forgeable, so the role boundary is a *precondition of prod apply*, not a follow-up. **Scope:** the role boundary is a dedicated lane-wide hardening packet (the whole `ops.*` lane currently has no role boundary on any mutation path); this slice ships dev-only behind the gate.

## 6. Package layer (`packages/ops-intake`)
Reuse the existing `ops.*` sole-writer package. Thin wrappers: `attest_complete(apparatus_id, attested_by, reason)`, `recognize(apparatus_id, actor, datasheet_clearance, datasheet_ref, cx_clearance, cx_ref)`, `reverse(event_id, actor, reason)`, `revoke(attestation_id, actor, reason)`. Map DB exceptions to typed, **value-free** errors.
**Cross-task (M3):** update `tests/test_approve_envelope.py:72` to reach `'Complete'` via `ops.attest_apparatus_complete` (the §5.7 guard would otherwise break the direct status set).

## 7. API — `services/ops/recognition_router.py`
`APIRouter(prefix="/api/v1/ops/recognition")` — path-distinct from prod `/api/v1/ops/revenue-recognition` (`lib/revenue-recognition.ts`). Host-gated (`OPS_DEV_DSN`; registers only when configured); actor-gated `ops.persons`; **value-free** 400/409.
- `POST /api/v1/ops/recognition/completion/attest` `{apparatus_id, attested_by, reason}` → 200 `{attestation_id}` / 400 / 409 (already Complete / active attestation exists)
- `POST /api/v1/ops/recognition/completion/{attestation_id}/revoke` `{revoked_by, reason}` → 200 / 400 / 409 (open recognition → reverse first)
- `POST /api/v1/ops/recognition/events/recognize` `{apparatus_id, recognized_by, datasheet_clearance, datasheet_ref, cx_clearance, cx_ref}` → 200 `{event_id}` / 400 / 409. **`obligation_clearance` (M3):** the route validates `datasheet_clearance`/`cx_clearance` against the enum **`{'provided','not_applicable'}`** and returns a value-free **400** on an out-of-enum value (never a raw PG cast error); tested with an invalid value.
- `POST /api/v1/ops/recognition/events/{event_id}/reverse` `{reversed_by, reason}` → 200 `{reversal_id}` / 400 / 409
- `GET /api/v1/ops/recognition/worklist?project_number=` → `v_completion_recognition_worklist`
- `GET /api/v1/ops/recognition/rollup?project_number=` → `v_completion_recognition_rollup` (recognized $ **shown** — operator-authoritative, consistent with §261)

API tests: actor-400s, the clearance-enum 400, value-free errors, and a host-gating disabled-subprocess test.

## 8. UI — `apps/operations-web/app/pm-review/recognition`
Worklist table from `/recognition/worklist`, grouped by scope; per-row actions gated by the view flags — **Attest** (reason-required modal) on `can_attest`; **Recognize** (clearance inputs, enum-constrained) on `can_recognize`; **Revoke** on `can_revoke`; **Reverse** on `can_reverse`. Recognized-$ rollup panel from `/recognition/rollup`. Copy is **"Attest testing complete — for recognition"** everywhere; **never "production complete."** Route-mocked Playwright smoke (POST bodies + re-render).

## 9. Testing & gates
TDD on throwaway `ops_test`; API self-contained; UI typecheck + smoke. **Merge to main + `ops_dev` apply operator-gated. PROD apply blocked behind the §5.11 RELEASE GATE.** IRP cross-engine pass before merge; the Chip-3 firewall touch (§5.5/5.6) + the down-restore (§5.9) get dedicated focused-review lenses.

## 10. Deferred / forward-compatible
- **Billing slice** (Chip-4 wrap) — next slice, separate.
- **Records-datasheet production-tracking authority** — future completion source; lands as `provenance='production_tracking'` (extend the §5.1 CHECK). **Supersession sequence (D3):** because the partial-unique active index blocks a second active attestation and §5.4 blocks revoke while net>0, replacing a PM attestation with a production-tracking one runs: `reverse_recognition` (if recognized) → revoke the PM attestation → attest with `provenance='production_tracking'` → re-recognize. (Spelled out so "supersedes by policy" does not gloss the reverse-first requirement.)
- **`ops_app` role boundary** — the §5.11 lane-wide hardening packet; a hard prod-apply precondition.
- **Prod application of ops `005`–`009`** — separate, gated; blocked behind the release gate.

## 11. Findings traceability
**R1/R2 (operator audits):** id PK, prior_status, partial-unique, clearances, no-billing (§5.1/§5.3/§2); source-flip→ now subsumed by the governed-state guard (§5.7); GUC reframe + role design (§5.11); positive-basis (§5.3/§5.8); revoked-attestation reject (§5.6/§5.10); API prefix (§7).

**IRP round 3 (Claude + Codex + live grounding):**
| Finding | Sev | Resolved in |
|---|---|---|
| CRITICAL — `source='ops-intake'` matches 0 live Miner rows | crit | §3, §5.3/5.7/5.8 → `provenance_status='approved'` (D1) |
| INSERT + predicate-transition bypass | high | §5.7 (governed-state, INSERT OR UPDATE, TG_OP-aware) + §5.10 |
| attestation-row mutability | high | §5.1 immutability trigger |
| `search_path` `public` escalation | high | §5.11 (`ops, pg_temp` + REVOKE CREATE) |
| down cannot "restore" 005 bodies | high | §5.9 (verbatim embed + source-diff test) |
| post-reversal lineage unanalyzed | high | §5.2 (active-at-write), §5.8, §5.10 |
| security insufficient for revenue path | high | §5.11 RELEASE GATE (B6) + REVOKE INSERT |
| revoke lock-order | med | §5.4 (apparatus FOR UPDATE; D-OPS-12) |
| `/rollup` view undefined | med | §5.8 `v_completion_recognition_rollup` |
| clearance-enum unvalidated | med | §7 (`{provided, not_applicable}` → 400) |
| firewall regression untested | med | §5.10 |
| missing tests (cross-apparatus, no-attestation, race) | med | §5.10 |
| reversal column-default coupling; INVOKER/DEFINER | minor | §5.6, §5.5 |
