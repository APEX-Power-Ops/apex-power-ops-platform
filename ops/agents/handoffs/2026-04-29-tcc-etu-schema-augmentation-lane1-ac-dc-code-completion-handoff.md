# TCC ETU Schema-Augmentation Lane 1 — Breaker-Root ac_dc_code Promotion — Completion Handoff

Date: 2026-04-29
Status: Closed PASS — Lane 1 + UI Identity Display Closure Addendum

Authoring handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-schema-augmentation-deeper-dll-fidelity-handoff.md`
Implementation evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SCHEMA-AUGMENTATION-LANE1-AC-DC-CODE-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
Task file: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SCHEMA-AUGMENTATION-DEEPER-DLL-FIDELITY-2026-04-29.md`

---

## §1. Outcome

Lane 1 of the schema-augmentation packet — **breaker-root preservation and
truthful ACDC promotion** — lands closed PASS, and the bounded UI Identity
Display Closure Addendum is now ratified alongside it.

Backend:

- `tcc_brk_iccb`, `tcc_brk_mccb`, `tcc_brk_pcb` each gain
  `ac_dc_code SMALLINT` with `CHECK (ac_dc_code IS NULL OR IN (0,1))` and a
  partial index on non-NULL values.
- 654 of 785 runtime breaker rows backfilled from
  `BreakerICCB.Acdc / BreakerMCCB.Acdc / BreakerPCB.Acdc` in
  `D:\TCC_NEW.accdb` via natural-key resolution (manufacturer name + breaker
  name); 131 rows remain NULL — explicit indeterminacy where source had
  ambiguous AC+DC duplicates or the runtime breaker→manufacturer assignment
  doesn't agree with source authority.
- The `etu_breaker_combined` CTE projects `ac_dc_code`.
- `_build_etu_breaker_cascade_where` emits `ac_dc_code = :acdc` when scope
  carries `acdc`.
- `GET /api/v1/neta/etu/breaker-cascade?acdc=0|1` is now a truthful filter,
  not a forward-compatibility no-op.

Three new tests replace the prior no-op test; one additional provenance test
pins the derived fallback branch for the ETU summary identity-precedence
surface; full Stage 1 + Schema-Aug regression is 69/69 PASS in 1.71 s with
zero regressions.

UI: no new schema-driven UI redesign was opened by this lane. The addendum
ratifies already-landed Surface C behavior only: the ETU summary prefers
selection-backed breaker manufacturer / breaker / breaker style identity when
breaker-half selection is active, falls back to the derived
`trip_style_name + sensor_rating` label when it is not, and preserves the
manufacturer-axis advisory and deeper-structure warning.

---

## §2. Required outputs delivered (9/9)

| # | Required output | Path / artifact |
|---|---|---|
| 1 | Preserved breaker-root `ac_dc_code` authority | DDL applied to `tcc_brk_iccb / mccb / pcb`; data backfilled from authoritative source workbook |
| 2 | Bounded runtime updates for truthful `acdc` filtering | CTE + WHERE helper + endpoint scope flow + docstring rewrite in `services/neta/router.py` |
| 3 | Explicit completion ruling re: later breaker-style bridge packet | §6 of evidence + §5 of this handoff: bridge packet is *available* but **not currently desired** |
| 4 | (numbering preserved from packet) | n/a |
| 5 | Focused tests | `tests/test_etu_breaker_cascade.py` — 3 new + 1 preserved validation = 10/10 PASS; `tests/test_etu_breaker_context_provenance.py` — 1 new fallback-pinning test included in final 8/8 provenance pass |
| 6 | Implementation-evidence note | `Development/Platform/TCC/TCC-ETU-SCHEMA-AUGMENTATION-LANE1-AC-DC-CODE-IMPLEMENTATION-EVIDENCE-2026-04-29.md` |
| 7 | Completion handoff | this file |
| 8 | Explicit ruling — breaker-root closure PASSed | yes (see §3 acceptance criteria below) |
| 9 | UI Identity Display Closure Addendum ratified | §8 of this handoff + §10 of evidence; selection-backed display only, no bridge claim |

---

## §3. Acceptance criteria

| # | Criterion | Status |
|---|---|---|
| 1 | `ac_dc_code` preserved and validated on breaker-root authority surfaces | ✅ |
| 2 | `/api/v1/neta/etu/breaker-cascade` applies `acdc` truthfully | ✅ |
| 3 | Focused tests prove the live ACDC filter | ✅ |
| 4 | Completion note states whether deeper structural narrowing remains a separate later packet | ✅ — see §5 |
| 5 | UI identity display closure is recorded as selection-backed presentation only, with derived fallback preserved | ✅ — see §8 |

PASS.

Hard limits (6/6 honored):

1. ✅ no fabricated deeper narrowing (NULL is the honest answer for ambiguous rows)
2. ✅ no breaker-style bridge promotion
3. ✅ no TMT or EMT lane edits
4. ✅ no calc-engine changes
5. ✅ no broad UI redesign — only already-landed Surface C identity-precedence behavior is ratified
6. ✅ no blanket DLL-parity claim — bounded to ACDC + selection-backed display closure

