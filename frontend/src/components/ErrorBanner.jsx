import { AlertTriangle, X } from 'lucide-react'
import { useState } from 'react'

export default function ErrorBanner({ message, onDismiss }) {
  return (
    <div className="flex items-start gap-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-4">
      <AlertTriangle size={16} className="shrink-0 mt-0.5"/>
      <span className="text-sm flex-1">{message}</span>
      {onDismiss && <button onClick={onDismiss} className="text-red-400 hover:text-red-300"><X size={14}/></button>}
    </div>
  )
}
