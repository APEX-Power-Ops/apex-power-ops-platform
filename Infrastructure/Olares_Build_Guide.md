# APEX Platform on Olares One — Blue-Sky Workspace Build Guide

_Reference: `Olares_Architecture.svg` (pin near workstation). Checklist: `Olares_Checklist.md`._
_Authored 2026-04-22. Olares OS v1.12.5 baseline._

---

## 1. What this guide is

A concrete plan for turning a new Olares One into the center of gravity for APEX Platform development, staging, and field-accessible operation — without giving up the laptop-first workflow you already have. The design deliberately lets you work from anywhere (laptop on the couch, docked to the One, or remote via Parsec + LarePass) without forking your environment.

Three load-bearing choices shape everything below:

1. **Three-zone layout on one box.** The Olares One hosts a *dev* zone (ephemeral, docker-compose, laptop-driven), a *services* zone (Olares Market apps — Ollama, Dify, vector DB, Syncthing, etc.), and a *staging* zone (APEX packaged as native Olares apps with SSO). This mirrors APEX's own two-zone architecture and enforces the "sandbox-complete ≠ end-to-end" rule at the infrastructure level.
2. **Hybrid packaging for APEX itself.** Dev iteration happens in plain Docker Compose for speed; promotion to the staging zone means authoring an `OlaresManifest.yaml` and installing via the Market as a private app. The staging zone is the only path to "complete."
3. **LarePass is the network spine.** WireGuard-based VPN gives you and trusted teammates access to *everything* — the MCP fabric, Ollama endpoints, APEX UIs — from any device, anywhere, without exposing a public attack surface. Parsec stays for low-latency GUI streaming; Cloudflare Tunnel is held in reserve for eventual public field-console access.

---

## 2. Hardware & OS baseline

The One ships as a dedicated personal-cloud device: Intel Ultra 9 275HX, NVIDIA RTX 5090 Mobile (24 GB GDDR7), 96 GB DDR5 (upgradeable to 128), 2 TB PCIe 4.0 NVMe (with a free PCIe 5.0 slot for expansion), Thunderbolt 5, 2.5 GbE, and a quiet profile (19 dB idle, under 39 dB at max). Power modes for the GPU are Silent (95 W) and Performance (175 W).

Olares OS is built on Ubuntu 24.04 LTS and runs workloads on K3s with Calico networking and Envoy as the ingress. System updates are free for the life of the device.

Relevant constraint: the HDMI output currently shows only a shell or Steam session, not the Olares web desktop. Treat the One as a **headless server with an optional local shell**, not as a traditional desktop PC. Your "sitting-at-the-box" workflow will be either (a) an external keyboard/monitor into the shell for admin work, or (b) a browser pointed at the Olares web UI from a nearby laptop / the One's own lightweight browser if you wire one in. Everything else is Remote-SSH or LarePass.

---

## 3. Network & access — reach from anywhere without exposing anything

Your answer about Parsec was the key signal: you already live a remote-workstation lifestyle. Keep that, and add two layers.

**Layer 1 — LarePass VPN (primary).** LarePass is Olares' built-in identity + WireGuard/Headscale control plane. Install LarePass on your laptop, iPad, and any teammate's device; approve each device once; they now have encrypted mesh access to the Olares One from anywhere. This is how you'll reach Ollama endpoints, MCP servers, and the APEX field/office/admin UIs day-to-day. No public attack surface.

**Layer 2 — Parsec (GUI streaming).** Keep Parsec installed on the One for the cases where you need a responsive full desktop remotely — heavy VS Code sessions, screen-sharing with a teammate, running a Windows-only tool if that ever comes up. Parsec is complementary to LarePass, not redundant: LarePass gives you *network* access; Parsec gives you *pixels*.

**Layer 3 — Cloudflare Tunnel or Olares Tunnel (deferred).** Only stand this up when a real need appears — e.g., a field lead on a job site without the LarePass app installed, or a client-facing portal. When you do, put Authelia in front with MFA, and expose only the public-facing APEX UIs, never the MCP endpoints or the raw DB.

**Recommended sequencing.** Day 1: LarePass for you, Parsec for the fallback. Week 2: LarePass for one teammate as a test. Month 2+: Cloudflare Tunnel if and only if you hit a concrete remote-access requirement LarePass doesn't cover.

---

## 4. The three zones on one box

This is the mental model that makes the rest of the design make sense.

**Dev zone.** Ephemeral. Runs inside a docker-compose stack in the APEX monorepo — Postgres, Qdrant, MinIO-local, and the MCP servers. VS Code Remote-SSH (or code-server via browser) attaches to the monorepo directly. Hot-reload, fast iteration, no SSO, bound to localhost or the LarePass mesh. Sandbox, by definition. Canary tests run here; packet-promote operations are blocked here by design.

