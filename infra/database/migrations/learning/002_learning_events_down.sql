-- ============================================================================
-- learning migration 002 DOWN -- reverse 002_learning_events.sql. Drop the table (its trigger
-- and indexes go with it), then the guard function. Explicit order; idempotent.
-- ============================================================================
drop table if exists public.learning_events;
drop function if exists public.learning_events_block_mutation();
