"""
Pydantic schemas for the NETA ETT Testing endpoints.

Matches the PostgreSQL views and functions applied via Supabase migrations:
  - vw_trip_unit_cascade
  - vw_sensor_calc_context
  - fn_sensor_available_settings(p_sensor_id)
  - fn_calculate_test_currents(p_sensor_id, p_plug_rating, ...)
  - fn_evaluate_test_results(p_sensor_id, ...)
"""

import warnings as _warnings
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


# ──────────────────────────────────────────────
# Cascade Selection
# ──────────────────────────────────────────────

class CascadeQuery(BaseModel):
    """Query parameters for cascade drill-down filtering."""
    manufacturer_id: Optional[int] = Field(None, description="Filter by manufacturer")
    trip_type_id: Optional[int] = Field(None, description="Filter by trip type")
    trip_style_id: Optional[int] = Field(None, description="Filter by trip style")
    sensor_id: Optional[int] = Field(None, description="Filter to specific sensor")


class CascadeManufacturer(BaseModel):
    manufacturer_id: int
    manufacturer_ids: Optional[list[int]] = None
    manufacturer_name: str
    manufacturer_display: Optional[str] = None
    trip_type_count: int


class CascadeTripType(BaseModel):
    trip_type_id: int
    trip_type_ids: Optional[list[int]] = None
    style_ids: Optional[list[int]] = None
    trip_type_name: str
    trip_model_display: Optional[str] = None
    manufacturer_id: int
    manufacturer_ids: Optional[list[int]] = None
    manufacturer_name: str
    trip_style_count: int
    dedupe_divergence_count: int = 0


class CascadeTripStyle(BaseModel):
    trip_style_id: int
    style_ids: Optional[list[int]] = None
    trip_style_name: str
    trip_model_display: Optional[str] = None
    # Protection-element class (L/S/I/G, e.g. "LSIG") — the Trip Style axis after
    # the step-2 restructure (Type=model, Style=protection class). Derived from the
    # style's sensors' has_* flags; never null in practice ('L' is always present).
    protection_class: Optional[str] = None
    trip_type_id: int
    trip_type_ids: Optional[list[int]] = None
    trip_type_name: str
    manufacturer_id: int
    manufacturer_ids: Optional[list[int]] = None
    manufacturer_name: str
    sensor_count: int
    dedupe_divergence_count: int = 0


class CascadeSensor(BaseModel):
    sensor_id: int
    sensor_rating: Optional[int] = None
    sensor_desc: str
    trip_style_id: int
    trip_style_name: str
    trip_model_display: Optional[str] = None
    trip_type_id: int
    trip_type_name: str
    manufacturer_id: int
    manufacturer_name: str
    has_ltpu: bool
    has_stpu: bool
    has_inst: bool
    has_gfpu: bool


class CascadePlugOption(BaseModel):
    plug_value: float
    sensor_count: int


class CascadeResponse(BaseModel):
    """Response for cascade drill-down at any level."""
    level: str = Field(
        ...,
        description="Current cascade level: manufacturers, trip_types, trip_styles, or sensors"
    )
    count: int
    manufacturers: Optional[list[CascadeManufacturer]] = None
    trip_types: Optional[list[CascadeTripType]] = None
    trip_styles: Optional[list[CascadeTripStyle]] = None
    sensors: Optional[list[CascadeSensor]] = None
    plug_values: list[CascadePlugOption] = Field(default_factory=list)


class EtuSearchResult(BaseModel):
    sensor_id: int
    sensor_rating: Optional[int] = None
    sensor_desc: str
    trip_style_id: int
    trip_style_name: str
    trip_type_id: int
    trip_type_name: str
    manufacturer_id: int
    manufacturer_name: str
    compatible_plug_values: list[float] = Field(default_factory=list)


class EtuSearchResponse(BaseModel):
    count: int
    results: list[EtuSearchResult] = Field(default_factory=list)


class EtuBreakerManufacturer(BaseModel):
    manufacturer_id: int
    manufacturer_ids: Optional[list[int]] = None
    manufacturer_name: str
    manufacturer_display: Optional[str] = None
    breaker_count: int


class EtuBreakerClassOption(BaseModel):
    breaker_class: str
    breaker_count: int


class EtuBreakerOption(BaseModel):
    breaker_id: int
    breaker_ids: Optional[list[int]] = None
    style_ids: Optional[list[int]] = None
    breaker_name: str
    breaker_class: str
    manufacturer_id: int
    manufacturer_ids: Optional[list[int]] = None
    manufacturer_name: str
    style_count: int
    dedupe_divergence_count: int = 0


class EtuBreakerStyleOption(BaseModel):
    breaker_style_id: int
    style_ids: Optional[list[int]] = None
    breaker_style_name: str
    breaker_model_display: Optional[str] = None
    breaker_id: int
    breaker_ids: Optional[list[int]] = None
    breaker_name: str
    breaker_class: str
    manufacturer_id: int
    manufacturer_ids: Optional[list[int]] = None
    manufacturer_name: str
    dedupe_divergence_count: int = 0


class EtuBreakerCascadeResponse(BaseModel):
    level: str
    count: int
    scope: dict[str, Any] = Field(default_factory=dict)
    manufacturers: list[EtuBreakerManufacturer] = Field(default_factory=list)
    breaker_classes: list[EtuBreakerClassOption] = Field(default_factory=list)
    breakers: list[EtuBreakerOption] = Field(default_factory=list)
    breaker_styles: list[EtuBreakerStyleOption] = Field(default_factory=list)


class EtuBridgeSensor(BaseModel):
    """One compatible ETU sensor for a breaker style, via the recovered SST bridge.

    Backed by tcc.vw_breaker_sst_bridge (migration 006). The tmt_sst_* triple is the
    bridged trip-unit identity (manufacturer / type / style); the sensor_* fields are
    the compatible sensor narrowed by that bridge.
    """
    breaker_class: str
    breaker_id: int
    breaker_style_id: int
    breaker_style_frame: Optional[str] = None
    breaker_model_display: Optional[str] = None
    tmt_sst_mfr: Optional[str] = None
    tmt_sst_type: Optional[str] = None
    tmt_sst_style: Optional[str] = None
    # SC3 display-parity fields (task #129): the same COALESCE chain the cascade
    # serves (mfr_aliases / trip_style_aliases pick / trip_model_aliases), so the
    # breaker-axis dropdown shows the normalized trip identity the trip axis shows.
    tmt_sst_mfr_display: Optional[str] = None
    tmt_sst_model_display: Optional[str] = None
    trip_style_id: int
    sensor_id: int
    sensor_rating: Optional[int] = None
    sensor_description: Optional[str] = None


