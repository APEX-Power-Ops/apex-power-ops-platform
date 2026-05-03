# TCC ETU Stage 1 Slice γ Cross-Half SQL And UI Scoping — Completion Handoff

Date: 2026-04-29
Status: Closed PASS — Slice γ (mixed: backend cross-half SQL + minimal UI scoping)

Authoring handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-gamma-cross-half-sql-and-ui-scoping-execution-handoff.md`
Implementation evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-GAMMA-CROSS-HALF-SQL-AND-UI-SCOPING-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
Task file: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-GAMMA-CROSS-HALF-SQL-AND-UI-SCOPING-2026-04-29.md`

---

## §1. Outcome

Slice γ — the final mixed slice of the 2026-04-29 ETU contract-reconciliation
scoping ruling — lands **closed PASS**. The ETU lane now honors a truthful
**cross-half cross-filter contract** at the manufacturer-axis between the
breaker-half cascade (Slice α / β) and the trip-unit-half cascade (the
existing `/api/v1/neta/cascade`).

Backend:

- `GET /api/v1/neta/cascade` now accepts `breaker_class`, `breaker_id`, and
  `breaker_style_id` cross-half filters. When set, the trip-unit cascade
  narrows to manufacturers with at least one matching breaker via an
  `IN (SELECT manufacturer_id FROM etu_breaker_combined WHERE ...)`
  subquery prepended with the existing CTE.
- `GET /api/v1/neta/etu/breaker-cascade` now accepts `trip_type_id`,
  `trip_style_id`, and `sensor_id` cross-half filters. When set, the
  breaker cascade narrows to manufacturers with at least one matching
  trip-unit via an `IN (SELECT manufacturer_id FROM vw_trip_unit_cascade
  WHERE ...)` subquery.

UI:

- `buildCascadeQuery` and `buildBreakerCascadeQuery` accept optional
  cross-half selection args; both refresh helpers read the live snapshot
  of the OTHER half and pass it through.
- Breaker-half handlers re-narrow the trip-unit cascade after their own
  refresh; trip-unit selectors get a separate listener that re-narrows
  the breaker-half cascade and refreshes the cross-half advisory.
- The cross-half advisory was rewritten from "Slice γ held" warning to an
  informational disclosure of the manufacturer-axis cross-filter and the
  no-deeper-structural-cross-filter caveat. The HTML inline note above
  the breaker-half group was rewritten to match.

No DDL, no schema migration, no calc-engine touch, no TMT/EMT widening, no
parity claim. Slice α and Slice β surfaces are intact (8 + 19 prior tests
continue to PASS).

**Trigger #3 of the TCC program closeout artifact (breaker-side hierarchy
ownership) is now satisfied.**

---

## §2. Required outputs delivered (7/7)

| # | Required output | Path / artifact |
|---|---|---|
| 1 | One truthful backend cross-half contract surface | `_build_cross_half_breaker_filter` + `_build_cross_half_trip_unit_filter` helpers in `services/neta/router.py`, applied to both `/cascade` and `/etu/breaker-cascade` |
| 2 | Minimal schema updates needed for that surface | Zero schema-model edits — `EtuBreakerCascadeResponse.scope` is `dict[str, Any]` and accepts new keys natively; cascade response is unchanged |
| 3 | Minimal UI scoping updates | Query builders extended with optional cross-half args; refresh helpers pass cross-half snapshots; reciprocal change-event listeners; advisory wording rewritten; HTML inline note rewritten |
| 4 | Focused tests proving cross-half contract + tightened UI behavior | `tests/test_etu_cross_half_filter.py` (11 backend tests) + updated UI tests in `test_etu_breaker_half_ui.py` |
| 5 | One implementation-evidence note | `Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-GAMMA-CROSS-HALF-SQL-AND-UI-SCOPING-IMPLEMENTATION-EVIDENCE-2026-04-29.md` |
| 6 | One completion handoff | this file |
| 7 | Exact downstream statement about Trigger #3 disposition | §6 below — Trigger #3 satisfied |

---

## §3. Files changed

