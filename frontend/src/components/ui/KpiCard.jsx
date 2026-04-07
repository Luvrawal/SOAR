export function KpiCard({ label, value, tone = 'neutral' }) {
  const toneClass = {
    neutral: 'text-cyan-100',
    success: 'text-emerald-300',
    warning: 'text-yellow-300',
    danger: 'text-red-300',
  }

  return (
    <article className="panel p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{label}</p>
      <p className={`metric-value mt-2 ${toneClass[tone] || toneClass.neutral}`}>{value}</p>
    </article>
  )
}
