---
dispatch_id: 2026-06-03-codex-sst-bridge-scramble-scope-verify
target: CODEX
priority: 1
from: CC
created_at: 2026-06-03
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-06-03-sst-bridge-scramble-scope-verify-closeout.md
---

# SST-bridge scramble bug — quantify scope + confirm load-vs-source (prod read-only)

**Lane:** lvbreakertcc · SST bridge (`tcc.vw_breaker_sst_bridge` ← `tcc.brk_{mccb,iccb,pcb}_styles`, D1/§104).
**Type:** READ-ONLY verification. **No writes. No DDL. No code.** Deliverable = the counts/samples in the closeout.

## Why
CC found a real, field-facing bridge data error: Eaton Power Defense **PDG6** frames (1600–2500 A) map via
`tmt_sst_style="PDG2-LSI"` to **60–225 A** sensors; PDG3/PDG4 frames (600/800 A) map to **NRX-LSI (800–4000 A)**;
only PDG2 maps correctly. The scramble pattern (small frames → big trip styles and big frames → small trip styles)
is the signature of the **§104 D1 re-carry** ("4 cols re-carried via `rank=id`") misaligning the `tmt_sst_*`
attribution. A tech selecting an affected breaker is offered the **wrong sensor set → wrong NETA settings**. We need
the true SCOPE (how many styles, which classes/families) and confirmation of **load-vs-source** before re-deriving.

## Prerequisite (check before claim — inbox step 4)
Prod (Supabase) read access. If unreachable, leave in `pending/` and report. (This is the same access the
`2026-06-03-codex-i2x6-prod-band-population-check` dispatch used successfully.)

## Run these read-only queries

**1) Column inventory** (find the rating/amp column + the tmt_sst_* + frame-name columns on the style tables):
```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'tcc' AND table_name IN ('brk_mccb_styles','brk_iccb_styles','brk_pcb_styles')
ORDER BY table_name, ordinal_position;
-- and the bridge view:
SELECT column_name, data_type FROM information_schema.columns
WHERE table_schema='tcc' AND table_name='vw_breaker_sst_bridge' ORDER BY ordinal_position;
```

**2) Rating-consistency scan — the scope.** For each breaker style, compare the breaker frame's nameplate rating
(use a real amp/rating column from step 1 if present; else parse the trailing number from the frame/style name) to
the **max sensor rating** the bridge maps it to. Flag clear inconsistencies. Adjust the column names per step 1:
```sql
WITH brg AS (
  SELECT breaker_class, breaker_style_id,
         max(breaker_style_frame) AS frame,
         min(sensor_rating) AS min_sensor, max(sensor_rating) AS max_sensor,
         count(*) AS n_sensors
  FROM tcc.vw_breaker_sst_bridge
  GROUP BY breaker_class, breaker_style_id
), rated AS (
  SELECT *,
         -- last integer in the frame name as a rough nameplate amp (refine if a real column exists)
         NULLIF((regexp_match(frame, '(\d+)\s*A?\s*$'))[1], '')::numeric AS frame_amp
  FROM brg
)
SELECT breaker_class,
       count(*) AS styles,
       count(*) FILTER (WHERE frame_amp IS NOT NULL AND frame_amp > 2.0 * max_sensor) AS frame_gt_2x_sensor_max,
       count(*) FILTER (WHERE frame_amp IS NOT NULL AND frame_amp < 0.5 * min_sensor) AS frame_lt_half_sensor_min
FROM rated
GROUP BY breaker_class
ORDER BY breaker_class;
```

**3) Samples of the worst offenders** (so we can eyeball the wrong mapping + the `tmt_sst_*` it carries):
```sql
WITH brg AS (
  SELECT breaker_class, breaker_style_id, max(breaker_style_frame) AS frame,
         max(tmt_sst_mfr) AS tmt_mfr, max(tmt_sst_type) AS tmt_type, max(tmt_sst_style) AS tmt_style,
         min(sensor_rating) AS min_sensor, max(sensor_rating) AS max_sensor
  FROM tcc.vw_breaker_sst_bridge GROUP BY breaker_class, breaker_style_id
)
SELECT frame, tmt_mfr, tmt_type, tmt_style, min_sensor, max_sensor
FROM brg
WHERE frame ~* 'PDG[3-7]'                       -- Eaton Power Defense large frames (the known-bad family)
ORDER BY frame
LIMIT 60;
```

**4) Eaton Power Defense full picture** (group the family by frame prefix → what each maps to):
```sql
SELECT split_part(frame,'-',1) AS frame_family, tmt_style,
       min(min_sensor) AS min_sensor, max(max_sensor) AS max_sensor, count(*) AS styles
FROM (
  SELECT breaker_style_id, max(breaker_style_frame) AS frame, max(tmt_sst_style) AS tmt_style,
         min(sensor_rating) AS min_sensor, max(sensor_rating) AS max_sensor
  FROM tcc.vw_breaker_sst_bridge WHERE breaker_style_frame ~* '^PDG' GROUP BY breaker_style_id
) q
GROUP BY split_part(frame,'-',1), tmt_style ORDER BY frame_family, tmt_style;
```

## (Optional, if reachable) load-vs-source confirm
If the EasyPower source `BreakerMCCBStyles` (Access DB on the host, or the §104 source artifact) is reachable, read
`TMT_SST_Mfr/Type/Style` for 3 sample PDG6 frames and compare to what prod `brk_mccb_styles` carries. If they
match → the source itself is odd (unlikely); if prod ≠ source → confirms the §104 re-carry misaligned. If the source
isn't reachable here, just note that — CC will do the source-confirm separately.

## Success criterion / what we need back
- The **scope**: per class (MCCB/ICCB/PCB), how many styles are rating-inconsistent (step 2 counts).
- The **Eaton PD family map** (step 4) + worst-offender samples (step 3) — which frame families are scrambled and
  what they wrongly point to.
- The column inventory (step 1) — esp. whether a real rating/amp column exists on `brk_*_styles` (cleaner than name-parsing).
- Load-vs-source note (optional step), if reachable.
- A one-line verdict: scramble scope (e.g., "~N MCCB styles inconsistent, concentrated in Eaton PD PDG3-7").

## Boundaries
- READ-ONLY. No writes/DDL/code. PUBLIC repo + no secrets (no token/DSN/project-ref in the closeout/chat); aggregate
  counts + style/frame names only.
- Inbox lifecycle: `git mv pending→claimed` + push before running; closeout to the `closeout:` path; then
  `git mv claimed→done` + push.

## Acceptance / closeout
Closeout at `ops/agents/handoffs/2026-06-03-sst-bridge-scramble-scope-verify-closeout.md` with the step results +
the verdict. CC will use it to design the bridge re-derivation (the fix) — which is a separate prod-write packet.