class EtuBridgeSensorsResponse(BaseModel):
    """Breaker-style -> compatible ETU sensor set (SST bridge narrowing).

    bridge_match_status == 'unmatched' (empty sensors) means the caller should fall
    back to the manufacturer axis (/etu/breaker-cascade) or free-text (/etu/search):
    the style either does not use the SST bridge or its bridged target is not in catalog.
    """
    breaker_style_id: Optional[int] = None
    breaker_style_ids: Optional[list[int]] = None
    breaker_id: Optional[int] = None
    bridge_match_status: str = "unmatched"
    count: int = 0
    sensors: list[EtuBridgeSensor] = Field(default_factory=list)
    # Interim SST-bridge mismatch flag (the §104 re-carry scramble, under repair):
    # set when the frame nameplate rating is clearly inconsistent with the bridged
    # sensor ratings, so the page can warn the tech before they test a wrong sensor.
    rating_warning: Optional[str] = None
    # The breaker-style continuous rating (Access r_cont_current, migration 011) used
    # to rating-narrow the bridged sensor set (#75). Set for a single-style query.
    breaker_rating: Optional[float] = None
    # True when the sensor set was narrowed to the sensor(s) matching breaker_rating
    # (an exact match existed); False = full style set served (no exact match / no rating).
    rating_narrowed: bool = False


class EtuBreakerAltTrip(BaseModel):
    """An alternative (retrofit/upgrade) trip unit compatible with a breaker, BEYOND its
    as-shipped trip — sourced from tcc.breaker_alt_trip_bridge (migration 017).

    protection_class is the protection-element complement derived from the trip's modelled
    elements: 'L' is always present, plus 'S' (short-time), 'I' (instantaneous) and 'G'
    (ground-fault) when present — e.g. 'LSIG', 'LIG', 'LI'. It disambiguates trip variants
    that share a display name (the GE EntelliGuard TU 'WavePro' vs 'Wavepro LI' both
    display as 'Entelliguard' but differ by element complement).
    """
    trip_style_id: int
    relation: str
    protection_class: Optional[str] = None


class EtuBreakerAltTripsResponse(BaseModel):
    """The alternative-trip set for a breaker (the alt-trip bridge), so the picker can tag a
    trip as a retrofit/upgrade and show its protection class without re-querying the main
    SST bridge. Empty alt_trips = the breaker carries only its native (as-shipped) trip."""
    breaker_id: Optional[int] = None
    breaker_style_id: Optional[int] = None
    count: int = 0
    alt_trips: list[EtuBreakerAltTrip] = Field(default_factory=list)


class ResolvedBreakerContext(BaseModel):
    label: Optional[str] = None
    source: Optional[str] = None
    manufacturer_name: Optional[str] = None
    breaker_class: Optional[str] = None
    breaker_name: Optional[str] = None
    breaker_style_name: Optional[str] = None
    type_name: Optional[str] = None
    style_name: Optional[str] = None
    tcc_number: Optional[str] = None


class ResolvedTripUnitIdentity(BaseModel):
    manufacturer_name: Optional[str] = None
    trip_type_name: Optional[str] = None
    trip_style_name: Optional[str] = None
    label: Optional[str] = None


class ResolvedRatingContext(BaseModel):
    label: Optional[str] = None
    sensor_id: Optional[int] = None
    sensor_desc: Optional[str] = None
    sensor_rating: Optional[float] = None
    frame_id: Optional[int] = None
    frame_size: Optional[str] = None
    frame_desc: Optional[str] = None
    amp_ratings: list[float] = Field(default_factory=list)
    section_id: Optional[int] = None
    section_name: Optional[str] = None


class ResolvedEquipmentSummary(BaseModel):
    family: str
    family_label: Optional[str] = None
    resolved_id: Optional[str] = None
    primary_label: Optional[str] = None
    secondary_label: Optional[str] = None
    breaker_context: Optional[ResolvedBreakerContext] = None
    trip_unit: Optional[ResolvedTripUnitIdentity] = None
    rating_context: Optional[ResolvedRatingContext] = None


# ──────────────────────────────────────────────
# Sensor Calculation Context
# ──────────────────────────────────────────────

class SensorCalcContext(BaseModel):
    """Complete calculation context for a single sensor — from vw_sensor_calc_context.

    The view returns ~65 columns; we capture the ones the NETA workflow needs
    and ignore the rest via extra='ignore'.  has_* booleans are injected by the
    router (derived from *_calc != -1) since they are not native view columns.
    """
    model_config = ConfigDict(extra="ignore")

    sensor_id: int
    sensor_desc: str
    trip_style_id: int
    trip_style_name: str
    trip_type_name: str
    manufacturer_name: str
    rating: Optional[float] = None
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None

    # Element availability — injected by the router from *_calc != -1
    has_ltpu: bool = False
    has_stpu: bool = False
    has_inst: bool = False
    has_gfpu: bool = False

    # SSTCalcMethod enum per element (-1 = absent, 0-10 = method)
    ltpu_calc: Optional[int] = None
    stpu_calc: Optional[int] = None
    inst_calc: Optional[int] = None
    gfpu_calc: Optional[int] = None

    # Tolerances (asymmetric, per-sensor)
    ltpu_tol_hi: Optional[float] = None
    ltpu_tol_lo: Optional[float] = None
    stpu_tol_hi: Optional[float] = None
    stpu_tol_lo: Optional[float] = None
    inst_ovrtol_min: Optional[float] = None
    inst_ovrtol_max: Optional[float] = None
    gfpu_tol_hi: Optional[float] = None
    gfpu_tol_lo: Optional[float] = None

    # Step sizes for slider/input validation
    ltpu_step: Optional[float] = None
    stpu_step: Optional[float] = None
    inst_step: Optional[float] = None
    gfpu_step: Optional[float] = None

    # Delay curve routing (SSTDelayCalc enum). Canonical names match the view
    # (renamed from legacy *_i2t at Phase 5 Tier A); the *_i2t aliases stay
    # populated for backward compatibility via the validator below.
    stpu_delay_calc_code: Optional[int] = None
    ground_delay_calc_code: Optional[int] = None
    stpu_i2t: Optional[int] = None
    gfpu_i2t: Optional[int] = None

    # LTD context
    ltd_func: Optional[int] = None
    ltd_setting_method: Optional[int] = None
    ltd_tol_hi: Optional[float] = None
    ltd_tol_lo: Optional[float] = None

    # Maintenance mode context (from LEFT JOIN to tcc.etu_sensor_maint)
    maint_available: bool = False          # runtime toggle (original Access DB value)
    maint_capable: bool = False            # derived: True when MAINT config data exists
    maint_ltpu_reduction: Optional[float] = None
    maint_stpu_reduction: Optional[float] = None
    maint_inst_calc: Optional[int] = None
    maint_inst_tol_hi: Optional[float] = None
    maint_inst_tol_lo: Optional[float] = None
    maint_gfpu_calc: Optional[int] = None
    maint_gfpu_tol_hi: Optional[float] = None
    maint_gfpu_tol_lo: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def _backfill_legacy_delay_route_aliases(cls, values):
        """Keep the legacy *_i2t aliases populated from the canonical view columns.

        The view emits stpu_delay_calc_code / ground_delay_calc_code (renamed from
        legacy stpu_i2t / gfpu_i2t at Phase 5 Tier A). Older clients still read the
        *_i2t names, so mirror the canonical value into them when absent.
        """
        if isinstance(values, dict):
            if values.get("stpu_i2t") is None and values.get("stpu_delay_calc_code") is not None:
                values["stpu_i2t"] = values["stpu_delay_calc_code"]
            if values.get("gfpu_i2t") is None and values.get("ground_delay_calc_code") is not None:
                values["gfpu_i2t"] = values["ground_delay_calc_code"]
        return values


