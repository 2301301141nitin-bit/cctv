import { useState, useEffect, useCallback, useRef } from 'react'
import { 
  MonitorPlay, Plus, Trash2, RefreshCw, Wifi, WifiOff,
  Target, SlidersHorizontal, Check, AlertTriangle, Video,
  Bell, BellOff, Settings
} from 'lucide-react'
import axios from 'axios'

const API = ''

export default function RealtimeMonitor() {
  const [cameras, setCameras] = useState([])
  const [events, setEvents] = useState([])
  const [aiConfig, setAiConfig] = useState({ targets: ['person','car'], confidence: 0.25 })
  const [showAddModal, setShowAddModal] = useState(false)
  const [newCam, setNewCam] = useState({ name: '', source: '', sampling_rate: 3 })
  const [targetsInput, setTargetsInput] = useState('person, car')
  const [confValue, setConfValue] = useState(25)
  const [configStatus, setConfigStatus] = useState('idle')

  // Alert threshold state
  const [alertConfig, setAlertConfig] = useState({
    enabled: true, thresholds: { person: 0.6, car: 0.5 }, cooldown_seconds: 10
  })
  const [showAlertConfig, setShowAlertConfig] = useState(false)
  const [newThresholdClass, setNewThresholdClass] = useState('')
  const [newThresholdValue, setNewThresholdValue] = useState(50)

  const fetchCameras = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/api/realtime/cameras`)
      setCameras(res.data)
    } catch {}
  }, [])

  const fetchEvents = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/api/realtime/events`)
      setEvents(res.data)
    } catch {}
  }, [])

  const fetchAiConfig = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/api/realtime/ai/config`)
      setAiConfig(res.data)
      setTargetsInput(res.data.targets.join(', '))
      setConfValue(Math.round(res.data.confidence * 100))
    } catch {}
  }, [])

  const fetchAlertConfig = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/api/realtime/alerts/config`)
      setAlertConfig(res.data)
    } catch {}
  }, [])

  useEffect(() => {
    fetchCameras()
    fetchAiConfig()
    fetchAlertConfig()
    const interval = setInterval(() => {
      fetchCameras()
      fetchEvents()
    }, 2000)
    return () => clearInterval(interval)
  }, [fetchCameras, fetchEvents, fetchAiConfig, fetchAlertConfig])

  const addCamera = async () => {
    if (!newCam.source) return
    try {
      await axios.post(`${API}/api/realtime/cameras`, newCam)
      setShowAddModal(false)
      setNewCam({ name: '', source: '', sampling_rate: 3 })
      fetchCameras()
    } catch (err) {
      alert('Failed to add camera: ' + (err.response?.data?.detail || err.message))
    }
  }

  const removeCamera = async (id) => {
    try {
      await axios.delete(`${API}/api/realtime/cameras/${id}`)
      fetchCameras()
    } catch {}
  }

  const updateAiConfig = async () => {
    setConfigStatus('updating')
    const classList = targetsInput.split(',').map(t => t.trim()).filter(t => t)
    try {
      await axios.post(`${API}/api/realtime/ai/config`, {
        targets: classList.length ? classList : ['person', 'car'],
        confidence: confValue / 100
      })
      setConfigStatus('success')
      setTimeout(() => setConfigStatus('idle'), 2000)
    } catch {
      setConfigStatus('error')
      setTimeout(() => setConfigStatus('idle'), 3000)
    }
  }

  const saveAlertConfig = async () => {
    try {
      await axios.post(`${API}/api/realtime/alerts/config`, alertConfig)
      setShowAlertConfig(false)
    } catch (err) {
      alert('Failed to save alert config: ' + err.message)
    }
  }

  const addThreshold = () => {
    if (!newThresholdClass.trim()) return
    setAlertConfig(prev => ({
      ...prev,
      thresholds: { ...prev.thresholds, [newThresholdClass.trim().toLowerCase()]: newThresholdValue / 100 }
    }))
    setNewThresholdClass('')
    setNewThresholdValue(50)
  }

  const removeThreshold = (className) => {
    setAlertConfig(prev => {
      const t = { ...prev.thresholds }
      delete t[className]
      return { ...prev, thresholds: t }
    })
  }

  return (
    <>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h2>📡 Real-Time Monitoring</h2>
            <p>Live AI-powered camera feeds with object detection and tracking</p>
          </div>
          <div className="flex gap-3">
            <button className="btn btn-ghost btn-sm" onClick={() => setShowAlertConfig(true)}>
              <Bell size={14} /> Alert Thresholds
            </button>
            <button className="btn btn-ghost btn-sm" onClick={fetchCameras}>
              <RefreshCw size={14} /> Refresh
            </button>
            <button className="btn btn-primary btn-sm" onClick={() => setShowAddModal(true)}>
              <Plus size={14} /> Add Camera
            </button>
          </div>
        </div>
      </div>

      <div className="page-body">
        {/* AI Control Bar */}
        <div className="card mb-6 animate-in">
          <div className="card-header">
            <div className="card-title"><Target size={16} /> Global AI Detection Control</div>
          </div>
          <div className="flex gap-4 items-center" style={{flexWrap:'wrap'}}>
            <div className="form-group" style={{flex:'1', minWidth:'200px'}}>
              <label className="form-label">Detection Targets</label>
              <input
                className="form-input"
                value={targetsInput}
                onChange={(e) => setTargetsInput(e.target.value)}
                placeholder="e.g. red shirt, backpack, black car"
              />
            </div>
            <div className="form-group" style={{width:'200px'}}>
              <label className="form-label">Confidence: {confValue}%</label>
              <input
                type="range" min="5" max="95" value={confValue}
                onChange={(e) => setConfValue(parseInt(e.target.value))}
              />
            </div>
            <div style={{paddingTop:'1.2rem'}}>
              <button
                className={`btn btn-sm ${configStatus === 'success' ? 'btn-success' : configStatus === 'error' ? 'btn-danger' : 'btn-primary'}`}
                onClick={updateAiConfig}
                disabled={configStatus === 'updating'}
              >
                {configStatus === 'updating' ? 'Updating...' : 
                 configStatus === 'success' ? <><Check size={14}/> Updated</> :
                 configStatus === 'error' ? 'Failed' : 'Apply Config'}
              </button>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="card-grid card-grid-4 mb-6">
          <div className="stat-card animate-in">
            <div className="stat-label">Active Cameras</div>
            <div className="stat-value" style={{color:'var(--accent-emerald)'}}>{cameras.filter(c => c.status === 'running').length}</div>
          </div>
          <div className="stat-card animate-in" style={{animationDelay:'50ms'}}>
            <div className="stat-label">Total Cameras</div>
            <div className="stat-value">{cameras.length}</div>
          </div>
          <div className="stat-card animate-in" style={{animationDelay:'100ms'}}>
            <div className="stat-label">Active Detections</div>
            <div className="stat-value" style={{color:'var(--accent-amber)'}}>{events.reduce((sum, e) => sum + (e.detections?.length || 0), 0)}</div>
          </div>
          <div className="stat-card animate-in" style={{animationDelay:'150ms'}}>
            <div className="stat-label">Alert Thresholds</div>
            <div className="stat-value text-sm" style={{fontSize:'1rem'}}>
              {alertConfig.enabled ? `🔔 ${Object.keys(alertConfig.thresholds || {}).length} rules` : '🔕 Disabled'}
            </div>
          </div>
        </div>

        {/* Camera Grid */}
        {cameras.length === 0 ? (
          <div className="empty-state animate-in">
            <Video size={48} className="icon" />
            <h3>No cameras connected</h3>
            <p>Add a camera source (RTSP, HTTP, or device index) to start real-time monitoring</p>
            <button className="btn btn-primary mt-4" onClick={() => setShowAddModal(true)}>
              <Plus size={16} /> Add First Camera
            </button>
          </div>
        ) : (
          <div className="camera-grid">
            {cameras.map((cam) => {
              const camEvents = events.find(e => e.camera_id === cam.id)
              return (
                <div key={cam.id} className="camera-card animate-in" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                  <div style={{ display: 'flex', flex: 1, minHeight: '300px' }}>
                    <div className="camera-preview" style={{ flex: 2, position: 'relative', background: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {cam.status === 'running' ? (
                        <img src={`${API}/api/realtime/cameras/${cam.id}/stream`} style={{ width: '100%', height: '100%', objectFit: 'contain' }} alt="Live Feed" />
                      ) : (
                        <div style={{textAlign:'center'}}>
                          <MonitorPlay size={32} style={{opacity:0.2, marginBottom:'0.5rem'}} />
                          <div style={{fontSize:'0.8rem'}}>Camera stopped</div>
                        </div>
                      )}
                      <div style={{position:'absolute', top:'0.5rem', right:'0.5rem'}}>
                        {cam.status === 'running' ? (
                          <span className="badge badge-green"><Wifi size={10}/> Live</span>
                        ) : (
                          <span className="badge badge-red"><WifiOff size={10}/> Offline</span>
                        )}
                      </div>
                    </div>
                    <div style={{ flex: 1, padding: '1rem', borderLeft: '1px solid var(--border-color)', background: 'var(--bg-secondary)', overflowY: 'auto' }}>
                      {camEvents && camEvents.detections?.length > 0 ? (
                        <>
                          <div className="flex items-center gap-2 mb-3">
                            <AlertTriangle size={14} style={{color:'var(--accent-amber)'}} />
                            <span style={{fontSize:'0.85rem', color:'var(--accent-amber)', fontWeight:600}}>
                              {camEvents.detections.length} Alert(s)
                            </span>
                          </div>
                          <div className="flex flex-col gap-2">
                            {camEvents.detections.map((d, i) => (
                              <div key={i} style={{fontSize:'0.8rem', color:'var(--text-secondary)', padding:'0.4rem', border: '1px solid var(--border-color)', borderRadius: '6px', background: 'var(--bg-primary)'}}>
                                <span className={`badge ${d.class_name.includes('Group') || d.class_name.includes('Gun') || d.class_name.includes('Mask') ? 'badge-red' : 'badge-blue'}`} style={{marginRight:'0.4rem', fontWeight: 600}}>{d.class_name}</span>
                                {d.track_id != null && <span className="text-muted" style={{fontSize: '0.7rem'}}>ID #{d.track_id}</span>}
                                <span className="text-muted" style={{float:'right'}}>{(d.confidence * 100).toFixed(0)}%</span>
                              </div>
                            ))}
                          </div>
                        </>
                      ) : (
                        <div style={{fontSize:'0.8rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '2rem'}}>
                          No active alerts
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="camera-info" style={{ borderTop: '1px solid var(--border-color)' }}>
                    <div>
                      <div className="camera-name">{cam.name || cam.id}</div>
                      <div className="camera-source truncate" style={{maxWidth:'200px'}}>{cam.source}</div>
                    </div>
                    <button className="btn btn-icon btn-ghost" onClick={() => removeCamera(cam.id)} title="Remove camera">
                      <Trash2 size={14} style={{color:'var(--accent-rose)'}} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Add Camera Modal */}
        {showAddModal && (
          <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.7)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:100}} onClick={() => setShowAddModal(false)}>
            <div className="card" style={{width:'480px', maxWidth:'90vw'}} onClick={e => e.stopPropagation()}>
              <div className="card-header">
                <div className="card-title"><Plus size={18}/> Add Camera Source</div>
              </div>
              <div className="flex flex-col gap-4">
                <div className="form-group">
                  <label className="form-label">Camera Name</label>
                  <input className="form-input" placeholder="e.g. Front Gate, Lobby" value={newCam.name} onChange={e => setNewCam({...newCam, name: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Source URL / Device Index</label>
                  <input className="form-input" placeholder="rtsp://192.168.1.100:554/stream or 0" value={newCam.source} onChange={e => setNewCam({...newCam, source: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Frame Sampling Rate (process 1 in N frames)</label>
                  <input className="form-input" type="number" min="1" max="30" value={newCam.sampling_rate} onChange={e => setNewCam({...newCam, sampling_rate: parseInt(e.target.value) || 3})} />
                </div>
                <div className="flex gap-3 justify-between">
                  <button className="btn btn-ghost" onClick={() => setShowAddModal(false)}>Cancel</button>
                  <button className="btn btn-primary" onClick={addCamera}>Add & Start Camera</button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Alert Threshold Configuration Modal */}
        {showAlertConfig && (
          <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.7)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:100}} onClick={() => setShowAlertConfig(false)}>
            <div className="card" style={{width:'560px', maxWidth:'90vw'}} onClick={e => e.stopPropagation()}>
              <div className="card-header">
                <div className="card-title"><Bell size={18}/> Alert Threshold Configuration</div>
              </div>
              <p style={{fontSize:'0.85rem', color:'var(--text-muted)', marginBottom:'1rem'}}>
                Alerts will <strong>only fire</strong> when a detection's confidence exceeds its threshold. No continuous alerts — just precise matches.
              </p>

              {/* Enable/Disable Toggle */}
              <div className="flex items-center gap-3 mb-4">
                <label className="form-label" style={{margin:0}}>Alerts Enabled</label>
                <button
                  className={`btn btn-sm ${alertConfig.enabled ? 'btn-success' : 'btn-ghost'}`}
                  onClick={() => setAlertConfig(prev => ({...prev, enabled: !prev.enabled}))}
                >
                  {alertConfig.enabled ? <><Bell size={14}/> ON</> : <><BellOff size={14}/> OFF</>}
                </button>
              </div>

              {/* Cooldown */}
              <div className="form-group mb-4">
                <label className="form-label">Cooldown (seconds between alerts for same class)</label>
                <input
                  className="form-input"
                  type="number" min="1" max="300"
                  value={alertConfig.cooldown_seconds}
                  onChange={e => setAlertConfig(prev => ({...prev, cooldown_seconds: parseInt(e.target.value) || 10}))}
                  style={{width:'120px'}}
                />
              </div>

              {/* Threshold List */}
              <div className="form-group mb-4">
                <label className="form-label">Per-Class Thresholds</label>
                <div className="flex flex-col gap-2">
                  {Object.entries(alertConfig.thresholds || {}).map(([cls, val]) => (
                    <div key={cls} className="flex items-center gap-3" style={{padding:'0.5rem', background:'var(--bg-secondary)', borderRadius:'8px'}}>
                      <span className="badge badge-purple" style={{minWidth:'80px', textAlign:'center'}}>{cls}</span>
                      <input
                        type="range" min="5" max="95"
                        value={Math.round(val * 100)}
                        onChange={e => setAlertConfig(prev => ({
                          ...prev,
                          thresholds: {...prev.thresholds, [cls]: parseInt(e.target.value) / 100}
                        }))}
                        style={{flex:1}}
                      />
                      <span style={{fontSize:'0.8rem', fontWeight:600, minWidth:'40px', textAlign:'right'}}>
                        {Math.round(val * 100)}%
                      </span>
                      <button className="btn btn-icon btn-ghost" onClick={() => removeThreshold(cls)} title="Remove">
                        <Trash2 size={12} style={{color:'var(--accent-rose)'}} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Add New Threshold */}
              <div className="flex gap-2 items-end mb-4">
                <div className="form-group" style={{flex:1}}>
                  <label className="form-label">Add Class</label>
                  <input
                    className="form-input"
                    placeholder="e.g. weapon, backpack, dog"
                    value={newThresholdClass}
                    onChange={e => setNewThresholdClass(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && addThreshold()}
                  />
                </div>
                <div className="form-group" style={{width:'100px'}}>
                  <label className="form-label">{newThresholdValue}%</label>
                  <input type="range" min="5" max="95" value={newThresholdValue} onChange={e => setNewThresholdValue(parseInt(e.target.value))} />
                </div>
                <button className="btn btn-ghost btn-sm" onClick={addThreshold} style={{marginBottom:'0.25rem'}}>
                  <Plus size={14} /> Add
                </button>
              </div>

              <div className="flex gap-3 justify-between">
                <button className="btn btn-ghost" onClick={() => setShowAlertConfig(false)}>Cancel</button>
                <button className="btn btn-primary" onClick={saveAlertConfig}>
                  <Check size={14} /> Save & Apply
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
