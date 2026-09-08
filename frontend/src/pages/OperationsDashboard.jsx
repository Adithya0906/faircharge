import React, { useState, useEffect } from 'react'
import { RefreshCw, Zap, Battery, Plug, Activity, Play, CheckCircle } from 'lucide-react'
import { getChargers, getEnergy, getVehicles, getMetrics, runScenario, runScheduler } from '../services/api.js'
import MetricCard from '../components/MetricCard.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useNavigate } from 'react-router-dom'

export default function OperationsDashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState({ chargers: [], energy: null, metrics: null, vehicles: [] })
  const [loading, setLoading] = useState(true)
  const [demoLoading, setDemoLoading] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [c, e, m, v] = await Promise.all([
        getChargers().catch(() => ({ data: [] })),
        getEnergy().catch(() => ({ data: { current_solar_kw: 0, current_battery_kwh: 0, current_grid_kw: 0, current_ev_load_kw: 0, history: [] } })),
        getMetrics('urgency').catch(() => ({ data: { energy_delivery_rate: 0, total_sessions: 0, jains_fairness_index: 0 } })),
        getVehicles().catch(() => ({ data: [] }))
      ])
      setData({ chargers: c.data, energy: e.data, metrics: m.data, vehicles: v.data })
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [])

  const runDemo = async () => {
    setDemoLoading(true)
    try {
      await runScenario({ scenario: 'normal', policy: 'urgency', num_vehicles: 10 })
      await runScheduler({ policy: 'urgency' })
      navigate('/timeline')
    } catch(e) { console.error(e) }
    finally { setDemoLoading(false) }
  }

  const energyHistory = data.energy?.history || []

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Operations Dashboard</h1>
          <p className="text-slate-400 mt-1">Real-time overview of campus charging infrastructure</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn-secondary text-brand-400 hover:text-brand-300 border border-brand-500/30" onClick={runDemo} disabled={demoLoading}>
            {demoLoading ? <div className="w-4 h-4 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin"/> : <Play size={15}/>}
            {demoLoading ? 'Running Demo...' : 'Run Demo Scenario'}
          </button>
          <button className="btn-secondary" onClick={fetchData}><RefreshCw size={15}/></button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard label="Active Sessions" value={data.metrics?.total_sessions || 0} icon={Activity} />
        <MetricCard label="Energy Delivery Rate" value={`${((data.metrics?.energy_delivery_rate || 0)*100).toFixed(1)}%`} icon={Zap} color={data.metrics?.energy_delivery_rate > 0.8 ? 'text-emerald-400' : 'text-amber-400'} />
        <MetricCard label="Jain's Fairness" value={(data.metrics?.jains_fairness_index || 0).toFixed(3)} icon={CheckCircle} color="text-purple-400" />
        <MetricCard label="Current EV Load" value={(data.energy?.current_ev_load_kw || 0).toFixed(1)} unit="kW" icon={Plug} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card space-y-4">
          <h2 className="text-lg font-semibold text-white">Energy Load Profile</h2>
          {energyHistory.length > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={energyHistory}>
                  <defs>
                    <linearGradient id="colorEv" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#14b88a" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#14b88a" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="time" stroke="#475569" fontSize={12} tickFormatter={(t) => new Date(t).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}/>
                  <YAxis stroke="#475569" fontSize={12} />
                  <Tooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px'}} />
                  <Area type="monotone" dataKey="ev_load" stroke="#14b88a" fillOpacity={1} fill="url(#colorEv)" name="EV Load (kW)" />
                  <Area type="monotone" dataKey="solar" stroke="#f59e0b" fillOpacity={0} name="Solar (kW)" />
                  <Area type="monotone" dataKey="grid" stroke="#ef4444" fillOpacity={0} name="Grid Import (kW)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex flex-col items-center justify-center text-slate-500 border border-slate-800 rounded-lg bg-slate-900/50">
              <Activity size={32} className="mb-2 opacity-50"/>
              No energy history available. Run demo scenario.
            </div>
          )}
        </div>

        <div className="card space-y-4">
          <h2 className="text-lg font-semibold text-white">Charger Status</h2>
          <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
            {data.chargers && data.chargers.length > 0 ? data.chargers.map(c => (
              <div key={c.charger_id} className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${c.status === 'charging' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : c.status === 'faulted' ? 'bg-red-500' : 'bg-slate-500'}`} />
                  <div>
                    <div className="text-sm font-semibold text-white">{c.charger_id} <span className="text-xs text-slate-400 font-normal ml-1">({c.type})</span></div>
                    <div className="text-xs text-slate-400 capitalize">{c.status}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-white">{c.max_power_kw} kW</div>
                  <div className="text-xs text-slate-500">Max Power</div>
                </div>
              </div>
            )) : (
              <div className="text-center text-slate-500 py-8 text-sm border border-slate-800 border-dashed rounded-lg">No chargers configured</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
