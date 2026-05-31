# Decision-012 Phase 4a - Repoint DB Object Bodies Closeout

Dispatch: `2026-05-30-cc-d012-phase4a-repoint-db-objects`
Executor: Codex
Claim commit: `3a845406`
Migration commit: `ad38a72e`

## Scope

Applied the reversible Phase 4a SQL migration pair:

- `infra/database/migrations/tcc/002_phase4a_repoint_db_objects.sql`
- `infra/database/migrations/tcc/002_phase4a_repoint_db_objects_down.sql`

Only the 3 authorized DB object bodies were changed:

- `public.fn_calculate_test_currents(...)`
- `public.fn_sensor_available_settings(integer)`
- `public.vw_trip_unit_cascade`

No drops, no table changes, no app code changes.

## Captured Originals / DOWN

Captured the pre-apply live definitions with:

- `pg_get_functiondef('public.fn_calculate_test_currents(...)'::regprocedure)`
- `pg_get_functiondef('public.fn_sensor_available_settings(integer)'::regprocedure)`
- `pg_get_viewdef('public.vw_trip_unit_cascade'::regclass, true)`

The DOWN migration restores those captured bodies. Function definitions were terminated as executable SQL statements; the view body is the captured `pg_get_viewdef` body under `CREATE OR REPLACE VIEW public.vw_trip_unit_cascade AS`.

## Final `vw_trip_unit_cascade` UP Definition

```sql
CREATE OR REPLACE VIEW public.vw_trip_unit_cascade AS
 SELECT m.id AS manufacturer_id,
    m.mfr_name AS manufacturer_name,
    tt.id AS trip_type_id,
    tt.name AS trip_type_name,
    ts.id AS trip_style_id,
    ts.style AS trip_style_name,
    ts.tcc_no AS tcc_number,
    s.id AS sensor_id,
    s.rating AS sensor_rating,
    s.description AS sensor_desc,
    s.sensor_idx,
    s.ltpu_calc IS NOT NULL AND s.ltpu_calc <> '-1'::integer AS has_ltpu,
    s.stpu_calc IS NOT NULL AND s.stpu_calc <> '-1'::integer AS has_stpu,
    s.inst_calc IS NOT NULL AND s.inst_calc <> '-1'::integer AS has_inst,
    s.gfpu_calc IS NOT NULL AND s.gfpu_calc <> '-1'::integer AS has_gfpu,
    s.ltpu_calc,
    s.stpu_calc,
    s.inst_calc,
    s.gfpu_calc
   FROM tcc.manufacturers m
     JOIN tcc.trip_styles ts ON ts.mfg_id = m.id
     JOIN tcc.etu_sensors s ON s.trip_style_id = ts.id
     LEFT JOIN tcc.trip_types tt ON tt.manufacturer_id = m.id AND tt.name::text = ts.type::text;
```

## Dry Run

Ran the UP migration in a transaction with final `COMMIT` replaced by validation SELECTs plus `ROLLBACK`.

Pre-dry-run baseline:

- total rows: `17831`
- NULL `trip_type_id`: `396`
- sensor `29442` rows: `1`
- sensor `29442` with `531 / NA`: `0`

Inside dry-run transaction after UP:

- total rows: `17831`
- NULL `trip_type_id`: `0`
- sensor `29442` rows: `1`
- sensor `29442` with `531 / NA`: `1`
- old-ref guard across the 3 objects: `0`

Post-rollback baseline confirmed unchanged before apply:

- total rows: `17831`
- NULL `trip_type_id`: `396`
- sensor `29442` with `531 / NA`: `0`

## Apply Result

Applied `infra/database/migrations/tcc/002_phase4a_repoint_db_objects.sql` to live with `COMMIT`; psql exited `0`.

Post-apply DB spot check:

- total rows: `17831`
- NULL `trip_type_id`: `0`
- sensor `29442` rows: `1`
- sensor `29442` with `531 / NA`: `1`
- old-reference scan across the 3 objects: `0`

DOWN was not needed.

## Post-Apply Gate Table

| Gate | Result |
| --- | --- |
| ETU SQL parity | PASS: `RESULT PASS`, 3 seeded scenarios, evaluate warnings `0` |
| `GET /api/v1/neta/settings/29442` | PASS: HTTP `200`; plug `1`, LTPU `6`, STPU `15`, INST `20`, GFPU `7` |
| `GET /api/v1/neta/context/29442` | PASS: HTTP `200`; Chint / `NA` / `NA1` |
| `GET /api/v1/neta/etu/search?sensor_id=29442` | PASS: HTTP `200`; count `1`, Chint, trip type `531 / NA` |
| `GET /api/v1/neta/etu/breaker-cascade?sensor_id=29442` | PASS: HTTP `200`; count `68`, manufacturer options `1`, class options `2` |
| 396-restore spot check | PASS: NULL `trip_type_id` count `396 -> 0`; sensor `29442` resolves `531 / NA` |
| Breaker catalog/status | PASS: HTTP `200`, `manufacturer_count=63`, `sensor_count=17831` |
| NETA family hosted smoke | PASS: ETU/TMT/EMT route smoke completed; sample ETU search count `17831` |
| Relay SQL parity | PASS: `RESULT PASS`, 6 seeded scenarios, warnings `0`, failures `0` |
| `GET /api/v1/neta/relay/sections?supported_only=true&limit=3` | PASS: HTTP `200`; count `3`, sections `3`, first TD section `82782` |

## Notes

- The first local ETU parity invocation failed before running because the shell did not source the canonical DSN; reran with `/home/olares/apex-secrets/olares/ai-live-dsn.env` sourced and it passed.
- A dry-run guard initially used SQL `LIKE` with unescaped underscores; that falsely matched the intended `tcc.etu_plugs` body. The guard was tightened to escape underscores literally before commit/apply.
- Secrets were sourced from the canonical file only and no DSN value was printed.
