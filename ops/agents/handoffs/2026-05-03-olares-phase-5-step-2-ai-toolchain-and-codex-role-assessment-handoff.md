# Olares Phase 5 Step 2 AI Toolchain And Codex Role Assessment Handoff

Date: 2026-05-03
Status: Complete
Scope: bounded packet-preparatory assessment of the intended Olares AI toolchain shape and Codex role only; no implementation, installation, promotion, or migration decision

## Authority

This handoff executes the assessment-only lane opened in:

1. `plan/infrastructure-olares-full-implementation-roadmap-1.md` Phase 5
2. `Infrastructure/Olares_Workspace_Authority_Framework.md`
3. `Infrastructure/Olares_Build_Guide.md`
4. `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md`
5. `.claude/DECISION_LOG.md`
6. `docs/architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md`

This handoff does not reopen generic Olares implementation.

## Tasks Covered

This handoff closes the evidence-gathering pass for:

1. `TASK-022` - assess the intended AI toolchain shape on Olares against current repo truth
2. `TASK-024` - assess the correct role of Codex in the Olares-hosted workflow and produce a bounded recommendation

This handoff informs but does not close:

1. `TASK-023` - services-zone AI/supporting-tool classification
2. `TASK-025` - split decision among workstation migration, AI-services expansion, code-hosting mirror, and canonical-hosting transition
3. `TASK-026` - packet-ready decision surface for future Olares expansion

This handoff does not authorize:

1. host runtime mutation,
2. Olares installs,
3. ingress or auth changes,
4. code-hosting changes,
5. Olares-first daily development migration.

## Executive Verdict

The intended Olares AI toolchain is richly documented as design intent, partially deployed at the Supabase orchestration layer, and almost entirely absent at the Olares host runtime layer.

Of the examined surfaces:

1. the Supabase-side `ai_*` orchestration schema is operational,
2. Claude Code on Max is operational off-Olares with a clear governed role,
3. Codex remains explicitly unresolved in `.claude/DECISION_LOG.md` while simultaneously treated as load-bearing in `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md`,
4. Ollama or local models, MCP fabric, Dify, n8n, the distinct `apex-jobs` run ledger, and any LiteLLM-style proxy remain design-intent only and are not part of the current Olares evidence floor.

The current Olares evidence floor remains bounded to:

1. workstation lane,
2. `forms-engine` and `p6-ingest` installed proof,
3. alias cleanup,
4. the host-only private `personal-notes` lane.

No AI-toolchain surface beyond off-host Claude Code is currently part of governed Olares truth.

Conclusion: conditionally ready after bounded decisions.

A narrow AI-toolchain packet is plausible only after explicit decisions are taken on:

1. the `ai_tasks` versus `apex-jobs` trust boundary,
2. closure of the open orchestration and Codex-role decisions in `.claude/DECISION_LOG.md`,
3. whether `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` is restated against current Olares boundaries or explicitly superseded.

Without those decisions, the lane is not ready.

## AI Toolchain Matrix

### Claude Code

Intent:

1. primary Claude gateway,
2. Max subscription path,
3. intended on both the laptop and the Olares One.

Repo-visible truth:

1. operational off-Olares,
2. governed role is clear,
3. not yet part of the current Olares-hosted evidence floor.

Bounded assessment:

1. first-slice candidate: yes,
2. defer: no,
3. open decision: whether the Olares-side install shares the same Max account session model and how MCP discovery behaves for laptop-client versus on-host-client usage.

### Codex

Intent:

1. `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` treats `codex-max` as a bulk Executor,
2. the deployed `ai_agent` enum includes `codex-max`,
3. Olares design documents are otherwise silent on Codex as a wired client.

Repo-visible truth:

1. no Codex install path on Olares,
2. no governed Codex MCP wiring,
3. no Codex env-tag rules,
4. `.claude/DECISION_LOG.md` leaves the role explicitly unresolved.

Bounded assessment:

