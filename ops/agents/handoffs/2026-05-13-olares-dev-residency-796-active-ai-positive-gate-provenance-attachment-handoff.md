# Packet 796 Handoff - Active AI Positive-Gate Provenance Attachment

## Packet
- Packet ID: `2026-05-13-olares-dev-residency-796`
- Lane: bounded AI/operator positive-gate provenance hardening
- Scope: tighten the helper-backed host promotion artifact so later packet and two-lane closeouts can consume primary promotion provenance without reconstructing it from nested check payloads
- Change type: repo-owned helper truthfulness hardening, focused tests, and evidence-contract alignment

## Why This Packet
The current host-qualified promotion path is already proven through Packet `2026-05-13-olares-dev-residency-791`.

The next bounded follow-on named by the validation matrix was a provenance-hardening slice around that same helper-backed host path.

The remaining local gap was narrow: the helper artifact preserved the core proof, but later packet and handoff closeouts still had to pull the primary host run and promotion facts out of nested `checks` payloads instead of consuming them as first-class top-level provenance.

## What Changed
- Updated `tools/ai/capture_apex_jobs_promotion.py` so the emitted summary now preserves the helper tool identity, optional output artifact path, the top-level closed host run record, the matching host-success run list, and the top-level promotion record in addition to the existing detailed checks.
- Updated `tests/test_capture_apex_jobs_promotion_truthfulness.py` so the focused helper truthfulness surface now asserts that richer top-level provenance explicitly.
- Updated `docs/operations/APEX-JOBS-TRUST-AND-PROMOTION-CONTRACT-2026-05-08.md` so the Packet 791 note now records the Packet 796 provenance attachment floor.
- Updated `docs/operations/AI-BACKBONE-CANARY-EVIDENCE-BUNDLE-2026-05-08.md` so the optional emitted promotion artifact rules now name the richer helper provenance surface explicitly.
- Updated `PROJECT_STATUS.md` so Packet 796 is recorded as the current positive-gate provenance-attachment floor.

## Validation
- Focused helper tests: `& ".\.venv\Scripts\python.exe" -m pytest tests/test_capture_apex_jobs_promotion_truthfulness.py -q`
- Focused helper test result: `5 passed`
- Targeted markdown diagnostics: no diagnostics on the touched contract, evidence-bundle, status, and handoff files
- Repo-state check: only the expected Packet 796 files were pending before publication

## Repo-Visible Evidence
- `tools/ai/capture_apex_jobs_promotion.py`
- `tests/test_capture_apex_jobs_promotion_truthfulness.py`
- `docs/operations/APEX-JOBS-TRUST-AND-PROMOTION-CONTRACT-2026-05-08.md`
- `docs/operations/AI-BACKBONE-CANARY-EVIDENCE-BUNDLE-2026-05-08.md`
- `PROJECT_STATUS.md`
- `ops/agents/handoffs/2026-05-13-olares-dev-residency-796-active-ai-positive-gate-provenance-attachment-handoff.md`

## Outcome
Packet `2026-05-13-olares-dev-residency-796` closes the next bounded positive-gate provenance follow-on after Packet 795.

The helper-backed host promotion path now stays easier to consume in later closeouts without widening the admitted boundary:

1. the primary host run record is available at the top level,
2. the matching host-success runs are available at the top level,
3. the promotion record and repo-visible artifact path are available at the top level when emitted,
4. the existing nested checks remain intact for detailed truthfulness inspection.

The next bounded follow-on, if any, remains another similarly narrow provenance, rehearsal, or evidence-hardening slice, or a fresh coordinator-owned two-lane packet that reuses the Packet 786 model without widening controller scope.

## Boundaries Preserved
- No new MCP service was admitted.
- No `ai_tasks` ownership was admitted.
- No auth, ingress, or runtime scope widened.
- No host runtime behavior or business-logic surface changed.