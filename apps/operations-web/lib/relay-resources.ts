import { browserEnv } from './browser-env'

export type RelayLineSectionSummary = {
  line_section_source_id: number
  section_number: number
  section_name: string | null
  pickup: number | null
  secondary_i_code: number | null
  amps_calc_mode: number | null
  use_toc_multiplier: boolean | null
}

export type RelayRangeDiscreteValue = {
  value: number | string | null
  description: string | null
}

export type RelayRangeOption = {
  range_source_id: number
  source_parent_id: number | null
  parent_kind: string
  parent_label: string | null
  aux_key: number | null
  ordinal: number | null
  min_value: number | null
  max_value: number | null
  step_value: number | null
  relative_unit_code: number | null
  use_range: boolean | null
  scales_with_time_multiplier: boolean | null
  discrete_values: RelayRangeDiscreteValue[]
}

export type RelayCurveParentOption = {
  curve_parent_source_id: number
  storage_kind: string
  curve_name: string | null
  curve_parent_ordinal: number | null
  min_pickup: number | null
  max_pickup: number | null
  is_discrete: boolean | null
  step_size: number | null
  horizontal_amps_code: number | null
  preview_option_count: number
}

export type RelayPreviewOption = {
  curve_parent_source_id: number
  storage_kind: string
  curve_name: string | null
  curve_ordinal: number | null
  source_ordinal: number | null
  time_dial: number | null
  td_desc: string | null
  point_count: number | null
  current_min: number | null
  current_max: number | null
  coefficients: Record<string, number | null>
}

export type RelaySectionSearchResult = {
  manufacturer_source_id: number
  relay_type: string | null
  relay_device_source_id: number
  device_function: string | null
  device_ordinal: number
  standard_code: number | null
  dftype_code: number | null
  voltage_restraint_kind: string | null
  td_section_source_id: number
  td_section_name: string | null
  family_code: number
  family_name: string
  storage_kind: string
  supported: boolean
}

export type RelaySectionSearchResponse = {
  count: number
  sections: RelaySectionSearchResult[]
}

export type RelayContextResponse = {
  manufacturer_source_id: number
  relay_type: string | null
  relay_device_source_id: number
  device_function: string | null
  device_ordinal: number
  standard_code: number | null
  dftype_code: number | null
  voltage_restraint_kind: string | null
  td_section_source_id: number
  td_section_name: string | null
  family_code: number
  family_name: string
  storage_kind: string
  supported: boolean
  unsupported_reason: string | null
  line_section_count: number
  range_count: number
  curve_parent_count: number
  preview_option_count: number
  line_sections: RelayLineSectionSummary[]
}

export type RelaySettingsResponse = {
  td_section_source_id: number
  family_code: number
  family_name: string
  storage_kind: string
  supported: boolean
  unsupported_reason: string | null
  line_sections: RelayLineSectionSummary[]
  ranges: RelayRangeOption[]
  curve_parents: RelayCurveParentOption[]
  preview_options: RelayPreviewOption[]
}

export type RelayPlotCurvePoint = {
  current_multiple: number
  seconds: number
  evaluated_current_multiple?: number | null
}

export type RelayPlotCurve = {
  id: string
  family_name: string
  storage_kind: string
  curve_name: string
  curve_parent_source_id: number
  curve_ordinal: number | null
  source_ordinal: number | null
  time_dial: number | null
  td_desc: string | null
  points: RelayPlotCurvePoint[]
}

export type RelayPlotMeta = {
  td_section_source_id: number
  relay_device_source_id: number
  manufacturer_source_id: number
  relay_type: string | null
  device_function: string | null
  td_section_name: string | null
  family_code: number
  family_name: string
  storage_kind: string
  supported: boolean
  status: string
  unsupported_reason: string | null
  selected_curve_parent_source_id: number | null
  selected_curve_name: string | null
  selected_curve_ordinal: number | null
  selected_source_ordinal: number | null
  selected_time_dial: number | null
  selected_td_desc: string | null
  candidate_applied: boolean
  candidate_pickup_multiplier: number | null
  candidate_time_dial: number | null
  candidate_voltage_threshold_multiplier: number | null
  plot_disclaimer: string
}

export type RelayPlotResponse = {
  meta: RelayPlotMeta
  warnings: string[]
  curves: RelayPlotCurve[]
}

export type RelayPlotRequest = {
  td_section_source_id: number
  curve_parent_source_id?: number
  curve_ordinal?: number
  source_ordinal?: number
  time_dial?: number
  current_multiples: number[]
  candidate_overrides?: {
    pickup_multiplier?: number
    time_dial?: number
    voltage_threshold_multiplier?: number
  }
}

export class RelayResourcesError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'RelayResourcesError'
    this.status = status
  }
}

function getErrorDetail(payload: unknown, fallback: string) {
  if (typeof payload !== 'object' || payload === null) {
    return fallback
  }

  const detail = (payload as { detail?: unknown }).detail
  return typeof detail === 'string' && detail.trim().length > 0 ? detail : fallback
}

async function parseJsonResponse(response: Response) {
  try {
    return (await response.json()) as unknown
  } catch {
    return null
  }
}

async function getJson<T>(path: string): Promise<T> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const response = await fetch(`${baseUrl}${path}`, {
    headers: {
      Accept: 'application/json',
    },
  })
  const payload = await parseJsonResponse(response)

  if (!response.ok) {
    throw new RelayResourcesError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as T
}

async function postJson<T>(path: string, body: RelayPlotRequest): Promise<T> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const response = await fetch(`${baseUrl}${path}`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  const payload = await parseJsonResponse(response)

  if (!response.ok) {
    throw new RelayResourcesError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as T
}

export async function fetchRelaySections(query = ''): Promise<RelaySectionSearchResponse> {
  const search = new URLSearchParams({ supported_only: 'true', limit: '12' })
  const normalizedQuery = query.trim()
  if (normalizedQuery.length > 0) {
    search.set('q', normalizedQuery)
  }
  return getJson<RelaySectionSearchResponse>(`/api/v1/neta/relay/sections?${search.toString()}`)
}

export async function fetchRelayContext(tdSectionSourceId: number): Promise<RelayContextResponse> {
  return getJson<RelayContextResponse>(`/api/v1/neta/relay/context/${tdSectionSourceId}`)
}

export async function fetchRelaySettings(tdSectionSourceId: number): Promise<RelaySettingsResponse> {
  return getJson<RelaySettingsResponse>(`/api/v1/neta/relay/settings/${tdSectionSourceId}`)
}

export async function fetchRelayPlot(request: RelayPlotRequest): Promise<RelayPlotResponse> {
  return postJson<RelayPlotResponse>('/api/v1/neta/relay/plot-tcc', request)
}
