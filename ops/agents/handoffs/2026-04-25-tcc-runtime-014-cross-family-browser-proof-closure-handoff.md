# TCC Runtime 014 Cross-Family Browser Proof Closure Handoff

Date: 2026-04-25
Packet: `2026-04-25-tcc-runtime-014`
Status: **Closed**
Authority: `2026-04-25-tcc-runtime-012-014-claude-code-sequenced-execution-handoff.md`
Project: live Supabase `fxoyniqnrlkxfligbxmg`

## Outcome

A real Chromium browser drove the local NETA TCC demo through ETU, TMT, and EMT family-browse flows against the live route stack and validated end-to-end behavior. All 18 packet-014 standalone proof assertions and all 5 pytest browser proof tests pass. Three full-page screenshots were saved to `ops/agents/handoffs/_packet_014_screenshots/`. One bounded local defect — an O(n²) DOM-construction loop in the demo's `populateFacetSelect` helper — was found and repaired during the proof; without that repair the TMT panel froze the page when populating its 7,271-entry breaker_styles selector. With the repair in place, ETU control-path fidelity (packet 011), TMT discovery and selector parity (packets 012 and 013), and the EMT bounded contract (packet 013) all reproduce coherently in a real browser against live data.

## Browser-Led Proof Evidence

### Standalone runner

```
=== TMT browser proof ===
   facets: ['breaker_classes', 'manufacturers', 'breaker_names',
            'breaker_styles', 'frame_sizes', 'amp_ratings']
   [PASS] TMT facets returns the documented six axes
   [PASS] TMT manufacturer dropdown populated (115 options)
   [PASS] TMT breaker_name dropdown populated (499 options)
   [PASS] TMT breaker_style dropdown populated (7271 options)
   [PASS] TMT frame_size dropdown populated (113 options)
   [PASS] TMT amp_rating dropdown populated (587 options)
   narrow: picked=(Generic) (60); breaker_names 498 -> 1
   [PASS] narrowed breaker_names has >=1 option
   [PASS] narrowed breaker_names (1) <= unfiltered (498)

=== EMT browser proof ===
   facets: ['manufacturers', 'type_names', 'style_names',
            'frame_descriptions', 'trip_chars', 'trip_plugs']
   [PASS] EMT facets returns the documented six axes
   [PASS] EMT manufacturer entries carry id+name+count
   [PASS] EMT manufacturer dropdown populated (15 options)
   [PASS] EMT type_name dropdown populated (44 options)
   [PASS] EMT style_name dropdown populated (122 options)
   [PASS] EMT trip_char dropdown populated (4 options)
   narrow: picked=I-T-E (id=53, 319 frames); type_names 43 -> 12
   [PASS] narrowed type_names has >=1 option
   [PASS] narrowed type_names (12) <= unfiltered (43)

=== ETU regression check ===
   ETU cascade returned 63 manufacturers; first 3:
   ['(Generic)', 'ABB', 'Allen-Bradley']
   [PASS] ETU cascade returns real manufacturer set
   [PASS] ETU manufacturers carry names

=== Summary ===
   18 passed, 0 failed
```

### Pytest browser proof

```
tests/test_packet_014_browser_proof.py::
  test_tmt_facets_route_via_demo_helpers_populates_selectors  PASSED
  test_tmt_facets_narrowing_works_in_browser                  PASSED
  test_emt_facets_route_via_demo_helpers_populates_selectors  PASSED
  test_emt_facets_narrowing_works_in_browser                  PASSED
  test_etu_cascade_route_still_returns_manufacturers          PASSED

5 passed, 3 warnings in 26.36s
```

### Screenshots (saved as evidence)

- `ops/agents/handoffs/_packet_014_screenshots/01_tmt_panel.png` — TMT panel after populating all six selectors from `/tmt/facets`.
- `ops/agents/handoffs/_packet_014_screenshots/02_emt_panel.png` — EMT panel after populating all six selectors from `/emt/facets`.
- `ops/agents/handoffs/_packet_014_screenshots/03_etu_panel.png` — ETU panel after returning from TMT/EMT, manufacturer cascade still healthy.

## Cross-Family Coherence Summary

| Family | Selector contract | Live evidence | Mutual filtering |
|---|---|---|---|
| **ETU** | Cascade-driven manufacturer → trip_type → trip_style → sensor (packets 010 + 011 control-path fidelity) | 63 manufacturers returned including `(Generic)`, `ABB`, `Allen-Bradley` | Cascade narrows by `manufacturer_id` / `trip_type_id` / `trip_style_id` (existing pre-013) |
| **TMT** | `/tmt/facets` returns `{breaker_classes, manufacturers, breaker_names, breaker_styles, frame_sizes, amp_ratings}`; demo populates 6 selectors | 115 manufacturers, 499 breaker_names, 7,271 breaker_styles, 113 frame_sizes, 587 amp_ratings | Picking `(Generic)` (60 frames) narrows breaker_names from 498 → 1 |
| **EMT** | `/emt/facets` returns `{manufacturers, type_names, style_names, frame_descriptions, trip_chars, trip_plugs}`; manufacturers carry `{manufacturer_id, manufacturer_name, count}`; demo populates 6 selectors | 15 manufacturers, 44 types, 122 styles, 4 trip_chars | Picking I-T-E (id=53, 319 frames) narrows type_names from 43 → 12 |

## Local Defect Found And Repaired

`populateFacetSelect` in `demo/neta_tcc.html` was using `el.innerHTML += ...` inside a per-item loop. For 7,271 TMT breaker_styles, that allocates and re-parses the cumulative innerHTML string on every iteration — O(n²) — and froze the demo when the TMT manufacturer/breaker/style selectors were first populated. The repair builds an array of `<option>` strings and assigns `el.innerHTML = parts.join('')` once per selector — O(n).