**Services zone.** Long-running. Olares Market apps — Ollama, Open WebUI, Dify, Qdrant (if available as a Market app; otherwise run it in compose and graduate later), n8n, Syncthing, Restic. These are shared across both your dev work and the staging zone. Ollama's "Internal" auth level means the LLM endpoint is reachable from anything on the LarePass mesh but not from the public internet.

**Staging zone.** APEX packaged properly. Each APEX service (`forms-engine`, `p6-ingest`, `sync-service`) gets an `OlaresManifest.yaml` that declares required middleware (Postgres account, MinIO bucket, optional Ollama dependency), entrance URLs, and OIDC integration with Authelia. The three UI surfaces (`apex-field`, `apex-office`, `apex-admin`) become installable private Market apps. This is the host-bootstrap environment — packet-promote only succeeds with a run ID originating here.

Physically the three zones are all on one box. Logically they are separated by K3s namespaces, Postgres databases, and Olares' `system-server` permissions layer.

---

## 5. Olares Market apps — the baseline install set

In rough priority order:

- **Ollama + Open WebUI** — local LLMs and a human chat surface. Non-negotiable.
- **Dify** — agent orchestration and RAG pipelines. This is where your "orchestrator agent" lives once you're past the task-agent tier.
- **Qdrant** (or **Weaviate**) — vector DB for NETA forms, past estimates, P6 job corpora.
- **n8n** — low-code orchestration. Useful for scheduled jobs (nightly canary runs, P6 ingest cadence, backups) that don't need a full agent.
- **Syncthing** — bidirectional file sync to field tablets. Critical once the field console leaves the office.
- **Restic** — encrypted offsite backups. Configure this in the first week.
- **Files · Vault · Drive · Dashboard** — Olares built-ins; leave them enabled.
- **Gitea (optional)** — local Git mirror of the APEX monorepo if you want to be able to commit while disconnected from GitHub. Keep GitHub as the canonical origin.
- **Jupyter or code-server** (if available as Market apps) — secondary IDE surfaces for exploratory notebooks and browser-only editing.

Skip ComfyUI unless you actually need image generation for APEX narrative/presentation work. It's heavy on the GPU and competes with Ollama for VRAM.

---

## 6. AI orchestration on Olares — concrete wiring

Recall the earlier frame: **Claude Code on Max subscription is the gateway for all Claude work.** Anthropic API tokens get spent only where a scheduled unattended agent genuinely needs them. Local models do the bulk.

**Model slate (pulled by `ollama pull` on the One):**

- `qwen3:30b-a3b` — general reasoning. The Olares One benchmarks show 157 tok/s single-request, 81 tok/s at 8 concurrent — plenty fast for an estimator's working pace.
- `qwen2.5-coder:14b` — inline code completion, test scaffolding, small refactors.
- `bge-m3` — embedding model for the APEX corpus.
- Optional: `qwen3:70b` if you want a heavier local model for weekend batch generation; it will fit in 96 GB RAM with aggressive quantization.

**Ollama exposure.** In `Settings → Application → Ollama`, set Authentication level to "Internal." Copy the endpoint URL. That endpoint is reachable from any LarePass-connected device. Append `/v1` for OpenAI-compatible clients. API key can be any string.

**The MCP fabric.** Build these as a set of small services in the APEX monorepo at `services/mcp/`:

- `apex-fs` — filesystem server scoped to `~/code/apex` and `~/apex-data`
- `apex-db` — Postgres reader (read-only by default; `apex-db-write` gated behind an env flag)
- `apex-p6` — wraps PyP6Xer for XER reads plus queries against the mirrored P6 schema
- `apex-forms` — NETA-Forms lookup + forms-engine render API
- `apex-jobs` — current job context, packet status, the sandbox-vs-host run ledger
- `apex-memory` — exposes `.auto-memory/` as a queryable tool instead of dumping it into prompts

Run them in the dev zone during development (docker-compose), then package the "stable" ones as OlaresManifest apps so they persist across reboots and are reachable from Claude Desktop via LarePass. Every client — Claude Code, Claude Desktop, custom GPT via a bridge — points at the same set.

**Client wiring.**

- **Claude Code** — installed on both the laptop and the One; authenticated with your Anthropic account (Max, not API). `CLAUDE.md` at the monorepo root. Subagent configs per service boundary (`.claude/agents/forms-engine.md`, `.claude/agents/p6-ingest.md`, `.claude/agents/ui.md`).
- **Claude Desktop** (laptop) — configure MCP servers in `claude_desktop_config.json` pointing at the LarePass-reachable URLs of the `apex-*` servers.
- **ChatGPT** — use loosely. Either a custom GPT with Actions against a small HTTP-MCP bridge, or just paste relevant MCP outputs into chat when you want a second opinion.
- **Dify / n8n** — for scheduled autonomous runs. Dify workflows invoke Claude Code as a subprocess where you need Anthropic reasoning, hit Ollama directly for bulk work. Log every run to `apex-jobs`.

