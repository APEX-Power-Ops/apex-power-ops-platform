import { browserEnv } from './browser-env'

export type BreakerFamily = 'etu' | 'tmt' | 'emt'

export type CatalogStatusResponse = {
  catalog: string
  manufacturer_count: number
  sensor_count: number
  error?: string
}

export type ResolvedEquipmentSummary = {
  family: string
  family_label: string | null
  resolved_id: string | null
  primary_label: string | null
  secondary_label: string | null
  breaker_context: {
    label: string | null
    source: string | null
    manufacturer_name: string | null
    breaker_class: string | null
    breaker_name: string | null
    breaker_style_name: string | null
    type_name: string | null
    style_name: string | null
    tcc_number: string | null
  } | null
  trip_unit: {
    manufacturer_name: string | null
    trip_type_name: string | null
    trip_style_name: string | null
    label: string | null
  } | null
  rating_context: {
    label: string | null
    sensor_id: number | null
    sensor_desc: string | null
    sensor_rating: number | null
    frame_id: number | null
    frame_size: string | null
    frame_desc: string | null
    amp_ratings: number[]
    section_id: number | null
    section_name: string | null
  } | null
}

export type EtuSearchResult = {
  sensor_id: number
  sensor_rating: number | null
  sensor_desc: string
  trip_style_id: number
  trip_style_name: string
  trip_type_id: number
  trip_type_name: string
  manufacturer_id: number
  manufacturer_name: string
  compatible_plug_values: number[]
}

export type EtuSearchResponse = {
  count: number
  results: EtuSearchResult[]
}

export type CascadeManufacturer = {
  manufacturer_id: number
  manufacturer_name: string
  trip_type_count: number
}

export type CascadeTripType = {
  trip_type_id: number
  trip_type_name: string
  manufacturer_id: number
  manufacturer_name: string
  trip_style_count: number
}

export type CascadeTripStyle = {
  trip_style_id: number
  trip_style_name: string
  trip_type_id: number
  trip_type_name: string
  manufacturer_id: number
  manufacturer_name: string
  sensor_count: number
}

export type CascadeSensor = {
  sensor_id: number
  sensor_rating: number | null
  sensor_desc: string
  trip_style_id: number
  trip_style_name: string
  trip_type_id: number
  trip_type_name: string
  manufacturer_id: number
  manufacturer_name: string
  has_ltpu: boolean
  has_stpu: boolean
  has_inst: boolean
  has_gfpu: boolean
}

export type CascadePlugOption = {
  plug_value: number
  sensor_count: number
}

export type CascadeResponse = {
  level: string
  count: number
  manufacturers: CascadeManufacturer[]
  trip_types: CascadeTripType[]
  trip_styles: CascadeTripStyle[]
  sensors: CascadeSensor[]
  plug_values: CascadePlugOption[]
}

export type CascadeParams = {
  manufacturerId?: number | null
  tripTypeId?: number | null
  tripStyleId?: number | null
  sensorId?: number | null
  plugValue?: number | null
  breakerClass?: string | null
  breakerId?: number | null
  breakerStyleId?: number | null
}

export type EtuBreakerCascadeResponse = {
  level: string
  count: number
  scope: Record<string, number | string | null>
  manufacturers: {
    manufacturer_id: number
    manufacturer_name: string
    breaker_count: number
  }[]
  breaker_classes: {
    breaker_class: string
    breaker_count: number
  }[]
  breakers: {
    breaker_id: number
    breaker_name: string
    breaker_class: string
    manufacturer_id: number
    manufacturer_name: string
    style_count: number
  }[]
  breaker_styles: {
    breaker_style_id: number
    breaker_style_name: string
    breaker_id: number
    breaker_name: string
    breaker_class: string
    manufacturer_id: number
    manufacturer_name: string
  }[]
}

export type EtuBreakerCascadeParams = {
  manufacturerId?: number | null
  breakerClass?: string | null
  breakerId?: number | null
  breakerStyleId?: number | null
  tripTypeId?: number | null
  tripStyleId?: number | null
  sensorId?: number | null
}

// SST-bridge narrowing: breaker style -> compatible ETU sensor set (D1 / migration 006).
export type EtuBridgeSensor = {
  breaker_class: string
  breaker_id: number
  breaker_style_id: number
  breaker_style_frame: string | null
  tmt_sst_mfr: string | null
  tmt_sst_type: string | null
  tmt_sst_style: string | null
  trip_style_id: number
  sensor_id: number
  sensor_rating: number | null
  sensor_description: string | null
}

