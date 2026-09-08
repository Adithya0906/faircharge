import React, { useState, useEffect } from 'react'
import { Zap, AlertTriangle, CheckCircle, Clock, Battery, Info } from 'lucide-react'
import { submitChargingRequest } from '../services/api.js'
import { useAuth } from '../App.jsx'

export default function RequestPage() {
  const { userId } = useAuth()
  const [form, setForm] = useState({
    vehicle_id: userId || 'EV-001',
    user_id: userId || 'EMP-001',
    arrival_time: '',
    departure_time: '',
    battery_capacity_kwh: 75,
    initial_soc: 0.3,
    required_energy_kwh: 30,
    max_charging_power_kw: 22,
    charger_type: 'AC',
    priority_category: 'standard',
  })
  const [warnings, setWarnings] = useState([])
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState(null)

  // Auto-fill with today's times as default
  useEffect(() => {
    const now = new Date()
    now.setMinutes(0, 0, 0)
    const arrival = new Date(now)
    arrival.setHours(9, 0, 0)
    const departure = new Date(now)
    departure.setHours(17, 0, 0)
    setForm(f => ({
      ...f,
      arrival_time: toLocalInput(arrival),
      departure_time: toLocalInput(departure),
    }))
  }, [])

  function toLocalInput(d) {
    const pad = n => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
  }

  // Real-time validation
  useEffect(() => {
    const w = []
    if (form.arrival_time && form.departure_time) {
      const arr = new Date(form.arrival_time)
      const dep = new Date(form.departure_time)
      if (dep <= arr) { w.push('Departure must be after arrival.'); }
      else {
        const windowH = (dep - arr) / 3600000
        const maxPossible = windowH * form.max_charging_power_kw
        if (form.required_energy_kwh > maxPossible) {
          w.push(`WARNING: Cannot deliver ${form.required_energy_kwh} kWh in ${windowH.toFixed(1)}h window. Max possible: ${maxPossible.toFixed(1)} kWh.`)
        }
        const maxBattery = form.battery_capacity_kwh * (1 - form.initial_soc)
        if (form.required_energy_kwh > maxBattery) {
          w.push(`Required energy (${form.required_energy_kwh} kWh) exceeds available battery space (${maxBattery.toFixed(1)} kWh).`)
        }
      }
    }
    if (form.required_energy_kwh <= 0) w.push('Required energy must be greater than 0.')
    setWarnings(w)
  }, [form])

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)
    try {
      const payload = {
        ...form,
        arrival_time: new Date(form.arrival_time).toISOString(),
        departure_time: new Date(form.departure_time).toISOString(),
      }
      const res = await submitChargingRequest(payload)
      setSuccess(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  const updateForm = (k, v) => setForm(f => ({ ...f, [k]: v }))

  // Estimated completion
  const estCompletion = () => {
    if (!form.arrival_time) return null
    const arr = new Date(form.arrival_time)
    const h = form.required_energy_kwh / form.max_charging_power_kw
    const comp = new Date(arr.getTime() + h * 3600000)
    return comp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Request EV Charging</h1>
        <p className="text-slate-400 mt-1">Submit your vehicle's charging requirements. The scheduler will assign a fair slot.</p>
      </div>

      {success && (
        <div className="flex items-start gap-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg p-4 animate-fade-in">
          <CheckCircle size={16} className="shrink-0 mt-0.5"/>
          <div>
            <div className="font-semibold">Request submitted!</div>
            <div className="text-sm mt-1">ID: {success.request_id} — {success.message}</div>
            {success.validation_warnings?.map((w,i) => <div key={i} className="text-amber-400 text-xs mt-1">⚠ {w}</div>)}
          </div>
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-4">
          <AlertTriangle size={16} className="shrink-0 mt-0.5"/>
          <span className="text-sm">{error}</span>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="space-y-2">
          {warnings.map((w,i) => (
            <div key={i} className="flex items-start gap-2 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-lg p-3 text-sm">
              <AlertTriangle size={14} className="shrink-0 mt-0.5"/><span>{w}</span>
            </div>
          ))}
        </div>
      )}

      <div className="card space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label">Vehicle ID</label><input className="input-field" value={form.vehicle_id} onChange={e=>updateForm('vehicle_id',e.target.value)}/></div>
          <div><label className="label">User ID</label><input className="input-field" value={form.user_id} onChange={e=>updateForm('user_id',e.target.value)}/></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label">Arrival Time</label><input type="datetime-local" className="input-field" value={form.arrival_time} onChange={e=>updateForm('arrival_time',e.target.value)}/></div>
          <div><label className="label">Departure Time</label><input type="datetime-local" className="input-field" value={form.departure_time} onChange={e=>updateForm('departure_time',e.target.value)}/></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label">Battery Capacity (kWh)</label><input type="number" className="input-field" value={form.battery_capacity_kwh} onChange={e=>updateForm('battery_capacity_kwh',+e.target.value)}/></div>
          <div>
            <label className="label">Current SOC: {Math.round(form.initial_soc*100)}%</label>
            <input type="range" min="0" max="1" step="0.05" className="w-full accent-brand-500" value={form.initial_soc} onChange={e=>updateForm('initial_soc',+e.target.value)}/>
            <div className="flex justify-between text-xs text-slate-500 mt-1"><span>0%</span><span>100%</span></div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label">Required Energy (kWh)</label><input type="number" className="input-field" value={form.required_energy_kwh} onChange={e=>updateForm('required_energy_kwh',+e.target.value)}/></div>
          <div><label className="label">Max Charging Power (kW)</label><input type="number" className="input-field" value={form.max_charging_power_kw} onChange={e=>updateForm('max_charging_power_kw',+e.target.value)}/></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Charger Type</label>
            <select className="select-field" value={form.charger_type} onChange={e=>updateForm('charger_type',e.target.value)}>
              <option value="AC">AC (up to 22 kW)</option>
              <option value="DC">DC Fast (up to 50 kW)</option>
            </select>
          </div>
          <div>
            <label className="label">Priority Category</label>
            <select className="select-field" value={form.priority_category} onChange={e=>updateForm('priority_category',e.target.value)}>
              <option value="standard">Standard</option>
              <option value="priority">Priority</option>
              <option value="emergency">Emergency</option>
            </select>
          </div>
        </div>

        {/* Estimated completion */}
        {form.arrival_time && form.required_energy_kwh > 0 && (
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 flex items-center gap-3">
            <Clock size={16} className="text-brand-400 shrink-0"/>
            <div className="text-sm">
              <span className="text-slate-400">Estimated completion: </span>
              <span className="text-white font-semibold">{estCompletion()}</span>
              <span className="text-slate-500 ml-2">(based on max charging power)</span>
            </div>
          </div>
        )}

        <div className="bg-slate-800/30 rounded-lg p-3 text-xs text-slate-500 flex items-start gap-2">
          <Info size={12} className="shrink-0 mt-0.5"/>
          <span>Hard constraints: energy cannot exceed battery capacity, charging cannot start before arrival or continue after departure. Warnings above indicate potential issues.</span>
        </div>

        <button className="btn-primary w-full justify-center" onClick={handleSubmit} disabled={loading || warnings.some(w=>w.startsWith('Departure must'))}>
          {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/> : <Zap size={16}/>}
          {loading ? 'Submitting...' : 'Request Charging'}
        </button>
      </div>
    </div>
  )
}
