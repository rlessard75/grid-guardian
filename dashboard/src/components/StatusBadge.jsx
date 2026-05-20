export default function StatusBadge({ status }) {
  const labels = {
    clean: '✓ Clean',
    issues_found: '✗ Issues Found',
    running: '⟳ Running…',
  }
  return (
    <span className={`badge ${status}`}>
      {labels[status] ?? status}
    </span>
  )
}