export type EtuBridgeSensorsResponse = {
  breaker_style_id: number | null
  breaker_id: number | null
  bridge_match_status: 'matched' | 'unmatched'
  count: number
  sensors: EtuBridgeSensor[]
}

export type EtuBridgeSensorsParams = {
  breakerStyleId?: number | null
  breakerId?: number | null
}

export type SensorCalcContext = {
  sensor_id: number
  sensor_desc: string
  trip_style_id: number
  trip_style_name: string
  trip_type_name: string
  manufacturer_name: string
  rating: number | null
  resolved_equipment: ResolvedEquipmentSummary | null
  has_ltpu: boolean
  has_stpu: boolean
  has_inst: boolean
  has_gfpu: boolean
  ltpu_calc: number | null
  stpu_calc: number | null
  inst_calc: number | null
  gfpu_calc: number | null
  ltpu_tol_hi: number | null
  ltpu_tol_lo: number | null
  stpu_tol_hi: number | null
  stpu_tol_lo: number | null
  inst_ovrtol_min: number | null
  inst_ovrtol_max: number | null
  gfpu_tol_hi: number | null
  gfpu_tol_lo: number | null
  ltpu_step: number | null
  stpu_step: number | null
  inst_step: number | null
  gfpu_step: number | null
  stpu_i2t: number | null
  gfpu_i2t: number | null
  ltd_func: number | null
  ltd_setting_method: number | null
  ltd_tol_hi: number | null
  ltd_tol_lo: number | null
  maint_available: boolean
  maint_capable: boolean
}

export type DelayBandOption = {
  band: string
  label: string
  open_time: number
  clear_time: number | null
  is_default: boolean
}

export type AvailableSettingsResponse = {
  sensor_id: number
  plug_values: number[]
  ltpu_settings: number[]
  ltd_settings: DelayBandOption[]
  std_settings: DelayBandOption[]
  gfd_settings: DelayBandOption[]
  ltd_multipliers: unknown[]
  stpu_settings: number[]
  inst_settings: number[]
  gfpu_settings: number[]
}

export type PlotCurvePoint = {
  amps: number
  seconds: number
}

export type EtuPlotCurve = {
  id: string
  element: string
  phase: string
  line_style: string
  points: PlotCurvePoint[]
}

export type EtuPlotExpectedMarker = {
  id: string
  element: string
  kind: string
  render_hint: string
  test_multiple: number
  expected_current: number
  expected_time: number | null
  limit_low: number | null
  limit_high: number | null
  curve_ref: string | null
  label: string
}

export type EtuPlotTableRow = {
  element: string
  kind: string
  setting: number | null
  test_multiple: number | null
  expected_current: number | null
  limit_low: number | null
  limit_high: number | null
  expected_time: number | null
  time_limit_low: number | null
  time_limit_high: number | null
  calc_method: string | null
  notes: string | null
}

export type EtuPlotResponse = {
  meta: {
    sensor_id: number
    sensor_desc: string
    breaker_context_label: string | null
    breaker_context_source: string | null
    manufacturer: string | null
    trip_type: string | null
    trip_style: string | null
    trip_unit_manufacturer: string | null
    trip_unit_type: string | null
    trip_unit_style: string | null
    plug_rating: number
    maint_mode: boolean
    maint_capable: boolean
    maint_support_level: string
    plot_disclaimer: string | null
    resolved_equipment: ResolvedEquipmentSummary | null
  }
  warnings: string[]
  curves: EtuPlotCurve[]
  expected_markers: EtuPlotExpectedMarker[]
  table_rows: EtuPlotTableRow[]
}

export type EtuPlotRequest = {
  sensor_id: number
  plug_rating: number
  ltpu_setting?: number
  ltd_setting?: number
  stpu_setting?: number
  std_setting?: number
  inst_setting?: number
  gfpu_setting?: number
  gfd_setting?: number
  ltd_delay_setting?: number
  std_delay_setting?: number
  gfd_delay_setting?: number
  ltd_test_multiple?: number
  std_test_multiple?: number
  gfd_test_multiple?: number
  multiplier_value?: number
  c_factor?: number
  maint_mode?: boolean
  breaker_context_label?: string
  breaker_context_source?: string
  trip_unit_manufacturer_name?: string
  trip_unit_type_name?: string
  trip_unit_style_name?: string
  include_nominal_curve: boolean
  include_expected_markers: boolean
  include_measured_markers: boolean
}

export type TMTFacet = {
  name: string
  values: Array<number | string>
  cardinality: number
}

