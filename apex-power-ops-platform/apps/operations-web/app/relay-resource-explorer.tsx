'use client'

import { FormEvent, useState } from 'react'
import {
  RelayPlotRequest,
  RelayResourcesError,
  RelaySectionSearchResponse,
  RelaySettingsResponse,
  fetchRelayContext,
  fetchRelayPlot,
  fetchRelaySections,
  fetchRelaySettings,
} from '../lib/relay-resources'
import {
  RelayPrimaryDetail,
  RelaySearchCard,
  RelaySelectionData,
  RelaySelectionPanel,
  RelaySelectionSlot,
} from './relay-selection-panels'

const defaultCurrentMultiples = '2, 5, 10'

function parseCurrentMultiples(rawValue: string) {
  const parts = rawValue
    .split(',')
    .map((part) => Number(part.trim()))
    .filter((value) => Number.isFinite(value) && value > 1)

  return Array.from(new Set(parts))
}

function toSectionId(tdSectionSourceId: number) {
  return String(tdSectionSourceId)
}

function buildPlotRequest(
  tdSectionSourceId: number,
  settingsResult: RelaySettingsResponse,
  currentMultiples: number[],
): RelayPlotRequest | null {
  const previewOption = settingsResult.preview_options[0]
  if (!previewOption) {
    return null
  }

  const plotRequest: RelayPlotRequest = {
    td_section_source_id: tdSectionSourceId,
    current_multiples: currentMultiples,
    curve_parent_source_id: previewOption.curve_parent_source_id,
  }

  if (previewOption.curve_ordinal !== null) {
    plotRequest.curve_ordinal = previewOption.curve_ordinal
    plotRequest.time_dial = 1.0
  }
  if (previewOption.source_ordinal !== null) {
    plotRequest.source_ordinal = previewOption.source_ordinal
  }
  if (previewOption.time_dial !== null) {
    plotRequest.time_dial = previewOption.time_dial
  }

  return plotRequest
}

function collectSelectionWarnings(selection: RelaySelectionData) {
  const warnings = new Set<string>()

  if (!selection.section.supported) {
    warnings.add('Unsupported sections remain selectable for disclosure-only compare.')
  }

  if (selection.context.unsupported_reason) {
    warnings.add(selection.context.unsupported_reason)
  }

  if (selection.settings.unsupported_reason) {
    warnings.add(selection.settings.unsupported_reason)
  }

  if (selection.settings.preview_options.length > 1) {
    warnings.add(
      `Preview is currently showing the first published governed option out of ${selection.settings.preview_options.length} options for this TD-section.`,
    )
  }

  if (selection.plot?.meta.unsupported_reason) {
    warnings.add(selection.plot.meta.unsupported_reason)
  }

  for (const warning of selection.plot?.warnings ?? []) {
    warnings.add(warning)
  }

  if (!selection.plot && selection.settings.preview_options.length === 0) {
    warnings.add('No stored preview option is available for this TD-section in the governed API surface.')
  }

  return Array.from(warnings)
}

async function loadSelectionData(
  section: RelaySectionSearchResponse['sections'][number],
  slot: RelaySelectionSlot,
  currentMultiples: number[],
): Promise<RelaySelectionData> {
  const [contextResult, settingsResult] = await Promise.all([
    fetchRelayContext(section.td_section_source_id),
    fetchRelaySettings(section.td_section_source_id),
  ])

  const plotRequest = buildPlotRequest(section.td_section_source_id, settingsResult, currentMultiples)
  const plotResult = plotRequest ? await fetchRelayPlot(plotRequest) : null

  return {
    slot,
    section,
    context: contextResult,
    settings: settingsResult,
    plot: plotResult,
    currentMultiples,
  }
}

