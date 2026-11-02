export default function StatsBar({ data }) {
  if (!data) return null

  // Calculate source distribution
  const papers = data.papers || []
  const distribution = {}
  papers.forEach(p => {
    const sources = p.source_list || [p.best_source]
    sources.forEach(s => {
      if (s) distribution[s] = (distribution[s] || 0) + 1
    })
  })

  const sourceKeys = Object.keys(distribution).sort((a, b) => distribution[b] - distribution[a])

  return (
    <div className="stats-container">
      <div className="stats-bar">
        <div className="stat-item">
          <span className="stat-value">{data.total}</span>
          <span className="stat-label">unique papers</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-item">
          <span className="stat-value">{data.raw_records}</span>
          <span className="stat-label">raw records</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-item">
          <span className="stat-value">{data.merged_count}</span>
          <span className="stat-label">duplicates merged</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-item">
          <span className="stat-value">{data.time_ms}ms</span>
          <span className="stat-label">latency</span>
        </div>
        {data.cache_hit && (
          <>
            <div className="stat-divider" />
            <div className="stat-item">
              <span className="cache-hit">⚡ cached</span>
            </div>
          </>
        )}
      </div>

      <div className="source-distribution">
        {sourceKeys.map(key => (
          <div key={key} className="source-stat">
            <span className={`dot dot-${key}`} />
            <span style={{ textTransform: 'capitalize' }}>{key.replace('_', ' ')}</span>
            <span style={{ opacity: 0.5 }}>{distribution[key]}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
