# TCC Runtime 017 Phase D ETU Needs-Evidence Review

Date: 2026-05-29
Status: PASS for fresh host-run active-runtime capability-gating proof; NO-GO for promoting the lineage helper set as active contract
Purpose: Record the repo-local evidence review for the Phase D ETU `needs-evidence` slice defined in the Runtime 017 remaining-task list

---

## 1. Governing Question

Phase D in `ops/agents/handoffs/2026-05-28-tcc-runtime-017-remaining-end-to-end-task-list.md` asks for focused browser proof on the ETU control-path and pickup-control helper slice, then a decision on whether the following should be promoted as part of the active contract:

- `getActiveSettingControlId`
- `getControlPathMode`
- `renderControlPathTags`
- `syncContinuousSettingInput`
- `syncEtuPickupControlModes`
- `applySettingValueIfApplicable`

This review answers that question using repo-local evidence only.

---

## 2. Evidence Reviewed

Repo-owned evidence surfaces reviewed:

1. `ops/agents/handoffs/2026-05-28-tcc-runtime-017-remaining-end-to-end-task-list.md`
2. `ops/agents/handoffs/2026-05-28-tcc-runtime-017-etu-live-sql-parity-and-local-host-refresh-closeout-handoff.md`
3. `ops/agents/handoffs/2026-05-29-tcc-etu-hardening-slices-1-4-closeout.md`
4. `apps/control-plane-api/demo/neta_tcc.html`
5. `apps/control-plane-api/tests/test_demo_browser.py`

Host limitation observed during this review:

- the sibling lineage source-domain path was not mounted on this Olares session, so this review does not rely on live side-by-side reads from `tcc_v5_backend`

---

## 3. What Is Proven In The Active Runtime

The active ETU demo already has repo-local logic that enforces the core user-visible behavior that Phase D cares about, even though it does not use the exact lineage helper names.

Current active-demo implementation evidence:

1. `setControlVisibility(...)` hides non-applicable ETU rows and clears stale control values when a row becomes inapplicable.
2. `isControlApplicable(...)` gates whether values are included in calculate/evaluate payload construction.
3. `syncEtuApplicableRows(settings, ctx)` derives ETU row visibility from the active settings payload plus context capability flags and applies that visibility to both setting controls and measured-value controls.

That means the active runtime already has contract-relevant behavior for:

1. trimming ETU controls to the resolved sensor capability,
2. preventing hidden controls from leaking stale values into payloads,
3. clearing stale measured values when the resolved sensor loses those elements,
4. clearing maintenance-mode state when MAINT is no longer applicable.

---

## 4. Existing Browser Proof Already In Repo

The strongest repo-local executable evidence is already present in browser coverage.

`apps/control-plane-api/tests/test_demo_browser.py` includes focused ETU proof that switching from sensor `25` to sensor `26`:

1. hides STPU, INST, GFPU, GFD, and MAINT rows when the newly resolved sensor lacks those capabilities,
2. clears stale GFPU setting and measured values,
3. clears the MAINT toggle,
4. preserves the applicable LTPU and LTD rows.

This is materially the same behavior Phase D asked to prove for the active runtime: the UI contract follows resolved sensor capability rather than preserving stale branch state.

The 2026-05-29 ETU hardening closeout also records this as an admitted PASS surface under slice 4 browser validation and slice 3 targeted browser validation.

---

## 4A. Fresh Host-Run Browser Proof

The active Olares host now also has fresh executable proof for the same Phase D behavior.

Focused command:

1. `PYTHONPATH=apps/control-plane-api .venv/bin/python -m pytest apps/control-plane-api/tests/test_demo_browser.py -k "sensor_change_hides_non_applicable_rows_and_clears_stale_values or upstream_sensor_change_clears_stale_execution_sections" -q`

Fresh host-run result:

1. `2 passed, 18 deselected, 2 warnings in 3.63s`

Local enabling repair required before the host proof could run:

1. `apps/control-plane-api/tests/test_demo_browser.py` now sets a placeholder `DATABASE_URL` for app import, matching nearby control-plane test practice.
2. the same test module now mocks `/api/v1/neta/etu/breaker-cascade` and `/api/v1/neta/etu/search` for the focused ETU sensor-change slice so the startup path remains fully governed on a DB-less host.

This closes the earlier evidence gap for the active runtime behavior itself: the capability-gating and stale-state-clearing path is now proven in a fresh host-run browser loop, not only inferred from previously committed notes.

---

## 5. What Is Not Proven

The named lineage helper set itself is not evidenced as active contract.

Repo-local finding:

1. the exact helper names listed in Phase D are not present in the active `apps/control-plane-api/demo/neta_tcc.html` surface,
2. the current repo-local evidence proves behavior, not those exact abstractions,
3. no repo-local browser proof in this review demonstrates control-path tags or lineage-style continuous-setting helper behavior as a promoted UI contract.

The practical result is:

1. there is enough evidence to say the active runtime already owns capability-gated ETU row visibility and stale-value clearing,
2. there is not enough evidence to say the lineage helper bundle should be promoted wholesale as part of the active contract.

---

## 6. Decision

Decision: PASS for the active-runtime Phase D behavior under fresh host-run proof.

Accepted as evidenced in the active contract:

1. capability-gated ETU row visibility,
2. stale-value clearing on sensor change,
3. payload exclusion for non-applicable controls,
4. MAINT applicability reset.

Not accepted as evidenced for promotion:

1. `getActiveSettingControlId`
2. `getControlPathMode`
3. `renderControlPathTags`
4. `syncContinuousSettingInput`
5. `syncEtuPickupControlModes`
6. `applySettingValueIfApplicable`

Reason:

- the repo proves the active behavior through different local abstractions, but it does not yet prove that these specific lineage-named helpers are required, present, or contract-defining in the active demo.

---

## 7. Recommended Follow-On

If a follow-on ETU parity slice is opened, it should be scoped as one of these two paths, not both at once:

1. active-contract documentation path:
   - document the current active ETU control-visibility and payload-gating behavior as the governing contract,
   - keep lineage helper names out of scope unless they are actually ported.

2. bounded parity-port path:
   - port one concrete lineage-visible behavior such as control-path tags or continuous-setting input handling,
   - add focused browser proof for that exact user-visible behavior,
   - only then decide whether the corresponding helper abstraction belongs in the active contract.

Until one of those happens, Phase D should be treated as closed only for the already-proven active behavior, and still open for any claim that the lineage helper set itself has been adopted.