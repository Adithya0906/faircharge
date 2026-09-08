import React, { useState, createContext, useContext } from 'react'
import { BrowserRouter, Routes, Route, Navigate, NavLink, Outlet } from 'react-router-dom'
import { Zap, LayoutDashboard, Calendar, Battery, Settings, ClipboardList, FlaskConical, LogOut, X, ChevronRight, Activity, Users } from 'lucide-react'

import LoginPage from './pages/LoginPage.jsx'
import RequestPage from './pages/RequestPage.jsx'
import MySchedulePage from './pages/MySchedulePage.jsx'
import OperationsDashboard from './pages/OperationsDashboard.jsx'
import TimelinePage from './pages/TimelinePage.jsx'
import FairnessDashboard from './pages/FairnessDashboard.jsx'
import EnergyDashboard from './pages/EnergyDashboard.jsx'
import AdminPanel from './pages/AdminPanel.jsx'
import AuditLog from './pages/AuditLog.jsx'
import ExperimentsPage from './pages/ExperimentsPage.jsx'

export const AuthContext = createContext(null)
export function useAuth() { return useContext(AuthContext) }

const NAV = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', roles: ['user','admin'] },
  { path: '/request', icon: Zap, label: 'Request Charging', roles: ['user','admin'] },
  { path: '/my-schedule', icon: Calendar, label: 'My Schedule', roles: ['user','admin'] },
  { path: '/timeline', icon: Activity, label: 'Timeline', roles: ['user','admin'] },
  { path: '/fairness', icon: Users, label: 'Fairness', roles: ['user','admin'] },
  { path: '/energy', icon: Battery, label: 'Energy', roles: ['user','admin'] },
  { path: '/experiments', icon: FlaskConical, label: 'Experiments', roles: ['user','admin'] },
  { path: '/admin', icon: Settings, label: 'Admin Control', roles: ['admin'] },
  { path: '/audit', icon: ClipboardList, label: 'Audit Log', roles: ['admin'] },
]

function Sidebar({ role, onLogout, collapsed, setCollapsed }) {
  return (
    <aside className={`${collapsed ? 'w-16' : 'w-60'} bg-slate-900 border-r border-slate-800 flex flex-col transition-all duration-300 shrink-0 min-h-screen`}>
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-800">
        <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center shrink-0 shadow-lg shadow-brand-500/30"><Zap size={16} className="text-white" /></div>
        {!collapsed && <div><div className="font-bold text-white text-sm">FairCharge</div><div className="text-xs text-slate-500">EV Scheduler</div></div>}
        <button onClick={() => setCollapsed(!collapsed)} className="ml-auto text-slate-500 hover:text-slate-300">{collapsed ? <ChevronRight size={14}/> : <X size={14}/>}</button>
      </div>
      {!collapsed && <div className="px-4 py-3"><span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${role==='admin'?'bg-amber-500/10 text-amber-400 border-amber-500/20':'bg-brand-500/10 text-brand-400 border-brand-500/20'}`}>{role==='admin'?'🛡 Administrator':'👤 Employee'}</span></div>}
      <nav className="flex-1 px-2 py-2 space-y-0.5 overflow-y-auto">
        {NAV.filter(i=>i.roles.includes(role)).map(item=>(
          <NavLink key={item.path} to={item.path} className={({isActive})=>`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all ${isActive?'bg-brand-500/15 text-brand-400':'text-slate-400 hover:text-slate-200 hover:bg-slate-800'}`}>
            <item.icon size={15} className="shrink-0"/>{!collapsed&&<span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 border-t border-slate-800">
        <button onClick={onLogout} className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all w-full"><LogOut size={15}/>{!collapsed&&'Sign out'}</button>
      </div>
    </aside>
  )
}

function AppLayout() {
  const { role, logout } = useAuth()
  const [collapsed, setCollapsed] = useState(false)
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar role={role} onLogout={logout} collapsed={collapsed} setCollapsed={setCollapsed}/>
      <main className="flex-1 overflow-y-auto"><div className="p-6 animate-fade-in"><Outlet/></div></main>
    </div>
  )
}

export default function App() {
  const [auth, setAuth] = useState(null)
  const login = (role, userId) => setAuth({role, userId})
  const logout = () => setAuth(null)
  return (
    <AuthContext.Provider value={{role:auth?.role, userId:auth?.userId, login, logout}}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={!auth?<LoginPage/>:<Navigate to="/dashboard" replace/>}/>
          {auth ? (
            <Route element={<AppLayout/>}>
              <Route path="/dashboard" element={<OperationsDashboard/>}/>
              <Route path="/request" element={<RequestPage/>}/>
              <Route path="/my-schedule" element={<MySchedulePage/>}/>
              <Route path="/timeline" element={<TimelinePage/>}/>
              <Route path="/fairness" element={<FairnessDashboard/>}/>
              <Route path="/energy" element={<EnergyDashboard/>}/>
              <Route path="/experiments" element={<ExperimentsPage/>}/>
              <Route path="/admin" element={auth.role==='admin'?<AdminPanel/>:<Navigate to="/dashboard"/>}/>
              <Route path="/audit" element={auth.role==='admin'?<AuditLog/>:<Navigate to="/dashboard"/>}/>
              <Route path="*" element={<Navigate to="/dashboard" replace/>}/>
            </Route>
          ) : (
            <Route path="*" element={<Navigate to="/login" replace/>}/>
          )}
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  )
}
