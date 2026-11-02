import { useState } from 'react'
import SourceBadge from '../monitoring/SourceBadge.jsx'
import MergeDetails from '../deduplication/MergeDetails.jsx'

function formatCitations(n) {
  if (!n) return null
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

function truncateAuthors(authors = [], max = 4) {
  if (authors.length <= max) return authors.join(', ')
  return authors.slice(0, max).join(', ') + ` +${authors.length - max} more`
}

export default function PaperCard({ paper }) {
  const [expanded, setExpanded] = useState(false)
  const citations = formatCitations(paper.citations)

  return (
    <div
      className={`paper-card ${expanded ? 'expanded' : ''}`}
      onClick={() => setExpanded(e => !e)}
    >
      <div className="paper-header">
        <h3 className="paper-title">{paper.title}</h3>
        <span className={`expand-icon ${expanded ? 'open' : ''}`}>▼</span>
      </div>

      <div className="paper-meta">
        {paper.year && <span className="paper-year">{paper.year}</span>}
        {paper.year && paper.venue && <span style={{ color: 'var(--border-light)' }}>·</span>}
        {paper.venue && <span className="paper-venue">{paper.venue}</span>}
        {citations && (
          <>
            <span style={{ color: 'var(--border-light)' }}>·</span>
            <span className="paper-citations">{citations} Citations</span>
          </>
        )}
      </div>

      {paper.authors?.length > 0 && (
        <p className="paper-authors">{truncateAuthors(paper.authors)}</p>
      )}

      <div className="paper-badges">
        {(paper.source_list || [paper.best_source]).filter(Boolean).map(s => (
          <SourceBadge key={s} source={s} />
        ))}
        {paper.source_count > 1 && (
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
            merged from {paper.source_count} sources
          </span>
        )}
      </div>

      {expanded && <MergeDetails paper={paper} />}
    </div>
  )
}
