# Olares Phase 5 Packet 029 - Post-028 Narrow Application-Source Trial Planning Handoff

Date: 2026-05-04
Status: Complete - planning
Packet: `ops/agents/packets/draft/2026-05-03-olares-phase-5-029-post-028-narrow-application-source-trial-planning.json`
Scope: plan one bounded non-runtime application-source host trial after Packet 028 restored Packet 026 and Packet 027 authority parity, without editing source or approving migration

## Authority

This planning pass used:

1. `ops/agents/packets/draft/2026-05-03-olares-phase-5-029-post-028-narrow-application-source-trial-planning.json`
2. `ops/agents/handoffs/2026-05-03-olares-phase-5-028-packet-026-and-packet-027-authority-publication-and-host-mirror-resync-gate-handoff.md`
3. `ops/agents/packets/draft/2026-05-03-olares-phase-5-028-packet-026-and-packet-027-authority-publication-and-host-mirror-resync-gate.json`
4. `ops/agents/handoffs/2026-05-03-olares-phase-5-027-post-026-workstation-migration-readiness-reassessment-handoff.md`
5. `ops/agents/handoffs/2026-05-03-olares-phase-5-026-packet-023-test-artifact-publication-and-host-mirror-resync-gate-handoff.md`
6. `ops/agents/handoffs/2026-05-03-olares-phase-5-next-task-and-prompt-routing-handoff.md`
7. `plan/infrastructure-olares-full-implementation-roadmap-1.md`

Packet 029 does not reopen generic Olares implementation. It does not approve migration, runtime mutation, service mutation, install work, package or lockfile mutation, source edits, AI-services expansion, Gitea/code-hosting transition, canonical-hosting transition, remote rewrite, force, reset, clean, or mutation of `/home/olares/src/apex-power-ops-platform`.

## Executive Verdict

Packet 029 closes as `complete - planning`.

Decision:

`plan one first production-source host trial, but publish Packet 028 and Packet 029 authority before execution`

Selected target surface:

`apps/operations-web` relay browser selection reset surface

Planned later write set:

1. `apps/operations-web/app/relay-resource-explorer.tsx`
2. `apps/operations-web/tests/browser-shell.smoke.spec.ts`

The selected trial should add one bounded source-side reset or clear-selection affordance for the relay browser and a focused browser-smoke assertion proving it clears selection state without widening backend calls. The exact implementation remains deferred to the later execution packet.

## Current Evidence

### Prepared Host Mirror

Observed through read-only SSH:

```text
host_path=/home/olares/code/apex
host_branch=clean-main
host_commit=9690d1d93136e74b3ee12b4427fc8c6a25c5e0ce
host_remote=https://github.com/jasonlswenson-sys/RESA-Power-Project-Management.git
host_status_count=0
packet026_handoff=present
packet027_handoff=present
packet028_json=present
```

Interpretation:

Packet 028 authority parity is sufficient for planning. It is not sufficient to execute from the current local Packet 029 planning record until Packet 029 itself is published or otherwise synchronized.

### Preserved Historical Clone

Observed through read-only SSH:

```text
old_path=/home/olares/src/apex-power-ops-platform
old_branch=clean-main
old_commit=2836a2622309b4e146ca24f23b5bf87312c0c857
old_remote=https://github.com/jasonlswenson-sys/apex-power-ops.git
old_status_count=30
```

Interpretation:

The old clone remains untouched historical evidence and must not be blended into the prepared host mirror.

### Host Validation Limitation

Observed through read-only SSH inside `/home/olares/code/apex/apex-power-ops-platform/apps/operations-web`:

```text
node_modules=missing
playwright_cache=missing
```

Interpretation:

Host-side executable validation is still unavailable under the no-install boundary. This does not block a bounded host-side edit trial, but it blocks direct publication of any source artifact without a separate no-install workstation validation step or another explicitly approved validation path.

### Workstation App Surface

Observed tracked `apps/operations-web` surfaces:

1. `app/apparatus-resource-explorer.tsx`
2. `app/page.tsx`
3. `app/relay-resource-explorer.tsx`
4. `app/relay-selection-panels.tsx`
5. `lib/apparatus-resources.ts`
6. `lib/browser-env.ts`
7. `lib/relay-resources.ts`
8. `tests/browser-shell.smoke.spec.ts`
9. `scripts/smoke-hosted-routes.mjs`
10. `scripts/smoke-promoted-host.mjs`

Relevant validation scripts from `apps/operations-web/package.json`:

1. `typecheck`: `tsc --noEmit`
2. `smoke:browser`: `pnpm build && playwright test`
3. `smoke:hosted`: `node scripts/smoke-hosted-routes.mjs`
4. `smoke:promoted-host`: `node scripts/smoke-promoted-host.mjs`

## Candidate Surface Assessment

### Candidate A - Static Re-Homed Route Smoke

Files:

1. `apps/operations-web/tests/browser-shell.smoke.spec.ts`
2. `apps/operations-web/scripts/smoke-hosted-routes.mjs`

Disposition:

Deferred.

Reason:

Packet 023 through Packet 026 already proved a test-only application-adjacent loop against the static PM route surface. Repeating that shape would not materially answer the remaining blocker that no production-source edit has been trialed.

### Candidate B - Apparatus UUID Consumer

Files:

1. `apps/operations-web/app/apparatus-resource-explorer.tsx`
2. `apps/operations-web/tests/browser-shell.smoke.spec.ts`