# ──────────────────────────────────────────────
# Available Settings
# ──────────────────────────────────────────────

class SettingOption(BaseModel):
    """A single available setting value (e.g., 0.5, 0.6, 0.7 for LTPU multiplier)."""
    value: float
    label: Optional[str] = None


class DelayBandOption(BaseModel):
    """A single ETU delay band option surfaced exactly from persisted band tables."""
    band: str = Field(..., description="Band identifier (e.g., 'I-Min CB', 'I-C-2')")
    label: str = Field(..., description="Display label (e.g., 'Min CB', 'C-2')")
    open_time: float = Field(..., description="Opening time in seconds")
    clear_time: Optional[float] = Field(None, description="Clearing time in seconds when stored")
    is_default: bool = Field(False, description="True when the source row is marked as default")


class LtdMultiplierOption(BaseModel):
    """An LTD multiplier from tcc.etu_ltpu_multipliers."""
    value: float
    label: Optional[str] = None


class AvailableSettingsResponse(BaseModel):
    """Available dropdown/slider values for each protection element — from fn_sensor_available_settings."""
    sensor_id: int
    plug_values: list[float] = Field(default_factory=list, description="Available plug ratings")
    ltpu_settings: list[float] = Field(default_factory=list, description="LTPU multiplier options")
    ltd_settings: list[DelayBandOption] = Field(default_factory=list, description="LTD delay band options")
    std_settings: list[DelayBandOption] = Field(default_factory=list, description="STD delay band options")
    gfd_settings: list[DelayBandOption] = Field(default_factory=list, description="GFD delay band options")
    ltd_multipliers: list[Any] = Field(default_factory=list, description="LTD multiplier options")
    stpu_settings: list[float] = Field(default_factory=list, description="STPU multiplier options")
    inst_settings: list[float] = Field(default_factory=list, description="INST pickup options")
    gfpu_settings: list[float] = Field(default_factory=list, description="GFPU multiplier options")
    units: dict[str, str] = Field(
        default_factory=dict,
        description="Display unit per pickup element (ltpu/stpu/inst/gfpu): 'A' | 'x Ir' | 'x In' | 'x Isd'",
    )
    validated_source: Optional[str] = Field(
        None,
        description="Citation when settings come from the validated vendor-doc catalog (envelope-only sensors)",
    )
    terminology: Optional[dict] = Field(
        None,
        description=(
            "SC3 field-facing vocabulary for this sensor's trip lineage (task #129; "
            "tcc.field_terminology): per-element labels + faceplate dial symbols, "
            "trust badges (MFR/VERIFY/N/A), method labels, honesty notes. Absent = "
            "fail-open; the UI keeps its built-in labels."
        ),
    )


class ApparatusStudyResource(BaseModel):
    resource_id: UUID
    title: str
    resource_type: str
    source_table: str
    level: Optional[str] = None
    description: Optional[str] = None
    url_slug: Optional[str] = None
    estimated_minutes: Optional[int] = None


class ApparatusStudyResourcesResponse(BaseModel):
    apparatus_id: UUID
    count: int
    resources: list[ApparatusStudyResource] = Field(default_factory=list)


# ──────────────────────────────────────────────
# TMT Contract Lift
# ──────────────────────────────────────────────

class TMTAmpOption(BaseModel):
    rating: float
    max_override: Optional[float] = None


class TMTSettingOption(BaseModel):
    value: Optional[float] = None
    label: Optional[str] = None
    tol_lo: Optional[float] = None
    tol_hi: Optional[float] = None


class TMTFrameContext(BaseModel):
    frame_id: int
    breaker_style_id: int
    breaker_class: Optional[str] = None
    frame_size: Optional[str] = None
    manufacturer_name: Optional[str] = None
    breaker_name: Optional[str] = None
    breaker_style_name: Optional[str] = None
    breaker_model_display: Optional[str] = None
    standard: Optional[float] = None
    available_trip_classes: list[int] = Field(default_factory=list)
    amp_rating_count: int = 0
    setting_count: int = 0
    thermal_adjustment_count: int = 0
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None


class TMTFrameSearchResult(BaseModel):
    frame_id: int
    frame_ids: Optional[list[int]] = None
    breaker_style_id: int
    style_ids: Optional[list[int]] = None
    breaker_class: Optional[str] = None
    frame_size: Optional[str] = None
    manufacturer_name: Optional[str] = None
    breaker_name: Optional[str] = None
    breaker_style_name: Optional[str] = None
    breaker_model_display: Optional[str] = None
    standard: Optional[float] = None
    matched_amp_rating: Optional[float] = None
    dedupe_divergence_count: int = 0


class TMTFrameSearchResponse(BaseModel):
    count: int
    frames: list[TMTFrameSearchResult] = Field(default_factory=list)
    dedupe_divergence_count: int = 0


class TMTFacet(BaseModel):
    name: str
    values: list[int | float | str] = Field(default_factory=list)
    cardinality: int = 0


class TMTFacetsResponse(BaseModel):
    facets: list[TMTFacet] = Field(default_factory=list)
    total_matching_frames: int = 0
    active_filters: dict[str, int | float | str | list[int]] = Field(default_factory=dict)


class TMTSettingsResponse(BaseModel):
    frame_id: int
    available_trip_classes: list[int] = Field(default_factory=list)
    amp_ratings: list[TMTAmpOption] = Field(default_factory=list)
    settings: list[TMTSettingOption] = Field(default_factory=list)
    thermal_adjustments: list[float] = Field(default_factory=list)


class TMTPlotRequest(BaseModel):
    frame_id: int = Field(..., description="TMT frame ID")
    trip_class: int = Field(..., description="TMT trip class / curve class")
    amp_rating: Optional[float] = Field(None, description="Optional selected amp rating")
    setting_value: Optional[float] = Field(None, description="Optional selected TMT setting")
    thermal_adjustment: Optional[float] = Field(None, description="Optional thermal adjustment factor")
    include_raw_points: bool = Field(False, description="Include the raw control points")
    num_output_points: Optional[int] = Field(
        None,
        description="Optional output density override for spline interpolation",
    )


class TMTPlotCurvePoint(BaseModel):
    amps: float
    seconds: float


class TMTPlotCurve(BaseModel):
    id: str
    curve_family: str = Field("TMT", description="Curve family identifier")
    trip_class: int
    line_style: str = Field("solid", description="Rendering hint")
    points: list[TMTPlotCurvePoint]


class TMTPlotMeta(BaseModel):
    frame_id: int
    breaker_style_id: int
    breaker_class: Optional[str] = None
    frame_size: Optional[str] = None
    manufacturer_name: Optional[str] = None
    breaker_name: Optional[str] = None
    breaker_style_name: Optional[str] = None
    breaker_model_display: Optional[str] = None
    standard: Optional[float] = None
    selected_trip_class: int
    selected_amp_rating: Optional[float] = None
    selected_max_override: Optional[float] = None
    selected_setting: Optional[float] = None
    selected_setting_label: Optional[str] = None
    selected_setting_tol_lo: Optional[float] = None
    selected_setting_tol_hi: Optional[float] = None
    selected_thermal_adjustment: Optional[float] = None
    selections_applied_to_curve: bool = False
    plot_disclaimer: Optional[str] = None
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None


