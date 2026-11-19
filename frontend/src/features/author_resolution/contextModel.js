/**
 * Pure helpers for the optional author-resolution context.
 *
 * The UI never invents context: a blank field is omitted from the request, which the backend
 * reports as "not provided" rather than as a mismatch. Only DOIs and OpenAlex work IDs are
 * accepted as publication identifiers (titles are not stable identities).
 */
export const MAX_ITEMS = 50
export const YEAR_MIN = 1800
export const YEAR_MAX = 2200

const DOI_RE = /^10\.\d{4,9}\/\S+$/
const DOI_PREFIX_RE = /^(?:https?:\/\/(?:dx\.)?doi\.org\/|doi:)\s*/i
const WORK_ID_RE = /^(?:https?:\/\/openalex\.org\/)?W\d+$/i
const AUTHOR_ID_RE = /^(?:https?:\/\/openalex\.org\/)?A\d+$/i

export function emptyContextForm() {
  return { institution: '', publications: '', coauthors: '', yearStart: '', yearEnd: '' }
}

export function parseList(text) {
  if (typeof text !== 'string') return []
  const seen = new Set()
  const items = []
  for (const part of text.split(/[\n;,]/)) {
    const value = part.trim()
    if (value && !seen.has(value.toLowerCase())) {
      seen.add(value.toLowerCase())
      items.push(value)
    }
  }
  return items
}

export function normalizePublicationId(value) {
  const doi = value.replace(DOI_PREFIX_RE, '').trim().toLowerCase()
  if (DOI_RE.test(doi)) return doi
  if (WORK_ID_RE.test(value.trim())) return value.trim().replace(/^https?:\/\/openalex\.org\//i, '').toUpperCase()
  return null
}

/**
 * Build the request pieces from the form.
 * Returns { institutionHint, context, errors, provided }. `context` is null when nothing
 * beyond the name was supplied, so name-only searches send no context at all.
 */
export function buildAuthorContext(form) {
  const f = { ...emptyContextForm(), ...(form || {}) }
  const errors = []
  const context = {}

  const institution = String(f.institution || '').trim()

  const rawPublications = parseList(f.publications)
  if (rawPublications.length > MAX_ITEMS) errors.push(`Enter at most ${MAX_ITEMS} publication identifiers.`)
  const publications = []
  for (const raw of rawPublications.slice(0, MAX_ITEMS)) {
    const id = normalizePublicationId(raw)
    if (id) { if (!publications.includes(id)) publications.push(id) }
    else errors.push(`"${raw}" is not a DOI or OpenAlex work ID (titles are not accepted).`)
  }
  if (publications.length) context.publications = publications

  const coauthors = parseList(f.coauthors)
  if (coauthors.length > MAX_ITEMS) errors.push(`Enter at most ${MAX_ITEMS} coauthors.`)
  if (coauthors.length) {
    context.coauthors = coauthors.slice(0, MAX_ITEMS).map((value) =>
      AUTHOR_ID_RE.test(value)
        ? { openalex_id: value.replace(/^https?:\/\/openalex\.org\//i, '').toUpperCase() }
        : { name: value })
  }

  const start = String(f.yearStart ?? '').trim()
  const end = String(f.yearEnd ?? '').trim()
  if (start || end) {
    const a = Number(start)
    const b = Number(end)
    if (!start || !end) errors.push('Enter both a start and an end year, or neither.')
    else if (!Number.isInteger(a) || !Number.isInteger(b)) errors.push('Years must be whole numbers.')
    else if (a < YEAR_MIN || b > YEAR_MAX || a > b) errors.push(`Years must be between ${YEAR_MIN} and ${YEAR_MAX}, start before end.`)
    else {
      context.active_year_start = a
      context.active_year_end = b
    }
  }

  return {
    institutionHint: institution || null,
    context: Object.keys(context).length ? context : null,
    errors,
    provided: {
      institution: Boolean(institution),
      publications: publications.length > 0,
      coauthors: coauthors.length > 0,
      active_years: context.active_year_start !== undefined,
    },
  }
}

const STATUS_LABELS = {
  observed: 'Observed',
  unavailable_query_input_absent: 'Not provided',
  unavailable_candidate_data_absent: 'Candidate profile has no data',
  unavailable_not_retrieved: 'Not retrieved',
  unavailable_retrieval_failed: 'Retrieval failed',
  unavailable_inconclusive: 'Inconclusive',
  unavailable_input_unresolvable: 'Input could not be compared',
}

export function describeSignalStatus(status, availability) {
  if (status && STATUS_LABELS[status]) return STATUS_LABELS[status]
  return availability === 'available' ? 'Observed' : 'Unavailable'
}

export const SIGNAL_ORDER = [
  'name_similarity', 'institution_similarity', 'publication_overlap', 'coauthor_overlap', 'temporal_compatibility',
]

/** Always list all five signals; an absent entry is shown as unavailable, never as agreement. */
export function signalRows(evidence) {
  const byName = new Map((Array.isArray(evidence) ? evidence : []).map((e) => [e.signal_name || e.signal, e]))
  return SIGNAL_ORDER.map((name) => {
    const e = byName.get(name)
    const score = e ? (e.normalized_score ?? e.score ?? null) : null
    const observed = typeof score === 'number' && (e?.status ? e.status === 'observed' : e?.availability === 'available')
    return {
      name,
      label: name.replaceAll('_', ' '),
      observed,
      score: observed ? score : null,
      status: e ? describeSignalStatus(e.status, e.availability) : 'Unavailable',
      explanation: e?.explanation || '',
    }
  })
}