Disposition:

Deferred.

Reason:

The apparatus invalid-UUID guard is already covered by the first browser smoke test and is simpler than the relay browser state surface. It is a valid future target, but it is less useful for the first production-source host trial.

### Candidate C - Relay Selection Panel Rendering

Files:

1. `apps/operations-web/app/relay-selection-panels.tsx`
2. `apps/operations-web/tests/browser-shell.smoke.spec.ts`

Disposition:

Deferred.

Reason:

This surface is source-real and well covered, but it is larger and more presentation-heavy than needed for the first production-source host trial.

### Candidate D - Relay Browser Selection Reset

Files:

1. `apps/operations-web/app/relay-resource-explorer.tsx`
2. `apps/operations-web/tests/browser-shell.smoke.spec.ts`

Disposition:

Selected.

Reason:

The relay browser already has deterministic mocked Playwright coverage for search results, primary and compare selection, backend-call counts, and selection panel rendering. A small reset or clear-selection affordance is a narrow production-source change that exercises React state management without changing backend routes, packages, runtime, environment, or deployment configuration.

## Planned Trial Shape

The later execution packet should:

1. operate from `/home/olares/code/apex/apex-power-ops-platform`;
2. verify the host mirror is clean at the then-governing published authority commit before editing;
3. edit only `apps/operations-web/app/relay-resource-explorer.tsx` and `apps/operations-web/tests/browser-shell.smoke.spec.ts`;
4. add a bounded relay reset or clear-selection affordance in the source file;
5. add a focused browser-smoke assertion that the affordance clears primary or compare selection state and does not issue unexpected context, settings, or plot requests;
6. run host-side `git diff --check` and path-scope verification;
7. record that host typecheck and Playwright remain unavailable if `node_modules` and browser cache are still missing;
8. leave the source artifact uncommitted on the host until a separate decision or validation packet handles workstation validation and publication.

The execution packet should not install dependencies, start services, mutate runtime, change packages, change lockfiles, rewrite remotes, force, reset, clean, or touch the old clone.

## Validation Plan

Host-side validation during the later execution packet:

1. `git status --short`
2. `git diff -- apps/operations-web/app/relay-resource-explorer.tsx apps/operations-web/tests/browser-shell.smoke.spec.ts`
3. `git diff --check -- apps/operations-web/app/relay-resource-explorer.tsx apps/operations-web/tests/browser-shell.smoke.spec.ts`
4. evidence that no package, lockfile, runtime, service, generated, or secret file changed

Required workstation validation before publication:

1. mirror the exact host diff into `C:/APEX Platform/apex-power-ops-platform`;
2. run `git diff --check` against the two-file diff;
3. run `pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck`;
4. run `pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web smoke:browser`;
5. compare the workstation diff to the host artifact before any publication packet.

## Rollback Plan

Before publication, rollback should be path-scoped only:

1. restore `apps/operations-web/app/relay-resource-explorer.tsx` from the governing host `HEAD`;
2. restore `apps/operations-web/tests/browser-shell.smoke.spec.ts` from the governing host `HEAD`;
3. verify host status is clean;
4. do not use `git reset`, `git clean`, branch switching, remote rewrite, or old-clone mutation.

Any rollback must be explicitly authorized by the execution or decision packet that owns the artifact.

## Blocker Decision

Remote-moved condition:

Not a blocker for the next planning or host-side execution packet because execution does not require push. It remains a blocker or ambiguity for any later publication packet and must continue to be handled without remote rewrite unless a separate remote-authority packet authorizes a change.

Host-side executable validation gap:

Not a blocker for a bounded host-side source trial if the execution packet stops at host diff evidence. It is a blocker for direct publication. A separate workstation validation or explicitly approved host toolchain lane is required before publication.

## Single Next Packet

Packet 029 supports opening exactly one narrow next packet:

`Olares Phase 5 030 - Packet 028 And Packet 029 Authority Publication And Host Mirror Resync Gate`

Purpose:

Publish the Packet 028 closure handoff, Packet 029 planning handoff, Packet 029 completion JSON, minimal routing and roadmap updates, and the authored Packet 030 JSON through the parent-root boundary, then fast-forward-only synchronize `/home/olares/code/apex` so the later host-side source trial starts from a host mirror that already carries the planning authority.

This must happen before any host-side source or test execution packet depends on Packet 029.

## No-Go Items Preserved

Packet 029 did not perform or authorize:

1. migration approval
2. Olares-first daily development cutover
3. runtime or service mutation
4. service start, stop, restart, or reconfiguration
5. installs
6. package or lockfile changes
7. source edits
8. ingress or auth changes
9. Docker, Kubernetes, Helm, LarePass, Headscale, or Olares Settings changes
10. AI-services expansion
11. Gitea/code-hosting transition
12. canonical-hosting transition
13. remote rewrite
14. force, reset, or clean
15. mutation of `/home/olares/src/apex-power-ops-platform`

## Final Recommendation

Packet 029 closes as complete.

Final readiness:

1. Packet 028 authority parity: sufficient for planning
2. selected target: relay browser selection reset surface
3. next required move: Packet 030 authority publication and host-mirror resync
4. later execution posture: first bounded production-source host trial, not migration
5. validation posture: host diff evidence first, workstation executable validation before publication
6. migration, runtime, AI-services, Gitea/code-hosting, and canonical-hosting: not ready
