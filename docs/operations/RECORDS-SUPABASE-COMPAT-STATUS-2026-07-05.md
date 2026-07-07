# Records Supabase-Compat Lane - Status (2026-07-05)

Lane: `records/supabase-compat` off `origin/main @ 3f3ebe46`. Spec/plan:
`docs/superpowers/specs/2026-07-04-records-supabase-compat-design.md` (rev 4) /
`docs/superpowers/plans/2026-07-04-records-supabase-compat.md`.

## Summary

**Phase 1 (local non-superuser harness + red-proof) is DONE and committed.**
**Phase 0 (Supabase branch capability probe) and Phase 2/3 (migration adaptation +
branch green proof) remain BLOCKED on Supabase lifecycle capacity** - not on repo
implementation.

This lane has NOT proven Supabase managed-`postgres` compatibility. A real Supabase
branch is the fidelity authority (spec B2/Phase 0), and that branch cannot be
provisioned right now (see below).

## Phase-0 lifecycle-capacity preflight (2026-07-05, read-only)

- Project `fxoyniqnrlkxfligbxmg` (apex-power-ops): `ACTIVE_HEALTHY`, us-west-2.
- Postgres `17.6.1.127` - ABOVE the `17.6.1.121` upgrade floor; no upgrade needed.
- Branches: only `main` (the default branch = the prod project itself). **No
  preview/dev branch is provisioned to reuse.**
- Prod records: fully greenfield (schema absent, 0 objects, 0 roles) - rolled back
  after the 2026-07-04 prod-apply superuser incompatibility.

## Why Phase 0 is blocked

Supabase reported an unresolved multi-region lifecycle incident (2026-07-05)
affecting project creation, branch provisioning, resize, and restart (Database/Auth/
API themselves operational). Phase 0 Task 0.1 requires `create_branch`, and every
Phase-0 capability probe (Gate A, Gate B, ownership choreography, DDL envelope) is a
scratch-WRITE the lane forbids on prod. Prod is greenfield, so there is no read-only
inventory to run against it either. With no running preview branch to reuse and branch
provisioning destabilized, Phase 0 cannot start. Per operator direction, the lane is
recorded BLOCKED on Supabase lifecycle capacity - not turned into a fake code blocker.
See `[[feedback_supabase_prod_superuser_fidelity]]`.

## What Phase 1 delivered (branch-independent, committed)

- **T1.1 (`10a55c9b`)** - `--apply-as-non-superuser` on `run_validation.py`: the
  tier-3 walk applies through a disposable non-superuser applier role
  (`make_local_applier` + a provisional non-super/createrole envelope;
  bypassrls/replication/createdb deliberately omitted pending Phase-0 confirmation).
- **T1.2 (`068b8436`)** - DB-backed red-proof (`test_supabase_compat_redproof.py`):
  001-044 apply cleanly as the applier (base-stack viability), then the UNADAPTED
  045 fails at line 21 (`alter role records_api ... nosuperuser`) with SQLSTATE
  42501 - reproducing the 2026-07-04 prod failure class as a local CI tripwire.
  Self-skips once 045 is adapted (Phase 2 supersedes it).

Verified on host local Postgres: 20 passed (2 red-proof + 18 unit). Disposable DBs and
applier roles left ZERO residue.

**This is a LOCAL APPROXIMATION on a true-superuser local Postgres. It is NOT a
Supabase-compat proof.**

## Reproduce the local red-proof (host)

```
set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a
export RECORDS_PG_ADMIN_DSN="host=127.0.0.1 port=5432 dbname=postgres user=postgres password=${DEV_PG_PASSWORD} sslmode=disable"
export PATH=$HOME/.local/bin:$PATH
cd infra/database/migrations/records
uv run --no-project --with pytest --with 'psycopg[binary]' python -m pytest \
  test_supabase_compat_redproof.py test_run_validation_unit.py -q
```

## Resume path (when Supabase lifecycle is stable)

1. Confirm branch provisioning is available (project not mid-incident).
2. Run Phase 0 (Task 0.1-0.7): `create_branch` -> apply 001-044 -> capability probes
   -> write `PHASE0-FINDINGS.md` -> `delete_branch` + zero-residue proof.
3. Task 2.0 gate: resolve Gate A / Gate B / ownership choreography from the findings
   (STOP + escalate on any unavoidable edge), then Phase 2 (adapt 045-049 up+down)
   and Phase 3 (branch green + invariants 1-8 + residue).

## Note (not this lane's residue)

Local PG carries pre-existing `records_api` / `records_intake_writer` roles
(`login=true`, no password) left by a prior admin-mode validation run. They are NOT
from this lane (Phase 1 rolls back 045, so it never persists these). Left in place -
dropping shared cluster roles is an operator call.
