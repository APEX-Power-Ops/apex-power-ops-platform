# Resource Governance Audit
## End-to-End Resource Lifecycle, Policy, and Supabase Reconciliation
### Version 1.1 | March 25, 2026

---

## Purpose

This document defines the governed operating model for resources across the workspace. It connects:

1. source intake and canonical storage
2. naming and category rules
3. manifest-based tracking
4. curated extraction processing
5. coverage measurement
6. Supabase `study_content.source_path` integrity
7. retirement and historical-source handling

This is the authoritative resource lifecycle audit and policy summary referenced by `MASTER-STANDARDS.md`.

---

## Authoritative Surfaces

Use these together. No single one is sufficient by itself.

| Surface | Role |
|---|---|
| `MASTER-STANDARDS.md` | Top-level standards and resource control rules |
| `GOVERNANCE-FRAMEWORK.md` | Enforcement, authority, escalation, and change-control model |
| `Process-Guides/RESOURCE-EXTRACTION-GUIDE.md` | Extraction quality and disk-first processing standard |
| `Resources/RESOURCE-MANIFEST-RAW.json` | File-level inventory of the active `Resources/` tree |
| `Resources/RESOURCE-MANIFEST.json` | Enriched linkage surface for inventory, extraction, and coverage context |
| `Development/RESOURCE-COVERAGE-REPORT.md` | Coverage and extraction-gap reporting |
| `Development/RESOURCE-PATH-STATUS.md` | Current Supabase path audit state |
| `Development/RESOURCE-PATH-REMEDIATION.md` | Remaining mismatches and retired-source dispositions |

---

## Current Audited State

### Active Top-Level Resource Trees

The active `Resources/` tree currently consists of:

- `All-About-Circuits/`
- `Catalog/`
- `Extractions/`
- `References/`
- `Source-PDFs/`
- `Templates/`
- `Tools/`
- `RESOURCE-MANIFEST-RAW.json`
- `RESOURCE-MANIFEST.json`

### Canonical Active Source Categories

The active source library under `Resources/Source-PDFs/` is normalized to these categories:

- `ASTM/`
- `CIGRE/`
- `Equipment-Manuals/`
- `Exam-Resources/`
- `IEC/`
- `IEEE/`
- `Industry-Guides/`
- `Industry-NETA/`
- `Instrument-Transformers/`
- `NEMA/`
- `NETA/`
- `NFPA-OSHA/`
- `PEARL/`
- `Textbooks/`
- `UL/`
- `VFD/`
- `_Unsorted/`

### Confirmed Residual Supabase Path Cases

The current governed status of `study_content.source_path` reconciliation is:

- 873 rows audited
- 0 remaining auto-fix cases
- 2 remaining documented residual cases

Residual cases:

- `EXT-IEEE-030` - historical-source-retired
- `EXT-IEEE-040` - historical-source-retired

These are no longer general “manual review” cases. They are explicitly classified dispositions for sources that were historically referenced but are not present in the active governed library.

---

## End-to-End Resource Lifecycle

### 1. Intake

New or recovered source material enters through `Resources/Source-PDFs/_Unsorted/`.

Controls:

- do not load new sources straight into arbitrary categories without naming and classification
- maintain `_Unsorted/` as a queue, not a permanent storage area
- identify duplicates or clearly superseded copies before promotion into the canonical library

### 2. Naming and Classification

Each active source is assigned one canonical home in `Resources/Source-PDFs/`.

Controls:

- standards use stable organization and standard identifiers in the filename
- books, manuals, and guides use publisher/author plus concise descriptive slug
- legacy alias categories are not valid for new placement
- active source categories should contain source materials, not extraction byproducts

### 3. Canonical Storage

`Resources/Source-PDFs/` is the source-of-record for active PDFs used by the platform.

Controls:

- one active source should not exist in multiple canonical categories
- category names are part of the governed contract and should not be changed casually
- any structural rename requires manifest regeneration and downstream path audit

