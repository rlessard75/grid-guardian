import { useState, useEffect } from 'react'
import StatusBadge from './StatusBadge.jsx'

export default function ReviewPane({ prId, onDecisionSaved }) {
  const [review, setReview] = useState(null)
  const [decision, setDecision] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [expandedEvidence, setExpandedEvidence] = useState({})

  useEffect(() => {
    if (!prId) return
    setLoading(true)
    setError(null)
    setDecision(null)

    fetch(`/api/reviews/${prId}`)
      .then(r => r.json())
      .then(data => { setReview(data); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })

    fetch(`/api/decisions/${prId}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setDecision(d) })
      .catch(() => {})
  }, [prId])

  async function recordDecision(choice) {
    const body = { pr_id: prId, decision: choice, reviewer: 'reviewer' }
    const res = await fetch('/api/decisions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const d = await res.json()
    setDecision(d)
    if (onDecisionSaved) onDecisionSaved(prId, choice)
  }

  if (!prId) return null
  if (loading) return <div className="empty-state"><p>Loading review…</p></div>
  if (error)   return <div className="empty-state"><p>Error: {error}</p></div>
  if (!review) return null

  const pr = review.context_snapshot?.pr_data ?? {}
  const govFindings = review.raw_findings?.governance ?? []
  const patFindings = review.raw_findings?.patterns ?? []
  const comments    = review.comments ?? []
  const recs        = review.recommendations ?? []
  const violations  = review.summary?.violations ?? []

  // Group comments by file
  const byFile = {}
  for (const c of comments) {
    const key = c.file ?? 'unknown'
    if (!byFile[key]) byFile[key] = []
    byFile[key].push(c)
  }

  return (
    <div>
      {/* ── Header ── */}
      <div className="review-header">
        <h1>{pr.title || review.pr_id}</h1>
        <div className="review-meta">
          <span>🔖 {review.pr_id}</span>
          {pr.author && <span>👤 {pr.author}</span>}
          {pr.branch && <span>⎇ {pr.branch}</span>}
          {pr.created_at && <span>🕐 {new Date(pr.created_at).toLocaleString()}</span>}
        </div>
        <StatusBadge status={review.status} />
      </div>

      {/* ── Summary ── */}
      <div className="section">
        <div className="section-heading">Summary</div>
        <div className="section-body">
          {violations.length === 0 ? (
            <div className="clean-banner">
              <span style={{ fontSize: 20 }}>✅</span>
              No violations found. This PR looks clean.
            </div>
          ) : (
            <div className="violation-chips">
              {violations.map(v => (
                <span key={v.category} className={`violation-chip ${v.category}`}>
                  {v.count}× {v.category}
                </span>
              ))}
            </div>
          )}
          <div style={{ marginTop: 10, fontSize: 12, color: '#64748b' }}>
            {govFindings.length} governance finding(s) · {patFindings.length} pattern finding(s)
            · {(review.context_snapshot?.tool_call_log ?? []).length} tool call(s) logged
          </div>
        </div>
      </div>

      {/* ── Comments ── */}
      {comments.length > 0 && (
        <div className="section">
          <div className="section-heading">Comments ({comments.length})</div>
          <div className="section-body">
            {Object.entries(byFile).map(([file, fileComments]) => (
              <div key={file} className="file-group">
                <div className="file-name">{file}</div>
                {fileComments.map((c, i) => (
                  <div key={i} className={`comment-card ${c.severity}`}>
                    <div className="comment-line">
                      {c.line ? `Line ${c.line} ` : ''}
                      <span className={`severity ${c.severity}`}>{c.severity}</span>
                    </div>
                    <div className="comment-body">{c.body}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Recommendations ── */}
      {recs.length > 0 && (
        <div className="section">
          <div className="section-heading">Recommendations ({recs.length})</div>
          <div className="section-body">
            {recs.map((r, i) => (
              <div key={i} className="rec-card">
                <div className="rec-title">{r.title}</div>
                <div className="rec-body">{r.body}</div>
                {r.linked_evidence?.length > 0 && (
                  <div className="evidence-chips">
                    {r.linked_evidence.map(ev => (
                      <span
                        key={ev}
                        className="evidence-chip"
                        title={ev}
                        onClick={() => setExpandedEvidence(prev => ({
                          ...prev,
                          [ev]: !prev[ev],
                        }))}
                      >
                        {ev}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Tool call log ── */}
      {(review.context_snapshot?.tool_call_log ?? []).length > 0 && (
        <details style={{ marginBottom: 16 }}>
          <summary style={{ cursor: 'pointer', fontSize: 12, color: '#94a3b8', padding: '6px 0' }}>
            Tool call log ({review.context_snapshot.tool_call_log.length} calls)
          </summary>
          <div className="section" style={{ marginTop: 6 }}>
            <div className="section-body">
              {review.context_snapshot.tool_call_log.map((entry, i) => (
                <div key={i} style={{
                  fontFamily: 'monospace',
                  fontSize: 11,
                  padding: '4px 0',
                  borderBottom: '1px solid #f1f5f9',
                  color: '#475569',
                }}>
                  <span style={{ color: '#6366f1', fontWeight: 600 }}>{entry.tool}</span>
                  {' → '}
                  <span>{entry.result_summary}</span>
                  <span style={{ color: '#94a3b8', marginLeft: 8 }}>
                    {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </details>
      )}

      {/* ── Decision buttons ── */}
      {decision ? (
        <div className={`decision-banner ${decision.decision}`}>
          {decision.decision === 'approved'
            ? `✓ Approved by ${decision.reviewer}`
            : `✗ Changes requested by ${decision.reviewer}`}
          {' · '}
          {new Date(decision.timestamp).toLocaleString()}
        </div>
      ) : (
        <div className="actions">
          <button className="btn btn-approve" onClick={() => recordDecision('approved')}>
            ✓ Approve PR
          </button>
          <button className="btn btn-reject" onClick={() => recordDecision('changes_requested')}>
            ✗ Request Changes
          </button>
        </div>
      )}
    </div>
  )
}
