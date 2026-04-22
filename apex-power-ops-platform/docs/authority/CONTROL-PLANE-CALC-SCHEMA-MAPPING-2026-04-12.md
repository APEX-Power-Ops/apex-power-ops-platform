# Control Plane And Calc Schema Mapping

This document maps the current bounded control-plane and calc tables into the future platform entity model.

Use this document for the current consolidation phase only.

Interpretation rules:
- current table names are transitional implementation assets, not canonical future names
- the target entities below describe ownership and meaning, not final SQL naming
- split tables only when they represent distinct lifecycle domains

## Mapping Goals

This pass is intentionally narrow.

Included:
- control-plane task routing and local execution surfaces
- validation and evidence tracking surfaces
- image-linking surfaces already consumed by the governed runtime
- ETU and TMT calc catalog surfaces used by the extracted calc package

Deferred:
- broader work-package orchestration redesign
- forms and workflow-generation entities
- full study-content normalization beyond the currently referenced runtime tables
- historical import and archive utility tables

## Control-Plane Surface

### Task Routing And Review

Current tables:
- `mcp_task_packets`
- `mcp_review_decisions`

Future target entities:
- `WorkPacket`
- `ReviewDecision`
- `ExecutionRoutePolicy`

Mapping intent:
- `mcp_task_packets` becomes the transient implementation backing for `WorkPacket`, which should own task identity, lane, risk, current status, preferred execution path, and packet payload provenance
- `mcp_review_decisions` becomes `ReviewDecision`, separated from packet state so approvals, rejection reasons, and closeout decisions remain append-only review events
- route metadata currently embedded in packet JSON should eventually become first-class `ExecutionRoutePolicy` fields rather than opaque packet payload content

Boundary note:
- packet storage should remain operational control-plane data, not product-domain content data

### Local Execution Queue And Runs

Current tables:
- `mcp_local_action_queue`
- `mcp_job_runs`

Future target entities:
- `LocalActionRequest`
- `ExecutionRun`
- `ExecutionArtifactRef`

Mapping intent:
- `mcp_local_action_queue` becomes `LocalActionRequest`, representing an approved action request against a governed local subject
- `mcp_job_runs` becomes `ExecutionRun`, representing claim, start, completion, summary, and result JSON for a concrete worker execution attempt
- evidence paths currently attached to run payloads should normalize into `ExecutionArtifactRef` references once evidence becomes queryable independently of the run record

Boundary note:
- queue identity and run history should be separate even if both remain in the control-plane schema area

### Validation Evidence

Current tables:
- `mcp_validation_artifacts`

Future target entities:
- `ValidationArtifact`
- `ValidationSubjectLink`

Mapping intent:
- `mcp_validation_artifacts` becomes `ValidationArtifact`, storing artifact type, human summary, structured payload, origin runner, and durable path or URI
- subject binding should move toward a generic `ValidationSubjectLink` pattern so guides, assets, packets, and future forms can all share one evidence model

### Governed Content-Adjacent Assets

Current tables:
- `image_assets`
- `image_guide_links`
- `study_content`

Future target entities:
- `KnowledgeAsset`
- `KnowledgeAssetUsage`
- `KnowledgeContentItem`

Mapping intent:
- `image_assets` becomes a subtype or bounded specialization of `KnowledgeAsset` for governed visual assets
- `image_guide_links` becomes `KnowledgeAssetUsage`, linking an asset to a specific content item, file, line, and section context
- `study_content` becomes `KnowledgeContentItem`, the future canonical representation for governed guide or study content records consumed by the platform

Boundary note:
- this pass does not rename the broader study-content domain; it only records how the currently referenced runtime tables should land

## Calc Surface

### ETU Catalog Backbone

Current tables:
- `tcc_etu_sensors`
- `tcc_etu_plugs`

Future target entities:
- `BreakerTripUnitVariant`
- `BreakerTripUnitRatingOption`

Mapping intent:
- `tcc_etu_sensors` becomes `BreakerTripUnitVariant`, owning the canonical ETU variant at a style-and-rating level, including element availability, calc-method selection, and tolerances
- `tcc_etu_plugs` becomes `BreakerTripUnitRatingOption`, representing compatible plug or rating options tied to a trip-unit style or variant context

Boundary note:
- trip-style, breaker-style, and manufacturer master data are upstream dependencies and should not remain duplicated inside the calc package boundary

### ETU Indexed Parameters And Delay Configuration

