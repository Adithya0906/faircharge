export default function MetricCard({ label, value, unit = '', icon: Icon, color = 'text-brand-400', tooltip }) {
  return (
    <div className="card flex flex-col gap-1 group relative">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">{label}</span>
        {Icon && <Icon size={16} className="text-slate-600"/>}
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}<span className="text-sm font-normal text-slate-500 ml-1">{unit}</span></div>
      {tooltip && <div className="text-xs text-slate-500 mt-1">{tooltip}</div>}
    </div>
  )
}
