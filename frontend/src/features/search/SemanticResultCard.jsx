import { useState } from 'react'
import SourceBadge from '../monitoring/SourceBadge.jsx'

export default function SemanticResultCard({ hit, rank }) {
  const [expanded, setExpanded] = useState(false)
  const scorePercent = Math.round((hit.score || 0) * 100)

  return (
    <div className="paper-card semantic-card">
      <div className="paper-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <h3 className="paper-title" style={{ flex: 1, paddingRight: '1rem' }}>
          <span style={{ color: 'var(--accent)', marginRight: '0.6rem', fontFamily: 'var(--font-mono)', fontSize: '1.05rem' }}>
            #{rank}
          </span>
          {hit.title}
        </h3>
        
        {hit.score !== undefined && (
          <div 
            className="semantic-score-pill"
            title={`Cosine similarity: ${Number(hit.score).toFixed(4)}`}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.3rem 0.75rem',
              borderRadius: '20px',
              fontSize: '0.75rem',
              fontWeight: 700,
              fontFamily: 'var(--font-mono)',
              background: scorePercent >= 50 ? 'rgba(85, 107, 47, 0.12)' : 'rgba(230, 81, 0, 0.12)',
              color: scorePercent >= 50 ? 'var(--accent)' : '#e65100',
              border: `1px solid ${scorePercent >= 50 ? 'rgba(85, 107, 47, 0.25)' : 'rgba(230, 81, 0, 0.25)'}`,
              whiteSpace: 'nowrap'
            }}
          >
            <span>{scorePercent}% Match</span>
          </div>
        )}
      </div>

      <div className="paper-meta">
        {hit.year && <span className="paper-year">{hit.year}</span>}
        {hit.year && hit.venue && <span style={{ color: 'var(--border-light)' }}>·</span>}
        {hit.venue && <span className="paper-venue">{hit.venue}</span>}
        {hit.doi && (
          <>
            <span style={{ color: 'var(--border-light)' }}>·</span>
            <a 
              href={`https://doi.org/${hit.doi}`} 
              target="_blank" 
              rel="noreferrer" 
              style={{ color: '#2563eb', fontSize: '0.75rem', fontFamily: 'var(--font-mono)', textDecoration: 'none' }}
              onClick={e => e.stopPropagation()}
            >
              DOI ↗
            </a>
          </>
        )}
      </div>

      {hit.authors && hit.authors.length > 0 && (
        <p className="paper-authors">
          {hit.authors.slice(0, 5).join(', ')}{hit.authors.length > 5 ? ` +${hit.authors.length - 5} more` : ''}
        </p>
      )}

      {/* Abstract preview or full */}
      {hit.abstract && (
        <div 
          className="semantic-abstract" 
          style={{
            margin: '0.75rem 0 1rem',
            padding: '0.9rem 1.1rem',
            background: 'var(--bg-surface)',
            borderRadius: 'var(--radius-sm)',
            borderLeft: '3px solid var(--accent)',
            fontSize: '0.88rem',
            lineHeight: 1.6,
            color: 'var(--text-secondary)'
          }}
        >
          <p>
            {expanded || hit.abstract.length <= 260
              ? hit.abstract
              : `${hit.abstract.slice(0, 260)}...`}
            {hit.abstract.length > 260 && (
              <button
                type="button"
                onClick={() => setExpanded(!expanded)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent)',
                  fontWeight: 600,
                  cursor: 'pointer',
                  marginLeft: '0.5rem',
                  fontSize: '0.85rem'
                }}
              >
                {expanded ? 'Show less' : 'Read more'}
              </button>
            )}
          </p>
        </div>
      )}

      {/* Sources provenance */}
      <div className="paper-badges">
        {(hit.sources || []).map(s => (
          <SourceBadge key={s} source={s} />
        ))}
      </div>
    </div>
  )
}