class TMTPlotResponse(BaseModel):
    meta: TMTPlotMeta
    warnings: list[str] = Field(default_factory=list)
    curves: list[TMTPlotCurve] = Field(default_factory=list)
    raw_points: list[TMTPlotCurvePoint] = Field(default_factory=list)


# ──────────────────────────────────────────────
# EMT Contract Lift
# ──────────────────────────────────────────────

class EMTFrameSearchResult(BaseModel):
    emt_id: int
    frame_id: int
    manufacturer_id: Optional[int] = None
    manufacturer_name: Optional[str] = None
    type_name: Optional[str] = None
    style_name: Optional[str] = None
    tcc_number: Optional[str] = None
    trip_char: Optional[int] = None
    trip_plug: Optional[int] = None
    frame_size: Optional[float] = None
    frame_desc: Optional[str] = None
    amp_rating_count: int = 0
    section_count: int = 0


class EMTFrameSearchResponse(BaseModel):
    count: int
    frames: list[EMTFrameSearchResult] = Field(default_factory=list)


class EMTFacet(BaseModel):
    name: str
    values: list[int | float | str] = Field(default_factory=list)
    cardinality: int = 0


class EMTFacetsResponse(BaseModel):
    facets: list[EMTFacet] = Field(default_factory=list)
    total_matching_frames: int = 0
    active_filters: dict[str, int | float | str | list[int]] = Field(default_factory=dict)


class ManufacturerFacetOption(BaseModel):
    """A manufacturer option for a guided dropdown (TMT/EMT selectors)."""
    manufacturer_id: int
    manufacturer_ids: Optional[list[int]] = None
    manufacturer_name: Optional[str] = None
    manufacturer_display: Optional[str] = None
    frame_count: int = 0


class TMTManufacturersResponse(BaseModel):
    """TMT manufacturers available for a breaker class (drives the TMT selector dropdown)."""
    manufacturers: list[ManufacturerFacetOption] = Field(default_factory=list)


class EMTManufacturersResponse(BaseModel):
    """EMT manufacturers available (drives the EMT selector dropdown)."""
    manufacturers: list[ManufacturerFacetOption] = Field(default_factory=list)


class EMTSectionSummary(BaseModel):
    section_id: int
    name: Optional[str] = None
    sec_char: Optional[int] = None
    curve_type: Optional[int] = None
    pickup_calc: Optional[int] = None
    pickup_setting: Optional[int] = None
    step_size: Optional[float] = None
    current_calc: Optional[int] = None
    pickup_tol_lo: Optional[float] = None
    pickup_tol_hi: Optional[float] = None
    band_count: int = 0
    pickup_count: int = 0


class EMTFrameContext(BaseModel):
    emt_id: int
    frame_id: int
    manufacturer_id: Optional[int] = None
    manufacturer_name: Optional[str] = None
    type_name: Optional[str] = None
    style_name: Optional[str] = None
    tcc_number: Optional[str] = None
    trip_char: Optional[int] = None
    trip_plug: Optional[int] = None
    frame_size: Optional[float] = None
    frame_desc: Optional[str] = None
    amp_ratings: list[float] = Field(default_factory=list)
    sections: list[EMTSectionSummary] = Field(default_factory=list)
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None


class EMTPickupOption(BaseModel):
    setting: Optional[float] = None
    description: Optional[str] = None


class EMTBandOption(BaseModel):
    band_id: int
    band_name: Optional[str] = None
    ordinal: Optional[int] = None
    current_at: Optional[float] = None
    curve_point_count: int = 0
    curve_classes: list[int] = Field(default_factory=list)


class EMTSectionSettingsResponse(BaseModel):
    section_id: int
    name: Optional[str] = None
    sec_char: Optional[int] = None
    curve_type: Optional[int] = None
    pickup_calc: Optional[int] = None
    pickup_setting: Optional[int] = None
    step_size: Optional[float] = None
    current_calc: Optional[int] = None
    pickup_tol_lo: Optional[float] = None
    pickup_tol_hi: Optional[float] = None
    pickups: list[EMTPickupOption] = Field(default_factory=list)
    bands: list[EMTBandOption] = Field(default_factory=list)


class EMTPlotRequest(BaseModel):
    section_id: int = Field(..., description="EMT section ID")
    band_id: int = Field(..., description="EMT band ID from the section settings surface")
    curve_class: Optional[int] = Field(
        None,
        description="Optional EMT_Curves.Class filter. Omit to return all stored classes for the band.",
    )


class EMTPlotCurvePoint(BaseModel):
    amps: float
    seconds: float


class EMTPlotCurve(BaseModel):
    id: str
    curve_family: str = Field("EMT", description="Curve family identifier")
    band_id: int
    curve_class: Optional[int] = None
    class_label: Optional[str] = None
    line_style: str = Field("solid", description="Rendering hint")
    points: list[EMTPlotCurvePoint] = Field(default_factory=list)


class EMTPlotMeta(BaseModel):
    emt_id: int
    frame_id: int
    section_id: int
    band_id: int
    manufacturer_id: Optional[int] = None
    manufacturer_name: Optional[str] = None
    type_name: Optional[str] = None
    style_name: Optional[str] = None
    tcc_number: Optional[str] = None
    frame_size: Optional[float] = None
    frame_desc: Optional[str] = None
    section_name: Optional[str] = None
    sec_char: Optional[int] = None
    curve_type: Optional[int] = None
    pickup_calc: Optional[int] = None
    pickup_setting: Optional[int] = None
    current_calc: Optional[int] = None
    band_name: Optional[str] = None
    band_ordinal: Optional[int] = None
    current_at: Optional[float] = None
    available_curve_classes: list[int] = Field(default_factory=list)
    selected_curve_class: Optional[int] = None
    selections_applied_to_curve: bool = False
    plot_disclaimer: Optional[str] = None
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None


class EMTPlotResponse(BaseModel):
    meta: EMTPlotMeta
    warnings: list[str] = Field(default_factory=list)
    curves: list[EMTPlotCurve] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Relay Contract Lift
# ──────────────────────────────────────────────

class RelayLineSectionSummary(BaseModel):
    line_section_source_id: int
    section_number: int
    section_name: Optional[str] = None
    pickup: Optional[float] = None
    secondary_i_code: Optional[int] = None
    amps_calc_mode: Optional[int] = None
    use_toc_multiplier: bool = False


class RelayRangeDiscreteValue(BaseModel):
    value: Optional[float] = None
    description: Optional[str] = None


class RelayRangeOption(BaseModel):
    range_source_id: int
    source_parent_id: int
    parent_kind: str
    parent_label: Optional[str] = None
    aux_key: int
    ordinal: int
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step_value: Optional[float] = None
    relative_unit_code: int
    use_range: bool = False
    scales_with_time_multiplier: bool = False
    discrete_values: list[RelayRangeDiscreteValue] = Field(default_factory=list)


