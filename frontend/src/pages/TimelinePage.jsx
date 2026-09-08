import React, { useState, useEffect } from 'react'
import { getSchedule } from '../services/api.js'
import LoadingSpinner from '../components/LoadingSpinner.jsx'

export default function TimelinePage() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSchedule({}).then(res => setSessions(res.data)).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center p-12"><LoadingSpinner size="lg"/></div>

  if (sessions.length === 0) return (
    <div className="text-center p-12 card text-slate-400">No scheduled sessions. Run the scheduler first.</div>
  )

  const vehicles = [...new Set(sessions.map(s => s.vehicle_id))].sort()
  const minTime = Math.min(...sessions.map(s => new Date(s.start_time).getTime()))
  const maxTime = Math.max(...sessions.map(s => new Date(s.end_time).getTime()))
  const durationMs = maxTime - minTime || 3600000 // default 1h if 0

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Charging Timeline</h1>
        <p className="text-slate-400 mt-1">Gantt chart view of all scheduled charging sessions.</p>
      </div>

      <div className="card overflow-x-auto">
        <div className="min-w-[800px]">
          <div className="flex mb-2 text-xs text-slate-500 border-b border-slate-800 pb-2">
            <div className="w-32 shrink-0">Vehicle</div>
            <div className="flex-1 flex justify-between relative">
              <span>{new Date(minTime).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>
              <span>{new Date(maxTime).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>
            </div>
          </div>
          
          <div className="space-y-4 py-2">
            {vehicles.map(vid => {
              const vSessions = sessions.filter(s => s.vehicle_id === vid)
              return (
                <div key={vid} className="flex items-center">
                  <div className="w-32 shrink-0 text-sm font-medium text-slate-300">{vid}</div>
                  <div className="flex-1 h-8 bg-slate-800/30 rounded relative border border-slate-800">
                    {vSessions.map(s => {
                      const start = new Date(s.start_time).getTime()
                      const end = new Date(s.end_time).getTime()
                      const left = ((start - minTime) / durationMs) * 100
                      const width = ((end - start) / durationMs) * 100
                      const isDc = s.charger_id.includes('DC')
                      const bg = s.is_admin_override ? 'bg-amber-500' : isDc ? 'bg-emerald-500' : 'bg-brand-500'
                      
                      return (
                        <div 
                          key={s.session_id} 
                          className={`absolute h-full rounded ${bg} opacity-80 hover:opacity-100 transition-opacity cursor-pointer group`}
                          style={{ left: `${left}%`, width: `${Math.max(width, 0.5)}%` }}
                        >
                          <div className="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max bg-slate-900 border border-slate-700 text-xs p-2 rounded shadow-xl z-10">
                            <div className="font-bold text-white">{vid} @ {s.charger_id}</div>
                            <div className="text-slate-300 mt-1">{new Date(start).toLocaleTimeString()} - {new Date(end).toLocaleTimeString()}</div>
                            <div className="text-slate-400">Policy: {s.policy} | {s.planned_energy_kwh} kWh</div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
      
      <div className="flex gap-4 text-xs">
        <div className="flex items-center gap-2"><div className="w-3 h-3 bg-brand-500 rounded"/> AC Charger</div>
        <div className="flex items-center gap-2"><div className="w-3 h-3 bg-emerald-500 rounded"/> DC Fast Charger</div>
        <div className="flex items-center gap-2"><div className="w-3 h-3 bg-amber-500 rounded"/> Admin Override</div>
      </div>
    </div>
  )
}
