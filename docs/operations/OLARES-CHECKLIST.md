# APEX on Olares One - Provisioning Checklist

_Repo-owned operational copy established 2026-05-07 so the active Olares provisioning checklist lives inside the canonical repo boundary._
_Companion to `../authority/OLARES-BUILD-GUIDE.md`. Work top to bottom; do not skip phases._
_Authority anchor: `../authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`._
_Olares OS v1.12.5 baseline, LarePass-first, hybrid packaging._
_Retained as the original first-run provisioning reference after post-cutover closeout; it is not the default current operator queue._

---

## Historical Interpretation Note

This checklist preserves the original first-run Olares provisioning sequence.

Use it as historical provisioning reference or for intentional rebuild/audit comparison, not as the default active execution backlog for current Apex Ops work.

Current routing:

1. use `../authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md` for current authority and boundary rules,
2. use `../architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the remaining post-cutover closeout queue,
3. use `../architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md` for maintained rerun and drift-trigger work,
4. use this file only when the original first-run provisioning sequence itself is the subject of reference, audit, or deliberate recreation.

## Phase 0 - Before the box arrives

- [ ] Anthropic account confirmed on Max plan; Claude Desktop plus Claude Code installed on laptop
- [ ] OpenAI account with Codex access confirmed; prefer plan-authenticated use over API billing
- [ ] GitHub access to the APEX monorepo verified from the laptop
- [ ] LarePass account created
- [ ] External Thunderbolt drive for the primary backup target on hand
- [ ] Backblaze B2 or other S3 bucket created for the offsite backup target
- [ ] Decide custom domain now or `.local` for week one

## Phase 1 - Hardware unbox and activation

- [ ] Unbox, connect 2.5 GbE, power on
- [ ] Complete Olares One activation wizard
- [ ] Set admin password; record in Vault or 1Password
- [ ] Register first Olares ID; link to LarePass on the laptop
- [ ] Approve the laptop as a trusted LarePass device
- [ ] Verify LarePass mesh over LAN and cellular
- [ ] Note the primary NVMe free space and second-slot SSD timeline

## Phase 2 - Identity and access

- [ ] Confirm Authelia and LLDAP are running
- [ ] Create LLDAP groups: `admin`, `estimator`, `field-lead`, `reviewer`
- [ ] Create your user in `admin` plus `estimator`; verify SSO to Files
- [ ] Enable MFA on your user
- [ ] Configure `.local` domain or custom domain via Olares settings
- [ ] Install Parsec on the One and verify from the laptop
- [ ] Document which URLs resolve, which require LarePass, and which require public tunnel (none yet)

## Phase 3 - Baseline services install

- [ ] Install Syncthing
- [ ] Install Restic; configure both targets and run first test backup
- [ ] Install Gitea only if you want an offline mirror on the One
- [ ] Install code-server only if VS Code Remote-SSH alone proves insufficient
- [ ] Install n8n only if an immediate scheduled workflow exists
- [ ] Install Dify only if a concrete orchestrated workflow exists
- [ ] Install Qdrant only if a real retrieval workload is already identified
- [ ] Install Open WebUI only if a browser-native shared chat surface is actually useful
- [ ] Defer Ollama unless offline, local-GPU, or cost-buffered batch work is a concrete near-term need
- [ ] Confirm host GPU visibility with `nvidia-smi`

## Phase 4 - Premium AI surface verification

- [ ] Install Claude Code on the One and authenticate with Anthropic Max plan
- [ ] Verify Claude Desktop on the laptop can reach the Olares host over LarePass
- [ ] Verify Codex access on the laptop and, if useful, on the One
- [ ] Confirm the normal daily workflow does not require Anthropic or OpenAI API keys
- [ ] Write down the trigger conditions that would justify adding Ollama later
- [ ] Optional later lane only if justified: install Ollama, set authentication to Internal, then add only the specific local models the proven workflow needs

## Phase 5 - Dev tooling on the One

- [ ] SSH in from laptop using the LarePass-reachable hostname
- [ ] Install `fnm` or `volta`; Node LTS
- [ ] Install `pnpm` globally
- [ ] Install `uv` for Python
- [ ] Verify Docker works
- [ ] Install code-server or configure VS Code Remote-SSH
- [ ] Clone the APEX monorepo to `~/code/apex`
- [ ] Create `~/apex-data/` and seed with a sanitized test job

## Phase 6 - Dev compose stack

- [x] Author `infra/compose.dev.yml` with Postgres 16, Qdrant, MinIO-local, and Mailhog
- [ ] Bring up the stack and verify each service is reachable
- [ ] Add seed data
- [x] Author `.env.dev.template` and keep the real `.env.dev` file ignored via `.gitignore`

## Phase 7 - MCP fabric, minimum viable

- [x] Scaffold `services/mcp/apex-fs/`
- [x] Scaffold `services/mcp/apex-db/`
- [x] Scaffold `services/mcp/apex-jobs/`
- [ ] Run all three under compose and verify each responds to `tools/list`
- [x] Align the repo-owned backbone scaffold and execution-brief docs to the admitted MCP trio
- [ ] Verify the repo-owned session prompt and Claude Desktop wiring match the admitted backbone boundary

## Phase 8 - Claude wiring

- [ ] Install Claude Code on the One and laptop with Anthropic account auth
- [ ] Verify Codex can reach the same Olares-hosted repo and MCP context
- [ ] Edit Claude Desktop's `claude_desktop_config.json` on the laptop
- [ ] Restart Claude Desktop and verify each MCP server shows as connected
- [ ] Smoke test filesystem, DB query, and `apex-jobs` run registration

## Phase 9 - First staging graduation

- [ ] Choose `forms-engine` as the first service to graduate
- [x] Author `infra/olares/forms-engine/Chart.yaml` and `OlaresManifest.yaml`
- [x] Declare middleware, entrance URL, and OIDC client in `infra/olares/forms-engine/OlaresManifest.yaml`
- [ ] Install as a private Market app
- [ ] Verify launcher visibility, SSO, and LarePass reachability
- [ ] Add `env=host` tag emission on every run it logs to `apex-jobs`

## Phase 10 - Canary suite

- [x] Capture the stack-data-center canary input fixture and known-good outputs under `apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.xer`, `tests/canary/p6-ingest-stack-fixture/actual/`, and `tests/canary/apex-p6-stack-summary/actual/`
- [x] Author `tools/run-canary.sh`
- [ ] Run canary and require pass on dev and staging
- [ ] Wire canary into nightly scheduling with failure notifications and `apex-jobs` ledger entry

## Phase 11 - Ergonomics polish

- [ ] Peacock colors per workspace
- [ ] Zellij layouts saved per service
- [ ] Shell aliases: `apex-dev`, `apex-stage`, `apex-canary`, `apex-logs`
- [ ] MOTD script on the One
- [ ] Hostname convention for dev versus staging

## Phase 12 - Safety and observability

- [ ] Nightly Postgres dumps wired into Restic
- [ ] Weekly JuiceFS snapshot schedule
- [ ] Pre-ingest DB snapshot hook in `p6-ingest`
- [ ] Prometheus dashboard bookmarked; token-spend chart for any metered API calls
- [ ] First quarterly restore drill on the calendar

## Phase 13 - First teammate onboarding

- [ ] Create LLDAP user and assign role group
- [ ] Send LarePass invite link
- [ ] Verify teammate SSO against the first APEX UI and any optional shared AI surface actually installed
- [ ] Document anything that broke

## Phase 14 - Public access

- [ ] Decide Cloudflare Tunnel versus Olares Tunnel
- [ ] Expose only the public-facing APEX UIs
- [ ] Put Authelia plus MFA in front of every public route
- [ ] Re-run canary over the public route

---

## Ongoing rhythms

- Daily: `apex-canary` runs nightly; check email on failure
- Weekly: review token-spend dashboard and any `env=sandbox` promotion attempts
- Monthly: Restic restore drill and LLDAP user audit
- Quarterly: full OlaresManifest review across all graduated services and removal of stale apps

## Red flags that mean stop and fix

- Canary regresses unexpectedly
- `apex-jobs` shows packets promoted without `env=host`
- Any APEX service is reachable from the public internet without tunnel plus Authelia
- Any optional internal model endpoint is accessible outside the LarePass mesh
- Normal daily work starts depending on metered Anthropic or OpenAI API calls without an explicit budget decision
- Restic has not completed a successful backup in 48 hours