class RelayCurveParentOption(BaseModel):
    curve_parent_source_id: int
    storage_kind: str
    curve_name: Optional[str] = None
    curve_parent_ordinal: Optional[int] = None
    min_pickup: Optional[float] = None
    max_pickup: Optional[float] = None
    is_discrete: Optional[bool] = None
    step_size: Optional[float] = None
    horizontal_amps_code: Optional[int] = None
    preview_option_count: int = 0


class RelayPreviewOption(BaseModel):
    curve_parent_source_id: int
    storage_kind: str
    curve_name: Optional[str] = None
    curve_ordinal: Optional[int] = None
    source_ordinal: Optional[int] = None
    time_dial: Optional[float] = None
    td_desc: Optional[str] = None
    point_count: Optional[int] = None
    current_min: Optional[float] = None
    current_max: Optional[float] = None
    coefficients: dict[str, Optional[float]] = Field(default_factory=dict)


class RelayCandidateOverrides(BaseModel):
    pickup_multiplier: Optional[float] = Field(
        None,
        gt=0,
        description="Ephemeral pickup multiplier for read-only what-if evaluation",
    )
    time_dial: Optional[float] = Field(
        None,
        gt=0,
        description="Ephemeral analytical time-dial value for read-only what-if evaluation",
    )
    voltage_threshold_multiplier: Optional[float] = Field(
        None,
        gt=0,
        description="Ephemeral voltage-threshold multiplier for read-only what-if evaluation",
    )


class RelaySectionSearchResult(BaseModel):
    manufacturer_source_id: int
    relay_type: Optional[str] = None
    relay_device_source_id: int
    device_function: Optional[str] = None
    device_ordinal: int
    standard_code: Optional[int] = None
    dftype_code: Optional[int] = None
    voltage_restraint_kind: Optional[str] = None
    td_section_source_id: int
    td_section_name: Optional[str] = None
    family_code: int
    family_name: str
    storage_kind: str
    supported: bool = False


class RelaySectionSearchResponse(BaseModel):
    count: int
    sections: list[RelaySectionSearchResult] = Field(default_factory=list)


# ── Relay selection cascade (Chip 2): guided, no-free-text dropdowns ──
# Mirrors the breaker TMT/EMT manufacturer-cascade pattern for relays
# (Mfr → Type → Device Function → Standard / Curve family). GR §1.

class RelayManufacturerOption(BaseModel):
    """A manufacturer option for the relay selector's guided dropdown (cascade top)."""
    manufacturer_source_id: int
    manufacturer_name: Optional[str] = None
    relay_count: int = 0
    section_count: int = 0


class RelayManufacturersResponse(BaseModel):
    """Manufacturers available for the relay selector dropdown (GR §1 cascade step 1)."""
    manufacturers: list[RelayManufacturerOption] = Field(default_factory=list)


class RelayFacetOption(BaseModel):
    """A cross-filtered text cascade option (relay_type / device_function)."""
    value: str
    count: int = 0


class RelayStandardOption(BaseModel):
    """A standard facet option (ANSI / IEC / Both)."""
    standard_code: int
    label: str
    count: int = 0


class RelayFamilyOption(BaseModel):
    """A curve-family facet option (RelayTDSection.Model 0-9), trust-tagged."""
    family_code: int
    family_name: str
    storage_kind: str
    supported: bool = False
    count: int = 0


class RelayFacetsResponse(BaseModel):
    """Cross-filtered relay cascade options for the current partial selection (GR §1)."""
    relay_types: list[RelayFacetOption] = Field(default_factory=list)
    device_functions: list[RelayFacetOption] = Field(default_factory=list)
    standards: list[RelayStandardOption] = Field(default_factory=list)
    families: list[RelayFamilyOption] = Field(default_factory=list)
    total_matching_sections: int = 0
    active_filters: dict[str, int | str] = Field(default_factory=dict)


class RelayFacetToleranceModel(BaseModel):
    """One facet's acceptance band — percent window and/or an absolute floor (GR §7 / Chip 3)."""
    pct_low: Optional[float] = None
    pct_high: Optional[float] = None
    abs_low: Optional[float] = None
    abs_high: Optional[float] = None
    unit: str  # "A" (pickup) | "s" (timing)


class RelayToleranceResponse(BaseModel):
    """Per-relay field-test acceptance tolerance, tier-resolved + trust-tagged (Chip 3).

    Tier order: Enoserv [VENDOR-DOC] catalog (PRIMARY) -> Relays.Note OEM seed -> withheld
    (no NETA floor yet). ``found=false`` with ``trust='withheld'`` means no validated band — the
    field sheet must show the manufacturer datasheet is required, never a fabricated tolerance.
    """
    td_section_source_id: int
    manufacturer_source_id: Optional[int] = None
    manufacturer_name: Optional[str] = None
    relay_type: Optional[str] = None
    found: bool = False
    provenance: str = "none"      # "vendor-doc" | "note" | "none"
    trust: str = "withheld"       # "validated" | "withheld"
    match_kind: str = ""          # "exact" | "canonical" | "note" | ""
    source: str = ""
    pickup: Optional[RelayFacetToleranceModel] = None
    timing: Optional[RelayFacetToleranceModel] = None


class RelayContext(BaseModel):
    manufacturer_source_id: int
    relay_type: Optional[str] = None
    relay_device_source_id: int
    device_function: Optional[str] = None
    device_ordinal: int
    standard_code: Optional[int] = None
    dftype_code: Optional[int] = None
    voltage_restraint_kind: Optional[str] = None
    td_section_source_id: int
    td_section_name: Optional[str] = None
    family_code: int
    family_name: str
    storage_kind: str
    supported: bool = False
    unsupported_reason: Optional[str] = None
    line_section_count: int = 0
    range_count: int = 0
    curve_parent_count: int = 0
    preview_option_count: int = 0
    line_sections: list[RelayLineSectionSummary] = Field(default_factory=list)
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None


class RelaySettingsResponse(BaseModel):
    td_section_source_id: int
    family_code: int
    family_name: str
    storage_kind: str
    supported: bool = False
    unsupported_reason: Optional[str] = None
    line_sections: list[RelayLineSectionSummary] = Field(default_factory=list)
    ranges: list[RelayRangeOption] = Field(default_factory=list)
    curve_parents: list[RelayCurveParentOption] = Field(default_factory=list)
    preview_options: list[RelayPreviewOption] = Field(default_factory=list)


class RelayPlotRequest(BaseModel):
    td_section_source_id: int = Field(..., description="Relay TD-section source ID")
    curve_parent_source_id: Optional[int] = Field(
        None,
        description="Optional family parent source ID when multiple stored curve parents exist",
    )
    curve_ordinal: Optional[int] = Field(
        None,
        description="Optional analytical curve ordinal from the settings surface",
    )
    source_ordinal: Optional[int] = Field(
        None,
        description="Optional TCP source ordinal from the settings surface",
    )
    time_dial: Optional[float] = Field(
        None,
        description="Analytical time-dial multiplier or exact TCP stored time-dial selector",
    )
    current_multiples: list[float] = Field(
        default_factory=lambda: [2.0, 3.0, 5.0, 10.0, 20.0],
        description="Current multiples of pickup to evaluate or interpolate",
    )
    candidate_overrides: Optional[RelayCandidateOverrides] = Field(
        None,
        description="Ephemeral read-only candidate settings; never persisted",
    )


