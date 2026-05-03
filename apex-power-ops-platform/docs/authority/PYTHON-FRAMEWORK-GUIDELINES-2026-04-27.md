# Python Framework Guidelines

This document establishes the current Python framework standard across the active APEX Platform lanes.

It is an authority-layer interpretation document, not a workstation bootstrap note. Use it to decide which Python project pattern is sanctioned for new work, which legacy patterns remain temporarily acceptable, and what cleanup must happen before migration.

## Scope

In scope:

- Python interpreter policy across the active workstation and repo lanes
- dependency-manifest ownership
- lock-file expectations
- linter and formatter ownership
- packaging boundaries for apps versus reusable packages
- migration posture for the three active Python lanes currently visible in this workspace

Out of scope:

- Node.js and browser toolchains
- CI runner images
- Docker or container-specific Python strategy
- non-Python package managers beyond their interaction with Python surfaces

## Audited Lanes

### 1. `apex-power-ops-platform`

Observed 2026-04-27:

- root and imported packages already carry `pyproject.toml`
- reusable packages such as `packages/calc-engine` and `packages/forms-engine` are already package-shaped and use `setuptools` metadata in `pyproject.toml`
- `apps/control-plane-api` currently carries both `pyproject.toml` and `requirements*.txt`
- repo-owned Python tasks execute from the platform root `.venv`
- repo-owned Ruff configuration is now established at the monorepo root
- repo-owned app tooling has been normalized to Ruff on `apps/control-plane-api` and `apps/mutation-seam`

Interpretation:

- this is the target Python governance lane
- reusable code inside `packages/` should be `pyproject.toml` first
- imported applications may temporarily retain requirements-based install surfaces when deployment or bootstrap flows still depend on them
- repo-owned application tooling in this lane should now inherit the monorepo Ruff configuration instead of adding new Black plus Flake8 surfaces

### 2. `source-domains/tcc_v5_backend`

Observed 2026-04-27:

- the repo README already standardizes on `uv`, `.venv`, and `requirements.lock`
- runtime and dev dependencies remain requirements-driven through `requirements.txt`, `requirements-dev.txt`, and `requirements.lock`
- repo bootstrapping now provisions `ruff` instead of `black` and `flake8`
- a repo-local `pyproject.toml` now exists as the Ruff configuration surface while packaging remains requirements-driven
- `requirements.lock` has been regenerated through the documented `uv pip compile` flow against the Ruff-based dev manifest

Interpretation:

- this is a sanctioned legacy application lane
- the current `uv` + `requirements*.txt` + `requirements.lock` model remains acceptable and is now aligned to Ruff-first repo tooling
- this repo is Ruff-migrated for repo-owned tooling, but it is still not a package-managed `pyproject.toml` lane
- that packaging boundary is now considered stable; do not treat `pyproject.toml` + `uv.lock` migration as part of routine lane maintenance

### 3. `source-domains/neta-ett-study-material`

Observed 2026-04-27:

- the repo currently uses `requirements.txt` plus a committed `requirements.lock` and still has no `pyproject.toml`
- the repo-local `.venv` has now been rebuilt onto uv-managed Python 3.13.5
- the committed manifest now declares 103 packages
- the committed `requirements.lock` is now a resolver-generated uv lock surface for the current manifest
- the live repo-local `.venv` contains 103 uniquely named installed packages
- the live repo-local `.venv` now has zero undeclared package names relative to the committed manifest

Interpretation:

- this is a legacy analysis and tooling lane, not a clean framework baseline
- it was correct not to migrate this lane by blindly swapping interpreters first
- manifest normalization, resolver-generated lock generation, live-environment cleanup, and controlled interpreter rebuild are now materially complete
- this lane now satisfies the requirements+lock application pattern on uv-managed Python 3.13

## Governing Decisions

### A. Interpreter Standard

1. `uv`-managed Python is the default for new project work.
2. Python 3.13.x is the preferred baseline unless a repo has an explicit reason to pin higher.
3. System Python 3.14 may remain installed only as a bare workstation fallback, but it is not the sanctioned dependency-install target for any active repo lane.

### B. Environment Standard

1. Every active Python project uses an isolated `.venv/`.
2. System site-packages remain effectively empty except for `pip`.
3. Global Python CLI tools belong in `uv tool install`, not inside project environments unless the repo explicitly needs them as project dependencies.

### C. Manifest Standard

1. New reusable packages and new platform-owned Python modules should be `pyproject.toml` first.
2. Existing application lanes may remain on `requirements.txt` plus `requirements-dev.txt` when that matches the repo's current deploy/bootstrap contract.
3. A repo must not rely on undeclared packages in its live `.venv` as hidden framework state.

### D. Lock Standard

