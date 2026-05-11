# APEX Platform on Olares One - Blue-Sky Workspace Build Guide

_Repo-owned guidance copy established 2026-05-07 so the active Olares build guide lives inside the canonical repo boundary._
_Keep the historical parent-root Infrastructure copy aligned until the broader authority relocation lane is complete._

_Reference: `Olares_Architecture.svg` (pin near workstation). Checklist: `../operations/OLARES-CHECKLIST.md`._
_Repo authority: `OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`._
_Authored 2026-04-22. Reviewed and revised 2026-05-06. Olares OS v1.12.5 baseline._

Closeout interpretation note:

This guide is now a retained architecture and first-run design reference for the Olares lane, not the default active operator entrypoint for current repo work.

Current routing:

1. use `OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md` for the governing authority order and boundary rules,
2. use `../architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md` for the current Olares operating model,
3. use `../../plan/infrastructure-olares-full-implementation-roadmap-1.md` and `../architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md` for maintained closeout, rerun, and trigger guidance,
4. use this guide when the original Olares architecture rationale, three-zone model, or first-run design standards need to be referenced or audited.

---

## 1. What this guide is

This guide preserves the concrete design rationale for turning an Olares One into the center of gravity for APEX Platform development, staging, and field-accessible operation while keeping the laptop as a client surface rather than the durable workstation. The design deliberately lets you work from anywhere without forking your environment, but current execution priority and routing now live in the maintained post-cutover authority, roadmap, and checklist surfaces listed above.

Four load-bearing choices shape everything below:

1. **Three-zone layout on one box.** The Olares One hosts a *dev* zone (ephemeral, docker-compose, Olares-hosted), a *services* zone (shared long-running apps and host utilities), and a *staging* zone (APEX packaged as native Olares apps with SSO). This mirrors APEX's own two-zone architecture and enforces the "sandbox-complete != end-to-end" rule at the infrastructure level.
2. **Hybrid packaging for APEX itself.** Dev iteration happens in plain Docker Compose for speed; promotion to the staging zone means authoring an `OlaresManifest.yaml` and installing via the Market as a private app. The staging zone is the only path to "complete."
3. **GitHub stays canonical while Olares becomes operationally primary.** `C:/APEX Platform/apex-power-ops-platform` is the canonical local repo root and publication boundary for active Apex Ops repo work, while `/home/olares/code/apex/apex-power-ops-platform` is the durable host mirror and the target operating context for day-to-day execution.
4. **LarePass plus premium-model subscriptions beat day-one local model hosting.** LarePass is the network spine. Claude Code and Codex under monthly plans are the primary reasoning stack. Local-model services such as Ollama remain optional accelerators, not baseline requirements.

---

## 2. Hardware and OS baseline

The One ships as a dedicated personal-cloud device: Intel Ultra 9 275HX, NVIDIA RTX 5090 Mobile (24 GB GDDR7), 96 GB DDR5 (upgradeable to 128), 2 TB PCIe 4.0 NVMe (with a free PCIe 5.0 slot for expansion), Thunderbolt 5, 2.5 GbE, and a quiet profile (19 dB idle, under 39 dB at max). Power modes for the GPU are Silent (95 W) and Performance (175 W).

Olares OS is built on Ubuntu 24.04 LTS and runs workloads on K3s with Calico networking and Envoy as the ingress. System updates are free for the life of the device.

Relevant constraint: the HDMI output currently shows only a shell or Steam session, not the Olares web desktop. Treat the One as a **headless server with an optional local shell**, not as a traditional desktop PC. Your "sitting-at-the-box" workflow will be either (a) an external keyboard/monitor into the shell for admin work, or (b) a browser pointed at the Olares web UI from a nearby laptop or the One's own lightweight browser if you wire one in. Everything else is Remote-SSH or LarePass.

---

## 3. Network and access

Your answer about Parsec was the key signal: you already live a remote-workstation lifestyle. Keep that, and add two layers.

**Layer 1 - LarePass VPN (primary).** LarePass is Olares' built-in identity plus WireGuard and Headscale control plane. Install LarePass on your laptop, iPad, and any teammate's device; approve each device once; they now have encrypted mesh access to the Olares One from anywhere. This is how you'll reach the MCP fabric, the Olares-hosted repo mirror, and the APEX field, office, and admin UIs day-to-day. No public attack surface.

**Layer 2 - Parsec (GUI streaming).** Keep Parsec installed on the One for the cases where you need a responsive full desktop remotely - heavy VS Code sessions, screen-sharing with a teammate, or running a Windows-only tool if that ever comes up. Parsec is complementary to LarePass, not redundant: LarePass gives you *network* access; Parsec gives you *pixels*.

**Layer 3 - Cloudflare Tunnel or Olares Tunnel (deferred).** Only stand this up when a real need appears, for example a field lead on a job site without the LarePass app installed, or a client-facing portal. When you do, put Authelia in front with MFA, and expose only the public-facing APEX UIs, never the MCP endpoints or the raw DB.

