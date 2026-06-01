# D1 SST-bridge loader — reproduction order

Generated bulk staging for migration `006_brk_styles_sst_bridge.sql` (the breaker→ETU
SST-bridge re-carry + 325-orphan repoint). Source: Access `D:\TCC_NEW.accdb` (read-only).
The `rank=id` mapping (Supabase `brk_*_styles.id` == Access `Breaker*Styles` row position
ordered by `ID` asc) is **proven** — see the closeout. All loads are integrity-checked by md5.

## Files
- `gen_d1_sql.ps1` — regenerates every `.sql` below from Access (ADODB, `Mode=Read`).
- `d1_04_triples_{iccb,pcb,mccb}.sql` — 431 distinct SST `(mfr,type,style)` triples → `tcc._stg_d1_triples`.
- `d1_05_sst_{iccb,mccb,pcb}.sql` — 5,412 `(style_id,triple_id)` assignments → `tcc._stg_d1_sst`.
- `d1_06_orphan.sql` — 325 orphan `(style_id → twin 4-tuple)` rows → `tcc._stg_d1_orphan`.
- `d1_90_srcid_{mccb,iccb,pcb}.sql` — **DEFERRED, un-applied** `source_id` population
  (rank=id array UPDATE). Apply only when source_id is wanted; not required by the bridge.
- `conn_test.py` / `.venv/` — one-off write-path probe (NOT committed; see `.gitignore`).

## Apply order (against governed Supabase, service-role / MCP)
1. `006_*.sql` part (A): add columns + create `tcc._stg_d1_*`.
2. Load: `d1_04_triples_*.sql`, then `d1_05_sst_*.sql`, then `d1_06_orphan.sql`.
3. `006_*.sql` part (C): the SST-carry + orphan-repoint UPDATEs + asserts.
4. `006_*.sql` part (D): `tcc.vw_breaker_sst_bridge` + drop the `_stg_d1_*` tables.

## Integrity hashes (verified on load, 2026-06-01)
- triples — iccb `7307e473…` · mccb `e84fdb37…` · pcb `1abb32bb…`
- sst     — iccb `14e56066…` · mccb `a38c9bd5…` · pcb `12bf85fb…`

## Acceptance (verified live)
- counts unchanged 10335/608/3279; **0 MCCB orphans**; `tmt_use_sst` = 1704/515/3193.
- bridge match-rates (non-null triples): **ICCB 100% / MCCB 95.6% / PCB 97.5%** (== Access live-join).
- `T8-1600` → `(ABB, PR332/P, MCCB-LSIG)` → trip_style 1226 → 3 sensors (deterministic narrowing).
