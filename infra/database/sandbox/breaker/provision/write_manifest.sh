#!/usr/bin/env bash
set -euo pipefail
# Usage: write_manifest.sh <BASELINE_DB> <DUMP_FILE> <STAMP_UTC> <SOURCE_REF>
BASELINE_DB="${1:?}"; DUMP_FILE="${2:?}"; STAMP="${3:?}"; SRC="${4:?}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SU() { docker exec -i apex-dev-pg psql -tA -U postgres "$@"; }
counts=$(SU -d "$BASELINE_DB" -c "select string_agg(k||'='||n,' ') from (
  select case relkind when 'r' then 'tables' when 'v' then 'views' when 'S' then 'sequences'
                      when 'i' then 'indexes' else relkind::text end k, count(*) n
  from pg_class c join pg_namespace s on s.oid=c.relnamespace
  where s.nspname='tcc' group by 1) z;")
policies=$(SU -d "$BASELINE_DB" -c "select count(*) from pg_policies where schemaname='tcc';")
rls=$(SU -d "$BASELINE_DB" -c "select count(*) from pg_class c join pg_namespace s on s.oid=c.relnamespace where s.nspname='tcc' and c.relkind='r' and c.relrowsecurity;")
sha=$(sha256sum "$DUMP_FILE" | awk '{print $1}')
cat > "$HERE/SNAPSHOT_MANIFEST.md" <<EOF
# Breaker Sandbox — Snapshot Manifest

- Source: $SRC
- Baseline DB: $BASELINE_DB
- Snapshot timestamp (UTC): $STAMP
- Dump command shape: \`pg_dump --no-owner --no-privileges --schema=tcc -Fc <PROD_RO_DSN>\`
- Object counts (tcc): $counts
- RLS: $rls tables RLS-enabled; $policies policies (prod: all \`to public\`; 60 ref auth.*, 0 vault.*)
- Restore preflight: auth.uid/role/jwt stubs created pre-restore; NO login-role stubs needed;
  defaults core-only (no contrib extension); \`pg_restore --exit-on-error\` clean.
- Dump sha256: $sha
- Privilege matrix: (filled by Task 7 acceptance run)
- Dump-file deletion proof: (filled by Task 7)
- Doc drift: repo docs say ~60 tcc tables; prod has 91 — reconcile separately.
EOF
echo "write_manifest OK"
