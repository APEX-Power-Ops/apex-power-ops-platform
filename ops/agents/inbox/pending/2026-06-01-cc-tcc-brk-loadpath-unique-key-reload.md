---
dispatch_id: 2026-06-01-cc-tcc-brk-loadpath-unique-key-reload
target: CC
priority: 3
from: Desktop
created_at: 2026-06-01
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-06-01-tcc-brk-loadpath-unique-key-reload-closeout.md
---

# Widen the breaker unique key + reload the 41 dropped MCCB AC/DC twins (lean 2) — companion to the SST-bridge (D1) reload

**Lane:** TCC Master Reference — breaker load-path correction. **Spec of record:** `reference/tcc/G1-SCHEMA-GUIDE.md` §5 (load-delta register, the `brk_mccb` 599-vs-640 entry) + dropped-column register D1/D4; `reference/tcc/G2-RULES-GUIDE.md` **§4.6** (this finding) + **§4.3 / BG-1..BG-5** (the sibling SST-bridge gap). **This is the reload deferred by §98 lean 2** (characterization landed 2026-06-01). **Natural companion to the SST-bridge (D1) reload — both re-touch the `brk_*` load path; coordinate them.** Cite + fix the guides first per the SSoT Law.

## Why
`tcc.brk_mccb` carries **599** of Access `BreakerMCCB`'s **640** rows. Root cause (verified live 2026-06-01, G2 §4.6): the governed table has `UNIQUE (manufacturer_id, name)`, but the Access natural key is the **4-tuple `(Mfr_ID, Type, cStandard, Acdc)`** (0 dups there). 43 `(Mfr_ID, Type)` pairs have a twin differing **only by `Acdc` (AC↔DC)** and/or `cStandard` (ANSI↔IEC) — e.g. ABB `Formula`/`Tmax [IEC]`, GE `E100`, Siemens `Sentron` — collapsed by the too-narrow index. (41, not 43: 2 case-only twins `Multi 9`/`MULTI 9`, `ComPact [IEC]`/`COMPACT [IEC]` survive because Postgres unique is case-sensitive.) `brk_iccb` (29→29) and `brk_pcb` (157→157) loaded fully today but carry the **same latent risk** (same too-narrow index). `manufacturer_id` is preserved 1:1 — this is **not** the D1 name-vs-id drop.

## Do
1. **Claim** (git mv pending→claimed, push) before starting.
2. **Widen the unique key** on `tcc.brk_{mccb,iccb,pcb}` from `(manufacturer_id, name)` → **`(manufacturer_id, name, standard, ac_dc_code)`** via a migration (drop the old `*_manufacturer_id_name_key`, add the 4-col unique). Confirm no *other* collisions appear at the wider key (Access proved the full 4-tuple unique).
3. **Reload the dropped twins** from Access `BreakerMCCB` (read-only, `Microsoft.ACE.OLEDB.16.0`, `D:\TCC_NEW.accdb`): insert the 41 rows whose `(Mfr_ID, Type, cStandard, Acdc)` is absent in `tcc.brk_mccb`, mapping `Acdc`→`ac_dc_code`, `cStandard`→`standard`, `Type`→`name`, `Mfr_ID`→`manufacturer_id` (the IDs are preserved 1:1). Use a fresh surrogate `id`.
4. **Verify completeness:** `tcc.brk_mccb` = **640** (and iccb/pcb still 29/157); each Access 4-tuple now present exactly once.
5. **Coordinate with the SST-bridge (D1) reload** if that lane runs in the same packet: the D1 fix re-carries `tmt_use_sst`/`tmt_sst_{mfr,type,style}` onto `brk_*_styles` + a new bridge surface (G2 §4.3, BG-4). Both touch the `brk_*` load — do them together if possible to avoid two reloads. (This dispatch is independently executable if D1 is not yet ready.)
6. **Guide updates first (SSoT Law):** G1 §5 load-delta entry → CLOSED (640/640) + the widened key documented; G2 §4.6 → CLOSED; note the iccb/pcb latent-risk now removed by the wider key.

## Acceptance
- `tcc.brk_mccb` = 640 (all Access 4-tuples present, none duplicated); `brk_iccb`/`brk_pcb` unchanged at 29/157; new 4-col unique key live on all three.
- The breaker explorer still resolves correctly (the AC/DC twins now selectable by `ac_dc_code`); no regression to the `/cascade` + ETU/TMT surfaces.
- G1 §5 + G2 §4.6 updated to CLOSED per the SSoT Law.

## Guardrails
- **Authorized governed-Supabase write** (migration + a bounded INSERT of the 41 rows) — this is squarely the lean-2 remediation. Access opened **read-only**. The governed `tcc.*` posture is now public-read/service-write (G2 §4.7) — writes go via service-role/migration.
- Scoped `git add`. DSN/service key out-of-band; no `.env*` contents; PUBLIC repo — no client/job identifiers, no project ref/keys in the dispatch trail.

## Closeout
Record: the widened-key migration, the 41 reloaded rows (by manufacturer/type), the 640/640 verification, any explorer re-check, commit hash(es), and the guide sections amended. Then `git mv` claimed→done, commit, push. **Note:** if bundled with the D1 SST-bridge reload, reference that closeout.
