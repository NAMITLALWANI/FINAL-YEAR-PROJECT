export default function SourceStatusPanel({ statuses }) {
  if (!statuses) return null

  return (
    <div className="source-panel">
      {Object.entries(statuses).map(([source, info]) => {
        let label = source
        let statusClass = info.status
        let subText = ''

        if (source === 'scholar') {
          if (info.cached) {
            label = 'Scholar Cached'
            statusClass = 'ok'
          } else if (info.demo_fallback) {
            label = 'Scholar Disabled (Demo)'
            statusClass = 'disabled'
          } else if (info.status === 'ok') {
            label = 'Scholar Enriched'
          } else if (info.reason === 'captcha') {
            label = 'Scholar Blocked'
            statusClass = 'failed'
          }
        }

        if (info.records != null && info.status === 'ok') {
          subText = ` · ${info.records}`
        } else if (info.reason && info.status !== 'ok') {
          subText = ` · ${info.reason}`
        }

        return (
          <div key={source} className={`source-chip ${statusClass}`}>
            <span className="source-dot" />
            <span className="source-label" style={{ fontWeight: 800 }}>{label.toUpperCase()}</span>
            {subText && <span className="source-subtext" style={{ opacity: 0.7, marginLeft: '4px' }}>{subText}</span>}
          </div>
        )
      })}
    </div>
  )
}
