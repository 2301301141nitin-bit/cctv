import { useState, useEffect, useCallback } from 'react'
import { 
  ShieldAlert, Clock, AlertTriangle, Filter,
  AlertOctagon, ShieldCheck, XCircle, Video,
  Activity, ChevronRight
} from 'lucide-react'
import axios from 'axios'

const API = ''

const severityColors = {
  low: 'badge-green',
  medium: 'badge-amber',
  high: 'badge-red',
  critical: 'badge-red',
}

function timeAgo(ts) {
  const seconds = Math.floor(Date.now() / 1000 - ts)
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds/60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds/3600)}h ago`
  return `${Math.floor(seconds/86400)}d ago`
}

export default function Dashboard() {
  const [events, setEvents] = useState([])
  const [cameras, setCameras] = useState([])
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [severityFilter, setSeverityFilter] = useState('all')
  const [cameraFilter, setCameraFilter] = useState('all')

  const fetchData = useCallback(async () => {
    try {
      const [evRes, camRes] = await Promise.all([
        axios.get(`${API}/api/realtime/events`),
        axios.get(`${API}/api/realtime/cameras`)
      ])
      // Flatten all detections into event-like entries
      const allEvents = []
      for (const ev of evRes.data) {
        if (ev.detections && ev.detections.length > 0) {
          // Group as a single event per camera per poll
          allEvents.push({
            id: `${ev.camera_id}-${ev.frame_index}`,
            camera_id: ev.camera_id,
            camera_name: ev.camera_name || ev.camera_id,
            timestamp: ev.timestamp,
            event_type: `${ev.detections.length} Object(s) Detected`,
            severity: ev.detections.length >= 5 ? 'high' : ev.detections.length >= 3 ? 'medium' : 'low',
            detections: ev.detections,
            entity_ids: ev.detections.filter(d => d.track_id != null).map(d => d.track_id)
          })
        }
      }
      setEvents(allEvents)
      setCameras(camRes.data)
    } catch {}
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [fetchData])

  const filteredEvents = events.filter(e => {
    if (severityFilter !== 'all' && e.severity !== severityFilter) return false
    if (cameraFilter !== 'all' && e.camera_id !== cameraFilter) return false
    return true
  })

  return (
    <>
      <div className="page-header">
        <h2>🛡️ SOC Dashboard</h2>
        <p>Security Operations Center — Real-time event monitoring and threat intelligence</p>
      </div>

      <div style={{display:'flex', flex:1, overflow:'hidden'}}>
        {/* Event Feed */}
        <div style={{width:'320px', minWidth:'320px', borderRight:'1px solid var(--border-subtle)', display:'flex', flexDirection:'column', background:'var(--bg-secondary)'}}>
          {/* Filters */}
          <div style={{padding:'0.75rem', borderBottom:'1px solid var(--border-subtle)'}}>
            <div className="flex items-center gap-2 mb-2">
              <Filter size={14} style={{color:'var(--text-muted)'}} />
              <span style={{fontSize:'0.7rem', textTransform:'uppercase', letterSpacing:'0.08em', color:'var(--text-muted)', fontWeight:600}}>Filters</span>
            </div>
            <div className="flex gap-2">
              <select className="form-input" style={{fontSize:'0.75rem', padding:'0.35rem 0.5rem'}} value={cameraFilter} onChange={e => setCameraFilter(e.target.value)}>
                <option value="all">All Cameras</option>
                {cameras.map(c => <option key={c.id} value={c.id}>{c.name || c.id}</option>)}
              </select>
              <select className="form-input" style={{fontSize:'0.75rem', padding:'0.35rem 0.5rem'}} value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}>
                <option value="all">All Severity</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          {/* Event List */}
          <div style={{flex:1, overflowY:'auto'}}>
            <div style={{padding:'0.5rem 0.75rem', borderBottom:'1px solid var(--border-subtle)'}}>
              <span style={{fontSize:'0.7rem', textTransform:'uppercase', letterSpacing:'0.08em', color:'var(--text-muted)', fontWeight:600}}>
                <ShieldAlert size={12} style={{verticalAlign:'middle', marginRight:4}} /> 
                Events ({filteredEvents.length})
              </span>
            </div>
            {filteredEvents.length === 0 ? (
              <div style={{padding:'2rem 1rem', textAlign:'center', color:'var(--text-muted)', fontSize:'0.85rem'}}>
                No events detected. Waiting for alerts...
              </div>
            ) : (
              filteredEvents.map(event => (
                <div
                  key={event.id}
                  className={`event-item ${selectedEvent?.id === event.id ? 'selected' : ''}`}
                  onClick={() => setSelectedEvent(event)}
                >
                  <div className="event-header">
                    <span className={`badge ${severityColors[event.severity] || 'badge-blue'}`}>
                      {event.severity}
                    </span>
                    <span className="event-time">
                      <Clock size={10} style={{marginRight:3, verticalAlign:'middle'}} />
                      {timeAgo(event.timestamp)}
                    </span>
                  </div>
                  <div className="event-type">{event.event_type}</div>
                  <div className="event-camera">{event.camera_name}</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Event Detail */}
        <div style={{flex:1, overflowY:'auto', padding:'1.5rem 2rem'}}>
          {!selectedEvent ? (
            <div className="empty-state" style={{height:'100%'}}>
              <AlertOctagon size={48} className="icon" />
              <h3>Select an event</h3>
              <p>Click on an event from the feed to view detection details and evidence</p>
            </div>
          ) : (
            <div className="animate-in">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 style={{fontSize:'1.4rem', fontWeight:700}}>{selectedEvent.event_type}</h2>
                  <div className="flex items-center gap-3 mt-2 text-sm text-muted">
                    <span>Camera: {selectedEvent.camera_name}</span>
                    <span>•</span>
                    <span>{new Date(selectedEvent.timestamp * 1000).toLocaleTimeString()}</span>
                  </div>
                </div>
                <span className={`badge ${severityColors[selectedEvent.severity] || 'badge-blue'}`} style={{fontSize:'0.8rem', padding:'0.3rem 0.8rem'}}>
                  {selectedEvent.severity.toUpperCase()}
                </span>
              </div>

              {/* Detections Table */}
              <div className="card mb-6">
                <div className="card-header">
                  <div className="card-title"><Activity size={16}/> Detections</div>
                  <span className="badge badge-blue">{selectedEvent.detections?.length || 0} objects</span>
                </div>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Track ID</th>
                      <th>Class</th>
                      <th>Confidence</th>
                      <th>Bounding Box</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(selectedEvent.detections || []).map((d, i) => (
                      <tr key={i}>
                        <td><span className="font-mono">{d.track_id != null ? `#${d.track_id}` : '—'}</span></td>
                        <td><span className="badge badge-purple">{d.class_name}</span></td>
                        <td>{(d.confidence * 100).toFixed(1)}%</td>
                        <td className="font-mono text-xs text-muted">
                          {d.bbox ? `(${Math.round(d.bbox.x1)}, ${Math.round(d.bbox.y1)}) → (${Math.round(d.bbox.x2)}, ${Math.round(d.bbox.y2)})` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Entity IDs */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">Tracked Entities</div>
                </div>
                <div className="flex gap-2" style={{flexWrap:'wrap'}}>
                  {selectedEvent.entity_ids?.length > 0 ? (
                    selectedEvent.entity_ids.map(id => (
                      <span key={id} className="badge badge-blue" style={{fontSize:'0.8rem', padding:'0.3rem 0.6rem'}}>
                        ID: {id}
                      </span>
                    ))
                  ) : (
                    <span className="text-muted text-sm">No tracked entities</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
