import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { ErrorState } from '../components/ui/ErrorState'
import { LoadingState } from '../components/ui/LoadingState'
import { Panel } from '../components/ui/Panel'
import { SeverityBadge } from '../components/ui/SeverityBadge'
import { StatusBadge } from '../components/ui/StatusBadge'
import { usePolling } from '../hooks/usePolling'
import { api } from '../lib/api'

export function IncidentDetailPage() {
  const { incidentId } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [detail, setDetail] = useState(null)

  const fetchDetail = useCallback(async () => {
    if (!incidentId) return
    try {
      const response = await api.get(`/incidents/${incidentId}`)
      setDetail(response.data.data)
      setError('')
      setLoading(false)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }, [incidentId])

  useEffect(() => {
    fetchDetail()
  }, [fetchDetail])

  usePolling(fetchDetail, undefined, !loading && !error)

  if (loading) {
    return <LoadingState label="Loading incident investigation context..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchDetail} />
  }

  const incident = detail?.incident || {}
  const execution = detail?.playbook_execution || {}
  const risk = detail?.risk_scoring || {}

  return (
    <div className="space-y-5">
      <Panel
        title={`Incident #${incident.id}`}
        subtitle={incident.title}
        actions={<SeverityBadge severity={incident.severity} />}
      >
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={incident.status} />
          <StatusBadge status={incident.playbook_status} />
          <span className="text-sm text-slate-400">Created {new Date(incident.created_at).toLocaleString()}</span>
        </div>
      </Panel>

      <div className="grid gap-5 xl:grid-cols-2">
        <Panel title="Timeline View" subtitle="Created -> Queued -> Running -> Completed">
          <ol className="space-y-3">
            {(detail.timeline || []).map((step) => (
              <li key={step.step} className="rounded-md border border-soc-700 bg-soc-950/50 p-3">
                <div className="flex items-center justify-between">
                  <p className="font-display text-lg capitalize text-cyan-100">{step.step}</p>
                  <StatusBadge status={step.status} />
                </div>
                <p className="mt-1 text-xs text-slate-500">{step.timestamp ? new Date(step.timestamp).toLocaleString() : 'pending'}</p>
              </li>
            ))}
          </ol>
        </Panel>

        <Panel title="Playbook Execution" subtitle="Runtime status and step logs">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <StatusBadge status={execution.current_status} />
              <span className="text-sm text-slate-400">Duration: {execution.execution_duration_ms ?? 'n/a'} ms</span>
            </div>
            <div className="max-h-72 space-y-2 overflow-auto rounded-md border border-soc-700 bg-black/40 p-3 font-mono text-xs">
              {(execution.logs || []).map((log, index) => (
                <div key={`${log.step}-${index}`} className="border-b border-soc-800 pb-2">
                  <p className="text-cyan-300">[{new Date(log.timestamp).toLocaleTimeString()}] {log.step}</p>
                  <p className="mt-1 text-slate-300">{log.message}</p>
                </div>
              ))}
              {!execution.logs?.length ? <p className="text-slate-500">No execution logs yet.</p> : null}
            </div>
          </div>
        </Panel>

        <Panel title="Threat Intelligence" subtitle="Provider results and degraded mode">
          <div className="space-y-3 text-sm">
            <p className="text-slate-300">Degraded mode: {detail?.threat_intelligence?.degraded ? 'Yes' : 'No'}</p>
            <pre className="max-h-72 overflow-auto rounded-md border border-soc-700 bg-soc-950/60 p-3 text-xs text-slate-300">
              {JSON.stringify(detail?.threat_intelligence?.results || {}, null, 2)}
            </pre>
            {Object.keys(detail?.threat_intelligence?.provider_errors || {}).length ? (
              <pre className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-200">
                {JSON.stringify(detail?.threat_intelligence?.provider_errors || {}, null, 2)}
              </pre>
            ) : null}
          </div>
        </Panel>

        <Panel title="Risk & Automated Actions" subtitle="Scoring and response actions">
          <div className="mb-4">
            <p className="font-display text-3xl text-cyan-100">{risk.score ?? 0}/100</p>
            <p className="text-sm uppercase tracking-wider text-slate-400">{risk.label || 'low'} risk</p>
          </div>
          <ul className="space-y-2">
            {(detail?.automated_actions || []).map((action, index) => (
              <li key={`${action.action}-${index}`} className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-200">
                {action.action}
              </li>
            ))}
            {!detail?.automated_actions?.length ? (
              <li className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-400">
                No automated actions recorded.
              </li>
            ) : null}
          </ul>
        </Panel>
      </div>
    </div>
  )
}
