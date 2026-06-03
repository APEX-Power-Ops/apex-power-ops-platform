# Handoff — I2X-6 gate: confirm prod route-1 band data is populated (Supabase / prod read-only)

- **Date:** 2026-06-03
- **Lane:** lvbreakertcc · L4 I2X promotion chain (STATE §116 · punch-list L4 · G4 §3b·I2X)
- **Status:** PENDING — needs a worker/operator with prod (Supabase Postgres) read access
- **Requester:** CC (TCC lane). I2X-4 (native-CIxt parity, bit-exact) + I2X-5 (composite rule recovered) are DONE; this is the one blocked sub-task of **I2X-6**.
- **Type:** read-only verification. **No writes. No DDL. No secrets in this doc or in chat.**

## Why this is needed
Before wiring the validated `etu_ixt` route-1 (I2X / Iˣt) delay kernel into `/calculate` and promoting route-1 trust
`withheld → db`, we must confirm the **prod band tables actually carry the kernel inputs populated** (not just that the
columns exist). The schema is provisioned (002 migration); the open question is **data population** for the I2X bands.

## The blocker
The Supabase MCP server is **unauthorized** in CC's current session:
> `Unauthorized. Please provide a valid access token to the MCP server via the --access-token flag or SUPABASE_ACCESS_TOKEN.`

So CC cannot self-serve the prod read. **You do not need to log into Supabase interactively** — this is about the MCP
server's token, or simply running the queries below.

## Two ways to clear it (pick one)
- **Path A — authorize CC's Supabase MCP (durable; preferred).** Set a valid `SUPABASE_ACCESS_TOKEN` (a read-capable
  Supabase personal/project access token) for the `supabase` MCP server in CC's MCP config (`~/.claude.json` →
  `mcpServers.supabase`, or the server's `--access-token` arg). **Enter it out-of-band** (never paste the token into
  chat or a model-visible terminal). Once set, tell CC "supabase is connected" and CC runs the checks itself.
- **Path B — run + return (quick).** Anyone with prod read access (Supabase SQL editor / `psql` / an authorized agent)
  runs the SQL below and pastes the **result tables** back (the counts are non-secret aggregate data). Do **not** paste
  any DSN / token / connection string.

## Security boundary (must hold)
- Token entered **out-of-band only**; it must never appear in chat, this doc, a committed file, or a model-visible terminal.
- This handoff lives in the **public** `apex-power-ops-platform` repo — it contains **no secrets** and must stay that way.
  The table/column names referenced are already public in `apps/control-plane-api/services/neta/router.py`.
- Output is **aggregate counts only** — safe to share. Do not return row-level customer/job data.

## The read-only SQL

**1) Confirm the actual prod column names** (the 002 migration mapped the extraction layer's
`std_x`/`i_open`/`t_open`/`i2x` → these tables; verify the real names before trusting steps 2–4):
```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'tcc' AND table_name IN ('etu_std_bands', 'etu_gfd_bands')
ORDER BY table_name, ordinal_position;
```

**2) STD band population, grouped by I2X shape** (`count(col)` counts non-NULLs; adjust names per step 1 if they differ):
```sql
SELECT i2x,
       count(*)          AS rows,
       count(exp_x)      AS has_exp_x,
       count(i_open)     AS has_i_open,
       count(t_open)     AS has_t_open,
       count(i_clear)    AS has_i_clear,
       count(t_clear)    AS has_t_clear,
       count(std_open)   AS has_std_open,
       count(std_clear)  AS has_std_clear
FROM tcc.etu_std_bands
GROUP BY i2x
ORDER BY i2x;
```

**3) GFD band population, grouped by I2X shape:**
```sql
SELECT i2x,
       count(*)          AS rows,
       count(exp_x)      AS has_exp_x,
       count(i_open)     AS has_i_open,
       count(t_open)     AS has_t_open,
       count(i_clear)    AS has_i_clear,
       count(t_clear)    AS has_t_clear,
       count(std_open)   AS has_std_open,
       count(std_clear)  AS has_std_clear
FROM tcc.etu_gfd_bands
GROUP BY i2x
ORDER BY i2x;
```

**4) Gap check on the bands the kernel actually needs** — ramp (`i2x=1`) + composite (`i2x=2`):
```sql
SELECT i2x,
       count(*)                                                   AS rows,
       count(*) FILTER (WHERE exp_x IS NULL)                      AS null_exp_x,
       count(*) FILTER (WHERE i_open IS NULL OR t_open IS NULL)   AS null_open_anchor,
       count(*) FILTER (WHERE i_clear IS NULL OR t_clear IS NULL) AS null_clear_anchor,
       count(*) FILTER (WHERE i2x = 2 AND (std_open IS NULL OR std_clear IS NULL)) AS composite_null_floor
FROM tcc.etu_std_bands
WHERE i2x IN (1, 2)
GROUP BY i2x
ORDER BY i2x;
-- repeat for tcc.etu_gfd_bands
```
(Run the same block against `tcc.etu_gfd_bands`.)

> Note: run these in a **direct prod SQL runner** (Supabase SQL editor / `psql` / authorized MCP). CC's MCP wrapper
> auto-appends `LIMIT 50` and rejects some constructs, but these are plain grouped SELECTs and are fine as-is.

## Success criterion (what "populated" means)
- **Ramp (`i2x=1`)** and **composite (`i2x=2`)** bands have **non-NULL `exp_x` and open/clear anchors**
  (`i_open/t_open/i_clear/t_clear`). `null_exp_x`, `null_open_anchor`, `null_clear_anchor` should be **0** for those shapes.
- **Composite (`i2x=2`)** additionally needs a **non-NULL floor** (`std_open/std_clear`) — `composite_null_floor` = 0.
- **Flat (`i2x=0`/NULL)** bands legitimately have NULL anchors (definite-time only) — that's expected, not a gap.
- Confirm the **column names match** what `etu_ixt` / the `/calculate` wiring will read (`i2x`, `exp_x`, `i_open`,
  `t_open`, `i_clear`, `t_clear`, `std_open`, `std_clear`). Flag any name mismatch.

If those hold, route-1 prod data is populated and I2X-6 wiring can proceed (after the composite native-render
validation + the operator's trust-flip sign-off). Any NULL gaps in ramp/composite anchors = the extraction/load
didn't populate them → fix the load before wiring.

## RESULTS (fill in — Path B, or CC fills after Path A)
> Paste the four result tables here (or in chat). Counts only.

- Step 1 (columns): _…_
- Step 2 (std by shape): _…_
- Step 3 (gfd by shape): _…_
- Step 4 (ramp/composite gap check, std + gfd): _…_
- Verdict: populated ✅ / gaps found ⚠️ (describe): _…_
