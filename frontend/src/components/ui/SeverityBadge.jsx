import clsx from 'clsx'

const severityClass = {
  low: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
  medium: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
  high: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
  critical: 'bg-red-500/20 text-red-300 border-red-500/40',
}

export function SeverityBadge({ severity }) {
  const normalized = String(severity || 'unknown').toLowerCase()
  return (
    <span
      className={clsx(
        'inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold uppercase tracking-wider',
        severityClass[normalized] || 'bg-slate-700/40 text-slate-300 border-slate-600',
      )}
    >
      {normalized}
    </span>
  )
}
