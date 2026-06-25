-- Stub the `work` schema enum TYPES that prod `tcc` columns reference (relay provenance + relay
-- range/restraint kinds). The `--schema=tcc` dump EXCLUDES the work schema, so these types must
-- exist on the baseline BEFORE pg_restore (the relay_* table DDL references them as column types).
-- Value lists are the COMPLETE prod pg_enum labels (probed 2026-06-25) — a missing label would fail
-- the data COPY. Idempotent.
create schema if not exists work;
do $$ begin
  if not exists (select 1 from pg_type t join pg_namespace n on n.oid=t.typnamespace
                 where n.nspname='work' and t.typname='provenance_source_enum') then
    create type work.provenance_source_enum as enum
      ('manual','p6_import','api','automation','migration','bulk_upload');
  end if;
  if not exists (select 1 from pg_type t join pg_namespace n on n.oid=t.typnamespace
                 where n.nspname='work' and t.typname='provenance_status_enum') then
    create type work.provenance_status_enum as enum
      ('curated','imported','provisional','validated','rejected');
  end if;
  if not exists (select 1 from pg_type t join pg_namespace n on n.oid=t.typnamespace
                 where n.nspname='work' and t.typname='relay_range_parent_kind_enum') then
    create type work.relay_range_parent_kind_enum as enum
      ('td_section','line_section','iec_curve','swz_curve','bsl_curve','meq_curve','pcd_curve',
       'lrm_curve','rxd_curve','egc_curve','tcp_curve');
  end if;
  if not exists (select 1 from pg_type t join pg_namespace n on n.oid=t.typnamespace
                 where n.nspname='work' and t.typname='relay_voltage_restraint_kind_enum') then
    create type work.relay_voltage_restraint_kind_enum as enum
      ('none','multiplier','discrete_curve_set');
  end if;
end $$;
