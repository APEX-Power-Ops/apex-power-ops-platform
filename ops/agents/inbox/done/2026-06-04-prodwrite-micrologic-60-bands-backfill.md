---
dispatch_id: 2026-06-04-prodwrite-micrologic-60-bands-backfill
target: PRODWRITE
priority: 1
from: CC
created_at: 2026-06-04
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-06-04-micrologic-60-bands-backfill-closeout.md
---

# PROD-WRITE — backfill STD/GFD delay bands for the band-less Micrologic 6.0 styles

**Lane:** lvbreakertcc · ETU delay bands (`tcc.etu_std_bands` / `tcc.etu_gfd_bands`).
**Type:** DATA backfill (INSERT only; no DDL, no code). **Operator-authorized 2026-06-04** ("Persist cited bands to DB").
**Migration (the artifact):** `infra/database/migrations/tcc/008_micrologic_60_bands_backfill.sql` (+ `_down`).

## Why
EasyPower's source genuinely carries **no** STD/GFD delay-band rows for the Micrologic 6.0 styles
**238 / 1919 / 1920 / 1921 / 1922 / 2173** (Compact NS + Masterpact NW 6.0A/E/H/P) — a genuine source gap,
not a load defect (STATE §138, verified vs raw Access). The bands are **rating-independent** and EasyPower's
own style **246** (SQD Compact NS 6.0A) carries them — verified identical across all 9 of its sensors and equal
to the datasheet-validated canonical spec (`reference/tcc/MICROLOGIC-6.0A.md` [VENDOR-DOC] ·
`services/neta/micrologic_curves.py`). This persists those same bands to the 593 band-less 6.0 sensors so the
data is self-describing (the §137 runtime fallback already renders them; this makes it dormant).

## Apply (against governed Supabase, service-role)
Run `infra/database/migrations/tcc/008_micrologic_60_bands_backfill.sql` verbatim. It is **idempotent**
(NOT EXISTS guard) and wrapped in a transaction with a post-assert (every target sensor must end with exactly
4 STD + 5 GFD bands, else it RAISEs and rolls back).

## Pre-flight (verified read-only by CC 2026-06-04, expect unchanged)
- Target sensors: **593** (238→10, 1919→148, 1920→118, 1921→148, 1922→159, 2173→10), all currently 0 STD / 0 GFD.
- Rows inserted: **2,372 STD** (593×4) + **2,965 GFD** (593×5).

## Verify (after apply)
```sql
-- every band-less 6.0 sensor now carries 4 STD + 5 GFD; nothing else touched
SELECT s.trip_style_id,
       count(*) AS sensors,
       count(*) FILTER (WHERE (SELECT count(*) FROM tcc.etu_std_bands b WHERE b.sensor_id=s.id)=4) AS std_ok,
       count(*) FILTER (WHERE (SELECT count(*) FROM tcc.etu_gfd_bands g WHERE g.sensor_id=s.id)=5) AS gfd_ok
FROM tcc.etu_sensors s
WHERE s.trip_style_id IN (238,1919,1920,1921,1922,2173)
GROUP BY s.trip_style_id ORDER BY s.trip_style_id;
-- expect sensors==std_ok==gfd_ok for every row
```
Then live-spot-check a former band-less sensor on prod (`/api/v1/neta/plot-tcc` + `/settings`): STD/GFD now
serve from the DB band rows (identical curve to the prior runtime fallback).

## Boundaries
- INSERT only into `tcc.etu_std_bands` / `tcc.etu_gfd_bands`; **no DDL, no other tables, no code.**
- Reversible via `008_micrologic_60_bands_backfill_down.sql` (deletes bands for those 6 styles → restores band-less).
- PUBLIC repo + no secrets in the closeout/chat (counts + style ids only).

## Acceptance / closeout
Closeout at the `closeout:` path with the verify-query result + a one-line confirm (593 sensors → 4 STD + 5 GFD each).
