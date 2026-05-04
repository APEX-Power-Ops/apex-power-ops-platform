# Olares Phase 5 Packet 021 - Bounded Non-Runtime Application-Source Host Trial Planning Handoff

Date: 2026-05-03
Status: Complete - bounded non-runtime application-source host trial planning
Packet: `ops/agents/packets/draft/2026-05-03-olares-phase-5-021-bounded-non-runtime-application-source-host-trial-planning.json`
Scope: define the smallest truthful non-runtime host-side source or test trial after Packet 020 without executing that trial, publishing authority, approving migration, or mutating runtime state

## Authority

This planning pass used:

1. `plan/infrastructure-olares-full-implementation-roadmap-1.md`
2. `ops/agents/handoffs/2026-05-03-olares-phase-5-next-task-and-prompt-routing-handoff.md`
3. `ops/agents/handoffs/2026-05-03-olares-phase-5-020-post-019-workstation-migration-readiness-reassessment-handoff.md`
4. `ops/agents/packets/draft/2026-05-03-olares-phase-5-020-post-019-workstation-migration-readiness-reassessment.json`
5. `ops/agents/handoffs/2026-05-03-olares-phase-5-019-packet-017-artifact-publication-and-host-mirror-resync-gate-handoff.md`
6. `ops/agents/handoffs/2026-05-03-olares-phase-5-017-second-bounded-host-documentation-planning-trial-execution-handoff.md`
7. `ops/agents/handoffs/2026-05-03-olares-phase-5-014-bounded-host-editing-trial-execution-handoff.md`
8. `apps/operations-web`
9. `C:/APEX Platform/Infrastructure/Olares_Workspace_Authority_Framework.md`
10. `C:/APEX Platform/Infrastructure/Olares_Build_Guide.md`

This packet does not reopen generic Olares implementation. It does not approve Olares-first daily development migration, daily center-of-gravity cutover, host runtime mutation, service change, install work, ingress change, auth change, AI-services expansion, Gitea/code-hosting work, canonical-hosting transition, remote rewrite, force, reset, clean, authority publication execution, host-side source execution, or mutation of `/home/olares/src/apex-power-ops-platform`.

## Executive Verdict

Packet 021 closes as `complete - planning`.

Recommended trial class:

`test-only application surface`

Recommended exact later execution slice:

`apps/operations-web/tests/browser-shell.smoke.spec.ts`

Recommended later edit intent:

Extend the existing re-homed browser surfaces smoke coverage to assert the currently advertised PM static surfaces:

1. `/pm-review/schedule.html`
2. `/pm-review/tracer.html`
3. `/pm-review/variance.html`

Reason this is the smallest truthful next host-side source/test trial:

1. it touches one existing test file only
2. it is application-adjacent but non-runtime and does not alter production behavior
3. it stays inside the `apps/operations-web` promoted-host browser proof lane named in the roadmap
4. it exercises a real APEX application surface beyond documentation/planning without requiring backend, database, Docker, Kubernetes, Helm, ingress, auth, or service mutation
5. rollback remains one-file and reviewable

Important sequencing decision:

Packet 019, Packet 020, and Packet 021 closure authority must be published and `/home/olares/code/apex` must be resynchronized before a later host-side execution packet depends on this planning record.

Single next packet:

`Olares Phase 5 022 - Packet 019 Through Packet 021 Authority Publication And Host Mirror Resync Gate`

Packet 022 should publish only the bounded local closure and routing/roadmap authority set needed to make Packet 021 visible on `/home/olares/code/apex`. It should not execute the planned test edit.

## Current Evidence

### Workstation Parent Root

Observed from `C:/APEX Platform`:

| Field | Evidence |
| --- | --- |
| branch | `clean-main` |
| upstream | `origin/clean-main` |
| current base commit | `c91bd571dcaab9e7df82682d396ec3a01529b9dc` |
| local Olares authority drift | Packet 019 closure, Packet 020 closure, Packet 021 JSON, routing, and roadmap surfaces |
| unrelated drift | `.vercelignore` remains untracked and outside this lane |

### Prepared Host Mirror

Read-only SSH evidence from `olares-mesh`:

| Field | Evidence |
| --- | --- |
| path | `/home/olares/code/apex` |
| branch | `clean-main` |
| commit | `c91bd571dcaab9e7df82682d396ec3a01529b9dc` |
| status count | `0` |
| Packet 020 handoff | missing |
| Packet 021 JSON | missing |

Interpretation:

The host mirror is clean, but it is not authority-current for Packet 020 closure or Packet 021 planning. A later execution packet must not rely on Packet 021 instructions on the host until a publication/resync gate puts them there.

### Candidate Application Surface

Observed workstation surface:

| Surface | Evidence |
| --- | --- |
| package | `apps/operations-web/package.json` |
| typecheck script | `pnpm typecheck` -> `tsc --noEmit` |
| browser smoke test | `apps/operations-web/tests/browser-shell.smoke.spec.ts` |
| current smoke coverage | integration dashboard, lead ops, PM drivers review, and PM approval shell |
| advertised but not covered in that smoke block | PM schedule, PM upstream tracer, and PM variance static surfaces |

The later execution should change only the existing smoke test unless the execution packet explicitly detects that the advertised target surfaces are absent or unstable. If they are absent or unstable, the execution packet should stop and report a blocked trial rather than widening the edit.

## Planned Trial Contract

### Allowed File Classes

Allowed for the later execution packet:

1. exactly one test file: `apps/operations-web/tests/browser-shell.smoke.spec.ts`
2. optionally no-op evidence reads of `apps/operations-web/package.json`, `apps/operations-web/playwright.config.ts`, and the target static files under `apps/operations-web/public/`

No other file should be edited by the execution packet unless a separate planning amendment authorizes it.

### Prohibited File Classes

The later execution packet must not edit:

1. production application source under `apps/operations-web/app/` or `apps/operations-web/lib/`
2. `package.json`, lockfiles, dependency manifests, or `node_modules`
3. `.env`, `.env.local`, `.env*.local`, secrets, tokens, credentials, or Supabase config
4. `.next`, `.vercel`, test output, Playwright report, or generated build artifacts
5. Docker, Kubernetes, Helm, Olares, ingress, auth, LarePass, Headscale, or service configuration
6. parent-root remotes or git config
7. `/home/olares/src/apex-power-ops-platform`
8. unrelated parent-root files such as `.vercelignore`

### Entry Criteria For Later Execution

The later execution packet must verify before editing:

1. Packet 022, or an equivalent bounded authority-publication packet, has published Packet 019, Packet 020, and Packet 021 closure authority.
2. `/home/olares/code/apex` is on `clean-main`, clean, and synchronized to the Packet 022 governing commit.
3. `git rev-parse --show-toplevel` from the host implementation lane resolves to `/home/olares/code/apex`.
4. `git rev-parse --show-prefix` from `/home/olares/code/apex/apex-power-ops-platform` resolves to `apex-power-ops-platform/`.
5. `/home/olares/src/apex-power-ops-platform` remains untouched historical evidence.
6. The advertised static routes or files for schedule, tracer, and variance exist under `apps/operations-web/public/pm-review/`.

If any entry criterion fails, the execution packet should stop before editing.

### Validation Commands For Later Execution

Required non-runtime validation:

1. `git diff --check -- apps/operations-web/tests/browser-shell.smoke.spec.ts`
2. `pnpm --dir apps/operations-web typecheck`
3. `git status --short`

Optional validation, only if the host already has dependencies and Playwright browsers available without install:

1. `pnpm --dir apps/operations-web smoke:browser`

If optional browser validation requires install work, browser installation, package-manager mutation, service mutation, or runtime reconfiguration, skip it and record that it was unavailable under the no-install boundary.

### Success Criteria For Later Execution

The later execution succeeds only if:

1. exactly one planned test file changes
2. no runtime, service, auth, ingress, secret, package, or generated artifact changes occur
3. required validation passes or any unavailable optional validation is explicitly recorded as skipped without install
4. host status shows only the planned test file as the trial artifact
5. rollback remains a one-file inverse patch
6. `/home/olares/src/apex-power-ops-platform` remains unchanged

### Failure And Stop Triggers

The later execution must stop if:

1. the host mirror is not clean before editing
2. Packet 019/020/021 closure authority is not present on the host after the required publication/resync gate
3. the target static PM files are missing
4. the edit requires production source changes to make tests pass
5. validation requires installs or dependency mutation
6. any `.env`, secret, package, lockfile, runtime, service, ingress, auth, remote, generated, or old-clone surface would need mutation
7. rollback would require force, reset, clean, remote rewrite, branch switch, or old-clone mutation

### Rollback Rules

Rollback for the later execution must be limited to reversing the one test-file edit. It must not use force, reset, clean, branch switch, remote rewrite, service mutation, runtime mutation, install work, or old-clone mutation.

## Task Status Impact

### TASK-021

No checkbox change is required.

Restatement:

The repo authority and publication model can now support planning a one-file non-runtime test-only host-side trial, but it still does not approve daily Olares-first development or application-source editing as a general workflow.

### TASK-023

No status change is required.

Packet 021 does not assess or expand AI-services, services-zone runtime, Olares apps, Docker, K3s, Helm, or installed services.

### TASK-025

No checkbox change is required.

The split-path result remains:

1. workstation-only migration: bounded-trial planning may continue
2. AI-services-zone expansion: not ready
3. Gitea/code-hosting mirror enhancement: not ready
4. broader canonical-hosting transition: no-go

## Explicit No-Go Items Preserved

Packet 021 does not authorize:

1. Olares-first daily development migration
2. host runtime mutation
3. host-side trial execution
4. authority-publication execution
5. service start, stop, restart, reconfiguration, or install work
6. Docker, Kubernetes, Helm, ingress, auth, LarePass, Headscale, or Olares Settings changes
7. AI-services expansion
8. Gitea/code-hosting transition
9. canonical-hosting transition
10. remote rewrite
11. force, reset, or clean
12. mutation of `/home/olares/src/apex-power-ops-platform`
13. inclusion of unrelated `.vercelignore`

## Final Recommendation

Packet 021 supports opening one narrow publication packet first:

`Olares Phase 5 022 - Packet 019 Through Packet 021 Authority Publication And Host Mirror Resync Gate`

After that publication/resync gate closes cleanly, a separate execution packet may run the planned one-file test-only host trial against `apps/operations-web/tests/browser-shell.smoke.spec.ts`.

Final readiness:

1. trial class: test-only application surface
2. execution readiness: deferred until Packet 019/020/021 authority is published and host-resynchronized
3. full migration: not approved
4. AI-services expansion: not ready
5. Gitea/code-hosting: not ready
6. canonical-hosting transition: no-go
