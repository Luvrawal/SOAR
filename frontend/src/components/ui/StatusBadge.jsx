import clsx from 'clsx'

const statusClass = {
  pending: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
  running: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
  success: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  open: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
  closed: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  failed: 'bg-red-500/20 text-red-300 border-red-500/40',
}

export function StatusBadge({ status }) {
  const normalized = String(status || 'unknown').toLowerCase()
  return (
    <span
      className={clsx(
        'inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold uppercase tracking-wider',
        statusClass[normalized] || 'bg-slate-700/40 text-slate-300 border-slate-600',
      )}
    >
      {normalized}
    </span>
  )
}
