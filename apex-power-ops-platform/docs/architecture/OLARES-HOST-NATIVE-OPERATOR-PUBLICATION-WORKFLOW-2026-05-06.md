# Olares Host-Native Operator Publication Workflow

Date: 2026-05-06
Status: Active operator workflow
Scope: preferred Olares-hosted staging, staged-diff review, and focused validation flow while the current publication boundary remains transitional

## Purpose

This workflow makes the authoritative Olares host mirror the default operator surface for bounded git preparation work.

It reduces dependence on the field laptop for staging and staged-diff review without silently changing GitHub canonical status or asserting that the Windows parent-root publication boundary is already retired.

## Boundary Conditions

1. GitHub on `clean-main` remains canonical.
2. `/home/olares/code/apex` remains the authoritative host mirror.
3. `/home/olares/code/apex/apex-power-ops-platform` remains the authoritative host implementation surface.
4. `C:/APEX Platform` remains the current transitional publication boundary until a later explicit cutover packet changes that rule.
5. `/home/olares/src/apex-power-ops-platform` remains observe-only.

## Preferred Operator Surfaces

Use one of these host-native surfaces first:

1. VS Code Remote-SSH attached to `olares-mesh`,
2. direct `ssh olares-mesh` terminal access,
3. browser-terminal fallback on the Olares host when the first two are unavailable.

Use the Windows workspace as a client surface or fallback, not as the default place to originate bounded git preparation.

## Default Host-Native Flow

Run bounded git preparation from `/home/olares/code/apex`.

Host-terminal example:

```bash
cd /home/olares/code/apex
git status --short -- apex-power-ops-platform/
git add -- apex-power-ops-platform/path/to/file1 apex-power-ops-platform/path/to/file2
git diff --cached -- apex-power-ops-platform/
```

Client-triggered one-shot example:

```powershell
ssh olares-mesh 'cd /home/olares/code/apex && git status --short -- apex-power-ops-platform/'
ssh olares-mesh 'cd /home/olares/code/apex && git diff --cached -- apex-power-ops-platform/'
```

Required behavior:

1. keep staging bounded to explicit `apex-power-ops-platform/` paths unless a broader cutover packet explicitly authorizes more,
2. review the staged diff from the host mirror before any commit,
3. run focused validation from the host posture when the touched slice has an admitted host validation path,
4. finish with the normal publication and host-parity gate; this workflow does not skip that closeout.

## Client Fallback

Use `C:/APEX Platform` only when:

1. the host session is unavailable,
2. a client-only tool is explicitly required,
3. a later packet has not yet moved the needed operator helper onto the host.

Fallback use does not reopen a laptop-first default.

## Explicit Non-Goals

This workflow does not authorize:

1. GitHub replacement,
2. Gitea canonical transition,
3. remote rewrite,
4. silent retirement of the parent-root publication boundary,
5. runtime or service mutation,
6. package or lockfile mutation,
7. old-clone mutation.

## Next Remaining Dependency

After this workflow is published, the next remaining publication-boundary retirement target should be the highest-traffic lane README command surfaces that still normalize Windows-local execution.