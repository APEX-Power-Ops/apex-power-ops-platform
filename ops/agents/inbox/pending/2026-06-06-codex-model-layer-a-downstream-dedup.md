# Codex Packet — lvbreakertcc MODEL LAYER slice (a): downstream LABEL DEDUP (serving + frontend, no DB change)

Lane: lvbreakertcc EP→ETAP nomenclature normalization. The manufacturer DISPLAY layer and manufacturer
DUP-CONSOLIDATION are shipped + live. Consolidating the EP duplicate-manufacturer ids (e.g. Square-D = ids
17/35/235) pushed the duplication ONE LEVEL DOWN: identical frame/model/type labels now appear twice under a
single consolidated manufacturer, concentrated on the TMT frame axis. This packet is **slice (a) of the model
layer — a mechanical, exact-string DEDUP of those downstream labels.** It does NOT rename anything to ETAP
equivalents (that is slice (b), a separate packet).

## Boundary / hygiene (read first)
- PUBLIC repo `apex-power-ops-platform`. NO secrets / client / job / site / person identifiers in any committed
  artifact. Manufacturer/model/frame names + ids are library taxonomy and are fine to commit.
- Scoped `git add` only (never `-A`). Commit message ends with the Co-Authored-By trailer (see end). Use Git Bash
  heredoc for commit messages (NOT PowerShell `@'...'@`).
- **NO database change.** No prod DDL, no migration, no prod write. Pure serving-layer aggregation + frontend.
- TDD required (tests first, red→green). No production code before a failing test.

## Problem (measured by the prior packet's closeout)
After manufacturer consolidation, selecting a consolidated manufacturer unions its EP ids, and the downstream
level dropdowns now list the same label more than once (one per underlying EP id). Excess duplicate rows measured
live (`2026-06-06-mfr-dup-consolidation-closeout.md`):

| Downstream surface | display (ids) | dup groups | EXCESS dup rows | examples |
|---|---|---:|---:|---|
| ETU trip type | ITE (BBC) [11,125] | 1 | 1 | Power Shield ×2 |
| ETU breaker name | Square-D [17,35] | 2 | 2 | `(Std)` ×2, MP NW UL489 ×2 |
| ETU breaker name | Westinghouse [18,36] | 1 | 1 | Series C ×2 |
| TMT MCCB frame label | ABB [1,43] | 18 | 146 | Tmax Ts3* |
| TMT MCCB frame label | Cutler-Hammer [28,41] | 11 | 55 | WMZ, Series G, Navy AQB |
| TMT MCCB frame label | Federal Pacific [8,118] | 20 | 169 | NJL/NF/Fusematic/FPower |
| TMT MCCB frame label | Fuji [46,102] | 33 | 137 | G-TWIN/BU Series |
| TMT MCCB frame label | ITE (BBC) [11,173] | 25 | 88 | EQ/ET/MCP |
| TMT MCCB frame label | LSIS [192,304] | 43 | 135 | ABE/ABH/EBE/EBH |
| TMT MCCB frame label | Square-D [17,235] | 18 | 177 | H/M/F Frame |
| TMT MCCB frame label | Westinghouse [18,36] | 15 | 113 | MCP/AB DE-ION/Series C |
| TMT PCB frame label | ITE (BBC) [4,11] | 34 | 134 | LK/LKE/K-series |
| TMT PCB frame label | Square-D [17,35] | 30 | 146 | Masterpact/MP MT/MP NT |

These came from different EP duplicate-manufacturer records carrying the SAME catalog (e.g. SQD vs SquareD both
list "H Frame"), so they are genuinely the same physical frame duplicated — safe to collapse.

## Approach (mechanical, minimal)
Apply the SAME group-by-union pattern, one level down. At each downstream cascade LEVEL that lists model / frame /
type labels and can receive a multi-id manufacturer selection, GROUP BY the existing label string and UNION the
underlying style ids:
- return one row per distinct label with `style_ids: list[int]` (sorted) — the union of the underlying
  trip_style_id / breaker_style_id values that share that label
- keep a representative `id = min(style_ids)` and the existing label field for back-compat
- the count (if any) = SUM of per-style counts (union; each device row has exactly one style id → no overlap)
- the NEXT level down (sensors / settings / frame detail) must accept the `style_ids` set and filter
  `style_id = ANY(:ids)`; keep single-id back-compat (lone id ⇒ 1-element list)

Apply this GENERICALLY to every downstream level that can receive a consolidated (multi-id) manufacturer — not
only the surfaces in the table — so un-sampled paths don't regress. The measured surfaces are the acceptance anchors.

