import StatusBadge from './StatusBadge.jsx'

export default function PRList({ reviews, selectedId, onSelect }) {
  if (!reviews.length) {
    return (
      <div className="pr-list-empty">
        No reviews yet.<br />
        Click <strong>Submit PR for Review</strong> to get started.
      </div>
    )
  }

  return (
    <div className="pr-list">
      {reviews.map(r => (
        <div
          key={r.pr_id}
          className={`pr-item${r.pr_id === selectedId ? ' selected' : ''}`}
          onClick={() => onSelect(r.pr_id)}
        >
          <div className="pr-item-id">{r.pr_id}</div>
          <div className="pr-item-title">{r.title || '(no title)'}</div>
          <div className="pr-item-meta">
            <StatusBadge status={r.status} />
            {r.author && <span className="pr-item-author">by {r.author}</span>}
          </div>
        </div>
      ))}
    </div>
  )
}
