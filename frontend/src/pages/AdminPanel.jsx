import React, { useState, useEffect } from 'react'
import { Settings, ShieldAlert, CheckCircle, Zap } from 'lucide-react'
import { getCampusConfig, updateCampusConfig, adminOverride } from '../services/api.js'
import ErrorBanner from '../components/ErrorBanner.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'

export default function AdminPanel() {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  
  const [overrideForm, setOverrideForm] = useState({
    admin_id: 'admin',
    admin_password: '',
    vehicle_id: '',
    request_id: '',
    new_priority_score: 100.0,
    reason: ''
  })

  useEffect(() => { fetchConfig() }, [])

  const fetchConfig = async () => {
    try {
      const res = await getCampusConfig()
      setConfig(res.data)
    } catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const handleConfigUpdate = async () => {
    try {
      await updateCampusConfig({
        max_grid_import_kw: config.max_grid_import_kw,
        battery_reserve_soc: config.battery_reserve_soc
      })
      setSuccess('Campus config updated successfully.')
      setTimeout(() => setSuccess(null), 3000)
    } catch(e) { setError(e.message) }
  }

  const handleOverride = async () => {
    try {
      await adminOverride(overrideForm)
      setSuccess(`Override applied successfully for ${overrideForm.vehicle_id}`)
      setTimeout(() => setSuccess(null), 3000)
      setOverrideForm(f => ({ ...f, vehicle_id: '', request_id: '', reason: '' }))
    } catch(e) { setError(e.response?.data?.detail || e.message) }
  }

  if (loading) return <div className="flex justify-center p-12"><LoadingSpinner size="lg"/></div>

  return (
    <div className="max-w-4xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2"><Settings className="text-amber-400"/> Admin Control Panel</h1>
        <p className="text-slate-400 mt-1">Configure campus parameters and perform manual overrides.</p>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
      {success && (
        <div className="flex items-start gap-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg p-4">
          <CheckCircle size={16} className="shrink-0 mt-0.5"/>
          <span className="text-sm">{success}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card space-y-5">
          <h2 className="text-lg font-semibold text-white border-b border-slate-800 pb-2">Campus Configuration</h2>
          {config && (
            <>
              <div>
                <label className="label">Max Grid Import (kW)</label>
                <div className="flex items-center gap-4">
                  <input type="range" min="0" max="500" step="10" className="w-full accent-brand-500" value={config.max_grid_import_kw} onChange={e=>setConfig({...config, max_grid_import_kw: +e.target.value})}/>
                  <span className="text-white font-semibold w-16 text-right">{config.max_grid_import_kw} kW</span>
                </div>
              </div>
              <div>
                <label className="label">Battery Reserve SOC (%)</label>
                <div className="flex items-center gap-4">
                  <input type="range" min="0" max="1" step="0.05" className="w-full accent-brand-500" value={config.battery_reserve_soc} onChange={e=>setConfig({...config, battery_reserve_soc: +e.target.value})}/>
                  <span className="text-white font-semibold w-16 text-right">{Math.round(config.battery_reserve_soc * 100)}%</span>
                </div>
              </div>
              <button className="btn-secondary w-full justify-center" onClick={handleConfigUpdate}>Save Configuration</button>
            </>
          )}
        </div>

        <div className="card space-y-5 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.05)]">
          <h2 className="text-lg font-semibold text-amber-400 border-b border-slate-800 pb-2 flex items-center gap-2"><ShieldAlert size={18}/> Manual Priority Override</h2>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">Admin ID</label><input className="input-field" value={overrideForm.admin_id} onChange={e=>setOverrideForm({...overrideForm, admin_id: e.target.value})}/></div>
            <div><label className="label">Admin Password</label><input type="password" className="input-field" value={overrideForm.admin_password} onChange={e=>setOverrideForm({...overrideForm, admin_password: e.target.value})}/></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">Vehicle ID</label><input className="input-field" placeholder="EV-001" value={overrideForm.vehicle_id} onChange={e=>setOverrideForm({...overrideForm, vehicle_id: e.target.value})}/></div>
            <div><label className="label">Request ID (optional)</label><input className="input-field" value={overrideForm.request_id} onChange={e=>setOverrideForm({...overrideForm, request_id: e.target.value})}/></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">New Priority Score</label><input type="number" className="input-field text-amber-400 font-semibold" value={overrideForm.new_priority_score} onChange={e=>setOverrideForm({...overrideForm, new_priority_score: +e.target.value})}/></div>
            <div><label className="label">Reason</label><input className="input-field" placeholder="VIP visitor" value={overrideForm.reason} onChange={e=>setOverrideForm({...overrideForm, reason: e.target.value})}/></div>
          </div>
          <button className="bg-amber-600 hover:bg-amber-500 text-white font-semibold px-5 py-2.5 rounded-lg transition-all flex items-center justify-center gap-2 w-full" onClick={handleOverride}>
            <Zap size={16}/> Apply Override
          </button>
        </div>
      </div>
    </div>
  )
}
