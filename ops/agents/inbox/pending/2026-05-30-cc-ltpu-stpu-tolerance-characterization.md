---
dispatch_id: 2026-05-30-cc-ltpu-stpu-tolerance-characterization
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-relay-live-validation-parity
closeout: ops/agents/handoffs/2026-05-30-ltpu-stpu-tolerance-characterization-closeout.md
---

# LTPU/STPU tolerance characterization — close the open ±10 question (Breaker↔Relay Parity step 2)

**Lane:** TCC Breaker↔Relay Parity — **step 2 of 3** (calc parity; sequencing operator-delegated). **Operator authorization: GRANTED.** **CHARACTERIZE-BEFORE-FIX is a hard gate — surface findings before touching any calc code.** Follow the inbox lifecycle (claim-push BEFORE executing).

## Why
The INST/GFPU "drop-the-±10" correction (§58; find the fix commit, ~`ad79bc4d`) was characterized against DatSensor (17,831 rows): a NULL element tolerance ⇔ `PICKUP_CALC = -1` absent-element, so the old ±10 NETA-general fallback was **dead and spec-violating** → removed. `_calc_tolerance` in `packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_pickup.py` (≈ lines 637–662) now defaults a NULL `tol_lo/hi` to **0.0** (no band) for ALL elements; `_calc_element` passes `sensor.ltpu_tol_lo/hi`, `sensor.stpu_tol_lo/hi`, etc.

The **LTPU/STPU** side was never characterized — the open carry-forward. The ±10 isn't lingering in code; the question is whether the uniform **0.0 is spec-correct for LTPU/STPU**, or whether LTPU/STPU has a class the INST/GFPU finding didn't cover (element PRESENT but manufacturer tolerance NULL) that should instead get the NETA general tolerance.

## Goal — characterize first; fix only if warranted.

### Part 1 — CHARACTERIZE (read-only; this is the deliverable)
Mirror the INST/GFPU DatSensor analysis for LTPU and STPU. Against the live catalog (`tcc_etu_sensors` + the LTPU/STPU pickup tables; **read-only** via the DSN):
- For each sensor, classify LTPU and STPU: tolerance present vs NULL, cross-referenced with the element-present indicator (`PICKUP_CALC` / the absent-element marker used in the INST/GFPU work).
- Determine which holds: **NULL LTPU/STPU tolerance is ALWAYS an absent element** (⇔ the INST/GFPU finding → current 0.0 correct, old ±10 was dead), **OR there exist PRESENT LTPU/STPU elements with NULL manufacturer tolerance** (which the uniform 0.0 under-serves and which may warrant NETA general tolerance).
- Quantify — counts per class across the full sensor set (like the 17,831-row INST/GFPU characterization). Cross-check the §58 reasoning / DatSensor contract for what the engine SHOULD do.

**Surface the characterization to Desktop BEFORE writing any calc-engine change.** Outcomes:
- **(a) LTPU/STPU mirror INST/GFPU** (NULL ⇔ absent) → 0.0 is correct; **no code change** — lock the characterization + add a regression test asserting 0.0-band-for-absent. Done.
- **(b) LTPU/STPU differ** (present-element NULL-tolerance cases exist) → a fix is warranted (NETA general tolerance for present-but-NULL, 0.0 only for absent). Surface the proposed fix + spec basis; proceed to Part 2 only on Desktop confirmation.
- **(c) Ambiguous** → STOP and surface the specific ambiguity.

### Part 2 — FIX (only on outcome (b), and only after Desktop confirms)
Apply the characterized correction in `etu_pickup.py` (`_calc_tolerance` / `_calc_element`), mirroring the INST/GFPU fix shape. Then Part 3.

### Part 3 — RE-VALIDATE (only if Part 2 ran)
- ETU live parity probe `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py` → still PASS (or improved).
- calc-engine golden/unit suites green; change isolated to ETU tolerance handling.

## Verify
- **Part 1 (always):** the characterization (per-class counts, verdict a/b/c, spec basis). Read-only — no calc change.
- **If Part 2:** parity probe PASS + golden/unit green + isolated diff.

## Guardrails
- **Characterize-before-fix is a hard gate.** No calc-engine edit until the characterization is surfaced and (for outcome b) Desktop confirms.
- Read-only against the live catalog for Part 1.
- Any fix is isolated to ETU tolerance handling — do NOT touch pickup-current math, delay routing, or other elements.
- Scoped `git add`.

## Closeout
Record the characterization (per-class counts, verdict, spec basis), whether a fix was applied, and (if so) the re-validation (parity probe + golden). Then `git mv claimed/ → done/`, commit, push, return to Desktop. This closes the open LTPU/STPU ±10 question (parity step 2).
