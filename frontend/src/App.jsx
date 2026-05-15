import { useState, useEffect } from 'react'
import SearchBar from './components/SearchBar.jsx'
import StatsBar from './components/StatsBar.jsx'
import SourceStatusPanel from './components/SourceStatusPanel.jsx'
import PaperCard from './components/PaperCard.jsx'
import CandidateSelector from './components/CandidateSelector.jsx'
import { searchAuthor, getAuthorCandidates } from './api.js'

// ── Skeleton placeholders while loading ──────────────────────────
function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton sk-title" />
      <div className="skeleton sk-meta" style={{ marginTop: '0.5rem' }} />
      <div className="skeleton sk-tags" style={{ marginTop: '0.6rem' }} />
    </div>
  )
}

// ── Empty / error states ──────────────────────────────────────────
function EmptyState({ query }) {
  return (
    <div className="state-box">
      <div className="state-icon">🔍</div>
      <p className="state-title">No papers found for "{query}"</p>
      <p className="state-desc">Try a different name or check spelling.</p>
    </div>
  )
}

function ErrorState({ message }) {
  return (
    <div className="state-box error">
      <div className="state-icon">⚠️</div>
      <p className="state-title">Search failed</p>
      <p className="state-desc">{message}</p>
    </div>
  )
}

function WelcomeState() {
  return (
    <div className="state-box">
      <div className="state-icon">🏛️</div>
      <p className="state-title">ProjectX Intelligence</p>
      <p className="state-desc">
        A unified engine for cross-institutional research discovery. Aggregating disparate metadata sources into a high-fidelity knowledge layer.
      </p>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────────
export default function App() {
  const [query, setQuery]       = useState('')
  const [institution, setInstitution] = useState('')
  const [loading, setLoading]   = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('Searching metadata...')
  const [result, setResult]     = useState(null)
  const [candidates, setCandidates] = useState(null)
  const [error, setError]       = useState(null)
  const [searched, setSearched] = useState('')

  // ── Rotating Loading Message ─────────────────────────────────────
  useEffect(() => {
    if (!loading) return
    const messages = [
      "Searching metadata...",
      "Querying OpenAlex & ArXiv...",
      "Connecting to Scholar...",
      "Merging duplicate records...",
      "Finalizing publication list...",
      "Removing false positives...",
      "Building knowledge graph..."
    ]
    let idx = 0
    const interval = setInterval(() => {
      idx = (idx + 1) % messages.length
      setLoadingMessage(messages[idx])
    }, 2000)
    return () => clearInterval(interval)
  }, [loading])

  async function handleSearch() {
    const name = query.trim()
    if (!name) return

    setLoading(true)
    setError(null)
    setResult(null)
    setCandidates(null)
    setSearched(name)
    setLoadingMessage('Resolving author identity...')

    try {
      const candData = await getAuthorCandidates(name, institution.trim() || null)
      
      if (candData.multiple_candidates && candData.candidates.length > 1) {
        setCandidates(candData.candidates)
        setLoading(false)
      } else {
        const autoSelected = candData.auto_selected || (candData.candidates && candData.candidates[0])
        await fetchPapers(name, autoSelected?.candidate_id, autoSelected?.source)
      }
    } catch (err) {
      setError(err.message || 'Unknown error')
      setLoading(false)
    }
  }

  async function handleCandidateSelect(candidate) {
    setCandidates(null)
    setLoading(true)
    setError(null)
    setLoadingMessage(`Fetching works for ${candidate.display_name}...`)
    try {
      await fetchPapers(searched, candidate.candidate_id, candidate.source)
    } catch (err) {
      setError(err.message || 'Unknown error')
      setLoading(false)
    }
  }

  async function fetchPapers(name, candidateId, source) {
    const data = await searchAuthor(name, candidateId, source)
    setResult(data)
    setLoading(false)
  }

  const papers = result?.papers || []

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-brand">
          <span className="header-logo">ProjectX</span>
        </div>
        <span className="header-subtitle">Institutional Research Discovery</span>
      </header>

      {/* ── Main ── */}
      <main className="main">
        <SearchBar
          value={query}
          institution={institution}
          onValueChange={setQuery}
          onInstitutionChange={setInstitution}
          onSubmit={handleSearch}
          loading={loading}
        />

        {/* Candidate Selector */}
        {!loading && candidates && (
          <CandidateSelector 
            candidates={candidates} 
            onSelect={handleCandidateSelect} 
          />
        )}

        {/* Stats */}
        {result && !loading && !candidates && <StatsBar data={result} />}

        {/* Source status */}
        {result && !loading && !candidates && <SourceStatusPanel statuses={result.source_statuses} />}

        {/* Loading skeletons */}
        {loading && (
          <div className="results-container">
            <div className="loading-status-overlay">
              <div className="spinner-small" />
              <span className="loading-text">{loadingMessage}</span>
            </div>
            <div className="results-grid" style={{ opacity: 0.5 }}>
              {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
            </div>
          </div>
        )}

        {/* Results */}
        {!loading && result && !candidates && papers.length > 0 && (
          <div className="results-grid animate-in">
            {papers.map((paper, i) => (
              <PaperCard key={paper.canonical_id || paper.id || i} paper={paper} />
            ))}
          </div>
        )}

        {/* States */}
        {!loading && result && !candidates && papers.length === 0 && <EmptyState query={searched} />}
        {!loading && error && <ErrorState message={error} />}
        {!loading && !result && !error && !candidates && <WelcomeState />}
      </main>
    </div>
  )
}
