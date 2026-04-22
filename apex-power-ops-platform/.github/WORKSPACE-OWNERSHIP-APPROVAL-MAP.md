# Workspace Ownership And Approval Map

Date: 2026-04-21
Status: Active governance surface
Scope: `C:/APEX Platform/apex-power-ops-platform`

## Purpose

This file makes path ownership and approval routing explicit for the active platform workspace.

It complements `.github/CODEOWNERS`.

`CODEOWNERS` tells GitHub who must be requested for review.
This document tells operators which stewardship lane is responsible for a path and which approval concerns must be checked before merge.

## Current Maintainer Model

Current maintainer of record:

- `@jasonlswenson-sys`

Current practical reality:

1. GitHub review routing currently collapses to the maintainer of record for every path.
2. Stewardship is still divided by lane so future maintainers can be slotted in without redesigning the repo.
3. No path should rely on chat memory to determine who owns it or which approval concern applies.

## Stewardship Lanes

| Steward lane | Responsibility |
| --- | --- |
| platform-governance | workspace structure, repo policy, authority docs, root contracts |
| runtime-apps | deployable app lanes and app-local runtime behavior |
| shared-packages | reusable package contracts and shared implementation |
| infra-data | infrastructure, database, migration, and environment boundaries |
| ops-automation | runbooks, packets, automation, and operator workflows |
| docs-governance | architecture docs, authority docs, and narrative operator documentation |
| knowledge-curation | governed knowledge assets, mappings, manifests, published artifacts, and extraction boundaries |
| archive-hygiene | archive lanes and legacy snapshots |

## Approval Rules

Baseline rule:

1. Every change requires approval from the primary steward lane for the touched path.

Additional approval requirements:

1. Changes that alter deployment, secrets, environment contracts, migrations, or persistence boundaries also require `infra-data` review.
2. Changes that alter repo policy, lane topology, authority order, or governance process also require `platform-governance` review.
3. Changes that alter shared schemas or reusable package contracts require `shared-packages` review and a consuming runtime impact check.
4. Changes under `docs/authority/` or `docs/architecture/` require `docs-governance` review even when another lane is primary.
5. Changes under `knowledge/` require `knowledge-curation` review. Changes under `docs/knowledge/` require `docs-governance` review, not `knowledge-curation`, unless the change also moves or reclassifies governed knowledge assets.
6. Changes under `archive/` require `archive-hygiene` review and must not silently promote archived material back into active lanes.

## Path Ownership Map

| Path | Primary steward lane | Required approval concerns |
| --- | --- | --- |
| repo root files (`README.md`, `AGENTS.md`, root manifests, workspace config) | platform-governance | platform-governance |
| `.github/` | platform-governance | platform-governance, docs-governance when policy docs change |
| `apps/control-plane-api/` | runtime-apps | runtime-apps, infra-data when API env, persistence, or migration boundaries change |
| `apps/operations-web/` | runtime-apps | runtime-apps |
| `apps/mutation-seam/` | runtime-apps | runtime-apps, infra-data when persistence or integration boundaries change |
| `apps/forms-studio/` | runtime-apps | runtime-apps, shared-packages if shared form contracts are introduced |
| `apps/field-surface/` | runtime-apps | runtime-apps, platform-governance if the lane is renamed or promoted |
| `apps/integration-surface/` | runtime-apps | runtime-apps, platform-governance if keep-or-merge status changes |
| `apps/lead-surface/` | runtime-apps | runtime-apps, platform-governance if keep-or-merge status changes |
| `apps/pm-surface/` | runtime-apps | runtime-apps, platform-governance if keep-or-merge status changes |
| `packages/calc-engine/` | shared-packages | shared-packages, runtime-apps when behavior changes impact active apps |
| `packages/forms-engine/` | shared-packages | shared-packages, runtime-apps when behavior changes impact active apps |
| `packages/api-contracts/` | shared-packages | shared-packages, runtime-apps when shared schemas affect app contracts |
| `infra/` | infra-data | infra-data, platform-governance when topology or import policy changes |
| `ops/agents/` | ops-automation | ops-automation |
| `ops/knowledge-control-plane/` | ops-automation | ops-automation, docs-governance when registry or operator docs become authority surfaces |
| `ops/knowledge-resource-operations/` | ops-automation | ops-automation |
| `knowledge/` | knowledge-curation | knowledge-curation |
| `docs/authority/` | docs-governance | docs-governance, platform-governance |
| `docs/architecture/` | docs-governance | docs-governance, platform-governance |
| `docs/knowledge/` | docs-governance | docs-governance |
| other `docs/` content | docs-governance | docs-governance |
| `tests/` | platform-governance | platform-governance, owning implementation lane review |
| `archive/` | archive-hygiene | archive-hygiene, platform-governance if material is reclassified |

## Workflow Map

Current workflow inventory:

1. `calc-engine-ci.yml`
2. `control-plane-api-ci.yml`
3. `deployed-control-plane-smoke.yml`
4. `pm-idempotency-metrics-export.yml`
5. `pm-idempotency-sweep.yml`

Workflow stewardship:

| Workflow | Primary steward lane | Notes |
| --- | --- | --- |
| `calc-engine-ci.yml` | shared-packages | validates the calc-engine slice |
| `control-plane-api-ci.yml` | runtime-apps | validates the primary backend app lane |
| `deployed-control-plane-smoke.yml` | runtime-apps | smoke validation for deployed control-plane surfaces |
| `pm-idempotency-metrics-export.yml` | ops-automation | ops workflow tied to control-plane observability |
| `pm-idempotency-sweep.yml` | ops-automation | scheduled hygiene workflow for control-plane persistence residue |

## Merge Routing Guidance

Use this order when deciding who must review a change:

1. identify the primary path owner from `.github/CODEOWNERS`
2. identify the primary steward lane from this file
3. add any secondary approval concern triggered by the change type
4. if the change crosses multiple top-level lanes, route it as a cross-lane change and require platform-governance review

Cross-lane changes include:

1. app plus package changes that alter public contracts
2. app plus infra changes that alter runtime or persistence behavior
3. docs plus knowledge changes that move assets across the `knowledge/` versus `docs/knowledge/` boundary
4. topology changes that rename, merge, promote, or archive lanes

## Future Expansion Rule

When additional maintainers or teams are introduced:

1. update `.github/CODEOWNERS` first
2. update this file second
3. keep steward lane names stable unless the governance model itself changes
4. never add a new top-level lane without assigning a primary steward lane and approval concerns at the same time