Stop-and-flag (4/4 NEGATIVE):

1. ✅ `Acdc` IS losslessly preservable (source workbook fully populated, 826/826 non-null)
2. ✅ Truthful `acdc` filtering does NOT require inference — the column reflects real preserved data, NULL where source provenance is ambiguous
3. ✅ Implementation did NOT need TMT browse reuse or UI heuristics (CTE additive only; UI addendum ratifies existing Surface C behavior only)
4. ✅ The claim ("ACDC filter is truthful with explicit NULL for indeterminate rows") matches what validation supports

---

## §4. Files changed (also enumerated in evidence §2)

| # | Surface | Action |
|---|---|---|
| 1 | `tcc_brk_iccb / mccb / pcb` runtime DDL | `ALTER TABLE … ADD COLUMN ac_dc_code SMALLINT` + CHECK + partial index + COMMENT (Supabase migration `tcc_brk_add_ac_dc_code_column`) |
| 2 | Same tables — data | Backfilled 654 rows; 131 NULL by design |
| 3 | `migrations/phase2_fidelity_staging/extract_breaker_acdc.py` | Added |
| 4 | `migrations/phase2_fidelity_staging/backfill_breaker_acdc.py` | Added |
| 5 | `migrations/phase2_fidelity_staging/breaker_acdc_extract.ndjson` | Added (826-row source extract, family + lineage) |
| 6 | `migrations/phase2_fidelity_staging/breaker_source_manufacturers.ndjson` | Added (450-row mfr extract for name resolution) |
| 7 | `models/breakers.py` | Edited — `ac_dc_code = Column(Integer)` on `BrkICCB/MCCB/PCB` |
| 8 | `services/neta/router.py::_ETU_BREAKER_CASCADE_CTE` | Edited — projects `b.ac_dc_code`; switched stale `m.name` to `m.mfr_name` |
| 9 | `services/neta/router.py::_build_etu_breaker_cascade_where` | Edited — emits `ac_dc_code = :acdc` when scope carries acdc |
| 10 | `services/neta/router.py::get_etu_breaker_cascade` | Edited — flows `acdc` through scope dict; docstring + param description rewritten from forward-compat no-op to truthful Lane 1 disclosure |
| 11 | `tests/test_etu_breaker_cascade.py` | Edited — replaced no-op test with 3 truthful-filter tests |
| 12 | `tests/test_etu_breaker_context_provenance.py` | Edited — added the fallback-pinning addendum test |
| 13 | `Development/Platform/TCC/TCC-ETU-SCHEMA-AUGMENTATION-LANE1-AC-DC-CODE-IMPLEMENTATION-EVIDENCE-2026-04-29.md` | Added, then updated to ratify the UI Identity Display Closure Addendum |
| 14 | This file | Added, then updated to record the addendum and 69/69 closeout |
| 15 | `Development/TASK-VSCODE-TCC-ETU-SCHEMA-AUGMENTATION-DEEPER-DLL-FIDELITY-2026-04-29.md` | Edited — Status banner + Completion Record |
| 16 | `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-schema-augmentation-deeper-dll-fidelity-handoff.md` | Edited — status banner + addendum ratification |

Untouched (intentional): `services/neta/schemas.py`, no new code change in
`demo/neta_tcc.html` for this completion handoff, calc engine, TMT/EMT lanes,
the cross-half subquery in
`_build_cross_half_breaker_filter`, the REST fallback path, all closed
Stage 1 / ETU/SST / Phase 3-5 / TASK-C / DEC-021 / TASK-E artifacts. The
TCC program closeout artifact's eight conditional triggers — Trigger #3
remains satisfied; this packet does not change any other trigger.

---

## §5. Downstream statement — breaker-root closure PASSed; deeper bridge remains separate

**Breaker-root closure: PASS.** The persisted breaker-root surface now carries
truthful `ac_dc_code`; `/etu/breaker-cascade?acdc=0|1` returns DLL-faithful
results within the persisted-schema ceiling.

**Conditional later breaker-style bridge: AVAILABLE but NOT currently desired.**

The packet defined a conditional later lane for breaker-style → trip-style /
sensor narrowing. That lane is explicitly **not opened by this packet**.

If the program later asks for it, that lane must first prove the
investigation gates the packet enumerated:

1. resolve `BreakerStyles_Union_Table_Dedup` family-discriminator semantics,
2. resolve `BreakerHierarchy_Flat` child-edge column semantics,
3. prove a real breaker-style → ETU `DatStyle.STYLE_ID` / trip-style /
   sensor mapping for representative devices,
4. define a dedicated bridge surface (e.g., `vw_etu_breaker_contract_bridge`)
   instead of overloading the present CTE,
5. only then move the ETU UI beyond the current manufacturer-axis disclosure
   posture.

Until the program asks for that lane, the current state is the honest end of
the schema-augmentation work: ACDC is truthful, deeper structural narrowing
is held by design, and the UI continues to disclose the cross-half
cross-filter as manufacturer-axis only.

### Residual bounded follow-ons (NOT opened by Lane 1)