1. first-slice candidate: no,
2. defer: yes,
3. governing contradiction: the orchestration protocol assumes Codex is load-bearing while the Olares build guidance does not.

### Ollama Or Local Models

Intent:

1. Olares-hosted local models over private mesh,
2. internal-only auth posture,
3. Open WebUI as a human chat surface.

Repo-visible truth:

1. not part of the current evidence floor,
2. not included in the governed Olares closure set,
3. no current live host proof.

Bounded assessment:

1. first-slice candidate: no,
2. defer: yes,
3. belongs to a later services-zone decision surface rather than the first AI-toolchain packet.

### MCP Fabric

Intent:

1. six intended servers: `apex-fs`, `apex-db`, `apex-p6`, `apex-forms`, `apex-jobs`, `apex-memory`,
2. MVP narrowing to the trio `apex-fs`, `apex-db`, `apex-jobs`.

Repo-visible truth:

1. not part of the current Olares evidence floor,
2. no landed Olares-hosted proof for the fabric,
3. unresolved placement between compose-only dev-zone services and Olares-installed app surfaces.

Bounded assessment:

1. first-slice candidate: conditional,
2. only one read-only server is credible in the first slice,
3. the six-server fabric is not a truthful first packet.

### Dify

Intent:

1. higher-level agent orchestration,
2. RAG pipelines,
3. workflow logging back into `apex-jobs`.

Repo-visible truth:

1. not installed,
2. not governed,
3. not part of current Olares closure state.

Bounded assessment:

1. first-slice candidate: no,
2. defer: yes,
3. too many unresolved dependencies on identity, RAG corpus, embeddings, and logging destination.

### n8n

Intent:

1. low-code orchestration for scheduled jobs,
2. possible replacement or wrapper for scripted scheduled work.

Repo-visible truth:

1. not installed,
2. not governed,
3. overlaps conceptually with recently landed systemd-based private-lane automation.

Bounded assessment:

1. first-slice candidate: no,
2. defer: yes,
3. requires a later explicit decision on whether it competes with or supersedes the current timer pattern.

### `apex-jobs` Ledger Versus `ai_tasks`

Intent:

1. `apex-jobs` is described as the current job context and sandbox-versus-host run ledger,
2. the framework treats env tagging and promotion refusal logic as load-bearing trust boundaries.

Repo-visible truth:

1. deployed Supabase orchestration uses `ai_tasks`, `ai_agent_state`, `ai_task_history`, `ai_knowledge`, `content_registry`, and `ai_handoffs`,
2. the schema reference does not expose an `env=sandbox|host` column on `ai_tasks`,
3. the `promote_packet` refusal contract is not currently visible as deployed logic.

Bounded assessment:

1. this is the most load-bearing unresolved contradiction in the AI-toolchain lane,
2. the repo evidence supports a likely layered design where an `apex-jobs` MCP surface fronts Supabase tables, but that trust boundary is not fully deployed,
3. the schema-side trust model cannot be deferred if later packets depend on it.

### ChatGPT Or Custom GPT

Intent:

1. optional second-opinion surface,
2. either via a small HTTP-to-MCP bridge or by pasting outputs manually.

Repo-visible truth:

1. no bridge exists,
2. no governed runtime evidence exists.

Bounded assessment:

1. first-slice candidate: no,
2. defer: yes.

### LiteLLM Or Proxy Aggregation

Intent:

1. local-model proxying only,
2. explicitly not for Anthropic routing.

Repo-visible truth:

1. not installed,
2. the constraint against Anthropic proxying is explicit and governed.

Bounded assessment:

1. first-slice candidate: no,
2. defer: yes,
3. any future packet must preserve the rule that local-model proxying must not front Anthropic access.

## Codex Role Recommendation

### Current State Of Authority

Current repo authority speaks in conflicting ways:

