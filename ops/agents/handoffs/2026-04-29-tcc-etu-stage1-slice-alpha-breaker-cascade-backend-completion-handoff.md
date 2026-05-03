# TCC ETU Stage 1 Slice α Breaker-Cascade Backend — Completion Handoff

Date: 2026-04-29
Status: Closed PASS — Slice α only (read-only ETU-distinct breaker-half cascade backend)

Authoring handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-alpha-breaker-cascade-backend-execution-handoff.md`
Implementation evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
Task file: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-2026-04-29.md`

---

## §1. Outcome

Slice α of the 2026-04-29 ETU contract-reconciliation scoping ruling lands
**closed PASS**. Contract Stage 1 (upstream breaker-half identity) is now
exposed as a **read-only ETU-distinct backend cascade endpoint**:

```text
GET /api/v1/neta/etu/breaker-cascade
```

The endpoint mirrors the EasyPower DLL `FindMatchingBreakerStyles`
(DeviceLibrary.cs:403) join shape via UNION ALL across the three breaker
classes (ICCB / MCCB / PCB) inside a CTE named `etu_breaker_combined`, with
cross-filtered facets for manufacturers / breaker classes / breakers /
breaker styles. Read-only. No frontend (Slice β). No cross-half wiring
(Slice γ). No DDL. No parity claim.

---

## §2. Required outputs delivered (6/6)

| # | Required output | Path / artifact |
|---|---|---|
| 1 | One new read-only ETU breaker-cascade endpoint | `GET /api/v1/neta/etu/breaker-cascade` in `tcc_v5_backend/services/neta/router.py` |
| 2 | One matching schema set in `services/neta/schemas.py` | `EtuBreakerManufacturer`, `EtuBreakerClassOption`, `EtuBreakerOption`, `EtuBreakerStyleOption`, `EtuBreakerCascadeResponse` |
| 3 | One focused test file | `tcc_v5_backend/tests/test_etu_breaker_cascade.py` (8 tests) |
| 4 | One evidence note | `Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-IMPLEMENTATION-EVIDENCE-2026-04-29.md` |
| 5 | One completion handoff | this file |
| 6 | Exact downstream statement preserving Slice β and Slice γ as separately governed follow-ons | §6 below |

---

## §3. Files changed (3 edited / added)

| # | Surface | Action |
|---|---|---|
| 1 | `tcc_v5_backend/services/neta/schemas.py` | Edited — added 5 new Pydantic models for breaker-cascade response |
| 2 | `tcc_v5_backend/services/neta/router.py` | Edited — added schema imports, `_ETU_BREAKER_CASCADE_CTE`, `_build_etu_breaker_cascade_where`, `_etu_breaker_cascade_level`, and `GET /etu/breaker-cascade` endpoint |
| 3 | `tcc_v5_backend/tests/test_etu_breaker_cascade.py` | Added — 8 focused tests |
| 4 | `Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-2026-04-29.md` | Edited — Status banner + Completion Record |
| 5 | `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-alpha-breaker-cascade-backend-execution-handoff.md` | Edited — Status banner only |

**Untouched (intentional):**

- `tcc_v5_backend/demo/neta_tcc.html` — frontend deferred to Slice β.
- `tcc_v5_backend/services/neta/router.py` `/cascade`, `/etu/sensors-matching-plug`, `/etu/search`, `/context/{sensor_id}`, `/settings/{sensor_id}`, `/calculate`, `/evaluate`, `/plot-tcc`, all `/tmt/*`, all `/emt/*` — unchanged.
- `tcc_v5_backend/services/neta/plans.py` — unchanged.
- `tcc_v5_backend/services/calc_engine/` — unchanged.
- `tcc_v5_backend/migrations/` — no schema migration.
- `tcc_v5_backend/models/` — no model changes (existing `BrkICCB / BrkMCCB / BrkPCB + styles` were inspected for column verification only; the SQL path uses raw `text()` against the existing tables).
- DLL-authority revision contract note + workflow audit + scoping ruling — load-bearing authority, untouched.
- TCC program closeout artifact — eight conditional triggers stand unchanged.
- All Phase 3 / 4 / 5, ETU/SST trio (Surfaces A+D / B / C), TASK-C inverse-equation validation/parity, DEC-021, TASK-E execution closure artifacts — all unchanged.

---

## §4. Verification

### Focused new endpoint tests (8/8 PASS)

```text
$ NETA_PREFER_DATA_API_READS=false ./.venv/Scripts/pytest.exe \
    tests/test_etu_breaker_cascade.py -v
======================== 8 passed, 1 warning in 1.66s =========================
```

Coverage:
1. Happy-path cross-filter at root level (manufacturers + breaker classes)
2. Upstream-scope filter narrows breakers facet (manufacturer_id + breaker_class)
3. Leaf level (breaker_id resolves to style facet)
4. Zero-match empty state with advisory preserved
5. Validation: `breaker_class` rejects non-{ICCB, MCCB, PCB}
6. Validation: `acdc` bounded to 0/1
7. Forward-compat: `acdc=0` accepted but never bound to SQL params and never appears as `ACDC` in any executed statement
8. ETU-distinct guarantee: SQL hits `tcc_brk_iccb / tcc_brk_mccb / tcc_brk_pcb` only — never `tcc_tmt_*`, `tcc_emt_*`, `vw_trip_unit_cascade`, or `emt_breaker_combined`

### Adjacent ETU regression suite (32/32 PASS)