**Recommended sequencing.** Day 1: LarePass for you, Parsec for the fallback. Week 2: LarePass for one teammate as a test. Month 2 and later: Cloudflare Tunnel if and only if you hit a concrete remote-access requirement LarePass does not cover.

---

## 4. The three zones on one box

This is the mental model that makes the rest of the design make sense.

**Dev zone.** Ephemeral. Runs inside a docker-compose stack in the APEX monorepo - Postgres, any bounded supporting services, and the MCP servers. VS Code Remote-SSH (or code-server via browser) attaches to the monorepo directly on the Olares host. Hot-reload, fast iteration, no SSO, bound to localhost or the LarePass mesh. Sandbox, by definition. Canary tests run here; packet-promote operations are blocked here by design.

**Services zone.** Long-running. Olares Market apps and Linux host services that support the dev and staging zones: Authelia and LLDAP built-ins, Syncthing, Restic, optional Qdrant, optional n8n, optional Dify, optional code-server, optional Open WebUI, and optional Ollama. These are shared capabilities, not proof that APEX is complete.

**Staging zone.** APEX packaged properly. Each APEX service (`forms-engine`, `p6-ingest`, `sync-service`) gets an `OlaresManifest.yaml` that declares required middleware, entrance URLs, and OIDC integration with Authelia. Optional model-serving dependencies can be added later if they are genuinely justified. The three UI surfaces (`apex-field`, `apex-office`, `apex-admin`) become installable private Market apps. This is the host-bootstrap environment - packet-promote only succeeds with a run ID originating here.

Physically the three zones are all on one box. Logically they are separated by K3s namespaces, Postgres databases, and Olares' `system-server` permissions layer.

---

## 5. Olares Market apps and host services

### Day-one baseline

- **Files · Vault · Drive · Dashboard** - Olares built-ins; leave them enabled.
- **Syncthing** - bidirectional file sync to field tablets and support devices when that workflow opens.
- **Restic** - encrypted offsite backups. Configure this in the first week.
- **Gitea (optional)** - local Git mirror of the APEX monorepo if you want disconnected review or mirror insurance. Keep GitHub as the canonical origin.
- **code-server or VS Code Remote-SSH** - secondary browser IDE surface only if Remote-SSH alone proves insufficient.

### Conditional, not baseline

- **Qdrant** (or **Weaviate**) - add only when a real retrieval workload appears for NETA forms, estimates, or P6 corpora.
- **n8n** - add when scheduled operational workflows exist and justify their own service boundary.
- **Dify** - add when you have a specific orchestrated workflow that benefits from it more than from scripts plus MCP plus premium interactive tooling.
- **Open WebUI** - add only if a browser-native shared chat surface becomes useful.
- **Ollama** - optional local-model runtime for offline, GPU-local, or cost-buffered workloads only after a concrete need appears. It is not a day-one requirement.
- **Jupyter** - optional for exploratory notebooks if the repo develops a notebook-heavy analysis lane.

Skip ComfyUI unless you actually need image generation for APEX narrative or presentation work.

---

## 6. AI orchestration on Olares

The primary AI operating model is **plan-authenticated premium tooling first, local models second**.

That means:

1. **Claude Code on Max** is the default Claude surface.
2. **Codex on a subscription-authenticated OpenAI surface** is the default second premium reasoning and coding surface.
3. Anthropic or OpenAI API billing stays exceptional, not routine.
4. Local model hosting is optional and should be introduced only when offline operation, GPU-local batch work, or a clear economic case justifies it.

### Default AI stack

- **Claude Code** - installed on both the laptop and the One; authenticated with your Anthropic account under the monthly plan, not an API key. Current repo-owned guidance for this lane lives in `docs/operations/OLARES-VSCODE-BUILD-SESSION-PROMPT.md`, `docs/architecture/OLARES-AI-BACKBONE-SCAFFOLD-SPEC-2026-05-08.md`, and `docs/operations/CODEX-AI-BACKBONE-FIRST-PASS-EXECUTION-BRIEF-2026-05-08.md`.
- **Codex** - available as the second premium reasoning and coding surface under the monthly OpenAI plan rather than API metering.
- **Claude Desktop** - optional laptop-side review and MCP client surface.
- **ChatGPT** - optional second-opinion or UX-review surface when useful.

### Local model stack

Local models are explicitly optional.

If a later packet justifies them, the preferred shape is:

1. **Ollama** with authentication level set to `Internal`,
2. **Open WebUI** only if a browser-native local chat surface is useful,
3. local embeddings or retrieval services only when a real corpus workflow exists,
4. no public exposure beyond the LarePass mesh.

Until such a packet exists, do not treat Ollama as a blocker or prerequisite for the Olares build.

**The MCP fabric.** Build the currently admitted trio as a set of small services in the APEX monorepo at `services/mcp/`:

