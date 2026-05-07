# APEX on Olares One — Provisioning Checklist

_Companion to `Olares_Build_Guide.md`. Work top to bottom; don't skip phases._
_Authority anchor: `Olares_Workspace_Authority_Framework.md`._
_Olares OS v1.12.5 baseline · LarePass-first · Hybrid packaging._

---

## Phase 0 — Before the box arrives

- [ ] Anthropic account confirmed on Max plan; Claude Desktop + Claude Code installed on laptop
- [ ] OpenAI account with Codex access confirmed; prefer plan-authenticated use over API billing
- [ ] GitHub access to the APEX monorepo verified from the laptop
- [ ] LarePass account created (the same Olares ID will register the One)
- [ ] External Thunderbolt drive for the primary backup target on hand
- [ ] Backblaze B2 (or other S3) bucket created for the offsite backup target
- [ ] Decide: custom domain now (NS record ready) or `.local` for week one

---

## Phase 1 — Hardware unbox and activation (hours 1–4)

- [ ] Unbox, connect 2.5 GbE, power on
- [ ] Complete Olares One activation wizard
- [ ] Set admin password; record in Vault / 1Password
- [ ] Register first Olares ID; link to LarePass on the laptop
- [ ] Approve the laptop as a trusted LarePass device
- [ ] Verify LarePass mesh: laptop can reach `https://<host>.local` over LAN and over cellular
- [ ] Note the primary NVMe has free space; decide on a second-slot PCIe 5.0 SSD timeline

## Phase 2 — Identity and access (hours 5–12)

- [ ] Confirm Authelia and LLDAP are running (system apps)
- [ ] Create LLDAP groups: `admin`, `estimator`, `field-lead`, `reviewer`
- [ ] Create your user in `admin` + `estimator`; verify SSO to the built-in Files app
- [ ] Enable MFA on your user (Authelia → TOTP)
- [ ] Configure `.local` domain OR custom domain via Olares settings
- [ ] Install Parsec on the One (for fallback GUI streaming) and verify from the laptop
- [ ] Document in the monorepo: which URLs resolve, which require LarePass, which require public tunnel (none yet)

## Phase 3 — Baseline services install (day 1 evening)

- [ ] Install **Syncthing**
- [ ] Install **Restic**; configure both targets (Thunderbolt drive + S3); run first test backup
- [ ] Install **Gitea** only if you want an offline mirror on the One
- [ ] Install **code-server** only if VS Code Remote-SSH alone proves insufficient
- [ ] Install **n8n** only if an immediate scheduled workflow exists
- [ ] Install **Dify** only if a concrete orchestrated workflow exists
- [ ] Install **Qdrant** only if a real retrieval workload is already identified
- [ ] Install **Open WebUI** only if a browser-native shared chat surface is actually useful
- [ ] Defer **Ollama** unless offline, local-GPU, or cost-buffered batch work is a concrete near-term need
- [ ] Confirm host GPU visibility with `nvidia-smi`; do not treat unused GPU capacity as a reason to add services early

## Phase 4 — Premium AI surface verification (day 1 evening)

- [ ] Install Claude Code on the One; authenticate with Anthropic Max plan
- [ ] Verify Claude Desktop on the laptop can reach the Olares host over LarePass
- [ ] Verify Codex access on the laptop and, if useful, on the One
- [ ] Confirm the normal daily workflow does not require Anthropic or OpenAI API keys
- [ ] Write down the trigger conditions that would justify adding Ollama later
- [ ] Optional later lane only if justified: install **Ollama**, set Authentication level → Internal, then add only the specific local models the proven workflow needs

## Phase 5 — Dev tooling on the One (day 2 morning)

- [ ] SSH in from laptop using LarePass-reachable hostname
- [ ] Install `fnm` (or `volta`); Node LTS
- [ ] Install `pnpm` globally
- [ ] Install `uv` for Python
- [ ] Verify Docker works (K3s runtime is present; `docker` CLI may need install)
- [ ] Install `code-server` OR configure VS Code Remote-SSH from the laptop
- [ ] Clone the APEX monorepo to `~/code/apex`
- [ ] Create `~/apex-data/` directory; seed with a sanitized test job (Stack Data Center derivative)

## Phase 6 — Dev compose stack (day 2 morning)

- [ ] Author `infra/compose.dev.yml` with: Postgres 16, Qdrant, MinIO-local, Mailhog
- [ ] Bring up; verify each service reachable from the monorepo root
- [ ] Add seed data: run `tools/seed-dev-db.ts` (or create it) to populate core tables
- [ ] Author `.env.dev` template; gitignore the real file

## Phase 7 — MCP fabric, minimum viable (day 2 afternoon)

