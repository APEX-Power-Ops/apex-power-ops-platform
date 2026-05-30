---
dispatch_id: 2026-05-30-cc-relay-phase-4-readonly-preview
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-05-30-relay-phase-4-readonly-preview-closeout.md
---

# Relay Sub-Lane — Phase 4 read-only interactive trip-envelope preview

**Lane:** TCC relay sub-lane (NETA tool, in-repo). Builds on the DONE read-only base — six golden-tested calc families (TCP/IEC/MEQ/BSL/SWZ/PCD), the read-only API `/relay/{sections,context,settings,plot-tcc}`, and the browser compare surface. **Operator authorization: GRANTED 2026-05-30** — open Phase 4 *read-only* preview. (Full scoping/authority packet lives in the substrate: `apex-ops-substrate/.claude/PLATFORM/RELAY_PHASE_4_READONLY_ENRICHMENT_SCOPING_2026-05-29.md`; this dispatch is self-contained.)

## What you're building (the protection_explorer interaction pattern, governed + read-only)
What-if sliders on relay settings (pickup, time-delay, voltage thresholds) → real-time trip-envelope recalc → multi-curve overlay (baseline vs proposed vs optional standard reference) → click-to-drop fault-current markers. Borrow the *interaction pattern* only — NOT any Banner-project content/narrative.

## HARD boundary (do not cross)
- **Read-only / ephemeral only.** Candidate settings are evaluated + rendered, **NEVER persisted**. No saved comparisons, no notes, no workspaces, no DB writes, **no mutation-seam**. (That is the deferred Phase 3 write-workflow — it STAYS deferred.)
- **Governed server-side math only.** Reuse the existing six calc families. **NO browser-side relay math** (the prior governance memo reserved that too).
- Model codes **7–9 (RXD/LRM/EGC) stay gated** — out of scope unless separately scoped.

## Bounded slices
- **R1 — stateless what-if preview (backend).** First confirm whether `POST /relay/plot-tcc` already accepts candidate/override settings. Prefer **extending that existing route** to accept candidate overrides and return the recomputed trip envelope via the governed calc families — NOT a new route, NOT browser-side math. No persistence. Route tests: (a) baseline (no overrides) == the current `/relay/settings`-seeded envelope; (b) an override changes the envelope; (c) an invalid override surfaces cleanly (no 500).
- **R2 — interactive preview (frontend).** On the `relay-resource-explorer` / compare surface, add what-if sliders bound to the baseline `/relay/settings` values → debounced call to R1 → live curve re-render; multi-curve overlay (baseline vs what-if vs optional standard reference); fault-current marker. Read-only; nothing saved.
- **R3 — proof.** Browser proof of the slider → recalc → overlay loop (DB-less mock pattern is fine where the live DB isn't available, same as Phase E3); relay family smoke green; **no regression** to the read-only base (existing `/relay/*` route + compare tests stay green).

## DB / environment posture (same as Phase F)
Any live surface points at the governed Supabase via `APEX_OLARES_LIVE_DSN` (`source /home/olares/apex-secrets/olares/ai-live-dsn.env`); **no local PG**; **read-only**. R3's browser proof can use DB-less mocks for the wiring loop (route correctness is covered by R1 tests).

## Guardrails
- Local-commit + push at closeout (inbox protocol). **Scoped `git add`** (never `-A`). Exclude residue (`.vscode/tasks.json`, `output/`).
- If R1 finds `/relay/plot-tcc` cannot cleanly carry overrides and a contract change beyond a bounded extension is needed, **STOP and surface to Desktop before widening** — do not invent a new contract unilaterally.

## Closeout
Write the closeout to the `closeout:` path. Record: R1 route decision (extended existing vs gap surfaced) + tests; R2 wiring + browser proof result; R3 smoke + no-regression evidence; and confirm the read-only / no-persistence boundary held. Then `git mv` this dispatch `claimed/` → `done/`, commit, push. Return to Desktop for review (after which TCC-G hosted becomes the next operator-gated decision).
