import React, { useState, useEffect } from 'react'
import { Shield, Key, AlertTriangle, CheckCircle, RefreshCw, Zap, Sliders, Users, MessageSquare } from 'lucide-react'
import { adminLogin, adminOverride, getCampusConfig, updateCampusConfig, getSchedule, getVehicles } from '../services/api.js'

export default function AdminPanel() {
  const [token, setToken] = useState(localStorage.getItem('admin_token') || '')
  const [adminId, setAdminId] = useState('admin')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginSuccess, setLoginSuccess] = useState('')

  const [config, setConfig] = useState(null)
  const [vehicles, setVehicles] = useState([])
  const [sessions, setSessions] = useState([])

  // Override Form
  const [overrideForm, setOverrideForm] = useState({
    vehicle_id: '',
    request_id: '',
    reason: '',
    new_priority_score: 0.95,
    new_charger_id: '',
  })
  const [overrideSuccess, setOverrideSuccess] = useState(null)
  const [overrideError, setOverrideError] = useState(null)
  const [loading, setLoading] = useState(false)

  // Stakeholder Feedback Form
  const [feedback, setFeedback] = useState([
    { id: 1, name: 'Campus Facilities Director', role: 'Facilities', comment: 'The explanation strings give clear rationale when overriding emergency vehicles.', rating: 5 },
    { id: 2, name: 'EV Fleet Coordinator', role: 'Fleet Lead', comment: 'ToU grid tariff visualizer helps plan overnight charging cost savings.', rating: 5 },
    { id: 3, name: 'Sustainability Officer', role: 'ESG', comment: 'Battery 20% reserve protection avoids deep discharge degradation.', rating: 4 },
  ])
  const [newComment, setNewComment] = useState('')
  const [newRole, setNewRole] = useState('Facility Manager')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [cfgRes, vehRes, sesRes] = await Promise.all([
        getCampusConfig(),
        getVehicles(),
        getSchedule(),
      ])
      setConfig(cfgRes.data)
      setVehicles(vehRes.data)
      setSessions(sesRes.data)
    } catch (e) {
      console.error(e)
    }
  }

  const handleLogin = async () => {
    setLoginError('')
    setLoginSuccess('')
    try {
      const res = await adminLogin(adminId, password)
      const jwtToken = res.data.access_token
      localStorage.setItem('admin_token', jwtToken)
      setToken(jwtToken)
      setLoginSuccess(`Authenticated as ${res.data.admin_name} (${res.data.role})`)
    } catch (e) {
      setLoginError(e.response?.data?.detail || 'Invalid admin credentials')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('admin_token')
    setToken('')
    setLoginSuccess('')
  }

  const handleOverride = async () => {
    setLoading(true)
    setOverrideError(null)
    setOverrideSuccess(null)
    try {
      const payload = {
        admin_id: adminId,
        admin_name: 'Campus Admin',
        admin_password: password || 'admin123',
        ...overrideForm,
      }
      const res = await adminOverride(payload)
      setOverrideSuccess(res.data)
      fetchData()
    } catch (e) {
      setOverrideError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAddFeedback = () => {
    if (!newComment.trim()) return
    setFeedback([
      ...feedback,
      { id: Date.now(), name: 'Campus Stakeholder', role: newRole, comment: newComment, rating: 5 },
    ])
    setNewComment('')
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Admin Control & Security Panel</h1>
          <p className="text-slate-400 mt-1">
            Environment-variable backed JWT authentication, interactive priority overrides, and Review 2 stakeholder validation
          </p>
        </div>
        <button className="btn-secondary" onClick={fetchData}>
          <RefreshCw size={15} />
        </button>
      </div>

      {/* Role-Based Authentication Card */}
      <div className="card space-y-4 border-l-4 border-l-amber-500">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-semibold text-white">
            <Shield size={18} className="text-amber-400" />
            Role-Based Admin Authentication (JWT Token)
          </div>
          {token && (
            <span className="badge-green flex items-center gap-1">
              <CheckCircle size={12} /> Active Admin Session
            </span>
          )}
        </div>

        {token ? (
          <div className="flex items-center justify-between bg-slate-800/50 p-3 rounded-lg text-sm">
            <div className="text-slate-300">
              Logged in with Bearer Token: <code className="text-brand-400 text-xs">{token.substring(0, 30)}...</code>
            </div>
            <button className="btn-secondary text-xs" onClick={handleLogout}>
              Sign Out Token
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="label">Admin ID</label>
              <input
                className="input-field"
                value={adminId}
                onChange={(e) => setAdminId(e.target.value)}
              />
            </div>
            <div>
              <label className="label">Admin Secret Key / Password</label>
              <input
                type="password"
                className="input-field"
                placeholder="Environment password (admin123)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <button className="btn-primary w-full justify-center" onClick={handleLogin}>
                <Key size={16} /> Authenticate & Issue JWT
              </button>
            </div>
          </div>
        )}

        {loginSuccess && <div className="text-emerald-400 text-xs font-semibold">{loginSuccess}</div>}
        {loginError && <div className="text-red-400 text-xs font-semibold">{loginError}</div>}
      </div>

      {/* Interactive Vehicle Override Controls */}
      <div className="card space-y-5">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Sliders size={18} className="text-brand-400" />
          Interactive Vehicle Priority Override
        </h2>

        {overrideSuccess && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 text-sm text-emerald-400">
            Override applied successfully for {overrideSuccess.vehicle_id}! (New score: {overrideSuccess.new_priority})
          </div>
        )}

        {overrideError && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-400">
            {overrideError}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Select Active Session / Request</label>
            <select
              className="select-field"
              value={overrideForm.request_id}
              onChange={(e) => {
                const s = sessions.find((x) => x.request_id === e.target.value)
                setOverrideForm({
                  ...overrideForm,
                  request_id: e.target.value,
                  vehicle_id: s ? s.vehicle_id : '',
                })
              }}
            >
              <option value="">-- Choose Request --</option>
              {sessions.map((s) => (
                <option key={s.session_id} value={s.request_id}>
                  {s.vehicle_id} ({s.charger_id} — Score: {s.priority_score})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Target Priority Score (0.0 to 1.0)</label>
            <input
              type="number"
              step="0.05"
              min="0"
              max="1"
              className="input-field"
              value={overrideForm.new_priority_score}
              onChange={(e) => setOverrideForm({ ...overrideForm, new_priority_score: parseFloat(e.target.value) })}
            />
          </div>
        </div>

        <div>
          <label className="label">Override Rationale / Justification</label>
          <input
            className="input-field"
            placeholder="e.g. Executive VIP arrival / Emergency medical vehicle"
            value={overrideForm.reason}
            onChange={(e) => setOverrideForm({ ...overrideForm, reason: e.target.value })}
          />
        </div>

        <button
          className="btn-primary w-full justify-center"
          onClick={handleOverride}
          disabled={loading || !overrideForm.request_id}
        >
          {loading ? 'Applying...' : 'Apply Admin Override'}
        </button>
      </div>

      {/* Review 2 Stakeholder Validation Panel */}
      <div className="card space-y-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <MessageSquare size={18} className="text-blue-400" />
          Review 2 Stakeholder Validation & Feedback
        </h2>

        <div className="space-y-3">
          {feedback.map((f) => (
            <div key={f.id} className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-3 text-sm">
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-white">{f.name} <span className="text-xs text-slate-500">({f.role})</span></span>
                <span className="text-amber-400 font-bold">★ {f.rating}/5</span>
              </div>
              <p className="text-slate-300 text-xs">{f.comment}</p>
            </div>
          ))}
        </div>

        <div className="flex gap-2">
          <select className="select-field w-1/3" value={newRole} onChange={(e) => setNewRole(e.target.value)}>
            <option value="Facility Manager">Facility Manager</option>
            <option value="Fleet Director">Fleet Director</option>
            <option value="Campus Employee">Campus Employee</option>
          </select>
          <input
            className="input-field flex-1"
            placeholder="Add stakeholder feedback comment..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
          />
          <button className="btn-secondary shrink-0" onClick={handleAddFeedback}>
            Submit Feedback
          </button>
        </div>
      </div>
    </div>
  )
}
