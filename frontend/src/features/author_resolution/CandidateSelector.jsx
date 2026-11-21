import React from 'react';
import { signalRows } from './contextModel.js';

export default function CandidateSelector({
  candidates,
  retrieval,
  meta = null,
  onSelect,
  onMarkUnresolved,
  saving = false,
}) {
  if (!Array.isArray(candidates)) return null;
  const hasCandidates = candidates.length > 0;

  return (
    <div className="candidate-selector animate-in" aria-busy={saving}>
      <div className="selector-header">
        <div className="selector-icon" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
        </div>
        <div className="selector-title-group">
          <h3 className="selector-title">
            {hasCandidates ? 'Candidate Review Required' : 'No Candidate Profiles Found'}
          </h3>
          <p className="selector-subtitle">
            {hasCandidates
              ? 'Review the source profiles and multi-signal evidence before selecting a researcher.'
              : meta?.retrievalStatus === 'empty'
                ? 'OpenAlex answered successfully but returned no matching profile (this is not a provider error). You may record this identity as unresolved.'
                : 'No source profile was returned. You may record this identity as unresolved.'}
          </p>
        </div>
      </div>

      {meta && (
        <div className="selector-advisory" style={{ margin: '0.6rem 0', padding: '0.6rem 0.8rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '0.82rem', color: '#475569' }}>
          {meta.contextReceived && (
            <div>
              Context used: {['institution', 'publications', 'coauthors', 'active_years'].filter((k) => meta.contextReceived[k]).map((k) => k.replace('_', ' ')).join(', ') || 'name only'}.
              {meta.contextReceived.ignored_title_only_publications > 0 && ' Title-only publications were ignored (titles are not stable identifiers).'}
              {meta.contextReceived.rejected_inputs?.length > 0 && ` Rejected inputs: ${meta.contextReceived.rejected_inputs.join('; ')}.`}
            </div>
          )}
          {meta.enrichment?.any_failed && (
            <div style={{ color: '#b45309', marginTop: '0.3rem' }}>
              Some evidence could not be retrieved from OpenAlex; affected signals are marked “Retrieval failed” and were not scored.
            </div>
          )}
          {meta.assessment && (
            <div style={{ marginTop: '0.3rem' }}>
              <strong>System assessment (advisory only; nothing is applied automatically):</strong>{' '}
              {String(meta.assessment.status).replaceAll('_', ' ')}. {meta.assessment.reason}
              {meta.assessment.auto_blockers?.length > 0 && (
                <span> Automatic assignment withheld ({meta.assessment.auto_blockers.join(', ').replaceAll('_', ' ')}).</span>
              )}
            </div>
          )}
          <div style={{ marginTop: '0.3rem', fontStyle: 'italic' }}>
            Scores are heuristic evidence summaries, not probabilities. Your selection is recorded as a reviewer decision.
          </div>
        </div>
      )}

      {hasCandidates && <div className="candidate-list">
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

                {/* All five signals are always listed; unavailable evidence is never shown as agreement */}
                {Array.isArray(candidate.evidence) && (
                  <div className="evidence-signals" style={{ marginTop: '0.6rem' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.2rem' }}>
                      Evidence signals:
                    </div>
                    {signalRows(candidate.evidence).map((row) => (
                      <div
                        key={row.name}
                        className="candidate-institution"
                        style={{ fontSize: '0.78rem', color: row.observed ? '#475569' : '#94a3b8' }}
                      >
                        • {row.label}: {row.observed ? row.score.toFixed(2) : `not scored — ${row.status}`}
                        {row.observed && row.explanation ? ` (${row.explanation})` : ''}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="candidate-meta">
                <div className="confidence-indicator">
                  <span className="conf-label">Heuristic score band</span>
                  <span className={`conf-value ${confClass}`}>
                    {candidate.confidence || 'Review required'}
                  </span>
                </div>

                <button
                  className="select-btn"
                  type="button"
                  onClick={() => onSelect(candidate)}
                  disabled={saving}
                >
                  {saving ? 'Saving decision…' : 'Select Profile'}
                </button>
              </div>
            </div>
          );
        })}
      </div>}

      {/* Semantic retrieval context section */}
      {retrieval && (
        <section className="candidate-evidence" aria-label="Retrieved scholarly evidence" style={{ marginTop: '1.2rem', padding: '1rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <h4 style={{ margin: '0 0 0.4rem', fontSize: '0.95rem', color: '#1e293b' }}>
            Retrieved Context & Scholarly Evidence
          </h4>
          <p style={{ margin: '0 0 0.8rem', fontSize: '0.82rem', color: '#64748b', fontStyle: 'italic' }}>
            <strong>Note:</strong> Semantic similarity represents topical relevance for retrieval context, not identity probability.
          </p>

          {retrieval.status === 'unavailable' && (
            <p style={{ margin: '0 0 0.8rem', fontSize: '0.82rem', color: '#b45309' }}>
              Topical retrieval context is unavailable. This does not change the candidate evidence or identity decision.
            </p>
          )}

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
          disabled={saving}
          style={{ background: '#475569' }}
        >
          {saving ? 'Saving decision…' : 'Mark identity unresolved'}
        </button>
      </div>
    </div>
  );
}
