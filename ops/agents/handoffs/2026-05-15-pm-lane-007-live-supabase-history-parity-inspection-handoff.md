# PM Lane 007 Handoff - Live Supabase History Parity Inspection

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-007`
Scope: PM runtime live database parity inspection, read-only

## Summary

This tranche inspected the live Supabase/Postgres storage shape needed by the PM Lane 006 decision-history panel.

The inspection was read-only:

```text
default_transaction_read_only=on
SELECT only
```

No SQL write, migration, fixture reset, demo seed, persisted mutation test run, service admission, auth, ingress, or autonomous AI mutation authority was used.

## Live Inspection Result

Connection:

1. Database: `apex_pm_stage`
2. User: `apex_pm_stage_user`
3. Tables present: `seam.audit_log`, `seam.issues`

Schema parity:

1. `seam.audit_log.timestamp` exists as `timestamp with time zone` and is not nullable.
2. `seam.audit_log.from_state` and `seam.audit_log.to_state` exist as `jsonb`.
3. `seam.audit_log.entity_id`, `action_type`, `actor_role`, and `reason` exist for PM history display.
4. `seam.issues.data` exists as non-null `jsonb`, preserving the overflow shape needed for PM follow-up fields.

Live data verdict:

1. `seam.audit_log` row count: `0`.
2. PM decision-history row count: `0`.
3. `seam.issues` row count: `4`.
4. Issue rows with `data.pm_followup_note`: `0`.
5. Issue rows with `data.pm_followup_sent_at`: `0`.
6. Issue rows with `data.pm_followup_workfront_row_id`: `0`.
7. Issue rows with `data.pm_followup_source`: `0`.

## Parity Verdict

The live schema is ready for the PM Lane 006 read-only history panel.

The live data is not yet sufficient to claim returned-to-lead history parity, because there are no live audit rows and no issue PM follow-up overflow fields present.

The truthful state is therefore:

```text
PASS_WITH_EMPTY_LIVE_HISTORY
```

## Files Changed

Packet and status only:

1. `PROJECT_STATUS.md`
2. `ops/agents/packets/draft/2026-05-15-pm-lane-007-live-supabase-history-parity-inspection.json`
3. `ops/agents/handoffs/2026-05-15-pm-lane-007-live-supabase-history-parity-inspection-handoff.md`

## Guardrails Preserved

1. No SQL or schema migration.
2. No SQL write.
3. No persisted mutation seam test run.
4. No fixture reset.
5. No demo seed.
6. No new service admission.
7. No auth or ingress widening.
8. No assignment mutation.
9. No schedule mutation.
10. No Operations Visibility reopening.
11. No autonomous AI business-state mutation.

## Next Bounded Move

Recommended next move: add optional query narrowing to the existing `/api/v1/reads/decision-history` endpoint with bounded `entity_id` filters and a capped `limit`, preserving default behavior and validating in memory only.

Do not claim live returned-to-lead history parity until a later governed packet admits a non-destructive live-data source or a bounded staging mutation proof.
