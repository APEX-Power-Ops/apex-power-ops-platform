# Codex Packet — lvbreakertcc manufacturer DUP-CONSOLIDATION (serving + frontend, no DB change)

Lane: lvbreakertcc EP→ETAP nomenclature normalization. Manufacturer DISPLAY layer is already shipped + live
(`tcc.mfr_aliases`, `manufacturer_display = COALESCE(etap_mfr_name, raw_name)` on the four selector paths).
This packet is the next increment: **collapse the EP duplicate-manufacturer ids that now share one display
name into a single dropdown entry that filters to ALL underlying ids.** Display-name normalization
intentionally created duplicate-looking labels (e.g. three "Square-D" rows = EP ids SQD/Square D/SquareD).

## Boundary / hygiene (read first)
- This is the PUBLIC repo `apex-power-ops-platform`. NO secrets, NO client/job/site/person identifiers in any
  committed artifact. The manufacturer names + ids below are library taxonomy and are fine to commit.
- Scoped `git add` only (never `-A`). Commit message ends with the Co-Authored-By trailer (see end).
- **NO database change.** No prod DDL, no migration, no prod write. The `tcc.mfr_aliases` table already supplies
  the display. This is purely serving-layer aggregation + frontend.
- TDD is required (tests first, red→green). Do not write production code before a failing test.

## Approach (decided — do NOT mutate EP identity)
Serving/UI-layer consolidation. Group the manufacturer-LIST endpoints by `manufacturer_display`, return the set
of underlying EP `manufacturer_id`s, and make the downstream cascade/facet filters accept a list of ids
(`manufacturer_id = ANY(:ids)`). EP `manufacturer_id` stays the immutable key. **Do NOT** merge/reassign rows in
`tcc.manufacturers` or any device table — the EP ids (SQD vs Square D vs SquareD) are genuinely distinct EP
records; this is a display concern only and must stay fully reversible.

## Authoritative duplicate map (global, from prod `tcc.manufacturers` ⋈ `tcc.mfr_aliases`)
12 display names map to multiple EP ids. Group DYNAMICALLY by display (do NOT hardcode these ids in code —
this table is for your tests/acceptance only):

| display | EP ids | EP raw names |
|---|---|---|
| ABB | 1, 43 | ABB, SACE |
| Allis-Chalmers | 2, 85 | Allis Chalmer, Allis-Chalmers |
| Cutler-Hammer | 28, 41 | Cutler-Hammer, Cutler Hammer |
| Federal Pacific | 8, 118 | Fed Pacific, Federal Pacific |
| Fuji | 46, 102 | Fuji, Fuji America |
| ITE (BBC) | 4, 11, 125, 173 | Brown Boveri, ITE, BBC, Gould |
| L&T | 253, 358 | Larsen & Toubro, L&T |
| LSIS | 192, 303, 304 | LS Industrial, LSIS, LG Industrial |
| Siemens-Allis | 16, 33 | Siemens Allis, Siemens-Allis |
| Square-D | 17, 35, 235 | SQD, Square D, SquareD |
| SYLVANIA | 149, 395 | Sylvania, GTE/Sylvania |
| Westinghouse | 18, 36 | West, Westinghouse |

Per-family membership is a subset (an id only appears in a dropdown if it has devices in that family). Group by
display generically so every case is handled wherever it surfaces.

## Design contract

### 1. Manufacturer-LIST endpoints (the four selector dropdowns) — CONSOLIDATE
Endpoints (in `apps/control-plane-api/services/neta/router.py`):
- `get_cascade` (~L3681) — ETU trip-unit cascade manufacturer level
- `get_etu_breaker_cascade` (~L3949) — ETU breaker manufacturer level
- `get_tmt_manufacturers` (~L4562) via `_load_tmt_manufacturers` (~L4524); also `get_tmt_facets`/`_load_tmt_facets`
- `get_emt_manufacturers` (~L4865) via `_load_emt_manufacturers` (~L4831); also `get_emt_facets`/`_load_emt_facets`

For each, where the response currently returns one row per `manufacturer_id`, GROUP BY `manufacturer_display` and return one row per display with:
- `manufacturer_display` — the label (unchanged field)
- `manufacturer_ids: list[int]` — NEW, sorted, all underlying EP ids for this display **in this family**
- `manufacturer_id: int` — KEEP, = `min(manufacturer_ids)` (representative, for back-compat)
- `manufacturer_name: str` — KEEP, the raw name of the representative id (back-compat; frontend renders display)
- the count field — = SUM of the per-id device counts (this equals the union count because every device row has
  exactly one `manufacturer_id`; there is no overlap, so summing is correct — verify this in a test).

Add `manufacturer_ids: Optional[list[int]]` to the relevant Pydantic response models in
`apps/control-plane-api/services/neta/schemas.py` (the same models that received `manufacturer_display`:
CascadeManufacturer, EtuBreakerManufacturer, ManufacturerFacetOption — confirm exact set).

