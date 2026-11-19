import React from 'react';

const fieldStyle = { display: 'flex', flexDirection: 'column', gap: '0.2rem', fontSize: '0.82rem', color: '#475569' };
const inputStyle = { padding: '0.4rem 0.5rem', border: '1px solid #cbd5e1', borderRadius: '6px', font: 'inherit' };

/**
 * Optional known-context fields for author resolution. Every field may stay empty; empty fields
 * are omitted from the request and reported by the backend as "not provided", never as a mismatch.
 */
export default function AuthorContextForm({ value, onChange, errors = [], disabled = false }) {
  const set = (key) => (event) => onChange({ ...value, [key]: event.target.value });
  return (
    <details className="author-context-form" style={{ margin: '0.6rem 0' }}>
      <summary style={{ cursor: 'pointer', fontSize: '0.85rem', color: '#334155' }}>
        Add known context (optional) — improves evidence, never required
      </summary>
      <div style={{ display: 'grid', gap: '0.6rem', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', marginTop: '0.6rem' }}>
        <label style={fieldStyle}>
          Institution
          <input style={inputStyle} type="text" value={value.institution} onChange={set('institution')} disabled={disabled}
                 placeholder="e.g. University of Montreal" maxLength={300} />
        </label>
        <label style={fieldStyle}>
          Known publications (DOI or OpenAlex work ID)
          <textarea style={inputStyle} rows={2} value={value.publications} onChange={set('publications')} disabled={disabled}
                    placeholder="10.1000/xyz123, W2741809807" />
        </label>
        <label style={fieldStyle}>
          Known coauthors (OpenAlex author IDs are scored; names alone are not)
          <textarea style={inputStyle} rows={2} value={value.coauthors} onChange={set('coauthors')} disabled={disabled}
                    placeholder="A5023888391, A5012345678" />
        </label>
        <div style={{ ...fieldStyle, flexDirection: 'row', gap: '0.5rem', alignItems: 'flex-end' }}>
          <label style={fieldStyle}>
            Active from
            <input style={{ ...inputStyle, width: '6rem' }} type="number" value={value.yearStart} onChange={set('yearStart')}
                   disabled={disabled} min="1800" max="2200" placeholder="year" />
          </label>
          <label style={fieldStyle}>
            to
            <input style={{ ...inputStyle, width: '6rem' }} type="number" value={value.yearEnd} onChange={set('yearEnd')}
                   disabled={disabled} min="1800" max="2200" placeholder="year" />
          </label>
        </div>
      </div>
      {errors.length > 0 && (
        <ul role="alert" style={{ margin: '0.5rem 0 0', paddingLeft: '1.1rem', color: '#b91c1c', fontSize: '0.82rem' }}>
          {errors.map((message) => <li key={message}>{message}</li>)}
        </ul>
      )}
    </details>
  );
}
