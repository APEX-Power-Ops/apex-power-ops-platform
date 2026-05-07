# APEX Platform on Olares One — Blue-Sky Workspace Build Guide

_Reference: `Olares_Architecture.svg` (pin near workstation). Checklist: `Olares_Checklist.md`._
_Repo authority: `Olares_Workspace_Authority_Framework.md`._
_Authored 2026-04-22. Reviewed and revised 2026-05-06. Olares OS v1.12.5 baseline._

---

## 1. What this guide is

A concrete plan for turning a new Olares One into the center of gravity for APEX Platform development, staging, and field-accessible operation while keeping the laptop as a client surface rather than the durable workstation. The design deliberately lets you work from anywhere without forking your environment, but the governing direction is now Olares-first execution with GitHub still canonical.

Four load-bearing choices shape everything below:

1. **Three-zone layout on one box.** The Olares One hosts a *dev* zone (ephemeral, docker-compose, Olares-hosted), a *services* zone (shared long-running apps and host utilities), and a *staging* zone (APEX packaged as native Olares apps with SSO). This mirrors APEX's own two-zone architecture and enforces the "sandbox-complete ≠ end-to-end" rule at the infrastructure level.
2. **Hybrid packaging for APEX itself.** Dev iteration happens in plain Docker Compose for speed; promotion to the staging zone means authoring an `OlaresManifest.yaml` and installing via the Market as a private app. The staging zone is the only path to "complete."
3. **GitHub stays canonical while Olares becomes operationally primary.** `C:/APEX Platform` is still the transitional publication boundary, but `/home/olares/code/apex` is the durable host mirror and the target operating context for day-to-day execution.
4. **LarePass plus premium-model subscriptions beat day-one local model hosting.** LarePass is the network spine. Claude Code and Codex under monthly plans are the primary reasoning stack. Local-model services such as Ollama remain optional accelerators, not baseline requirements.

---

## 2. Hardware & OS baseline

The One ships as a dedicated personal-cloud device: Intel Ultra 9 275HX, NVIDIA RTX 5090 Mobile (24 GB GDDR7), 96 GB DDR5 (upgradeable to 128), 2 TB PCIe 4.0 NVMe (with a free PCIe 5.0 slot for expansion), Thunderbolt 5, 2.5 GbE, and a quiet profile (19 dB idle, under 39 dB at max). Power modes for the GPU are Silent (95 W) and Performance (175 W).

Olares OS is built on Ubuntu 24.04 LTS and runs workloads on K3s with Calico networking and Envoy as the ingress. System updates are free for the life of the device.

Relevant constraint: the HDMI output currently shows only a shell or Steam session, not the Olares web desktop. Treat the One as a **headless server with an optional local shell**, not as a traditional desktop PC. Your "sitting-at-the-box" workflow will be either (a) an external keyboard/monitor into the shell for admin work, or (b) a browser pointed at the Olares web UI from a nearby laptop / the One's own lightweight browser if you wire one in. Everything else is Remote-SSH or LarePass.

---

## 3. Network & access — reach from anywhere without exposing anything

Your answer about Parsec was the key signal: you already live a remote-workstation lifestyle. Keep that, and add two layers.

**Layer 1 — LarePass VPN (primary).** LarePass is Olares' built-in identity + WireGuard/Headscale control plane. Install LarePass on your laptop, iPad, and any teammate's device; approve each device once; they now have encrypted mesh access to the Olares One from anywhere. This is how you'll reach the MCP fabric, the Olares-hosted repo mirror, and the APEX field/office/admin UIs day-to-day. No public attack surface.

**Layer 2 — Parsec (GUI streaming).** Keep Parsec installed on the One for the cases where you need a responsive full desktop remotely — heavy VS Code sessions, screen-sharing with a teammate, running a Windows-only tool if that ever comes up. Parsec is complementary to LarePass, not redundant: LarePass gives you *network* access; Parsec gives you *pixels*.

**Layer 3 — Cloudflare Tunnel or Olares Tunnel (deferred).** Only stand this up when a real need appears — e.g., a field lead on a job site without the LarePass app installed, or a client-facing portal. When you do, put Authelia in front with MFA, and expose only the public-facing APEX UIs, never the MCP endpoints or the raw DB.

