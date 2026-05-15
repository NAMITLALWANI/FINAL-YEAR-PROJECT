import { useEffect, useState } from 'react'
import SourceBadge from './SourceBadge.jsx'
import { getSimilarityLog } from '../api.js'

const PROVENANCE_FIELDS = [
  { key: 'abstract_source',  label: 'Abstract' },
  { key: 'doi_source',       label: 'DOI' },
  { key: 'venue_source',     label: 'Venue' },
  { key: 'citations_source', label: 'Citations' },
]

export default function MergeDetails({ paper }) {
  const [logs, setLogs] = useState([])
  const [loadingLogs, setLoadingLogs] = useState(false)
  
  const provenanceItems = PROVENANCE_FIELDS.filter(f => paper[f.key])

  useEffect(() => {
    if (paper.id) {
      setLoadingLogs(true)
      getSimilarityLog(paper.id)
        .then(res => setLogs(res.logs || []))
        .catch(() => setLogs([]))
        .finally(() => setLoadingLogs(false))
    }
  }, [paper.id])

  const confidencePercent = ((paper.confidence_score || 1) * 100).toFixed(0)

  return (
    <div className="merge-details">
      {/* ── Confidence Header ── */}
      <div className="merge-header-row">
        <div className="merge-summary-item">
          <span className="merge-section-title">Resolution Confidence</span>
          <div className="confidence-display">
            <div className="confidence-track">
              <div 
                className="confidence-fill" 
                style={{ 
                  width: `${confidencePercent}%`,
                  background: paper.confidence_score > 0.9 ? 'var(--green)' : 'var(--amber)'
                }} 
              />
            </div>
            <span className="confidence-text" style={{ color: paper.confidence_score > 0.9 ? 'var(--green)' : 'var(--amber)' }}>
              {confidencePercent}%
            </span>
          </div>
        </div>

        <div className="merge-summary-item">
          <span className="merge-section-title">Aggregated From</span>
          <div className="source-list-mini">
            {(paper.source_list || []).map(s => (
              <SourceBadge key={s} source={s} />
            ))}
          </div>
        </div>
      </div>

      <div className="merge-grid-layout">
        {/* ── Field Provenance ── */}
        <div className="merge-column">
          <p className="merge-section-title">Data Provenance (Source Selection)</p>
          <div className="provenance-table">
            <div className="prov-row header">
              <span>Metadata Field</span>
              <span>Selected Source</span>
            </div>
            {provenanceItems.map(f => (
              <div key={f.key} className="prov-row">
                <span className="prov-label">{f.label}</span>
                <span className="prov-value-badge">{paper[f.key]}</span>
              </div>
            ))}
            <div className="prov-row primary">
              <span className="prov-label">Primary Identity</span>
              <span className="prov-value-badge primary">{paper.best_source}</span>
            </div>
          </div>
        </div>

        {/* ── Similarity Logs ── */}
        <div className="merge-column">
          <p className="merge-section-title">Entity Resolution Audit Trail</p>
          <div className="log-container">
            {loadingLogs ? (
              <div className="log-msg loading">
                <div className="spinner-tiny" />
                <span>Fetching similarity scores...</span>
              </div>
            ) : logs.length > 0 ? (
              <div className="log-scroll">
                {logs.map((log, i) => (
                  <div key={i} className={`log-entry ${log.decision}`}>
                    <div className="log-entry-header">
                      <span className="log-id">Match Candidate #{i+1}</span>
                      <span className="log-score-badge">{(log.score * 100).toFixed(0)}% Match</span>
                    </div>
                    <div className="log-metrics">
                      <div className="metric"><span>Title:</span> {log.title_sim.toFixed(2)}</div>
                      <div className="metric"><span>Author:</span> {log.author_sim.toFixed(2)}</div>
                      <div className="metric"><span>Year:</span> {log.year_match ? '✓' : '✗'}</div>
                    </div>
                    <div className="log-decision">
                      Action: <span className="decision-tag">{log.decision}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="log-msg empty">
                <span>No cross-record merges detected.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Abstract ── */}
      {paper.abstract && (
        <div className="abstract-section">
          <p className="merge-section-title">Abstract Summary</p>
          <div className="abstract-box">{paper.abstract}</div>
        </div>
      )}

      {/* ── Footer Info ── */}
      <div className="merge-footer">
        <div className="identifier-pill">
          <span className="id-label">Canonical ID:</span>
          <span className="id-value">{paper.canonical_id}</span>
        </div>
        {paper.doi && (
          <a
            className="doi-link-btn"
            href={`https://doi.org/${paper.doi}`}
            target="_blank"
            rel="noreferrer"
          >
            View on DOI.org ↗
          </a>
        )}
      </div>
    </div>
  )
}
