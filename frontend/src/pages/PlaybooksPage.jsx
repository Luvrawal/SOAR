import { useCallback, useEffect, useMemo, useState } from 'react'
import { ErrorState } from '../components/ui/ErrorState'
import { LoadingState } from '../components/ui/LoadingState'
import { Panel } from '../components/ui/Panel'
import { StatusBadge } from '../components/ui/StatusBadge'
import { usePolling } from '../hooks/usePolling'
import { api } from '../lib/api'

export function PlaybooksPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [playbooks, setPlaybooks] = useState([])
  const [activePlaybookId, setActivePlaybookId] = useState('')
  const [activeStats, setActiveStats] = useState(null)
  const [activeExecutions, setActiveExecutions] = useState(null)
  const [historyStatusFilter, setHistoryStatusFilter] = useState('all')
  const [historyWindow, setHistoryWindow] = useState('all')
  const [historyPage, setHistoryPage] = useState(1)
  const [historyPageSize, setHistoryPageSize] = useState(10)

  const fetchPlaybooks = useCallback(async () => {
    try {
      const response = await api.get('/playbooks')
      const items = response.data.data.items || []
      setPlaybooks(items)
      if (!activePlaybookId && items.length > 0) {
        setActivePlaybookId(items[0].id)
      }
      setError('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [activePlaybookId])

  const fetchActiveStats = useCallback(async () => {
    if (!activePlaybookId) {
      return
    }
    try {
      const response = await api.get(`/playbooks/${activePlaybookId}/stats`)
      setActiveStats(response.data.data)
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }, [activePlaybookId])

  const fetchActiveExecutions = useCallback(async () => {
    if (!activePlaybookId) {
      return
    }
    try {
      const sinceHours = historyWindow === '24h' ? 24 : historyWindow === '7d' ? 7 * 24 : undefined
      const response = await api.get(`/playbooks/${activePlaybookId}/executions`, {
        params: {
          ...(historyStatusFilter !== 'all' ? { status: historyStatusFilter } : {}),
          ...(sinceHours ? { since_hours: sinceHours } : {}),
          page: historyPage,
          page_size: historyPageSize,
        },
      })
      setActiveExecutions(response.data.data)
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }, [activePlaybookId, historyStatusFilter, historyWindow, historyPage, historyPageSize])

  useEffect(() => {
    fetchPlaybooks()
  }, [fetchPlaybooks])

  useEffect(() => {
    fetchActiveStats()
  }, [fetchActiveStats])

  useEffect(() => {
    fetchActiveExecutions()
  }, [fetchActiveExecutions])

  usePolling(fetchPlaybooks, undefined, !loading)
  usePolling(fetchActiveStats, undefined, !loading && Boolean(activePlaybookId))
  usePolling(fetchActiveExecutions, undefined, !loading && Boolean(activePlaybookId))

  const stepComparison = useMemo(() => {
    const failed = activeExecutions?.latest_failed
    const success = activeExecutions?.latest_success
    const failedSteps = failed?.execution_steps || []
    const successSteps = success?.execution_steps || []

    const ids = Array.from(new Set([...failedSteps.map((step) => step.id), ...successSteps.map((step) => step.id)]))
    return ids.map((id) => {
      const failedStep = failedSteps.find((step) => step.id === id)
      const successStep = successSteps.find((step) => step.id === id)
      return {
        id,
        name: failedStep?.name || successStep?.name || id,
        failedStatus: failedStep?.status || 'n/a',
        successStatus: successStep?.status || 'n/a',
      }
    })
  }, [activeExecutions])

  const historyRows = useMemo(() => {
    const items = activeExecutions?.items || []

    return items.map((item, index) => {
      const nextOlder = items[index + 1]
      const currentSteps = item.execution_steps || []
      const olderMap = new Map((nextOlder?.execution_steps || []).map((step) => [step.id, step.status]))

      let changedSteps = 0
      for (const step of currentSteps) {
        const olderStatus = olderMap.get(step.id)
        if (olderStatus && olderStatus !== step.status) {
          changedSteps += 1
        }
      }

      return {
        ...item,
        changedSteps,
      }
    })
  }, [activeExecutions])

  const totalHistory = activeExecutions?.total_all || 0
  const totalHistoryPages = Math.max(1, Math.ceil(totalHistory / historyPageSize))

  const totals = useMemo(() => {
    const totalRuns = playbooks.reduce((sum, item) => sum + (item.total_runs || 0), 0)
    const totalFailed = playbooks.reduce((sum, item) => sum + (item.failed_count || 0), 0)
    const avgSuccess = playbooks.length
      ? (playbooks.reduce((sum, item) => sum + (item.success_rate || 0), 0) / playbooks.length).toFixed(2)
      : '0.00'
    return { totalRuns, totalFailed, avgSuccess }
  }, [playbooks])

  const statusFromPlaybook = (playbook) => {
    if (!playbook.total_runs) {
      return 'pending'
    }
    return playbook.failed_count > 0 ? 'failed' : 'success'
  }

  if (loading) {
    return <LoadingState label="Loading playbook inventory..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchPlaybooks} />
  }

  return (
    <div className="space-y-5">
      <section className="grid gap-3 md:grid-cols-3">
        <div className="rounded-lg border border-soc-700 bg-soc-950/50 p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Total Runs</p>
          <p className="mt-2 font-display text-3xl text-cyan-100">{totals.totalRuns}</p>
        </div>
        <div className="rounded-lg border border-soc-700 bg-soc-950/50 p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Failed Executions</p>
          <p className="mt-2 font-display text-3xl text-red-300">{totals.totalFailed}</p>
        </div>
        <div className="rounded-lg border border-soc-700 bg-soc-950/50 p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Avg Success Rate</p>
          <p className="mt-2 font-display text-3xl text-emerald-300">{totals.avgSuccess}%</p>
        </div>
      </section>

      <Panel title="Playbooks" subtitle="Execution readiness and flow map">
        <div className="grid gap-4 lg:grid-cols-3">
          {playbooks.map((playbook) => (
            <article
              key={playbook.id}
              className="cursor-pointer rounded-lg border border-soc-700 bg-soc-950/50 p-4 transition hover:border-cyan-500/50"
              onClick={() => setActivePlaybookId(playbook.id)}
            >
              <div className="flex items-center justify-between gap-2">
                <h3 className="font-display text-lg text-cyan-100">{playbook.name}</h3>
                <StatusBadge status={statusFromPlaybook(playbook)} />
              </div>
              <p className="mt-1 text-sm text-slate-400">Type: {playbook.type}</p>
              <p className="mt-1 text-sm text-slate-400">Version: {playbook.version || 'n/a'} · Owner: {playbook.owner || 'n/a'}</p>
              <p className="mt-1 text-sm text-slate-400">Last run: {playbook.last_run ? new Date(playbook.last_run).toLocaleString() : 'Never'}</p>
              <p className="mt-1 text-sm text-slate-400">Success rate: {playbook.success_rate}%</p>

              <div className="mt-4 flex flex-wrap gap-2">
                {(playbook.steps || []).map((step, index) => (
                  <span key={`${playbook.id}-${index}`} className="rounded-md border border-soc-600 bg-soc-900 px-2 py-1 text-xs text-slate-300">
                    {index + 1}. {step}
                  </span>
                ))}
              </div>

              {(playbook.latest_execution_steps || []).length ? (
                <div className="mt-4 space-y-1">
                  <p className="text-xs uppercase tracking-wider text-slate-500">Latest Execution Step State</p>
                  {(playbook.latest_execution_steps || []).map((step) => (
                    <div key={`${playbook.id}-${step.id}`} className="flex items-center justify-between rounded-md border border-soc-700 bg-soc-900/60 px-2 py-1 text-xs">
                      <span className="text-slate-300">{step.name}</span>
                      <StatusBadge status={step.status} />
                    </div>
                  ))}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Selected Playbook Details" subtitle="Drilldown stats for SOC review">
        {!activeStats ? (
          <p className="text-sm text-slate-400">Select a playbook to view detailed metrics.</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
              <p className="font-semibold text-cyan-100">{activeStats.name}</p>
              <p className="mt-1">MITRE: {activeStats.mitre_technique}</p>
              <p className="mt-1">Version: {activeStats.version || 'n/a'}</p>
              <p className="mt-1">Owner: {activeStats.owner || 'n/a'}</p>
              <p className="mt-1">Active: {activeStats.is_active ? 'yes' : 'no'}</p>
              <p className="mt-1">Total runs: {activeStats.total_runs}</p>
              <p className="mt-1">Success: {activeStats.success_count}</p>
              <p className="mt-1">Failed: {activeStats.failed_count}</p>
            </div>
            <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
              <p>Average execution: {activeStats.avg_execution_ms ?? 'n/a'} ms</p>
              <p className="mt-1">Last run: {activeStats.last_run ? new Date(activeStats.last_run).toLocaleString() : 'Never'}</p>
              <p className="mt-1">Success rate: {activeStats.success_rate}%</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {(activeStats.steps || []).map((step, index) => (
                  <span key={`${activeStats.id}-${index}`} className="rounded-md border border-soc-600 bg-soc-900 px-2 py-1 text-xs text-slate-300">
                    {index + 1}. {step}
                  </span>
                ))}
              </div>
              {(activeStats.latest_execution_steps || []).length ? (
                <div className="mt-3 space-y-2">
                  {(activeStats.latest_execution_steps || []).map((step) => (
                    <div key={`${activeStats.id}-latest-${step.id}`} className="flex items-center justify-between rounded-md border border-soc-700 bg-soc-900/60 px-2 py-1 text-xs">
                      <span className="text-slate-300">{step.name}</span>
                      <StatusBadge status={step.status} />
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        )}
      </Panel>

      <Panel title="Execution Comparison" subtitle="Latest failed run vs latest successful run">
        {!activeExecutions?.latest_failed || !activeExecutions?.latest_success ? (
          <p className="text-sm text-slate-400">Comparison becomes available after at least one failed run and one successful run.</p>
        ) : (
          <div className="space-y-3">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-100">
                <p className="font-semibold">Latest failed execution #{activeExecutions.latest_failed.id}</p>
                <p className="mt-1">Duration: {activeExecutions.latest_failed.execution_duration_ms ?? 'n/a'} ms</p>
              </div>
              <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-100">
                <p className="font-semibold">Latest successful execution #{activeExecutions.latest_success.id}</p>
                <p className="mt-1">Duration: {activeExecutions.latest_success.execution_duration_ms ?? 'n/a'} ms</p>
              </div>
            </div>
            <div className="space-y-2">
              {stepComparison.map((step) => (
                <div key={`${activePlaybookId}-${step.id}`} className="grid items-center gap-2 rounded-md border border-soc-700 bg-soc-950/50 px-3 py-2 text-xs md:grid-cols-3">
                  <p className="font-semibold text-cyan-100">{step.name}</p>
                  <div className="flex items-center justify-between gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-2 py-1">
                    <span className="text-red-200">Failed</span>
                    <StatusBadge status={step.failedStatus} />
                  </div>
                  <div className="flex items-center justify-between gap-2 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-1">
                    <span className="text-emerald-200">Success</span>
                    <StatusBadge status={step.successStatus} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Panel>

      <Panel title="Execution History Timeline" subtitle="Run chronology with step-state drift indicators">
        <div className="mb-3 grid gap-2 md:grid-cols-2">
          <select
            value={historyStatusFilter}
            onChange={(event) => {
              setHistoryStatusFilter(event.target.value)
              setHistoryPage(1)
            }}
            className="rounded-md border border-soc-700 bg-soc-950 px-3 py-2 text-sm text-slate-100"
          >
            <option value="all">All statuses</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="running">Running</option>
          </select>

          <select
            value={historyWindow}
            onChange={(event) => {
              setHistoryWindow(event.target.value)
              setHistoryPage(1)
            }}
            className="rounded-md border border-soc-700 bg-soc-950 px-3 py-2 text-sm text-slate-100"
          >
            <option value="all">All time</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
          </select>
        </div>

        <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
          <span>
            Showing page {historyPage} of {totalHistoryPages} ({totalHistory} total runs)
          </span>
          <div className="flex items-center gap-2">
            <select
              value={historyPageSize}
              onChange={(event) => {
                setHistoryPageSize(Number(event.target.value))
                setHistoryPage(1)
              }}
              className="rounded-md border border-soc-700 bg-soc-950 px-2 py-1 text-xs text-slate-100"
            >
              <option value={10}>10 / page</option>
              <option value={20}>20 / page</option>
              <option value={50}>50 / page</option>
            </select>
            <button
              type="button"
              disabled={historyPage <= 1}
              onClick={() => setHistoryPage((prev) => Math.max(1, prev - 1))}
              className="rounded-md border border-soc-700 bg-soc-900 px-2 py-1 text-xs text-slate-200 disabled:opacity-40"
            >
              Prev
            </button>
            <button
              type="button"
              disabled={historyPage >= totalHistoryPages}
              onClick={() => setHistoryPage((prev) => Math.min(totalHistoryPages, prev + 1))}
              className="rounded-md border border-soc-700 bg-soc-900 px-2 py-1 text-xs text-slate-200 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-xs">
            <thead>
              <tr className="border-b border-soc-700 text-slate-400">
                <th className="px-2 py-2">Execution</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Started</th>
                <th className="px-2 py-2">Duration</th>
                <th className="px-2 py-2">Step Changes</th>
              </tr>
            </thead>
            <tbody>
              {historyRows.map((row) => (
                <tr key={`${activePlaybookId}-history-${row.id}`} className="border-b border-soc-800">
                  <td className="px-2 py-2 font-semibold text-cyan-100">#{row.id}</td>
                  <td className="px-2 py-2"><StatusBadge status={row.status} /></td>
                  <td className="px-2 py-2 text-slate-300">{row.started_at ? new Date(row.started_at).toLocaleString() : 'n/a'}</td>
                  <td className="px-2 py-2 text-slate-300">{row.execution_duration_ms ?? 'n/a'} ms</td>
                  <td className="px-2 py-2">
                    <span className={row.changedSteps > 0 ? 'font-semibold text-amber-300' : 'text-slate-400'}>
                      {row.changedSteps}
                    </span>
                  </td>
                </tr>
              ))}
              {!historyRows.length ? (
                <tr>
                  <td colSpan={5} className="px-2 py-4 text-center text-slate-500">No executions match current filters.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}