export type TMTFacetsResponse = {
  facets: TMTFacet[]
  total_matching_frames: number
  active_filters: Record<string, number | string>
}

export type TMTFrameSearchResult = {
  frame_id: number
  breaker_style_id: number
  breaker_class: string | null
  frame_size: string | null
  manufacturer_name: string | null
  breaker_name: string | null
  breaker_style_name: string | null
  standard: number | null
  matched_amp_rating: number | null
}

export type TMTFrameSearchResponse = {
  count: number
  frames: TMTFrameSearchResult[]
}

export type TMTFrameContext = {
  frame_id: number
  breaker_style_id: number
  breaker_class: string | null
  frame_size: string | null
  manufacturer_name: string | null
  breaker_name: string | null
  breaker_style_name: string | null
  standard: number | null
  available_trip_classes: number[]
  amp_rating_count: number
  setting_count: number
  thermal_adjustment_count: number
  resolved_equipment: ResolvedEquipmentSummary | null
}

export type TMTAmpOption = {
  rating: number
  max_override: number | null
}

export type TMTSettingOption = {
  value: number | null
  label: string | null
  tol_lo: number | null
  tol_hi: number | null
}

export type TMTSettingsResponse = {
  frame_id: number
  available_trip_classes: number[]
  amp_ratings: TMTAmpOption[]
  settings: TMTSettingOption[]
  thermal_adjustments: number[]
}

export type TMTPlotRequest = {
  frame_id: number
  trip_class: number
  amp_rating?: number
  setting_value?: number
  thermal_adjustment?: number
  include_raw_points?: boolean
  num_output_points?: number
}

export type TMTPlotResponse = {
  meta: {
    frame_id: number
    breaker_style_id: number
    breaker_class: string | null
    frame_size: string | null
    manufacturer_name: string | null
    breaker_name: string | null
    breaker_style_name: string | null
    standard: number | null
    selected_trip_class: number
    selected_amp_rating: number | null
    selected_max_override: number | null
    selected_setting: number | null
    selected_setting_label: string | null
    selected_setting_tol_lo: number | null
    selected_setting_tol_hi: number | null
    selected_thermal_adjustment: number | null
    selections_applied_to_curve: boolean
    plot_disclaimer: string | null
    resolved_equipment: ResolvedEquipmentSummary | null
  }
  warnings: string[]
  curves: {
    id: string
    curve_family: string
    trip_class: number
    line_style: string
    points: PlotCurvePoint[]
  }[]
  raw_points: PlotCurvePoint[]
}

export type EMTFacet = {
  name: string
  values: Array<number | string>
  cardinality: number
}

export type EMTFacetsResponse = {
  facets: EMTFacet[]
  total_matching_frames: number
  active_filters: Record<string, number | string>
}

export type EMTFrameSearchResult = {
  emt_id: number
  frame_id: number
  manufacturer_id: number | null
  manufacturer_name: string | null
  type_name: string | null
  style_name: string | null
  tcc_number: string | null
  trip_char: number | null
  trip_plug: number | null
  frame_size: number | null
  frame_desc: string | null
  amp_rating_count: number
  section_count: number
}

export type EMTFrameSearchResponse = {
  count: number
  frames: EMTFrameSearchResult[]
}

export type EMTSectionSummary = {
  section_id: number
  name: string | null
  sec_char: number | null
  curve_type: number | null
  pickup_calc: number | null
  pickup_setting: number | null
  step_size: number | null
  current_calc: number | null
  pickup_tol_lo: number | null
  pickup_tol_hi: number | null
  band_count: number
  pickup_count: number
}

export type EMTFrameContext = {
  emt_id: number
  frame_id: number
  manufacturer_id: number | null
  manufacturer_name: string | null
  type_name: string | null
  style_name: string | null
  tcc_number: string | null
  trip_char: number | null
  trip_plug: number | null
  frame_size: number | null
  frame_desc: string | null
  amp_ratings: number[]
  sections: EMTSectionSummary[]
  resolved_equipment: ResolvedEquipmentSummary | null
}

export type EMTPickupOption = {
  setting: number | null
  description: string | null
}

export type EMTBandOption = {
  band_id: number
  band_name: string | null
  ordinal: number | null
  current_at: number | null
  curve_point_count: number
  curve_classes: number[]
}

export type EMTSectionSettingsResponse = {
  section_id: number
  name: string | null
  sec_char: number | null
  curve_type: number | null
  pickup_calc: number | null
  pickup_setting: number | null
  step_size: number | null
  current_calc: number | null
  pickup_tol_lo: number | null
  pickup_tol_hi: number | null
  pickups: EMTPickupOption[]
  bands: EMTBandOption[]
}

