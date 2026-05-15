import React from 'react';

export default function CandidateSelector({ candidates, onSelect }) {
  if (!candidates || candidates.length === 0) return null;

  return (
    <div className="candidate-selector animate-in">
      <div className="selector-header">
        <div className="selector-icon">👥</div>
        <div className="selector-title-group">
          <h3 className="selector-title">Multiple Authors Found</h3>
          <p className="selector-subtitle">
            Refine your search by selecting the correct researcher profile.
          </p>
        </div>
      </div>
      
      <div className="candidate-list">
        {candidates.map((candidate, idx) => {
          let confClass = 'conf-low';
          if (candidate.confidence === 'High') confClass = 'conf-high';
          if (candidate.confidence === 'Medium') confClass = 'conf-med';

          return (
            <div 
              key={candidate.candidate_id || idx} 
              className="candidate-card"
              onClick={() => onSelect(candidate)}
            >
              <div className="candidate-info">
                <div className="candidate-name">
                  {candidate.display_name}
                </div>
                <div className="candidate-institution">
                  {candidate.institution} {candidate.country ? `(${candidate.country})` : ''}
                </div>
                <div className="candidate-stats">
                  <span className="stat-pill">{candidate.works_count} papers</span>
                  <span className="stat-pill">{candidate.cited_by_count} citations</span>
                </div>
              </div>
              
              <div className="candidate-meta">
                <div className="confidence-indicator">
                  <span className="conf-label">Confidence</span>
                  <span className={`conf-value ${confClass}`}>{candidate.confidence}</span>
                </div>
                
                <button 
                  className="select-btn"
                >
                  Select Profile
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
