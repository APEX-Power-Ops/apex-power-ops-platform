# 2026-06-02 CC lvbreakertcc — TMT/EMT selectors → guided dropdown cascades (no free-text)

## Status

**Shipped.** Operator: "make the EMT and TMT sections dropdown selections, too hard for someone to come up
with verbiage." Both Screen-1 selectors now require **picking**, never typing.

## The problem

- **TMT** selector had a free-text **"Manufacturer filter"** `<input>` (class + frame were already dropdowns).
- **EMT** selector required typing a **≥2-char search** to discover frames before the frame/section dropdowns
  populated.

A field tech had to recall the exact manufacturer / frame verbiage.

## The fix

Two small read-only manufacturer-list endpoints + selector rewrites to manufacturer-dropdown cascades
(mirroring the ETU cascade). Manufacturer options show name + frame count (e.g. `Square D (38)`).

- **`GET /api/v1/neta/tmt/manufacturers?breaker_class=`** → `[{manufacturer_id, manufacturer_name, frame_count}]`
  (aggregation over the `_TMT_FACET_CTE` joined to `tcc.manufacturers`). Cascade: **class → manufacturer →
  frame** (`/tmt/frames?manufacturer_id`, frame fetch limit raised 12→200).
- **`GET /api/v1/neta/emt/manufacturers`** → same shape (over `tcc.emt_frames ⋈ tcc.emt ⋈ tcc.manufacturers`,
  via the EMT column-contract resolver). Cascade: **manufacturer → frame** (`/emt/frames?manufacturer_id`,
  `q` omitted) **→ section**. The debounced free-text search is removed.

Why endpoints (not client-side derive): TMT has ~101 manufacturers/class but the facets expose IDs only and the
frame fetch caps at 50/200, so deriving the full manufacturer list client-side was unreliable. The
selection/cross-filter *logic* is unchanged — only the selection *surface* (manufacturer axis enumerated
server-side instead of typed).

## Files

- `apps/control-plane-api/services/neta/schemas.py` — `ManufacturerFacetOption` + `TMT/EMTManufacturersResponse`.
- `apps/control-plane-api/services/neta/router.py` — `_load_tmt_manufacturers` / `_load_emt_manufacturers` + the
  two routes.
- `apps/operations-web/lib/breaker-resources.ts` — `fetchTmtManufacturers` / `fetchEmtManufacturers` + types;
  `fetchTmtFrames` / `fetchEmtFrames` gained a `limit` option.
- `apps/operations-web/app/lvbreakertcc/page.tsx` — `TmtSelector` + `EmtSelector` rewritten as dropdown cascades;
  removed the now-unused `useRef` import.

## Validation

- `py_compile` clean; **app imports + `/tmt/manufacturers` + `/emt/manufacturers` routes registered**;
  **61 route/trust tests pass** (settings + cascade + delay-trust — no regression). Frontend `tsc --noEmit` exit 0.
- Live: deploy + verify both dropdowns populate with real manufacturer names/counts and a pick flows to Screen 2.

## SSoT

- `reference/tcc/G3-ROUTING-GUIDE.md` §A1e — the guided-dropdown selection surface + the two new endpoints.