```text
$ NETA_PREFER_DATA_API_READS=false ./.venv/Scripts/pytest.exe \
    tests/test_etu_breaker_cascade.py \
    tests/test_cascade_route.py \
    tests/test_settings_route.py \
    tests/test_etu_plug_reverse_filter.py \
    tests/test_etu_guided_step_indicator.py \
    tests/test_etu_breaker_context_provenance.py -v
======================== 32 passed, 1 warning in 3.57s ========================
```

New breaker-cascade (8) + cascade route (5) + settings route (5) + ETU/SST
trio Surface B (4) + Surface A+D (5) + Surface C (5) = 32/32 PASS. The
single warning is the pre-existing `models\base.py:7 MovedIn20Warning`,
unchanged and unrelated.

The Surface C test `test_provenance_disclosure_does_not_add_breaker_hierarchy`
continues to PASS — Slice α adds a separate read-only ETU-distinct endpoint,
not a cascade attached to the existing `vw_trip_unit_cascade` surface or
the heuristic provenance disclosure. The trip-unit-rooted runtime contract
is intact; zero regressions in adjacent routes.

---

## §5. Acceptance criteria (7/7 PASS)

Per the authority task §"Acceptance Criteria":

1. ✅ ETU lane exposes a read-only breaker-cascade backend surface rooted on existing `tcc_brk_*` tables.
2. ✅ Endpoint remains ETU-distinct and does not silently reuse TMT browse helpers or TMT framing semantics.
3. ✅ Returned breaker-half identity rows map truthfully to existing data and do not invent fake breaker / style surfaces.
4. ✅ Focused validation passes (32/32).
5. ✅ No frontend or cross-half wiring lands.
6. ✅ Authority docs describe the endpoint truthfully as Slice α only.
7. ✅ Packet ends with explicit next-step statement preserving Slice β and Slice γ as conditional later slices.

## §6. Hard limits honored (8/8)

Per the authoring handoff §"Hard Limits":

1. ✅ No HTML or other frontend changes.
2. ✅ No cross-half breaker-to-trip-unit wiring.
3. ✅ No schema migration or DDL.
4. ✅ No reuse of TMT browse helpers as the ETU implementation surface.
5. ✅ No calc-engine, settings-route, calculate, evaluate, or plot changes.
6. ✅ No TMT or EMT lane edits.
7. ✅ No fabricated breaker hierarchy or parity claim.
8. ✅ No reopening of any closed Phase 3 / 4 / 5, ETU/SST trio, TASK-C, DEC-021, or TASK-E lane.

## §7. Stop-and-flag (5/5 NEGATIVE)

Per the authority task §"Stop-And-Flag Rules":

1. ✅ Endpoint stayed ETU-distinct without reusing the TMT browse path.
2. ✅ Endpoint does not require frontend work to be meaningful — JSON response is self-describing.
3. ✅ Endpoint does not require schema migration or other DDL — all referenced tables and columns already exist; the `acdc` parameter is forward-compat reserved as documented.
4. ✅ Smallest truthful implementation did NOT force cross-half trip-unit filtering.
5. ✅ Focused validation did not expose a broader ETU runtime regression.

---

## §8. Downstream statement — Slice β and Slice γ remain conditional

This packet executes **Slice α only**. The 2026-04-29 ETU contract-
reconciliation scoping ruling decomposed the Stage 1 gap into three
sequenceable slices; with α now landed, the conditional follow-ons are:

- **Slice β (frontend-only):** add ETU-side breaker-half UI selectors
  (breaker-class / breaker-name / breaker-style) above or alongside the
  manufacturer dropdown in `demo/neta_tcc.html`; wire to
  `GET /api/v1/neta/etu/breaker-cascade`; add cross-half dependency
  invalidation between breaker-half and trip-unit-half; extend the
  guided-step indicator to render breaker-half steps. **Not authorized
  by this packet — requires a separately authored execution packet.**

- **Slice γ (mixed):** wire cross-filter SQL between the breaker-half and
  trip-unit-half cascades — when both halves carry a selection, narrow
  the trip-unit cascade by the chosen breaker (and vice-versa where the
  DLL workflow supports it); UI scoping rules. **Not authorized by this
  packet — gated on Slice β landing and requires a separately authored
  execution packet.**

The TCC program closeout artifact's eight conditional triggers remain
unchanged. Trigger #3 (breaker-side hierarchy ownership) fired contract
revision → scoping ruling → this Slice α packet. Slices β and γ each need
their own separately authored execution packet to fire. No parity claim
is made against the EasyPower runtime; parity against
`FindMatchingBreakerStyles` requires β + γ to land first, and even then
is a separately scoped concern.

---

## §9. Bottom Line

Slice α (read-only ETU-distinct breaker-cascade backend) is the smallest
honest restoration of Contract Stage 1 into the ETU lane. It uses existing
`tcc_brk_*` tables, mirrors the DLL `FindMatchingBreakerStyles` join shape,
remains family-distinct from TMT and EMT, and adds zero risk to the frozen
validated trip-unit-rooted runtime baseline (32/32 adjacent regression PASS).

The endpoint is bounded, advisory-tagged, and read-only. Future Slice β
and Slice γ remain conditional follow-ons gated on separately authored
execution packets. No closed lane was reopened; no held or conditional
ruling was weakened; no fabricated default next packet was introduced.

Post-closeout authoring update:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-BETA-BREAKER-HALF-UI-AND-INVALIDATION-2026-04-29.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-beta-breaker-half-ui-and-invalidation-execution-handoff.md`

Those files author Slice β only. They do not pre-authorize Slice γ.
