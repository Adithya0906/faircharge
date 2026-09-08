import React, { useState, useEffect } from 'react'
import { Calendar, RefreshCw, Zap, Clock, Battery, AlertTriangle, CheckCircle, Info } from 'lucide-react'
import { getSchedule, runScheduler } from '../services/api.js'
import { useAuth } from '../App.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import PolicyBadge from '../components/PolicyBadge.jsx'

export default function MySchedulePage() {
  const { userId } = useAuth()
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [policy, setPolicy] = useState('urgency')
  const [error, setError] = useState(null)
  const [runResult, setRunResult] = useState(null)

  const fetchSchedule = async () => {
    setLoading(true)
    try {
      const res = await getSchedule({})
      setSessions(res.data.filter(s => s.user_id === userId || s.vehicle_id === userId))
    } catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchSchedule() }, [userId])

  const handleRunScheduler = async () => {
    setRunning(true)
    try {
      const res = await runScheduler({ policy })
      setRunResult(res.data)
      await fetchSchedule()
    } catch(e) { setError(e.message) }
    finally { setRunning(false) }
  }

  const formatTime = (iso) => new Date(iso).toLocaleString([], { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' })
  const duration = (start, end) => {
    const m = (new Date(end) - new Date(start)) / 60000
    return m >= 60 ? `${(m/60).toFixed(1)}h` : `${Math.round(m)}m`
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">My Charging Schedule</h1>
          <p className="text-slate-400 mt-1">Your assigned charging sessions and their explanations</p>
        </div>
        <div className="flex items-center gap-3">
          <select className="select-field w-auto" value={policy} onChange={e=>setPolicy(e.target.value)}>
            <option value="fcfs">FCFS</option>
            <option value="urgency">Urgency First</option>
            <option value="fairness">Fairness First</option>
          </select>
          <button className="btn-primary" onClick={handleRunScheduler} disabled={running}>
            {running ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/> : <Zap size={15}/>}
            Run Scheduler
          </button>
          <button className="btn-secondary" onClick={fetchSchedule}><RefreshCw size={15}/></button>
        </div>
      </div>

      {runResult && (
        <div className="bg-brand-500/10 border border-brand-500/30 rounded-lg p-4 text-sm">
          <div className="text-brand-400 font-semibold">Scheduler ran successfully</div>
          <div className="text-slate-300 mt-1">{runResult.sessions_created} sessions created | Energy delivery rate: {(runResult.metrics?.energy_delivery_rate * 100 || 0).toFixed(1)}% | Jain's fairness: {runResult.metrics?.jains_fairness_index?.toFixed(3) || 'N/A'}</div>
        </div>
      )}

      {loading ? <div className="flex justify-center py-12"><LoadingSpinner size="lg"/></div> : (
        sessions.length === 0 ? (
          <div className="card text-center py-12">
            <Calendar size={40} className="text-slate-600 mx-auto mb-4"/>
            <div className="text-slate-400">No charging sessions scheduled yet.</div>
            <div className="text-slate-500 text-sm mt-2">Submit a charging request, then run the scheduler.</div>
          </div>
        ) : (
          <div className="space-y-4">
            {sessions.map(s => (
              <div key={s.session_id} className={`card border-l-4 ${s.is_fully_served ? 'border-l-emerald-500' : s.failure_reason ? 'border-l-amber-500' : 'border-l-slate-600'}`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="font-semibold text-white text-lg">{s.vehicle_id}</div>
                    <PolicyBadge policy={s.policy}/>
                    {s.is_admin_override && <span className="badge-yellow">ADMIN OVERRIDE</span>}
                  </div>
                  <div className={`flex items-center gap-1.5 text-sm font-semibold ${
                    s.is_fully_served ? 'text-emerald-400' : 'text-amber-400'
                  }`}>
                    {s.is_fully_served ? <CheckCircle size={14}/> : <AlertTriangle size={14}/>}
                    {s.is_fully_served ? 'Fully Served' : 'Partial'}
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div><div className="text-xs text-slate-500">Charger</div><div className="font-medium text-white text-sm">{s.charger_id}</div></div>
                  <div><div className="text-xs text-slate-500">Start</div><div className="font-medium text-white text-sm">{formatTime(s.start_time)}</div></div>
                  <div><div className="text-xs text-slate-500">End</div><div className="font-medium text-white text-sm">{formatTime(s.end_time)}</div></div>
                  <div><div className="text-xs text-slate-500">Duration</div><div className="font-medium text-white text-sm">{duration(s.start_time, s.end_time)}</div></div>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="text-xs text-slate-500 mb-1">Planned Energy</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-800 rounded-full h-2">
                        <div className="bg-brand-500 h-2 rounded-full" style={{width:`${Math.min(100, s.planned_energy_kwh/40*100)}%`}}/>
                      </div>
                      <span className="text-sm font-semibold text-white">{s.planned_energy_kwh} kWh</span>
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 mb-1">Priority Score</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-800 rounded-full h-2">
                        <div className="bg-amber-500 h-2 rounded-full" style={{width:`${s.priority_score*100}%`}}/>
                      </div>
                      <span className="text-sm font-semibold text-white">{s.priority_score?.toFixed(3)}</span>
                    </div>
                  </div>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-3 flex items-start gap-2">
                  <Info size={13} className="text-brand-400 shrink-0 mt-0.5"/>
                  <p className="text-xs text-slate-300 leading-relaxed">{s.explanation}</p>
                </div>
                {s.failure_reason && (
                  <div className="mt-3 flex items-start gap-2 bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
                    <AlertTriangle size={13} className="text-amber-400 shrink-0 mt-0.5"/>
                    <p className="text-xs text-amber-300">{s.failure_reason}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