**Recommended sequencing.** Day 1: LarePass for you, Parsec for the fallback. Week 2: LarePass for one teammate as a test. Month 2+: Cloudflare Tunnel if and only if you hit a concrete remote-access requirement LarePass doesn't cover.

---

## 4. The three zones on one box

This is the mental model that makes the rest of the design make sense.

**Dev zone.** Ephemeral. Runs inside a docker-compose stack in the APEX monorepo — Postgres, any bounded supporting services, and the MCP servers. VS Code Remote-SSH (or code-server via browser) attaches to the monorepo directly on the Olares host. Hot-reload, fast iteration, no SSO, bound to localhost or the LarePass mesh. Sandbox, by definition. Canary tests run here; packet-promote operations are blocked here by design.

**Services zone.** Long-running. Olares Market apps and Linux host services that support the dev and staging zones: Authelia/LLDAP built-ins, Syncthing, Restic, optional Qdrant, optional n8n, optional Dify, optional code-server, optional Open WebUI, and optional Ollama. These are shared capabilities, not proof that APEX is complete.

**Staging zone.** APEX packaged properly. Each APEX service (`forms-engine`, `p6-ingest`, `sync-service`) gets an `OlaresManifest.yaml` that declares required middleware, entrance URLs, and OIDC integration with Authelia. Optional model-serving dependencies can be added later if they are genuinely justified. The three UI surfaces (`apex-field`, `apex-office`, `apex-admin`) become installable private Market apps. This is the host-bootstrap environment — packet-promote only succeeds with a run ID originating here.

Physically the three zones are all on one box. Logically they are separated by K3s namespaces, Postgres databases, and Olares' `system-server` permissions layer.

---

## 5. Olares Market apps and host services — the baseline install set

### Day-one baseline

- **Files · Vault · Drive · Dashboard** — Olares built-ins; leave them enabled.
- **Syncthing** — bidirectional file sync to field tablets and support devices when that workflow opens.
- **Restic** — encrypted offsite backups. Configure this in the first week.
- **Gitea (optional)** — local Git mirror of the APEX monorepo if you want disconnected review or mirror insurance. Keep GitHub as the canonical origin.
- **code-server or VS Code Remote-SSH** — secondary browser IDE surface only if Remote-SSH alone proves insufficient.

### Conditional, not baseline

- **Qdrant** (or **Weaviate**) — add only when a real retrieval workload appears for NETA forms, estimates, or P6 corpora.
- **n8n** — add when scheduled operational workflows exist and justify their own service boundary.
- **Dify** — add when you have a specific orchestrated workflow that benefits from it more than from scripts plus MCP plus premium interactive tooling.
- **Open WebUI** — add only if a browser-native shared chat surface becomes useful.
- **Ollama** — optional local-model runtime for offline, GPU-local, or cost-buffered workloads only after a concrete need appears. It is not a day-one requirement.
- **Jupyter** — optional for exploratory notebooks if the repo develops a notebook-heavy analysis lane.

Skip ComfyUI unless you actually need image generation for APEX narrative or presentation work.

---

## 6. AI orchestration on Olares — concrete wiring

The primary AI operating model is **plan-authenticated premium tooling first, local models second**.

That means:

1. **Claude Code on Max** is the default Claude surface.
2. **Codex on a subscription-authenticated OpenAI surface** is the default second premium reasoning and coding surface.
3. Anthropic or OpenAI API billing stays exceptional, not routine.
4. Local model hosting is optional and should be introduced only when offline operation, GPU-local batch work, or a clear economic case justifies it.

### Default AI stack

- **Claude Code** — installed on both the laptop and the One; authenticated with your Anthropic account under the monthly plan, not an API key. `CLAUDE.md` at the monorepo root. Subagent configs per service boundary (`.claude/agents/forms-engine.md`, `.claude/agents/p6-ingest.md`, `.claude/agents/ui.md`).
- **Codex** — available as the second premium reasoning and coding surface under the monthly OpenAI plan rather than API metering.
- **Claude Desktop** — optional laptop-side review and MCP client surface.
- **ChatGPT** — optional second-opinion or UX-review surface when useful.

