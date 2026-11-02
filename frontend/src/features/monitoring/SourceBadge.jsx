export default function SourceBadge({ source }) {
  return (
    <span className={`source-badge badge-${source || 'unknown'}`}>
      {source || 'unknown'}
    </span>
  )
}
