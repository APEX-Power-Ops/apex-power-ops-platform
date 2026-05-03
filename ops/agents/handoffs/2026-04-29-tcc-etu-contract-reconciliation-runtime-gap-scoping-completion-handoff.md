# TCC ETU Contract Reconciliation / Runtime-Gap Scoping — Completion Handoff

Date: 2026-04-29
Status: Closed PASS — scoping-only lane lands inside contract
Purpose: Record completion of the ETU contract-reconciliation / runtime-gap scoping lane authorized by the 2026-04-29 DLL-authority revision

Authoring handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-contract-reconciliation-runtime-gap-scoping-handoff.md`
Scoping ruling: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-RULING-2026-04-29.md`
Task file: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-2026-04-29.md`

---

## §1. Outcome

The ETU contract-reconciliation / runtime-gap scoping lane required by the
2026-04-29 DLL-authority revision is **closed PASS**. The current ETU/SST
runtime represents **9 of 10** DLL-authored contract stages. The single
material runtime gap is **Stage 1 — upstream breaker-half identity surfaces**
(the `Manufacturers + BreakerXXX + BreakerXXXStyles WHERE ACDC = {0|1}` SQL
pattern preserved by `FindMatchingBreakerStyles()` at
`EasyPower.DeviceLibrary.DeviceLibrary.cs` line 403).

That gap is mixed end-to-end but honestly decomposes into **three
independently scopable later slices**: Slice α (backend-support, read-only
breaker-cascade endpoint), Slice β (frontend-only, breaker-half UI selectors
+ cross-half invalidation), and Slice γ (mixed, cross-filter SQL between
halves + UI scoping). The first later execution packet authorized by this
ruling is **Slice α only** — Slices β and γ remain conditional follow-ons
gated on Slice α landing and on a separately authored execution packet.

No code, schema, migration, runtime, calc-engine, TMT, or EMT change was made.
No closed lane was reopened. No held or conditional ruling was weakened. No
parity claim was made.

---

## §2. Required outputs delivered (6/6)

| # | Required output | Path / artifact |
|---|---|---|
| 1 | One scoping ruling under `Development/Platform/TCC/` | `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-RULING-2026-04-29.md` |
| 2 | One completion handoff under `ops/agents/handoffs/` | this file |
| 3 | Status / Completion Record updates on the task file | `Development/TASK-VSCODE-TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-2026-04-29.md` — Status banner + Completion Record updated |
| 4 | At least one focused verification or inspection step | endpoint inventory (19 endpoints, no breaker-cascade endpoint exists) + focused regression run (24/24 PASS) — see §4 below |
| 5 | One exact downstream ruling on later implementation shape | **Multiple later bounded slices, not one packet.** Slice α first; Slices β + γ conditional follow-ons. See §3 question 4. |
| 6 | One exact included / excluded-surface list for the first later execution packet | Scoping ruling §"Exact Included / Excluded Surface For First Later Execution Packet (Slice α)" |

---

## §3. Decision-boundary answers (5/5)

| # | Question | Answer |
|---|---|---|
| 1 | Which DLL-authored ETU contract stages are already represented? | **Stages 2–10 (9 of 10).** Manufacturer/type/style/sensor cascade (Stages 2–5) via `/cascade` over `vw_trip_unit_cascade`; sensor-rooted record (Stage 6) via `/context/{sensor_id}`; curve gating (Stage 7) via `/settings/{sensor_id}` post-resolution; sensor-rooted plug options (Stage 8); reverse plug-aware validation helper (Stage 9, Surface B closed PASS 2026-04-29); final sensor-rooted runtime record (Stage 10) feeds `/calculate`, `/evaluate`, `/plot-tcc`. |
| 2 | Which remain partial, flattened, or absent? | **Stage 1 — Absent.** No upstream breaker-half identity selectors in ETU lane; no `tcc_brk_*` queries in any ETU endpoint; the Surface C heuristic breaker-context label is explicitly provenance-tagged "derived" and is not a cascade. |
| 3 | Which gaps are frontend-only, backend-support, or mixed? | The single Stage 1 gap is **mixed** end-to-end but decomposes into: Slice α — **backend-support** (read-only breaker-cascade endpoint); Slice β — **frontend-only** (UI selectors + cross-half invalidation + step-indicator extension); Slice γ — **mixed** (cross-filter SQL between halves + UI scoping). |
| 4 | Does honest follow-on execution fit one bounded packet or multiple later slices? | **Multiple later bounded slices.** The first execution packet authorized by this ruling is Slice α only (read-only breaker-cascade backend over existing `tcc_brk_*` tables). Slices β and γ are conditional follow-ons gated on Slice α landing. |
| 5 | What exact surfaces must remain excluded? | (1) HTML edits during Slice α; (2) cross-filter wiring between halves during Slice α; (3) schema migrations; (4) reuse of TMT browse SQL helpers for ETU (family-distinct per Gap 5); (5) calc-engine / settings-route / calculate-evaluate-plot touch points; (6) TMT or EMT lane edits; (7) reopening any closed lane (Phase 3/4/5, ETU/SST trio, TASK-C, DEC-021, TASK-E); (8) fake breaker rows; (9) promoting plug / sensor rating to breaker-half identity; (10) any parity claim. |

---

## §4. Acceptance criteria (7/7 PASS)

Per the authority task §"Acceptance Criteria":

1. ✅ DLL-authored contract stages mapped explicitly against current runtime
   surfaces (scoping ruling §"DLL-Authored Contract Spine vs Runtime Mapping",
   10-row table).
2. ✅ Already-landed ETU/SST slices not accidentally reclassified as absent
   (Stages 8, 9 explicitly credit Surface B; Stages 2–5 explicitly credit
   Surface A+D guided-step indicator; Surface C credit preserved in audit-gap
   table Gap 4).
3. ✅ Breaker-half hierarchy handled as contract content without inventing
   fake runtime ancestry (Slice α scoped to read-only consumption of existing
   `tcc_brk_*` tables; no DDL; no synthesized rows).
4. ✅ Current runtime classified honestly as satisfied / partial / absent per
   contract stage (mapping table uses Represented / Absent only; no Partial
   classifications because the ETU/SST trio closed the prior partials).
5. ✅ At least one focused inspection step run (two: endpoint inventory + 24/24
   focused regression — see §"Focused Inspection Step" of the ruling).
6. ✅ Ruling states clearly whether later implementation is authorizable and
   in what packet shape (multiple later bounded slices α/β/γ; first packet =
   Slice α only).
7. ✅ No implementation or parity claim made (Slice α explicitly described as
   read-only catalog plumbing; no parity wording anywhere; mapping table uses
   structural language only).

Focused inspection step:

```
$ NETA_PREFER_DATA_API_READS=false ./.venv/Scripts/pytest.exe \
    tests/test_cascade_route.py \
    tests/test_settings_route.py \
    tests/test_etu_plug_reverse_filter.py \
    tests/test_etu_guided_step_indicator.py \
    tests/test_etu_breaker_context_provenance.py -v
