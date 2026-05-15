export default function SearchBar({ value, institution, onValueChange, onInstitutionChange, onSubmit, loading }) {
  function handleKey(e) {
    if (e.key === 'Enter') onSubmit()
  }

  return (
    <div className="search-section">
      <div className="search-wrapper" style={{ flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', width: '100%' }}>
          <input
            id="author-search-input"
            className="search-input"
            type="text"
            placeholder="Search by author name — e.g. Geoffrey Hinton"
            value={value}
            onChange={e => onValueChange(e.target.value)}
            onKeyDown={handleKey}
            autoComplete="off"
            spellCheck={false}
            style={{ flex: 2 }}
          />
          <input
            id="institution-search-input"
            className="search-input"
            type="text"
            placeholder="Institution Hint (Optional) — e.g. IIT Bombay"
            value={institution}
            onChange={e => onInstitutionChange(e.target.value)}
            onKeyDown={handleKey}
            autoComplete="off"
            spellCheck={false}
            style={{ flex: 1 }}
          />
          <button
            id="search-submit-btn"
            className="search-btn"
            onClick={onSubmit}
            disabled={loading || !value.trim()}
          >
            {loading ? 'Initializing…' : 'Analyze Identity'}
          </button>
        </div>
      </div>
      <p className="search-hint">
        Cross-referencing OpenAlex, DBLP, Crossref, and arXiv records for automated entity resolution.
      </p>
    </div>
  )
}