### Scope of "label" grouping — EXACT string only
Group ONLY rows whose existing displayed label is byte-for-byte identical (after the trim/normalization the code
already applies for display). Do NOT fuzzy-match, do NOT rename, do NOT map to ETAP names. This slice removes only
the duplication introduced by the manufacturer union. (ETAP model normalization + tier-gated crosswalk display is
slice (b), a later packet.)

### Safety valve — catch false merges
Two same-label styles under one manufacturer should be the same catalog entry. As a guard, when grouping collapses
≥2 style ids under one label, check whether their downstream sensor/setting sets DIVERGE. If any group's members
have materially different downstream data, DO NOT silently merge that group — keep it split (or surface it) and
LIST those cases in the closeout. Expectation: near-zero divergence (these are EP dup-mfr artifacts), but report
the count so we know.

## Files (likely; confirm by reading)
Backend `apps/control-plane-api/services/neta/router.py`:
- ETU cascade level builder `_cascade_level` (~L2178) + `get_cascade` (~L3681) — trip-type level.
- ETU breaker cascade `_etu_breaker_cascade_level` (~L2473) + `get_etu_breaker_cascade` (~L3949) — breaker-name level.
- TMT facets `_load_tmt_facets` (~L2992) + `get_tmt_facets` (~L4496) — frame-label level (the big one).
- Downstream where-builders that filter by a single style id → also accept `style_ids` (`= ANY`).
- EMT path: no dups measured; apply the generic group-by only if it can receive a multi-id manufacturer, else leave.
Schemas `apps/control-plane-api/services/neta/schemas.py`: add `style_ids: Optional[list[int]]` to the relevant
level/facet response models.
Frontend `apps/operations-web/app/lvbreakertcc/page.tsx` + types `lib/breaker-resources.ts`: model/frame/type
dropdown renders one option per label; selection carries the `style_ids` set; downstream calls pass it. Add
`style_ids?: number[]` to the item types.

## TDD — write first (red), then implement (green)
New backend test file e.g. `apps/control-plane-api/tests/test_neta_downstream_label_dedup_routes.py`:
1. ETU breaker-name list for Square-D (`manufacturer_ids=[17,35,235]`) returns `(Std)` exactly ONCE with
   `style_ids` unioned; no duplicate `MP NW UL489`.
2. TMT MCCB frame-label list for Square-D returns each frame label once (e.g. `H Frame` once); EXCESS dup rows = 0.
3. Selecting a deduped frame (passing its `style_ids`) returns the UNION of downstream sensors (≥ either single
   style alone).
4. Back-compat: a single style id still returns that style's results unchanged.
5. ETU trip-type list for ITE (BBC) returns `Power Shield` once.
6. (guard) grouping does not crash when a label maps to divergent downstream sets; the divergence count is reported.
Frontend: `pnpm --filter @apex/operations-web typecheck` and `build` pass.

### Acceptance (every "EXCESS dup rows" in the table above → 0)
- TMT MCCB Square-D 177→0, Federal Pacific 169→0, Fuji 137→0, LSIS 135→0, ABB 146→0, Westinghouse 113→0, ITE 88→0,
  Cutler-Hammer 55→0; TMT PCB Square-D 146→0, ITE 134→0; ETU breaker Square-D 2→0, Westinghouse 1→0; ETU trip ITE 1→0.
- Selecting a deduped label still reaches the union of underlying devices (no device lost).

## Out of scope
- ETAP MODEL NORMALIZATION / renaming (slice b) — do not rename labels to ETAP equivalents here.
- Manufacturer axis (already done). Relay endpoints (own lane). Any DB schema/data change.

## Validation + deploy + deliverables
1. TDD as above; focused + adjacent backend suites green; `compileall`; frontend typecheck + build.
2. Non-env regression subset with `-m "not integration"` (per the prior closeout's note about this workstation's
   localhost Postgres SSL mismatch); report pass count.
3. Deploy: push to main (admin bypass; verify `git status -sb` in-sync); confirm Vercel prod READY; focused hosted
   browser check on `https://operations.apexpowerops.com/lvbreakertcc`: pick Square-D on the TMT MCCB axis and
   confirm each frame label (H/M/F Frame …) appears ONCE, and the downstream selection still resolves devices.
4. Independently re-verify the deployed API: the TMT MCCB frame-label list for a consolidated mfr shows zero
   duplicate labels and rows carry `style_ids`.
5. Closeout to `ops/agents/handoffs/2026-06-06-model-layer-a-downstream-dedup-closeout.md`: commits, TDD red→green,
   per-surface before/after excess-dup counts (target all 0), the safety-valve divergence count (any false-merge
   candidates), and surprises. Then `git mv` this packet pending→done and push.

## Commit hygiene
- Scoped `git add` of only changed files. Git Bash heredoc for the commit message. End every commit message with:

```
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```
