# MASTER.md

## 1. Repo identity

apex-power-ops-platform at `C:/APEX Platform/apex-power-ops-platform` with status `active`.

This repo IS the canonical platform substrate. The framework-level conventions document `PROTOCOLS_AND_NOMENCLATURE.md` lives inside this repo at `.claude/PLATFORM/PROTOCOLS_AND_NOMENCLATURE.md`; other enrolled repos cite it as the cross-repo conventions reference.

**Workspace constellation pointer** (condensed from legacy `AGENTS.md` §2 by apex-power-ops-platform audit packet 2026-05-23):

- Parent workspace root: `C:/APEX Platform/`
- Active platform repo (this one): `C:/APEX Platform/apex-power-ops-platform/`
- Source domains: `C:/APEX Platform/source-domains/{tcc_v5_backend, neta-ett-study-material, neta-forms}/`
- Historical strategic provenance: `C:/APEX Platform/Platform-Authority/` (read-only per `docs/authority/README.md` Interpretation Rules)
- Separate workspace constellation: `D:/apex-power-ops-platform/` (not enrolled in C:\-side registry)

Full topology and per-repo enrollment status: see `docs/authority/WORKSPACE-REGISTRY-2026-05-23.md`.

## 2. Authority chain

1. `apex-power-ops-platform/REPO_PASSPORT.md`
2. `apex-power-ops-platform/.claude/PLATFORM/PROTOCOLS_AND_NOMENCLATURE.md`
3. Legacy-tolerated repo-local files (preserved as provenance; not modified by Era 3.1):
   - `AGENTS.md` (root; ~2,936 B; 8 sections; pre-cutover agent instructions; audit-packet migration pending)
   - `.github/copilot-instructions.md` (~2,673 B; 2026-05-07; RESA-era Copilot context; audit-packet shim conversion pending)
   - `ops/agents/legacy-governance/` (pre-Era-2.3 governance content; preserved as provenance)
4. `apex-power-ops-platform/.claude/MASTER.md`

Authority documents inside `docs/authority/` are themselves governed by `docs/authority/README.md` Strategic Authority Order, which threads REPO-PASSPORT-STANDARD-2026-05-23 + WORKSPACE-REGISTRY-2026-05-23 + OLARES-WORKSPACE-AUTHORITY-FRAMEWORK + APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.

## 3. Per-repo declarations

```yaml
governing-rules-file: AGENTS.md (root, legacy-tolerated)
state-file: PROJECT_STATUS.md (root, ~1.59 MB)
handoffs-directory: ops/agents/handoffs/
packet-directory: ops/agents/packets/
content-authority: docs/authority/README.md
```

## 4. `ops/agents/` layout participation

Mandatory-core (per `PROTOCOLS_AND_NOMENCLATURE.md` §5):

- `ops/agents/packets/draft/` (existing; populated with prior packet drafts)
- `ops/agents/packets/active/` (added 2026-05-23 by Era 3.1 propagation)
- `ops/agents/packets/blocked/` (added 2026-05-23 by Era 3.1 propagation)
- `ops/agents/packets/review/` (added 2026-05-23 by Era 3.1 propagation)
- `ops/agents/packets/done/` (added 2026-05-23 by Era 3.1 propagation)
- `ops/agents/packets/archive/` (added 2026-05-23 by Era 3.1 propagation)
- `ops/agents/handoffs/` (existing; populated with closeout history)
- `ops/agents/policies/` (added 2026-05-23 by Era 3.1 propagation)

Optional-rest present:

- `ops/agents/legacy-governance/` — pre-Era-2.3 governance content preserved as provenance; not part of mandatory-core vocabulary; legacy-tolerated.

## 5. `apex-jobs` ledger participation

ledger-writes-from-this-repo: yes

This repo hosts the canonical `apex-jobs` ledger service source under `services/mcp/apex-jobs/`. Physical ledger storage is runtime-resolved per `PROTOCOLS_AND_NOMENCLATURE.md` §9; current discovered storage is `/home/olares/code/apex/apex-power-ops-platform/.apex-data/apex-jobs-ledger.json` (Olares host).

## 6. MCP scope

Per-repo MCP advertisement is declared in `.claude/MCP_TOPOLOGY.md`.
Per-user stdio MCPs at `~/.claude.json` are user-scoped and are not repo-propagated.

## 7. Credential discipline

