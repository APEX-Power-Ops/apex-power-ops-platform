'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  AvailableSettingsResponse,
  BreakerFamily,
  BreakerResourcesError,
  CascadePlugOption,
  CascadeResponse,
  CascadeSensor,
  CatalogStatusResponse,
  DelayBandOption,
  EMTFrameSearchResponse,
  EtuBreakerCascadeResponse,
  EMTSectionSettingsResponse,
  EtuPlotRequest,
  EtuSearchResult,
  EtuSearchResponse,
  TMTFrameSearchResponse,
  TMTPlotRequest,
  TMTSettingsResponse,
  fetchCascade,
  fetchCatalogStatus,
  fetchEmtContext,
  fetchEmtFacets,
  fetchEmtFrames,
  fetchEmtPlot,
  fetchEmtSettings,
  fetchEtuBreakerCascade,
  fetchEtuContext,
  fetchEtuPlot,
  fetchEtuSearch,
  fetchEtuSettings,
  fetchTmtContext,
  fetchTmtFacets,
  fetchTmtFrames,
  fetchTmtPlot,
  fetchTmtSettings,
} from '../lib/breaker-resources'
import {
  BreakerFacetPanel,
  BreakerSelectionData,
  BreakerSelectionPanel,
  EmtSearchCard,
  EtuSearchCard,
  TmtSearchCard,
} from './breaker-selection-panels'

const familyLabels: Record<BreakerFamily, string> = {
  etu: 'ETU',
  tmt: 'TMT',
  emt: 'EMT',
}

const defaultQueries: Record<BreakerFamily, string> = {
  etu: '',
  tmt: '',
  emt: '',
}

function toResultId(value: number) {
  return String(value)
}

