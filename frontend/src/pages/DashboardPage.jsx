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
import { api } from '../lib/api'

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

export function DashboardPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [summary, setSummary] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [runningSimulation, setRunningSimulation] = useState('')
  const [lastRefreshedAt, setLastRefreshedAt] = useState(null)

  const fetchDashboardData = useCallback(async () => {
    setError('')
    try {
      const [summaryRes, incidentsRes] = await Promise.all([
        api.get('/simulations/summary', { params: { limit: 50 } }),
        api.get('/incidents', { params: { page: 1, page_size: 50 } }),
      ])

      setSummary(summaryRes.data.data)
      setIncidents(incidentsRes.data.data.items || [])
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
    </div>
  )
}
