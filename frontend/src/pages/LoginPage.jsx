import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App.jsx'
import { Zap, User, Shield, Sun, Battery, Plug, ChevronRight } from 'lucide-react'

export default function LoginPage() {
  const { login } = useAuth()
  const [selectedRole, setSelectedRole] = useState(null)
  const [userId, setUserId] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = () => {
    if (!userId.trim()) return
    setLoading(true)
    setTimeout(() => {
      login(selectedRole, userId)
      navigate('/dashboard')
    }, 500)
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-brand-500/10 rounded-full blur-3xl pointer-events-none"/>
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-blue-500/5 rounded-full blur-3xl pointer-events-none"/>
      
      <div className="w-full max-w-md px-6 animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-brand-500 rounded-2xl shadow-xl shadow-brand-500/30 mb-4">
            <Zap size={32} className="text-white"/>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">FairCharge</h1>
          <p className="text-slate-400">Fair, transparent EV charging for shared workplaces.</p>
        </div>

        {!selectedRole ? (
          <div className="space-y-4">
            <p className="text-center text-sm text-slate-400 mb-6">Select your role to continue</p>
            <button onClick={() => setSelectedRole('user')} className="w-full card hover:border-brand-500/50 hover:bg-slate-800/50 transition-all p-5 text-left group">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-brand-500/15 rounded-xl flex items-center justify-center group-hover:bg-brand-500/25 transition-all">
                  <User size={24} className="text-brand-400"/>
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-white">Employee / User</div>
                  <div className="text-sm text-slate-400 mt-0.5">Submit charging requests, view your schedule</div>
                </div>
                <ChevronRight size={16} className="text-slate-600 group-hover:text-slate-400"/>
              </div>
            </button>
            <button onClick={() => setSelectedRole('admin')} className="w-full card hover:border-amber-500/50 hover:bg-slate-800/50 transition-all p-5 text-left group">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-amber-500/15 rounded-xl flex items-center justify-center group-hover:bg-amber-500/25 transition-all">
                  <Shield size={24} className="text-amber-400"/>
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-white">Administrator</div>
                  <div className="text-sm text-slate-400 mt-0.5">Full access: schedule control, overrides, audit log</div>
                </div>
                <ChevronRight size={16} className="text-slate-600 group-hover:text-slate-400"/>
              </div>
            </button>
          </div>
        ) : (
          <div className="card space-y-5 animate-fade-in">
            <div className="flex items-center gap-3">
              <button onClick={() => setSelectedRole(null)} className="text-slate-500 hover:text-slate-300 transition-colors">
                <ChevronRight size={16} className="rotate-180"/>
              </button>
              <span className={`text-sm font-semibold px-3 py-1 rounded-full ${selectedRole==='admin'?'bg-amber-500/15 text-amber-400':'bg-brand-500/15 text-brand-400'}`}>
                {selectedRole === 'admin' ? '🛡 Administrator' : '👤 Employee'}
              </span>
            </div>
            <div>
              <label className="label">User ID</label>
              <input className="input-field" placeholder={selectedRole==='admin'?'admin or ops':'EMP-001'} value={userId} onChange={e=>setUserId(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handleLogin()}/>
              {selectedRole==='admin' && <p className="text-xs text-slate-500 mt-1.5">Admin IDs: admin / ops | Password: admin123 (set in Override page)</p>}
            </div>
            <button className="btn-primary w-full justify-center" onClick={handleLogin} disabled={!userId.trim()||loading}>
              {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/> : <Zap size={16}/>}
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </div>
        )}

        {/* Campus stats */}
        <div className="mt-8 grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="flex justify-center mb-2"><Sun size={20} className="text-amber-400"/></div>
            <div className="text-sm font-semibold text-white">80 kW</div>
            <div className="text-xs text-slate-500">Solar Peak</div>
          </div>
          <div className="text-center">
            <div className="flex justify-center mb-2"><Battery size={20} className="text-brand-400"/></div>
            <div className="text-sm font-semibold text-white">150 kWh</div>
            <div className="text-xs text-slate-500">Battery</div>
          </div>
          <div className="text-center">
            <div className="flex justify-center mb-2"><Plug size={20} className="text-blue-400"/></div>
            <div className="text-sm font-semibold text-white">4 Chargers</div>
            <div className="text-xs text-slate-500">2 DC + 2 AC</div>
          </div>
        </div>
      </div>
    </div>
  )
}
