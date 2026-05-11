# TCC Relay Exploratory Compare Concept Adoption Memo

Date: 2026-05-03
Status: Active feature-intake memo
Scope: Classify the externally-authored relay comparison POC as an exploratory concept and decide what the TCC relay lane should carry now, defer, or reject for the current governed browser widening phase

## Purpose

An external HTML POC was created on a short timeline for immediate operational use:

1. `C:\Users\jjswe\Box\BANNER_Settings Print_Y1202A_Y1202C\protection_explorer.html`

This memo does not treat that file as an implementation candidate.

This memo treats it as an exploratory concept surface that may contain feature ideas worth admitting into the governed TCC relay lane.

The goal is to preserve useful product direction without importing rushed construction, browser-side evaluator logic, or site-specific shortcuts into the governed platform.

## Governing Inputs

This memo is grounded in:

1. `TCC-RELAY-GOVERNANCE-INDEX-2026-05-03.md`
2. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md`
3. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md`
4. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-operations-web-promoted-host-redeploy-blocker-handoff.md`
5. `TCC-RELAY-SCHEMA-TO-UI-READ-ONLY-IMPLEMENTATION-PLAN-2026-05-03.md`
6. the externally-authored exploratory file `C:\Users\jjswe\Box\BANNER_Settings Print_Y1202A_Y1202C\protection_explorer.html`

## Framing Decision

The correct posture is:

1. do not treat the POC as a code import candidate,
2. do treat the POC as evidence that the relay lane would benefit from a compare-oriented browser surface beyond a single-device workflow,
3. keep current implementation bounded to the Phase 2 read-only compare contract,
4. reserve broader simulation, instructional, and site-specific workflow layers for later phases unless explicitly reopened.

## What The POC Validates

The exploratory concept validates the following product direction:

1. users want relay comparison, not only single-device inspection,
2. users benefit from element-level comparison in addition to TCC comparison,
3. provenance, unsupported-state, and warning disclosure should stay adjacent to the visualization,
4. operator and tester interpretation guidance has product value when clearly separated from sourced runtime truth,
5. a compare workspace can become a meaningful expansion of the existing TCC breaker-style UI rather than a separate product family.

## Carry Now

These concepts fit the current Phase 2 browser widening lane and should be treated as admissible now, if implemented through governed data and bounded browser surfaces.

### 1. Explicit two-sided compare

Carry forward:

1. a left selection and right selection model,
2. compare limited to at most two explicitly selected relay TD-sections at one time,
3. no silent defaulting to a current relay when multiple candidates exist.

Why:

1. this aligns directly to the Phase 2 bounded compare contract,
2. it expands the current single-device workflow without reopening writes or optimizer behavior.

### 2. Provenance-first readouts

Carry forward:

1. source-faithful identity readouts,
2. visible family and storage-kind disclosure,
3. explicit unsupported and partial-support warnings,
4. per-side disclosure rather than merged or simplified summaries.

Why:

1. the relay lane already treats source identity as a protected contract,
2. compare becomes misleading quickly if identity or support state is flattened.

### 3. Read-only comparison views beyond a single chart

Carry forward:

1. context comparison,
2. settings comparison,
3. preview comparison,
4. bounded TCC overlay comparison where the data already exists through the governed API and shared calc surfaces.

Why:

1. the POC usefully shows that “compare” is broader than a single curve image,
2. Phase 2 already authorizes richer read-only browse and compare behavior inside the browser lane.

### 4. Warning-rich UI patterns

Carry forward:

1. visible disabled-state banners,
2. alarm-only or non-functional state disclosure,
3. “illustrative” or “not supported” badges only when backed by governed status semantics,
4. inline disclosure instead of burying caveats in documentation.

Why:

1. relay users need to know when a compared surface is real, unsupported, or intentionally bounded,
2. this is one of the strongest product behaviors in the exploratory concept.

## Defer Later

These concepts are useful but should not be pulled into the current Phase 2 slice.

### 1. Element-class exploration beyond bounded compare

Defer:

1. dedicated voltage, frequency, differential, LoE, directional, and composite-logic training tabs,
2. cross-element engineering workspaces that behave like a study companion rather than a compare surface.

Why:

1. they widen the browser surface well beyond the currently approved compare slice,
2. they deserve a separate later phase once read-only compare proves value.

### 2. Tester and commissioning guidance layers

Defer:

1. tester tips,
2. scenario instruction blocks,
3. procedural injection guidance,
4. approval-oriented narrative framing.

Why:

1. these may be product-value features later,
2. they are not required to prove the current read-only compare lane,
3. mixing sourced runtime truth with training guidance too early increases confusion risk.

### 3. Site-specific narrative packages

Defer:

1. one-off customer topology explanations,
2. project-specific owner notes,
3. immediate-use workbook companion framing,
4. operational risk notes tied to a single site or lineup.

Why:

1. the APEX relay lane should remain platform-shaped first,
2. site-specific overlays can be layered later if the product model proves out.

## Reject For Current Lane

These should not be admitted into the current governed lane as-is.

### 1. Browser-side relay evaluator logic

Reject:

1. analytical substitution in the browser,
2. family evaluators implemented in browser code,
3. placeholder curve models that produce computed operating behavior outside the governed shared calc and API boundary.

Why:

1. the current lane explicitly blocks browser-side relay math,
2. this would break the runtime boundary already fixed by earlier packets.

### 2. Placeholder or illustrative behavior presented as runtime truth

Reject:

1. placeholder models used for operator-facing decision surfaces,
2. illustrative geometry presented as if it were sourced relay behavior,
3. any compare result that is not grounded in governed data and admitted backend behavior.

Why:

1. the exploratory concept could tolerate immediate-use shortcuts,
2. the governed lane cannot.

### 3. Identity collapse and template substitution that hides the selected source

Reject:

1. collapsing multiple compared devices into one hidden template when the UI still presents them as distinct,
2. silently choosing defaults that bypass explicit left and right selection,
3. any compare posture that merges or ranks instead of preserving each side independently.

Why:

1. this conflicts with the source-faithful compare contract,
2. it makes compare easier to build but less truthful to use.

## Hardening Rules For Adoption

If concepts from the exploratory POC enter the lane, they must be hardened under these rules:

1. every compared side must preserve its own source identity,
2. every selection must be explicit when more than one candidate exists,
3. every compare output must be read-only and sourced from governed relay surfaces,
4. warnings and unsupported-state disclosures must be first-class UI elements,
5. no merged recommendation, optimization, or auto-selection layer may be introduced,
6. site-specific copy must remain outside the bounded Phase 2 implementation unless separately authorized.

## Recommended Next Implementation Slice

Use the exploratory concept as product guidance for the current Phase 2 work, but keep the implementation slice narrow.

Do next:

1. add explicit two-sided TD-section selection to the existing relay explorer,
2. add bounded compare views for read-only context, settings, and preview,
3. surface source identity, family, storage kind, and unsupported-state on both sides,
4. keep the compare surface inside the approved `apps/operations-web` files,
5. leave training tabs, browser-side evaluators, and site-specific explainer surfaces out of the first adoption slice.

## Bottom Line

The exploratory HTML file is useful as a concept surface.

Its product thesis should be admitted.

Its rushed implementation shortcuts should not.

The correct governed interpretation is:

1. carry forward the compare-oriented UX direction,
2. implement only the bounded read-only compare parts now,
3. defer training and broader engineering workspaces,
4. reject browser-side analytical substitution and hidden identity collapse.