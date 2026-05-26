# Workspace Registry

Date: 2026-05-23
Status: Active workspace-control surface
Scope: repo constellation registry, workspace-level routing contract, and enrollment status for the current Olares-first operating model

## Purpose

This document is the repo-owned workspace registry for the current APEX repo constellation.

It executes Move 1 from the blue-sky Olares workspace architecture by making the multi-repo working set explicit, inspectable, and resumable from inside the canonical repo boundary.

Use this document when the question is:

1. which repos are in the active workspace constellation,
2. what role each repo plays,
3. which repos are fully enrolled in the repo-passport standard,
4. what cross-repo boundaries are allowed,
5. which executor classes are allowed to touch each repo by default.

Companion surfaces:

1. `docs/authority/REPO-PASSPORT-STANDARD-2026-05-23.md`
2. `REPO_PASSPORT.md`
3. `docs/architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md`

## Registry Rules

1. The workspace registry is a routing surface, not a merge directive.
2. Separate repos remain separate repos unless a later authority packet changes that boundary.
3. A repo is not considered fully enrolled until it has a repo passport at its front door.
4. Cross-repo execution must remain packetized whenever it changes more than one repo or changes a shared contract.
5. Data-class and executor-boundary rules apply per repo even when one workspace spans them all.

## Registry Fields

Each repo entry should declare:

1. repo id,
2. canonical path,
3. current role,
4. deployment or runtime posture,
5. dominant data classes,
6. allowed executor classes,
7. passport status,
8. key cross-repo dependencies,
9. current notes on maturity or boundary risk.

## Active Registry

### 1. `apex-power-ops-platform`

- Repo id: `apex-power-ops-platform`
- Canonical local path: `C:/APEX Platform/apex-power-ops-platform`
- Authoritative host path: `/home/olares/code/apex/apex-power-ops-platform`
- Current role: platform substrate, operator workflow surface, workspace-control home base, shared services, governance, and packet history
- Deployment posture: GitHub-canonical publication boundary with Olares-hosted durable mirror and mixed cloud deployment targets
- Dominant data classes: `public`, `internal`, `customer-sensitive`, `ip-core`
- Allowed executor classes: human operator, VS Code Copilot, Desktop Claude, Codex, local AI for private lanes
- Passport status: `active`
- Key cross-repo dependencies: `tcc_v5_backend`, `neta-ett-study-material`, `neta-forms`, future PSS repo when admitted
- Notes: this repo is the canonical workspace-control surface and therefore owns the registry, passport standard, and cross-repo packet grammar

### 2. `tcc_v5_backend`

- Repo id: `tcc_v5_backend`
- Canonical local path: `C:/APEX Platform/source-domains/tcc_v5_backend`
- Current role: calculation-engine and associated integration surface
- Deployment posture: hybrid candidate; calculation core should remain portable between private and cloud runtimes
- Dominant data classes: `internal`, `ip-core`, selective `customer-sensitive`
- Allowed executor classes: human operator, VS Code Copilot, Desktop Claude, Codex for bounded packets, local AI by default for proprietary logic exploration
- Passport status: `provisional`
- Key cross-repo dependencies: `apex-power-ops-platform`
- Notes: strong early candidate for the first cross-repo vertical slice because the domain already shows higher contract maturity than the less-normalized source domains

### 3. `neta-ett-study-material`

- Repo id: `neta-ett-study-material`
- Canonical local path: `C:/APEX Platform/source-domains/neta-ett-study-material`
- Current role: content, governance, and study-side planning surface
- Deployment posture: private-first authoring with later publication of approved artifacts
- Dominant data classes: base `internal` + `ip-core`; carve-out `customer-sensitive` + `ip-core` for `Development/Platform/`, `Development/Control-Plane/`, `Development/Scripts/`, `PowerShell/`, and `PM-Pro-Guide-xer-Templates/` including the sibling `.rar`
- Allowed executor classes: human operator, Desktop Claude, VS Code Copilot for bounded repo-local work, local AI by default for source drafting and sensitive analysis
- Passport status: `provisional`
- Key cross-repo dependencies: `apex-power-ops-platform`
- Notes: structurally important for local-AI routing and IP-boundary enforcement. Data-class carve-out reflects NETA ETT Packet 1 finding #1 resolution and operator-ratified Packet 2 sub-decision on 2026-05-26.

### 4. `neta-forms`

- Repo id: `neta-forms`
- Canonical local path: `C:/APEX Platform/source-domains/neta-forms`
- Current role: form-template and generation-asset surface
- Deployment posture: hybrid candidate with private-first normalization
- Dominant data classes: `internal`, selective `ip-core`
- Allowed executor classes: human operator, Desktop Claude, VS Code Copilot for bounded repo-local work, Codex only after packetized scope declaration
- Passport status: `provisional`
- Key cross-repo dependencies: `apex-power-ops-platform`
- Notes: treated as real source-domain inventory, but still carries the highest normalization debt of the currently registered repos

### 5. Future `pss` domain

- Repo id: `pss` (reserved)
- Canonical local path: not yet admitted
- Current role: unresolved
- Deployment posture: unresolved
- Dominant data classes: unresolved
- Allowed executor classes: unresolved until repo admission
- Passport status: `not-enrolled`
- Key cross-repo dependencies: expected `apex-power-ops-platform`
- Notes: do not treat this as an active repo until a later packet admits the boundary explicitly

## Enrollment Status

Current enrollment result:

1. the workspace registry now exists as a repo-owned control surface,
2. the passport standard now exists,
3. `apex-power-ops-platform` is enrolled with an active repo passport,
4. the source-domain repos are registered but remain provisional until repo-local passports are authored inside their own repo boundaries.

## Next Safe Move

The next safe workspace-architecture move is to author repo-local passports in `tcc_v5_backend`, `neta-ett-study-material`, and `neta-forms`, then use those front-door contracts to choose the first clean cross-repo execution slice.
