---
dispatch_id: 2026-06-03-codex-i2x6-prod-band-population-check
target: CODEX
priority: 1
from: CC
created_at: 2026-06-03
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-06-03-i2x6-prod-band-population-check-closeout.md
---

# I2X-6 gate — confirm prod route-1 band data is populated (prod read-only)

**Lane:** lvbreakertcc · L4 I2X promotion chain (STATE §116 · punch-list L4 · G4 §3b·I2X).
**Type:** READ-ONLY verification against prod (Supabase Postgres). **No writes. No DDL. No migrations. No code.**
Single deliverable = the result counts (in the closeout / back to CC).

## Why
Before CC wires the validated `etu_ixt` route-1 (I2X / Iˣt) delay kernel into `/calculate` and promotes route-1
trust `withheld → db`, we must confirm the **prod band tables carry the kernel inputs populated** — not just that the
columns exist. Schema is provisioned (002 migration); **data population** is the open question. I2X-4 (native-CIxt
parity, bit-exact) and I2X-5 (composite rule recovered) are DONE; this is the one blocked sub-task of I2X-6.

## Prerequisite (check before claim — inbox step 4)
You need **prod (Supabase) read access** in your environment (a Supabase SQL editor session, a read DSN for `psql`,
or an authorized `supabase` MCP). If prod is plainly unreachable from your clone/host, **do not claim** — leave this
in `pending/` and report back: "I2X-6 band check not executable here — no prod read access." (CC's own Supabase MCP
is unauthorized this session, which is why this is dispatched.)

## Run these read-only queries

**1) Confirm the actual prod column names** (the 002 migration mapped the extraction layer's
`std_x`/`i_open`/`t_open`/`i2x` → these tables; verify real names before trusting steps 2–4):
```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'tcc' AND table_name IN ('etu_std_bands', 'etu_gfd_bands')
ORDER BY table_name, ordinal_position;
```

**2) STD band population, grouped by I2X shape** (`count(col)` = non-NULLs; adjust names per step 1 if they differ):
```sql
SELECT i2x,
       count(*)         AS rows,
       count(exp_x)     AS has_exp_x,
       count(i_open)    AS has_i_open,
       count(t_open)    AS has_t_open,
       count(i_clear)   AS has_i_clear,
       count(t_clear)   AS has_t_clear,
       count(std_open)  AS has_std_open,
       count(std_clear) AS has_std_clear
FROM tcc.etu_std_bands
GROUP BY i2x
ORDER BY i2x;
```

**3) GFD band population, grouped by I2X shape** — same SELECT against `tcc.etu_gfd_bands`.

**4) Gap check on the bands the kernel needs** — ramp (`i2x=1`) + composite (`i2x=2`):
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
-- then repeat the same block against tcc.etu_gfd_bands
```

## Success criterion (what "populated" means)
- **Ramp (`i2x=1`)** and **composite (`i2x=2`)** bands have non-NULL `exp_x` + open/clear anchors
  (`i_open/t_open/i_clear/t_clear`) → `null_exp_x`, `null_open_anchor`, `null_clear_anchor` should be **0** for both.
- **Composite (`i2x=2`)** additionally needs a non-NULL floor (`std_open/std_clear`) → `composite_null_floor` = 0.
- **Flat (`i2x=0`/NULL)** bands legitimately have NULL anchors (definite-time only) — expected, not a gap.
- Confirm the **column names** the `/calculate` wiring will read exist as named: `i2x, exp_x, i_open, t_open,
  i_clear, t_clear, std_open, std_clear`. Flag any mismatch (the real names win — report them).

If those hold → prod route-1 data is populated; I2X-6 wiring can proceed (after the composite native-render
validation + the operator's trust-flip go). Any NULL gaps in ramp/composite anchors = the load didn't populate them
→ that load fix precedes wiring.

## Boundaries / guardrails
- **READ-ONLY.** No writes, DDL, migrations, or code. No `page.tsx` / route / engine edits.
- **PUBLIC repo + no-secrets:** never paste a token, DSN, connection string, or project ref into the closeout, this
  file, or chat. A Supabase access token (if you configure one) is entered **out-of-band only**. Output is **aggregate
  counts only** — no row-level customer/job data.
- Follow the inbox lifecycle: `git mv pending→claimed` + push BEFORE running; closeout to the `closeout:` path; then
  `git mv claimed→done` + push.

## Acceptance / closeout
Write the closeout at `ops/agents/handoffs/2026-06-03-i2x6-prod-band-population-check-closeout.md` containing:
- The four result tables (step 1 columns; step 2 std-by-shape; step 3 gfd-by-shape; step 4 std + gfd gap check).
- A one-line **verdict**: populated ✅ / gaps found ⚠️ (describe which shapes/columns).
- Any column-name mismatches vs the expected set, with the real names.