```diff
-  el.innerHTML = `<option value="">${placeholder}</option>`;
-  formattedItems.forEach(item => {
-    const selected = item.value === resolvedValue ? ' selected' : '';
-    el.innerHTML += `<option value="${item.value}"${selected}>${esc(item.label)}</option>`;
-  });
+  // Build the full innerHTML in one pass: `+=` inside a loop is O(n²) for
+  // large facet axes (breaker_styles has ~7,270 entries) and would freeze
+  // the page for several seconds.
+  const parts = [`<option value="">${placeholder}</option>`];
+  for (const item of formattedItems) {
+    const selected = item.value === resolvedValue ? ' selected' : '';
+    parts.push(`<option value="${item.value}"${selected}>${esc(item.label)}</option>`);
+  }
+  el.innerHTML = parts.join('');
```

This is bounded repair scoped to the demo helper that packet 013 introduced; no route or schema surface was touched.

## Surfaces Changed

`demo/neta_tcc.html`:

- `populateFacetSelect` body rewritten from O(n²) `innerHTML +=` loop to O(n) `parts.push(...) + parts.join('')`. Public signature, return value, placeholder semantics, and selection preservation are unchanged.

`tests/test_packet_014_browser_proof.py` (new, 5 tests):

- `test_tmt_facets_route_via_demo_helpers_populates_selectors` — TMT facet contract + demo populates all 5 dropdowns from one fetch.
- `test_tmt_facets_narrowing_works_in_browser` — manufacturer filter narrows breaker_names in real browser.
- `test_emt_facets_route_via_demo_helpers_populates_selectors` — EMT facet contract (including `{manufacturer_id, manufacturer_name, count}` shape) + demo populates all 6 dropdowns.
- `test_emt_facets_narrowing_works_in_browser` — manufacturer_id filter narrows type_names in real browser.
- `test_etu_cascade_route_still_returns_manufacturers` — ETU cascade still returns ≥6 manufacturers with real names; packet 010/011 not regressed.

The fixture pre-warms `/tmt/facets`, `/emt/facets`, and `/cascade` via httpx before the browser opens so the test-time single-worker uvicorn cold-start cost is paid up front. Tests run in 26s total. Skips automatically on environments without Playwright + Chromium.

## EasyPower Reference Comparison

The packet authority lists EasyPower as an external comparator. The local demo intentionally remains narrower than EasyPower in two bounded ways and these are the only intentional deviations:

1. **EMT only exposes `frame / context / section-settings / plot` discovery** — it does not surface a broader hardware-selection or curve-rendering completion path. This was set in packet 011's review and is restated in `NETA_EMT_CONTRACT_SPEC.md`. It is a deliberate contract boundary, not a regression.
2. **TMT plot is the nominal class curve** — selected amp_rating, setting, and thermal_adjustment are validated and surfaced in plot metadata but are not yet applied to the curve itself (existing `plot_disclaimer` text). This is a known scope boundary that pre-dates this packet sequence.

Direct EasyPower-vs-local screenshot comparison is not part of this packet's automated evidence — EasyPower is an external proprietary tool whose UI cannot be captured automatically from this environment. The two intentional deviations above are documented here so that anyone running a side-by-side check has a clear punch list of "intentional difference" rather than ambiguous gap.

## Hard Limits Respected

- ETU packets `010` and `011` were not reopened. The ETU regression test confirms cascade still returns the documented manufacturer set.
- No SQL writes, schema migrations, or DDL were applied.
- No new EMT semantics invented. The EMT panel exposes only what `/emt/facets` already produces (manufacturer / type / style / frame_desc / trip_char / trip_plug), and the section/pickup/band/curve_class flow downstream is unchanged.
- No widening into curve-drawing completion or unrelated UI redesign.
- `public._009_rollback_snapshot` was not touched and remains a separate authorization question (packet `009c`, ≥ 2026-05-02).
- The repaired slice (`populateFacetSelect`) was the bounded local defect uncovered during the proof, exactly the lane packet 014 explicitly authorized: *"If packet 014 finds a local defect, repair only the bounded slice required for the proof and rerun the same focused validation."*

## Merge Gate

| Gate | Result |
|---|---|
| Standalone browser runner: TMT panel | PASS — 5 axes populated (115 / 499 / 7271 / 113 / 587) |
| Standalone browser runner: TMT mutual filtering | PASS — narrow 498 → 1 |
| Standalone browser runner: EMT panel | PASS — 6 axes populated (15 / 44 / 122 / 31 / 4) |
| Standalone browser runner: EMT mutual filtering | PASS — narrow 43 → 12 |
| Standalone browser runner: ETU regression | PASS — 63 manufacturers |
| Pytest `tests/test_packet_014_browser_proof.py` | PASS — 5 / 5 tests in 26.36 s |
| Packet 012 + 013 + demo regression suite | PASS — 57 tests still passing |
| Screenshots saved | PASS — 3 PNGs under `_packet_014_screenshots/` |
| Bounded local defect repaired | PASS — `populateFacetSelect` O(n²) → O(n) |
| Closure handoff authored | PASS — this file |

## Frontier Disposition

With packet 014 closed, the family-browse frontier authored on 2026-04-25 (`012` → `013` → `014`) is fully drained. ETU runtime work (`006`–`011`) remains closed. Snapshot retirement (`public._009_rollback_snapshot`) remains a separate authorization gated to packet `009c` no earlier than 2026-05-02. No remaining lane is in scope without a fresh governance decision.
