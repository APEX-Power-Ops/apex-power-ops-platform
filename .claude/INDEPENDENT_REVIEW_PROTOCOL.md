# Independent Review Protocol (IRP)

**Status:** Active standard — 2026-06-22. **Mandatory across all Apex lanes.**
**This doc = the definition.** Execution = the `/independent-review` skill + three `irp-*` Workflow templates (paths in §8).
**Origin:** distilled from the Chips 3–5 reviews — the brainstorm round, the custom-line reconciliation, the grain-widening vet, and the external Codex audit. Each of those caught defects single-pass authoring missed; IRP makes the mechanics that worked repeatable.

---

## 1. Why this exists

Independent, adversarial, cross-engine review repeatedly caught real defects that the author (me) would otherwise have shipped:
- The grain-widening vet's **adversarial pass** caught a blended-denominator defect written into the design.
- The **cross-engine** Codex audit caught a stale-doc contradiction and the D2 direction-vs-mechanics distinction the Claude agents hadn't.
- The brainstorm **proved same-model agents converge** (3 opus → one spine) — i.e. real diversity needs a *different engine*.
- **Source-grounding with honest gaps** kept the vets trustworthy even when the live DB was unreachable.

IRP standardizes those four mechanics so every change gets them.

## 2. The five invariants (every IRP review honors these)

1. **Independence by construction** — viewpoints are produced *blind to each other* (no-peek) and from *non-leading* prompts (guardrails only). No shared answer is assumed.
2. **Engine diversity** — multiple Claude agents **and ≥1 different engine** (Codex). Same-model agents converge; cross-engine is where genuine divergence comes from. The cross-engine pass is **non-negotiable at every tier**.
3. **Adversarial stage** — at least one pass is told to **refute / break**, not confirm; default-to-flag when uncertain.
4. **Source-grounding with honest gaps** — every claim ties to authoritative source (code / DB / spec). Anything that can't be verified is **stated as unverified**, never asserted.
5. **Synthesis + operator ratification** — reconcile viewpoints into *convergence vs. genuine forks*; the **operator's authority decides**. A finding is not a veto; a convergence is not a mandate.

## 3. Two modes

- **Viewpoint** — divergent *design exploration* (generate diverse independent designs/ideas for an open problem). Template: `irp-viewpoint-fanout`.
- **Audit** — adversarial *verification* of a built or proposed artifact (find what's wrong). Templates: `irp-design-panel` (compare/score candidate approaches) · `irp-grounded-audit` (verify an artifact against source).

## 4. Mandatory everywhere, proportional depth

**Every change is reviewed (no exemptions), and every review includes a cross-engine pass.** Only the *depth* scales with risk — this keeps mandatory-everywhere from decaying into ignorable ritual.

| Depth | When | Claude side | Cross-engine |
|---|---|---|---|
| **Light** | trivial / mechanical (doc edits, single-file fixes) | 1–2 agents (sanity + one adversarial) | 1 `codex exec review` pass, low reasoning effort |
| **Standard** | normal features / changes | 3–4 agents (multi-lens + adversarial verify) + synthesis | `codex exec review`, medium/high effort |
| **Deep** | schema / financial / irreversible / pre-merge | full fan-out (Viewpoint or Audit panel) + N-vote adversarial + grounded re-verify + synthesis | `codex exec review`, xhigh effort, structured-schema findings |

The **trigger never scales** — Light is still mandatory and still cross-engine.

## 5. The cross-engine gate (Codex)

**Verified contract (host, 2026-06-22)** — full detail in §9 and `[[codex-exec-host-contract]]`.

- **Preferred mechanism — apex-jobs:** enqueue a `kind=agent` job with **executor = `codex`** → durable, async, host-local (Codex runs where the dev DBs + code live). The job runs `codex exec review --base <base_ref> --json -o <out>` in the worktree; its output is captured as the job **result** (a *review job* = capture-result, **no promotion gate**). Requires wiring the codex executor into the apex-jobs agent-runner (the runner is engine-agnostic by design; see `[[orchestration-durable-multi-agent-2026-06-19]]`). Pre-build: confirm the review-job variant + reasoning-effort setting.
- **Fallback — operator-run packet:** until the apex-jobs codex executor is wired, the Claude side emits a **ready-to-run command + prompt**; the operator runs it on the host and pastes the result back. Always available.
- **Structured findings:** pass `--output-schema <file>` so Codex's verdict matches the Claude side's findings shape → uniform synthesis.
- **Reasoning effort:** set deliberately per depth (`-c model_reasoning_effort=…`); the default is **xhigh** (expensive).

## 6. Review record (the output of every IRP run)

- Subject · mode · depth
- **Convergence vs. genuine forks**
- **Findings** (severity + grounded evidence)
- **Cross-engine delta** — what Codex flagged that Claude didn't, and vice-versa
- **Verdict**
- **Unverified / grounding caveats**
- **Operator decisions surfaced** (with leans)

## 7. Triggers & ratification

- **Triggers (mandatory):** every spec sign-off, every pre-merge, every schema/financial/irreversible change. Light depth for trivia; **no exemptions**.
- **Ratification:** IRP informs; the operator decides. Findings and convergences are inputs to that decision, not the decision.
- **Composition with apex-jobs:** an apex-jobs **promotion gate may require a passing IRP review** before the operator approves a merge — IRP becomes the standing audit between "agent wrote a branch" and "operator merges it."

## 8. How to run

Invoke the **`/independent-review`** skill — it classifies mode + depth, runs the matching template, emits the cross-engine pass, and produces the review record. Templates (invoke via `Workflow({scriptPath, args})`):

- `C:\APEX Platform\.claude\workflows\irp-viewpoint-fanout.js`
- `C:\APEX Platform\.claude\workflows\irp-design-panel.js`
- `C:\APEX Platform\.claude\workflows\irp-grounded-audit.js`

(Canonical + version-controlled here in the platform governance repo. The `/independent-review` skill is junctioned into user-level `~\.claude\skills\` so it loads from any working directory — `C:\…`, `D:\…`, or the Olares host.)

## 9. Appendix — verified Codex contract

```
# host, over mesh ssh; prepend the node-v20 bin dir (holds node + codex)
ssh olares-mesh "export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH; \
  codex exec review --base <base_ref> --json -o /tmp/review.json \
  -c model_reasoning_effort=high  <<'PROMPT'
<the IRP review packet / instructions>
PROMPT"
```

- `codex exec [OPTIONS] [PROMPT|-]` — non-interactive; prompt as arg or stdin. `--sandbox read-only` for reviews · `-m/--model` · `-C/--cd DIR` · `--skip-git-repo-check` · `--json` · `--output-schema FILE` · `-o/--output-last-message FILE`.
- `codex exec review [PROMPT|-]` — code review: `--base <branch>` · `--commit <sha>` · `--uncommitted` · `--title` · `-m`.
- codex-cli **0.141.0**, default model **gpt-5.5**, headless auth persisted (`approval: never`). Caveats: default reasoning effort **xhigh** (set it); bubblewrap not installed (bundled fallback, non-fatal).
