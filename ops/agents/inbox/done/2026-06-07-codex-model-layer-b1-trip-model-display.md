# Codex Packet — lvbreakertcc MODEL LAYER slice (b1): TRIP-UNIT model display wire-up (serving + frontend)

Lane: lvbreakertcc EP→ETAP nomenclature normalization, model layer, slice (b1) = trip-unit model NAMES.
The manufacturer layer + dup-consolidation + slice (a) downstream label-dedup are all shipped+live.

**CC has ALREADY persisted the prod table `tcc.trip_model_aliases` (LIVE).** This packet is the serving +
frontend wire-up only. **No prod write in this packet** (the table exists; do NOT re-apply DDL/seed to prod).

## Boundary / hygiene (read first)
- PUBLIC repo. NO secrets / client / job / site / person identifiers in committed artifacts. Mfr/model names + ids are library taxonomy and are fine.
- Scoped `git add` only. Git Bash heredoc for commit messages. Trailer at end.
- TDD required (tests first, red→green).

## The live prod table (already applied by CC via migration `create_tcc_trip_model_aliases_b1_seed`)
```
tcc.trip_model_aliases (
  trip_style_id integer primary key references tcc.trip_styles(id),
  etap_model    text not null,         -- the ETAP display name, e.g. 'MICROLOGIC 6.0', 'Digitrip 310+ (FD) LSIG'
  tier          text not null,         -- 'exact' | 'core'  (frame/none deliberately NOT persisted)
  provenance    text not null default '[ETAP Star Library List - published help docs] names-only crosswalk',
  created_at    timestamptz
)
```
- **826 rows, 1:1 (one ETAP model per trip_style_id).** exact 473 / core 353. Built from the v2 Star Library
  `trip_unit_crosswalk.tsv` exact+core rows, EXCLUDING the 15 rows that conflict with an existing authoritative
  alias (`agrees_with_existing_alias='no'`) — so this table never disagrees with `tcc.trip_style_aliases`.
- Spot-checks: trip_style_id 238 → `MICROLOGIC 6.0`; 871 → `STR53UP`.

## Existing authoritative overlay (do NOT modify)
`tcc.trip_style_aliases` (803 rows, 123 distinct trip_style_id, MULTI-ROW per style; cols: alias_id,
trip_style_id, alias_name, alias_mfr, match_tier['exact'|'core'|'frame'], match_basis, n_candidates,
provenance). This is the public-catalog authoritative source (#77/#79) and **wins over trip_model_aliases**.

## Serving resolution — `trip_model_display`
For each trip-unit cascade row (keyed by trip_style_id), compute:
```
trip_model_display = COALESCE(
  <preferred-pick from tcc.trip_style_aliases WHERE match_tier IN ('exact','core')>,  -- authoritative, withhold 'frame'
  tcc.trip_model_aliases.etap_model,                                                  -- v2 Star Library gap-fill
  <EP raw trip style/type>                                                            -- fallback
)
```
- **Preferred-pick from `trip_style_aliases`** (multi-row): per trip_style_id pick ONE row — order by
  `match_tier` (exact before core; **exclude frame entirely**), then a deterministic tie-break (e.g. lowest
  `alias_id`). Implement as a window function / lateral, not app-side.
- Expose `trip_model_display` additively on the trip-unit level response model(s) in
  `apps/control-plane-api/services/neta/schemas.py`. Keep the raw EP fields for back-compat.
- Coverage: ~881 / 2095 trip styles resolve to an ETAP display; the rest fall back to EP (expected).

## Re-key the slice-(a) trip dedup on the display
Slice (a) dedups the trip-type/style level by the raw label and unions `style_ids`/`trip_type_ids`. **Re-key that
dedup to group by `trip_model_display`** (the normalized name) instead of the raw EP label. Effect:
- two raw EP styles that normalize to the SAME ETAP model collapse into one option (unioned style_ids);
- options that resolve to DIFFERENT ETAP models stay distinct.
This is the trip-axis analogue of the divergence resolution. (The ETU trip-type divergence was tiny — ITE (BBC)
`Power Shield` ×2 — so the visible change here is small, but wire the re-key generically.)

## Files (confirm by reading)
- Backend `apps/control-plane-api/services/neta/router.py`: the ETU trip cascade level (`get_cascade` ~L3681 /
  `_cascade_level` ~L2178) — add the resolution + re-key. Thread `trip_model_display` through to the response.
- Schemas `apps/control-plane-api/services/neta/schemas.py`: add `trip_model_display: Optional[str]`.
- Frontend `apps/operations-web/app/lvbreakertcc/page.tsx` (trip-unit/model dropdown) + types in
  `lib/breaker-resources.ts`: render `trip_model_display ?? <existing EP label>`; add the TS field.
- Repo migration RECORD: create `infra/database/migrations/tcc/014_tcc_trip_model_aliases.sql` (+ `_down`)
  recording the live table. The exact applied SQL is in `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/_trip_model_aliases_seed.sql`
  (host-local, gitignored) — copy its content verbatim into 014 as the record. **Mark it as already-applied to
  prod (do NOT re-run against prod).**

## TDD — write first (red), then implement (green)
New backend test file e.g. `apps/control-plane-api/tests/test_neta_trip_model_display_routes.py`:
1. A trip-unit cascade row for trip_style_id 238 has `trip_model_display == 'MICROLOGIC 6.0'`; 871 → `STR53UP`.
2. A trip_style_id present in `trip_style_aliases` at exact/core tier shows the AUTHORITATIVE alias (not the
   trip_model_aliases value) — pick a style that exists in both and differs; assert authoritative wins.
3. A trip_style_id with NO alias and NO trip_model_aliases row falls back to the EP label.
4. `frame`-tier-only existing aliases are NOT shown (withheld) — fall through to trip_model_aliases or EP.
5. Re-key dedup: two EP styles normalizing to the same `trip_model_display` under one manufacturer collapse to one
   option with unioned style_ids.
Frontend: `pnpm --filter @apex/operations-web typecheck` + `build` pass.

## Out of scope
- Breaker model names = slice (b2), a separate packet.
- Manufacturer axis, relay endpoints, EMT/TMT model names beyond the trip-unit cascade level handled here.
- Any prod DDL/data change (table is already live).

## Validation + deploy + deliverables
1. TDD as above; focused + adjacent backend suites green; `compileall`; frontend typecheck + build.
2. Non-env regression subset with `-m "not integration"`; report pass count.
3. Deploy: push to main (admin bypass; verify `git status -sb` in-sync); confirm Vercel prod READY; hosted browser
   check on `https://operations.apexpowerops.com/lvbreakertcc`: select a manufacturer with normalized trips (e.g.
   Square-D) and confirm the trip-unit dropdown shows ETAP model names (e.g. `MICROLOGIC 6.0`) instead of raw EP.
4. Independently re-verify the deployed API: the ETU cascade returns `trip_model_display` and 238→`MICROLOGIC 6.0`.
5. Closeout to `ops/agents/handoffs/2026-06-07-model-layer-b1-trip-model-display-closeout.md`: commits, TDD
   red→green, the count of trip rows now showing an ETAP display vs EP fallback, any trip-axis dedup change, and
   surprises. Then `git mv` this packet pending→done and push.

## Commit hygiene
Scoped `git add`; Git Bash heredoc; end every commit message with:
```
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```
