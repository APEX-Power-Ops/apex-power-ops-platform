# TCC ETU / SST Guided-Selection Step-Indicator Implementation — Execution Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-etu-sst-guided-selection-step-indicator-implementation`
Status: Ready for execution.

Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SST-GUIDED-SELECTION-STEP-INDICATOR-IMPLEMENTATION-2026-04-29.md`
Scoping authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-REMAINING-GAP-SCOPING-RULING-2026-04-29.md`

## Objective

Implement the ETU / SST guided-selection step-indicator UI affordance authorized
by the scoping ruling's bundled Surface A + D slice.

This handoff authorizes UI-only work. It does not authorize backend changes,
schema changes, TMT / EMT work, breaker-hierarchy invention, or parity claims.

## Included Surface

1. Guided workflow rendering for manufacturer, type, style, and sensor.
2. Per-step counts from existing `/cascade` data.
3. Named-step identity tuple display fidelity.

## Excluded Surface

1. Backend or schema changes.
2. Plug-aware reverse filtering.
3. Breaker-context provenance disclosure.
4. TMT / EMT work.
5. Parity claims.