1. `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` treats Codex as a primary Executor,
2. `.claude/DECISION_LOG.md` leaves the Codex question explicitly open,
3. `Infrastructure/Olares_Build_Guide.md` does not name Codex in the client-wiring list,
4. `Infrastructure/VSCode_Build_Prompt.md` does not name Codex in the AI wiring list.

The orchestration protocol's assumption that Codex is load-bearing was not reconciled with the current Olares design boundary.

### Bounded Recommendation

Leave Codex out of the first Olares dev-workspace expansion slice.

Concretely:

1. not local executor on Olares yet,
2. not remote batch worker yet,
3. explicitly excluded from the first slice,
4. may only re-enter under a later packet after the trust-boundary and authority contradictions are closed in writing.

### Re-Entry Gate

Codex may be reconsidered only after all of the following are true:

1. the `ai_tasks` schema or the explicit `apex-jobs` ledger gains the required `env=sandbox|host` trust boundary and promotion-refusal logic,
2. `.claude/DECISION_LOG.md` closes the open orchestration and Codex-role questions in sections `8.2` and `8.3`,
3. `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` is re-stated against the current Olares boundary and dated accordingly.

### Risks Of Early Admission

1. trust-boundary leakage if sandbox-versus-host provenance is not enforced,
2. authority drift if Codex-driven completion bypasses the framework's non-silent promotion expectations,
3. identity ambiguity because no current Authelia or OIDC posture is documented for Codex,
4. ungoverned cost surface because Codex billing posture is not recorded in the Olares authority stack.

### Credible Later Benefit

Codex remains a plausible later fit for bulk-generation or unattended remote-batch work, but only after the re-entry gate above is satisfied.

## Current Contradictions And Unresolved Decisions

The following items must be reconciled before any narrow AI-toolchain packet is opened:

1. `apex-jobs` MCP run-ledger intent versus the deployed `ai_tasks` schema and missing env-tag enforcement,
2. Codex as a load-bearing Executor in the orchestration protocol versus silence or explicit openness in the current Olares authority stack,
3. whether `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` remains authoritative after the Olares transition,
4. Settings API limitations versus the intended internal-auth posture for a future Ollama install,
5. unresolved location of the MCP servers across dev zone, staging zone, or installed-app posture,
6. unresolved decision on whether laptop Claude Code or Olares-host Claude Code is the primary first-slice client surface,
7. the entire open AI orchestration decision block in `.claude/DECISION_LOG.md` sections `8.1` through `8.3`.

## Safe First-Slice Boundary

The lane is only conditionally ready for a narrow AI-toolchain packet.

That first slice is plausible only if it is bounded to:

1. deciding and documenting the `ai_tasks` versus `apex-jobs` relationship in writing,
2. declaring Claude Code as the only first-class Olares-side AI surface in the slice,
3. bringing up exactly one MCP server, not the full fabric,
4. closing the open `.claude/DECISION_LOG.md` orchestration questions,
5. re-stating or superseding `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` against the current Olares boundary.

Absent those decisions, the lane is not ready.

## Explicit No-Go Items For Now

1. no Codex install on Olares,
2. no Codex admission as local executor or remote batch worker,
3. no Ollama install under the AI-toolchain packet,
4. no Dify, n8n, or Open WebUI in the first slice,
5. no MCP fabric beyond one server,
6. no LiteLLM or equivalent Anthropic proxying,
7. no public ingress for any AI surface,
8. no promotion of the private personal lane into AI-toolchain scope,
9. no canonical-hosting change,
10. no silent reuse of the December 2025 orchestration protocol as if it were Olares-aware,
11. no collapsing Claude Code, Codex, local models, MCP, Dify, n8n, and run-ledger design into one undifferentiated decision.

## Recommendation

Recommendation: conditionally ready after bounded decisions.

The lane becomes ready for a narrow AI-toolchain packet only after the trust-boundary, orchestration-authority, and Codex-role contradictions above are closed in writing.

Codex specifically remains out of the first slice until the re-entry gate is satisfied.