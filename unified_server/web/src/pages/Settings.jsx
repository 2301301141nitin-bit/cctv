import { useState, useEffect, useCallback } from 'react'
import {
  Settings as SettingsIcon, Camera, Cpu, Shield, Database,
  Save, Plus, Trash2, TestTube2, Check, X, Server,
  Flame, RefreshCw, Eye, EyeOff, ChevronDown, ChevronUp
} from 'lucide-react'
import axios from 'axios'

const API = ''

export default function SettingsPage() {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState(null)
  const [testResults, setTestResults] = useState({})
  const [sysInfo, setSysInfo] = useState(null)
  const [expandedSections, setExpandedSections] = useState({
    cameras: true, ai: true, firebase: false, rules: false, static: false
  })

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const fetchConfig = useCallback(async () => {
    try {
      const [cfgRes, sysRes] = await Promise.all([
        axios.get(`${API}/api/settings/`),
        axios.get(`${API}/api/system/info`)
      ])
      setConfig(cfgRes.data)
      setSysInfo(sysRes.data)
    } catch (err) {
      showToast('Failed to load configuration', 'error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchConfig() }, [fetchConfig])

  const saveConfig = async () => {
    setSaving(true)
    try {
      await axios.put(`${API}/api/settings/`, config)
      showToast('Configuration saved successfully')
    } catch {
      showToast('Failed to save configuration', 'error')
    } finally {
      setSaving(false)
    }
  }

  const testCamera = async (source, idx) => {
    setTestResults(prev => ({ ...prev, [idx]: 'testing' }))
    try {
      const res = await axios.post(`${API}/api/settings/test-camera`, { source })
      setTestResults(prev => ({ ...prev, [idx]: res.data.status }))
    } catch {
      setTestResults(prev => ({ ...prev, [idx]: 'error' }))
    }
    setTimeout(() => setTestResults(prev => ({ ...prev, [idx]: null })), 4000)
  }

  const addCamera = () => {
    const id = `cam-${Math.random().toString(36).substr(2, 6)}`
    setConfig(prev => ({
      ...prev,
      cameras: [...prev.cameras, { id, name: '', source: '', sampling_rate: 3, enabled: true }]
    }))
  }

  const removeCamera = (idx) => {
    setConfig(prev => ({
      ...prev,
      cameras: prev.cameras.filter((_, i) => i !== idx)
    }))
  }

  const updateCamera = (idx, field, value) => {
    setConfig(prev => {
      const cameras = [...prev.cameras]
      cameras[idx] = { ...cameras[idx], [field]: value }
      return { ...prev, cameras }
    })
  }

  const updateAI = (field, value) => {
    setConfig(prev => ({ ...prev, ai: { ...prev.ai, [field]: value } }))
  }

  const updateFirebase = (field, value) => {
    setConfig(prev => ({ ...prev, firebase: { ...prev.firebase, [field]: value } }))
  }

  const updateStaticAnalysis = (field, value) => {
    setConfig(prev => ({ ...prev, static_analysis: { ...prev.static_analysis, [field]: value } }))
  }

  const toggleSection = (key) => {
    setExpandedSections(prev => ({ ...prev, [key]: !prev[key] }))
  }

  if (loading || !config) {
    return (
      <>
        <div className="page-header"><h2>⚙️ Configuration</h2></div>
        <div className="page-body"><div className="empty-state"><RefreshCw size={32} className="icon" /><h3>Loading configuration...</h3></div></div>
      </>
    )
  }

  return (
    <>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h2>⚙️ Configuration</h2>
            <p>Manage cameras, AI models, detection rules, and platform settings</p>
          </div>
          <button className="btn btn-primary" onClick={saveConfig} disabled={saving}>
            <Save size={14} /> {saving ? 'Saving...' : 'Save All Changes'}
          </button>
        </div>
      </div>

      <div className="page-body">
        {/* System Info */}
        {sysInfo && (
          <div className="card-grid card-grid-4 mb-6 animate-in">
            <div className="stat-card">
              <div className="stat-label">Platform</div>
              <div className="stat-value text-sm" style={{fontSize:'0.95rem'}}>v{sysInfo.version}</div>
              <div className="stat-sub">Unified Server</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Compute Device</div>
              <div className="stat-value text-sm" style={{fontSize:'0.95rem', color: sysInfo.device === 'cuda' ? 'var(--accent-emerald)' : 'var(--accent-amber)'}}>
                {sysInfo.device === 'cuda' ? '🚀 GPU' : '⚠️ CPU'}
              </div>
              <div className="stat-sub">
                {sysInfo.gpu?.name
                  ? `${sysInfo.gpu.name} (${sysInfo.gpu.vram_gb}GB)`
                  : `${sysInfo.cpu_cores} CPU cores`
                }
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Indexed Frames</div>
              <div className="stat-value">{sysInfo.indexed_frames.toLocaleString()}</div>
              <div className="stat-sub">FAISS store (768-dim)</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">AI Stack</div>
              <div className="stat-value text-sm" style={{fontSize:'0.85rem'}}>
                {sysInfo.gpu?.cuda_version ? `CUDA ${sysInfo.gpu.cuda_version}` : 'CPU Only'}
              </div>
              <div className="stat-sub">torch {sysInfo.torch_version}</div>
            </div>
          </div>
        )}

        {/* ─── Camera Configuration ───────────────────────────────────────── */}
        <div className="settings-section animate-in">
          <div className="settings-section-header" onClick={() => toggleSection('cameras')} style={{cursor:'pointer'}}>
            <h3><Camera size={16}/> Camera Sources</h3>
            <div className="flex items-center gap-3">
              <span className="badge badge-blue">{config.cameras.length} configured</span>
              {expandedSections.cameras ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
            </div>
          </div>
          {expandedSections.cameras && (
            <div className="settings-section-body">
              {config.cameras.map((cam, idx) => (
                <div key={cam.id || idx} style={{padding:'1rem', background:'var(--bg-primary)', borderRadius:'var(--radius-md)', marginBottom:'0.75rem', border:'1px solid var(--border-subtle)'}}>
                  <div className="flex gap-3" style={{flexWrap:'wrap'}}>
                    <div className="form-group" style={{flex:'1', minWidth:'160px'}}>
                      <label className="form-label">Camera Name</label>
                      <input className="form-input" value={cam.name} placeholder="e.g. Front Gate" onChange={e => updateCamera(idx, 'name', e.target.value)} />
                    </div>
                    <div className="form-group" style={{flex:'2', minWidth:'240px'}}>
                      <label className="form-label">Source URL / Device Index</label>
                      <input className="form-input" value={cam.source} placeholder="rtsp://192.168.1.100:554/stream or 0" onChange={e => updateCamera(idx, 'source', e.target.value)} />
                    </div>
                    <div className="form-group" style={{width:'100px'}}>
                      <label className="form-label">Sampling</label>
                      <input className="form-input" type="number" min="1" max="30" value={cam.sampling_rate} onChange={e => updateCamera(idx, 'sampling_rate', parseInt(e.target.value) || 3)} />
                    </div>
                    <div className="form-group" style={{width:'80px'}}>
                      <label className="form-label">Enabled</label>
                      <label className="toggle" style={{marginTop:'0.3rem'}}>
                        <input type="checkbox" checked={cam.enabled} onChange={e => updateCamera(idx, 'enabled', e.target.checked)} />
                        <span className="toggle-slider"></span>
                      </label>
                    </div>
                    <div style={{display:'flex', gap:'0.5rem', alignItems:'flex-end', paddingBottom:'0.15rem'}}>
                      <button className="btn btn-ghost btn-sm" onClick={() => testCamera(cam.source, idx)} disabled={!cam.source}>
                        {testResults[idx] === 'testing' ? '...' :
                         testResults[idx] === 'success' ? <Check size={14} style={{color:'var(--accent-emerald)'}}/> :
                         testResults[idx] === 'error' ? <X size={14} style={{color:'var(--accent-rose)'}}/> :
                         <><TestTube2 size={14}/> Test</>}
                      </button>
                      <button className="btn btn-icon btn-ghost btn-sm" onClick={() => removeCamera(idx)}>
                        <Trash2 size={14} style={{color:'var(--accent-rose)'}} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              <button className="btn btn-ghost w-full" onClick={addCamera} style={{borderStyle:'dashed'}}>
                <Plus size={14}/> Add Camera Source
              </button>
            </div>
          )}
        </div>

        {/* ─── AI Configuration ───────────────────────────────────────────── */}
        <div className="settings-section animate-in" style={{animationDelay:'50ms'}}>
          <div className="settings-section-header" onClick={() => toggleSection('ai')} style={{cursor:'pointer'}}>
            <h3><Cpu size={16}/> AI Detection Settings</h3>
            {expandedSections.ai ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
          </div>
          {expandedSections.ai && (
            <div className="settings-section-body">
              <div className="flex gap-4" style={{flexWrap:'wrap'}}>
                <div className="form-group" style={{flex:'1', minWidth:'200px'}}>
                  <label className="form-label">Real-Time Model</label>
                  <select className="form-input" value={config.ai.realtime_model} onChange={e => updateAI('realtime_model', e.target.value)}>
                    <option value="yolov8n.pt">YOLOv8n (Fast, 6.5MB)</option>
                    <option value="yolov8s.pt">YOLOv8s (Balanced, 22MB)</option>
                    <option value="yolov8m.pt">YOLOv8m (Accurate, 52MB)</option>
                    <option value="yolov8l-worldv2.pt">YOLOv8l-World v2 (Open-Vocab, 94MB)</option>
                  </select>
                </div>
                <div className="form-group" style={{flex:'1', minWidth:'200px'}}>
                  <label className="form-label">CLIP Model (Static Analysis)</label>
                  <input className="form-input" value={config.ai.clip_model} onChange={e => updateAI('clip_model', e.target.value)} />
                </div>
              </div>
              <div className="flex gap-4 mt-4" style={{flexWrap:'wrap'}}>
                <div className="form-group" style={{flex:'2', minWidth:'200px'}}>
                  <label className="form-label">Detection Targets (comma-separated)</label>
                  <input className="form-input" value={config.ai.targets.join(', ')} onChange={e => updateAI('targets', e.target.value.split(',').map(t => t.trim()).filter(t => t))} />
                </div>
                <div className="form-group" style={{width:'180px'}}>
                  <label className="form-label">Confidence: {Math.round(config.ai.confidence * 100)}%</label>
                  <input type="range" min="5" max="95" value={Math.round(config.ai.confidence * 100)} onChange={e => updateAI('confidence', parseInt(e.target.value) / 100)} />
                </div>
                <div className="form-group" style={{width:'120px'}}>
                  <label className="form-label">Frame Sampling</label>
                  <input className="form-input" type="number" min="1" max="30" value={config.ai.frame_sampling} onChange={e => updateAI('frame_sampling', parseInt(e.target.value) || 3)} />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ─── Firebase Configuration ─────────────────────────────────────── */}
        <div className="settings-section animate-in" style={{animationDelay:'100ms'}}>
          <div className="settings-section-header" onClick={() => toggleSection('firebase')} style={{cursor:'pointer'}}>
            <h3><Flame size={16}/> Firebase Integration</h3>
            <div className="flex items-center gap-3">
              <span className={`badge ${config.firebase.enabled ? 'badge-green' : 'badge-amber'}`}>
                {config.firebase.enabled ? 'Enabled' : 'Disabled'}
              </span>
              {expandedSections.firebase ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
            </div>
          </div>
          {expandedSections.firebase && (
            <div className="settings-section-body">
              <div className="settings-row">
                <div className="setting-info">
                  <div className="setting-label">Enable Firebase Sync</div>
                  <div className="setting-desc">Sync events and snapshots to Firebase Firestore & Storage</div>
                </div>
                <div className="setting-control">
                  <label className="toggle">
                    <input type="checkbox" checked={config.firebase.enabled} onChange={e => updateFirebase('enabled', e.target.checked)} />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>
              {config.firebase.enabled && (
                <div className="flex flex-col gap-4 mt-4">
                  <div className="flex gap-4" style={{flexWrap:'wrap'}}>
                    <div className="form-group" style={{flex:1, minWidth:'200px'}}>
                      <label className="form-label">Credentials Path</label>
                      <input className="form-input" value={config.firebase.credentials_path} onChange={e => updateFirebase('credentials_path', e.target.value)} />
                    </div>
                    <div className="form-group" style={{flex:1, minWidth:'200px'}}>
                      <label className="form-label">Storage Bucket</label>
                      <input className="form-input" placeholder="your-project.appspot.com" value={config.firebase.storage_bucket} onChange={e => updateFirebase('storage_bucket', e.target.value)} />
                    </div>
                  </div>
                  <div className="flex gap-4" style={{flexWrap:'wrap'}}>
                    <div className="form-group" style={{flex:1}}>
                      <label className="form-label">API Key</label>
                      <input className="form-input" value={config.firebase.api_key} onChange={e => updateFirebase('api_key', e.target.value)} />
                    </div>
                    <div className="form-group" style={{flex:1}}>
                      <label className="form-label">Project ID</label>
                      <input className="form-input" value={config.firebase.project_id} onChange={e => updateFirebase('project_id', e.target.value)} />
                    </div>
                    <div className="form-group" style={{flex:1}}>
                      <label className="form-label">Auth Domain</label>
                      <input className="form-input" value={config.firebase.auth_domain} onChange={e => updateFirebase('auth_domain', e.target.value)} />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ─── Static Analysis Configuration ─────────────────────────────── */}
        <div className="settings-section animate-in" style={{animationDelay:'150ms'}}>
          <div className="settings-section-header" onClick={() => toggleSection('static')} style={{cursor:'pointer'}}>
            <h3><Database size={16}/> Static Analysis Settings</h3>
            {expandedSections.static ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
          </div>
          {expandedSections.static && (
            <div className="settings-section-body">
              <div className="flex gap-4">
                <div className="form-group" style={{width:'200px'}}>
                  <label className="form-label">Frame Extraction Rate (FPS)</label>
                  <select className="form-input" value={config.static_analysis.fps_extract} onChange={e => updateStaticAnalysis('fps_extract', parseFloat(e.target.value))}>
                    <option value="1.0">1.0 FPS (High Detail)</option>
                    <option value="0.5">0.5 FPS (Standard)</option>
                    <option value="0.2">0.2 FPS (Fast)</option>
                    <option value="0.1">0.1 FPS (Ultra Fast)</option>
                  </select>
                </div>
                <div className="form-group" style={{width:'160px'}}>
                  <label className="form-label">Batch Size</label>
                  <input className="form-input" type="number" min="1" max="128" value={config.static_analysis.batch_size} onChange={e => updateStaticAnalysis('batch_size', parseInt(e.target.value) || 32)} />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Bottom spacer */}
        <div style={{height:'2rem'}}></div>
      </div>

      {/* Toast */}
      {toast && (
        <div className={`toast ${toast.type === 'success' ? 'toast-success' : 'toast-error'}`}>
          {toast.type === 'success' ? <Check size={16} style={{color:'var(--accent-emerald)'}}/> : <X size={16} style={{color:'var(--accent-rose)'}}/>}
          {toast.msg}
        </div>
      )}
    </>
  )
}
