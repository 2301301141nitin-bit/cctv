import { useState, useRef } from 'react'
import { Upload, Search, Image as ImageIcon, FileText, Video, Database } from 'lucide-react'
import axios from 'axios'

const API = ''

export default function StaticAnalysis() {
  const [activeTab, setActiveTab] = useState('upload')
  const [searchMode, setSearchMode] = useState('text')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchImage, setSearchImage] = useState(null)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')
  const [uploading, setUploading] = useState(false)
  const [indexStats, setIndexStats] = useState(null)
  const fileRef = useRef()

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/api/static-analysis/index-stats`)
      setIndexStats(res.data)
    } catch {}
  }

  useState(() => { fetchStats() })

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setUploadStatus('Uploading & processing...')
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await axios.post(`${API}/api/static-analysis/upload`, formData)
      setUploadStatus(`✅ ${res.data.message} (Video ID: ${res.data.video_id})`)
      fetchStats()
    } catch (err) {
      setUploadStatus(`❌ Upload failed: ${err.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleTextSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setLoading(true)
    setResults([])
    const formData = new FormData()
    formData.append('query', searchQuery)
    try {
      const res = await axios.post(`${API}/api/static-analysis/search/text`, formData)
      setResults(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleImageSearch = async (e) => {
    e.preventDefault()
    if (!searchImage) return
    setLoading(true)
    setResults([])
    const formData = new FormData()
    formData.append('file', searchImage)
    try {
      const res = await axios.post(`${API}/api/static-analysis/search/image`, formData)
      setResults(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fmtTime = (s) => {
    const h = Math.floor(s / 3600)
    const m = Math.floor((s % 3600) / 60)
    const sec = Math.floor(s % 60)
    return h > 0 ? `${h}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}` : `${m}:${String(sec).padStart(2,'0')}`
  }

  return (
    <>
      <div className="page-header">
        <h2>🔍 Static Forensic Analysis</h2>
        <p>Upload CCTV footage for AI-powered frame extraction and semantic search</p>
      </div>
      <div className="page-body">
        {/* Stats Row */}
        {indexStats && (
          <div className="card-grid card-grid-3 mb-6 animate-in">
            <div className="stat-card">
              <div className="stat-label">Indexed Frames</div>
              <div className="stat-value">{indexStats.total_indexed_frames.toLocaleString()}</div>
              <div className="stat-sub">In FAISS vector store</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Embedding Dimension</div>
              <div className="stat-value">{indexStats.embedding_dim}</div>
              <div className="stat-sub">CLIP ViT-B/32</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Metadata Entries</div>
              <div className="stat-value">{indexStats.metadata_entries.toLocaleString()}</div>
              <div className="stat-sub">Frame records</div>
            </div>
          </div>
        )}

        {/* Tab Bar */}
        <div className="tab-bar mb-6" style={{display:'inline-flex'}}>
          <button className={`tab-item ${activeTab === 'upload' ? 'active' : ''}`} onClick={() => setActiveTab('upload')}>
            <Upload size={14} style={{marginRight:6, verticalAlign:'middle'}} /> Upload Footage
          </button>
          <button className={`tab-item ${activeTab === 'search' ? 'active' : ''}`} onClick={() => setActiveTab('search')}>
            <Search size={14} style={{marginRight:6, verticalAlign:'middle'}} /> Analyze & Search
          </button>
        </div>

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="animate-in">
            <div className="card">
              <div className="card-header">
                <div className="card-title"><Video size={18} /> Upload CCTV Video</div>
              </div>
              <div className="upload-zone" onClick={() => fileRef.current?.click()}>
                <Upload size={48} className="icon" />
                <h3>Click to select video file</h3>
                <p>Supports MP4, AVI, MOV, MKV • AI will extract & index frames automatically</p>
                <input ref={fileRef} type="file" accept="video/*" style={{display:'none'}} onChange={handleUpload} />
              </div>
              {uploadStatus && (
                <div style={{marginTop:'1rem', padding:'0.85rem', background:'rgba(59,130,246,0.08)', borderRadius:'var(--radius-md)', fontSize:'0.85rem'}}>
                  {uploadStatus}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="animate-in">
            <div className="card mb-6">
              <div className="tab-bar mb-4" style={{display:'inline-flex'}}>
                <button className={`tab-item ${searchMode === 'text' ? 'active' : ''}`} onClick={() => setSearchMode('text')}>
                  <FileText size={14} style={{marginRight:4, verticalAlign:'middle'}} /> Keyword Search
                </button>
                <button className={`tab-item ${searchMode === 'image' ? 'active' : ''}`} onClick={() => setSearchMode('image')}>
                  <ImageIcon size={14} style={{marginRight:4, verticalAlign:'middle'}} /> Image Search
                </button>
              </div>

              {searchMode === 'text' ? (
                <form onSubmit={handleTextSearch} className="flex gap-3">
                  <input
                    className="form-input"
                    type="text"
                    placeholder="e.g. 'red car', 'person in black jacket', 'someone walking'"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <button className="btn btn-primary" type="submit" disabled={loading}>
                    {loading ? 'Searching...' : 'Search'}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleImageSearch} className="flex gap-3 items-center">
                  <input className="form-input" type="file" accept="image/*" onChange={(e) => setSearchImage(e.target.files[0])} />
                  <button className="btn btn-primary" type="submit" disabled={loading || !searchImage}>
                    {loading ? 'Searching...' : 'Search'}
                  </button>
                </form>
              )}
            </div>

            {/* Results */}
            <div className="results-grid">
              {results.map((res, idx) => (
                <div key={idx} className="result-card animate-in" style={{animationDelay: `${idx * 50}ms`}}>
                  <img
                    src={`${API}${res.filepath}`}
                    alt={`Frame at ${fmtTime(res.timestamp)}`}
                    loading="lazy"
                    onError={(e) => {
                      e.target.style.display = 'none'
                      e.target.parentElement.insertAdjacentHTML('afterbegin',
                        `<div style="display:flex;align-items:center;justify-content:center;height:180px;background:var(--bg-secondary);color:var(--text-muted);font-size:0.8rem">⚠️ Frame unavailable</div>`
                      )
                    }}
                  />
                  <div className="result-meta">
                    <div>
                      <span className="timestamp-badge">{fmtTime(res.timestamp)}</span>
                      <div className="text-xs text-muted mt-2">Video #{res.video_id}</div>
                    </div>
                    <span className={`score-badge ${res.score >= 0.7 ? 'score-high' : res.score >= 0.5 ? 'score-mid' : 'score-low'}`}>
                      {(res.score * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {results.length === 0 && !loading && (
              <div className="empty-state">
                <Database size={48} className="icon" />
                <h3>No results yet</h3>
                <p>Upload footage and perform a search to see AI-matched frames</p>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  )
}
