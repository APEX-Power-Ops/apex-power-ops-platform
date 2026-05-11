# Olares Host-Native Operator Publication Workflow

Date: 2026-05-06
Status: Active operator workflow
Scope: preferred Olares-hosted staging, staged-diff review, and focused validation flow from the canonical standalone repo root

Closeout interpretation note:

This workflow remains the current preferred bounded git-preparation path for the Olares-first repo posture. It is a standing operator baseline, not a packet-era queue opener.

Current routing:

1. use `../OPERATOR-BOOTSTRAP-RUNBOOK.md` for the broader repo-root and host-root operator workflow contract,
2. use `APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md` and `../../PROJECT_STATUS.md` for current lane selection and residue-retirement frontier,
3. use this document when the question is specifically how to originate bounded staging, staged-diff review, and focused validation preparation from the authoritative Olares host mirror.

## Purpose

This workflow makes the authoritative Olares host implementation repo the default operator surface for bounded git preparation work.

It reduces dependence on the field laptop for staging and staged-diff review while keeping GitHub canonical and the standalone repo boundary explicit.

## Boundary Conditions

1. GitHub on `clean-main` remains canonical.
2. `/home/olares/code/apex/apex-power-ops-platform` remains the authoritative host implementation surface.
3. `C:/APEX Platform/apex-power-ops-platform` is the matching workstation repo root.
4. `C:/APEX Platform` is workstation-umbrella residue, not the publication boundary for this repo.
5. `/home/olares/src/apex-power-ops-platform` remains observe-only.

## Preferred Operator Surfaces

Use one of these host-native surfaces first:

1. VS Code Remote-SSH attached to `olares-mesh`,
2. direct `ssh olares-mesh` terminal access,
3. browser-terminal fallback on the Olares host when the first two are unavailable.

Use the Windows workspace as a client surface or fallback, not as the default place to originate bounded git preparation.

## Default Host-Native Flow

Run bounded git preparation from `/home/olares/code/apex/apex-power-ops-platform`.

Host-terminal example:

```bash
cd /home/olares/code/apex/apex-power-ops-platform
git status --short
git add -- path/to/file1 path/to/file2
git diff --cached -- .
```

Client-triggered one-shot example:

```powershell
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git status --short'
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git diff --cached -- .'
```

Required behavior:

1. keep staging bounded to explicit repo-relative paths unless a broader change explicitly authorizes more,
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
4. silent publication-boundary changes outside the canonical standalone repo,
5. runtime or service mutation,
6. package or lockfile mutation,
7. old-clone mutation.

## Current Follow-On Boundary

This host-native workflow now assumes the standalone repo root is already canonical.

Use a separate bounded packet only if a different high-traffic lane README, packet surface, or operator entrypoint still normalizes parent-root or Windows-first publication practice unnecessarily.