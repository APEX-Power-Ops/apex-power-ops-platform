# Ops Recognition Bridge — Slice 1: Completion Attestation → Recognize

**Date:** 2026-06-23
**Lane:** `ops/recognition-bridge` (host worktree `~/code/apex/apex-ops-recognition`, off `main @ 1c07d7ca`)
**Status:** DESIGN — operator-approved-with-tweaks 2026-06-23; pending operator spec review before `writing-plans`.
**Migration:** ops `009`.

---

## 0. Resume pointer
First slice of the `/pm-review` app-bridge: make the built Chip-3 recognition engine reachable + live through the PM UI by introducing a **governed completion-for-recognition attestation** as the explicit, audited source of "Complete." Recognition only. Dev-only on `ops_dev`; **no prod DDL**. Three layers behind one migration: `009` (DB authority) → `packages/ops-intake` wrappers (seam) → `recognition_router.py` (host-gated API) → `/pm-review/recognition` (UI).

## 1. Goal & value
The Chip-3 recognition ledger (mig `005`) and Chip-4 billing (mig `006`) are durable on `ops.*` but **inert**: nothing drives `ops.apparatus.status → 'Complete'`, so `approve_and_recognize` can never fire and recognized revenue stays 0. This slice supplies the missing completion authority — as an honest, bounded **PM attestation** (not production tracking) — and surfaces attest → recognize → reverse → revoke → rollups through the PM UI. It turns a built-but-dark engine into demonstrable value on the live $4.69M Miner dataset.

## 2. Scope & boundaries (non-negotiable)
**In:** attest completion, recognize, reverse recognition, revoke attestation, read rollups/worklist.
**Out (hard):**
- **No billing** — no Chip-4 issue/draft/promotion/void path in this slice.
- No quantity / labor / production metrics.
- No customer-facing production status.
- **Not** the records-datasheet production-tracking authority — that is a *future* completion source that supersedes this via a new `provenance` value; this slice does not build it.

