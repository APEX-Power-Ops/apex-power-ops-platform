---
dispatch_id: 2026-06-06-codex-mfr-display-serving-wireup
target: CODEX
priority: 1
from: CC
created_at: 2026-06-06
authority: gated
predecessor: 2026-06-06-codex-ep-etap-nomenclature-crosswalk-v2-starlib
closeout: ops/agents/handoffs/2026-06-06-mfr-display-serving-wireup-closeout.md
---

# Wire recognizable manufacturer names into the lvbreakertcc selectors (manufacturer layer)

**Lane:** lvbreakertcc · nomenclature normalization · serving wire-up (manufacturer layer).
**Type:** App code change (backend + frontend) + tests + deploy. **TDD: tests first.** No prod DDL (the data is already live).
**Prereq:** the seed table `tcc.mfr_aliases` (53 rows) is **already applied to prod** by CC. Confirm `select count(*) from tcc.mfr_aliases;` = 53 before starting; if not, stop and report.

## Goal
The lvbreakertcc manufacturer dropdowns currently show the raw EasyPower name (`GE`, `West`, `Cutler Hammer`, `SQD`, `Schneider`…). Surface the recognizable ETAP-equivalent name (`General Electric`, `Westinghouse`, `Cutler-Hammer`, `Square-D`, `Schneider Electric`…) by joining `tcc.mfr_aliases` and exposing an **additive** `manufacturer_display` field. EP `manufacturer_id` stays the selection key; raw `manufacturer_name` stays in the payload. Frontend renders `manufacturer_display ?? manufacturer_name`.

## The data (already live)
`tcc.mfr_aliases (ep_mfr_id int PK -> tcc.manufacturers(id), ep_mfr_name text unique, etap_mfr_name text, tier, match_basis, provenance, created_at)` — 53 rows, 25 of them real relabels (e.g. GE->General Electric, West->Westinghouse, Schneider->Schneider Electric, Square D/SQD/SquareD->Square-D, Cutler Hammer->Cutler-Hammer, ITE/BBC/Brown Boveri/Gould->"ITE (BBC)", LS/LG Industrial->LSIS, SACE->ABB, Larsen & Toubro->L&T, Satin American->satinAMERICAN). Manufacturers absent from this table = no ETAP equivalent -> fall back to EP name.

## Backend (`apps/control-plane-api/services/neta/`)
The normalization is one pattern everywhere: **LEFT JOIN `tcc.mfr_aliases a ON a.ep_mfr_name = <the mfr-name column>`** and select **`COALESCE(a.etap_mfr_name, <mfr name>) AS manufacturer_display`**. Add `manufacturer_display: Optional[str] = None` to the relevant Pydantic models in `schemas.py`. Wire these four manufacturer-list paths:

1. **ETU trip-unit cascade** — `get_cascade` (`/cascade`), the manufacturer rows query (`router.py` ~L3747-3764, `v.manufacturer_name`). Schema: `CascadeManufacturer`.
2. **Breaker axis** — `get_etu_breaker_cascade` (`/etu/breaker-cascade`) manufacturer rows (the `etu_breaker_combined`/brk-styles manufacturer query, `m.mfr_name`). Schema: `EtuBreakerManufacturer`.
3. **TMT** — `_load_tmt_manufacturers` (`router.py` ~L4520-4551, `m.mfr_name`). Schema: `ManufacturerFacetOption` (drives `/tmt/manufacturers` + `/tmt/facets`).
4. **EMT** — the EMT manufacturer loader(s) (`router.py` ~L3269/3382/3570, `m.mfr_name`). Schema: `ManufacturerFacetOption`.

`ManufacturerFacetOption` is shared by TMT + EMT — adding the field once covers both. The join key is the manufacturer **name** (`mfr_name`); `tcc.mfr_aliases.ep_mfr_name` is unique, so the join is 1:1. Where a query already aliases `m.mfr_name AS manufacturer_name`, join `mfr_aliases` on `m.mfr_name` (or `v.manufacturer_name`). Keep `GROUP BY` valid (add `a.etap_mfr_name` to GROUP BY where the manufacturer rows are grouped).

