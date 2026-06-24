-- ============================================================================
-- ops migration 009 — recognition bridge (completion attestation -> recognize).
-- Built INCREMENTALLY across plan tasks T0..T6; each task appends one block to
-- THIS file and the matching teardown to 009_recognition_bridge_down.sql.
-- Dev DB: ops_dev / ops_test. Nothing applied to prod (blocked behind the §5.11
-- ops_app role-boundary RELEASE GATE). Builds on 001-008.
-- ============================================================================

-- ---- T0: completion attestation table + one-active-per-apparatus index -----
create table ops.completion_attestation (
  id            uuid primary key default gen_random_uuid(),
  apparatus_id  uuid not null references ops.apparatus(id),
  attested_by   uuid not null references ops.persons(person_id),
  reason        text not null check (btrim(reason) <> ''),
  provenance    text not null default 'pm_recognition_attestation'
                  check (provenance in ('pm_recognition_attestation')),
  prior_status  ops.apparatus_status not null,
  attested_at   timestamptz not null default now(),
  revoked_at    timestamptz,
  revoked_by    uuid references ops.persons(person_id),
  revoke_reason text
);
create unique index uq_completion_attestation_active
  on ops.completion_attestation (apparatus_id) where revoked_at is null;
comment on table ops.completion_attestation is
  'Governed PM attestation that an apparatus is testing-complete FOR RECOGNITION. NOT production truth, NOT customer-facing. Sole sanctioned writer of ops.apparatus.status=Complete for approved apparatus. A future production-tracking authority supersedes via provenance=production_tracking.';
