/**
 * Architectural Role: Main Application Component & Feature Coordinator.
 * 
 * Orchestrates user search queries, author disambiguation workflows, publication
 * inspection, and source status monitoring across modular feature components:
 * - features/search: Query input, paper cards, and analytics stats bar.
 * - features/author_resolution: Interactive candidate selector modal for human-in-the-loop review.
 * - features/deduplication: Merge inspection and duplicate group breakdowns.
 * - features/monitoring: Circuit breaker and source health status indicators.
 */
import { useState, useEffect } from 'react'
import SearchBar from './features/search/SearchBar.jsx'
import StatsBar from './features/search/StatsBar.jsx'
import SourceStatusPanel from './features/monitoring/SourceStatusPanel.jsx'
import PaperCard from './features/search/PaperCard.jsx'
import CandidateSelector from './features/author_resolution/CandidateSelector.jsx'
import {
  searchAuthor,
  getAuthorCandidates,
  fetchAuthorCandidatesV1,
  createAuthorResolution,
} from './services/api.js'

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
      <p className="state-title">HAMMER Intelligence</p>
      <p className="state-desc">
        Search scholarly metadata across connected sources, compare duplicate publication records, and review author candidates with traceable evidence.
      </p>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────────
export default function App() {
  const [query, setQuery]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('Searching metadata...')
  const [result, setResult]     = useState(null)
  const [candidates, setCandidates] = useState(null)
  const [retrieval, setRetrieval] = useState(null)
  const [error, setError]       = useState(null)
  const [unresolvedMessage, setUnresolvedMessage] = useState(null)
  const [searched, setSearched] = useState('')

  // ── Rotating Loading Message ─────────────────────────────────────
  useEffect(() => {
    if (!loading) return
    const messages = [
      "Searching metadata...",
      "Querying scholarly sources...",
      "Retrieving indexed publications...",
      "Merging duplicate records...",
      "Finalizing publication list...",
      "Reconciling duplicate records...",
      "Checking source provenance..."
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
    setUnresolvedMessage(null)
    setResult(null)
    setCandidates(null)
    setRetrieval(null)
    setSearched(name)
    setLoadingMessage('Resolving author identity & evidence...')

    try {
      let candData = null
      try {
        candData = await fetchAuthorCandidatesV1(name, null)
      } catch (e) {
        console.warn('V1 candidates endpoint fallback:', e)
        candData = await getAuthorCandidates(name, null)
      }

      if (candData.retrieval) {
        setRetrieval(candData.retrieval)
      }

      const cands = candData.candidates || []
      if (cands.length > 1) {
        setCandidates(cands)
        setLoading(false)
      } else if (cands.length === 1) {
        const topCand = cands[0]
        try {
          const res = await createAuthorResolution({
            author_name: name,
            candidate_ids: [topCand.candidate_id],
            selected_candidate_id: topCand.candidate_id,
          })
          await fetchPapers(name, topCand.candidate_id, topCand.source, res.resolution_id)
        } catch {
          await fetchPapers(name, topCand.candidate_id, topCand.source)
        }
      } else {
        await fetchPapers(name, null, null)
      }
    } catch (err) {
      setError(err.message || 'Unknown error')
      setLoading(false)
    }
  }

  async function handleCandidateSelect(candidate) {
    const candidateIds = candidates ? candidates.map(c => c.candidate_id || c.source_author_id) : []
    setCandidates(null)
    setLoading(true)
    setError(null)
    setLoadingMessage(`Persisting selection and retrieving works for ${candidate.display_name}...`)
    try {
      let resolutionId = null
      try {
        const res = await createAuthorResolution({
          author_name: searched,
          candidate_ids: candidateIds,
          selected_candidate_id: candidate.candidate_id,
          reason: 'User manual selection from candidate review UI',
        })
        resolutionId = res.resolution_id
      } catch (e) {
        console.warn('Could not persist manual resolution:', e)
      }
      await fetchPapers(searched, candidate.candidate_id, candidate.source, resolutionId)
    } catch (err) {
      setError(err.message || 'Unknown error')
      setLoading(false)
    }
  }

  async function handleMarkUnresolved() {
    const candidateIds = candidates ? candidates.map(c => c.candidate_id || c.source_author_id) : []
    setCandidates(null)
    setLoading(true)
    setLoadingMessage('Recording unresolved identity decision...')
    try {
      await createAuthorResolution({
        author_name: searched,
        candidate_ids: candidateIds,
        mark_unresolved: true,
        reason: 'Reviewer marked identity as unresolved',
      })
      setUnresolvedMessage(`Identity for "${searched}" marked unresolved. No multi-source retrieval was initiated.`)
      setResult(null)
    } catch (err) {
      setError(err.message || 'Failed to record unresolved decision')
    } finally {
      setLoading(false)
    }
  }

  async function fetchPapers(name, candidateId, source, resolutionId = null) {
    const data = await searchAuthor(name, candidateId, source, null, true, resolutionId)
    if (data.identity_context?.status === 'unresolved' || data.message?.includes('unresolved')) {
      setUnresolvedMessage(data.message || 'Identity is unresolved; multi-source retrieval was aborted.')
      setResult(null)
    } else {
      setResult(data)
    }
    setLoading(false)
  }

  const papers = result?.papers || []

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-brand">
          <span className="header-logo">HAMMER</span>
        </div>
        <span className="header-subtitle">Institutional Research Discovery</span>
      </header>

      {/* ── Main ── */}
      <main className="main">
        <SearchBar
          value={query}
          onValueChange={setQuery}
          onSubmit={handleSearch}
          loading={loading}
        />

        {/* Unresolved message banner */}
        {!loading && unresolvedMessage && (
          <div className="state-box" style={{ background: '#f8fafc', border: '1px solid #cbd5e1', marginTop: '1.5rem' }}>
            <div className="state-icon">ℹ️</div>
            <p className="state-title">Identity Unresolved</p>
            <p className="state-desc">{unresolvedMessage}</p>
          </div>
        )}

        {/* Candidate Selector */}
        {!loading && candidates && (
          <CandidateSelector 
            candidates={candidates} 
            retrieval={retrieval}
            onSelect={handleCandidateSelect}
            onMarkUnresolved={handleMarkUnresolved}
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
            {[1, 2, 3, 4].map(n => <SkeletonCard key={n} />)}
          </div>
        )}

        {/* Error */}
        {error && !loading && <ErrorState message={error} />}

        {/* Welcome */}
        {!loading && !result && !error && !candidates && !unresolvedMessage && <WelcomeState />}

        {/* Empty */}
        {!loading && result && papers.length === 0 && !error && !candidates && !unresolvedMessage && (
          <EmptyState query={searched} />
        )}

        {/* Paper cards */}
        {!loading && papers.length > 0 && !candidates && (
          <div className="results-container">
            <p className="results-count">
              Showing {papers.length} reconciled publication{papers.length !== 1 ? 's' : ''} for "{searched}"
            </p>
            {papers.map(p => (
              <PaperCard key={p.canonical_id || p.id} paper={p} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
