import { useMemo, useState } from 'react'
import { Panel } from '../components/ui/Panel'

export function SettingsPage() {
  const [pollingMs, setPollingMs] = useState(() => {
    const stored = window.localStorage.getItem('soc.pollingMs')
    return stored ? Number(stored) : 2500
  })

  const effectiveApiBaseUrl = useMemo(
    () => import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
    [],
  )

  const savePollingInterval = () => {
    const safeValue = Math.min(15000, Math.max(1000, Number(pollingMs || 2500)))
    setPollingMs(safeValue)
    window.localStorage.setItem('soc.pollingMs', String(safeValue))
  }

  return (
    <div className="space-y-5">
      <Panel title="Settings" subtitle="Environment and operational preferences">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
            API Base URL: <span className="text-cyan-200">{effectiveApiBaseUrl}</span>
          </div>
          <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
            Polling interval: <span className="text-cyan-200">{pollingMs} ms</span>
          </div>
        </div>

        <div className="mt-4 rounded-md border border-soc-700 bg-soc-950/50 p-3">
          <label className="block text-xs uppercase tracking-wider text-slate-400" htmlFor="polling-interval">
            Polling Interval (milliseconds)
          </label>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <input
              id="polling-interval"
              type="number"
              min={1000}
              max={15000}
              step={500}
              value={pollingMs}
              onChange={(event) => setPollingMs(Number(event.target.value || 2500))}
              className="w-40 rounded-md border border-soc-700 bg-soc-950 px-3 py-2 text-sm text-slate-100"
            />
            <button
              type="button"
              onClick={savePollingInterval}
              className="rounded-md border border-cyan-500/60 bg-cyan-500/20 px-3 py-2 text-sm font-semibold text-cyan-100 hover:bg-cyan-500/30"
            >
              Save
            </button>
          </div>
          <p className="mt-2 text-xs text-slate-500">Range: 1000 to 15000 ms. Stored in localStorage as soc.pollingMs.</p>
        </div>

      </Panel>
    </div>
  )
}
