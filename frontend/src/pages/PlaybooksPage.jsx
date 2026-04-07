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

  useEffect(() => {
    fetchPlaybooks()
  }, [fetchPlaybooks])

  useEffect(() => {
    fetchActiveStats()
  }, [fetchActiveStats])

  usePolling(fetchPlaybooks, undefined, !loading)
  usePolling(fetchActiveStats, undefined, !loading && Boolean(activePlaybookId))

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
              <p className="mt-1 text-sm text-slate-400">Last run: {playbook.last_run ? new Date(playbook.last_run).toLocaleString() : 'Never'}</p>
              <p className="mt-1 text-sm text-slate-400">Success rate: {playbook.success_rate}%</p>

              <div className="mt-4 flex flex-wrap gap-2">
                {(playbook.steps || []).map((step, index) => (
                  <span key={`${playbook.id}-${index}`} className="rounded-md border border-soc-600 bg-soc-900 px-2 py-1 text-xs text-slate-300">
                    {index + 1}. {step}
                  </span>
                ))}
              </div>
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
            </div>
          </div>
        )}
      </Panel>
    </div>
  )
}
