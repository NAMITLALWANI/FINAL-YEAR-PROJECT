const BASE = ''  // proxied by Vite → localhost:8000

export async function searchAuthor(name, candidateId = null, candidateSource = null, sources = null, useCache = true) {
  const params = new URLSearchParams({ name, use_cache: useCache })
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
