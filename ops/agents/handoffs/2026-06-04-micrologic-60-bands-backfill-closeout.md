---
dispatch_id: 2026-06-04-prodwrite-micrologic-60-bands-backfill
status: DONE
applied_by: CC
applied_at: 2026-06-04
mechanism: Supabase apply_migration (migration tcc_008_micrologic_60_bands_backfill), governed prod fxoyniqnrlkxfligbxmg
---

# CLOSEOUT — Micrologic 6.0 band backfill (migration 008) APPLIED + verified

Operator-authorized 2026-06-04 ("please run #71 packet"). Applied the reviewed migration
`infra/database/migrations/tcc/008_micrologic_60_bands_backfill.sql` to governed prod via
`apply_migration` (the migration mechanism — not ad-hoc `execute_sql`; the working read MCP stayed
read-only for the pre/post verification). `{"success":true}` (the in-migration post-assert passed).

## Pre-flight (read-only, matched the packet exactly)
593 Micrologic 6.0 sensors (styles 238/1919/1920/1921/1922/2173), **all band-less** (0 STD / 0 GFD rows).

## Result (read-only post-verify)
- **2,372 STD rows** (593×4) + **2,965 GFD rows** (593×5) inserted; nothing else touched.
- Every band-less 6.0 sensor now carries exactly **4 STD + 5 GFD** bands. Per-style:

| trip_style_id | sensors | std_ok (=4) | gfd_ok (=5) |
|---|---|---|---|
| 238  | 10  | 10  | 10  |
| 1919 | 148 | 148 | 148 |
| 1920 | 118 | 118 | 118 |
| 1921 | 148 | 148 | 148 |
| 1922 | 159 | 159 | 159 |
| 2173 | 10  | 10  | 10  |

- Value spot-check (sensor 3833, style 238) = `CANONICAL_STD_BANDS` verbatim (i2x=2, i_open=10,
  open/clear/anchor times 0.08/0.14/0.08 … 0.35/0.50/0.32). Faithful propagation of EasyPower's own
  style-246 bands (datasheet-cross-checked, `MICROLOGIC-6.0A.md` [VENDOR-DOC]).

## Effect
The 593 band-less 6.0 sensors now serve STD/GFD delay from the DB band rows (self-describing); the §137
runtime canonical fallback is now dormant for them (identical curve). Idempotent — re-running is a no-op.
Reversible via `008_micrologic_60_bands_backfill_down.sql`.

**#71 DONE (applied).** Remaining queued prod-write packets: `009` PDG5, `010` PDG3/PDG6 (SST corrections).
