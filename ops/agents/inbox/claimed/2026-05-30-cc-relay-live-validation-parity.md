---
dispatch_id: 2026-05-30-cc-relay-live-validation-parity
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-tcc-phase-g3-relay-live-population
closeout: ops/agents/handoffs/2026-05-30-relay-live-validation-parity-closeout.md
---

# Relay live-data validation parity — bring relay to the breaker's proven-against-live-data standard

**Lane:** TCC Breaker↔Relay Parity — **step 1 of 3** (validation parity; sequencing operator-delegated 2026-05-30: "drive work in either or both lanes in sequences you determine"). **Operator authorization: GRANTED.** Follow the inbox lifecycle (claim-push BEFORE executing).

## Why (the parity gap)
The breaker (ETU) is validated against LIVE data by an **independent-reference probe**: `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py` driven by `apps/control-plane-api/scripts/etu_parity_matrix.json` (the "ETU SQL parity 3/0 vs prod" harness). Relay has **no equivalent**:
- Relay calc is golden-tested at the UNIT level only (`packages/calc-engine/tests/test_relay_golden_fixtures.py` vs frozen `fixtures/relay/golden_curves.json`) — synthetic, not live.
- The relay LIVE-integration test (`apps/control-plane-api/tests/test_neta_relay_live_integration.py`) is a SMOKE (pipeline returns 200/supported) and currently **SKIPS** — it grabs `sections[0]` (section 82782, no preview options) and bails at the "no stored preview options" guard.
- **Nothing checks** that, for the ACTUAL G-3 catalog (relays 1442 / 1.57M tcp points), the relay routes produce curves matching an INDEPENDENT reference.

## Goal — give relay the breaker's live-parity layer, in two parts.

### Part A — stop the smoke skip (quick; do first)
In `test_neta_relay_live_integration.py`, select the first supported section whose `settings.preview_options` is non-empty (or `preview_option_count > 0`) instead of blind `sections[0]`. Keep the environment guards (tables-absent / no-supported-sections) but eliminate the "no preview options" skip by **choosing** a section that has them. Result: against the loaded catalog the test RUNS green end-to-end (discovery → context → settings → preview).

### Part B — relay live-parity probe (mirror the breaker's harness shape)
Build `apps/control-plane-api/scripts/probe_live_relay_sql_parity.py` + `apps/control-plane-api/scripts/relay_parity_matrix.json`, modeled on `probe_live_etu_sql_parity.py` + `etu_parity_matrix.json`: a frozen representative cohort + an INDEPENDENT reference computed from the live catalog, compared to the relay route/calc output, summarized pass/warn/fail.

**Characterize first — the reference MUST be independent (do NOT write a circular check).** A probe that re-calls `plot-tcc` to "verify" `plot-tcc` proves nothing. Per `storage_kind` (confirmed in `golden_curves.json` — TCP stores `points`, the rest store `coefficients`):
- **`storage_kind = "points"` (TCP):** the curve IS the stored points. Reference = the stored points read DIRECTLY from the live catalog via SQL (the `work.tcc_relay_*` curve/point tables). Assert the route faithfully reproduces them at the stored current-multiples (exact / near-exact).
- **Formula families (IEC / SWZ / BSL / MEQ / PCD):** reference = the published standard inverse-time equation evaluated from the **stored coefficients** (read from the catalog) via an INDEPENDENT from-spec function — NOT a call into `relay_family_*`. Cross-reference the decoded evaluators in `D:\apex-power-ops-platform\spec\relay-family-scoping\05-tcc-relay-schema-proposal.md`.

If a non-circular reference for any family is unclear or expensive, **STOP and surface to Desktop** with the family + the specific ambiguity. Do not force a circular or hand-tuned assertion.

**Cohort:** representative sample from the LIVE catalog spanning the supported families actually loaded (TCP + whichever of IEC/SWZ/BSL/MEQ/PCD are present), a few sections each; freeze into `relay_parity_matrix.json` (td_section_source_id, family, storage_kind, reference inputs, expected values, current-multiples).

**Compare:** route output (`/api/v1/neta/relay/plot-tcc`) vs the independent reference within a **stated tolerance** — exact-ish for stored points; `rel`-class for formula eval (state a defined engineering tolerance if live coefficients carry rounding). Emit a pass/warn/fail summary like the ETU probe.

**Run target:** the configured live catalog via the governed DSN, **READ-ONLY** (pooler `ai-live-dsn.env` / `APEX_OLARES_LIVE_DSN` is fine — read-only). Local `apex_pm_stage.work` (identical data per G-3) is an acceptable dev fallback; record which DB the cohort came from.

## Verify
- **Part A:** `pytest apps/control-plane-api/tests/test_neta_relay_live_integration.py -q -rs` (DSN set) → RUNS and passes, **no skip**.
- **Part B:** run the probe → pass/warn/fail summary; cohort spans ≥2 families incl. TCP; the per-family reference method documented in the closeout; ideally also wire the probe behind a pytest marker.
- **Regression:** `packages/calc-engine/tests/test_relay_golden_fixtures.py` still passes; **no** calc-engine / route / schema / data change.

## Guardrails
- **Test / script / fixture only.** Do NOT modify the relay calc engine, routes, schema, or data. If the route genuinely disagrees with the independent reference, **STOP and surface** — that's a real finding, not something to loosen the tolerance around.
- Read-only against the live catalog. No writes.
- Scoped `git add` (the probe + matrix + the smoke-test edit only).
- Honor the characterize-first checkpoint before writing Part B assertions.

## Closeout
Record: Part A now-passing (section chosen); Part B cohort (families × sections, the independent-reference method per family, tolerances, pass/warn/fail counts), which DB the cohort came from, and ANY route-vs-reference discrepancies found (specifics). Then `git mv claimed/ → done/`, commit, push, return to Desktop. This closes relay validation parity (step 1) — relay reaches the breaker's proven-against-live-data bar.
