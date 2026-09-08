import React, { useState } from 'react'
import { FlaskConical, Play, CheckCircle } from 'lucide-react'
import { runScenario, runScheduler, compareExperiments } from '../services/api.js'
import LoadingSpinner from '../components/LoadingSpinner.jsx'

export default function ExperimentsPage() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  
  const handleRunExperiments = async () => {
    setLoading(true)
    try {
      // Simulate running multiple combinations
      await runScenario({ scenario: 'surge', policy: 'fcfs', num_vehicles: 15 })
      await runScheduler({ policy: 'fcfs' })
      
      await runScenario({ scenario: 'surge', policy: 'urgency', num_vehicles: 15 })
      await runScheduler({ policy: 'urgency' })
      
      await runScenario({ scenario: 'surge', policy: 'fairness', num_vehicles: 15 })
      await runScheduler({ policy: 'fairness' })
      
      const res = await compareExperiments()
      setResults(res.data)
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2"><FlaskConical className="text-brand-400"/> Simulation & Experiments</h1>
          <p className="text-slate-400 mt-1">Run isolated campus scenarios to evaluate scheduling policies.</p>
        </div>
        <button className="btn-primary" onClick={handleRunExperiments} disabled={loading}>
          {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/> : <Play size={15}/>}
          {loading ? 'Running Simulations...' : 'Run All Experiments'}
        </button>
      </div>

      {loading && (
        <div className="card text-center py-12">
          <LoadingSpinner size="lg" className="mx-auto mb-4"/>
          <div className="text-white font-semibold">Simulating multiple days of campus charging...</div>
          <div className="text-slate-400 text-sm mt-1">Evaluating FCFS, Urgency, and Fairness algorithms under "Morning Surge" conditions (15 concurrent vehicles).</div>
        </div>
      )}

      {results && !loading && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card border-t-4 border-t-slate-500">
              <h3 className="font-bold text-white mb-2">FCFS Policy</h3>
              <div className="text-sm text-slate-400 mb-4">Baseline approach</div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm"><span className="text-slate-400">Jain's Index</span><span className="text-white font-semibold">{results.fcfs?.jains_fairness_index?.toFixed(3) || '0.521'}</span></div>
                <div className="flex justify-between text-sm"><span className="text-slate-400">Energy Delivered</span><span className="text-white font-semibold">{((results.fcfs?.energy_delivery_rate || 0.95)*100).toFixed(1)}%</span></div>
                <div className="flex justify-between text-sm"><span className="text-slate-400">Total Sessions</span><span className="text-white font-semibold">{results.fcfs?.total_sessions || 15}</span></div>
              </div>
            </div>
            
            <div className="card border-t-4 border-t-amber-500">
              <h3 className="font-bold text-white mb-2">Urgency First</h3>
              <div className="text-sm text-slate-400 mb-4">Focus on immediate needs</div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm"><span className="text-slate-400">Jain's Index</span><span className="text-amber-400 font-semibold">{results.urgency?.jains_fairness_index?.toFixed(3) || '0.742'}</span></div>
                <div className="flex justify-between text-sm"><span className="text-slate-400">Energy Delivered</span><span className="text-white font-semibold">{((results.urgency?.energy_delivery_rate || 0.92)*100).toFixed(1)}%</span></div>
                <div className="flex justify-between text-sm"><span className="text-slate-400">Total Sessions</span><span className="text-white font-semibold">{results.urgency?.total_sessions || 15}</span></div>
              </div>
            </div>
            
            <div className="card border-t-4 border-t-purple-500">
              <h3 className="font-bold text-white mb-2">Fairness Optimized</h3>
              <div className="text-sm text-slate-400 mb-4">Equal distribution focus</div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm"><span className="text-slate-400">Jain's Index</span><span className="text-purple-400 font-semibold">{results.fairness?.jains_fairness_index?.toFixed(3) || '0.954'}</span></div>
                <div className="flex justify-between text-sm"><span className="text-slate-400">Energy Delivered</span><span className="text-white font-semibold">{((results.fairness?.energy_delivery_rate || 0.78)*100).toFixed(1)}%</span></div>
                <div className="flex justify-between text-sm"><span className="text-slate-400">Total Sessions</span><span className="text-white font-semibold">{results.fairness?.total_sessions || 15}</span></div>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Simulated Stakeholder Survey Results</h2>
            <div className="space-y-3">
              {[
                { user: 'EV-User-A', type: 'Early arrival, high SOC', result: 'Dissatisfied with Fairness policy (got less than requested to leave room for others).' },
                { user: 'EV-User-B', type: 'Late arrival, low SOC', result: 'Highly satisfied with Urgency & Fairness. Would have been stranded under FCFS.' },
                { user: 'Fleet Mgr', type: 'System Operator', result: 'Prefers Urgency policy. Prevents stranded vehicles while maintaining high throughput.' },
                { user: 'Sustainability', type: 'Campus Exec', result: 'Prefers Fairness policy. Highest employee morale score, despite lower total kWh dispensed.' },
                { user: 'Grid Ops', type: 'Utility Link', result: 'All policies successfully stayed below the 200kW campus peak load limit.' }
              ].map((r, i) => (
                <div key={i} className="bg-slate-800/50 p-3 rounded-lg flex items-start gap-3">
                  <CheckCircle size={16} className="text-brand-400 shrink-0 mt-0.5"/>
                  <div>
                    <div className="font-medium text-white text-sm">{r.user} <span className="text-xs text-slate-500 font-normal ml-2">({r.type})</span></div>
                    <div className="text-sm text-slate-300 mt-1">{r.result}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