### 4. Inventory and Tracking

Resource tracking is manifest-first.

Controls:

- `RESOURCE-MANIFEST-RAW.json` captures the live tree state
- `RESOURCE-MANIFEST.json` enriches that inventory with workflow linkage
- folder browsing alone is not sufficient evidence for coverage or integrity claims

### 5. Curated Extraction Processing

Extraction is governed by `Process-Guides/RESOURCE-EXTRACTION-GUIDE.md`.

Controls:

- disk-first workflow: extraction lands on disk before any Supabase load
- curated markdown only; raw dumps do not satisfy the standard
- extraction header must preserve source citation, content ID, scope, and quality metadata
- extraction location should follow the canonical source category when practical, with documented exceptions for governed historical folders

### 6. Coverage and Gap Reporting

Coverage is measured against the active source library, not against memory or stale catalogs.

Controls:

- `Development/RESOURCE-COVERAGE-REPORT.md` is the primary human-readable gap report
- coverage should distinguish between extracted, extraction-only, Supabase-only, and unextracted states
- extraction prioritization should follow source relevance, not only file availability

### 7. Supabase Metadata Integration

Supabase is the deployment-side metadata system, not the source of truth for file placement.

Controls:

- `study_content.source_path` must match a canonical repo-relative path under `Resources/`
- Supabase paths should be reconciled against the active source library and manifest, not legacy folder memory
- source-path correction work must be documented as an auditable batch rather than silent record churn

### 8. Drift Audit and Remediation

Source-path drift is expected over time whenever files are reorganized, renamed, or retired.

Controls:

- run audit scripts against current paths before large metadata updates
- apply verified remaps only where the source file can be proven
- classify irreconcilable historical references as `historical-source-retired`
- regenerate `Development/RESOURCE-PATH-STATUS.md` and `Development/RESOURCE-PATH-REMEDIATION.md` after each remediation pass

### 9. Retirement and Historical Handling

Not every historical resource should remain active.

Controls:

- retired sources may remain documented for provenance without remaining part of the active source contract
- historical trees such as `Testing Resources/` are not to be restored as active working structures
- if a content record points only to a retired historical source with no governed active replacement, document the disposition instead of manufacturing a path

---

## Audit Findings

### Finding 1: Canonical Source Categories Have Already Been Normalized

The on-disk `Source-PDFs/` tree already reflects the intended canonical category model. Top-level governance documentation was lagging this reality and still showed legacy examples such as `IEEE-Standards/` and `NETA-Standards/`.

Disposition:

- authority docs updated to reflect the live canonical categories

### Finding 2: Extractions Still Contain Transitional Historical Splits

`Resources/Extractions/` includes both aligned canonical categories and historical categories such as `NETA-Standards/`, `NFPA-70E/`, `OSHA/`, `Paul-Gill/`, and vendor-specific groupings.

Disposition:

- preserve governed continuity for existing extraction history
- require new extraction placement to default to canonical source categories unless an established governed exception applies

### Finding 3: Tracking Needed a Single Lifecycle Model

The workspace already had manifests, coverage reports, extraction guides, and path remediation docs, but they were not elevated into a single lifecycle policy.

Disposition:

- establish a manifest-centered, disk-first, audit-backed lifecycle in governance surfaces

### Finding 4: Supabase Drift Is Mostly Resolved

Path remediation is substantially complete. The residual set is down to two historical-source-retired cases.

Disposition:

- treat future remediations as bounded audits
- do not leave unresolved rows in a vague manual-review state when the real disposition is retirement

### Finding 5: `Testing Resources/` Is Historical, Not Active

The previous `Testing Resources/` corpus represented a legacy dump, not a governed active library. Its useful content was triaged for promotion, archival retention, or discard.

Disposition:

- `Testing Resources/` is retired from the active model
- do not use it as a valid active source-path prefix or storage location

