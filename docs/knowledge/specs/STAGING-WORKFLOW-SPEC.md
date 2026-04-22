# Staging Workflow Specification
## Canonical Build-Spec Surface For Content Staging Workflow

Created: April 4, 2026
Status: Active canonical specification
Purpose: Define how staged content moves through activation, authoring, review, load, and truth-surface closeout in the current workspace model

---

## Scope

This specification defines the workflow for content that lives under `Development/staging/`.

It covers:

1. topic-folder activation
2. scaffold and assembly sequencing
3. pre-load review and image pass expectations
4. load and post-load truth updates
5. workflow boundaries between staging, Git, and Supabase

It does not cover:

1. HTML presentation requirements for tests or guides
2. runtime backend implementation
3. broad session-protocol or lane-governance rules beyond what staging work must obey
4. general repo governance outside staging workflow behavior

---

## Authority Relationship

This file is the canonical build-spec surface for staging workflow behavior.

It should be read together with:

1. `Development/staging/STAGING-PROCESS.md` for the detailed operational lifecycle and folder conventions
2. `MASTER-STANDARDS.md` for governing naming, workspace, and documentation rules
3. `Build-Specs/INFRASTRUCTURE-ROADMAP.md` for the historical planning context that originally called for this artifact

Interpretation:

1. this spec defines the stable workflow contract
2. `Development/staging/STAGING-PROCESS.md` remains the live operational detail surface when more procedural depth is needed
3. if the two ever diverge, reconcile them explicitly rather than silently using whichever file is newer

---

## Source-Of-Truth Model

Staging workflow must preserve this hierarchy:

1. Git is authoritative for staged assembled markdown
2. `Development/staging/` is the active authoring workspace
3. Supabase is the deployed copy derived from staged markdown, not the editing surface

Operational meaning:

1. edit staged markdown, not live Supabase rows
2. treat `STATUS.md` as the folder-level truth surface before acting on a topic
3. keep staging and canonical accepted surfaces distinct unless a separate promotion decision says otherwise

---

## Required Folder Shape

Every staged topic should use one topic folder under `Development/staging/`.

Minimum contents:

1. one `STATUS.md`
2. one assembled guide or staged primary artifact when assembly exists
3. any intermediate files needed to preserve build traceability

Rules:

1. do not leave loose topic artifacts at the root of `Development/staging/`
2. do not delete intermediates just because a guide has loaded
3. do not treat staging as temporary scratch space

---

## Standard Workflow Stages

The standard workflow is:

1. planned
2. scaffolded
3. in progress
4. assembled
5. pre-load review / IMG pass
6. staged
7. loaded
8. published

Workflow meaning:

1. a topic should not skip directly from initial setup to load without a truthful assembled and review stage
2. `active_work` in `STATUS.md` determines whether other operators should avoid load or overwrite actions
3. the pre-load review / IMG pass is a required gate, not optional cleanup

---

## Canonical Startup Sequence For New Topics

For a new guide or packet-local topic under staging, the workflow should follow this order:

1. complete any required boundary review first if the topic spans multiple NETA sections
2. create the topic folder
3. write `STATUS.md` before other artifacts
4. generate topic config, scaffold, and task artifacts in the approved build order
5. assemble the guide only after the required inputs exist
6. perform pre-load review and IMG pass before any load attempt
7. load with the governed loader only after the staged artifact is actually ready
8. update truth surfaces after load

This keeps staging workflow deterministic and reviewable.

---

## Pre-Load Review Requirements

Before a staged guide is treated as load-ready, the workflow must confirm:

1. publication-safe citation cleanup is complete
2. format ordering matches the active content standard
3. image placeholder insertion has been reviewed and applied where appropriate
4. unresolved `VERIFY`, `TODO`, or placeholder issues are either closed or explicitly recorded

The pre-load review exists to prevent staging from becoming a silent bypass around quality gates.

---

## Load And Closeout Rules

After a successful load:

1. update `STATUS.md` with load truth and UUID when applicable
2. preserve the staged markdown as the authoritative editable source
3. run any follow-on discovery or linking step required by the packet or workflow
4. keep packet or validation artifacts truthful about what was loaded and what remains open

Do not treat load success by itself as final publication or broad closeout if later review steps still remain.

---

## Workflow Boundaries

The staging workflow must preserve these boundaries:

1. staging is the authoring workspace, not the canonical accepted-spec namespace
2. Supabase is deployment state, not editing authority
3. workflow specs and build specs may describe staging, but they should not quietly replace live `STATUS.md` and packet truth for an individual topic
4. packet-scoped exceptions should be explicit rather than improvised

---

## Relationship To Older Staging Format Guidance

`Build-Specs/STAGING-FORMAT-SPEC.md` remains useful as a historical format-spec surface for older markdown staging patterns.

This file is different.

It defines workflow behavior, not just file formatting.

Use this file when the question is how staged content should move through the workspace lifecycle.

Use the format spec only when older or narrower formatting guidance is still directly relevant.

---

## Bottom Line

The staging workflow is the governed path by which staged content is created, reviewed, loaded, and kept truthful across Git, `STATUS.md`, and Supabase.

This specification is the canonical build-spec surface for that workflow.