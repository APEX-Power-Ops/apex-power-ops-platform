---
topic: r_cont_current rating-narrow (#75 / STATE §145)
status: DONE (applied + verified)
applied_by: CC
applied_at: 2026-06-04
mechanism: Supabase apply_migration (governed prod fxoyniqnrlkxfligbxmg); execute_sql read-only for verification
---

# CLOSEOUT — SST-bridge r_cont_current rating-narrow APPLIED + verified

Operator-authorized ("proceed as outlined"). Carried the breaker-style continuous rating
(Access `r_cont_current`) onto the governed store and narrowed the SST bridge to the ONE sensor
matching the breaker — the §138 residual ("even a correct mapping surfaces the whole style set").

## Governed writes (apply_migration; reviewed migration artifacts committed)
- **011** (`011_brk_rcont_current_backfill.sql`): `ALTER TABLE ADD COLUMN r_cont_current numeric` on
  `tcc.brk_{mccb,pcb,iccb}_styles`, then populate the **5412 bridged rows** (`tmt_use_sst`) from Access
  joined on `source_id` (= Access ID, the §104 rank=id key). Applied in 4 chunks (DDL + per-class), the
  §104 chunked-apply precedent. **Integrity: id-weighted checksum matched Access exactly per class** —
  mccb n=1704 Σrcc=1,453,944 Σ(id·rcc)=70,115,445,313 · pcb n=3193 Σrcc=7,120,515 Σ(id·rcc)=66,946,942,860 ·
  iccb n=515 Σrcc=1,114,700 Σ(id·rcc)=42,210,215,700. Zero corruption. Reversible (`_down` drops the columns).
- **012** (`012_bridge_view_rcont_current.sql`): `CREATE OR REPLACE VIEW tcc.vw_breaker_sst_bridge` to
  append `r_cont_current` (column appended last — CREATE OR REPLACE forbids reordering). Additive; existing
  consumers unaffected. Reversible (`_down` restores the 006 view).

## Serving (control-plane-api, TDD)
- `narrow_bridge_sensors_by_rating(sensors, r_cont_current)` (`services/neta/router.py`) — **safe by
  construction**: returns only sensor(s) whose `sensor_rating == r_cont_current`; if rating is NULL or no
  exact match, returns the full set (never hides the right sensor). 7 TDD tests (`test_bridge_rating_narrow.py`).
- `/etu/bridge-sensors` narrows per breaker-style group and returns `breaker_rating` + `rating_narrowed`.

## Coverage (measured in prod after the backfill — 4382 bridged rows, all now carry rcc)
- **3054** narrow to exactly one sensor (the win) · **699** narrow to a subset (duplicate ratings) ·
  **143** single-sensor styles (already singular) → **~3896 (89%) narrowed or already-singular**.
- **127** in-range no-exact + **230** out-of-range (the #74 rating-mismatch set, needs per-mfr docs) +
  **129** dangling (empty bridge) → fall back safely to the full set (never hidden).

## Live verify
- View: PDG5-K PXR 800A (style 8774) → all sensors [800,1200,1600], **narrowed_to [800]**. Combined with the
  §144 SST correction, an 800 A PDG5 breaker now surfaces exactly the 800 A sensor (was 60–225 A pre-arc).
- Tests: 22 green (7 narrow + 15 pxr); existing `test_etu_bridge_sensors_route.py` 5/5 (no regression).

**Frontend:** the narrow is server-side, so the page already shows the narrowed set; the new `rating_narrowed`
/`breaker_rating` fields are optional UI niceties (a "narrowed to N A" note), not required for the benefit.
