import React, { useState, useEffect } from 'react'
import { getMetrics } from '../services/api.js'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Users, Info } from 'lucide-react'

export default function FairnessDashboard() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMetrics('fairness').then(res => setMetrics(res.data)).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center p-12"><LoadingSpinner size="lg"/></div>

  const jains = metrics?.jains_fairness_index || 0
  const color = jains >= 0.85 ? 'text-emerald-400' : jains >= 0.7 ? 'text-amber-400' : 'text-red-400'

  const data = Object.keys(metrics?.satisfaction_ratio_per_vehicle || {}).map(k => ({
    name: k,
    ratio: (metrics.satisfaction_ratio_per_vehicle[k] * 100).toFixed(1)
  }))

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Fairness Metrics</h1>
        <p className="text-slate-400 mt-1">Analysis of allocation fairness across all requested sessions.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card flex flex-col items-center justify-center text-center p-8">
          <h2 className="text-sm text-slate-400 font-medium uppercase tracking-wider mb-2">Jain's Fairness Index</h2>
          <div className={`text-6xl font-bold ${color} my-4`}>{jains.toFixed(3)}</div>
          <p className="text-xs text-slate-500 max-w-[200px]">1.0 means perfectly fair (equal satisfaction for all users). &lt;0.7 is unfair.</p>
        </div>
        
        <div className="md:col-span-2 card">
          <div className="flex items-center gap-2 mb-4">
            <Users size={18} className="text-brand-400"/>
            <h2 className="text-lg font-semibold text-white">Satisfaction by Vehicle</h2>
          </div>
          {data.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="name" stroke="#475569" fontSize={12} />
                  <YAxis stroke="#475569" fontSize={12} domain={[0, 100]} />
                  <Tooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px'}} formatter={(val) => [`${val}%`, 'Satisfaction']} />
                  <Bar dataKey="ratio" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-500">No session data available</div>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Policy Comparison</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase font-semibold">
              <tr>
                <th className="px-4 py-3 rounded-tl-lg">Policy</th>
                <th className="px-4 py-3">Jain's Index</th>
                <th className="px-4 py-3">Energy Delivery Rate</th>
                <th className="px-4 py-3 rounded-tr-lg">Behavior</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              <tr>
                <td className="px-4 py-3 font-medium text-white"><span className="px-2 py-1 bg-slate-700 rounded text-xs mr-2">FCFS</span> First Come First Serve</td>
                <td className="px-4 py-3 text-red-400">Low (~0.5 - 0.6)</td>
                <td className="px-4 py-3 text-emerald-400">High (&gt;90%)</td>
                <td className="px-4 py-3 text-slate-400">Favors early arrivals; late arrivals get nothing.</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-medium text-white"><span className="px-2 py-1 bg-amber-500/20 text-amber-400 rounded text-xs mr-2">URGENCY</span> Urgency First</td>
                <td className="px-4 py-3 text-amber-400">Medium (~0.7 - 0.8)</td>
                <td className="px-4 py-3 text-emerald-400">High (&gt;90%)</td>
                <td className="px-4 py-3 text-slate-400">Prioritizes vehicles leaving soon or with low SOC.</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-medium text-white"><span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded text-xs mr-2">FAIRNESS</span> Fairness First</td>
                <td className="px-4 py-3 text-emerald-400">High (&gt;0.9)</td>
                <td className="px-4 py-3 text-amber-400">Medium (~70-85%)</td>
                <td className="px-4 py-3 text-slate-400">Distributes energy proportionally; may underutilize chargers to ensure fairness.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