export type EMTPlotRequest = {
  section_id: number
  band_id: number
  curve_class?: number
}

export type EMTPlotResponse = {
  meta: {
    emt_id: number
    frame_id: number
    section_id: number
    band_id: number
    manufacturer_id: number | null
    manufacturer_name: string | null
    type_name: string | null
    style_name: string | null
    tcc_number: string | null
    frame_size: number | null
    frame_desc: string | null
    section_name: string | null
    sec_char: number | null
    curve_type: number | null
    pickup_calc: number | null
    pickup_setting: number | null
    current_calc: number | null
    band_name: string | null
    band_ordinal: number | null
    current_at: number | null
    available_curve_classes: number[]
    selected_curve_class: number | null
    selections_applied_to_curve: boolean
    plot_disclaimer: string | null
    resolved_equipment: ResolvedEquipmentSummary | null
  }
  warnings: string[]
  curves: {
    id: string
    curve_family: string
    band_id: number
    curve_class: number | null
    class_label: string | null
    line_style: string
    points: PlotCurvePoint[]
  }[]
}

export class BreakerResourcesError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'BreakerResourcesError'
    this.status = status
  }
}

function getErrorDetail(payload: unknown, fallback: string) {
  if (typeof payload !== 'object' || payload === null) {
    return fallback
  }

  const detail = (payload as { detail?: unknown; error?: unknown }).detail
  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail
  }

  const error = (payload as { error?: unknown }).error
  return typeof error === 'string' && error.trim().length > 0 ? error : fallback
}

async function parseJsonResponse(response: Response) {
  try {
    return (await response.json()) as unknown
  } catch {
    return null
  }
}