**(Optional, lower priority)** `/etu/bridge-sensors` (`EtuBridgeSensorsResponse.manufacturer_name`, which reflects `tmt_sst_mfr`): you may also surface `manufacturer_display` there via the same join on `tmt_sst_mfr = a.ep_mfr_name`. If it complicates the bridge query, skip and note it.

## Frontend (`apps/operations-web/app/lvbreakertcc/page.tsx`)
Four dropdown-label spots use `m.manufacturer_name`; change each to prefer the display name:
- L471 breaker mfr: `` `${m.manufacturer_display ?? m.manufacturer_name} (${m.breaker_count})` ``
- L476 trip-unit mfr: `` `${m.manufacturer_display ?? m.manufacturer_name} (${m.trip_type_count})` ``
- L596-597 TMT mfr: `` `${m.manufacturer_display ?? m.manufacturer_name ?? `Mfr ${m.manufacturer_id}`} (${m.frame_count})` ``
- L688-689 EMT mfr: same pattern.
Update the corresponding TypeScript types (the manufacturer option types) to include `manufacturer_display?: string | null`. Selection value stays `manufacturer_id`.

## TDD (tests first)
Before implementing, add failing tests, then make them pass. Mirror the existing live-integration style (`tests/test_neta_tmt_live_integration.py`, `tests/test_etu_bridge_sensors_route.py`). Assert, per wired endpoint:
- a known **relabel** maps correctly — e.g. the cascade manufacturer row for EP `GE` has `manufacturer_display == "General Electric"`; TMT/breaker rows for `Cutler Hammer` -> `Cutler-Hammer`; `ITE` -> `ITE (BBC)`.
- a known **identity/absent** mfr (e.g. `Eaton`, or any tier=none like `OEZ`) has `manufacturer_display == manufacturer_name` (fallback).
- `manufacturer_id` is unchanged (still the EP id).
Run the API test suite; all green + pristine output.

## Known follow-up (do NOT solve here — just note in closeout)
Several EP ids share one display (e.g. `Cutler-Hammer` x2, `Square-D` x3, `ITE (BBC)` x4, `LSIS` x2) — mostly on the **breaker axis** — so those dropdowns will show duplicate-looking labels. Consolidating ids that share a display (so the dropdown shows one entry that filters to all underlying ids) is a **separate follow-up increment** (it changes the cascade filter from a single id to a display/id-set). Leave it; just confirm in the closeout which dropdowns show dups.

## Deploy + live-verify
Deploy API + web. Live-verify (no secrets in closeout):
- `/api/v1/neta/cascade` (or the deployed path) returns `manufacturer_display` and the GE row reads `General Electric`.
- the lvbreakertcc page renders recognizable names in at least the ETU + TMT manufacturer dropdowns.

## Repo hygiene
Add a repo migration file mirroring the already-applied table for version control: `infra/database/migrations/tcc/013_tcc_mfr_aliases.sql` (CREATE TABLE + the 53-row seed read from the live `tcc.mfr_aliases`, header comment: "applied to prod via MCP 2026-06-06; recorded here for version control"). Plus a matching `_down.sql` (`drop table tcc.mfr_aliases;`).

## Boundaries
- Backend writes = app code only; the only DB object is the already-live `tcc.mfr_aliases` (read via join). No new prod DDL in this packet.
- Scoped `git add` (never -A); commit messages end with the standard Co-Authored-By line; PUBLIC repo + no secrets.
- Inbox lifecycle: `git mv pending->claimed` + push before running; closeout to the `closeout:` path; then `git mv claimed->done` + push.

## Acceptance
Tests-first and green; `manufacturer_display` served on the 4 manufacturer-list paths; frontend renders recognizable names; deployed + live-verified; repo migration file added; closeout records the per-endpoint result, the dup-dropdown list (follow-up), and the deploy verification. CC reviews, then designs the trip-unit/breaker **model**-layer normalization (the bigger, tier-gated piece) + the dup-consolidation increment.
