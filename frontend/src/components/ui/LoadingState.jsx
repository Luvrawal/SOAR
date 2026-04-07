export function LoadingState({ label = 'Loading data...' }) {
  return (
    <div className="panel p-6 text-sm text-slate-300">
      <div className="mb-3 h-2 w-28 animate-pulse rounded bg-slate-700" />
      <div className="h-2 w-44 animate-pulse rounded bg-slate-700" />
      <p className="mt-4 text-slate-400">{label}</p>
    </div>
  )
}
