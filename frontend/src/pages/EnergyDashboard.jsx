import React, { useState, useEffect } from 'react'
import { Sun, Battery, Plug, DollarSign, CloudRain, RefreshCw, AlertCircle } from 'lucide-react'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, Legend, BarChart, Bar } from 'recharts'
import { getEnergy } from '../services/api.js'
import LoadingSpinner from '../components/LoadingSpinner.jsx'

export default function EnergyDashboard() {
  const [energyData, setEnergyData] = useState([])
  const [scenario, setScenario] = useState('normal')
  const [loading, setLoading] = useState(true)

  const fetchEnergy = async (sc = scenario) => {
    setLoading(true)
    try {
      const res = await getEnergy(sc)
      setEnergyData(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEnergy(scenario)
  }, [scenario])

  const formatTime = (ts) => {
    const d = new Date(ts)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Campus Energy & Tariff Dashboard</h1>
          <p className="text-slate-400 mt-1">
            Dynamic Time-of-Use (ToU) grid tariffs, solar intermittency profiles, and battery storage bounds
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            className="select-field w-auto"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
          >
            <option value="normal">Normal (Clear Sky)</option>
            <option value="cloudy">Cloudy Ramp (Stochastic Pass-over)</option>
            <option value="low_solar">Low Solar (Overcast)</option>
            <option value="grid_constraint">Grid Constraint (10 kW Limit)</option>
            <option value="battery_low">Battery Reserve Low</option>
          </select>
          <button className="btn-secondary" onClick={() => fetchEnergy(scenario)}>
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      {/* Tariff Legend Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card border-l-4 border-l-emerald-500 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Off-Peak Tariff (22:00 - 08:00)</div>
            <div className="text-xl font-bold text-emerald-400">$0.10 <span className="text-xs text-slate-500">/ kWh</span></div>
          </div>
          <DollarSign className="text-emerald-500/30" size={28} />
        </div>
        <div className="card border-l-4 border-l-amber-500 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Mid-Peak Tariff (08:00 - 14:00 & 20:00 - 22:00)</div>
            <div className="text-xl font-bold text-amber-400">$0.20 <span className="text-xs text-slate-500">/ kWh</span></div>
          </div>
          <DollarSign className="text-amber-500/30" size={28} />
        </div>
        <div className="card border-l-4 border-l-red-500 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">On-Peak Tariff (14:00 - 20:00)</div>
            <div className="text-xl font-bold text-red-400">$0.35 <span className="text-xs text-slate-500">/ kWh</span></div>
          </div>
          <DollarSign className="text-red-500/30" size={28} />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <div className="space-y-6">
          {/* Main Power Generation vs Demand Chart */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Sun size={18} className="text-amber-400" />
              Power Generation, Load & Solar Intermittency (24h Profile)
            </h2>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={energyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="timestamp" tickFormatter={formatTime} stroke="#94a3b8" />
                  <YAxis label={{ value: 'Power (kW)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    labelFormatter={formatTime}
                  />
                  <Legend />
                  <Area type="monotone" dataKey="solar_generation_kw" name="Solar Generation (kW)" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.25} />
                  <Area type="monotone" dataKey="campus_load_kw" name="Campus Base Load (kW)" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} />
                  <Area type="monotone" dataKey="ev_charging_load_kw" name="EV Charging Load (kW)" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                  <Area type="monotone" dataKey="grid_import_kw" name="Grid Import (kW)" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Time-of-Use Rate Profile & Battery Reserve Chart */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="text-md font-semibold text-white mb-3 flex items-center gap-2">
                <DollarSign size={16} className="text-emerald-400" />
                Dynamic ToU Grid Tariff Schedule ($/kWh)
              </h2>
              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={energyData.map(d => ({ ...d, rate: d.tou_tariff?.rate_usd_per_kwh || 0.2 }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="timestamp" tickFormatter={formatTime} stroke="#94a3b8" />
                    <YAxis domain={[0, 0.4]} stroke="#94a3b8" />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} labelFormatter={formatTime} />
                    <Bar dataKey="rate" name="Tariff ($/kWh)" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <h2 className="text-md font-semibold text-white mb-3 flex items-center gap-2">
                <Battery size={16} className="text-brand-400" />
                Battery State of Charge (SoC kWh)
              </h2>
              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={energyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="timestamp" tickFormatter={formatTime} stroke="#94a3b8" />
                    <YAxis domain={[0, 150]} stroke="#94a3b8" />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} labelFormatter={formatTime} />
                    <Area type="monotone" dataKey="battery_soc_kwh" name="Battery SoC (kWh)" stroke="#14b88a" fill="#14b88a" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