### 2. Downstream cascade/facet filters — ACCEPT MULTIPLE ids
Wherever a chosen manufacturer narrows the NEXT level (trip-unit list, breaker-style list, sensors, facet
counts), accept a `manufacturer_ids` list param and filter `manufacturer_id = ANY(:ids)`. Touch the where-builders:
`_build_cascade_where` (~L2156), `_build_etu_breaker_cascade_where` (~L2437), `_build_tmt_facet_where` (~L2963),
and the EMT facet/where path (~L3303/L4809). Keep single `manufacturer_id` working (treat a lone id as a 1-element
list; if both arrive, the list wins). Use the house style for list query params (repeated `?manufacturer_ids=..`
FastAPI `Query(default=None)` is fine — match whatever the codebase already does if there's precedent).

### 3. Dual-axis cross-filter — thread id-sets on BOTH axes
The bridge-aware dual-axis cross-filter (trip-unit axis ⋈ breaker axis) currently cross-filters by a single
manufacturer_id per axis. It must now accept an id-SET per axis and cross-filter with `= ANY`. This is the
trickiest area — add explicit tests for: selecting a consolidated manufacturer on one axis correctly cross-filters
the other axis to the union.

### 4. Frontend (`apps/operations-web/app/lvbreakertcc/page.tsx`, types in `lib/breaker-resources.ts`)
- Render one dropdown option per `manufacturer_display` (already the label).
- The selected-manufacturer state must carry the id-SET (`manufacturer_ids`), not a single id. On select, pass the
  id-set to all downstream cascade/facet calls.
- TS types: add `manufacturer_ids?: number[]` to the manufacturer item types.
- Keep the rest of the cascade behavior identical.

## TDD — write these tests first (red), then implement (green)
Backend (`apps/control-plane-api/tests/`), new file e.g. `test_neta_manufacturer_dup_consolidation_routes.py`:
1. **Consolidation**: ETU breaker-cascade manufacturer list contains exactly ONE "Square-D" row, with
   `manufacturer_ids == [17,35,235]` (intersected with ids actually present in that family) and `manufacturer_id == 17`.
   Add an ITE (BBC) assertion (ids ⊆ {4,11,125,173}) and an ABB assertion (ids ⊆ {1,43}).
2. **Count = union**: the consolidated Square-D count equals the sum of the per-id counts (and equals the count of
   the downstream union).
3. **Downstream union filter**: the breaker cascade filtered by `manufacturer_ids=[17,35,235]` returns the union of
   the three ids' styles, and ≥ what any single id returns alone.
4. **Back-compat**: a single `manufacturer_id=17` still returns SQD-only results (unchanged behavior).
5. **Dual-axis**: selecting a consolidated manufacturer on one axis cross-filters the other axis to the union.
6. Mirror a consolidation assertion for TMT (MCCB) and for the ETU trip cascade.
Frontend: `pnpm --filter @apex/operations-web typecheck` and `build` pass.

### Acceptance matrix (verify each collapses to ONE entry; from the live deployed UI before this change)
- ETU **trip**: ABB, ITE (BBC), LSIS
- ETU **breaker**: ABB, Cutler-Hammer, Federal Pacific, Fuji, ITE (BBC), LSIS, Square-D, Westinghouse
- TMT **MCCB**: ABB, Cutler-Hammer, Federal Pacific, Fuji, ITE (BBC), LSIS, Square-D, Westinghouse
- TMT **PCB**: ITE (BBC), Square-D
- TMT ICCB / EMT: none observed (but the generic group-by must not regress them)

## Out of scope (do NOT do here)
- The MODEL axis (trip-unit / breaker model names) — that is the next, separate increment.
- Downstream MODEL de-duplication: after the union, the same model name may appear under two merged ids. DO NOT
  build model-dedup here. Instead **MEASURE and REPORT** in the closeout whether any downstream model dups appear
  per family (counts), so the model-layer step can absorb it.
- Relay endpoints (`get_relay_manufacturers`/`get_relay_facets`, ~L5027/L5037) — Relay is its own lane. Leave alone.
- Any DB schema/data change.

## Validation + deploy + deliverables
1. TDD as above; full focused backend suite green; `compileall`; frontend typecheck + build.
2. Run the non-env regression subset (as in the prior packet) and report pass count.
3. Deploy: push to main (admin-bypass; verify `git status -sb` in-sync), confirm the Vercel prod deployment READY,
   and do a focused hosted browser check on `https://operations.apexpowerops.com/lvbreakertcc`: confirm Square-D,
   ITE (BBC), ABB, Cutler-Hammer appear ONCE in the relevant dropdowns and selecting Square-D returns the unioned
   downstream list.
4. Independently re-verify the deployed API: `/api/v1/neta/etu/breaker-cascade` shows a single Square-D with
   `manufacturer_ids:[17,35,235]`.
5. Write a closeout to `ops/agents/handoffs/2026-06-06-mfr-dup-consolidation-closeout.md`: commits, TDD red→green
   evidence, the per-family before/after dropdown-row counts, the measured downstream model-dup counts (out-of-scope
   but reported), and any surprises. Then `git mv` this packet pending→done and push.

## Commit hygiene
- Scoped `git add` of only the files you changed. Bash heredoc for the commit message (NOT PowerShell `@'...'@`).
- End every commit message with:

```
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```
