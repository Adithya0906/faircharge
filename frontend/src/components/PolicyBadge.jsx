export default function PolicyBadge({ policy }) {
  const map = {
    fcfs: 'bg-slate-700 text-slate-300',
    urgency: 'bg-orange-500/15 text-orange-400',
    fairness: 'bg-purple-500/15 text-purple-400',
  }
  return <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${map[policy] || map.fcfs}`}>{policy?.toUpperCase()}</span>
}
