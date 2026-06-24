-- ============================================================================
-- DOWN — ops migration 009 recognition bridge. Undoes ONLY 009 (leaves 001-008
-- intact). FULLY IDEMPOTENT: every block uses `if exists` / `create or replace`, so
-- running this down TWICE in a row is a clean no-op (proven by
-- test_down_is_idempotent_double_down). Built incrementally across T0..T6: each task
-- PREPENDS its teardown so the down runs in reverse dependency order. Final order
-- (T6 top -> T0 bottom): drop views; drop completion guard; drop attestation-
-- immutability trigger/fn; create-or-replace the two 005 fns VERBATIM; drop the
-- trace column; drop revoke fn; drop attest fn; drop completion_attestation.
-- ============================================================================

-- ---- T2: drop completion guard trigger + function -------------------------
drop trigger if exists apparatus_completion_guard on ops.apparatus;
drop function if exists ops.trg_apparatus_completion_guard() cascade;

-- ---- T1: drop attestation-immutability trigger + function ------------------
drop trigger if exists completion_attestation_immutable on ops.completion_attestation;
drop function if exists ops.trg_completion_attestation_immutable() cascade;

-- ---- T0: drop the completion attestation table -----------------------------
drop table if exists ops.completion_attestation cascade;
