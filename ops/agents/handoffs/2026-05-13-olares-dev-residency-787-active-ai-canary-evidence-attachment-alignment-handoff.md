# Packet 787 Handoff - Active AI Canary Evidence Attachment Alignment

## Packet
- Packet ID: `2026-05-13-olares-dev-residency-787`
- Lane: bounded AI/operator evidence-attachment alignment
- Scope: align the canonical canary evidence bundle with the current verifier contract after Packet 786
- Change type: repo-owned evidence-routing documentation hardening

## Why This Packet
Packet `2026-05-13-olares-dev-residency-786` extended `tools/ai/verify_minimal_mcp_trio.py` so verifier evidence now proves a closed sandbox run is visible through `apex-jobs list_runs`.

The canonical evidence bundle doc still stopped at `jobs_end_run` and promotion-refusal proof.

That mismatch left one narrow evidence-routing gap: the verifier artifact was richer than the repo-owned documentation that tells operators and packet closeouts what to capture.

## What Changed
- Updated `docs/operations/AI-BACKBONE-CANARY-EVIDENCE-BUNDLE-2026-05-08.md` so the example verifier summary now includes `jobs_list_runs` with a successful closed-run visibility record.
- Extended the minimum capture rules so `list_runs` ledger visibility is part of the canonical packet-local evidence bundle when emitted.
- Extended the handoff routing rules so closeout evidence explicitly carries the `list_runs` or equivalent ledger-visibility proof when present.
- Recorded Packet 787 in `PROJECT_STATUS.md` as the next bounded post-786 evidence-attachment follow-on.

## Validation
- Validation command: `get_errors` on `docs/operations/AI-BACKBONE-CANARY-EVIDENCE-BUNDLE-2026-05-08.md`
- Validation result: no diagnostics found

## Repo-Visible Evidence
- `docs/operations/AI-BACKBONE-CANARY-EVIDENCE-BUNDLE-2026-05-08.md`
- `PROJECT_STATUS.md`
- `ops/agents/handoffs/2026-05-13-olares-dev-residency-787-active-ai-canary-evidence-attachment-alignment-handoff.md`

## Outcome
Packet `2026-05-13-olares-dev-residency-787` closes the immediate evidence-attachment gap that remained after Packet 786.

The canonical repo-owned canary evidence contract now matches the emitted verifier artifact more closely: promotion-refusal proof, closed-run lifecycle proof, and ledger-visibility proof now route through one coherent packet and handoff evidence model.

The next bounded follow-on is a named validation-profile surface, not wider controller or queue admission.

## Boundaries Preserved
- No new MCP service was admitted.
- No `ai_tasks` ownership was admitted.
- No auth, ingress, or runtime scope widened.
- No business logic or product surface changed.