### Local model stack

Local models are explicitly optional.

If a later packet justifies them, the preferred shape is:

1. **Ollama** with authentication level set to `Internal`,
2. **Open WebUI** only if a browser-native local chat surface is useful,
3. local embeddings or retrieval services only when a real corpus workflow exists,
4. no public exposure beyond the LarePass mesh.

Until such a packet exists, do not treat Ollama as a blocker or prerequisite for the Olares build.

**The MCP fabric.** Build the currently admitted trio as a set of small services in the APEX monorepo at `services/mcp/`:

- `apex-fs` — filesystem server scoped to the host parent-root mirror `~/code/apex`, its active implementation lane `~/code/apex/apex-power-ops-platform`, and `~/apex-data`
- `apex-db` — Postgres reader (read-only by default; `apex-db-write` gated behind an env flag)
- `apex-jobs` — current job context, packet status, the sandbox-vs-host run ledger

Future expansion candidates such as `apex-p6`, `apex-forms`, and `apex-memory` stay closed until they are admitted by a separate packet and authority update.

Run the MCP services in the dev zone during development (docker-compose), then package the stable ones as OlaresManifest apps so they persist across reboots and are reachable over LarePass. Every admitted client should point at the same bounded set.

**Client wiring.**

- **Claude Code** — primary interactive engineering surface.
- **Codex** — second premium engineering surface where it adds value.
- **Claude Desktop** (laptop) — configure MCP servers in `claude_desktop_config.json` pointing at the LarePass-reachable URLs of the `apex-*` servers.
- **ChatGPT** — use loosely for second opinions or alternative framing when useful.
- **Dify / n8n** — deferred until a real unattended workflow exists. When you do introduce them, they should call the MCP fabric and premium plan-authenticated tooling only under a bounded cost and trust model. Do not add them as ceremony before a real job exists.

**Why not LiteLLM?** Because routing Claude or Codex through API brokers defeats the core economic decision here: use the monthly plans first. Skip proxy indirection until a later packet proves that an API-budgeted broker is materially better than direct plan-authenticated tooling.

---

## 7. APEX packaging — dev raw, staging native

Of the four options you considered, the right path is the hybrid: **develop in plain Docker Compose inside the monorepo; promote to OlaresManifest for the staging zone.** Reasoning:

Native Olares packaging (Helm + OlaresManifest) is real work — permissions, manifests, chart iteration, Market-submission smoke tests. Paying that cost on every tight dev loop will slow you down. But *not* paying it at all means you never get the payoff: SSO, multi-user, LarePass-aware URLs, per-app Postgres isolation, entrance registration in the Olares Desktop. Those are exactly the things that make APEX feel like a product rather than a pile of services.

The hybrid captures both. Compose runs the dev zone; OlaresManifest runs the staging zone. A service gets promoted to native when its compose definition stabilizes — interface is stable, tests are green, you're no longer restarting it five times a day. In practice the first service to graduate is probably `forms-engine` (the current priority import) because it's well-scoped and the core generators already exist. `p6-ingest` follows once the schema alignment work is stable. UI apps graduate when they stop being scaffolds.

For supporting services that are not themselves the APEX product, prefer the least-ceremony host-native surface that preserves governance: Olares Market app when mature and useful, ordinary Ubuntu or Linux service when simpler, and OlaresManifest only when you need the full staged product posture.

**Repo layout under `infra/olares/`:**

```
infra/olares/
  charts/
    forms-engine/
      Chart.yaml
      OlaresManifest.yaml
      templates/
    p6-ingest/
    apex-field/
    apex-office/
    apex-admin/
  scripts/
    promote.sh       # compose → olares chart diff + lint
    validate.sh      # schema + canary check before install
```

The `promote.sh` script is worth writing: it reads a service's `compose.yml`, diffs against the expected OlaresManifest, and flags drift. Stops you from silently diverging dev and staging.

---

## 8. Monorepo layout — where everything lives

Your existing `APEX Platform/` folder already has `apps/`, `packages/`, `source-domains/`, `spec/`, and the in-progress `apex-power-ops-platform/` (the unified repo). The shape that scales:

```
apex/ (monorepo root)
  apps/
    apex-field/        # three UI surfaces
    apex-office/
    apex-admin/
  packages/
    shared-types/
    p6-schema/
    neta-forms-core/
    api-client/
  services/
    forms-engine/
    p6-ingest/
    sync-service/
    mcp/
      apex-fs/
      apex-db/
      apex-p6/
      apex-forms/
      apex-jobs/
      apex-memory/
  infra/
    compose.dev.yml
    olares/
    k3s-local/         # raw manifests for anything not yet OlaresManifest-ized
  tools/
  docs/
  spec/                # existing domain spec, verbatim
  .claude/
    CLAUDE.md
    agents/
    mcp.json
  .vscode/
    settings.json      # Peacock colors per workspace
```

On the Olares One filesystem: clone the parent-root mirror to `~/code/apex`, with active implementation work under `~/code/apex/apex-power-ops-platform`. Job files and estimate data live at `~/apex-data/` — mount this into services (both compose and OlaresManifest) as a shared read/write volume. Keep them separate: `apex/` is source mirror; `apex-power-ops-platform/` is the implementation lane; `apex-data/` is state. This path shape preserves publication semantics but does not by itself approve migration of daily development onto Olares.

---

## 9. Multi-user and identity — use Olares' auth as APEX auth

This is an easy win most people miss. Olares ships with Authelia (SSO/MFA) backed by LLDAP. Instead of rolling your own auth for APEX, wire each APEX UI app as an OIDC client against Authelia. You get:

- One login for everything on the box — Olares apps, Market apps, APEX UIs.
- LarePass as the device-trust layer (device approval before VPN + SSO session).
- LLDAP groups map cleanly to APEX roles: `jason-admin`, `estimator`, `field-lead`, `reviewer`.
- Adding a teammate is one operation — create the LLDAP user, assign groups, they get access to the right APEX surfaces automatically.

Exercise this from week one even as a solo user, so the wiring is broken in early while you're the only victim.

---

## 10. Ergonomics — the small stuff that compounds

- **Three VS Code workspaces** colored distinctly via Peacock: Field (blue), Office (green), Admin (amber). The color tells you which UI you're editing before you read any code.
- **Zellij (or tmux) layouts** saved per service: `apex-forms`, `apex-p6`, `apex-ui`. `zellij attach apex-forms` brings up the exact terminal arrangement you ended yesterday with.
- **Shell aliases**: `apex-dev` → compose up dev stack; `apex-stage` → apply/upgrade OlaresManifest charts; `apex-canary` → run the regression suite.
- **MOTD on the One** that always shows current zone status: which compose stacks are up, which Olares apps are running, last canary result. Saves the "what's the state of the box?" guesswork.
- **Zone-distinct hostnames**: dev-facing URLs on `*.dev.olares.local`, staging on `*.stage.olares.local`. Muscle memory keeps you out of trouble.

---

## 11. Backups and data safety

This is the most boring section and the most important. Set up on day one, not day thirty.

