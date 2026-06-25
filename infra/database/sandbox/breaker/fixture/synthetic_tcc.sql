-- A tiny tcc-shaped schema standing in for prod. Deliberately exercises: a gen_random_uuid()
-- default (core PG13+), a sequence/nextval default, a now() default, RLS enabled, a policy that
-- references auth.uid() (the prod risk), and a view. NOT representative of real columns — it only
-- has to hit the same RESTORE/PREFLIGHT code paths.
create schema if not exists tcc;

create table tcc.fx_breakers (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  created_at  timestamptz not null default now()
);

create sequence tcc.fx_settings_seq;
create table tcc.fx_settings (
  id          bigint primary key default nextval('tcc.fx_settings_seq'),
  breaker_id  uuid references tcc.fx_breakers(id),
  owner_id    uuid,
  value       numeric
);

-- RLS + an auth.uid()-referencing policy (mirrors prod's 60 auth-ref policies, all "to public")
alter table tcc.fx_settings enable row level security;
create policy fx_settings_sel on tcc.fx_settings for select to public
  using (owner_id = auth.uid());

create view tcc.fx_summary as
  select b.id, b.name, count(s.*) as n
  from tcc.fx_breakers b left join tcc.fx_settings s on s.breaker_id = b.id
  group by 1, 2;

insert into tcc.fx_breakers(name) values ('FX-A'), ('FX-B');
insert into tcc.fx_settings(breaker_id, owner_id, value)
  select id, gen_random_uuid(), 1.0 from tcc.fx_breakers;
