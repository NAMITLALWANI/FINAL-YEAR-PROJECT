export default function StatsBar({ data }) {
  if (!data) return null
  return (
    <div className="stats-bar">
      <div className="stat-item">
        <span className="stat-value">{data.total}</span>
        <span className="stat-label">papers</span>
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
        <span className="stat-label">response time</span>
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
  )
}