======================== 24 passed, 1 warning in 3.31s ========================
```

Coverage: cascade route (5) + settings route (5) + ETU/SST trio Surface B (4)
+ Surface A+D (5) + Surface C (5) = 24 tests. All PASS. The single warning is
the pre-existing `models\base.py:7 MovedIn20Warning`, unchanged and unrelated.

The `test_provenance_disclosure_does_not_add_breaker_hierarchy` PASS confirms
Surface C closure deliberately did **not** add a real breaker hierarchy — the
gap remains exactly where the contract revision says it remains.

---

## §5. Stop-and-flag (5/5 NEGATIVE)

Per the authoring handoff §"Non-Negotiable Boundaries":

1. ✅ No repairs implemented. Documentation only — one scoping ruling, one
   completion handoff, one task-file update.
2. ✅ No widening from ETU/SST into TMT or EMT. TMT (`tcc_brk_*` queries +
   frame/amp/setting joins) and EMT (`emt_*` browse + section/band routes)
   left untouched.
3. ✅ No claim that current trip-unit-rooted runtime is contract-complete.
   Mapping table explicitly Absent on Stage 1; ruling §"Bottom Line" states
   "the single material runtime gap is Stage 1".
4. ✅ No fake breaker hierarchy invented. Slice α scoped to read-only
   surfacing of existing `tcc_brk_*` rows; Surface C's heuristic provenance
   disclosure preserved as-is; ruling explicitly excludes "promoting plug
   rating, sensor rating, or curve label to first-class breaker-half
   identity".
5. ✅ No parity claim. Stage classification uses structural words
   (Represented / Absent); no "matches EasyPower" / "byte-for-byte" / "live
   parity" wording.

---

## §6. Authority surfaces touched

| # | Surface | Action |
|---|---|---|
| 1 | `Development/Platform/TCC/TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-RULING-2026-04-29.md` | Added (scoping ruling) |
| 2 | `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-contract-reconciliation-runtime-gap-scoping-completion-handoff.md` | Added (this file) |
| 3 | `Development/TASK-VSCODE-TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-2026-04-29.md` | Edited — Status banner + Completion Record |
| 4 | `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-contract-reconciliation-runtime-gap-scoping-handoff.md` | Edited — Status banner only |

**Untouched (intentional):**

- The DLL-authority revision contract note (`TCC-ETU-CONTRACT-DLL-AUTHORITY-REVISION-2026-04-29.md`) — load-bearing authority, must remain untouched.
- The workflow audit (`TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md`) — load-bearing evidence, must remain untouched.
- The DLL architecture authority and DLL mapping/findings docs.
- `tcc_v5_backend/IMPLEMENTATION_STATUS.md` — already corrected by the contract-revision-completion handoff; further edits would be out of scope.
- All ETU/SST trio implementation evidence + closeout artifacts (Surface A+D, B, C).
- TCC program closeout artifact (`TCC-PROGRAM-CLOSEOUT-AND-DEFERRED-WORK-2026-04-29.md`) — its eight conditional triggers stand; this packet fires trigger #3 (breaker-side hierarchy ownership) by scoping only, not by reopening any closed lane.
- All runtime code (`router.py`, `schemas.py`, `neta_tcc.html`, models, migrations).
- All Phase 1–5 / TASK-C / DEC-021 / TASK-E / Tier B closure artifacts.
- The master orchestration plan (`tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`).

---

## §7. Hard limits honored

1. ✅ No code changes.
2. ✅ No schema, migration, or DDL changes.
3. ✅ No router or service-layer redesign.
4. ✅ No TMT or EMT widening.
5. ✅ No calc-engine work.
6. ✅ No parity claim.
7. ✅ No closed-lane reopening.
8. ✅ No fabricated default next packet (Slice α scope authorized; execution
   packet for Slice α not pre-authored).
9. ✅ No silent collapse of conditional lanes into active work (Slices β and γ
   explicitly held as conditional follow-ons).
10. ✅ No broadening into program redesign.

---

## §8. Bottom Line

The ETU contract-reconciliation / runtime-gap scoping lane is **closed PASS
2026-04-29**. The current ETU/SST runtime represents 9 of 10 DLL-authored
contract stages; Stage 1 (upstream breaker-half identity) is the single
material gap. The honest follow-on shape is multiple later bounded slices
α / β / γ. The first later execution packet authorized by this ruling is
**Slice α only** — a read-only breaker-cascade backend endpoint over existing
`tcc_brk_*` tables, with the included and excluded surfaces enumerated in the
ruling §"Exact Included / Excluded Surface For First Later Execution Packet
(Slice α)".

This handoff completes the contract-reconciliation scoping lane the 2026-04-29
DLL-authority revision required as the next move. It does not author or pre-
authorize Slice α's execution packet, does not pre-authorize Slices β or γ,
and does not weaken any closed ruling, held conditional, or accepted deferral
elsewhere in the TCC program.

Post-closeout authoring update:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-2026-04-29.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-alpha-breaker-cascade-backend-execution-handoff.md`

Those files author Slice α only. They do not pre-authorize Slice β or Slice γ.
