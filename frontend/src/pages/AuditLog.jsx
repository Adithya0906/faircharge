import React, { useState, useEffect } from 'react'
import { ClipboardList, RefreshCw } from 'lucide-react'
import { getAuditLog } from '../services/api.js'
import LoadingSpinner from '../components/LoadingSpinner.jsx'

export default function AuditLog() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const res = await getAuditLog(100)
      setLogs(res.data)
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchLogs() }, [])

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2"><ClipboardList className="text-brand-400"/> Admin Audit Log</h1>
          <p className="text-slate-400 mt-1">Immutable record of all administrative actions and system overrides.</p>
        </div>
        <button className="btn-secondary" onClick={fetchLogs}><RefreshCw size={15}/> Refresh</button>
      </div>

      <div className="card overflow-x-auto">
        {loading ? <div className="flex justify-center p-8"><LoadingSpinner /></div> : (
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase font-semibold">
              <tr>
                <th className="px-4 py-3 rounded-tl-lg">Timestamp</th>
                <th className="px-4 py-3">Admin ID</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Details</th>
                <th className="px-4 py-3 rounded-tr-lg">IP Address</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {logs.length > 0 ? logs.map(log => (
                <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 whitespace-nowrap text-slate-400">{new Date(log.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-3 font-medium text-white">{log.admin_id}</td>
                  <td className="px-4 py-3">
                    <span className="bg-amber-500/15 text-amber-400 text-xs font-semibold px-2 py-1 rounded-full">{log.action_type}</span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs max-w-md truncate" title={JSON.stringify(log.details)}>{JSON.stringify(log.details)}</td>
                  <td className="px-4 py-3 text-slate-500">{log.ip_address}</td>
                </tr>
              )) : (
                <tr><td colSpan="5" className="px-4 py-8 text-center text-slate-500">No audit logs found.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