function buildUrl(path: string) {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  return `${baseUrl}${path}`
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(buildUrl(path), {
    headers: {
      Accept: 'application/json',
    },
  })
  const payload = await parseJsonResponse(response)

  if (!response.ok) {
    throw new BreakerResourcesError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as T
}

async function postJson<T, B>(path: string, body: B): Promise<T> {
  const response = await fetch(buildUrl(path), {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  const payload = await parseJsonResponse(response)

  if (!response.ok) {
    throw new BreakerResourcesError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as T
}

function appendOptionalParam(search: URLSearchParams, key: string, value: number | string | null | undefined) {
  if (value === null || value === undefined) {
    return
  }

  const normalized = String(value).trim()
  if (normalized.length > 0) {
    search.set(key, normalized)
  }
}

export async function fetchCatalogStatus(): Promise<CatalogStatusResponse> {
  return getJson<CatalogStatusResponse>('/api/v1/neta/catalog/status')
}

export async function fetchEtuSearch(
  query: string,
  options: {
    manufacturerId?: number | null
  } = {},
): Promise<EtuSearchResponse> {
  const search = new URLSearchParams({ limit: '12' })
  appendOptionalParam(search, 'q', query)
  appendOptionalParam(search, 'manufacturer_id', options.manufacturerId)
  return getJson<EtuSearchResponse>(`/api/v1/neta/etu/search?${search.toString()}`)
}

export async function fetchCascade(params: CascadeParams = {}): Promise<CascadeResponse> {
  const search = new URLSearchParams()
  appendOptionalParam(search, 'manufacturer_id', params.manufacturerId)
  appendOptionalParam(search, 'trip_type_id', params.tripTypeId)
  appendOptionalParam(search, 'trip_style_id', params.tripStyleId)
  appendOptionalParam(search, 'sensor_id', params.sensorId)
  appendOptionalParam(search, 'plug_value', params.plugValue)
  appendOptionalParam(search, 'breaker_class', params.breakerClass)
  appendOptionalParam(search, 'breaker_id', params.breakerId)
  appendOptionalParam(search, 'breaker_style_id', params.breakerStyleId)
  const suffix = search.toString()
  return getJson<CascadeResponse>(`/api/v1/neta/cascade${suffix ? `?${suffix}` : ''}`)
}

export async function fetchEtuBreakerCascade(
  params: EtuBreakerCascadeParams = {},
): Promise<EtuBreakerCascadeResponse> {
  const search = new URLSearchParams()
  appendOptionalParam(search, 'manufacturer_id', params.manufacturerId)
  appendOptionalParam(search, 'breaker_class', params.breakerClass)
  appendOptionalParam(search, 'breaker_id', params.breakerId)
  appendOptionalParam(search, 'breaker_style_id', params.breakerStyleId)
  appendOptionalParam(search, 'trip_type_id', params.tripTypeId)
  appendOptionalParam(search, 'trip_style_id', params.tripStyleId)
  appendOptionalParam(search, 'sensor_id', params.sensorId)
  const suffix = search.toString()
  return getJson<EtuBreakerCascadeResponse>(
    `/api/v1/neta/etu/breaker-cascade${suffix ? `?${suffix}` : ''}`,
  )
}

export async function fetchEtuBridgeSensors(
  params: EtuBridgeSensorsParams = {},
): Promise<EtuBridgeSensorsResponse> {
  const search = new URLSearchParams()
  appendOptionalParam(search, 'breaker_style_id', params.breakerStyleId)
  appendOptionalParam(search, 'breaker_id', params.breakerId)
  return getJson<EtuBridgeSensorsResponse>(
    `/api/v1/neta/etu/bridge-sensors?${search.toString()}`,
  )
}

export async function fetchEtuContext(sensorId: number): Promise<SensorCalcContext> {
  return getJson<SensorCalcContext>(`/api/v1/neta/context/${sensorId}`)
}

export async function fetchEtuSettings(sensorId: number): Promise<AvailableSettingsResponse> {
  return getJson<AvailableSettingsResponse>(`/api/v1/neta/settings/${sensorId}`)
}

export async function fetchEtuPlot(request: EtuPlotRequest): Promise<EtuPlotResponse> {
  return postJson<EtuPlotResponse, EtuPlotRequest>('/api/v1/neta/plot-tcc', request)
}

export async function fetchTmtFacets(breakerClass: string): Promise<TMTFacetsResponse> {
  const search = new URLSearchParams()
  appendOptionalParam(search, 'breaker_class', breakerClass)
  const suffix = search.toString()
  return getJson<TMTFacetsResponse>(`/api/v1/neta/tmt/facets${suffix ? `?${suffix}` : ''}`)
}

export async function fetchTmtFrames({
  breakerClass,
  manufacturerId,
  manufacturerName,
}: {
  breakerClass: string
  manufacturerId?: number | null
  manufacturerName?: string
}): Promise<TMTFrameSearchResponse> {
  const search = new URLSearchParams({ limit: '12' })
  appendOptionalParam(search, 'breaker_class', breakerClass)
  appendOptionalParam(search, 'manufacturer_id', manufacturerId)
  appendOptionalParam(search, 'manufacturer_name', manufacturerName)
  return getJson<TMTFrameSearchResponse>(`/api/v1/neta/tmt/frames?${search.toString()}`)
}

export async function fetchTmtContext(frameId: number): Promise<TMTFrameContext> {
  return getJson<TMTFrameContext>(`/api/v1/neta/tmt/context/${frameId}`)
}

export async function fetchTmtSettings(frameId: number): Promise<TMTSettingsResponse> {
  return getJson<TMTSettingsResponse>(`/api/v1/neta/tmt/settings/${frameId}`)
}

export async function fetchTmtPlot(request: TMTPlotRequest): Promise<TMTPlotResponse> {
  return postJson<TMTPlotResponse, TMTPlotRequest>('/api/v1/neta/tmt/plot-tcc', request)
}

export async function fetchEmtFacets(): Promise<EMTFacetsResponse> {
  return getJson<EMTFacetsResponse>('/api/v1/neta/emt/facets')
}

export async function fetchEmtFrames(
  query: string,
  options: {
    manufacturerId?: number | null
  } = {},
): Promise<EMTFrameSearchResponse> {
  const search = new URLSearchParams({ limit: '12' })
  appendOptionalParam(search, 'q', query)
  appendOptionalParam(search, 'manufacturer_id', options.manufacturerId)
  return getJson<EMTFrameSearchResponse>(`/api/v1/neta/emt/frames?${search.toString()}`)
}

export async function fetchEmtContext(frameId: number): Promise<EMTFrameContext> {
  return getJson<EMTFrameContext>(`/api/v1/neta/emt/context/${frameId}`)
}

export async function fetchEmtSettings(sectionId: number): Promise<EMTSectionSettingsResponse> {
  return getJson<EMTSectionSettingsResponse>(`/api/v1/neta/emt/settings/${sectionId}`)
}

export async function fetchEmtPlot(request: EMTPlotRequest): Promise<EMTPlotResponse> {
  return postJson<EMTPlotResponse, EMTPlotRequest>('/api/v1/neta/emt/plot-tcc', request)
}
