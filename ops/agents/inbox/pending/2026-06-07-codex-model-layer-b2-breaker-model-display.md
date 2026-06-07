# Codex Packet — lvbreakertcc MODEL LAYER slice (b2): BREAKER model display wire-up (serving + frontend)

Lane: lvbreakertcc EP→ETAP nomenclature normalization, model layer, slice (b2) = breaker frame/model NAMES.
Manufacturer layer + dup-consolidation + slice (a) dedup + slice (b1) trip-model display are all shipped+live.

**CC has created + is seeding the prod table `tcc.breaker_style_aliases` (LIVE).** PCB rows (895) are already in.
MCCB (2,391) + ICCB (174) rows are being added by CC as separate governed writes — **wire all three classes now;
the MCCB/ICCB names light up automatically when their rows land (serving reads the table live, no redeploy).**
**No prod write in this packet.**

## Boundary / hygiene (read first)
- PUBLIC repo. NO secrets/client/job/site/person identifiers. Mfr/model names + ids are library taxonomy, fine.
- Scoped `git add`; Git Bash heredoc for commit messages; trailer at end. TDD required (tests first).

## The live prod table (created by CC; PCB seeded via `create_tcc_breaker_style_aliases_pcb_seed`)
```
tcc.breaker_style_aliases (
  breaker_class    text not null check (breaker_class in ('MCCB','ICCB','PCB')),
  breaker_style_id integer not null,    -- = tcc.brk_<class>_styles.id
  etap_model       text not null,       -- the ETAP display, e.g. 'NW12H1', 'M12 H1', 'DSII-308'
  tier             text not null,       -- 'exact' | 'core'  (frame/none NOT persisted)
  provenance       text not null,
  created_at       timestamptz,
  primary key (breaker_class, breaker_style_id)
)
```
- **Composite key `(breaker_class, breaker_style_id)`** — breaker style ids COLLIDE across the three breaker
  tables, so you MUST join with both the class literal and the id: e.g. for PCB,
  `join tcc.breaker_style_aliases a on a.breaker_class='PCB' and a.breaker_style_id = s.id` where `s` is
  `tcc.brk_pcb_styles`. Same pattern for MCCB→`brk_mccb_styles`, ICCB→`brk_iccb_styles`.
- 1:1 (one ETAP model per style). exact+core only. There is **NO existing breaker alias overlay** (unlike the
  trip layer's `trip_style_aliases`) — so resolution is just the table → EP fallback.
- Verify-data spot checks (PCB): `brk_pcb_styles.id` 19 → `75HL-3`; 3125 → `NW12H1`; 2370 → `M12 H1`.

## Serving resolution — `breaker_model_display`
For each breaker/frame cascade row (keyed by breaker class + brk_<class>_styles.id):
```
breaker_model_display = COALESCE(tcc.breaker_style_aliases.etap_model, <EP raw frame>)
```
- The EP raw frame is `brk_<class>_styles.frame` (e.g. `30HL-3 (600A)`).
- Expose `breaker_model_display` additively on the relevant breaker/frame response models in
  `apps/control-plane-api/services/neta/schemas.py`. Keep raw EP fields for back-compat.

## Re-key the slice-(a) frame dedup on the display — THIS resolves the TMT frame divergence
Slice (a) dedups the TMT frame-label level (and ETU breaker level) and reported high `dedupe_divergence_count`
(same EP frame label across unioned mfr ids carrying divergent downstream data: TMT MCCB LSIS 141, Fuji 97,
ABB 78, Square-D 73; TMT PCB Square-D 90, ITE 34, ...). **Re-key those dedups to group by
`(manufacturer_display, breaker_model_display)`** instead of the raw EP frame label:
- frames that normalize to the SAME ETAP model collapse (unioned style_ids) — confirmed same product;
- frames that normalize to DIFFERENT ETAP models re-split — were a false merge.
Report the new divergence count per surface (should drop sharply on PCB now; on MCCB after CC seeds it).

## Files (confirm by reading)
- Backend `apps/control-plane-api/services/neta/router.py`:
  - ETU breaker cascade `get_etu_breaker_cascade` (~L3949) / `_etu_breaker_cascade_level` (~L2473) — breaker/frame level.
  - TMT frame labels `_load_tmt_facets` (~L2992) / `get_tmt_facets` (~L4496).
  - EMT path (~L3303/L4809) IF it surfaces breaker frames; else leave.
  - Thread `breaker_model_display` through; re-key the frame dedup. Implement the 3-class join generically
    (dispatch on the cascade's breaker class to the right brk_<class>_styles table + class literal).
- Schemas `apps/control-plane-api/services/neta/schemas.py`: add `breaker_model_display: Optional[str]`.
- Frontend `apps/operations-web/app/lvbreakertcc/page.tsx` (breaker/frame dropdowns) + `lib/breaker-resources.ts`:
  render `breaker_model_display ?? <EP frame>`; add the TS field.
- Repo migration RECORD: `infra/database/migrations/tcc/015_tcc_breaker_style_aliases.sql` (+ `_down`) recording
  the table + PCB seed. The applied SQL is in
  `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/_breaker_style_aliases_pcb_seed.sql` (host-local,
  gitignored) — copy verbatim. **Mark already-applied to prod (do NOT re-run).** Note in the file that MCCB/ICCB
  seeds are separate CC migrations into the same table.

## TDD — write first (red), then implement (green)
New backend test file e.g. `apps/control-plane-api/tests/test_neta_breaker_model_display_routes.py`:
1. A PCB breaker/frame cascade row for `brk_pcb_styles.id` 3125 has `breaker_model_display == 'NW12H1'`; 2370 → `M12 H1`; 19 → `75HL-3`.
2. A PCB style with NO alias row falls back to the EP `frame`.
3. Composite-key correctness: an MCCB and a PCB sharing the same numeric `breaker_style_id` resolve independently
   (no cross-class leakage) — assert a PCB id resolves to its PCB model and the same numeric id under MCCB does NOT
   pick up the PCB value.
4. Frame dedup re-key: two PCB frames under one manufacturer that normalize to the same `breaker_model_display`
   collapse to one option with unioned style_ids; different models stay split.
Frontend: `pnpm --filter @apex/operations-web typecheck` + `build` pass.

## Out of scope
- Trip-unit model names (slice b1, done). Relay endpoints. Any prod DDL/data change (CC owns the table+seeds).

## Validation + deploy + deliverables
1. TDD as above; focused + adjacent backend suites green; `compileall`; frontend typecheck + build.
2. Non-env regression subset with `-m "not integration"`; report pass count.
3. Deploy: push to main (admin bypass; `git status -sb` in-sync); Vercel prod READY; hosted browser check on
   `https://operations.apexpowerops.com/lvbreakertcc`: select a PCB-bearing manufacturer (e.g. Square-D) on the
   TMT/ETU breaker axis and confirm frame options show ETAP models (e.g. `NW12H1`, `MTZ2 16H1`) instead of raw EP
   frames, with fewer duplicate frame labels.
4. Independently re-verify the deployed API: a PCB breaker/frame row returns `breaker_model_display` (3125→`NW12H1`).
5. Closeout to `ops/agents/handoffs/2026-06-07-model-layer-b2-breaker-model-display-closeout.md`: commits, TDD
   red→green, count of breaker/frame rows now showing an ETAP display vs EP fallback (note PCB-only until MCCB/ICCB
   seeded), the new per-surface frame `dedupe_divergence_count` (vs the slice-a baseline), and surprises. Then
   `git mv` this packet pending→done and push.

## Commit hygiene
Scoped `git add`; Git Bash heredoc; end every commit message with:
```
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```
