import { useState } from 'react'
import { Upload, Search, Image as ImageIcon, Video, FileText } from 'lucide-react'
import axios from 'axios'
import './index.css'

const API_URL = 'http://localhost:8001'

function App() {
  const [activeTab, setActiveTab] = useState('upload') // upload, search
  const [searchMode, setSearchMode] = useState('text') // text, image
  const [searchQuery, setSearchQuery] = useState('')
  const [searchImage, setSearchImage] = useState(null)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploadStatus('Uploading...')
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await axios.post(`${API_URL}/upload/`, formData)
      setUploadStatus(res.data.message)
    } catch (err) {
      setUploadStatus('Upload failed. ' + err.message)
    }
  }

  const handleTextSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery) return
    setLoading(true)

    const formData = new FormData()
    formData.append('query', searchQuery)

    try {
      const res = await axios.post(`${API_URL}/search/text/`, formData)
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

    const formData = new FormData()
    formData.append('file', searchImage)

    try {
      const res = await axios.post(`${API_URL}/search/image/`, formData)
      setResults(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Sentinal View</h1>
        <p>AI-powered forensic video analysis and frame extraction</p>
      </header>

      <div className="tabs" style={{ justifyContent: 'center' }}>
        <button
          className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          <Upload size={18} style={{ display: 'inline', marginRight: 8 }} />
          Upload Footage
        </button>
        <button
          className={`tab ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          <Search size={18} style={{ display: 'inline', marginRight: 8 }} />
          Analyze & Search
        </button>
      </div>

      {activeTab === 'upload' && (
        <div className="card glass">
          <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Video className="text-blue-500" />
            Upload CCTV Video
          </h2>
          <div className="upload-area" onClick={() => document.getElementById('video-upload').click()}>
            <Upload size={48} color="var(--primary-color)" style={{ marginBottom: '1rem' }} />
            <h3>Click or drag video to upload</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Supports MP4, AVI, MOV</p>
            <input
              type="file"
              id="video-upload"
              accept="video/*"
              style={{ display: 'none' }}
              onChange={handleFileUpload}
            />
          </div>
          {uploadStatus && (
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: 'rgba(59,130,246,0.1)', borderRadius: '8px' }}>
              {uploadStatus}
            </div>
          )}
        </div>
      )}

      {activeTab === 'search' && (
        <div>
          <div className="card glass">
            <div className="tabs">
              <button
                className={`tab ${searchMode === 'text' ? 'active' : ''}`}
                onClick={() => setSearchMode('text')}
              >
                <FileText size={18} style={{ display: 'inline', marginRight: 8 }} />
                Keyword Search
              </button>
              <button
                className={`tab ${searchMode === 'image' ? 'active' : ''}`}
                onClick={() => setSearchMode('image')}
              >
                <ImageIcon size={18} style={{ display: 'inline', marginRight: 8 }} />
                Image Search
              </button>
            </div>

            {searchMode === 'text' ? (
              <form onSubmit={handleTextSearch} style={{ display: 'flex', gap: '1rem' }}>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. 'red car', 'person in black jacket'"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleImageSearch}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <input
                    type="file"
                    className="input"
                    accept="image/*"
                    onChange={(e) => setSearchImage(e.target.files[0])}
                  />
                  <button type="submit" className="btn btn-primary" disabled={loading || !searchImage}>
                    {loading ? 'Searching...' : 'Search'}
                  </button>
                </div>
              </form>
            )}
          </div>

          <div className="grid">
            {results.map((res, idx) => (
              <div key={idx} className="result-card glass">
                <img src={`${API_URL}${res.filepath}`} alt={`Frame at ${res.timestamp}s`} className="result-image" />
                <div className="result-info">
                  <div>
                    <span className="timestamp">
                      {new Date(res.timestamp * 1000).toISOString().substr(11, 8)}
                    </span>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                      Camera/Video ID: {res.video_id}
                    </div>
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#a78bfa' }}>
                    Match: {(res.score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
            {results.length === 0 && !loading && (
              <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
                No results found. Perform a search to see extracted frames.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
