---
name: independent-review
description: Run a mandatory Independent Review (IRP) on a design, spec, change, or branch before sign-off/merge. Multi-agent + adversarial + cross-engine (Codex). Use for every substantive change, and whenever the user asks to review/audit/get independent viewpoints on work. Picks Viewpoint vs Audit mode and Light/Standard/Deep depth, runs the matching workflow, runs the Codex cross-engine pass, and produces a review record for operator ratification.
---

# Independent Review (IRP)

Runs the Independent Review Protocol. **Full standard:** `C:\APEX Platform\.claude\INDEPENDENT_REVIEW_PROTOCOL.md` (read it if unsure of the invariants/depth bands).

**The five invariants (hold all):** independence-by-construction (blind, non-leading) · engine-diversity (Claude agents **+ Codex**, always) · an adversarial refute-stage · source-grounding with honest "unverified" flags · synthesis + operator ratification.

## Steps

1. **Classify.**
   - **Mode:** *Viewpoint* (divergent design for an open problem) or *Audit* (verify a built/proposed artifact).
   - **Depth** (by risk): *Light* (trivial/mechanical) · *Standard* (normal change) · *Deep* (schema/financial/irreversible/pre-merge). Depth scales agent count + effort; the cross-engine pass is **always** included.

2. **Run the matching template** via `Workflow({ scriptPath, args })`:
   - Viewpoint → `C:\APEX Platform\.claude\workflows\irp-viewpoint-fanout.js`
   - Audit, compare approaches → `C:\APEX Platform\.claude\workflows\irp-design-panel.js`
   - Audit, verify against source → `C:\APEX Platform\.claude\workflows\irp-grounded-audit.js`
   - Pass `args = { subject, problem/constraints, depth, … }` (see each template's `meta.description`). For Deep, supply distinct `lenses`/`probes`/`seeds` so the agents diverge.

3. **Cross-engine pass (mandatory).** Run Codex on the same artifact:
   - **Preferred:** enqueue an apex-jobs `kind=agent` job, executor `codex` (durable/async/host-local) — once that executor is wired.
   - **Fallback (now):** emit a ready-to-run command for the operator and fold the returned findings into the synthesis:
     ```
     ssh olares-mesh "export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH; \
       codex exec review --base <base_ref> --json -o /tmp/irp-codex.json -c model_reasoning_effort=high" <<'PROMPT'
     <the review packet>
     PROMPT
     ```
   - Use `--output-schema` when you want Codex findings in the same shape as the Claude side.

4. **Synthesize the review record:** convergence vs genuine forks · findings (severity + grounded evidence) · **cross-engine delta** (what Codex caught that Claude didn't, and vice-versa) · verdict · unverified/caveats · operator decisions with leans.

5. **Surface to the operator for ratification.** IRP informs; the operator decides.

## Notes
- This is **mandatory everywhere** — Light depth still runs, and still includes Codex. Don't skip; right-size.
- Ground every claim; flag the unverifiable. Never assert what you couldn't check.
- If the mesh is down, the Codex pass is blocked — say so and proceed with the Claude side flagged as cross-engine-pending (see `[[mesh-check-on-start]]`).