class RelayPlotCurvePoint(BaseModel):
    current_multiple: float
    seconds: float
    evaluated_current_multiple: Optional[float] = None


class RelayPlotCurve(BaseModel):
    id: str
    curve_family: str = Field("RELAY", description="Curve family identifier")
    family_name: str
    storage_kind: str
    curve_name: Optional[str] = None
    curve_parent_source_id: Optional[int] = None
    curve_ordinal: Optional[int] = None
    source_ordinal: Optional[int] = None
    time_dial: Optional[float] = None
    td_desc: Optional[str] = None
    line_style: str = Field("solid", description="Rendering hint")
    points: list[RelayPlotCurvePoint] = Field(default_factory=list)


class RelayPlotMeta(BaseModel):
    td_section_source_id: int
    relay_device_source_id: int
    manufacturer_source_id: int
    relay_type: Optional[str] = None
    device_function: Optional[str] = None
    td_section_name: Optional[str] = None
    family_code: int
    family_name: str
    storage_kind: str
    supported: bool = False
    status: str
    unsupported_reason: Optional[str] = None
    selected_curve_parent_source_id: Optional[int] = None
    selected_curve_name: Optional[str] = None
    selected_curve_ordinal: Optional[int] = None
    selected_source_ordinal: Optional[int] = None
    selected_time_dial: Optional[float] = None
    selected_td_desc: Optional[str] = None
    candidate_applied: bool = False
    candidate_pickup_multiplier: Optional[float] = None
    candidate_time_dial: Optional[float] = None
    candidate_voltage_threshold_multiplier: Optional[float] = None
    plot_disclaimer: Optional[str] = None
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None


class RelayPlotResponse(BaseModel):
    meta: RelayPlotMeta
    warnings: list[str] = Field(default_factory=list)
    curves: list[RelayPlotCurve] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Test Current Calculation
# ──────────────────────────────────────────────

class CalculateRequest(BaseModel):
    """Input for NETA test current calculation."""
    sensor_id: int = Field(..., description="Sensor ID from cascade selection")
    plug_rating: float = Field(..., description="Selected plug/rating value (Ir)")
    ltpu_setting: Optional[float] = Field(None, description="LTPU multiplier setting")
    ltd_setting: Optional[float] = Field(None, description="LTD delay band setting")
    stpu_setting: Optional[float] = Field(None, description="STPU multiplier setting")
    std_setting: Optional[float] = Field(None, description="STD delay setting")
    inst_setting: Optional[float] = Field(None, description="Instantaneous pickup setting")
    gfpu_setting: Optional[float] = Field(None, description="GFPU multiplier setting")
    gfd_setting: Optional[float] = Field(None, description="GFD delay setting")
    ltd_test_multiple: Optional[float] = Field(
        None,
        description=(
            "LTD delay-test current multiple (x LTPU pickup). Defaults to the NETA "
            "default (3x). 6x is the long-time band reference where the expected trip "
            "time equals the stored dial setting; LTD time scales by the I2t law "
            "t = setting * (6/N)^2."
        ),
    )
    std_test_multiple: Optional[float] = Field(
        None,
        description="STD delay-test current multiple (x STPU pickup). Defaults to NETA 1.5x.",
    )
    gfd_test_multiple: Optional[float] = Field(
        None,
        description="GFD delay-test current multiple (x GFPU pickup). Defaults to NETA 1.5x.",
    )
    multiplier_value: Optional[float] = Field(
        None,
        description="Optional ETU multiplier used by calc methods 2 and 3",
    )
    c_factor: Optional[float] = Field(
        None,
        description="Optional ETU C factor used by calc methods 5 and 6",
    )
    breaker_context_label: Optional[str] = Field(None, description="Optional bounded breaker-side identity label")
    breaker_context_source: Optional[str] = Field(None, description="Source of breaker_context_label")
    trip_unit_manufacturer_name: Optional[str] = Field(None, description="Optional trip-unit manufacturer label")
    trip_unit_type_name: Optional[str] = Field(None, description="Optional trip-unit type label")
    trip_unit_style_name: Optional[str] = Field(None, description="Optional trip-unit style label")
    maint_mode: bool = Field(False, description="Enable maintenance mode calculations")
    maint_setting: Optional[float] = Field(
        None,
        description="DEPRECATED: Use maint_mode instead. Any truthy value enables maint mode.",
        exclude=True,
    )

    @model_validator(mode="before")
    @classmethod
    def _compat_maint_setting(cls, values):
        """Backward compat: map legacy maint_setting (float) → maint_mode (bool)."""
        if isinstance(values, dict):
            ms = values.get("maint_setting")
            if ms is not None:
                _warnings.warn(
                    "maint_setting is deprecated — use maint_mode: true instead",
                    DeprecationWarning,
                    stacklevel=2,
                )
                # Any truthy value → maint_mode=True; don't overwrite if maint_mode already set
                if not values.get("maint_mode"):
                    values["maint_mode"] = bool(ms)
        return values


class TestCurrentElement(BaseModel):
    """Calculated test current and tolerance band for a single protection element."""
    element: str = Field(..., description="Element name: LTPU, LTD, STPU, STD, INST, GFPU, GFD, MAINT")
    kind: str = Field("pickup", description="'pickup' or 'delay'")
    test_current: float = Field(..., description="Calculated test injection current (amps)")
    limit_low: Optional[float] = Field(None, description="Lower tolerance limit (amps)")
    limit_high: Optional[float] = Field(None, description="Upper tolerance limit (amps)")
    multiplier: float = Field(..., description="Test multiplier applied (1x, 3x, 1.5x, etc.)")
    calc_method: Optional[str] = Field(None, description="Calculation method used (DVL flag label)")
    time_limit_low: Optional[float] = Field(None, description="Lower time tolerance limit (seconds)")
    time_limit_high: Optional[float] = Field(None, description="Upper time tolerance limit (seconds)")
    delay_seconds: Optional[float] = Field(None, description="Expected delay time for time-delay elements")
    notes: Optional[str] = None
    # G4 per-sensor delay-route field-trust (delay elements only; see services/neta/delay_trust.py)
    delay_route: Optional[int] = Field(None, description="SSTDelayCalc route byte governing this delay element (STD/GFD; null for LTD or pickups)")
    trust: Optional[str] = Field(None, description="G4 field-trust tier for the expected delay TIME: db | verify | unsupported")
    trust_reason: Optional[str] = Field(None, description="Short field-tech explanation of the trust tier")


class CalculateResponse(BaseModel):
    """Complete NETA test current calculation results for all elements."""
    sensor_id: int
    sensor_desc: str
    plug_rating: float
    maint_mode: bool = False
    maint_capable: bool = False
    maint_support_level: str = Field("none", description="none | partial_inst_gfpu | full")
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None
    elements: list[TestCurrentElement]
    warnings: list[str] = Field(default_factory=list, description="Any calculation warnings")


# ──────────────────────────────────────────────
# Pass/Fail Evaluation
# ──────────────────────────────────────────────

