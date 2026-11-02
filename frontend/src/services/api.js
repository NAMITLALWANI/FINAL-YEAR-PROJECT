/**
 * Architectural Role: Centralized API Client Service.
 * 
 * Provides typed, asynchronous communication with the HAMMER FastAPI backend.
 * Endpoints covered:
 * - /search: Federated multi-source publication queries.
 * - /author-resolutions/candidates: Candidate profile harvesting for disambiguation.
 * - /author-resolutions: Submitting human review decisions (auto, manual, unresolved).
 * - /similarity-log: Inspection of pairwise deduplication feature scores.
 * - /metrics: System ingestion counts, duplicate group statistics, and circuit breaker states.
 */
const BASE = ''  // proxied by Vite → localhost:8000

export async function searchAuthor(
  name,
  candidateId = null,
  candidateSource = null,
  sources = null,
  useCache = true,
  resolutionId = null
) {
  const params = new URLSearchParams({ name, use_cache: useCache })
  if (resolutionId) params.append('resolution_id', resolutionId)
  if (candidateId) params.append('candidate_id', candidateId)
  if (candidateSource) params.append('candidate_source', candidateSource)
  if (sources) params.append('sources', sources.join(','))
  const res = await fetch(`${BASE}/search?${params}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || err.error || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function getAuthorCandidates(name, institution = null) {
  const params = new URLSearchParams({ name })
  if (institution) params.append('institution', institution)
  const res = await fetch(`${BASE}/search/candidates?${params}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || err.error || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function fetchAuthorCandidatesV1(authorName, institutionHint = null) {
  const res = await fetch(`${BASE}/author-resolutions/candidates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ author_name: authorName, institution_hint: institutionHint }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || err.error || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function createAuthorResolution(payload) {
  const res = await fetch(`${BASE}/author-resolutions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || err.error || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function getAuthorResolutionDetails(resolutionId) {
  const res = await fetch(`${BASE}/author-resolutions/${resolutionId}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function getPublication(id) {
  const res = await fetch(`${BASE}/publications/${id}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function getSimilarityLog(pubId) {
  const res = await fetch(`${BASE}/similarity-log/${pubId}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function getMetrics() {
  const res = await fetch(`${BASE}/metrics`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}


export async function searchSemanticEvidence(query, topK = 10, filters = null) {
  const res = await fetch(`${BASE}/evidence/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK, filters }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || err.error || `HTTP ${res.status}`)
  }
  return res.json()
}
