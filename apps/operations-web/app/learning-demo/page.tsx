'use client'

import { useEffect, useState } from 'react'
import { fetchLearningResources, LearningResource, LearningResourcesError } from '../../lib/learning-resources'
import {
  fetchLearningEvents,
  fetchLearningSections,
  fetchLearningUsers,
  LearningCaptureError,
  LearningEvent,
  LearningUser,
  recordLearningEvent,
} from '../../lib/learning-capture'

export default function LearningDemoPage() {
  const [section, setSection] = useState('7.2.1.1')
  const [level, setLevel] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [resources, setResources] = useState<LearningResource[] | null>(null)

  const [users, setUsers] = useState<LearningUser[]>([])
  const [userId, setUserId] = useState('')
  const [sections, setSections] = useState<string[]>([])
  const [events, setEvents] = useState<LearningEvent[]>([])
  const [captureMessage, setCaptureMessage] = useState<string | null>(null)
  const [confidence, setConfidence] = useState('3')
  const [score, setScore] = useState('80')

  useEffect(() => {
    fetchLearningUsers()
      .then((u) => {
        setUsers(u)
        if (u.length) setUserId((prev) => prev || u[0].id)
      })
      .catch(() => setUsers([]))
    fetchLearningSections().then(setSections).catch(() => setSections([]))
  }, [])

  async function refreshEvents(uid: string) {
    if (!uid) return
    try {
      setEvents(await fetchLearningEvents(uid, 20))
    } catch {
      setEvents([])
    }
  }

  useEffect(() => {
    refreshEvents(userId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId])

  async function run() {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const data = await fetchLearningResources(section.trim(), level || undefined, 20)
      setResources(data.resources)
    } catch (error) {
      setErrorMessage(
        error instanceof LearningResourcesError ? error.message : 'The learning resolver could not be reached.',
      )
      setResources([])
    } finally {
      setIsLoading(false)
    }
  }

  async function capture(eventType: string, opts?: { resource?: LearningResource; payload?: Record<string, unknown> }) {
    if (!userId) {
      setCaptureMessage('Pick a technician first.')
      return
    }
    setCaptureMessage(null)
    const ref = opts?.resource?.reference as { kind?: string; id?: string } | undefined
    try {
      await recordLearningEvent({
        user_id: userId,
        event_type: eventType,
        study_content_id: ref?.kind === 'study_content' ? ref.id ?? null : null,
        neta_section: section.trim() || null,
        payload: opts?.payload,
      })
      setCaptureMessage(`Recorded ${eventType}.`)
      await refreshEvents(userId)
    } catch (error) {
      setCaptureMessage(error instanceof LearningCaptureError ? error.message : 'Capture failed.')
    }
  }

  return (
    <main className="shell-page">
      <section className="hero-card">
        <p className="eyebrow">Learning &rarr; Slice 2 capture</p>
        <h1>Surface resources, then capture engagement.</h1>
      </section>

      <section className="notes-card">
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <label>NETA section
            <input list="neta-sections" value={section} onChange={(e) => setSection(e.target.value)} placeholder="7.6.1.1.1" />
            <datalist id="neta-sections">
              {sections.map((s) => <option key={s} value={s} />)}
            </datalist>
          </label>
          <label>Level
            <select value={level} onChange={(e) => setLevel(e.target.value)}>
              <option value="">Any</option>
              <option value="II">II</option>
              <option value="III">III</option>
              <option value="IV">IV</option>
            </select>
          </label>
          <label>Technician
            <select value={userId} onChange={(e) => setUserId(e.target.value)}>
              {users.length === 0 ? <option value="">(no users)</option> : null}
              {users.map((u) => (
                <option key={u.id} value={u.id}>{u.email}</option>
              ))}
            </select>
          </label>
          <button className="btn" onClick={run} disabled={isLoading}>Resolve</button>
        </div>

        {captureMessage ? <p className="resource-banner resource-banner-neutral">{captureMessage}</p> : null}
        {isLoading ? <p className="resource-banner resource-banner-neutral">Resolving&hellip;</p> : null}
        {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

        {resources && !isLoading && !errorMessage ? (
          <div className="resource-results">
            {resources.length === 0 ? (
              <p className="resource-banner resource-banner-neutral">No linked resources for this section yet.</p>
            ) : (
              [
                { key: 'curated', label: 'Curated', items: resources.filter((r) => r.source === 'curated') },
                { key: 'section', label: 'Section matches', items: resources.filter((r) => r.source !== 'curated') },
              ]
                .filter((g) => g.items.length > 0)
                .map((g) => (
                  <div key={g.key}>
                    <p className="eyebrow">{g.label}</p>
                    <div className="resource-grid">
                      {g.items.map((r, i) => (
                        <article className="resource-item" key={`${g.key}-${i}`}>
                          <div className="resource-item-row">
                            <span className="resource-chip">{r.source === 'curated' ? 'Curated' : 'Section match'}</span>
                            {r.is_primary ? <span className="resource-chip">Primary</span> : null}
                            {r.cert_level ? <span className="resource-chip">Level {r.cert_level}</span> : null}
                          </div>
                          <h3>{r.title}</h3>
                          <p>{r.why}</p>
                          <div className="resource-item-row">
                            <button className="btn" onClick={() => capture('resource_viewed', { resource: r })}>Mark viewed</button>
                            <button className="btn" onClick={() => capture('resource_completed', { resource: r })}>Mark completed</button>
                          </div>
                        </article>
                      ))}
                    </div>
                  </div>
                ))
            )}
          </div>
        ) : null}

        <div className="resource-item-row" style={{ marginTop: '1rem', gap: '0.75rem', alignItems: 'flex-end' }}>
          <label>Confidence
            <select value={confidence} onChange={(e) => setConfidence(e.target.value)}>
              {[1, 2, 3, 4, 5].map((n) => <option key={n} value={String(n)}>{n}</option>)}
            </select>
          </label>
          <button className="btn" onClick={() => capture('self_assessment', { payload: { confidence: Number(confidence) } })}>
            Log self-assessment
          </button>
          <label>Assessment score
            <input value={score} onChange={(e) => setScore(e.target.value)} style={{ width: '5rem' }} />
          </label>
          <button className="btn" onClick={() => capture('assessment_completed', { payload: { score_percent: Number(score) } })}>
            Record assessment
          </button>
        </div>
      </section>

      <section className="notes-card">
        <h2>Captured events</h2>
        {events.length === 0 ? (
          <p className="resource-banner resource-banner-neutral">No events captured for this technician yet.</p>
        ) : (
          <div className="resource-grid">
            {events.map((e) => (
              <article className="resource-item" key={e.event_id}>
                <div className="resource-item-row">
                  <span className="resource-chip">{e.event_type}</span>
                  {e.neta_section ? <span className="resource-chip">NETA {e.neta_section}</span> : null}
                </div>
                <p>{new Date(e.occurred_at).toLocaleString()}</p>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}
