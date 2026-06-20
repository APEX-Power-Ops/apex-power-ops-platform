'use client'

import { useState } from 'react'
import { fetchLearningResources, LearningResource, LearningResourcesError } from '../../lib/learning-resources'

export default function LearningDemoPage() {
  const [section, setSection] = useState('7.2.1.1')
  const [level, setLevel] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [resources, setResources] = useState<LearningResource[] | null>(null)

  async function run() {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const data = await fetchLearningResources(section.trim(), level || undefined, 20)
      setResources(data.resources)
    } catch (error) {
      setErrorMessage(
        error instanceof LearningResourcesError
          ? error.message
          : 'The learning resolver could not be reached.',
      )
      setResources([])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="shell-page">
      <section className="hero-card">
        <p className="eyebrow">Learning &rarr; Slice 1 demo</p>
        <h1>Contextual resources for a NETA section.</h1>
      </section>

      <section className="notes-card">
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <label>NETA section
            <input value={section} onChange={(e) => setSection(e.target.value)} placeholder="7.6.1.1.1" />
          </label>
          <label>Level
            <select value={level} onChange={(e) => setLevel(e.target.value)}>
              <option value="">Any</option>
              <option value="II">II</option>
              <option value="III">III</option>
              <option value="IV">IV</option>
            </select>
          </label>
          <button className="btn" onClick={run} disabled={isLoading}>Resolve</button>
        </div>

        {isLoading ? <p className="resource-banner resource-banner-neutral">Resolving&hellip;</p> : null}
        {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

        {resources && !isLoading && !errorMessage ? (
          <div className="resource-results">
            {resources.length === 0 ? (
              <p className="resource-banner resource-banner-neutral">No linked resources for this section yet.</p>
            ) : (
              <div className="resource-grid">
                {resources.map((r, i) => (
                  <article className="resource-item" key={i}>
                    <div className="resource-item-row">
                      <span className="resource-chip">{r.source === 'curated' ? 'Curated' : 'Section match'}</span>
                      {r.is_primary ? <span className="resource-chip">Primary</span> : null}
                      {r.is_mandatory ? <span className="resource-chip">Mandatory</span> : null}
                      {r.cert_level ? <span className="resource-chip">Level {r.cert_level}</span> : null}
                    </div>
                    <h3>{r.title}</h3>
                    <p>{r.why}</p>
                  </article>
                ))}
              </div>
            )}
          </div>
        ) : null}
      </section>
    </main>
  )
}