1. A committed lock surface is required for any actively maintained application lane.
2. For requirements-based repos, `requirements.lock` generated by `uv pip compile` is the sanctioned lock format.
3. For future `pyproject.toml`-first app lanes, `uv.lock` is acceptable once the repo explicitly adopts that workflow.
4. `neta-ett-study-material` now has a committed `uv`-generated lock surface and a rebuilt uv-managed Python 3.13 environment with zero undeclared installed packages relative to the committed manifest.

### E. Tooling Standard

1. Ruff is the default lint and formatting standard for new or newly-normalized Python lanes.
2. Black plus Flake8 remain tolerated only in legacy repos where migration has been explicitly deferred.
3. Workstation policy may describe Ruff as the default standard, but repo-local docs must still reflect actual repo state until migration lands.

### F. Testing Standard

1. Validation should run through focused `pytest` slices scoped to the changed lane.
2. Dependency or toolchain migrations must validate with the narrowest repo-owned test surface that can falsify the migration claim.
3. A lock or manifest change without a validation command is not considered closed.

## Sanctioned Lane Patterns

### Pattern 1: Package Lane

Use for reusable Python packages under the future platform root.

Required characteristics:

- `pyproject.toml` with package metadata
- explicit runtime dependencies in `project.dependencies`
- optional test dependencies in extras or a documented dev workflow
- isolated `.venv/`
- focused pytest surface

Current examples:

- `apex-power-ops-platform/packages/calc-engine`
- `apex-power-ops-platform/packages/forms-engine`
- `apex-power-ops-platform/packages/p6-ingest`

### Pattern 2: Application Lane

Use for FastAPI or script-heavy applications that still depend on requirements-driven deployment or bootstrap flows.

Required characteristics:

- `requirements.txt`
- `requirements-dev.txt` when dev tools differ from runtime
- committed `requirements.lock`
- isolated `.venv/` created with `uv`
- README that documents install and lock refresh flow

Current examples:

- `source-domains/tcc_v5_backend`
- `apex-power-ops-platform/apps/control-plane-api`
- `source-domains/neta-ett-study-material`

### Pattern 3: Legacy Analysis Lane

Use only for repos that have not yet been normalized and are still carrying historical tooling state.

Required restrictions:

- do not treat the current `.venv` as authoritative framework truth
- inventory live packages against the committed manifest
- classify undeclared packages before any interpreter migration
- introduce a lock surface before calling the lane normalized

Current example:

- none in the actively normalized lanes audited on 2026-04-27

## Required Next Actions By Lane

### `apex-power-ops-platform`

1. Keep new reusable Python work `pyproject.toml` first.
2. Avoid introducing new requirements-only package lanes under `packages/`.
3. Keep repo-owned app tooling on the shared Ruff baseline unless a repo-local exception is explicitly authorized.
4. When the control-plane app is ready for packaging normalization, decide explicitly whether it stays requirements+lock or moves to `pyproject.toml` plus `uv.lock`.

### `source-domains/tcc_v5_backend`

1. Treat the current repo as valid under the requirements+lock pattern.
2. Treat the Ruff migration as complete for repo-owned tooling surfaces.
3. Keep future packaging changes, if any, separate from the completed toolchain normalization.
4. Do not promote this repo to `pyproject.toml` + `uv.lock` unless a separate repo-structure or deployment-contract decision explicitly authorizes that change.

### `source-domains/neta-ett-study-material`

1. Preserve the cleaned lane-owned dependency set now captured in `requirements.txt` and `requirements.lock`.
2. Preserve the resolver-generated `requirements.lock` as the current authoritative lock surface.
3. Keep the repo-local `.venv` on uv-managed Python 3.13 unless an explicit lane requirement forces a different pin.
4. Treat any future undeclared package drift as a regression against the now-clean manifest-to-environment boundary.

## Prohibited Shortcuts

Do not do any of the following:

- install project dependencies into system Python
- claim Ruff as repo truth where Black and Flake8 still own the repo
- migrate a legacy repo by recreating `.venv` on a new interpreter without first reconciling undeclared packages
- add new package lanes under the platform root that bypass `pyproject.toml`
- treat an unpinned live `.venv` as a substitute for a committed lock file

## Decision Summary

The sanctioned Python framework standard is now:

1. `uv`-managed interpreters and isolated `.venv/` everywhere
2. `pyproject.toml` first for new reusable platform packages
3. `requirements*.txt` plus `requirements.lock` tolerated for legacy application lanes
4. Ruff as the default for new or normalized repos, but not retroactively declared for legacy repos until migration lands
5. `neta-ett-study-material` is now rebuilt from the committed manifest and lock on uv-managed Python 3.13, so future governance there is drift control rather than interpreter cutover