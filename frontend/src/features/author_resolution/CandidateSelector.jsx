import React from 'react';

export default function CandidateSelector({
  candidates,
  retrieval,
  onSelect,
  onMarkUnresolved,
}) {
  if (!candidates || candidates.length === 0) return null;

  return (
    <div className="candidate-selector animate-in">
      <div className="selector-header">
        <div className="selector-icon">👥</div>
        <div className="selector-title-group">
          <h3 className="selector-title">Candidate Review Required</h3>
          <p className="selector-subtitle">
            Review the source profiles and multi-signal evidence before selecting a researcher.
          </p>
        </div>
      </div>

      <div className="candidate-list">
        {candidates.map((candidate, idx) => {
          let confClass = 'conf-low';
          const conf = (candidate.confidence || '').toLowerCase();
          if (conf === 'high') confClass = 'conf-high';
          else if (conf === 'medium' || conf === 'med') confClass = 'conf-med';

          const works = candidate.works_count ?? 0;
          const citations = candidate.cited_by_count ?? candidate.citation_count ?? 0;
          const inst = candidate.institution_summary || candidate.institution || 'Unknown Institution';

          return (
            <div
              key={candidate.candidate_id || candidate.source_author_id || idx}
              className="candidate-card"
            >
              <div className="candidate-info">
                <div className="candidate-name">{candidate.display_name}</div>
                <div className="candidate-institution">
                  {inst} {candidate.country ? `(${candidate.country})` : ''}
                </div>
                <div className="candidate-stats">
                  <span className="stat-pill">{works} papers</span>
                  <span className="stat-pill">{citations} citations</span>
                  {candidate.score != null && (
                    <>
                      <span className="stat-pill">
                        Evidence score: {Number(candidate.score).toFixed(2)}
                      </span>
                      {candidate.available_signals != null && (
                        <span className="stat-pill">
                          {candidate.available_signals} available signals
                        </span>
                      )}
                    </>
                  )}
                </div>

                {/* Multi-signal evidence explanation */}
                {candidate.evidence && candidate.evidence.length > 0 && (
                  <div className="evidence-signals" style={{ marginTop: '0.6rem' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.2rem' }}>
                      Evidence Signals:
                    </div>
                    {candidate.evidence
                      .filter((e) => e.availability === 'available' || e.score != null || e.normalized_score != null)
                      .map((e, sIdx) => {
                        const sigName = (e.signal || e.signal_name || 'signal').replaceAll('_', ' ');
                        const sigScore = e.score ?? e.normalized_score ?? e.signal_value;
                        return (
                          <div
                            key={e.signal || e.signal_name || sIdx}
                            className="candidate-institution"
                            style={{ fontSize: '0.78rem', color: '#64748b' }}
                          >
                            • {sigName}: {typeof sigScore === 'number' ? sigScore.toFixed(2) : String(sigScore)}
                            {e.explanation ? ` (${e.explanation})` : ''}
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>

              <div className="candidate-meta">
                <div className="confidence-indicator">
                  <span className="conf-label">Confidence</span>
                  <span className={`conf-value ${confClass}`}>
                    {candidate.confidence || 'Review required'}
                  </span>
                </div>

                <button
                  className="select-btn"
                  type="button"
                  onClick={() => onSelect(candidate)}
                >
                  Select Profile
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Semantic retrieval context section */}
      {retrieval && (
        <section className="candidate-evidence" aria-label="Retrieved scholarly evidence" style={{ marginTop: '1.2rem', padding: '1rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <h4 style={{ margin: '0 0 0.4rem', fontSize: '0.95rem', color: '#1e293b' }}>
            Retrieved Context & Scholarly Evidence
          </h4>
          <p style={{ margin: '0 0 0.8rem', fontSize: '0.82rem', color: '#64748b', fontStyle: 'italic' }}>
            <strong>Note:</strong> Semantic similarity represents topical relevance for retrieval context, not identity probability.
          </p>

          {retrieval.hits && retrieval.hits.length > 0 ? (
            <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.85rem' }}>
              {retrieval.hits.map((hit, hIdx) => (
                <li key={hit.document_id || hIdx} style={{ marginBottom: '0.4rem' }}>
                  <strong>{hit.title}</strong> ({hit.year || 'n.d.'})
                  {hit.doi && (
                    <a
                      href={`https://doi.org/${hit.doi}`}
                      target="_blank"
                      rel="noreferrer"
                      style={{ marginLeft: '0.4rem', color: '#2563eb' }}
                    >
                      DOI
                    </a>
                  )}
                  {hit.authors && hit.authors.length > 0 && (
                    <small style={{ display: 'block', color: '#64748b' }}>
                      Authors: {hit.authors.join(', ')}
                    </small>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
              No indexed topical context records found for this author name.
            </p>
          )}

          {retrieval.explanation && retrieval.explanation.summary && (
            <div style={{ marginTop: '0.6rem', fontSize: '0.82rem', color: '#475569' }}>
              {retrieval.explanation.summary}
            </div>
          )}
        </section>
      )}

      {/* Explicit Unresolved Action */}
      <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
        <button
          className="select-btn"
          type="button"
          onClick={onMarkUnresolved}
          style={{ background: '#475569' }}
        >
          Mark identity unresolved
        </button>
      </div>
    </div>
  );
}
