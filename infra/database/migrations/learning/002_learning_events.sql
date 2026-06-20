-- ============================================================================
-- learning migration 002 -- append-only learning_events capture ledger. Slice 2a.
-- Authority: docs/superpowers/specs/2026-06-20-learning-slice2-capture-path-design.md.
-- Dev DB: learning_dev (apply gated). The immutable substrate every later projection
-- (user_study_progress / user_test_attempts) and ROI metric derives from. event_type is a text
-- CHECK vocab (extensible, per the records-lane preference); payload jsonb is the open extension
-- point (score_percent, confidence, duration_seconds, source surface, apparatus_type, ...).
-- ============================================================================

create table if not exists public.learning_events (
  event_id         uuid        primary key default gen_random_uuid(),
  user_id          uuid        not null references public.user_profiles(id) on delete cascade,
  event_type       text        not null,
  study_content_id uuid        null references public.study_content(id) on delete set null,
  neta_section     text        null,
  occurred_at      timestamptz not null default now(),
  payload          jsonb       not null default '{}'::jsonb,
  created_at       timestamptz not null default now(),
  constraint learning_events_event_type_check check (event_type in
    ('resource_viewed', 'resource_completed', 'assessment_completed', 'self_assessment'))
);

create index if not exists ix_learning_events_user_time on public.learning_events (user_id, occurred_at);
create index if not exists ix_learning_events_section   on public.learning_events (neta_section);
create index if not exists ix_learning_events_type      on public.learning_events (event_type);

comment on table public.learning_events is
  'Append-only learning capture ledger (Slice 2a). Immutable: UPDATE/DELETE blocked by a trigger. '
  'neta_section is the cross-lane work-context contract; payload jsonb is the open extension point.';

-- append-only guard: the ledger is immutable.
create or replace function public.learning_events_block_mutation() returns trigger
  language plpgsql as $fn$
begin
  raise exception 'learning_events is append-only (% blocked)', tg_op;
end;
$fn$;

drop trigger if exists trg_learning_events_append_only on public.learning_events;
create trigger trg_learning_events_append_only
  before update or delete on public.learning_events
  for each row execute function public.learning_events_block_mutation();
