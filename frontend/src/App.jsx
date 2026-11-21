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
import AuthorContextForm from './features/author_resolution/AuthorContextForm.jsx'
import { buildAuthorContext, emptyContextForm } from './features/author_resolution/contextModel.js'
import {
  searchAuthor,
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
      <div className="state-icon" aria-hidden="true">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      </div>
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
      <div className="state-icon" aria-hidden="true">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      </div>
      <p className="state-title" style={{ color: 'var(--red)' }}>Search Error</p>
      <p className="state-desc">{message}</p>
    </div>
  )
}

function WelcomeState({ mode = 'author' }) {
  return (
    <div className="state-box">
      <div className="state-icon" aria-hidden="true">
        {mode === 'author' ? (
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
          </svg>
        ) : (
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
          </svg>
        )}
      </div>
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
  const [savingResolution, setSavingResolution] = useState(false)
  // Optional known context. `searchContext` is the exact context used for the candidate search, so the
  // later review decision is made with identical evidence inputs.
  const [contextForm, setContextForm] = useState(emptyContextForm())
  const [contextErrors, setContextErrors] = useState([])
  const [searchContext, setSearchContext] = useState({ institutionHint: null, context: null })
  const [candidateMeta, setCandidateMeta] = useState(null)

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
    setCandidateMeta(null)
    setError(null)
    setUnresolvedMessage(null)
    setSavingResolution(false)
  }

  async function handleSearch() {
    const q = query.trim()
    if (!q) return

    if (searchMode === 'author') {
      const built = buildAuthorContext(contextForm)
      setContextErrors(built.errors)
      if (built.errors.length > 0) return      // nothing is sent until the optional context is valid
    }

    setLoading(true)
    setError(null)
    setUnresolvedMessage(null)
    setResult(null)
    setSemanticResults(null)
    setCandidates(null)
    setRetrieval(null)
    setCandidateMeta(null)
    setSearched(q)
    setSavingResolution(false)

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
      const built = buildAuthorContext(contextForm)
      setSearchContext({ institutionHint: built.institutionHint, context: built.context })
      const candData = await fetchAuthorCandidatesV1(name, built.institutionHint, built.context)
      setRetrieval(candData.retrieval || null)
      setCandidateMeta({
        retrievalStatus: candData.candidate_retrieval_status || null,
        assessment: candData.algorithmic_assessment || null,
        contextReceived: candData.context_received || null,
        enrichment: candData.enrichment || null,
      })
      // Always leave the identity decision visible to the reviewer. A single
      // source profile is still a candidate, not an implicit selection.
      setCandidates(candData.candidates || [])
    } catch (err) {
      setError(err.message || 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  async function handleCandidateSelect(candidate) {
    const candidateIds = candidates ? candidates.map(c => c.candidate_id || c.source_author_id).filter(Boolean) : []
    const candidateId = candidate.candidate_id || candidate.source_author_id
    setSavingResolution(true)
    setError(null)
    setLoadingMessage(`Persisting selection and retrieving works for ${candidate.display_name}...`)
    try {
      const res = await createAuthorResolution({
        author_name: searched,
        institution_hint: searchContext.institutionHint,
        ...(searchContext.context ? { context: searchContext.context } : {}),
        candidate_ids: candidateIds,
        selected_candidate_id: candidateId,
        reason: 'User manual selection from candidate review UI',
      })
      setCandidates(null)
      setLoading(true)
      try {
        await fetchPapers(searched, candidateId, candidate.source, res.resolution_id)
      } catch (err) {
        setError(`Decision was saved, but publications could not be loaded: ${err.message || 'Unknown error'}`)
      } finally {
        setLoading(false)
      }
    } catch (err) {
      setError(`Selection was not saved: ${err.message || 'Unknown error'}`)
    } finally {
      setSavingResolution(false)
    }
  }

  async function handleMarkUnresolved() {
    const candidateIds = candidates ? candidates.map(c => c.candidate_id || c.source_author_id).filter(Boolean) : []
    setSavingResolution(true)
    setError(null)
    setLoadingMessage('Recording unresolved identity decision...')
    try {
      await createAuthorResolution({
        author_name: searched,
        institution_hint: searchContext.institutionHint,
        ...(searchContext.context ? { context: searchContext.context } : {}),
        candidate_ids: candidateIds,
        mark_unresolved: true,
        reason: 'Reviewer marked identity as unresolved',
      })
      setCandidates(null)
      setUnresolvedMessage(`Identity for "${searched}" marked unresolved. No multi-source retrieval was initiated.`)
      setResult(null)
    } catch (err) {
      setError(`Unresolved decision was not saved: ${err.message || 'Unknown error'}`)
    } finally {
      setSavingResolution(false)
    }
  }

  async function fetchPapers(name, candidateId, source, resolutionId = null) {
    try {
      const data = await searchAuthor(name, candidateId, source, null, true, resolutionId)
      if (data.identity_context?.status === 'unresolved' || data.message?.includes('unresolved')) {
        setUnresolvedMessage(data.message || 'Identity is unresolved; multi-source retrieval was aborted.')
        setResult(null)
      } else {
        setResult(data)
      }
    } finally {
      setLoading(false)
    }
  }

  const papers = result?.papers || []
  const semanticHits = semanticResults?.hits || []

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-brand">
          <span className="header-logo">HAMMER</span>
          <span className="header-fullform">Hybrid Academic Metadata Matching and Evidence-based Resolution</span>
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

        {searchMode === 'author' && (
          <AuthorContextForm value={contextForm} onChange={setContextForm} errors={contextErrors} disabled={loading} />
        )}

        {/* Unresolved message banner */}
        {!loading && unresolvedMessage && (
          <div className="state-box" style={{ background: '#f8fafc', border: '1px solid #cbd5e1', marginTop: '1.5rem' }}>
            <div className="state-icon" aria-hidden="true">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <p className="state-title">Identity Unresolved</p>
            <p className="state-desc">{unresolvedMessage}</p>
          </div>
        )}

        {/* Candidate Selector (Author Mode) */}
        {!loading && candidates !== null && (
          <CandidateSelector 
            candidates={candidates} 
            retrieval={retrieval}
            meta={candidateMeta}
            onSelect={handleCandidateSelect}
            onMarkUnresolved={handleMarkUnresolved}
            saving={savingResolution}
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
            <h4>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ marginRight: '6px', verticalAlign: '-2px' }}>
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
              Grounded Literature Synthesis
            </h4>
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
