import React, { useState, useEffect } from 'react'
import { getEnergy } from '../services/api.js'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import MetricCard from '../components/MetricCard.jsx'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts'
import { Sun, Battery, Plug, Activity } from 'lucide-react'

export default function EnergyDashboard() {
  const [energy, setEnergy] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getEnergy().then(res => setEnergy(res.data)).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center p-12"><LoadingSpinner size="lg"/></div>

  const history = energy?.history || []

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Energy Dashboard</h1>
        <p className="text-slate-400 mt-1">Real-time solar, battery, grid, and EV charging load.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard label="Solar Generation" value={(energy?.current_solar_kw || 0).toFixed(1)} unit="kW" icon={Sun} color="text-amber-400" />
        <MetricCard label="Campus Base Load" value={(energy?.current_campus_load_kw || 0).toFixed(1)} unit="kW" icon={Activity} color="text-blue-400" />
        <MetricCard label="EV Charging Load" value={(energy?.current_ev_load_kw || 0).toFixed(1)} unit="kW" icon={Plug} color="text-brand-400" />
        <MetricCard label="Battery SOC" value={`${(energy?.current_battery_soc * 100 || 0).toFixed(1)}%`} icon={Battery} color="text-purple-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold text-white">Power Flows (kW)</h2>
          {history.length > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history}>
                  <defs>
                    <linearGradient id="colorSolar" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/><stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/></linearGradient>
                    <linearGradient id="colorEv" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#14b88a" stopOpacity={0.3}/><stop offset="95%" stopColor="#14b88a" stopOpacity={0}/></linearGradient>
                    <linearGradient id="colorGrid" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/><stop offset="95%" stopColor="#ef4444" stopOpacity={0}/></linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="time" stroke="#475569" fontSize={12} tickFormatter={(t) => new Date(t).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}/>
                  <YAxis stroke="#475569" fontSize={12} />
                  <Tooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px'}} />
                  <Legend />
                  <Area type="monotone" dataKey="solar" stroke="#f59e0b" fillOpacity={1} fill="url(#colorSolar)" name="Solar" />
                  <Area type="monotone" dataKey="ev_load" stroke="#14b88a" fillOpacity={1} fill="url(#colorEv)" name="EV Load" />
                  <Area type="monotone" dataKey="grid" stroke="#ef4444" fillOpacity={1} fill="url(#colorGrid)" name="Grid Import" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex items-center justify-center text-slate-500">No energy history</div>
          )}
        </div>
        
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold text-white">Battery State of Charge (%)</h2>
          {history.length > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="time" stroke="#475569" fontSize={12} tickFormatter={(t) => new Date(t).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}/>
                  <YAxis stroke="#475569" fontSize={12} domain={[0, 100]} />
                  <Tooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px'}} formatter={(val) => [`${(val*100).toFixed(1)}%`, 'Battery SOC']} />
                  <Line type="stepAfter" dataKey="battery_soc" stroke="#a855f7" strokeWidth={2} dot={false} name="SOC" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex items-center justify-center text-slate-500">No energy history</div>
          )}
        </div>
      </div>
    </div>
  )
}