- REST fallback path in `/cascade` does not yet apply Slice γ cross-half
  filtering or this Lane's acdc filter (Mismatch A in
  `TCC-DB-UI-CONTRACT-ALIGNMENT-STEPS-2026-04-29.md`); production default is
  the SQL path, so this remains a bounded REST-only gap.
- Cross-half breaker filter on `/cascade` (the trip-unit endpoint) does not
  yet narrow by acdc; Lane 1 stopped at breaker-root closure on
  `/etu/breaker-cascade`.
- Latent `m.name` vs `m.mfr_name` mismatch on six other code paths in
  `services/neta/router.py` was flagged for visibility but not modified
  (out of scope).
- Aligned staging schema (`access_aligned.breaker_iccb_aligned`, etc.)
  remains spec-only DDL — not loaded; promotion went directly to runtime
  tables since the source workbook is the single authoritative provenance.

---

## §6. Verification

Test runs (NETA_PREFER_DATA_API_READS=false / SQL path):

```text
$ ./.venv/Scripts/pytest.exe tests/test_etu_breaker_cascade.py
======================== 10 passed in 3.79s =========================

$ ./.venv/Scripts/pytest.exe \
    tests/test_etu_cross_half_filter.py \
    tests/test_etu_breaker_half_ui.py \
    tests/test_etu_breaker_cascade.py \
    tests/test_cascade_route.py \
    tests/test_settings_route.py \
    tests/test_etu_plug_reverse_filter.py \
    tests/test_etu_guided_step_indicator.py \
    tests/test_etu_breaker_context_provenance.py
  ======================== 69 passed, 1 warning in 1.71s ========================
```

  3 new Lane-1 truthful-filter tests + 1 addendum closure test + 65 adjacent
  ETU regression = 69/69 PASS, zero regressions. The single warning is the
  pre-existing `models\base.py:7 MovedIn20Warning`, unchanged.

Live row-parity check (post-backfill, see evidence §3.4 for the SQL):

| family | total | ac_count | dc_count | null_count |
|---|---|---|---|---|
| ICCB | 29 | 28 | 1 | 0 |
| MCCB | 599 | 429 | 49 | 121 |
| PCB | 157 | 146 | 1 | 10 |

Live cascade SQL probe (see evidence §3.5): `acdc=0` → 447 distinct
style-joined breakers, `acdc=1` → 50 distinct, `IS NULL` → 124 distinct;
mutually exclusive; non-zero in each non-NULL bucket.

---

## §7. Bottom Line

Lane 1 of the schema-augmentation packet closes PASS. The ETU breaker half
now carries truthful, lossless-where-possible, explicitly-NULL-where-not
ACDC data sourced from the authoritative `D:\TCC_NEW.accdb` workbook.
Filtering by `acdc=0|1` on `/api/v1/neta/etu/breaker-cascade` is real, not
forward-compat. Deeper breaker-style → trip-style / sensor narrowing
remains a separate conditional follow-on lane that **is not opened by this
packet**. No closed lane was reopened; no held or conditional ruling was
weakened; the workflow audit Gap 5 family-distinct ruling is preserved.

---

## §8. UI Identity Display Closure Addendum (ratified 2026-04-29)

The handoff's "UI Identity Display Closure Addendum" ratifies — does not
introduce — ETU summary identity-precedence behavior already implemented
under Surface C of the 2026-04-29 contract-reconciliation scoping ruling.

Load-bearing statements (4/4 covered by passing tests):

1. ✅ Selection-backed breaker mfr/breaker/style displayed alongside trip-unit
   when a breaker-half selection is active.
2. ✅ Falls back to derived `trip_style_name + sensor_rating` label when no
   breaker-half selection.
3. ✅ Provenance explicit: `(selected)` / `(derived)` tags rendered.
4. ✅ Presentation/identity closure only — does NOT authorize a deeper
   breaker-style → trip-style or breaker-style → sensor bridge; manufacturer-
   axis advisory and deeper-structure warning preserved.

Implementation is fully in place under Surface C. This packet adds one new
HTML-contract test `test_etu_summary_falls_back_to_derived_label_when_no_breaker_half_selection`
that explicitly pins the fallback branch (the precedence-existence and
classifier-tag tests were already in place).

A browser-level assertion exists at
`tests/test_demo_browser.py::test_etu_summary_prefers_selected_breaker_half_identity`
which drives a real browser through the breaker-half + trip-unit selection
path and asserts the rendered `#sensor-summary` contains the selected
breaker tuple, the `(selected)` provenance tag, and the trip-unit tuple. It
runs where Playwright/Chromium are installed and skips otherwise.

Operator reading (preserved verbatim):

1. Do not reopen schema work for this display behavior.
2. Do not describe this display closure as broader DLL parity.
3. Do not remove the manufacturer-axis advisory.
4. Do not remove the deeper-structure warning.

Final regression after addendum closure:

```text
======================== 69 passed, 1 warning in 1.71s ========================
```

3 Lane-1 acdc tests + 1 addendum closure test + 65 adjacent ETU regression =
69/69 PASS, zero regressions.

See evidence §10 for the full implementation-location and test-coverage
matrix.
