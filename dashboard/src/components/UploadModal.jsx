import { useState, useRef, useCallback } from 'react'

const PHASES = [
  { id: 'parse',      label: 'Parse',              icon: '📋' },
  { id: 'governance', label: 'Governance Sweep',    icon: '🔒' },
  { id: 'pattern',    label: 'Pattern Recognition', icon: '🔍' },
  { id: 'report',     label: 'Report',              icon: '📄' },
]

export default function UploadModal({ onClose, onComplete }) {
  const [file, setFile]           = useState(null)
  const [fileType, setFileType]   = useState(null) // 'json' | 'diff'
  const [pastedDiff, setPastedDiff] = useState('')
  const [dragOver, setDragOver]   = useState(false)
  const [title, setTitle]         = useState('')
  const [description, setDesc]    = useState('')
  const [author, setAuthor]       = useState('')
  const [branch, setBranch]       = useState('')
  const [running, setRunning]     = useState(false)
  const [phaseStatus, setPhaseStatus] = useState({}) // phase → 'pending'|'active'|'done'|'error'
  const [phaseMessages, setPhaseMessages] = useState({})
  const [currentPrId, setCurrentPrId] = useState(null)
  const fileInputRef = useRef(null)
  const timerRef    = useRef(null)

  const isDiffMode = fileType === 'diff' || (!file && pastedDiff)

  function handleFile(f) {
    if (!f) return
    setFile(f)
    const ext = f.name.split('.').pop().toLowerCase()
    if (ext === 'json') setFileType('json')
    else setFileType('diff')
  }

  function onDrop(e) {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files[0])
  }

  function parseDiffToFixture(diffText, form) {
    const prId = `PR-UPLOAD-${Date.now()}`
    const filesChanged = []
    const blocks = diffText.split(/^diff --git /m).filter(Boolean)

    for (const block of blocks) {
      const pathMatch = block.match(/^a\/.+? b\/(.+)$/m)
      const path = pathMatch ? pathMatch[1].trim() : 'unknown/uploaded.patch'
      const isAdded   = /^new file mode/m.test(block)
      const isDeleted = /^deleted file mode/m.test(block)
      const changeType = isAdded ? 'added' : isDeleted ? 'deleted' : 'modified'
      const ext = path.split('.').pop()?.toLowerCase() ?? ''
      const langMap = { py:'python', ts:'typescript', tsx:'typescript', js:'javascript',
                        jsx:'javascript', yaml:'yaml', yml:'yaml', go:'go',
                        json:'json', md:'markdown', rb:'ruby', java:'java' }
      filesChanged.push({
        path,
        language: langMap[ext] ?? ext ?? 'unknown',
        change_type: changeType,
        diff: 'diff --git ' + block,
      })
    }

    if (filesChanged.length === 0 && diffText.trim()) {
      filesChanged.push({
        path: 'unknown/uploaded.patch',
        language: 'unknown',
        change_type: 'modified',
        diff: diffText,
      })
    }

    return {
      pr_id: prId,
      title: form.title || 'Uploaded diff',
      description: form.description ?? '',
      author: form.author || 'demo-user',
      branch: form.branch || 'feature/demo-upload',
      base_branch: 'main',
      created_at: new Date().toISOString(),
      files_changed: filesChanged,
    }
  }

  async function handleSubmit() {
    setRunning(true)
    setPhaseStatus({})
    setPhaseMessages({})

    let fixture
    try {
      if (fileType === 'json' && file) {
        const text = await file.text()
        fixture = JSON.parse(text)
      } else {
        const diffText = file ? await file.text() : pastedDiff
        if (!diffText.trim()) { alert('Provide a diff file or paste diff text.'); setRunning(false); return }
        if (!title.trim())    { alert('PR title is required for diff uploads.'); setRunning(false); return }
        fixture = parseDiffToFixture(diffText, { title, description, author, branch })
      }
    } catch (e) {
      alert(`Parse error: ${e.message}`)
      setRunning(false)
      return
    }

    // POST to start the review
    const res = await fetch('/api/reviews', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fixture),
    })
    const { pr_id } = await res.json()
    setCurrentPrId(pr_id)

    // Poll GET /api/reviews/{pr_id} — more reliable than SSE on proxied deployments
    let lastIdx = 0
    timerRef.current = setInterval(async () => {
      try {
        const r = await fetch(`/api/reviews/${pr_id}`)
        const data = await r.json()

        // Process any new progress events
        const events = data.progress ?? []
        for (let i = lastIdx; i < events.length; i++) {
          const ev = events[i]
          if (ev.phase === 'complete') {
            clearInterval(timerRef.current)
            setPhaseStatus(prev => {
              const next = { ...prev }
              for (const p of PHASES) if (!next[p.id]) next[p.id] = 'done'
              return next
            })
            setTimeout(() => onComplete(pr_id), 600)
            return
          }
          if (ev.phase === 'error') {
            clearInterval(timerRef.current)
            setRunning(false)
            return
          }
          setPhaseStatus(prev => {
            const next = { ...prev }
            let found = false
            for (const p of PHASES) {
              if (p.id === ev.phase) { next[p.id] = 'active'; found = true }
              else if (!found)        next[p.id] = 'done'
            }
            return next
          })
          if (ev.message) {
            setPhaseMessages(prev => ({ ...prev, [ev.phase]: ev.message }))
          }
        }
        lastIdx = events.length

        // Review file written — pipeline finished
        if (data.status && data.status !== 'running') {
          clearInterval(timerRef.current)
          setPhaseStatus(prev => {
            const next = { ...prev }
            for (const p of PHASES) if (!next[p.id]) next[p.id] = 'done'
            return next
          })
          setTimeout(() => onComplete(pr_id), 600)
        }
      } catch (_) {
        // Network hiccup — keep polling
      }
    }, 1500)
  }

  function phaseState(id) {
    return phaseStatus[id] ?? 'pending'
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2>Submit PR for Review</h2>
          <button className="modal-close" onClick={onClose} disabled={running}>✕</button>
        </div>

        {running ? (
          /* ── Progress view ── */
          <div className="modal-body">
            <div style={{ marginBottom: 16, fontSize: 13, color: '#64748b' }}>
              Running review for <strong>{currentPrId}</strong>…
            </div>
            <div className="progress-view">
              {PHASES.map(p => {
                const state = phaseState(p.id)
                const icon = state === 'done'  ? '✓'
                           : state === 'error' ? '✗'
                           : state === 'active' ? '⟳'
                           : p.icon
                return (
                  <div key={p.id} className="phase-row">
                    <div className={`phase-icon ${state}`}>{icon}</div>
                    <div className="phase-info">
                      <div className="phase-name">{p.label}</div>
                      {phaseMessages[p.id] && (
                        <div className="phase-message">{phaseMessages[p.id]}</div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          /* ── Upload form ── */
          <div className="modal-body">
            {/* Drop zone */}
            <div
              className={`drop-zone${dragOver ? ' over' : ''}`}
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="drop-zone-icon">📂</div>
              <div className="drop-zone-label">
                Drop a PR fixture (.json) or diff file (.diff / .patch)
              </div>
              <div className="drop-zone-hint">
                Accepts JSON PR fixtures or raw unified diffs
              </div>
              {file && (
                <div className="drop-zone-file">
                  {file.name} ({fileType})
                </div>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.diff,.patch"
              style={{ display: 'none' }}
              onChange={e => handleFile(e.target.files[0])}
            />

            {/* Or paste */}
            {!file && (
              <>
                <div className="or-divider">or paste a diff</div>
                <textarea
                  className="diff-paste-area"
                  placeholder="Paste unified diff here (diff --git a/... b/...)"
                  value={pastedDiff}
                  onChange={e => { setPastedDiff(e.target.value); if (e.target.value) setFileType('diff') }}
                />
              </>
            )}

            {/* Form fields — shown for diff mode */}
            {(isDiffMode) && (
              <div style={{ marginTop: 16 }}>
                <div className="field">
                  <label>PR Title <span style={{ color: '#dc2626' }}>*</span></label>
                  <input
                    type="text"
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    placeholder="e.g. Add S3 backup uploader"
                  />
                </div>
                <div className="field">
                  <label>Description</label>
                  <textarea
                    value={description}
                    onChange={e => setDesc(e.target.value)}
                    placeholder="Optional: what does this PR do?"
                    style={{ minHeight: 60 }}
                  />
                </div>
                <div style={{ display: 'flex', gap: 12 }}>
                  <div className="field" style={{ flex: 1 }}>
                    <label>Author</label>
                    <input
                      type="text"
                      value={author}
                      onChange={e => setAuthor(e.target.value)}
                      placeholder="demo-user"
                    />
                  </div>
                  <div className="field" style={{ flex: 1 }}>
                    <label>Branch</label>
                    <input
                      type="text"
                      value={branch}
                      onChange={e => setBranch(e.target.value)}
                      placeholder="feature/demo-upload"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Sample uploads hint */}
            <div style={{ marginTop: 14, fontSize: 12, color: '#94a3b8', background: '#f8fafc', padding: '8px 10px', borderRadius: 6 }}>
              💡 Try dragging in one of the sample diffs from{' '}
              <code style={{ background: '#e2e8f0', padding: '1px 5px', borderRadius: 3 }}>
                dashboard/public/sample_uploads/
              </code>
            </div>
          </div>
        )}

        {!running && (
          <div className="modal-footer">
            <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={!file && !pastedDiff.trim()}
            >
              Run Review
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
