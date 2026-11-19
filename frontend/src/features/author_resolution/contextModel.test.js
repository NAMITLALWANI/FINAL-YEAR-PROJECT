// Run with: node --test frontend/src/features/author_resolution/contextModel.test.js
import test from 'node:test'
import assert from 'node:assert/strict'
import { buildAuthorContext, parseList, signalRows, emptyContextForm, normalizePublicationId } from './contextModel.js'

test('name-only search sends no context and no institution', () => {
  const r = buildAuthorContext(emptyContextForm())
  assert.equal(r.context, null)
  assert.equal(r.institutionHint, null)
  assert.deepEqual(r.errors, [])
  assert.deepEqual(r.provided, { institution: false, publications: false, coauthors: false, active_years: false })
})

test('institution only is submitted as a hint and nothing else is invented', () => {
  const r = buildAuthorContext({ institution: '  Example Institute ' })
  assert.equal(r.institutionHint, 'Example Institute')
  assert.equal(r.context, null)
  assert.equal(r.provided.institution, true)
})

test('publications and coauthors are parsed, normalised and de-duplicated', () => {
  const r = buildAuthorContext({
    publications: 'https://doi.org/10.1000/ABC, 10.1000/abc\nW123456',
    coauthors: 'Bob Jones; A5023888391',
    yearStart: '2015', yearEnd: '2020',
  })
  assert.deepEqual(r.context.publications, ['10.1000/abc', 'W123456'])
  assert.deepEqual(r.context.coauthors, [{ name: 'Bob Jones' }, { openalex_id: 'A5023888391' }])
  assert.equal(r.context.active_year_start, 2015)
  assert.deepEqual(r.errors, [])
})

test('titles and malformed identifiers are rejected, not silently sent', () => {
  const r = buildAuthorContext({ publications: 'A Paper Title, 10.1000/ok' })
  assert.equal(r.errors.length, 1)
  assert.deepEqual(r.context.publications, ['10.1000/ok'])
})

test('year validation requires both ends, order and range', () => {
  assert.equal(buildAuthorContext({ yearStart: '2020' }).errors.length, 1)
  assert.equal(buildAuthorContext({ yearStart: '2021', yearEnd: '2020' }).errors.length, 1)
  assert.equal(buildAuthorContext({ yearStart: '20x0', yearEnd: '2020' }).errors.length, 1)
  assert.equal(buildAuthorContext({ yearStart: '2000', yearEnd: '2020' }).context.active_year_end, 2020)
})

test('list parsing and publication id normalisation', () => {
  assert.deepEqual(parseList('a, b\n b ;c'), ['a', 'b', 'c'])
  assert.equal(normalizePublicationId('doi:10.1000/X'), '10.1000/x')
  assert.equal(normalizePublicationId('nonsense'), null)
})

test('signal rows always list five signals and never show missing evidence as agreement', () => {
  const rows = signalRows([
    { signal_name: 'name_similarity', normalized_score: 1.0, status: 'observed', availability: 'available' },
    { signal_name: 'coauthor_overlap', normalized_score: null, status: 'unavailable_retrieval_failed', availability: 'unavailable' },
  ])
  assert.equal(rows.length, 5)
  assert.equal(rows[0].observed, true)
  const coauthor = rows.find((r) => r.name === 'coauthor_overlap')
  assert.equal(coauthor.observed, false)
  assert.equal(coauthor.score, null)
  assert.equal(coauthor.status, 'Retrieval failed')
  assert.equal(rows.find((r) => r.name === 'publication_overlap').status, 'Unavailable')
})

test('an observed zero stays an observed zero', () => {
  const rows = signalRows([{ signal_name: 'temporal_compatibility', normalized_score: 0, status: 'observed', availability: 'available' }])
  const t = rows.find((r) => r.name === 'temporal_compatibility')
  assert.equal(t.observed, true)
  assert.equal(t.score, 0)
})
