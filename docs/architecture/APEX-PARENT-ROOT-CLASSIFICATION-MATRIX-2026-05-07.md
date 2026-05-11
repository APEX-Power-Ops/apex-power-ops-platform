# APEX Parent-Root Classification Matrix

Date: 2026-05-07
Status: Executed cutover classification baseline with residual residue tracking
Scope: classify the current `C:/APEX Platform` top-level folders into canonical-repo, external-source, workstation-local, archive, or retire-after-verification classes

Closeout interpretation note:

This matrix records the classification baseline that governed cutover. It is now a closeout and residue-tracking surface rather than a pre-cutover working matrix.

Current routing:

1. use `PROJECT_STATUS.md` for the current ordered residue queue,
2. use `docs/architecture/APEX-AUTHORITY-RELOCATION-PLAN-2026-05-07.md` for the current authority-relocation closeout context,
3. use `docs/architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the remaining publication-boundary closeout work.

## Purpose

This matrix turns the repo-foundation plan into a recorded cutover-classification surface.

It answers one concrete question for every current top-level parent-root item:

Did it belong inside the canonical repo, outside it, or nowhere at all at cutover time?

## Classification Keys

| Class | Meaning |
| --- | --- |
| `PROMOTE-INTO-REPO` | Active authoritative content that should live inside `apex-power-ops-platform/` |
| `KEEP-OUTSIDE-SOURCE` | Valid source lane or sibling checkout that must remain outside the canonical repo boundary |
| `KEEP-OUTSIDE-LOCAL` | Workstation-local, secret, generated, or runtime material that must never become repo authority |
| `KEEP-OUTSIDE-ARCHIVE` | Historical or heavy reference material that should remain outside the active repo or move into governed archive only |
| `RETIRE-AFTER-VERIFY` | Transitional residue that should disappear from the default workflow once cutover is complete |

## Current Parent-Root Matrix

| Parent-root item | Class | Target disposition |
| --- | --- | --- |
| `apex-power-ops-platform/` | `PROMOTE-INTO-REPO` | This is now the canonical repo root |
| `Platform-Authority/` | `PROMOTE-INTO-REPO` | Surviving active authority is now re-homed into repo-owned `docs/authority/` or `docs/architecture/`; the parent-root tree remains aligned historical mirror or provenance residue by rule |
| `Infrastructure/` | `PROMOTE-INTO-REPO` | Surviving active Olares governance and operator docs are now re-homed into repo-owned docs and infra lanes; the parent-root copies remain historical or aligned reference residue by rule |
| `apps/` | `KEEP-OUTSIDE-SOURCE` | Treat as parent-root residue until each active slice is re-homed or archived deliberately |
| `packages/` | `KEEP-OUTSIDE-SOURCE` | Reconcile only the slices not already re-homed into repo `packages/` |
| `services/` | `KEEP-OUTSIDE-SOURCE` | Reconcile lane-by-lane; do not treat as a permanent parallel app namespace |
| `source-domains/` | `KEEP-OUTSIDE-SOURCE` | Keep as extraction lanes outside the canonical repo |
| `Documentation/` | `KEEP-OUTSIDE-ARCHIVE` | Mine surviving active docs into repo `docs/`; leave the remainder archived |
| `Supabase/` | `KEEP-OUTSIDE-ARCHIVE` | Promote executable active assets into repo `infra/database/`; archive the rest |
| `spec/` | `KEEP-OUTSIDE-ARCHIVE` | Promote only active validation authority; otherwise keep external or archive |
| `Reference_Files/` | `KEEP-OUTSIDE-ARCHIVE` | Heavy reference holdings stay out of the active repo |
| `LASNAP16/` | `KEEP-OUTSIDE-ARCHIVE` | Binary-heavy project references stay outside the canonical repo |
| `APEX_Schema_V2/` | `KEEP-OUTSIDE-ARCHIVE` | Preserve as reviewed design input, not active runtime authority |
| `_archive/` | `KEEP-OUTSIDE-ARCHIVE` | Historical archive remains outside the active repo shell |
| `Sessions/` | `KEEP-OUTSIDE-ARCHIVE` | Historical session residue should not survive as active repo structure |
| `Logs/` | `KEEP-OUTSIDE-LOCAL` | Generated logs never belong in canonical repo authority |
| `tmp/` | `KEEP-OUTSIDE-LOCAL` | Scratch and temporary artifacts must stay outside canonical repo structure |
| `.secrets/` | `KEEP-OUTSIDE-LOCAL` | Secrets remain external to the repo |
| `.private/` | `KEEP-OUTSIDE-LOCAL` | Private local holdings remain external to the repo |
| `.venv/` | `KEEP-OUTSIDE-LOCAL` | Local environment state must not define repo structure |
| `.pytest_cache/` | `KEEP-OUTSIDE-LOCAL` | Generated cache only |
| `.vercel/` | `KEEP-OUTSIDE-LOCAL` | Local deployment state only |
| `.env.local` | `KEEP-OUTSIDE-LOCAL` | Local environment file only |
| `.git/` | `RETIRE-AFTER-VERIFY` | Parent-root git boundary should disappear from daily platform work after cutover |
| `.github/` | `RETIRE-AFTER-VERIFY` | Repo-owned `.github/` now carries ownership governance, Copilot instructions, and canonical workflow definitions; parent-root `.github/workflows` is now historical mirror residue after cutover |
| `.claude/` | `RETIRE-AFTER-VERIFY` | Historical-only for `MASTER.md`, `STATE.md`, `SESSION_LOG.md`, and `BACKLOG.md`; `DECISION_LOG.md` now retained for provenance after its surviving current AI decisions were extracted into the canonical repo |
| `.gitignore` | `RETIRE-AFTER-VERIFY` | Verified parent-root umbrella-only ignore surface with explicit split note; `apex-power-ops-platform/.gitignore` is already the only active ignore contract for canonical repo operations |
| `.vercelignore` | `RETIRE-AFTER-VERIFY` | Keep only if still needed after canonical repo boundary is established |
| `README.md` | `RETIRE-AFTER-VERIFY` | Verified as umbrella/workstation guidance, not project authority; retire or minimize further during residue closeout |
| `PROJECT_STATUS.md` | `RETIRE-AFTER-VERIFY` | Verified as parent-root aligned mirror of the repo-owned status surface; retire or minimize further during residue closeout |
| `PROJECT_OVERVIEW.md` | `RETIRE-AFTER-VERIFY` | Verified as parent-root aligned mirror of the repo-owned overview; retire or minimize further during residue closeout |
| `WORKSPACE_DESIGN.md` | `RETIRE-AFTER-VERIFY` | Verified historical-only design context; current routing now points to repo-owned Olares authority and roadmap surfaces |
| `WORKSPACE_PROTOCOL.md` | `RETIRE-AFTER-VERIFY` | Verified historical-only protocol context; current routing now points to repo-owned Olares authority and operator surfaces |
| `SUPABASE_REPORT_WORKFLOW.md` | `RETIRE-AFTER-VERIFY` | Verified historical-only; preserve repo-owned lineage copy and do not treat parent-root copy as active workflow authority |
| `ARCHIVE_NOTICE.md` | `RETIRE-AFTER-VERIFY` | Verified as historical archive-boundary guidance; current routing now points to repo-owned entry and authority surfaces rather than stale root-era active files |
| `APEX Platform.code-workspace` | `RETIRE-AFTER-VERIFY` | Compatibility shim now opens the canonical repo root; retire after cutover once the repo-owned workspace artifact is the only needed entrypoint |
| `apex-power-ops-platform-clean-main-reconcile/` | `RETIRE-AFTER-VERIFY` | Verified separate `clean-main` reconcile worktree; historical reconciliation lane and not part of permanent topology |
| `apex-power-ops-platform-deploy-worktree/` | `RETIRE-AFTER-VERIFY` | Verified bounded deploy-oriented residue lane with explicit marker README; not part of permanent topology |
| `untracked_files_root.txt` | `RETIRE-AFTER-VERIFY` | Verified transient audit residue with explicit non-authority marker; retire with the parent-root git boundary |
| `_offline-escrow/` | `KEEP-OUTSIDE-LOCAL` | Sensitive local holding, never part of canonical repo structure |

## Recorded Decisions This Matrix Implies

1. No new live authority should be authored only at the parent root.
2. `Platform-Authority/` and `Infrastructure/` were the highest-value authority lanes to re-home into the canonical repo, and that relocation baseline is now materially complete.
3. `Documentation/`, `Supabase/`, `spec/`, and `Reference_Files/` must not be imported wholesale.
4. `apps/`, `packages/`, and `services/` at the parent root require reconciliation by active slice, not bulk merge.
5. The parent-root git boundary and workspace entrypoint are migration debt to retire, not design assets to preserve.

## Recorded Initial Cutover Work Queue

1. Re-home surviving active authority from `Platform-Authority/`.
2. Re-home surviving active governance and operator docs from `Infrastructure/`.
3. Decide the final disposition of parent-root `services/`.
4. Move canonical status and overview authority into the repo root or repo docs.
5. Replace the parent-root workspace entrypoint with a canonical repo-first entrypoint.

This queue records the cutover-time follow-on set that the later cutover-family packets closed or routed. Preserve it as historical execution provenance rather than as an open current checklist.