export default function SearchBar({ 
  value, 
  onValueChange, 
  onSubmit, 
  loading,
  searchMode = 'author',
  onSearchModeChange = () => {}
}) {
  function handleKey(e) {
    if (e.key === 'Enter') onSubmit()
  }

  const isAuthorMode = searchMode === 'author'

  return (
    <div className="search-section">
      {/* ── Mode Switcher ─────────────────────────────────────── */}
      <div className="search-mode-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={isAuthorMode}
          className={`mode-tab ${isAuthorMode ? 'active' : ''}`}
          onClick={() => onSearchModeChange('author')}
        >
          <span className="tab-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </span>
          <span className="tab-label">Author Identity Resolution</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={!isAuthorMode}
          className={`mode-tab ${!isAuthorMode ? 'active' : ''}`}
          onClick={() => onSearchModeChange('semantic')}
        >
          <span className="tab-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          </span>
          <span className="tab-label">Semantic Literature & RAG</span>
        </button>
      </div>

      <div className="search-wrapper">
        <input
          id="main-search-input"
          className="search-input"
          type="text"
          placeholder={
            isAuthorMode
              ? "Search researcher name — e.g. Geoffrey Hinton, Andrew Ng"
              : "Search research concept, topic, or methodology — e.g. deep learning neural networks"
          }
          value={value}
          onChange={e => onValueChange(e.target.value)}
          onKeyDown={handleKey}
          autoComplete="off"
          spellCheck={false}
        />
        <button
          id="search-submit-btn"
          className="search-btn"
          onClick={onSubmit}
          disabled={loading || !value.trim()}
        >
          {loading 
            ? 'Searching…' 
            : isAuthorMode 
              ? 'Analyze Identity' 
              : 'Retrieve Literature'}
        </button>
      </div>
      
      <p className="search-hint">
        {isAuthorMode
          ? "Cross-referencing OpenAlex, DBLP, Crossref, and arXiv records for automated entity resolution."
          : "Querying 384-dimensional dense semantic vectors (all-MiniLM-L6-v2) over indexed scholarly publications."}
      </p>
    </div>
  )
}