| # | Surface | Action |
|---|---|---|
| 1 | `tcc_v5_backend/services/neta/router.py` | Edited — added 2 cross-half helper functions, extended `/cascade` (3 new query params + per-query cross-half clause + CTE prefix), extended `/etu/breaker-cascade` (3 new query params + per-query cross-half clause + scope echo of new keys) |
| 2 | `tcc_v5_backend/demo/neta_tcc.html` | Edited — `buildCascadeQuery` + `buildBreakerCascadeQuery` accept cross-half args; refresh helpers pass cross-half snapshots; breaker-half handlers re-narrow trip-unit; trip-unit selectors get a reciprocal-refresh listener; advisory rewritten; inline note rewritten |
| 3 | `tcc_v5_backend/tests/test_etu_cross_half_filter.py` | Added — 11 focused backend cross-half tests |
| 4 | `tcc_v5_backend/tests/test_etu_breaker_half_ui.py` | Edited — replaced superseded Slice β test + updated advisory test for new wording |
| 5 | `tcc_v5_backend/tests/test_etu_breaker_cascade.py` | Edited — relaxed scope-equality test to subset check |
| 6 | `Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-GAMMA-CROSS-HALF-SQL-AND-UI-SCOPING-IMPLEMENTATION-EVIDENCE-2026-04-29.md` | Added (implementation evidence) |
| 7 | `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-gamma-cross-half-sql-and-ui-scoping-completion-handoff.md` | Added (this file) |
| 8 | `Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-GAMMA-CROSS-HALF-SQL-AND-UI-SCOPING-2026-04-29.md` | Edited — Status banner + Completion Record |
| 9 | `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-gamma-cross-half-sql-and-ui-scoping-execution-handoff.md` | Edited — Status banner only |

**Untouched (intentional):**

- `services/neta/schemas.py` — no schema-model edit.
- `services/calc_engine/` — calc engine untouched.
- `migrations/` — no DDL.
- All Phase 3/4/5/ETU-SST trio/TASK-C/DEC-021/TASK-E/Slice α/Slice β closure artifacts.
- TCC program closeout artifact eight conditional triggers — trigger #3 now satisfied (see §6); the other seven are unchanged.
- DLL-authority revision + workflow audit + scoping ruling — load-bearing authority, untouched.
- TMT and EMT lanes.

---

## §4. Verification

### Focused new cross-half tests (11/11 PASS)

```text
$ NETA_PREFER_DATA_API_READS=false ./.venv/Scripts/pytest.exe \
    tests/test_etu_cross_half_filter.py
======================== 11 passed in 0.41s =========================
```

### Full Stage 1 suite (62/62 PASS — zero regressions)

```text
$ NETA_PREFER_DATA_API_READS=false ./.venv/Scripts/pytest.exe \
    tests/test_etu_cross_half_filter.py \
    tests/test_etu_breaker_half_ui.py \
    tests/test_etu_breaker_cascade.py \
    tests/test_cascade_route.py \
    tests/test_settings_route.py \
    tests/test_etu_plug_reverse_filter.py \
    tests/test_etu_guided_step_indicator.py \
    tests/test_etu_breaker_context_provenance.py
======================== 62 passed, 1 warning in 1.79s ========================
```

New Slice γ cross-half (11) + Slice β UI (19) + Slice α breaker-cascade
backend (8) + cascade route (5) + settings route (5) + ETU/SST trio
Surface B (4) + Surface A+D (5) + Surface C (5) = 62/62 PASS.

The single warning is the pre-existing `models\base.py:7 MovedIn20Warning`,
unchanged.

The Slice γ extension is fully backward-compatible when no cross-half filter
is passed — every pre-existing test exercises the no-filter path and
continues to PASS. Confirmed by `test_cascade_without_breaker_filters_omits_cross_half_subquery`
and `test_breaker_cascade_without_trip_unit_filters_omits_cross_half_subquery`.

---

## §5. Acceptance criteria (7/7 PASS) and hard limits (6/6 honored)

Acceptance:

