# dry_run_direct_access_population — Fidelity Report

**Path B, DRY-RUN ONLY.** Direct read-only Access -> disposable sandbox clone. Proves population LOGIC, not
production evidence custody. Governed frozen-snapshot custody (Path A) remains the prod-apply standard.

## Provenance / guardrails honored
- **Frozen source:** copy of `D:\TCC_NEW.accdb`, sha256 `c15adaefa57ed1bbc10d82c24842c5d9fc89e5d2b6992f50c0aeba764a59a16a`, 250,884,096 bytes (byte-identical to source). Read **read-only** via pyodbc `Mode=Read`.
- **Target:** disposable clone `tcc_breaker_d4d5_dryrun_20260627` (TEMPLATE of `tcc_breaker_baseline_20260625`), 029+030 DDL applied (both shape guards passed).
- **Hard guard:** the SQL refuses unless `current_database() LIKE '%dryrun%'`. Negative test PASSED — refused on `postgres` (`ERROR: GUARD OK: refused on postgres`).
- Nothing touched prod or the governed harness DBs.

## D4 re-carry (029) — ICCB/MCCB UPDATE by source_id
| class | styles | D4-updated (>=1 helper) | tmt_thermal non-null |
|---|---|---|---|
| ICCB | 608 | 608 | 492 |
| MCCB | 10335 | 10236 (99 have no helpers) | 8799 |
- Per-col non-null (ICCB / MCCB): tcc_number 608/10236, notes 608/10236, trip_plug 608/10236, breaker_type 608/10236, thermal_magnetic 608/10236, thermal 492/8799.
- Validated on clone: `iccb=608`, `mccb=10236` rows carry >=1 helper — matches generation exactly.

## D5 raw-carry (030) — all-3-class JSONB INSERT, keyed (breaker_class, source_id)
- **14,222 rows** (ICCB 608 + MCCB 10335 + PCB 3279); `distinct_pk = 14222` (no collisions); 2 CHECKs + composite PK hold.
- Block presence (non-null block = >=1 non-null Access col in that block):

| class | inst_override | ninst_override | brk_times | r_int | r_iec |
|---|---|---|---|---|---|
| ICCB | 608 | 608 | 143 | 608 | 4 |
| MCCB | 10335 | 10335 | 23 | 10333 | 4767 |
| PCB | 3279 | 3279 | 163 | 3279 | 1651 |
- `ovr_curves` always NULL (Breaker_OvrCurves empty in Access per G1; not read this dry-run).
- Spot-check PCB sid=46: inst_override 8 keys, r_int 9 keys — JSONB populated with verbatim Access keys.

## Override discriminator (the honest split: real override vs rating-only)
`InstOvrAmps` is the real-instantaneous-override signal; the rating blocks exist independently.

| class | total | real override (InstOvrAmps>0) | rating-only (InstOvrAmps NULL, r_int present) |
|---|---|---|---|
| ICCB | 608 | 241 | 367 |
| MCCB | 10335 | 129 | 10206 |
| PCB | 3279 | 317 | 2962 |

- **Codex review-333c08d3 fix VALIDATED:** an `InstOvrAmps>0` population filter would have dropped 367+10206+2962 = **13,535 rating-only rows**. The "any non-null block" rule correctly retains them.

## Finding -> one operator decision (HR1: what counts as a "real" override block is a behavioral call)
`inst_override` and `ninst_override` are non-null on **every** style — not because every style has a real override, but because Access defaults the byte-enum / tolerance columns (`InstOvrClrChar`, `InstOvrCurveCalcClr`, ...) to **0 (non-null)**, not NULL. So "any non-null block" == all 14,222 styles, and each no-override style carries a block of mostly default-zero values.

Two readings (operator's call):
- **(a) Maximal raw carry [current]** — preserve the raw block verbatim, default-zeros included. Most HR1-faithful (un-claimed; deciding "0 means no override" is itself interpretation). Cost: `inst_override IS NOT NULL` is not a meaningful "has-real-override" filter downstream (that signal lives in `InstOvrAmps` inside the block, preserved).
- **(b) Meaningfulness refinement** — carry `inst_override`/`ninst_override` only when `InstOvr/NInstOvrAmps` is non-null; no-override styles get the override block NULL but still carry via `r_int`/`r_iec` (rating-only retained). Cleaner downstream filter; but applies a (light) semantic judgment.

## Verdict
Population logic executes **faithfully and idempotently**: generated counts == loaded counts, PK/constraints/guard all hold, JSONB fidelity confirmed. Ready for a pre-apply Codex pass once the (a)/(b) inclusion-policy is settled.
