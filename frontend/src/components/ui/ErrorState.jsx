export function ErrorState({ message, onRetry }) {
  return (
    <div className="panel border-red-500/40 bg-red-500/10 p-5">
      <h3 className="font-display text-lg text-red-300">Request failed</h3>
      <p className="mt-2 text-sm text-red-200/80">{message || 'Unable to fetch data.'}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-md border border-red-400/50 px-3 py-2 text-sm font-semibold text-red-200 hover:bg-red-500/20"
        >
          Retry
        </button>
      ) : null}
    </div>
  )
}