1. ✅ ETU backend honors at least one truthful cross-half narrowing path — landed BOTH directions.
2. ✅ UI no longer presents Slice γ as merely advisory — advisory rewritten as informational disclosure.
3. ✅ Focused validation passes (62/62).
4. ✅ Implementation remains ETU-distinct — verified by `test_breaker_cascade_remains_etu_distinct_under_cross_half_filter`.
5. ✅ No DDL or unrelated route widening.
6. ✅ Authority docs describe the slice truthfully as the final Stage 1 mixed follow-on.
7. ✅ Trigger #3 disposition stated explicitly — satisfied.

Hard limits:

1. ✅ No schema migration or DDL.
2. ✅ No calc-engine, settings-route, calculate, evaluate, or plot changes.
3. ✅ No TMT or EMT lane edits.
4. ✅ No broad demo redesign beyond the cross-half contract.
5. ✅ No fabricated parity or unsupported backend capability claim.
6. ✅ No reopening of any closed ETU/SST trio, Phase 3/4/5, TASK-C, DEC-021, or TASK-E lane.

Stop-and-flag (5/5 NEGATIVE):

1. ✅ Smallest truthful cross-half contract did NOT require DDL or broader schema redesign.
2. ✅ Smallest truthful implementation did NOT force TMT or EMT browse reuse.
3. ✅ UI tightening stayed aligned with backend truth without broad demo rewrite.
4. ✅ Focused validation did not expose a broader ETU runtime regression.
5. ✅ Result described honestly — no parity claim; advisory explicitly names manufacturer-axis ceiling.

---

## §6. Downstream statement — Trigger #3 satisfied

The TCC program closeout artifact's Trigger #3 (breaker-side hierarchy
ownership, originally PARTIAL by intentional design) was the gating condition
for ETU/SST item 1 follow-up work. The trigger fired with the 2026-04-29
contract-authority revision and produced the Stage 1 slice chain:

| # | Packet | Status |
|---|---|---|
| 1 | Contract-authority revision | Closed PASS 2026-04-29 |
| 2 | Contract-reconciliation scoping ruling | Closed PASS 2026-04-29 |
| 3 | Slice α — read-only ETU-distinct breaker-cascade backend | Closed PASS 2026-04-29 |
| 4 | Slice β — frontend-only breaker-half UI + cross-half advisory | Closed PASS 2026-04-29 |
| 5 | **Slice γ — backend cross-half cross-filter + UI scoping (this packet)** | **Closed PASS 2026-04-29** |

**Trigger #3 is now satisfied.** All three Stage 1 slices have landed PASS;
no further conditional follow-on is required to honor the DLL-authority
revision contract within the persisted schema's structural ceiling.

### Residual bounded follow-ons (not Slice γ scope)

Pre-existing residuals from earlier decisions, NOT reopened or worsened by
this packet:

- The **REST fallback path** in `/cascade` (`_cascade_response_from_rest`)
  does not yet apply the Slice γ cross-half filter. Production default is
  the SQL path (`_prefer_supabase_data_api_reads()` returns False by
  default), so this is a bounded REST-only gap.
- The **`acdc` parameter** on `/etu/breaker-cascade` remains a forward-
  compatibility no-op until the `ACDC` column is added by a separately
  authored schema-augmentation packet.
- The other seven TCC program closeout artifact triggers (1, 2, 4, 5, 6, 7, 8)
  remain unchanged.

---

## §7. Bottom Line

Slice γ closes the Stage 1 follow-on chain that Trigger #3 unlocked. The
ETU lane now honors a truthful cross-half cross-filter contract at the
manufacturer-axis, backed by inline IN-subqueries against existing tables
and views — no DDL, no schema migration, no parity claim. The UI surfaces
this truth via an informational advisory and reciprocal refresh handlers.
Slice α + β + γ together fulfill the DLL-authority revision contract
within the persisted schema's structural ceiling.

No closed lane was reopened; no held or conditional ruling was weakened;
no fabricated default next packet was introduced; the workflow audit Gap 5
family-distinct ruling is preserved (verified — SQL never references TMT
or EMT tables under cross-half filter).