- [ ] Scaffold `services/mcp/apex-fs/` (filesystem MCP, scoped to `~/code/apex` + `~/apex-data`)
- [ ] Scaffold `services/mcp/apex-db/` (Postgres MCP, read-only)
- [ ] Scaffold `services/mcp/apex-jobs/` (job context + run ledger)
- [ ] Run all three under compose; verify each responds to `tools/list`
- [ ] Write `.claude/CLAUDE.md` at repo root (two-zone architecture, P6 strategy, sandbox-vs-host rule)
- [ ] Write `.claude/mcp.json` pointing at the three servers

## Phase 8 — Claude wiring (day 2 evening)

- [ ] Install Claude Code on the One; authenticate with Anthropic account (Max, not API)
- [ ] Install Claude Code on the laptop; authenticate with Anthropic account
- [ ] Verify Codex can reach the same Olares-hosted repo and MCP context from approved devices
- [ ] Edit Claude Desktop's `claude_desktop_config.json` on the laptop — add the three MCP servers via their LarePass-reachable URLs
- [ ] Restart Claude Desktop; verify each MCP server shows as connected
- [ ] **Smoke test**: ask Claude Desktop to (a) list files in `~/apex-data/`, (b) query a row from the APEX dev DB, (c) register a new run in `apex-jobs`. All three must succeed.

## Phase 9 — First staging graduation (day 3)

- [ ] Choose `forms-engine` as the first service to graduate
- [ ] Author `infra/olares/charts/forms-engine/Chart.yaml` + `OlaresManifest.yaml`
- [ ] Declare middleware: dedicated Postgres account, JuiceFS volume for form templates
- [ ] Declare entrance URL + OIDC client against Authelia
- [ ] Install as private Market app
- [ ] Verify it appears in the Olares Desktop launcher, SSO works, service is reachable over LarePass
- [ ] Add `env=host` tag emission on every run it logs to `apex-jobs`

## Phase 10 — Canary suite (day 3 evening)

- [ ] Create `tests/canary/stack-data-center/` with inputs + known-good outputs for one real packet
- [ ] Author `tools/run-canary.sh` that runs the full forms-engine pipeline against it and diffs
- [ ] Run canary — must pass on dev and on staging
- [ ] Wire canary into a nightly n8n schedule; failures go to your email + a note in the `apex-jobs` ledger

## Phase 11 — Ergonomics polish (day 4+)

- [ ] Peacock colors per workspace (Field blue / Office green / Admin amber)
- [ ] Zellij layouts saved per service
- [ ] Shell aliases: `apex-dev`, `apex-stage`, `apex-canary`, `apex-logs`
- [ ] MOTD script on the One: shows compose state + Market app state + last canary result
- [ ] Hostname convention: `*.dev.olares.local` vs `*.stage.olares.local`

## Phase 12 — Safety and observability (day 4+)

- [ ] Nightly Postgres dumps wired into Restic pipeline
- [ ] Weekly JuiceFS snapshot schedule
- [ ] Pre-ingest DB snapshot hook in `p6-ingest`
- [ ] Prometheus dashboard bookmarked; token-spend chart for any Anthropic API calls
- [ ] First quarterly restore drill on the calendar

## Phase 13 — First teammate onboarding (when ready)

- [ ] Create LLDAP user + assign to `estimator` or `field-lead`
- [ ] Send them the LarePass invite link
- [ ] They approve device; SSO test against the first APEX UI and any optional shared AI surface you actually installed
- [ ] Document anything that broke; that's the real acceptance test for the identity wiring

## Phase 14 — Public access (deferred; when field need is real)

- [ ] Decide Cloudflare Tunnel vs Olares Tunnel
- [ ] Expose only the public-facing APEX UI(s) — never MCP, never DB, never any optional internal model endpoint
- [ ] Authelia + MFA in front of every public route
- [ ] Re-run canary over public route to confirm no regressions

---

## Ongoing rhythms

- Daily: `apex-canary` runs nightly; check email on failure
- Weekly: review token-spend dashboard; review any `env=sandbox` packets that tried to promote
- Monthly: Restic restore drill (one random backup point); LLDAP user audit
- Quarterly: full OlaresManifest review across all graduated services; kill anything stale

---

## Red flags that mean stop and fix

- Canary regresses unexpectedly → do not ship; investigate model drift or data change
- `apex-jobs` shows packets promoted without `env=host` → the promote guard has failed; audit immediately
- Any APEX service reachable from the public internet without a tunnel + Authelia in front → pull the route now
- Any optional internal model endpoint accessible from outside the LarePass mesh → pull the route and re-check its auth settings
- Normal daily work starts depending on metered Anthropic or OpenAI API calls without an explicit budget decision → stop and re-evaluate the tooling path
- Restic hasn't successfully completed a backup in 48 hours → investigate before any risky operation