class MeasuredValue(BaseModel):
    """A single measured value from current injection testing."""
    element: str = Field(..., description="Element name: LTPU, LTD, STPU, STD, INST, GFPU, GFD, MAINT")
    measured_current: Optional[float] = Field(None, description="Measured trip current (amps)")
    measured_time: Optional[float] = Field(None, description="Measured trip time (seconds)")


class EvaluateRequest(BaseModel):
    """Input for pass/fail evaluation against calculated tolerance bands."""
    sensor_id: int
    plug_rating: float
    ltpu_setting: Optional[float] = None
    ltd_setting: Optional[float] = None
    stpu_setting: Optional[float] = None
    std_setting: Optional[float] = None
    inst_setting: Optional[float] = None
    gfpu_setting: Optional[float] = None
    gfd_setting: Optional[float] = None
    multiplier_value: Optional[float] = None
    c_factor: Optional[float] = None
    breaker_context_label: Optional[str] = Field(None, description="Optional bounded breaker-side identity label")
    breaker_context_source: Optional[str] = Field(None, description="Source of breaker_context_label")
    trip_unit_manufacturer_name: Optional[str] = Field(None, description="Optional trip-unit manufacturer label")
    trip_unit_type_name: Optional[str] = Field(None, description="Optional trip-unit type label")
    trip_unit_style_name: Optional[str] = Field(None, description="Optional trip-unit style label")
    maint_mode: bool = False
    maint_setting: Optional[float] = Field(
        None,
        description="DEPRECATED: Use maint_mode instead. Any truthy value enables maint mode.",
        exclude=True,
    )

    @model_validator(mode="before")
    @classmethod
    def _compat_maint_setting(cls, values):
        """Backward compat: map legacy maint_setting (float) → maint_mode (bool)."""
        if isinstance(values, dict):
            ms = values.get("maint_setting")
            if ms is not None:
                _warnings.warn(
                    "maint_setting is deprecated — use maint_mode: true instead",
                    DeprecationWarning,
                    stacklevel=2,
                )
                if not values.get("maint_mode"):
                    values["maint_mode"] = bool(ms)
        return values
    measurements: list[MeasuredValue] = Field(
        ..., description="Actual measured values from current injection test"
    )


class ElementResult(BaseModel):
    """Pass/fail result for a single protection element."""
    element: str
    kind: str = Field("pickup", description="'pickup' or 'delay'")
    passed: bool
    test_current: float = Field(..., description="Expected test current")
    delay_seconds: Optional[float] = Field(None, description="Expected delay time (seconds) for time-delay elements")
    limit_low: Optional[float] = None
    limit_high: Optional[float] = None
    time_limit_low: Optional[float] = None
    time_limit_high: Optional[float] = None
    measured_current: Optional[float] = None
    measured_time: Optional[float] = None
    deviation_pct: Optional[float] = Field(
        None, description="Deviation from expected as percentage"
    )
    notes: Optional[str] = None


class EvaluateResponse(BaseModel):
    """Complete pass/fail evaluation results."""
    sensor_id: int
    sensor_desc: str
    maint_mode: bool = False
    maint_capable: bool = False
    maint_support_level: str = Field("none", description="none | partial_inst_gfpu | full")
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None
    overall_pass: bool = Field(..., description="True only if ALL tested elements pass")
    elements: list[ElementResult]
    tested_count: int = Field(..., description="Number of elements tested")
    passed_count: int = Field(..., description="Number of elements that passed")
    failed_count: int = Field(..., description="Number of elements that failed")
    warnings: list[str] = Field(default_factory=list, description="Maint mode or calculation warnings")


# ──────────────────────────────────────────────
# Plot TCC Overlay
# ──────────────────────────────────────────────

class PlotMeasurement(BaseModel):
    """A single measured value for plot overlay."""
    element: str = Field(..., description="Element name: LTPU, STPU, INST, GFPU")
    measured_current: Optional[float] = None
    measured_time: Optional[float] = None


class PlotTccRequest(BaseModel):
    """Request for the combined TCC plot payload."""
    sensor_id: int = Field(..., description="Sensor ID from cascade selection")
    plug_rating: float = Field(..., description="Selected plug/rating value (Ir)")
    ltpu_setting: Optional[float] = None
    ltd_setting: Optional[float] = None
    stpu_setting: Optional[float] = None
    std_setting: Optional[float] = None
    inst_setting: Optional[float] = None
    gfpu_setting: Optional[float] = None
    gfd_setting: Optional[float] = None
    ltd_delay_setting: Optional[float] = Field(
        None,
        description="Selected LTD delay band/open-time setting; separates band selection from test multiple.",
    )
    std_delay_setting: Optional[float] = Field(
        None,
        description="Selected STD delay band/open-time setting; separates band selection from test multiple.",
    )
    gfd_delay_setting: Optional[float] = Field(
        None,
        description="Selected GFD delay band/open-time setting; separates band selection from test multiple.",
    )
    ltd_test_multiple: Optional[float] = Field(
        None,
        description="NETA LTD test multiple used to compute delay test current.",
    )
    std_test_multiple: Optional[float] = Field(
        None,
        description="NETA STD test multiple used to compute delay test current.",
    )
    gfd_test_multiple: Optional[float] = Field(
        None,
        description="NETA GFD test multiple used to compute delay test current.",
    )
    multiplier_value: Optional[float] = None
    c_factor: Optional[float] = None
    maint_mode: bool = False
    maint_setting: Optional[float] = Field(None, description="DEPRECATED", exclude=True)
    measurements: Optional[list[PlotMeasurement]] = Field(
        None, description="Optional measured values for overlay markers"
    )
    breaker_context_label: Optional[str] = Field(
        None,
        description="Optional bounded breaker-side identity label supplied by the UI",
    )
    breaker_context_source: Optional[str] = Field(
        None,
        description="How breaker_context_label was derived on the UI side",
    )
    trip_unit_manufacturer_name: Optional[str] = Field(
        None,
        description="Optional matched trip-unit manufacturer label from the UI",
    )
    trip_unit_type_name: Optional[str] = Field(
        None,
        description="Optional matched trip-unit type label from the UI",
    )
    trip_unit_style_name: Optional[str] = Field(
        None,
        description="Optional matched trip-unit style label from the UI",
    )
    include_nominal_curve: bool = Field(True, description="Include breaker curves in payload")
    include_expected_markers: bool = Field(True, description="Include expected test markers")
    include_measured_markers: bool = Field(True, description="Include measured result markers")

    @model_validator(mode="before")
    @classmethod
    def _compat_maint_setting(cls, values):
        if isinstance(values, dict):
            ms = values.get("maint_setting")
            if ms is not None:
                _warnings.warn(
                    "maint_setting is deprecated — use maint_mode: true instead",
                    DeprecationWarning, stacklevel=2,
                )
                if not values.get("maint_mode"):
                    values["maint_mode"] = bool(ms)
        return values


class PlotCurvePoint(BaseModel):
    amps: float
    seconds: float


class PlotCurve(BaseModel):
    """A single TCC curve segment."""
    id: str = Field(..., description="Unique curve ID, e.g. 'ltd_open'")
    element: str = Field(..., description="Element: LTD, STD, INST, GFD")
    phase: str = Field(..., description="'open' or 'clear'")
    line_style: str = Field("solid", description="Rendering hint: solid, dashed, dotted")
    points: list[PlotCurvePoint]