- **Restic** installed from the Market. Target: an external 2.5" drive via Thunderbolt *and* an S3 bucket (Backblaze B2 is cheap). Two targets, because one backup is zero backups.
- **Nightly Postgres dumps** of every APEX database (dev + staging + each Market app's DB that holds real work). Dumps go into the Restic pipeline.
- **Weekly JuiceFS snapshot.** JuiceFS supports it natively.
- **Pre-ingest snapshot.** Before any P6 XER import via `p6-ingest`, snapshot the staging DB. Project Miner runs are not idempotent; a corrupted input can poison downstream tables.
- **APEX code in Git, OlaresManifests in Git, compose files in Git.** Nothing config-like lives only on the box.

Verify restores quarterly. The backup you've never restored isn't a backup.

---

## 12. Trust and audit guardrails — enforced in the platform

Bring the earlier conversation down into concrete hooks:

- **`env=sandbox | host` tag** written by every agent run to `apex-jobs`. The `packet-promote` RPC refuses to mark a packet complete without at least one `env=host` run on record.
- **Provenance metadata** required on every AI-generated field in a NETA form or estimate — source of each value (DB-retrieved vs. inferred). UI surfaces inferences distinctly for human review.
- **Schema validation gates** between the model's output and the DB. A form with out-of-range torque values, mismatched units, or missing required fields never reaches the DB.
- **Canary suite.** A handful of historical jobs — starting with Stack Data Center — with known-good outputs checked into `tests/canary/`. `apex-canary` re-runs the full pipeline against them and diffs. Failure means you don't ship.
- **Two-pass review.** Local model drafts, Claude Sonnet reviews and flags, you review flags. Encoded as a Dify workflow so it runs the same way every time.

These aren't optional hardening steps bolted on later. They're the reason the whole design works — they turn un-auditable AI output into auditable AI output.

---

## 13. Provisioning order — the first 72 hours

High level; see `Olares_Checklist.md` for line-item steps.

**Hour 1–4 (unbox).** Power on, run Olares activation, set admin password, register your first Olares ID. Install LarePass on your laptop. Approve laptop as a trusted device. Verify the laptop can reach the One over LarePass.

**Hour 5–12 (network + identity).** Configure a `.local` domain or a custom domain (Olares supports either; defer the custom domain if not ready). Create LLDAP groups: `admin`, `estimator`, `field-lead`, `reviewer`. Create your own user in `admin` + `estimator`. Verify Authelia login flow.

**Day 1 evening (baseline services).** Install Syncthing and Restic first. Add Gitea only if you want a local mirror. Defer Ollama, Open WebUI, Dify, n8n, and Qdrant unless a concrete near-term workload already justifies them.

**Day 2 morning (dev tooling).** SSH in from laptop. Install Node (fnm or volta), pnpm, uv for Python, Docker (already present via K3s), code-server (optional). Clone the APEX monorepo. Bring up `compose.dev.yml`.

**Day 2 afternoon (MCP fabric).** Scaffold the admitted `apex-fs`, `apex-db`, and `apex-jobs` MCP servers in `services/mcp/`. Add `CLAUDE.md` at repo root. Install Claude Code on both the laptop and the One; authenticate with Max. Verify Codex access on the laptop and optionally on the One as the second premium engineering surface.

**Day 2 evening (wire Claude Desktop).** Configure Claude Desktop's MCP clients to hit the three LarePass-reachable MCP endpoints. Smoke test: "read a NETA form file, query a sample row from apex-db, and write a test case." If all three tool calls succeed, the fabric is sound.

**Day 3 (first graduation).** Author an `OlaresManifest.yaml` for `forms-engine`. Install as a private Market app. Run the canary against it. If canary passes, you have your first working dev→staging promotion loop.

After that: it's incremental. Graduate more services, add teammates, add the field-tablet sync flow once the UI is real enough to put in front of a field lead.

---

## 14. What this gets you, a month in

If you execute the above:

- You can open a laptop anywhere on the planet with LarePass installed and be in your full dev environment in under a minute.
- Claude Desktop, Claude Code, Codex, and any custom GPT all share the same APEX context via the MCP fabric — you stop re-explaining the domain with every new chat.
- Dev iteration happens fast (compose), but "complete" has a real meaning (staging, canary-gated).
- The premium monthly plans cover the bulk of reasoning and coding work; API billing stays exceptional, and local models remain an optional later acceleration lane rather than a prerequisite.
- Trust in AI-generated work is earned by measured canary pass-rates, not granted by faith.
- Teammates get access via one LLDAP entry, not a pile of bespoke credentials.
- The Cupertino / Stack Data Center packet workflow is the first real test — and the canary against it is what tells you the system is ready to scale to the next job.

---

## Appendix A — Open questions to revisit

- Does any real near-term workflow justify Qdrant, Dify, or n8n, or should they stay deferred until a concrete retrieval or automation job exists?
- Does any real near-term workflow justify Ollama or Open WebUI, or are Claude Code plus Codex sufficient for the first operating phase?
- Does Parsec-from-One-as-host work acceptably given the HDMI limitation? (Parsec can run headless but verify once you have the hardware.)
- When do field tablets actually need to reach the box — before or after you have a stable `apex-field` UI? That ordering determines when Cloudflare Tunnel becomes real.
- GitHub remains canonical during the current migration. Revisit mirror strategy only after Olares-first operations are dominant enough to justify changing the publication boundary.
