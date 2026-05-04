'use client'

import { FormEvent, useState } from 'react'
import {
  ApparatusResourcesError,
  ApparatusStudyResourcesResponse,
  fetchApparatusStudyResources,
} from '../lib/apparatus-resources'

const uuidLikePattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

const emptyResult: ApparatusStudyResourcesResponse | null = null

export function ApparatusResourceExplorer() {
  const [apparatusId, setApparatusId] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [result, setResult] = useState<ApparatusStudyResourcesResponse | null>(emptyResult)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const normalizedId = apparatusId.trim()
    if (!uuidLikePattern.test(normalizedId)) {
      setErrorMessage('Enter a valid apparatus UUID to read the governed backend study-resource seam.')
      setResult(emptyResult)
      return
    }

    setIsLoading(true)
    setErrorMessage(null)

    try {
      const response = await fetchApparatusStudyResources(normalizedId)
      setResult(response)
    } catch (error) {
      setResult(emptyResult)
      if (error instanceof ApparatusResourcesError) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage('The governed backend seam could not be reached from the browser shell.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  function handleClear() {
    setApparatusId('')
    setErrorMessage(null)
    setResult(emptyResult)
  }

  return (
    <section className="resource-lane-card">
      <div className="resource-lane-header">
        <div>
          <p className="eyebrow">First Governed Consumer Seam</p>
          <h2>Read apparatus study resources through the control-plane API.</h2>
        </div>
        <p className="resource-lane-copy">
          This explorer uses the bounded backend route rather than reopening direct browser database access.
        </p>
      </div>

      <form className="resource-form" onSubmit={handleSubmit}>
        <label className="resource-field" htmlFor="apparatus-id">
          Apparatus UUID
        </label>
        <div className="resource-form-row">
          <input
            id="apparatus-id"
            name="apparatusId"
            type="text"
            value={apparatusId}
            onChange={(event) => setApparatusId(event.target.value)}
            placeholder="00000000-0000-0000-0000-000000000000"
            autoComplete="off"
            spellCheck={false}
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Loading…' : 'Load Resources'}
          </button>
          <button type="button" onClick={handleClear} disabled={isLoading}>
            Clear
          </button>
        </div>
      </form>

      {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

      {result ? (
        <div className="resource-results">
          <div className="resource-summary">
            <div>
              <span className="resource-summary-label">Apparatus</span>
              <strong>{result.apparatus_id}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Resources</span>
              <strong>{result.count}</strong>
            </div>
          </div>

          <div className="resource-grid">
            {result.resources.map((resource) => (
              <article className="resource-item" key={resource.resource_id}>
                <div className="resource-item-row">
                  <span className="resource-chip">{resource.resource_type}</span>
                  <span className="resource-chip resource-chip-muted">{resource.source_table}</span>
                </div>
                <h3>{resource.title}</h3>
                <p>{resource.description ?? 'No description has been published for this study resource yet.'}</p>
                <dl>
                  <div>
                    <dt>Level</dt>
                    <dd>{resource.level ?? 'Unspecified'}</dd>
                  </div>
                  <div>
                    <dt>Estimated minutes</dt>
                    <dd>{resource.estimated_minutes ?? 'Unknown'}</dd>
                  </div>
                  <div>
                    <dt>Slug</dt>
                    <dd>{resource.url_slug ?? 'Not published'}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        </div>
      ) : (
        <p className="resource-banner resource-banner-neutral">
          Enter an apparatus UUID to exercise the new governed backend route from the browser shell.
        </p>
      )}
    </section>
  )
}
