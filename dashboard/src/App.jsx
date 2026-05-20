import { useState, useEffect, useCallback } from 'react'
import PRList from './components/PRList.jsx'
import ReviewPane from './components/ReviewPane.jsx'
import UploadModal from './components/UploadModal.jsx'

export default function App() {
  const [reviews, setReviews]         = useState([])
  const [selectedId, setSelectedId]   = useState(null)
  const [showModal, setShowModal]     = useState(false)
  const [pollTimer, setPollTimer]     = useState(null)

  const fetchReviews = useCallback(async () => {
    try {
      const res = await fetch('/api/reviews')
      const data = await res.json()
      setReviews(data)
    } catch (e) {
      console.error('Failed to fetch reviews', e)
    }
  }, [])

  useEffect(() => {
    fetchReviews()
  }, [fetchReviews])

  function handleUploadComplete(prId) {
    setShowModal(false)
    fetchReviews().then(() => setSelectedId(prId))
  }

  function handleDecisionSaved() {
    // Refresh list so status chips can update if needed
    fetchReviews()
  }

  return (
    <div className="app">
      {/* ── Top bar ── */}
      <header className="topbar">
        <span className="topbar-title">
          Grid <span>Guardian</span>
        </span>
        <button
          className="btn btn-primary"
          style={{ width: 'auto', flex: 'none', padding: '7px 16px', fontSize: 13 }}
          onClick={() => setShowModal(true)}
        >
          + Submit PR for Review
        </button>
      </header>

      {/* ── Body ── */}
      <div className="body">
        {/* Left pane */}
        <aside className="sidebar">
          <div className="sidebar-header">PR Reviews</div>
          <PRList
            reviews={reviews}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </aside>

        {/* Right pane */}
        <main className="main">
          {selectedId ? (
            <ReviewPane
              key={selectedId}
              prId={selectedId}
              onDecisionSaved={handleDecisionSaved}
            />
          ) : (
            <div className="empty-state">
              <h2>Grid Guardian</h2>
              <p>Select a review from the left, or submit a new PR for review.</p>
            </div>
          )}
        </main>
      </div>

      {/* ── Upload modal ── */}
      {showModal && (
        <UploadModal
          onClose={() => setShowModal(false)}
          onComplete={handleUploadComplete}
        />
      )}
    </div>
  )
}