- `apex-fs` - filesystem server scoped to the host parent-root mirror `~/code/apex`, its active implementation lane `~/code/apex/apex-power-ops-platform`, and `~/apex-data`
- `apex-db` - Postgres reader (read-only by default; `apex-db-write` gated behind an env flag)
- `apex-jobs` - current job context, packet status, the sandbox-vs-host run ledger

Future expansion candidates such as `apex-p6`, `apex-forms`, and `apex-memory` stay closed until they are admitted by a separate packet and authority update.

Run the MCP services in the dev zone during development (docker-compose), then package the stable ones as OlaresManifest apps so they persist across reboots and are reachable over LarePass. Every admitted client should point at the same bounded set.

**Client wiring.**

- **Claude Code** - primary interactive engineering surface.
- **Codex** - second premium engineering surface where it adds value.
- **Claude Desktop** (laptop) - configure MCP servers in `claude_desktop_config.json` pointing at the LarePass-reachable URLs of the `apex-*` servers.
- **ChatGPT** - use loosely for second opinions or alternative framing when useful.
- **Dify or n8n** - deferred until a real unattended workflow exists. When you do introduce them, they should call the MCP fabric and premium plan-authenticated tooling only under a bounded cost and trust model. Do not add them as ceremony before a real job exists.

**Why not LiteLLM?** Because routing Claude or Codex through API brokers defeats the core economic decision here: use the monthly plans first. Skip proxy indirection until a later packet proves that an API-budgeted broker is materially better than direct plan-authenticated tooling.

---

## 7. APEX packaging

Of the four options you considered, the right path is the hybrid: **develop in plain Docker Compose inside the monorepo; promote to OlaresManifest for the staging zone.**

Native Olares packaging (Helm plus OlaresManifest) is real work - permissions, manifests, chart iteration, Market-submission smoke tests. Paying that cost on every tight dev loop will slow you down. But *not* paying it at all means you never get the payoff: SSO, multi-user, LarePass-aware URLs, per-app Postgres isolation, entrance registration in the Olares Desktop. Those are exactly the things that make APEX feel like a product rather than a pile of services.

The hybrid captures both. Compose runs the dev zone; OlaresManifest runs the staging zone. A service gets promoted to native when its compose definition stabilizes - interface is stable, tests are green, and you are no longer restarting it five times a day. In practice the first service to graduate is probably `forms-engine` because it is well-scoped and the core generators already exist. `p6-ingest` follows once the schema alignment work is stable. UI apps graduate when they stop being scaffolds.

For supporting services that are not themselves the APEX product, prefer the least-ceremony host-native surface that preserves governance: Olares Market app when mature and useful, ordinary Ubuntu or Linux service when simpler, and OlaresManifest only when you need the full staged product posture.

---

## 8. Monorepo layout

The shape that scales is:

```text
apex/ (monorepo root)
  apps/
    apex-field/
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
    k3s-local/
  tools/
  docs/
    authority/
    architecture/
    operations/
  spec/
  .vscode/
    settings.json
```

On the Olares One filesystem: clone the parent-root mirror to `~/code/apex`, with active implementation work under `~/code/apex/apex-power-ops-platform`. Job files and estimate data live at `~/apex-data/` - mount this into services as a shared read/write volume. Keep them separate: `apex/` is source mirror; `apex-power-ops-platform/` is the implementation lane; `apex-data/` is state. This path shape preserves publication semantics but does not by itself approve migration of daily development onto Olares.

---

## 9. Multi-user and identity

Wire each APEX UI app as an OIDC client against Authelia. That gives you:

- one login for everything on the box - Olares apps, Market apps, APEX UIs
- LarePass as the device-trust layer
- LLDAP groups mapping cleanly to APEX roles
- one operation to add a teammate and grant the right app access

Exercise this from week one even as a solo user so the wiring is broken in early while you are the only victim.

---

## 10. Ergonomics

- Three VS Code workspaces colored distinctly via Peacock: Field (blue), Office (green), Admin (amber).
- Zellij or tmux layouts saved per service.
- Shell aliases such as `apex-dev`, `apex-stage`, and `apex-canary`.
- A MOTD on the One that always shows current zone status.
- Zone-distinct hostnames so staging and dev are visually obvious.

---

## 11. Backups and data safety

- Restic configured to both an external Thunderbolt drive and an S3 bucket.
- Nightly Postgres dumps of every APEX database.
- Weekly JuiceFS snapshot.
- Pre-ingest snapshot before any P6 XER import.
- Code, OlaresManifests, and compose files all in Git.

Verify restores quarterly.

---

## 12. Trust and audit guardrails

- `env=sandbox | host` tags written by every agent run to `apex-jobs`.
- Provenance metadata required on every AI-generated field.
- Schema validation gates between model output and the DB.
- Canary suite checked into `tests/canary/`.
- Two-pass review for AI-produced operational content.

These are not optional hardening steps bolted on later. They are the reason the design works.