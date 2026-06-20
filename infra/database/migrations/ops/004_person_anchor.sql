-- ============================================================================
-- ops migration 004 -- person anchor (ops.persons). Phase-5 additive identity slice.
-- Authority: .claude/PLATFORM/INTEGRATION_BACKBONE_IDENTITY_CONTRACT_2026-06-20.md (C1, D2, D4, D6).
-- Dev DB: ops_dev (local PG). Nothing applied to prod.
--
-- Local person anchor for the ops lane -- parity with the FIXED apparatus binding. The
-- canonical person key is prod public.employees.id (cross-DB contract-FK via employee_ref;
-- NOT a DB FK). STANDALONE: it does NOT retrofit FKs onto the ops.* audit columns
-- (created_by / updated_by / approved_by stay provenance-only per contract D6); it is the
-- anchor a future competency-input ops surface FKs into.
-- ============================================================================

create schema if not exists ops;

create table if not exists ops.persons (
  person_id     uuid        primary key default gen_random_uuid(),
  employee_ref  uuid        null,                    -- contract-FK -> prod public.employees.id (NOT a DB FK)
  display_name  text        not null,
  worker_class  text        not null default 'w2',
  match_adjudicated_by  uuid        null,
  match_adjudicated_at  timestamptz null,
  match_confidence      text        null,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),

  constraint ck_ops_persons_display_name_nonempty check (display_name <> ''),
  constraint ck_ops_persons_worker_class check (worker_class in ('w2','1099','partner','legacy')),
  constraint ck_ops_persons_match_confidence
      check (match_confidence is null or match_confidence in ('exact','high','manual')),
  constraint ck_ops_persons_match_adjudication_paired
      check ((match_adjudicated_by is null and match_adjudicated_at is null)
          or (match_adjudicated_by is not null and match_adjudicated_at is not null))
);

comment on table ops.persons is
  'Local person anchor for the ops lane (identity contract C1/D2). Canonical spine = prod '
  'public.employees.id via employee_ref (cross-DB contract-FK, not a DB FK). ops.* audit columns '
  'stay provenance-only (D6) until a competency-input ops surface adopts this anchor.';

create unique index if not exists uq_ops_persons_employee_ref
    on ops.persons (employee_ref) where employee_ref is not null;
