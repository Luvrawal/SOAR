import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { KpiCard } from '../components/ui/KpiCard'
import { ErrorState } from '../components/ui/ErrorState'
import { LoadingState } from '../components/ui/LoadingState'
import { Panel } from '../components/ui/Panel'
import { SeverityBadge } from '../components/ui/SeverityBadge'
import { StatusBadge } from '../components/ui/StatusBadge'
import { usePolling } from '../hooks/usePolling'
import { api, getLastCorrelationId } from '../lib/api'

function groupByDate(items) {
  const counts = new Map()
  items.forEach((item) => {
    const date = new Date(item.created_at).toISOString().slice(0, 10)
    counts.set(date, (counts.get(date) || 0) + 1)
  })

  return [...counts.entries()].map(([date, incidents]) => ({ date, incidents }))
}

function groupByType(items) {
  const counts = new Map()
  items.forEach((item) => {
    const type = item.title || 'Unknown'
    counts.set(type, (counts.get(type) || 0) + 1)
  })

  return [...counts.entries()].map(([name, value]) => ({ name, value }))
}

function buildQueueFallback(summaryData, incidents) {
  const breakdown = summaryData?.playbook_status_breakdown || {}
  const pendingFromBreakdown = Number(breakdown.pending || 0)
  const runningFromBreakdown = Number(breakdown.running || 0)

  const pendingFromIncidents = incidents.filter((item) => item.playbook_status === 'pending').length
  const runningFromIncidents = incidents.filter((item) => item.playbook_status === 'running').length

  const pending = pendingFromBreakdown || pendingFromIncidents
  const running = runningFromBreakdown || runningFromIncidents
  const backlog = pending + running
  const capacity = 200
  const utilization = capacity > 0 ? Number(((backlog / capacity) * 100).toFixed(2)) : 0

  let pressure = 'low'
  if (utilization >= 90) {
    pressure = 'critical'
  } else if (utilization >= 70) {
    pressure = 'high'
  } else if (utilization >= 40) {
    pressure = 'medium'
  }

  return {
    pending,
    running,
    backlog,
    capacity,
    utilization_pct: utilization,
    pressure,
    per_queue: {},
  }
}

