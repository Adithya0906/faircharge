export default function StatusBadge({ status }) {
  const map = {
    pending: 'badge-yellow',
    scheduled: 'badge-blue',
    active: 'badge-green',
    completed: 'badge-green',
    failed: 'badge-red',
    partial: 'badge-yellow',
  }
  return <span className={map[status] || 'badge-yellow'}>{status}</span>
}