### Finding 6: Active Operator Surfaces Still Contained Legacy Path Drift

After the primary governance alignment, a deeper pass over active scripts and operator-facing resource docs still found a small number of surfaces that could reintroduce or reinforce retired paths:

- `Development/Scripts/Build/build_resource_manifest.py` still enumerated `Testing Resources/` as an active tree
- `Resources/Extractions/EXTRACTION-CATALOG.md` still presented current source locations using retired names such as `IEEE-Standards/`, `ETT-Study-Materials/`, and `022826/`
- `Resources/QUICK-LOOKUP.md` still pointed to retired or missing active locations, including `NETA-Standards/` as a source-PDF path and removed Anki/Testing Resources trees
- `Resources/Catalog/KSA-MASTER-INDEX.md` still referenced the old `NETA-Standards/` source-PDF path for the ETT standard

Disposition:

- remove retired trees from active build/indexing scripts
- normalize active operator docs to canonical live paths or explicit historical notes
- keep broader historical/planning references separate from the active operating contract unless they are intentionally being rebaselined

### Finding 7: Active Loader Metadata Needed Canonical Source-Path Rebinding

After the script portability pass, active Supabase loader scripts still contained a bounded set of retired source-library aliases in payload metadata, including `IEEE-Standards/`, `IEC-Standards/`, `UL-Standards/`, `NETA-Standards/`, and `Manufacturer-Docs/`.

The affected active loader surfaces were limited to a small group of batch loaders and curated loaders that still referenced otherwise-correct source filenames through retired category prefixes.

Disposition:

- normalize active loader payload metadata to canonical source-library paths only where the exact replacement file is present on disk
- leave unresolved ATS manufacturer-source cases unremapped when the canonical `_Unsorted/` file cannot be proven, rather than guessing a replacement
- treat remaining legacy extraction-bucket paths separately from source-path governance when those buckets are still preserved as governed historical output folders

---

## Required Operating Rules

### Resource Naming

- use hyphenated filenames with meaningful identifiers
- preserve organization, standard number, and year where known
- avoid generic filenames that hide the document identity

### Resource Location

- all active source PDFs live under `Resources/Source-PDFs/`
- all active curated extractions live under `Resources/Extractions/`
- human-readable indexes belong in `Resources/Catalog/`
- helper tables/viewers belong in `Resources/References/`
- calculators and study utilities belong in `Resources/Tools/`

### Resource Processing

- extract once, curate well, reuse often
- do not treat OCR or raw text dumps as deliverables
- source changes and folder renames require a new manifest build

### Resource Tracking

- use manifests as the machine-readable tracking layer
- use coverage and path-status reports as auditable summary layers
- do not rely on stale catalogs or ad hoc counts for completion claims

### Supabase Corrections

- verify the local canonical source before writing any `source_path` correction
- update audit status documentation with each correction pass
- classify missing historical sources explicitly instead of mapping by guesswork

---

## Recurring Audit Checklist

Run this checklist after major resource restructuring, bulk intake, or Supabase reconciliation work:

1. confirm canonical `Source-PDFs/` categories still match workspace standards
2. regenerate `RESOURCE-MANIFEST-RAW.json`
3. regenerate `RESOURCE-MANIFEST.json`
4. update extraction coverage reporting
5. audit `study_content.source_path` against canonical repo-relative paths
6. document remaps, residual mismatches, and historical-source-retired cases
7. update any authority documentation affected by structural changes

---

## Governing Conclusion

The workspace now has a coherent governed resource model:

- canonical source storage in `Resources/Source-PDFs/`
- curated disk-first processing in `Resources/Extractions/`
- manifest-based inventory and linkage
- coverage reporting as a planning surface
- Supabase path integrity as an auditable downstream control
- explicit retirement handling for historical sources that no longer belong to the active library

Future resource work should be judged against this lifecycle, not against older folder names or informal historical practice.