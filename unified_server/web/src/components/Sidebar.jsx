import { NavLink } from 'react-router-dom'
import {
  Video, Search, Activity, Settings, Shield,
  MonitorPlay, BarChart3, Cpu
} from 'lucide-react'
import { useState, useEffect } from 'react'

const API = ''

export default function Sidebar() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    fetch(`${API}/api/system/health`)
      .then(r => r.json())
      .then(setHealth)
      .catch(() => { })
  }, [])

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>⚡ Sentinal View </h1>
        <div className="brand-sub">Intelligence Platform v2.0</div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Forensic Analysis</div>
        <NavLink to="/app" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Search className="nav-icon" size={18} />
          Static Analysis
        </NavLink>

        <div className="sidebar-section-label">Live Monitoring</div>
        <NavLink to="/app/realtime" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <MonitorPlay className="nav-icon" size={18} />
          Real-Time Feed
        </NavLink>
        <NavLink to="/app/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <BarChart3 className="nav-icon" size={18} />
          SOC Dashboard
        </NavLink>

        <div className="sidebar-section-label">Administration</div>
        <NavLink to="/app/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Settings className="nav-icon" size={18} />
          Configuration
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className="status-dot"></span>
          <span>
            {health ? `Online · ${health.device.toUpperCase()}` : 'Connecting...'}
          </span>
        </div>
      </div>
    </aside>
  )
}