export function RelayResourceExplorer() {
  const [query, setQuery] = useState('SEL')
  const [currentMultiplesInput, setCurrentMultiplesInput] = useState(defaultCurrentMultiples)
  const [isSearching, setIsSearching] = useState(false)
  const [isLoadingSelection, setIsLoadingSelection] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [sections, setSections] = useState<RelaySectionSearchResponse | null>(null)
  const [primarySectionId, setPrimarySectionId] = useState('')
  const [compareSectionId, setCompareSectionId] = useState('')
  const [primarySelection, setPrimarySelection] = useState<RelaySelectionData | null>(null)
  const [compareSelection, setCompareSelection] = useState<RelaySelectionData | null>(null)

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setIsSearching(true)
    setErrorMessage(null)
    setPrimarySectionId('')
    setCompareSectionId('')
    setPrimarySelection(null)
    setCompareSelection(null)

    try {
      const searchResponse = await fetchRelaySections(query)
      setSections(searchResponse)
    } catch (error) {
      setSections(null)
      if (error instanceof RelayResourcesError) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage('The governed relay backend seam could not be reached from the browser shell.')
      }
    } finally {
      setIsSearching(false)
    }
  }

  async function handleLoadSelection() {
    if (!sections || sections.count === 0) {
      setErrorMessage('Search the governed relay catalog before loading relay details.')
      return
    }

    const currentMultiples = parseCurrentMultiples(currentMultiplesInput)
    if (currentMultiples.length === 0) {
      setErrorMessage('Enter relay current multiples greater than 1, separated by commas.')
      setPrimarySelection(null)
      setCompareSelection(null)
      return
    }

    if (!primarySectionId) {
      setErrorMessage('Select a primary TD-section before loading relay details.')
      return
    }

    if (compareSectionId && compareSectionId === primarySectionId) {
      setErrorMessage('Compare selection must stay distinct from the primary TD-section.')
      return
    }

    const primarySection = sections.sections.find(
      (section) => toSectionId(section.td_section_source_id) === primarySectionId,
    )
    const compareSection = sections.sections.find(
      (section) => toSectionId(section.td_section_source_id) === compareSectionId,
    )

    if (!primarySection) {
      setErrorMessage('The selected primary TD-section is no longer available in the current search results.')
      return
    }

    setIsLoadingSelection(true)
    setErrorMessage(null)

    try {
      const [loadedPrimary, loadedCompare] = await Promise.all([
        loadSelectionData(primarySection, 'primary', currentMultiples),
        compareSection ? loadSelectionData(compareSection, 'compare', currentMultiples) : Promise.resolve(null),
      ])

      setPrimarySelection(loadedPrimary)
      setCompareSelection(loadedCompare)
    } catch (error) {
      setPrimarySelection(null)
      setCompareSelection(null)
      if (error instanceof RelayResourcesError) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage('The governed relay backend seam could not be reached from the browser shell.')
      }
    } finally {
      setIsLoadingSelection(false)
    }
  }

  function handleClearSelection() {
    setErrorMessage(null)
    setPrimarySectionId('')
    setCompareSectionId('')
    setPrimarySelection(null)
    setCompareSelection(null)
  }

  const hasSelectionState = Boolean(primarySectionId || compareSectionId || primarySelection || compareSelection)

  return (
    <section className="resource-lane-card">
      <div className="resource-lane-header">
        <div>
          <p className="eyebrow">Tranche 5 Browser Consumer</p>
          <h2>Browse relay TD-sections through the governed control-plane routes.</h2>
        </div>
        <p className="resource-lane-copy">
          This browser slice stays read-only, preserves relay family identity, and surfaces unsupported behavior instead of hiding it.
        </p>
      </div>

      <form className="resource-form" onSubmit={handleSearch}>
        <div className="relay-form-grid">
          <label className="resource-field" htmlFor="relay-search-query">
            Relay search
          </label>
          <label className="resource-field" htmlFor="relay-current-multiples">
            Preview multiples
          </label>
        </div>
        <div className="resource-form-row relay-form-row">
          <input
            id="relay-search-query"
            name="relayQuery"
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="SEL, GE, IEC, feeder"
            autoComplete="off"
            spellCheck={false}
          />
          <input
            id="relay-current-multiples"
            name="relayCurrentMultiples"
            type="text"
            value={currentMultiplesInput}
            onChange={(event) => setCurrentMultiplesInput(event.target.value)}
            placeholder="2, 5, 10"
            autoComplete="off"
            spellCheck={false}
          />
          <button type="submit" disabled={isSearching}>
            {isSearching ? 'Searching…' : 'Search Relay Sections'}
          </button>
        </div>
      </form>

      {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

      {!sections && !errorMessage ? (
        <p className="resource-banner resource-banner-neutral">
          Search the governed relay catalog to choose one TD-section, then optionally add one compare section before loading any read-only relay context, settings, or preview data.
        </p>
      ) : null}

      {sections && sections.count === 0 ? (
        <p className="resource-banner resource-banner-neutral">
          No supported relay TD-sections matched the current search. Adjust the search term and try again.
        </p>
      ) : null}

      {sections && sections.count > 0 ? (
        <div className="resource-results">
          <div className="resource-summary relay-summary-grid relay-search-summary-grid">
            <div>
              <span className="resource-summary-label">Search matches</span>
              <strong>{sections.count}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Primary TD-section</span>
              <strong>{primarySectionId || 'Choose explicitly'}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Compare TD-section</span>
              <strong>{compareSectionId || 'Optional'}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Preview multiples</span>
              <strong>{currentMultiplesInput}</strong>
            </div>
          </div>

          <div className="relay-selection-controls">
            <label className="relay-selection-field" htmlFor="relay-primary-section">
              <span className="resource-field">Primary TD-section</span>
              <select
                id="relay-primary-section"
                name="relayPrimarySection"
                value={primarySectionId}
                onChange={(event) => {
                  const nextPrimary = event.target.value
                  setPrimarySectionId(nextPrimary)
                  if (nextPrimary === compareSectionId) {
                    setCompareSectionId('')
                  }
                }}
              >
                <option value="">Select one TD-section</option>
                {sections.sections.map((section) => (
                  <option key={section.td_section_source_id} value={toSectionId(section.td_section_source_id)}>
                    {section.td_section_source_id} · {section.td_section_name ?? 'Unnamed TD-section'} ·{' '}
                    {section.family_name} / {section.storage_kind}
                  </option>
                ))}
              </select>
            </label>

            <label className="relay-selection-field" htmlFor="relay-compare-section">
              <span className="resource-field">Compare TD-section</span>
              <select
                id="relay-compare-section"
                name="relayCompareSection"
                value={compareSectionId}
                onChange={(event) => setCompareSectionId(event.target.value)}
              >
                <option value="">No compare selection</option>
                {sections.sections.map((section) => (
                  <option
                    key={section.td_section_source_id}
                    value={toSectionId(section.td_section_source_id)}
                    disabled={toSectionId(section.td_section_source_id) === primarySectionId}
                  >
                    {section.td_section_source_id} · {section.td_section_name ?? 'Unnamed TD-section'} ·{' '}
                    {section.family_name} / {section.storage_kind}
                  </option>
                ))}
              </select>
            </label>

            <div className="relay-selection-actions">
              <button type="button" onClick={handleLoadSelection} disabled={isLoadingSelection}>
                {isLoadingSelection ? 'Loading selections…' : 'Load Selected Sections'}
              </button>
              {hasSelectionState ? (
                <button type="button" onClick={handleClearSelection} disabled={isLoadingSelection}>
                  Clear Relay Selection
                </button>
              ) : null}
            </div>
          </div>

          {!primarySelection ? (
            <p className="resource-banner resource-banner-neutral relay-inline-banner">
              Select a primary TD-section before the browser treats any relay preview as current.
            </p>
          ) : null}

          <div className="relay-search-results">
            {sections.sections.map((section) => {
              const sectionId = toSectionId(section.td_section_source_id)
              const isPrimary = sectionId === primarySectionId
              const isCompare = sectionId === compareSectionId

              return (
                <RelaySearchCard
                  key={section.td_section_source_id}
                  section={section}
                  isPrimary={isPrimary}
                  isCompare={isCompare}
                />
              )
            })}
          </div>

          {primarySelection ? (
            <>
              <RelayPrimaryDetail selection={primarySelection} />
              <div className={`relay-compare-grid${compareSelection ? ' relay-compare-grid-double' : ''}`}>
                <RelaySelectionPanel selection={primarySelection} />
                {compareSelection ? <RelaySelectionPanel selection={compareSelection} /> : null}
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}