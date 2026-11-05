import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import AlertPopup from './components/AlertPopup'
import StaticAnalysis from './pages/StaticAnalysis'
import RealtimeMonitor from './pages/RealtimeMonitor'
import Dashboard from './pages/Dashboard'
import SettingsPage from './pages/Settings'
import './index.css'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/app" element={<StaticAnalysis />} />
            <Route path="/app/realtime" element={<RealtimeMonitor />} />
            <Route path="/app/dashboard" element={<Dashboard />} />
            <Route path="/app/settings" element={<SettingsPage />} />
            {/* Fallback for dev mode */}
            <Route path="/" element={<StaticAnalysis />} />
          </Routes>
        </main>
        {/* Global alert popup — active on all pages */}
        <AlertPopup />
      </div>
    </BrowserRouter>
  )
}

