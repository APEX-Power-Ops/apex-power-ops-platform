# TCC Phase G Hosted Parity And Relay Guard Closeout

Date: 2026-05-30
Dispatch: `2026-05-30-cc-tcc-phase-g-hosted-parity-and-relay-guard`
Status: Closed with one credential blocker recorded

## Claim

Claim lifecycle was restored before execution:

1. moved the dispatch from `pending/` to `claimed/`,
2. committed `9a1212e4 claim: 2026-05-30-cc-tcc-phase-g-hosted-parity-and-relay-guard by codex`,
3. pushed the claim before executing.

## G-1 Hosted Breaker-Lane Parity

Public host: `https://control.apexpowerops.com`

Deployed baseline smoke:

```text
apps/control-plane-api/.venv/bin/python apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com --skip-authenticated-checks
RESULT PASS
health=200 ok
ready=200 ready / database connected / catalog_available true
openapi=200
mcp=200
oauth discovery=200
unauth task packets=401 with Bearer challenge
```

Authenticated checks were intentionally skipped because this Phase G surface was read-only and must not mint disposable Supabase users.

Catalog parity anchor:

```text
GET https://control.apexpowerops.com/api/v1/neta/catalog/status
HTTP 200
{"catalog":"live","manufacturer_count":63,"sensor_count":17831}
```

Breaker family smoke:

```text
apps/control-plane-api/.venv/bin/python apps/control-plane-api/scripts/smoke_local_neta_family_routes.py --base-url https://control.apexpowerops.com --artifact-path ''
PASS
ETU: manufacturer_options=63, search_count=17831, known sensor 25 GE / MVT RMS-9 / ICCB, calculate warnings=0, plot curves=2
TMT: frame_id=8038, manufacturer=ABB, trip_class=4, curve_count=1
EMT: frame_id=2953, section_id=6200, band_id=12354, manufacturer=Allis-Chalmers, curve_count=1
```

ETU SQL parity:

```text
set -a; source /home/olares/apex-secrets/olares/ai-live-dsn.env; set +a; export APEX_OLARES_LIVE_DSN
cd apps/control-plane-api
PYTHONPATH=. .venv/bin/python scripts/probe_live_etu_sql_parity.py --base-url https://control.apexpowerops.com --artifact-path ''
RESULT FAIL
psycopg2.OperationalError: password authentication failed for user "postgres"
```

Credential interpretation:

1. the canonical loader file exists,
2. `APEX_OLARES_LIVE_DSN` is present after sourcing/exporting,
3. no DSN value was printed,
4. the selected DSN metadata points at the governed Supabase pooler shape,
5. the failure is PostgreSQL authentication for the sourced credential, not a hosted route parity mismatch.

Because of that credential failure, the expected `3 pass / 0 warn` SQL-parity result could not be reproduced in this run. The blocker is out-of-band credential material, not repo code.

## G-2 Relay Prod 500 Guard

Pre-fix public behavior:

```text
GET https://control.apexpowerops.com/api/v1/neta/relay/sections
HTTP 500
Internal Server Error
```

Implemented guard:

1. moved the relay work-schema table-presence probe into `apps/control-plane-api/services/neta/router.py`,
2. made `tests/test_neta_relay_live_integration.py` reuse the same router helper,
3. guarded `/relay/sections`, `/relay/context/{td_section_source_id}`, `/relay/settings/{td_section_source_id}`, and `/relay/plot-tcc`,
4. absent relay work-schema tables now return `HTTP 503` with detail `relay catalog unavailable: work-schema tables not present`,
5. no relay data load, schema migration, breaker route change, auth change, or new route was made.

Guard publication:

```text
bf8e43f3 Guard relay routes when catalog tables are absent
```

Post-deploy public verification:

```text
GET https://control.apexpowerops.com/api/v1/neta/relay/sections
HTTP 503
{"detail":"relay catalog unavailable: work-schema tables not present"}
```

The route flipped from the old 500 on poll attempt 6 to the expected 503 on poll attempt 7 after Render propagation.

Post-deploy host sanity:

```text
apps/control-plane-api/.venv/bin/python apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com --skip-authenticated-checks
RESULT PASS
```

```text
GET https://control.apexpowerops.com/api/v1/neta/catalog/status
HTTP 200
{"catalog":"live","manufacturer_count":63,"sensor_count":17831}
```

```text
apps/control-plane-api/.venv/bin/python apps/control-plane-api/scripts/smoke_local_neta_family_routes.py --base-url https://control.apexpowerops.com --artifact-path ''
PASS
```

## Local Validation

```text
source /home/olares/apex-secrets/olares/ai-live-dsn.env && cd apps/control-plane-api && PYTHONPATH=../../packages/calc-engine/src:. .venv/bin/python -m pytest tests/test_neta_relay_routes.py -q
11 passed, 1 warning
```

```text
set -a; source /home/olares/apex-secrets/olares/ai-live-dsn.env; set +a; export APEX_OLARES_LIVE_DSN; cd apps/control-plane-api && PYTHONPATH=../../packages/calc-engine/src:. .venv/bin/python -m pytest tests/test_neta_relay_live_integration.py -q -rs
1 skipped, 1 warning
SKIPPED: Relay work-schema tables are not present in the active database
```

```text
cd packages/calc-engine && PYTHONPATH=src ../../apps/control-plane-api/.venv/bin/python -m pytest tests/test_relay_golden_fixtures.py -q
19 passed
```

`git diff --check` passed for the bounded relay guard path set.

## Boundary Confirmation

Read-only boundary held:

1. no governed DB writes,
2. no disposable user minting,
3. no relay table load,
4. no schema migration,
5. no auth/ingress changes,
6. no breaker route changes,
7. no new route.

Scoped staging was used. Existing unrelated residue remained excluded: `pnpm-lock.yaml`, `output/`, and canary actual artifacts.

## Next Required Action

Rotate or repair `/home/olares/apex-secrets/olares/ai-live-dsn.env` out of band, then rerun:

```text
set -a; source /home/olares/apex-secrets/olares/ai-live-dsn.env; set +a; export APEX_OLARES_LIVE_DSN
cd apps/control-plane-api
PYTHONPATH=. .venv/bin/python scripts/probe_live_etu_sql_parity.py --base-url https://control.apexpowerops.com --artifact-path ''
```

Expected after credential repair: `RESULT PASS: live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 0`.