Current tables:
- `tcc_etu_sensor_params`
- `tcc_etu_ltd_params`

Future target entities:
- `TripUnitParameterSet`
- `TripUnitDelayCurveDefinition`

Mapping intent:
- `tcc_etu_sensor_params` becomes `TripUnitParameterSet`, storing indexed coefficient values by section, index, and optional curve grouping
- `tcc_etu_ltd_params` becomes `TripUnitDelayCurveDefinition`, owning LTD curve labels, methods, delay priorities, tolerances, and selection semantics

Boundary note:
- indexed numeric parameters are catalog data and should stay independent from runtime test execution records

### ETU Equation And Curve Tables

Current tables:
- `tcc_etu_std_equations`
- `tcc_etu_gfd_equations`
- `tcc_etu_inst_curves`

Future target entities:
- `TripUnitEquationSet`
- `TripUnitDiscreteCurve`

Mapping intent:
- `tcc_etu_std_equations` and `tcc_etu_gfd_equations` become typed `TripUnitEquationSet` records, distinguished by protection element and open or clear variant semantics
- `tcc_etu_inst_curves` becomes `TripUnitDiscreteCurve`, used where the platform stores actual point series rather than parametric coefficients

Boundary note:
- equation sets and discrete curves should share a common variant identity but remain physically separate because query patterns and row shapes differ

### ETU Band And Override Tables

Current tables:
- `tcc_etu_ltd_bands`
- `tcc_etu_std_bands`
- `tcc_etu_gfd_bands`
- `tcc_etu_stpu_overrides`
- `tcc_etu_sensor_maint`

Future target entities:
- `TripUnitBandDefinition`
- `TripUnitOverrideRule`
- `TripUnitMaintenanceProfile`

Mapping intent:
- the three `*_bands` tables become `TripUnitBandDefinition`, distinguished by element family and timing role
- `tcc_etu_stpu_overrides` becomes `TripUnitOverrideRule`, reserved for manufacturer-specific exceptions that should override ordinary calc selection
- `tcc_etu_sensor_maint` becomes `TripUnitMaintenanceProfile`, representing persisted MAINT-mode behavior and support-level metadata

### TMT Catalog And Curve Tables

Current tables:
- `tcc_tmt_frames`
- `tcc_tmt_amps`
- `tcc_tmt_curves`
- `tcc_tmt_settings`
- `tcc_tmt_thermal_adj`

Future target entities:
- `ThermalMagneticFrameVariant`
- `ThermalMagneticRatingOption`
- `ThermalMagneticCurvePoint`
- `ThermalMagneticSettingOption`
- `ThermalMagneticAdjustmentProfile`

Mapping intent:
- `tcc_tmt_frames` becomes `ThermalMagneticFrameVariant`, the anchor for frame size, breaker class, and style binding
- `tcc_tmt_amps` becomes `ThermalMagneticRatingOption`, representing available trip ratings for a frame variant
- `tcc_tmt_curves` becomes `ThermalMagneticCurvePoint`, a large point-series catalog that should remain optimized for frame-plus-class retrieval
- `tcc_tmt_settings` becomes `ThermalMagneticSettingOption`, representing adjustable values and tolerance ranges exposed by the runtime
- `tcc_tmt_thermal_adj` becomes `ThermalMagneticAdjustmentProfile`, storing adjustment multipliers that modify thermal behavior

Boundary note:
- `tcc_tmt_curves` is a high-volume catalog table and should stay isolated from operational control-plane tables even if both remain under one platform data estate

## Recommended Future Schema Areas

Suggested future ownership split for this bounded area:
- `apex_control`: `WorkPacket`, `ReviewDecision`, `LocalActionRequest`, `ExecutionRun`, `ValidationArtifact`
- `apex_knowledge`: `KnowledgeContentItem`, `KnowledgeAsset`, `KnowledgeAssetUsage`
- `apex_calc_catalog`: ETU and TMT catalog entities, equation sets, bands, settings, and adjustment profiles

This is an ownership recommendation, not a mandate on final physical schema names.

## Immediate Implementation Implications

Short-term decisions that follow from this mapping:
- keep the control-plane API focused on operational tables and validation surfaces, not broader domain authority
- keep `packages/calc-engine` consuming ETU and TMT catalog data as a read-oriented dependency slice
- avoid embedding future entity meaning into legacy `tcc_*` table names; treat those names as transitional storage only
- when broader platform schema work begins, migrate by bounded entity groups rather than by repository provenance