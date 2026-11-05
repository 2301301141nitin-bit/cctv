import { useState, useEffect, useCallback, useRef } from 'react'
import { AlertTriangle, X, Volume2, VolumeX, Bell } from 'lucide-react'

/**
 * AlertPopup — Real-time threshold-based alert notification system.
 * Connects via WebSocket and shows popup toasts when detections exceed thresholds.
 */

const ALERT_SOUND_FREQUENCY = 800
const ALERT_SOUND_DURATION = 200

function playAlertSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.frequency.value = ALERT_SOUND_FREQUENCY
    osc.type = 'sine'
    gain.gain.setValueAtTime(0.3, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + ALERT_SOUND_DURATION / 1000)
    osc.start(ctx.currentTime)
    osc.stop(ctx.currentTime + ALERT_SOUND_DURATION / 1000)
    setTimeout(() => {
      // Second beep
      const osc2 = ctx.createOscillator()
      const gain2 = ctx.createGain()
      osc2.connect(gain2)
      gain2.connect(ctx.destination)
      osc2.frequency.value = ALERT_SOUND_FREQUENCY * 1.2
      osc2.type = 'sine'
      gain2.gain.setValueAtTime(0.3, ctx.currentTime)
      gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + ALERT_SOUND_DURATION / 1000)
      osc2.start(ctx.currentTime)
      osc2.stop(ctx.currentTime + ALERT_SOUND_DURATION / 1000)
    }, ALERT_SOUND_DURATION + 50)
  } catch (e) {
    console.log('Audio not available:', e)
  }
}

function severityForClass(className) {
  const high = ['weapon', 'knife', 'gun', 'fire', 'Group of People']
  const medium = ['person', 'Solo Person']
  if (high.some(h => className.toLowerCase().includes(h.toLowerCase()))) return 'high'
  if (medium.some(m => className.toLowerCase().includes(m.toLowerCase()))) return 'medium'
  return 'low'
}

function AlertToast({ alert, onDismiss }) {
  const [exiting, setExiting] = useState(false)
  const timerRef = useRef(null)

  useEffect(() => {
    timerRef.current = setTimeout(() => {
      setExiting(true)
      setTimeout(onDismiss, 300)
    }, 8000) // Auto-dismiss after 8s
    return () => clearTimeout(timerRef.current)
  }, [onDismiss])

  const handleDismiss = () => {
    clearTimeout(timerRef.current)
    setExiting(true)
    setTimeout(onDismiss, 300)
  }

  const severity = alert.detections?.[0]
    ? severityForClass(alert.detections[0].class_name)
    : 'medium'

  const borderColor = severity === 'high' ? 'var(--accent-rose)' :
                       severity === 'medium' ? 'var(--accent-amber)' :
                       'var(--accent-emerald)'

  const ts = new Date(alert.timestamp * 1000)
  const timeStr = ts.toLocaleTimeString()

  return (
    <div
      className={`alert-toast ${exiting ? 'alert-toast-exit' : 'alert-toast-enter'}`}
      style={{ borderLeft: `4px solid ${borderColor}` }}
    >
      <div className="alert-toast-header">
        <div className="flex items-center gap-2">
          <AlertTriangle size={16} style={{ color: borderColor }} />
          <span className="alert-toast-title">
            {severity === 'high' ? '🚨' : '⚠️'} Threshold Match
          </span>
        </div>
        <button className="alert-toast-close" onClick={handleDismiss}>
          <X size={14} />
        </button>
      </div>

      <div className="alert-toast-body">
        <div className="alert-toast-camera">
          📷 {alert.camera_name || alert.camera_id}
          <span className="alert-toast-time">{timeStr}</span>
        </div>

        <div className="alert-toast-detections">
          {alert.detections?.map((d, i) => (
            <div key={i} className="alert-toast-detection">
              <span className={`badge ${severity === 'high' ? 'badge-red' : severity === 'medium' ? 'badge-amber' : 'badge-green'}`}>
                {d.class_name}
              </span>
              <span className="alert-toast-conf">
                {(d.confidence * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>

        {alert.snapshot && (
          <div className="alert-toast-snapshot">
            <img
              src={`data:image/jpeg;base64,${alert.snapshot}`}
              alt="Alert snapshot"
              style={{ width: '100%', borderRadius: '6px', marginTop: '0.5rem' }}
            />
          </div>
        )}
      </div>
    </div>
  )
}


export default function AlertPopup() {
  const [alerts, setAlerts] = useState([])
  const [connected, setConnected] = useState(false)
  const [soundEnabled, setSoundEnabled] = useState(true)
  const wsRef = useRef(null)
  const reconnectTimerRef = useRef(null)
  const alertIdCounter = useRef(0)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/realtime/ws/alerts`

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        setConnected(true)
        console.log('🔔 Alert WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'threshold_alert') {
            const alertWithId = { ...data, _id: ++alertIdCounter.current }
            setAlerts(prev => [alertWithId, ...prev].slice(0, 10)) // Keep max 10

            if (soundEnabled) {
              playAlertSound()
            }
          }
        } catch (e) {
          console.error('Failed to parse alert:', e)
        }
      }

      ws.onclose = () => {
        setConnected(false)
        // Auto-reconnect after 3 seconds
        reconnectTimerRef.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        ws.close()
      }

      wsRef.current = ws
    } catch (e) {
      console.error('WebSocket connection failed:', e)
      reconnectTimerRef.current = setTimeout(connect, 3000)
    }
  }, [soundEnabled])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimerRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  // Send periodic pings to keep connection alive
  useEffect(() => {
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
    return () => clearInterval(pingInterval)
  }, [])

  const dismissAlert = (id) => {
    setAlerts(prev => prev.filter(a => a._id !== id))
  }

  return (
    <>
      {/* Connection indicator */}
      <div className="alert-ws-indicator">
        <div className={`alert-ws-dot ${connected ? 'connected' : 'disconnected'}`} />
        <Bell size={12} />
        <button
          className="alert-sound-toggle"
          onClick={() => setSoundEnabled(!soundEnabled)}
          title={soundEnabled ? 'Mute alerts' : 'Unmute alerts'}
        >
          {soundEnabled ? <Volume2 size={12} /> : <VolumeX size={12} />}
        </button>
      </div>

      {/* Alert toasts container */}
      <div className="alert-toast-container">
        {alerts.map(alert => (
          <AlertToast
            key={alert._id}
            alert={alert}
            onDismiss={() => dismissAlert(alert._id)}
          />
        ))}
      </div>
    </>
  )
}
