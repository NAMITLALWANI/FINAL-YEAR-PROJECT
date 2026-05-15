export default function SearchBar({ value, onValueChange, onSubmit, loading }) {
  function handleKey(e) {
    if (e.key === 'Enter') onSubmit()
  }

  return (
    <div className="search-section">
      <div className="search-wrapper">
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
      <p className="search-hint">
        Cross-referencing OpenAlex, DBLP, Crossref, and arXiv records for automated entity resolution.
      </p>
    </div>
  )
}
