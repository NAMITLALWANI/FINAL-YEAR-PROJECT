/**
 * Architectural Role: Main Application Component & Feature Coordinator.
 * 
 * Orchestrates:
 * 1. Author Identity Resolution Mode (Multi-source harvesting, evidence ranking, disambiguation)
 * 2. Semantic Literature & RAG Mode (ChromaDB 384-d dense vector retrieval and grounded explanations)
 * 3. Cross-source publication deduplication and monitoring panels
 */
import { useState, useEffect } from 'react'
import SearchBar from './features/search/SearchBar.jsx'
import StatsBar from './features/search/StatsBar.jsx'
import SourceStatusPanel from './features/monitoring/SourceStatusPanel.jsx'
import PaperCard from './features/search/PaperCard.jsx'
import SemanticResultCard from './features/search/SemanticResultCard.jsx'
import CandidateSelector from './features/author_resolution/CandidateSelector.jsx'
import {
  searchAuthor,
  getAuthorCandidates,
  fetchAuthorCandidatesV1,
  createAuthorResolution,
  searchSemanticEvidence,
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
function EmptyState({ query, mode = 'author' }) {
  return (
    <div className="state-box">
      <div className="state-icon">🔍</div>
      <p className="state-title">No literature found for "{query}"</p>
      <p className="state-desc">
        {mode === 'author'
          ? "No publications matched this author query across connected registries. Verify spelling or check upstream source statuses."
          : "No indexed publications cleared the semantic similarity threshold (τ = 0.35) for this concept."}
      </p>
    </div>
  )
}

function ErrorState({ message }) {
  return (
    <div className="state-box">
      <div className="state-icon">⚠️</div>
      <p className="state-title" style={{ color: 'var(--red)' }}>Search Error</p>
      <p className="state-desc">{message}</p>
    </div>
  )
}

function WelcomeState({ mode = 'author' }) {
  return (
    <div className="state-box">
      <div className="state-icon">{mode === 'author' ? '🏛️' : '🧠'}</div>
      <p className="state-title">
        {mode === 'author' ? 'HAMMER Author Intelligence' : 'HAMMER Semantic Literature & RAG'}
      </p>
      <p className="state-desc">
        {mode === 'author'
          ? 'Search scholarly metadata across connected sources, compare duplicate publication records, and review author candidates with traceable evidence.'
          : 'Query 384-dimensional dense semantic vectors (all-MiniLM-L6-v2) over indexed scholarly publications with grounded claim verification.'}
      </p>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────────
export default function App() {
  const [searchMode, setSearchMode] = useState('author') // 'author' | 'semantic'
  const [query, setQuery]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('Searching metadata...')
  const [result, setResult]         = useState(null)
  const [semanticResults, setSemanticResults] = useState(null)
  const [candidates, setCandidates] = useState(null)
  const [retrieval, setRetrieval]   = useState(null)
  const [error, setError]           = useState(null)
  const [unresolvedMessage, setUnresolvedMessage] = useState(null)
  const [searched, setSearched]     = useState('')

  // ── Rotating Loading Message ─────────────────────────────────────
  useEffect(() => {
    if (!loading) return
    const messages = searchMode === 'author' ? [
      "Searching metadata across registries...",
      "Querying OpenAlex, DBLP, Crossref, and arXiv...",
      "Retrieving candidate profiles...",
      "Calculating multi-signal evidence...",
      "Merging duplicate records...",
      "Finalizing publication list..."
    ] : [
      "Embedding query into 384-d semantic space...",
      "Searching ChromaDB vector index...",
      "Filtering low-similarity candidates (cosine threshold τ = 0.35)...",
      "Retrieving grounded publication abstracts...",
      "Synthesizing traceable context..."
    ]
    let idx = 0
    const interval = setInterval(() => {
      idx = (idx + 1) % messages.length
      setLoadingMessage(messages[idx])
    }, 1800)
    return () => clearInterval(interval)
  }, [loading, searchMode])

  function handleModeChange(newMode) {
    setSearchMode(newMode)
    setResult(null)
    setSemanticResults(null)
    setCandidates(null)
    setRetrieval(null)
    setError(null)
    setUnresolvedMessage(null)
  }

  async function handleSearch() {
    const q = query.trim()
    if (!q) return

    setLoading(true)
    setError(null)
    setUnresolvedMessage(null)
    setResult(null)
    setSemanticResults(null)
    setCandidates(null)
    setRetrieval(null)
    setSearched(q)

    if (searchMode === 'semantic') {
      await handleSemanticSearch(q)
    } else {
      await handleAuthorSearch(q)
    }
  }

  // ── Semantic Search Flow ─────────────────────────────────────────
  async function handleSemanticSearch(term) {
    setLoadingMessage('Searching dense vector index...')
    try {
      const data = await searchSemanticEvidence(term, 10)
      setSemanticResults(data)
    } catch (err) {
      setError(err.message || 'Semantic search failed')
    } finally {
      setLoading(false)
    }
  }

  // ── Author Search Flow ───────────────────────────────────────────
  async function handleAuthorSearch(name) {
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
  const semanticHits = semanticResults?.hits || []

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
          searchMode={searchMode}
          onSearchModeChange={handleModeChange}
        />

        {/* Unresolved message banner */}
        {!loading && unresolvedMessage && (
          <div className="state-box" style={{ background: '#f8fafc', border: '1px solid #cbd5e1', marginTop: '1.5rem' }}>
            <div className="state-icon">ℹ️</div>
            <p className="state-title">Identity Unresolved</p>
            <p className="state-desc">{unresolvedMessage}</p>
          </div>
        )}

        {/* Candidate Selector (Author Mode) */}
        {!loading && candidates && (
          <CandidateSelector 
            candidates={candidates} 
            retrieval={retrieval}
            onSelect={handleCandidateSelect}
            onMarkUnresolved={handleMarkUnresolved}
          />
        )}

        {/* Author Mode: Stats & Source status */}
        {searchMode === 'author' && result && !loading && !candidates && <StatsBar data={result} />}
        {searchMode === 'author' && result && !loading && !candidates && (
          <SourceStatusPanel statuses={result.source_statuses} />
        )}

        {/* Semantic Mode: Grounded Explanation Banner */}
        {searchMode === 'semantic' && semanticResults?.explanation && !loading && (
          <div className="semantic-explanation-banner">
            <h4>💡 Grounded Literature Synthesis</h4>
            <p>{semanticResults.explanation.summary}</p>
          </div>
        )}

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
        {!loading && !result && !semanticResults && !error && !candidates && !unresolvedMessage && (
          <WelcomeState mode={searchMode} />
        )}

        {/* Empty States */}
        {!loading && searchMode === 'author' && result && papers.length === 0 && !error && !candidates && !unresolvedMessage && (
          <EmptyState query={searched} mode="author" />
        )}
        {!loading && searchMode === 'semantic' && semanticResults && semanticHits.length === 0 && !error && (
          <EmptyState query={searched} mode="semantic" />
        )}

        {/* Author Mode Results */}
        {!loading && searchMode === 'author' && papers.length > 0 && !candidates && (
          <div className="results-container">
            <p className="results-count">
              Showing {papers.length} reconciled publication{papers.length !== 1 ? 's' : ''} for "{searched}"
            </p>
            {papers.map(p => (
              <PaperCard key={p.canonical_id || p.id} paper={p} />
            ))}
          </div>
        )}

        {/* Semantic Mode Results */}
        {!loading && searchMode === 'semantic' && semanticHits.length > 0 && (
          <div className="results-container">
            <p className="results-count">
              Found {semanticHits.length} semantically relevant publication{semanticHits.length !== 1 ? 's' : ''} for "{searched}"
            </p>
            {semanticHits.map((hit, idx) => (
              <SemanticResultCard key={hit.document_id || idx} hit={hit} rank={idx + 1} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