export function DashboardPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [summary, setSummary] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [queueMetrics, setQueueMetrics] = useState(null)
  const [observability, setObservability] = useState(null)
  const [lastCorrelationId, setLastCorrelationId] = useState('')
  const [opsNotice, setOpsNotice] = useState('')
  const [endpointStatus, setEndpointStatus] = useState({
    summary: 'pending',
    queueMetrics: 'pending',
    observability: 'pending',
  })
  const [runningSimulation, setRunningSimulation] = useState('')
  const [lastRefreshedAt, setLastRefreshedAt] = useState(null)

  const fetchDashboardData = useCallback(async () => {
    setError('')
    try {
      const [summaryRes, incidentsRes, observabilityRes, queueMetricsRes] = await Promise.allSettled([
        api.get('/simulations/summary', { params: { limit: 50 } }),
        api.get('/incidents', { params: { page: 1, page_size: 50 } }),
        api.get('/observability/metrics'),
        api.get('/simulations/queue-metrics', { params: { window_hours: 24 } }),
      ])

      if (summaryRes.status !== 'fulfilled') {
        throw summaryRes.reason
      }
      if (incidentsRes.status !== 'fulfilled') {
        throw incidentsRes.reason
      }

      const summaryData = summaryRes.value.data.data
      setSummary(summaryData)
      const incidentItems = incidentsRes.value.data.data.items || []
      setIncidents(incidentItems)

      setEndpointStatus({
        summary: summaryRes.status,
        queueMetrics: queueMetricsRes.status,
        observability: observabilityRes.status,
      })

      const notices = []

      let resolvedQueueMetrics = summaryData?.queue || null
      if (!resolvedQueueMetrics && queueMetricsRes.status === 'fulfilled') {
        resolvedQueueMetrics = queueMetricsRes.value?.data?.data?.queue || null
      }

      if (!resolvedQueueMetrics) {
        resolvedQueueMetrics = buildQueueFallback(summaryData, incidentItems)
        notices.push('Queue metrics fallback is derived from summary and incident status data.')
      }

      if (!resolvedQueueMetrics) {
        notices.push('Queue metrics are temporarily unavailable.')
      }

      setQueueMetrics(resolvedQueueMetrics)

      if (observabilityRes.status === 'fulfilled') {
        setObservability(observabilityRes.value.data?.data?.metrics || null)
      } else {
        setObservability(null)
        const reason = String(observabilityRes.reason?.message || '')
        if (reason.includes('403') || reason.toLowerCase().includes('permission')) {
          notices.push('Detailed platform observability metrics are available to admin role.')
        } else {
          notices.push('Observability metrics are temporarily unavailable.')
        }
      }

      setOpsNotice(notices.join(' '))

      setLastCorrelationId(getLastCorrelationId() || '')

      setLastRefreshedAt(new Date().toISOString())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDashboardData()
  }, [fetchDashboardData])

  usePolling(fetchDashboardData, undefined, !loading && !runningSimulation)

  const runQuickSimulation = async (simulationType, count = 12) => {
    setRunningSimulation(simulationType)
    setError('')
    try {
      const response = await api.post(`/simulations/${simulationType}`, null, { params: { count } })
      const latestIncidentId = response.data?.data?.latest_incident_id
      await fetchDashboardData()
      if (latestIncidentId) {
        navigate(`/incidents/${latestIncidentId}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setRunningSimulation('')
    }
  }

  const openIncidents = useMemo(
    () => incidents.filter((item) => item.status === 'open').length,
    [incidents],
  )
  const runningPlaybooks = useMemo(
    () => incidents.filter((item) => item.playbook_status === 'running').length,
    [incidents],
  )
  const failedIncidents = useMemo(
    () => incidents.filter((item) => item.playbook_status === 'failed' || item.status === 'failed').length,
    [incidents],
  )

  const overTime = useMemo(() => groupByDate(incidents), [incidents])
  const byType = useMemo(() => groupByType(incidents), [incidents])

  if (loading) {
    return <LoadingState label="Building SOC dashboard telemetry..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchDashboardData} />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold text-cyan-100">Security Operations Dashboard</h1>
        <p className="mt-1 text-sm text-slate-400">Real-time incident and playbook monitoring console</p>
        <p className="mt-1 text-xs text-slate-500">Last refreshed: {lastRefreshedAt ? new Date(lastRefreshedAt).toLocaleTimeString() : 'n/a'}</p>
      </div>

      <Panel title="Rapid Response Actions" subtitle="Trigger high-value simulations and jump directly to generated incidents">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={Boolean(runningSimulation)}
            onClick={() => runQuickSimulation('phishing')}
            className="rounded-md border border-soc-700 bg-soc-950 px-3 py-2 text-sm text-slate-200 hover:border-cyan-500/50 disabled:opacity-50"
          >
            {runningSimulation === 'phishing' ? 'Running phishing...' : 'Run Phishing'}
          </button>
          <button
            type="button"
            disabled={Boolean(runningSimulation)}
            onClick={() => runQuickSimulation('malware')}
            className="rounded-md border border-soc-700 bg-soc-950 px-3 py-2 text-sm text-slate-200 hover:border-cyan-500/50 disabled:opacity-50"
          >
            {runningSimulation === 'malware' ? 'Running malware...' : 'Run Malware'}
          </button>
          <button
            type="button"
            disabled={Boolean(runningSimulation)}
            onClick={() => runQuickSimulation('all', 8)}
            className="rounded-md border border-cyan-500/50 bg-cyan-500/10 px-3 py-2 text-sm font-semibold text-cyan-100 hover:bg-cyan-500/20 disabled:opacity-50"
          >
            {runningSimulation === 'all' ? 'Running all scenarios...' : 'Run All Scenarios'}
          </button>
        </div>
      </Panel>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Total Incidents" value={summary?.total_incidents || incidents.length} tone="neutral" />
        <KpiCard label="Open Incidents" value={openIncidents} tone="warning" />
        <KpiCard label="Running Playbooks" value={runningPlaybooks} tone="warning" />
        <KpiCard label="Failed Incidents" value={failedIncidents} tone="danger" />
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <Panel title="Incidents Over Time" subtitle="Created incidents by day">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={overTime}>
                <defs>
                  <linearGradient id="incidentGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1ecad3" stopOpacity={0.7} />
                    <stop offset="95%" stopColor="#1ecad3" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#24344f" />
                <XAxis dataKey="date" stroke="#7f8ea8" />
                <YAxis stroke="#7f8ea8" />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#24344f' }} />
                <Area dataKey="incidents" stroke="#1ecad3" fill="url(#incidentGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Incident Type Distribution" subtitle="Volume by incident category">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={byType}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={50}
                  outerRadius={95}
                  fill="#1ecad3"
                  stroke="#0b1220"
                />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#24344f' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Recent Incidents" subtitle="Latest SOC activity">
          <div className="space-y-2">
            {incidents.slice(0, 6).map((incident) => (
              <button
                key={incident.id}
                type="button"
                onClick={() => navigate(`/incidents/${incident.id}`)}
                className="w-full rounded-md border border-soc-700/70 bg-soc-950/50 p-3 text-left transition hover:border-cyan-500/50"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium text-slate-100">#{incident.id} {incident.title}</p>
                  <SeverityBadge severity={incident.severity} />
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <StatusBadge status={incident.playbook_status} />
                  <span className="text-xs text-slate-500">{new Date(incident.created_at).toLocaleString()}</span>
                </div>
              </button>
            ))}
          </div>
        </Panel>
      </section>

      <Panel title="Platform Operations" subtitle="Queue pressure and API runtime telemetry">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
            <p className="text-xs uppercase tracking-wider text-slate-500">Queue Backlog</p>
            <p className="mt-1 font-display text-2xl text-cyan-100">{queueMetrics?.backlog ?? 'n/a'}</p>
            <p className="text-xs text-slate-400">Capacity: {queueMetrics?.capacity ?? 'n/a'}</p>
          </div>
          <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
            <p className="text-xs uppercase tracking-wider text-slate-500">Queue Pressure</p>
            <p className="mt-1 font-display text-2xl text-cyan-100">{queueMetrics?.pressure || 'n/a'}</p>
            <p className="text-xs text-slate-400">Utilization: {queueMetrics?.utilization_pct ?? 'n/a'}%</p>
          </div>
          <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
            <p className="text-xs uppercase tracking-wider text-slate-500">API Error Rate</p>
            <p className="mt-1 font-display text-2xl text-cyan-100">{observability?.error_rate_pct ?? 'n/a'}%</p>
            <p className="text-xs text-slate-400">Avg latency: {observability?.avg_latency_ms ?? 'n/a'} ms</p>
          </div>
        </div>

        {opsNotice ? <p className="mt-3 text-xs text-slate-500">{opsNotice}</p> : null}

        <p className="mt-2 text-xs text-slate-500">
          Endpoint status: summary={endpointStatus.summary}, queue-metrics={endpointStatus.queueMetrics}, observability={endpointStatus.observability}
        </p>

        <p className="mt-2 text-xs text-slate-500">
          Last correlation ID: {lastCorrelationId || 'n/a'}
        </p>

        {queueMetrics?.per_queue ? (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead>
                <tr className="border-b border-soc-700 text-slate-400">
                  <th className="px-2 py-2">Queue</th>
                  <th className="px-2 py-2">Total</th>
                  <th className="px-2 py-2">Failed</th>
                  <th className="px-2 py-2">Throughput/hr</th>
                  <th className="px-2 py-2">Failure Rate</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(queueMetrics.per_queue).map(([queueName, queueData]) => (
                  <tr key={`queue-${queueName}`} className="border-b border-soc-800">
                    <td className="px-2 py-2 text-slate-200">{queueName}</td>
                    <td className="px-2 py-2 text-slate-300">{queueData.total}</td>
                    <td className="px-2 py-2 text-slate-300">{queueData.failed}</td>
                    <td className="px-2 py-2 text-slate-300">{queueData.throughput_per_hour}</td>
                    <td className="px-2 py-2 text-slate-300">{queueData.failure_rate_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {observability?.recent_events?.length ? (
          <div className="mt-4 overflow-x-auto">
            <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">Recent API Events</p>
            <table className="min-w-full text-left text-xs">
              <thead>
                <tr className="border-b border-soc-700 text-slate-400">
                  <th className="px-2 py-2">Time</th>
                  <th className="px-2 py-2">Route</th>
                  <th className="px-2 py-2">Status</th>
                  <th className="px-2 py-2">Latency</th>
                  <th className="px-2 py-2">Correlation ID</th>
                </tr>
              </thead>
              <tbody>
                {observability.recent_events.slice(0, 8).map((event, index) => (
                  <tr key={`obs-event-${event.timestamp}-${index}`} className="border-b border-soc-800">
                    <td className="px-2 py-2 text-slate-300">{new Date(event.timestamp).toLocaleTimeString()}</td>
                    <td className="px-2 py-2 text-slate-200">{event.method} {event.route}</td>
                    <td className="px-2 py-2 text-slate-300">{event.status_code}</td>
                    <td className="px-2 py-2 text-slate-300">{event.latency_ms} ms</td>
                    <td className="px-2 py-2 font-mono text-[11px] text-slate-400">{event.correlation_id || 'n/a'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {observability?.recent_trace_events?.length ? (
          <div className="mt-4 overflow-x-auto">
            <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">Recent Queue and Task Events</p>
            <table className="min-w-full text-left text-xs">
              <thead>
                <tr className="border-b border-soc-700 text-slate-400">
                  <th className="px-2 py-2">Time</th>
                  <th className="px-2 py-2">Stage</th>
                  <th className="px-2 py-2">Message</th>
                  <th className="px-2 py-2">Correlation ID</th>
                </tr>
              </thead>
              <tbody>
                {observability.recent_trace_events.slice(0, 8).map((event, index) => (
                  <tr key={`trace-event-${event.timestamp}-${index}`} className="border-b border-soc-800">
                    <td className="px-2 py-2 text-slate-300">{new Date(event.timestamp).toLocaleTimeString()}</td>
                    <td className="px-2 py-2 text-cyan-200">{event.stage}</td>
                    <td className="px-2 py-2 text-slate-300">{event.message}</td>
                    <td className="px-2 py-2 font-mono text-[11px] text-slate-400">{event.correlation_id || 'n/a'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </Panel>
    </div>
  )
}
