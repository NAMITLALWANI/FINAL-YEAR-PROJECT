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
          <span className="tab-icon">👤</span>
          <span className="tab-label">Author Identity Resolution</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={!isAuthorMode}
          className={`mode-tab ${!isAuthorMode ? 'active' : ''}`}
          onClick={() => onSearchModeChange('semantic')}
        >
          <span className="tab-icon">✨</span>
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