## 3. Grounding (verified live on the host, 2026-06-23)
- `ops.apparatus.status` is enum `ops.apparatus_status` = {`Not Started`,`In Progress`,`Pending Review`,`Complete`,`Cancelled`}, default `Not Started`. **No migration writes `'Complete'` today** — the gap this slice fills.
- `ops.apparatus.source text` exists → the `source='ops-intake'` guard predicate is valid. `is_active`, `equipment_model_ref` confirmed.
- `ops.approve_and_recognize(p_apparatus_id uuid, p_actor_person_id uuid, p_datasheet_clearance ops.obligation_clearance, p_datasheet_ref text, p_cx_clearance ops.obligation_clearance, p_cx_ref text) returns uuid`. Gates: found; `status='Complete'`; active+non-cancelled chain; `scope_quote.is_frozen`+`frozen_at`; `quoted_hours/quoted_revenue` > 0; **both clearances NOT NULL**; net recognition = 0. Inserts the `recognized` event.
- `ops.reverse_recognition(p_event_id uuid, p_actor_person_id uuid, p_reason text) returns uuid` — reason required; idempotent (rejects double-reverse).
- Existing `BEFORE UPDATE ON ops.apparatus`: `apparatus_protect_recognition` (raises if `Complete→non-Complete` OR `is_active→false` while net recognition > 0 — the "reverse first" backstop, finding #4) and `apparatus_freeze_guard` (locks `quoted_*`/`quote_line_id` when scope frozen; **does not touch `status`** → my completion guard composes cleanly).
- Views: `v_recognition_review_queue` (Complete + unrecognized only — insufficient for the UI); `v_apparatus_recognition` (per-apparatus `status`, `net_recognized`, `is_recognized`, `recognized_event_id`) — build the worklist on this.
- `ops.persons(person_id)` = the actor anchor (mig `004`).

## 4. Architecture
A new **host-gated `ops_dev` router** (sibling to `intake_router.py`), registered only when `OPS_DEV_DSN` is configured, kept **distinct** from the prod/public derive-on-read `GET /api/v1/ops/revenue-recognition`. All state changes flow through `009` DB functions (sole-writer discipline); the API and package never mutate `ops.*` directly.

---

## 5. Migration `009` — completion authority + recognition trace

### 5.1 Table `ops.completion_attestation` (finding #1)
```sql
create table ops.completion_attestation (
  id            uuid primary key default gen_random_uuid(),          -- API addresses it: /completion/{id}/revoke
  apparatus_id  uuid not null references ops.apparatus(id),
  attested_by   uuid not null references ops.persons(person_id),
  reason        text not null check (btrim(reason) <> ''),
  provenance    text not null default 'pm_recognition_attestation'
                  check (provenance in ('pm_recognition_attestation')),  -- extends to 'production_tracking' later
  prior_status  ops.apparatus_status not null,                       -- captured at attest; restored on revoke (no guessing)
  attested_at   timestamptz not null default now(),
  revoked_at    timestamptz,
  revoked_by    uuid references ops.persons(person_id),
  revoke_reason text
);
create unique index uq_completion_attestation_active
  on ops.completion_attestation (apparatus_id) where revoked_at is null;  -- one ACTIVE attestation per apparatus
comment on table ops.completion_attestation is
  'Governed PM attestation that an apparatus is testing-complete FOR RECOGNITION. NOT production truth, NOT customer-facing. The sole sanctioned writer of ops.apparatus.status=Complete for source=ops-intake apparatus. A future production-tracking authority supersedes via provenance=production_tracking.';
```

### 5.2 Recognition-event trace column (sub-decision **a** — included)
```sql
alter table ops.revenue_recognition_event
  add column completion_attestation_id uuid references ops.completion_attestation(id);
```
Populated by `approve_and_recognize` from the apparatus's active attestation; **required on `recognized` rows**, NULL on `reversal` rows (enforced in 5.6). Closes the audit chain: every recognized $ → the exact attestation that authorized its completion.

### 5.3 Function `ops.attest_apparatus_complete(p_apparatus_id uuid, p_attested_by uuid, p_reason text) returns uuid`
1. Reason not blank; `p_attested_by` exists in `ops.persons` (else clean error → API 400).
2. Load apparatus `FOR UPDATE` joined to scope/project; verify: found; `source='ops-intake'`; `is_active` and active non-cancelled scope/project chain; `status NOT IN ('Complete','Cancelled')`; `scope_quote.is_frozen` + `frozen_at NOT NULL` (the "active ops-intake + frozen basis" gate).
3. Capture `prior_status := apparatus.status`.
4. `perform set_config('ops.completion_ctx','1', true);` (txn-local — opens the guard).
5. `update ops.apparatus set status='Complete', updated_at=now() where id=p_apparatus_id;`
6. Insert the attestation (provenance default, `prior_status`). The partial unique index makes a second concurrent/duplicate active attestation a unique violation → API maps to 409.
7. Return attestation id.

### 5.4 Function `ops.revoke_completion_attestation(p_attestation_id uuid, p_revoked_by uuid, p_reason text) returns uuid` (finding #4)
1. Reason not blank; actor in `ops.persons`.
2. Load the **active** attestation (`revoked_at is null`) by id `FOR UPDATE`; not found → error.
3. **Net-recognition gate:** if `sum(recognized_amount) for apparatus > 0` → raise `'apparatus has open recognition; reverse first'`. (Reverse → net 0 → revoke allowed; the `apparatus_protect_recognition` trigger is the hard backstop. Intake re-approval stays *stricter* on any history — `approve.py:140` — and is unchanged.)
4. `perform set_config('ops.completion_ctx','1', true);`
5. `update ops.apparatus set status = (attestation.prior_status), updated_at=now() where id = attestation.apparatus_id;`
6. `update ops.completion_attestation set revoked_at=now(), revoked_by=p_revoked_by, revoke_reason=p_reason where id=p_attestation_id;`
7. Return attestation id.

### 5.5 Modify `ops.approve_and_recognize` (the one Chip-3 touch)
After the existing gates (all unchanged), resolve the active attestation:
```sql
select id into v_att from ops.completion_attestation
 where apparatus_id = p_apparatus_id and revoked_at is null;
if not found then raise exception 'apparatus % has no active completion attestation', p_apparatus_id; end if;
```
Add `completion_attestation_id => v_att` to the `recognized`-event insert. All other behavior identical.

### 5.6 Modify `ops.trg_revrec_insert_integrity` (firewall touch — **FOCUSED REVIEW**)
- On `event_type='recognized'`: in addition to all existing checks, require `new.completion_attestation_id IS NOT NULL` and that it references an attestation with `revoked_at IS NULL` and `apparatus_id = new.apparatus_id`; else raise.
- On `event_type='reversal'`: require `new.completion_attestation_id IS NULL`. All other reversal checks unchanged.

### 5.7 Silent-completion guard (finding #2 — REQUIRED)
```sql
create function ops.trg_apparatus_completion_guard() returns trigger language plpgsql as $$
begin
  if new.source = 'ops-intake'
     and ((new.status = 'Complete') is distinct from (old.status = 'Complete'))   -- transition INTO or OUT OF Complete
     and current_setting('ops.completion_ctx', true) is distinct from '1' then
    raise exception 'apparatus % completion state changes only via attest/revoke functions', new.id;
  end if;
  return new;
end; $$;
create trigger apparatus_completion_guard before update on ops.apparatus
  for each row execute function ops.trg_apparatus_completion_guard();
```
Composes with the two existing `BEFORE UPDATE` apparatus triggers (independent checks; any raise aborts). A non-completion update on a Complete apparatus (status unchanged) does not trigger it.

### 5.8 View `ops.v_completion_recognition_worklist` (finding #5)
Per **eligible** apparatus (`is_active`, `source='ops-intake'`, active non-cancelled scope/project, `scope_quote.is_frozen`):
- `apparatus_id, apparatus_designation, scope_id, project_id, project_number, status, quoted_hours, quoted_revenue`
- active attestation (LEFT JOIN `completion_attestation` where `revoked_at is null`): `attestation_id, attested_by, attested_at, attest_reason`
- recognition (from `v_apparatus_recognition`): `net_recognized, is_recognized, recognized_event_id`
- computed flags: `can_attest` (status NOT IN Complete/Cancelled AND no active attestation), `can_recognize` (`status='Complete'` AND active attestation AND NOT `is_recognized`), `can_revoke` (active attestation AND NOT `is_recognized`), `can_reverse` (`is_recognized`).

### 5.9 Down migration
Reverse order, leaving `001`–`008` and all original `005` objects intact: drop the worklist view; drop `apparatus_completion_guard` trigger + fn; restore `trg_revrec_insert_integrity` to its `005` body; restore `approve_and_recognize` to its `005` body; drop the `completion_attestation_id` column; drop the revoke fn; drop the attest fn; drop `completion_attestation`.

### 5.10 pytest on throwaway `ops_test`
- mig up + down; down restores the `005` functions verbatim (assert recognize works without an attestation column after down).
- **attest:** success → `status='Complete'` + attestation row + `prior_status` captured; rejects non-`ops-intake` source, inactive/cancelled chain, already-Complete, unfrozen basis, unknown actor, blank reason; second active attest → conflict (unique).
- **silent-completion guard:** direct `update ops.apparatus set status='Complete'` (no ctx) **fails** for `source='ops-intake'`; attest path (sets ctx) succeeds.
- **recognize:** populates `completion_attestation_id`; integrity trigger rejects a hand-inserted `recognized` row with NULL or foreign `completion_attestation_id`.
- **revoke:** blocked iff net > 0 (recognize → revoke fails; reverse → revoke succeeds, restores `prior_status`, marks `revoked_*`); unknown actor / blank reason rejected.
- **worklist view:** flags correct across states (eligible-not-complete → `can_attest`; complete+attested+unrecognized → `can_recognize`+`can_revoke`; recognized → `can_reverse` only).

## 6. Package layer (`packages/ops-intake`)
Reuse the existing `ops.*` sole-writer package. Thin wrappers calling the `009` functions: `attest_complete(apparatus_id, attested_by, reason)`, `recognize(apparatus_id, actor, datasheet_clearance, datasheet_ref, cx_clearance, cx_ref)`, `reverse(event_id, actor, reason)`, `revoke(attestation_id, actor, reason)`. Map DB exceptions to typed, **value-free** errors (Chip-5 lesson).
**Cross-task (finding #3):** update `tests/test_approve_envelope.py:72` to reach `'Complete'` via `ops.attest_apparatus_complete` instead of forcing `status` directly (the `009` guard would otherwise break it).

## 7. API — `services/ops/recognition_router.py`
Host-gated (`OPS_DEV_DSN`; router registers only when configured, mirroring intake); actor-gated `ops.persons`; **value-free** guard errors (generic 400/409, no internal text).
- `POST /completion/attest` `{apparatus_id, attested_by, reason}` → 200 `{attestation_id}` / 400 (unknown actor, ineligible) / 409 (already Complete / active attestation exists)
- `POST /completion/{attestation_id}/revoke` `{revoked_by, reason}` → 200 / 400 / 409 (open recognition → reverse first)
- `POST /recognize` `{apparatus_id, recognized_by, datasheet_clearance, datasheet_ref, cx_clearance, cx_ref}` → 200 `{event_id}` / 400 / 409 (already recognized). `obligation_clearance` allowed values surfaced from the DB enum.
- `POST /recognition/{event_id}/reverse` `{reversed_by, reason}` → 200 `{reversal_id}` / 400 / 409 (already reversed / not a recognized event)
- `GET /recognition/worklist?project_number=` → rows from `v_completion_recognition_worklist`
- `GET /recognition/rollup?project_number=` → recognized-$ per scope/project (recognized $ **shown** — operator-authoritative, consistent with §261 `/pm-review/finance`)

API tests: actor-400s, value-free errors, and a host-gating disabled-subprocess test (mirrors the learning/intake pattern).

## 8. UI — `apps/operations-web/app/pm-review/recognition`
Worklist table from `/recognition/worklist`, grouped by scope; per-row actions gated by the view flags — **Attest** (reason-required modal) on `can_attest`; **Recognize** (clearance inputs) on `can_recognize`; **Revoke** on `can_revoke`; **Reverse** on `can_reverse`. Recognized-$ rollup panel. Copy is **"Attest testing complete — for recognition"** everywhere; **never "production complete."** Route-mocked Playwright smoke (asserts POST bodies + re-render).

## 9. Testing & gates
TDD on throwaway `ops_test`; API self-contained; UI typecheck + smoke. **Merge to main + `ops_dev` apply are operator-gated.** IRP cross-engine pass (Codex `review-run`) before merge; the Chip-3 firewall touch (5.5/5.6) gets a dedicated focused-review lens.

## 10. Deferred / forward-compatible
- **Billing slice** (Chip-4 wrap) — the next slice, separate.
- **Records-datasheet production-tracking authority** — future completion source; lands as `provenance='production_tracking'` (extend the CHECK) and can carry higher-fidelity evidence; supersedes PM attestation by policy.
- **Prod application of ops `005`–`009`** — a separate, gated prod-DDL decision; out of scope here.

## 11. Findings traceability (operator audit, 2026-06-23)
| Finding | Resolved in |
|---|---|
| H1 — revocation under-specified (id PK, prior_status, partial unique) | §5.1 |
| H2 — silent-completion guard required + direct-UPDATE-fails test | §5.7, §5.10 |
| M3 — migrate `test_approve_envelope.py:72` to the function | §6 |
| M4 — revoke blocks only on net>0; re-approval stays stricter | §5.4 |
| M5 — richer read model (`v_completion_recognition_worklist`) | §5.8 |
| Sub-decision (a) — `completion_attestation_id` on the ledger now | §5.2, §5.5, §5.6 |
| Sub-decision (b) — guard included (load-bearing) | §5.7 |
| Sub-decision (c) — naming + UI copy | §5.1, §8 |
| No-billing boundary exact | §2, §10 |