function toOptionalNumber(value: string) {
  const normalized = value.trim()
  if (normalized.length === 0) {
    return null
  }

  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

function firstFiniteNumber(values: number[]) {
  return values.find((value) => Number.isFinite(value)) ?? null
}

function firstDelayValue(options: DelayBandOption[]) {
  const defaultOption = options.find((option) => option.is_default)
  return defaultOption?.open_time ?? options[0]?.open_time ?? null
}

function optionalNumber(target: object, key: string, value: number | null) {
  if (value !== null && Number.isFinite(value)) {
    const mutableTarget = target as Record<string, number>
    mutableTarget[key] = value
  }
}

function cascadeSensorToSearchResult(sensor: CascadeSensor, plugValues: CascadePlugOption[]): EtuSearchResult {
  return {
    sensor_id: sensor.sensor_id,
    sensor_rating: sensor.sensor_rating,
    sensor_desc: sensor.sensor_desc,
    trip_style_id: sensor.trip_style_id,
    trip_style_name: sensor.trip_style_name,
    trip_type_id: sensor.trip_type_id,
    trip_type_name: sensor.trip_type_name,
    manufacturer_id: sensor.manufacturer_id,
    manufacturer_name: sensor.manufacturer_name,
    compatible_plug_values: plugValues.map((option) => option.plug_value),
  }
}

function fetchCountLabel<T extends { count: number }>(
  response: T | null,
  isLoading: boolean,
  errorMessage: string | null,
) {
  if (isLoading) {
    return 'loading'
  }
  if (errorMessage || response === null) {
    return 'unavailable'
  }
  return `${response.count} matches`
}

function buildEtuPlotRequest(settings: AvailableSettingsResponse, contextLabel: string | null): EtuPlotRequest | null {
  const plugRating = firstFiniteNumber(settings.plug_values)
  if (plugRating === null) {
    return null
  }

  const request: EtuPlotRequest = {
    sensor_id: settings.sensor_id,
    plug_rating: plugRating,
    maint_mode: false,
    include_nominal_curve: true,
    include_expected_markers: true,
    include_measured_markers: false,
  }

  optionalNumber(request, 'ltpu_setting', firstFiniteNumber(settings.ltpu_settings))
  optionalNumber(request, 'stpu_setting', firstFiniteNumber(settings.stpu_settings))
  optionalNumber(request, 'inst_setting', firstFiniteNumber(settings.inst_settings))
  optionalNumber(request, 'gfpu_setting', firstFiniteNumber(settings.gfpu_settings))

  const ltdDelay = firstDelayValue(settings.ltd_settings)
  const stdDelay = firstDelayValue(settings.std_settings)
  const gfdDelay = firstDelayValue(settings.gfd_settings)
  optionalNumber(request, 'ltd_delay_setting', ltdDelay)
  optionalNumber(request, 'std_delay_setting', stdDelay)
  optionalNumber(request, 'gfd_delay_setting', gfdDelay)
  optionalNumber(request, 'ltd_test_multiple', ltdDelay === null ? null : 3)
  optionalNumber(request, 'std_test_multiple', stdDelay === null ? null : 1.5)
  optionalNumber(request, 'gfd_test_multiple', gfdDelay === null ? null : 1.5)

  if (contextLabel) {
    request.breaker_context_label = contextLabel
    request.breaker_context_source = 'operations_web_breaker_explorer'
  }

  return request
}

function buildTmtPlotRequest(frameId: number, settings: TMTSettingsResponse) {
  const tripClass = firstFiniteNumber(settings.available_trip_classes)
  if (tripClass === null) {
    return null
  }

  const request: TMTPlotRequest = {
    frame_id: frameId,
    trip_class: tripClass,
    include_raw_points: false,
    num_output_points: 36,
  }
  const ampRating = settings.amp_ratings.find((option) => Number.isFinite(option.rating))?.rating ?? null
  const settingValue = settings.settings.find((option) => option.value !== null && Number.isFinite(option.value))?.value ?? null
  const thermalAdjustment = firstFiniteNumber(settings.thermal_adjustments)

  optionalNumber(request, 'amp_rating', ampRating)
  optionalNumber(request, 'setting_value', settingValue)
  optionalNumber(request, 'thermal_adjustment', thermalAdjustment)

  return request
}

function buildEmtPlotRequest(settings: EMTSectionSettingsResponse | null) {
  if (!settings) {
    return null
  }

  const band = settings.bands.find((option) => option.curve_point_count > 0) ?? settings.bands[0]
  if (!band) {
    return null
  }

  return {
    section_id: settings.section_id,
    band_id: band.band_id,
  }
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof BreakerResourcesError ? error.message : fallback
}

export function BreakerResourceExplorer() {
  const [family, setFamily] = useState<BreakerFamily>('etu')
  const [query, setQuery] = useState(defaultQueries.etu)
  const [tmtBreakerClass, setTmtBreakerClass] = useState('MCCB')
  const [catalogStatus, setCatalogStatus] = useState<CatalogStatusResponse | null>(null)
  const [catalogError, setCatalogError] = useState<string | null>(null)
  const [isCatalogLoading, setIsCatalogLoading] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [isLoadingSelection, setIsLoadingSelection] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState('')
  const [etuResults, setEtuResults] = useState<EtuSearchResponse | null>(null)
  const [tmtResults, setTmtResults] = useState<TMTFrameSearchResponse | null>(null)
  const [emtResults, setEmtResults] = useState<EMTFrameSearchResponse | null>(null)
  const [tmtFacets, setTmtFacets] = useState<Awaited<ReturnType<typeof fetchTmtFacets>> | null>(null)
  const [emtFacets, setEmtFacets] = useState<Awaited<ReturnType<typeof fetchEmtFacets>> | null>(null)
  const [selection, setSelection] = useState<BreakerSelectionData | null>(null)
  const [breakerAxis, setBreakerAxis] = useState<EtuBreakerCascadeResponse | null>(null)
  const [breakerAxisError, setBreakerAxisError] = useState<string | null>(null)
  const [isBreakerAxisLoading, setIsBreakerAxisLoading] = useState(false)
  const [breakerManufacturerId, setBreakerManufacturerId] = useState('')
  const [breakerClass, setBreakerClass] = useState('')
  const [breakerId, setBreakerId] = useState('')
  const [breakerStyleId, setBreakerStyleId] = useState('')
  const [etuCascade, setEtuCascade] = useState<CascadeResponse | null>(null)
  const [etuCascadeError, setEtuCascadeError] = useState<string | null>(null)
  const [isEtuCascadeLoading, setIsEtuCascadeLoading] = useState(false)
  const [etuManufacturerId, setEtuManufacturerId] = useState('')
  const [etuTripTypeId, setEtuTripTypeId] = useState('')
  const [etuTripStyleId, setEtuTripStyleId] = useState('')
  const [etuSensorId, setEtuSensorId] = useState('')

  useEffect(() => {
    let cancelled = false

    setIsCatalogLoading(true)
    fetchCatalogStatus()
      .then((status) => {
        if (!cancelled) {
          setCatalogStatus(status)
          setCatalogError(null)
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setCatalogStatus(null)
          setCatalogError(getErrorMessage(error, 'The governed catalog status route could not be reached.'))
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsCatalogLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  const breakerManufacturerFilter = useMemo(() => toOptionalNumber(breakerManufacturerId), [breakerManufacturerId])
  const breakerIdFilter = useMemo(() => toOptionalNumber(breakerId), [breakerId])
  const breakerStyleIdFilter = useMemo(() => toOptionalNumber(breakerStyleId), [breakerStyleId])
  const etuManufacturerFilter = useMemo(() => toOptionalNumber(etuManufacturerId), [etuManufacturerId])
  const etuTripTypeFilter = useMemo(() => toOptionalNumber(etuTripTypeId), [etuTripTypeId])
  const etuTripStyleFilter = useMemo(() => toOptionalNumber(etuTripStyleId), [etuTripStyleId])
  const etuSensorFilter = useMemo(() => toOptionalNumber(etuSensorId), [etuSensorId])
  const selectedCascadeSensor = useMemo(
    () => etuCascade?.sensors.find((sensor) => toResultId(sensor.sensor_id) === etuSensorId) ?? null,
    [etuCascade, etuSensorId],
  )
  const selectedGuidedEtuResult = useMemo(
    () => (selectedCascadeSensor ? cascadeSensorToSearchResult(selectedCascadeSensor, etuCascade?.plug_values ?? []) : null),
    [etuCascade?.plug_values, selectedCascadeSensor],
  )
  const selectedEtuResult = useMemo<EtuSearchResult | null>(() => {
    if (family !== 'etu' || !selectedId) {
      return null
    }
    if (selectedGuidedEtuResult && toResultId(selectedGuidedEtuResult.sensor_id) === selectedId) {
      return selectedGuidedEtuResult
    }
    return etuResults?.results.find((result) => toResultId(result.sensor_id) === selectedId) ?? null
  }, [etuResults, family, selectedGuidedEtuResult, selectedId])
  const etuResourceOptions = useMemo(() => {
    const results = etuResults?.results ?? []
    if (!selectedGuidedEtuResult) {
      return results
    }
    if (results.some((result) => result.sensor_id === selectedGuidedEtuResult.sensor_id)) {
      return results
    }
    return [selectedGuidedEtuResult, ...results]
  }, [etuResults, selectedGuidedEtuResult])
  const resultCount = useMemo(() => {
    if (family === 'etu') {
      return etuResults?.count ?? 0
    }
    if (family === 'tmt') {
      return tmtResults?.count ?? 0
    }
    return emtResults?.count ?? 0
  }, [emtResults, etuResults, family, tmtResults])
  const displayResultCount = family === 'etu' && selectedGuidedEtuResult && resultCount === 0 ? 1 : resultCount
  const hasResultRows = displayResultCount > 0
  const breakerAxisCountLabel = fetchCountLabel(breakerAxis, isBreakerAxisLoading, breakerAxisError)
  const etuCascadeCountLabel = fetchCountLabel(etuCascade, isEtuCascadeLoading, etuCascadeError)
  const selectedBreakerStyle = useMemo(
    () => breakerAxis?.breaker_styles.find((style) => toResultId(style.breaker_style_id) === breakerStyleId) ?? null,
    [breakerAxis, breakerStyleId],
  )
  const selectedBreakerContextLabel = selectedBreakerStyle
    ? `${selectedBreakerStyle.breaker_name} · ${selectedBreakerStyle.breaker_style_name}`
    : null

  useEffect(() => {
    if (family !== 'etu') {
      return
    }

    let cancelled = false

    setIsEtuCascadeLoading(true)
    fetchCascade({
      manufacturerId: etuManufacturerFilter,
      tripTypeId: etuTripTypeFilter,
      tripStyleId: etuTripStyleFilter,
      sensorId: etuSensorFilter,
      breakerClass: breakerClass || null,
      breakerId: breakerIdFilter,
      breakerStyleId: breakerStyleIdFilter,
    })
      .then((cascade) => {
        if (!cancelled) {
          setEtuCascade(cascade)
          setEtuCascadeError(null)
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setEtuCascade(null)
          setEtuCascadeError(getErrorMessage(error, 'The guided ETU cascade could not be reached.'))
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsEtuCascadeLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [
    breakerClass,
    breakerIdFilter,
    breakerStyleIdFilter,
    etuManufacturerFilter,
    etuSensorFilter,
    etuTripStyleFilter,
    etuTripTypeFilter,
    family,
  ])

  useEffect(() => {
    let cancelled = false

    setIsBreakerAxisLoading(true)
    fetchEtuBreakerCascade({
      manufacturerId: breakerManufacturerFilter,
      breakerClass: breakerClass || null,
      breakerId: breakerIdFilter,
      breakerStyleId: breakerStyleIdFilter,
      tripTypeId: selectedEtuResult?.trip_type_id ?? null,
      tripStyleId: selectedEtuResult?.trip_style_id ?? null,
      sensorId: selectedEtuResult?.sensor_id ?? null,
    })
      .then((cascade) => {
        if (!cancelled) {
          setBreakerAxis(cascade)
          setBreakerAxisError(null)
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setBreakerAxis(null)
          setBreakerAxisError(getErrorMessage(error, 'The breaker construction cascade could not be reached.'))
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsBreakerAxisLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [
    breakerClass,
    breakerIdFilter,
    breakerManufacturerFilter,
    breakerStyleIdFilter,
    selectedEtuResult?.sensor_id,
    selectedEtuResult?.trip_style_id,
    selectedEtuResult?.trip_type_id,
  ])

  function resetFamilyState(nextFamily: BreakerFamily) {
    setFamily(nextFamily)
    setQuery(defaultQueries[nextFamily])
    setSelectedId('')
    setSelection(null)
    setErrorMessage(null)
    setEtuResults(null)
    setTmtResults(null)
    setEmtResults(null)
    setTmtFacets(null)
    setEmtFacets(null)
    setEtuManufacturerId('')
    setEtuTripTypeId('')
    setEtuTripStyleId('')
    setEtuSensorId('')
  }

  function clearEtuGuidedPath() {
    setEtuManufacturerId('')
    setEtuTripTypeId('')
    setEtuTripStyleId('')
    setEtuSensorId('')
    setEtuResults(null)
  }

  function handleBreakerManufacturerChange(value: string) {
    setBreakerManufacturerId(value)
    setBreakerClass('')
    setBreakerId('')
    setBreakerStyleId('')
    setSelectedId('')
    setSelection(null)
    clearEtuGuidedPath()
  }

  function handleBreakerClassChange(value: string) {
    setBreakerClass(value)
    setBreakerId('')
    setBreakerStyleId('')
    setSelectedId('')
    setSelection(null)
    clearEtuGuidedPath()
  }

  function handleBreakerIdChange(value: string) {
    setBreakerId(value)
    setBreakerStyleId('')
    setSelectedId('')
    setSelection(null)
    clearEtuGuidedPath()
  }

  function handleBreakerStyleChange(value: string) {
    setBreakerStyleId(value)
    setSelectedId('')
    setSelection(null)
    setEtuSensorId('')
    setEtuResults(null)
  }

  function handleEtuManufacturerChange(value: string) {
    setEtuManufacturerId(value)
    setEtuTripTypeId('')
    setEtuTripStyleId('')
    setEtuSensorId('')
    setSelectedId('')
    setSelection(null)
    setEtuResults(null)
  }

  function handleEtuTripTypeChange(value: string) {
    setEtuTripTypeId(value)
    setEtuTripStyleId('')
    setEtuSensorId('')
    setSelectedId('')
    setSelection(null)
    setEtuResults(null)
  }

  function handleEtuTripStyleChange(value: string) {
    setEtuTripStyleId(value)
    setEtuSensorId('')
    setSelectedId('')
    setSelection(null)
    setEtuResults(null)
  }

  function handleEtuSensorChange(value: string) {
    setEtuSensorId(value)
    setSelectedId(value)
    setSelection(null)
    setEtuResults(null)
  }

  function handleSelectedResourceChange(value: string) {
    setSelectedId(value)
    setSelection(null)
    if (family === 'etu') {
      const cascadeHasSensor = (etuCascade?.sensors ?? []).some((sensor) => toResultId(sensor.sensor_id) === value)
      setEtuSensorId(cascadeHasSensor ? value : '')
    }
  }

  async function handleBrowse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const normalizedQuery = query.trim()
    setErrorMessage(null)
    setSelectedId('')
    setSelection(null)
    setEtuSensorId('')
    setIsSearching(true)

    try {
      if (family === 'etu') {
        const response = await fetchEtuSearch(normalizedQuery, {
          manufacturerId: breakerManufacturerFilter,
        })
        setEtuResults(response)
        setTmtResults(null)
        setEmtResults(null)
        setTmtFacets(null)
        setEmtFacets(null)
        return
      }

      if (family === 'tmt') {
        const effectiveBreakerClass = breakerClass || tmtBreakerClass
        const [facetsResponse, framesResponse] = await Promise.all([
          fetchTmtFacets(effectiveBreakerClass),
          fetchTmtFrames({
            breakerClass: effectiveBreakerClass,
            manufacturerId: breakerManufacturerFilter,
            manufacturerName: normalizedQuery || undefined,
          }),
        ])
        setTmtFacets(facetsResponse)
        setTmtResults(framesResponse)
        setEtuResults(null)
        setEmtResults(null)
        setEmtFacets(null)
        return
      }

      const [facetsResponse, framesResponse] = await Promise.all([
        fetchEmtFacets(),
        fetchEmtFrames(normalizedQuery, {
          manufacturerId: breakerManufacturerFilter,
        }),
      ])
      setEmtFacets(facetsResponse)
      setEmtResults(framesResponse)
      setEtuResults(null)
      setTmtResults(null)
      setTmtFacets(null)
    } catch (error) {
      setEtuResults(null)
      setTmtResults(null)
      setEmtResults(null)
      setTmtFacets(null)
      setEmtFacets(null)
      setErrorMessage(getErrorMessage(error, 'The governed breaker resource routes could not be reached.'))
    } finally {
      setIsSearching(false)
    }
  }

  async function handleLoadSelection() {
    setErrorMessage(null)

    if (!selectedId) {
      const article = family === 'etu' ? 'an' : 'a'
      setErrorMessage(`Select ${article} ${familyLabels[family]} result before loading context, settings, and plot data.`)
      return
    }

    setIsLoadingSelection(true)

    try {
      if (family === 'etu') {
        const searchResult = selectedEtuResult
        if (!searchResult) {
          setErrorMessage('The selected ETU sensor is no longer present in the current guided cascade or browse results.')
          return
        }

        const [context, settings, breakerCascade] = await Promise.all([
          fetchEtuContext(searchResult.sensor_id),
          fetchEtuSettings(searchResult.sensor_id),
          fetchEtuBreakerCascade({
            manufacturerId: breakerManufacturerFilter ?? searchResult.manufacturer_id,
            breakerClass: breakerClass || null,
            breakerId: breakerIdFilter,
            breakerStyleId: breakerStyleIdFilter,
            tripTypeId: searchResult.trip_type_id,
            tripStyleId: searchResult.trip_style_id,
            sensorId: searchResult.sensor_id,
          }),
        ])
        const contextLabel =
          selectedBreakerContextLabel ??
          context.resolved_equipment?.breaker_context?.label ??
          context.trip_style_name
        const plotRequest = buildEtuPlotRequest(settings, contextLabel)
        const plot = plotRequest ? await fetchEtuPlot(plotRequest) : null

        setSelection({
          family: 'etu',
          searchResult,
          context,
          settings,
          breakerCascade,
          plot,
          plotRequest,
        })
        return
      }

      if (family === 'tmt') {
        const frame = tmtResults?.frames.find((result) => toResultId(result.frame_id) === selectedId)
        if (!frame) {
          setErrorMessage('The selected TMT frame is no longer present in the current browse results.')
          return
        }

        const [context, settings] = await Promise.all([
          fetchTmtContext(frame.frame_id),
          fetchTmtSettings(frame.frame_id),
        ])
        const plotRequest = buildTmtPlotRequest(frame.frame_id, settings)
        const plot = plotRequest ? await fetchTmtPlot(plotRequest) : null

        setSelection({
          family: 'tmt',
          frame,
          context,
          settings,
          plot,
          plotRequest,
        })
        return
      }

      const frame = emtResults?.frames.find((result) => toResultId(result.frame_id) === selectedId)
      if (!frame) {
        setErrorMessage('The selected EMT frame is no longer present in the current browse results.')
        return
      }

      const context = await fetchEmtContext(frame.frame_id)
      const section =
        context.sections.find((candidate) => candidate.band_count > 0) ??
        context.sections.find((candidate) => candidate.pickup_count > 0) ??
        context.sections[0]
      const settings = section ? await fetchEmtSettings(section.section_id) : null
      const plotRequest = buildEmtPlotRequest(settings)
      const plot = plotRequest ? await fetchEmtPlot(plotRequest) : null

      setSelection({
        family: 'emt',
        frame,
        context,
        settings,
        plot,
        plotRequest,
      })
    } catch (error) {
      setSelection(null)
      setErrorMessage(getErrorMessage(error, 'The selected breaker resource could not be loaded from the governed routes.'))
    } finally {
      setIsLoadingSelection(false)
    }
  }

  function handleClearSelection() {
    setErrorMessage(null)
    setSelectedId('')
    setSelection(null)
    if (family === 'etu') {
      setEtuSensorId('')
    }
  }

  function handleResetBrowse() {
    resetFamilyState(family)
  }

  return (
    <section className="resource-lane-card" data-breaker-resource-explorer>
      <div className="resource-lane-header">
        <div>
          <p className="eyebrow">Breaker Resource Browser</p>
          <h2>Browse breaker resources through ETU, TMT, and EMT routes.</h2>
        </div>
        <p className="resource-lane-copy">
          This browser slice is read-only and renders only server-returned context, settings, and static curve points.
        </p>
      </div>

      <div className="resource-summary breaker-catalog-summary">
        <div>
          <span className="resource-summary-label">Catalog</span>
          <strong>{isCatalogLoading ? 'Checking' : catalogStatus?.catalog ?? 'Unknown'}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Manufacturers</span>
          <strong>{catalogStatus?.manufacturer_count ?? 'n/a'}</strong>
        </div>
        <div>
          <span className="resource-summary-label">ETU sensors</span>
          <strong>{catalogStatus?.sensor_count ?? 'n/a'}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Active family</span>
          <strong>{familyLabels[family]}</strong>
        </div>
      </div>

      {catalogError ? <p className="resource-banner resource-banner-error">{catalogError}</p> : null}

      <form className="resource-form breaker-resource-form" onSubmit={handleBrowse}>
        <div className="breaker-axis-panel" data-breaker-axis="breaker">
          <div className="resource-item-row">
            <span className="resource-chip">Axis 1</span>
            <span className="resource-chip resource-chip-muted">Breaker</span>
            <span className="resource-chip resource-chip-muted">{breakerAxisCountLabel}</span>
          </div>
          <div className="breaker-control-grid breaker-axis-control-grid">
            <label className="relay-selection-field" htmlFor="breaker-axis-manufacturer">
              <span className="resource-field">Breaker Manufacturer</span>
              <select
                id="breaker-axis-manufacturer"
                name="breakerAxisManufacturer"
                value={breakerManufacturerId}
                onChange={(event) => handleBreakerManufacturerChange(event.target.value)}
              >
                <option value="">Any manufacturer</option>
                {(breakerAxis?.manufacturers ?? []).map((manufacturer) => (
                  <option key={manufacturer.manufacturer_id} value={toResultId(manufacturer.manufacturer_id)}>
                    {manufacturer.manufacturer_name} ({manufacturer.breaker_count})
                  </option>
                ))}
              </select>
            </label>

            <label className="relay-selection-field" htmlFor="breaker-axis-class">
              <span className="resource-field">Breaker Class</span>
              <select
                id="breaker-axis-class"
                name="breakerAxisClass"
                value={breakerClass}
                onChange={(event) => handleBreakerClassChange(event.target.value)}
              >
                <option value="">Any class</option>
                {(breakerAxis?.breaker_classes ?? []).map((option) => (
                  <option key={option.breaker_class} value={option.breaker_class}>
                    {option.breaker_class} ({option.breaker_count})
                  </option>
                ))}
              </select>
            </label>

            <label className="relay-selection-field" htmlFor="breaker-axis-breaker">
              <span className="resource-field">Breaker</span>
              <select
                id="breaker-axis-breaker"
                name="breakerAxisBreaker"
                value={breakerId}
                onChange={(event) => handleBreakerIdChange(event.target.value)}
              >
                <option value="">Any breaker</option>
                {(breakerAxis?.breakers ?? []).map((option) => (
                  <option key={option.breaker_id} value={toResultId(option.breaker_id)}>
                    {option.manufacturer_name} · {option.breaker_name} ({option.style_count})
                  </option>
                ))}
              </select>
            </label>

            <label className="relay-selection-field" htmlFor="breaker-axis-style">
              <span className="resource-field">Breaker Style</span>
              <select
                id="breaker-axis-style"
                name="breakerAxisStyle"
                value={breakerStyleId}
                onChange={(event) => handleBreakerStyleChange(event.target.value)}
              >
                <option value="">Any style</option>
                {(breakerAxis?.breaker_styles ?? []).map((style) => (
                  <option key={style.breaker_style_id} value={toResultId(style.breaker_style_id)}>
                    {style.breaker_name} · {style.breaker_style_name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {breakerAxisError ? <p className="resource-banner resource-banner-error relay-inline-banner">{breakerAxisError}</p> : null}
        </div>

        <div className="breaker-axis-panel" data-breaker-axis="trip-unit">
          <div className="resource-item-row">
            <span className="resource-chip">Axis 2</span>
            <span className="resource-chip resource-chip-muted">Trip unit</span>
            {family === 'etu' ? <span className="resource-chip resource-chip-muted">{etuCascadeCountLabel}</span> : null}
            {breakerManufacturerFilter !== null ? (
              <span className="resource-chip resource-chip-muted">manufacturer filtered</span>
            ) : null}
          </div>
          <div className={`breaker-control-grid${family === 'etu' ? ' breaker-etu-cascade-grid' : ''}`}>
            <label className="relay-selection-field" htmlFor="breaker-family">
              <span className="resource-field">Trip Unit Type</span>
              <select
                id="breaker-family"
                name="breakerFamily"
                value={family}
                onChange={(event) => resetFamilyState(event.target.value as BreakerFamily)}
              >
                <option value="etu">ETU sensors</option>
                <option value="tmt">TMT frames</option>
                <option value="emt">EMT frames</option>
              </select>
            </label>

            {family === 'etu' ? (
              <>
                <label className="relay-selection-field" htmlFor="etu-cascade-manufacturer">
                  <span className="resource-field">Trip Manufacturer</span>
                  <select
                    id="etu-cascade-manufacturer"
                    name="etuCascadeManufacturer"
                    value={etuManufacturerId}
                    onChange={(event) => handleEtuManufacturerChange(event.target.value)}
                  >
                    <option value="">Choose manufacturer</option>
                    {(etuCascade?.manufacturers ?? []).map((manufacturer) => (
                      <option key={manufacturer.manufacturer_id} value={toResultId(manufacturer.manufacturer_id)}>
                        {manufacturer.manufacturer_name} ({manufacturer.trip_type_count})
                      </option>
                    ))}
                  </select>
                </label>

                <label className="relay-selection-field" htmlFor="etu-cascade-trip-type">
                  <span className="resource-field">Trip Type</span>
                  <select
                    id="etu-cascade-trip-type"
                    name="etuCascadeTripType"
                    value={etuTripTypeId}
                    onChange={(event) => handleEtuTripTypeChange(event.target.value)}
                    disabled={!etuManufacturerId}
                  >
                    <option value="">{etuManufacturerId ? 'Choose trip type' : 'Select manufacturer first'}</option>
                    {etuManufacturerId
                      ? (etuCascade?.trip_types ?? []).map((tripType) => (
                          <option key={tripType.trip_type_id} value={toResultId(tripType.trip_type_id)}>
                            {tripType.trip_type_name} ({tripType.trip_style_count})
                          </option>
                        ))
                      : null}
                  </select>
                </label>

                <label className="relay-selection-field" htmlFor="etu-cascade-trip-style">
                  <span className="resource-field">Trip Style</span>
                  <select
                    id="etu-cascade-trip-style"
                    name="etuCascadeTripStyle"
                    value={etuTripStyleId}
                    onChange={(event) => handleEtuTripStyleChange(event.target.value)}
                    disabled={!etuTripTypeId}
                  >
                    <option value="">{etuTripTypeId ? 'Choose trip style' : 'Select trip type first'}</option>
                    {etuTripTypeId
                      ? (etuCascade?.trip_styles ?? []).map((tripStyle) => (
                          <option key={tripStyle.trip_style_id} value={toResultId(tripStyle.trip_style_id)}>
                            {tripStyle.trip_style_name} ({tripStyle.sensor_count})
                          </option>
                        ))
                      : null}
                  </select>
                </label>

                <label className="relay-selection-field" htmlFor="etu-cascade-sensor">
                  <span className="resource-field">Sensor</span>
                  <select
                    id="etu-cascade-sensor"
                    name="etuCascadeSensor"
                    value={etuSensorId}
                    onChange={(event) => handleEtuSensorChange(event.target.value)}
                    disabled={!etuTripStyleId}
                  >
                    <option value="">{etuTripStyleId ? 'Choose sensor' : 'Select trip style first'}</option>
                    {etuTripStyleId
                      ? (etuCascade?.sensors ?? []).map((sensor) => (
                          <option key={sensor.sensor_id} value={toResultId(sensor.sensor_id)}>
                            {sensor.sensor_id} · {sensor.sensor_desc} · {sensor.sensor_rating ?? 'n/a'}A
                          </option>
                        ))
                      : null}
                  </select>
                </label>
              </>
            ) : (
              <>
                <label className="relay-selection-field" htmlFor="breaker-query">
                  <span className="resource-field">{family === 'tmt' ? 'TMT manufacturer' : 'EMT search'}</span>
                  <input
                    id="breaker-query"
                    name="breakerQuery"
                    type="text"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder={family === 'tmt' ? 'ABB, Eaton' : 'SOC, frame, style'}
                    autoComplete="off"
                    spellCheck={false}
                  />
                </label>

                {family === 'tmt' ? (
                  <label className="relay-selection-field" htmlFor="tmt-breaker-class">
                    <span className="resource-field">TMT class</span>
                    <select
                      id="tmt-breaker-class"
                      name="tmtBreakerClass"
                      value={tmtBreakerClass}
                      onChange={(event) => setTmtBreakerClass(event.target.value)}
                    >
                      <option value="MCCB">MCCB</option>
                      <option value="ICCB">ICCB</option>
                      <option value="PCB">PCB</option>
                    </select>
                  </label>
                ) : null}

                <div className="breaker-form-actions">
                  <button type="submit" disabled={isSearching}>
                    {isSearching ? 'Browsing...' : `Browse ${familyLabels[family]}`}
                  </button>
                  <button type="button" onClick={handleResetBrowse} disabled={isSearching || isLoadingSelection}>
                    Reset
                  </button>
                </div>
              </>
            )}
          </div>

          {family === 'etu' ? (
            <div className="breaker-control-grid breaker-etu-fallback-grid">
              <label className="relay-selection-field" htmlFor="breaker-query">
                <span className="resource-field">ETU search fallback</span>
                <input
                  id="breaker-query"
                  name="breakerQuery"
                  type="text"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="GE, Square D, trip style"
                  autoComplete="off"
                  spellCheck={false}
                />
              </label>

              <div className="breaker-form-actions">
                <button type="submit" disabled={isSearching}>
                  {isSearching ? 'Browsing...' : 'Browse ETU'}
                </button>
                <button type="button" onClick={handleResetBrowse} disabled={isSearching || isLoadingSelection}>
                  Reset
                </button>
              </div>
            </div>
          ) : null}
          {etuCascadeError && family === 'etu' ? (
            <p className="resource-banner resource-banner-error relay-inline-banner">{etuCascadeError}</p>
          ) : null}
        </div>
      </form>

      {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

      {!hasResultRows && !errorMessage ? (
        <p className="resource-banner resource-banner-neutral">
          Browse a trip unit type, select one returned row, then load the governed context, settings, and static trip curve.
        </p>
      ) : null}

      {tmtFacets ? (
        <BreakerFacetPanel
          title="TMT facet snapshot"
          total={tmtFacets.total_matching_frames}
          facets={tmtFacets.facets}
        />
      ) : null}

      {emtFacets ? (
        <BreakerFacetPanel
          title="EMT facet snapshot"
          total={emtFacets.total_matching_frames}
          facets={emtFacets.facets}
        />
      ) : null}

      {hasResultRows ? (
        <div className="resource-results">
          <div className="resource-summary breaker-result-summary">
            <div>
              <span className="resource-summary-label">Browse matches</span>
              <strong>{displayResultCount}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Selected row</span>
              <strong>{selectedId || 'Choose explicitly'}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Loaded selection</span>
              <strong>{selection ? familyLabels[selection.family] : 'None'}</strong>
            </div>
          </div>

          <div className="relay-selection-controls breaker-selection-controls">
            <label className="relay-selection-field" htmlFor="breaker-selected-resource">
              <span className="resource-field">{familyLabels[family]} resource</span>
              <select
                id="breaker-selected-resource"
                name="breakerSelectedResource"
                value={selectedId}
                onChange={(event) => handleSelectedResourceChange(event.target.value)}
              >
                <option value="">Select one row</option>
                {family === 'etu'
                  ? etuResourceOptions.map((result) => (
                      <option key={result.sensor_id} value={toResultId(result.sensor_id)}>
                        {result.sensor_id} · {result.manufacturer_name} · {result.trip_type_name} · {result.sensor_desc}
                      </option>
                    ))
                  : null}
                {family === 'tmt'
                  ? tmtResults?.frames.map((frame) => (
                      <option key={frame.frame_id} value={toResultId(frame.frame_id)}>
                        {frame.frame_id} · {frame.manufacturer_name ?? 'n/a'} · {frame.breaker_name ?? 'n/a'} · {frame.frame_size ?? 'n/a'}
                      </option>
                    ))
                  : null}
                {family === 'emt'
                  ? emtResults?.frames.map((frame) => (
                      <option key={frame.frame_id} value={toResultId(frame.frame_id)}>
                        {frame.frame_id} · {frame.manufacturer_name ?? 'n/a'} · {frame.type_name ?? 'n/a'} · {frame.frame_desc ?? 'n/a'}
                      </option>
                    ))
                  : null}
              </select>
            </label>

            <div className="relay-selection-actions breaker-selection-actions">
              <button type="button" onClick={handleLoadSelection} disabled={isLoadingSelection}>
                {isLoadingSelection ? 'Loading resource…' : 'Load Context + Curve'}
              </button>
              {selectedId || selection ? (
                <button type="button" onClick={handleClearSelection} disabled={isLoadingSelection}>
                  Clear
                </button>
              ) : null}
            </div>
          </div>

          <div className="breaker-search-results" data-breaker-results>
            {family === 'etu'
              ? etuResourceOptions.map((result) => (
                  <EtuSearchCard
                    key={result.sensor_id}
                    result={result}
                    selected={toResultId(result.sensor_id) === selectedId}
                  />
                ))
              : null}
            {family === 'tmt'
              ? tmtResults?.frames.map((frame) => (
                  <TmtSearchCard
                    key={frame.frame_id}
                    frame={frame}
                    selected={toResultId(frame.frame_id) === selectedId}
                  />
                ))
              : null}
            {family === 'emt'
              ? emtResults?.frames.map((frame) => (
                  <EmtSearchCard
                    key={frame.frame_id}
                    frame={frame}
                    selected={toResultId(frame.frame_id) === selectedId}
                  />
                ))
              : null}
          </div>

          {selection ? <BreakerSelectionPanel selection={selection} /> : null}
        </div>
      ) : null}
    </section>
  )
}