Credential handling is governed by `C:\APEX Platform\.claude\PLATFORM\MASTER.md` section `CREDENTIAL_HANDLING_PROTOCOL`.
AI assistants reference credentials by environment variable name only and do not read production credential env files.

## 8. Boot order

Read `.claude/READING_ORDER.md` before substantive work.

**Canonical-entry rule** (migrated from legacy `AGENTS.md` §1 by audit packet 2026-05-23): default working surface for this workspace constellation is `C:/APEX Platform/apex-power-ops-platform/`. Do not assume sibling source-domain repos are the default execution surface — they are bounded extraction/lineage lanes (see §10).

**Common starting reads after `READING_ORDER.md`** (migrated from legacy `AGENTS.md` §6; updated for Era 3.1 ordering):

1. `REPO_PASSPORT.md` (root) — front-door contract
2. `.claude/MASTER.md` (this file) — repo-scope authority
3. `docs/authority/README.md` — Strategic Authority Order
4. `ops/agents/packets/active/` and `ops/agents/packets/blocked/` — current in-flight work
5. Most recent `ops/agents/handoffs/<latest>-handoff.md` — latest closeout
6. `.claude/PLATFORM/PROTOCOLS_AND_NOMENCLATURE.md` — framework conventions (when work is cross-repo, skeleton-touching, or convention-touching)
7. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md` — when bootstrapping a fresh environment
8. Sibling source-domain docs under `../source-domains/<repo>/` — only when doing source-extraction work for that lane

## 9. Open per-repo carry-forward items

1. apex-power-ops-platform audit-and-backfill packet executed 2026-05-23. Operator-review items RESOLVED 2026-05-23: §3 Authority Order → **Option C** (keep legacy untouched; current routing via `REPO_PASSPORT.md` §3 + `.claude/MASTER.md` §2 + `docs/authority/README.md`; legacy reference to historical `Platform-Authority/` provenance is acceptable as legacy-tolerated); §8 Transition Intent → **Option A** (retain as historical voice in legacy file; passport §1 acknowledges current canonical-substrate status).
2. `/src/` clone divergence classification deliverable returned 2026-05-23; per-lane tactical packets pending operator acceptance (Lane F root package graph first per recommendation).
3. forms-engine + p6-ingest AppImage reconciliation (Option 2 selected 2026-05-23) awaiting dispatch.

## 10. Source-domain boundary + execution discipline

Migrated from legacy `AGENTS.md` §4 (Execution Rules) by apex-power-ops-platform audit packet 2026-05-23:

- Treat this repo as the primary implementation target.
- Treat source-domain repos (`tcc_v5_backend`, `neta-ett-study-material`, `neta-forms`) as bounded extraction and lineage lanes — not as the default execution surface.
- Do not import sibling source-domain repos wholesale into this repo.
- Move only approved slices into `apps/`, `packages/`, `infra/`, `ops/`, `knowledge/`, `docs/`, or `archive/` — and only via packetized decision.
- Keep archive-heavy and binary-heavy material out of active implementation paths unless a bounded packet decision explicitly promotes it.

These rules complement PATTERN-003 (scaffold-then-audit propagation) at the cross-repo level: source-domain content stays in its repo of origin until a deliberate audit packet authorizes movement.

## 11. Local Python environment

Migrated from legacy `AGENTS.md` §5 (Environment Rules) by apex-power-ops-platform audit packet 2026-05-23:

- Preferred local Python environment: `C:/APEX Platform/apex-power-ops-platform/.venv`
- If workspace tasks need an explicit interpreter, prefer the platform-local `.venv` or set the `APEX_PLATFORM_PYTHON` environment variable.
- PowerShell and direct file reads are reliable fallbacks when shell tooling is uneven.
- Credential handling per §7 — production credential values never enter AI conversation context; AI references credentials by env-var name only.

## 12. Validation posture (priority order)

Migrated from legacy `AGENTS.md` §7 (Validation Preference) by apex-power-ops-platform audit packet 2026-05-23:

After making changes, prefer focused validation in this priority order:

1. The smallest relevant test slice.
2. The narrowest lint or typecheck slice.
3. A targeted runbook or smoke command.
4. Diff-only inspection if no executable validation exists.

Concrete entrypoints (paths, commands) for this repo live in `REPO_PASSPORT.md` §8 "Validation entrypoints." The posture above declares the priority; the passport declares the routes.