**Why not LiteLLM?** Because routing Claude through an OpenAI-compatible proxy means paying per token on the Anthropic API side instead of using your Max subscription. Skip it for Claude. Use it *only* if you later want a unified OpenAI-compatible endpoint across local models and OpenAI — Anthropic calls go through Claude Code, not the proxy.

---

## 7. APEX packaging — dev raw, staging native

Of the four options you considered, the right path is the hybrid: **develop in plain Docker Compose inside the monorepo; promote to OlaresManifest for the staging zone.** Reasoning:

Native Olares packaging (Helm + OlaresManifest) is real work — permissions, manifests, chart iteration, Market-submission smoke tests. Paying that cost on every tight dev loop will slow you down. But *not* paying it at all means you never get the payoff: SSO, multi-user, LarePass-aware URLs, per-app Postgres isolation, entrance registration in the Olares Desktop. Those are exactly the things that make APEX feel like a product rather than a pile of services.

The hybrid captures both. Compose runs the dev zone; OlaresManifest runs the staging zone. A service gets promoted to native when its compose definition stabilizes — interface is stable, tests are green, you're no longer restarting it five times a day. In practice the first service to graduate is probably `forms-engine` (the current priority import) because it's well-scoped and the core generators already exist. `p6-ingest` follows once the schema alignment work is stable. UI apps graduate when they stop being scaffolds.

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

On the Olares One filesystem: clone to `~/code/apex`. Job files and estimate data live at `~/apex-data/` — mount this into services (both compose and OlaresManifest) as a shared read/write volume. Keep them separate: `apex/` is source; `apex-data/` is state.

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

**Day 1 evening (Market apps).** Install Ollama, Open WebUI, Dify, Syncthing, Restic, Qdrant (or note it for compose). Pull models: `qwen3:30b-a3b`, `qwen2.5-coder:14b`, `bge-m3`.

**Day 2 morning (dev tooling).** SSH in from laptop. Install Node (fnm or volta), pnpm, uv for Python, Docker (already present via K3s), code-server (optional). Clone the APEX monorepo. Bring up `compose.dev.yml`.

**Day 2 afternoon (MCP fabric).** Scaffold the six `apex-*` MCP servers in `services/mcp/`. Start minimum: `apex-fs`, `apex-db` read-only, `apex-jobs`. Add `CLAUDE.md` at repo root. Install Claude Code on both the laptop and the One; authenticate with Max.

**Day 2 evening (wire Claude Desktop).** Configure Claude Desktop's MCP clients to hit the three LarePass-reachable MCP endpoints. Smoke test: "read a NETA form file, query a sample row from apex-db, and write a test case." If all three tool calls succeed, the fabric is sound.

**Day 3 (first graduation).** Author an `OlaresManifest.yaml` for `forms-engine`. Install as a private Market app. Run the canary against it. If canary passes, you have your first working dev→staging promotion loop.

After that: it's incremental. Graduate more services, add teammates, add the field-tablet sync flow once the UI is real enough to put in front of a field lead.

---

## 14. What this gets you, a month in

If you execute the above:

- You can open a laptop anywhere on the planet with LarePass installed and be in your full dev environment in under a minute.
- Claude Desktop, Claude Code, and any custom GPT all share the same APEX context via the MCP fabric — you stop re-explaining the domain with every new chat.
- Dev iteration happens fast (compose), but "complete" has a real meaning (staging, canary-gated).
- Local models handle the bulk of token-hungry work; your Max subscription covers Claude Code; Anthropic API stays unused until you have a specific unattended-agent need.
- Trust in AI-generated work is earned by measured canary pass-rates, not granted by faith.
- Teammates get access via one LLDAP entry, not a pile of bespoke credentials.
- The Cupertino / Stack Data Center packet workflow is the first real test — and the canary against it is what tells you the system is ready to scale to the next job.

---

## Appendix A — Open questions to revisit

- Does the Olares Market ship Qdrant as a first-class app, or do we host it in compose? (Worth checking in the Market UI on day one.)
- Does Parsec-from-One-as-host work acceptably given the HDMI limitation? (Parsec can run headless but verify once you have the hardware.)
- When do field tablets actually need to reach the box — before or after you have a stable `apex-field` UI? That ordering determines when Cloudflare Tunnel becomes real.
- Is GitHub still the canonical origin, or does moving to Gitea-on-the-One make sense once remote-first is the default? Keep GitHub for now; revisit in six months.