class PlotCompositeBand(BaseModel):
    """Native-faithful composite boundary band (G4 §3g).

    The classic TCC staircase assembled from the served per-element curves
    (CPointsMergeSST/CPointsMergeGF semantics): vertical pickup asymptote →
    element blocks clipped at the inter-element handoffs → INST floor to the
    right edge. ``open_points``/``clear_points`` are the min-trip and
    total-clear boundaries; the frontend closes them into the shaded band.
    An element listed in ``open_only_elements`` serves no clear curve, so its
    clear segment reuses the open data (zero band width there)."""
    id: str = Field(..., description="'phase_band' or 'gf_band'")
    family: str = Field(..., description="'phase' or 'gf'")
    open_points: list[PlotCurvePoint] = Field(default_factory=list)
    clear_points: list[PlotCurvePoint] = Field(default_factory=list)
    open_only_elements: list[str] = Field(default_factory=list)
    right_edge_amps: float


class PlotEnvelopeElementBasis(BaseModel):
    """Per-element tolerance basis behind the acceptance envelope (#124).

    Derived from the SAME served acceptance surfaces the whiskers use
    (pickup marker limits / delay table rows), so the envelope and the
    whiskers cannot drift apart. ``estimated`` flags the generic LTD
    fallback so a placeholder never reads as DB-authoritative."""
    element: str
    pu_tol_lo_pct: Optional[float] = None
    pu_tol_hi_pct: Optional[float] = None
    time_tol_lo_pct: Optional[float] = None
    time_tol_hi_pct: Optional[float] = None
    pu_source: Optional[str] = None
    time_source: Optional[str] = Field(
        None,
        description="'ltd_curve_tol' | 'ltd_generic_estimate' | 'published_band'",
    )
    estimated: bool = False


class PlotEnvelopeBand(BaseModel):
    """Field-acceptance tolerance envelope band (#124).

    NOT the published curve pair (that is ``PlotCompositeBand``): the
    envelope applies the per-sensor mfr PU tolerances along the amps axis
    (every participating element) and the time-tolerance basis along the
    seconds axis (acceptance-window elements only — LTD) to the served
    curves, then reassembles min/max boundaries through the composite
    assembler. Elements with no usable basis are withheld and listed in
    ``no_envelope_elements`` (no fabrication; NETA=mfr law)."""
    id: str = Field(..., description="'phase_envelope' or 'gf_envelope'")
    family: str = Field(..., description="'phase' or 'gf'")
    min_points: list[PlotCurvePoint] = Field(default_factory=list)
    max_points: list[PlotCurvePoint] = Field(default_factory=list)
    element_basis: list[PlotEnvelopeElementBasis] = Field(default_factory=list)
    open_only_elements: list[str] = Field(default_factory=list)
    no_envelope_elements: list[str] = Field(default_factory=list)
    right_edge_amps: float


class PlotExpectedMarker(BaseModel):
    """Expected test target marker."""
    id: str
    element: str
    kind: str = Field(..., description="'pickup' or 'delay'")
    render_hint: str = Field(..., description="'vertical_marker' or 'point'")
    test_multiple: float
    expected_current: float
    expected_time: Optional[float] = None
    limit_low: Optional[float] = None
    limit_high: Optional[float] = None
    curve_ref: Optional[str] = None
    label: str
    # G4 per-element field-trust (same classifier as /calculate, #67 parity):
    # pickups are DB-authoritative; delay markers carry the route-classified tier.
    trust: Optional[str] = Field(None, description="'db' | 'verify' | 'unsupported'")
    trust_reason: Optional[str] = None


class PlotMeasuredMarker(BaseModel):
    """Measured result marker."""
    id: str
    element: str
    kind: str
    render_hint: str
    measured_current: Optional[float] = None
    measured_time: Optional[float] = None
    passed: bool
    deviation_pct: Optional[float] = None
    label: str


class PlotTableRow(BaseModel):
    """Companion summary table row.

    For pickup elements: current tolerance (limit_low / limit_high) is the
    primary acceptance surface; time fields are null.

    For delay elements: time tolerance (time_limit_low / time_limit_high) is
    the primary acceptance surface; expected_current documents the fixed
    injection level used for the test.
    """
    element: str
    kind: str = Field("pickup", description="'pickup' or 'delay'")
    setting: Optional[float] = None
    test_multiple: float
    expected_current: float
    limit_low: Optional[float] = Field(None, description="Current acceptance band low (A)")
    limit_high: Optional[float] = Field(None, description="Current acceptance band high (A)")
    expected_time: Optional[float] = None
    time_limit_low: Optional[float] = Field(None, description="Time acceptance band low (s)")
    time_limit_high: Optional[float] = Field(None, description="Time acceptance band high (s)")
    measured_current: Optional[float] = None
    measured_time: Optional[float] = None
    passed: Optional[bool] = None
    deviation_pct: Optional[float] = None
    calc_method: Optional[str] = None
    notes: Optional[str] = Field(
        None,
        description="For delay rows: 'timing_source=<source>' — the tolerance "
                    "basis ('ltd_reference_window' = per-mfr DS2_TOL band, from "
                    "the per-curve etu_ltd_params row or, when no curve rows "
                    "exist, the sensor-level etu_sensors.ltd_tol_lo/hi pair "
                    "(L11); '..._generic' = flagged generic estimate; "
                    "'band_table' = per-sensor DB band; 'i2x_*' = validated "
                    "etu_ixt surface; 'curve_interpolation' = open/clear curve "
                    "envelope).",
    )
    # G4 per-element field-trust (same classifier as /calculate, #67 parity).
    trust: Optional[str] = Field(None, description="'db' | 'verify' | 'unsupported'")
    trust_reason: Optional[str] = None


class PlotMeta(BaseModel):
    """Plot metadata."""
    sensor_id: int
    sensor_desc: str
    breaker_context_label: Optional[str] = None
    breaker_context_source: Optional[str] = None
    manufacturer: Optional[str] = None
    trip_type: Optional[str] = None
    trip_style: Optional[str] = None
    trip_unit_manufacturer: Optional[str] = None
    trip_unit_type: Optional[str] = None
    trip_unit_style: Optional[str] = None
    plug_rating: float
    maint_mode: bool = False
    maint_capable: bool = False
    maint_support_level: str = "none"
    overall_pass: Optional[bool] = None
    plot_disclaimer: Optional[str] = None
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None


class PlotTccResponse(BaseModel):
    """Complete TCC plot payload — curves, markers, table, and metadata."""
    meta: PlotMeta
    warnings: list[str] = Field(default_factory=list)
    curves: list[PlotCurve] = Field(default_factory=list)
    composite_bands: list[PlotCompositeBand] = Field(default_factory=list)
    envelope_bands: list[PlotEnvelopeBand] = Field(default_factory=list)
    expected_markers: list[PlotExpectedMarker] = Field(default_factory=list)
    measured_markers: list[PlotMeasuredMarker] = Field(default_factory=list)
    table_rows: list[PlotTableRow] = Field(default_factory=list)
