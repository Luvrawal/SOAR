import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ErrorState } from '../components/ui/ErrorState'
import { LoadingState } from '../components/ui/LoadingState'
import { Panel } from '../components/ui/Panel'
import { SeverityBadge } from '../components/ui/SeverityBadge'
import { StatusBadge } from '../components/ui/StatusBadge'
import { useGlobalSearch } from '../app/SearchContext'
import { usePolling } from '../hooks/usePolling'
import { api } from '../lib/api'

export function IncidentsPage() {
  const navigate = useNavigate()
  const { query, setQuery } = useGlobalSearch()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [items, setItems] = useState([])
  const [lastRefreshedAt, setLastRefreshedAt] = useState(null)

  const [filters, setFilters] = useState({
    status: '',
    severity: '',
    type: '',
    q: '',
  })

  useEffect(() => {
    setFilters((prev) => ({ ...prev, q: query }))
  }, [query])

  const fetchIncidents = useCallback(async () => {
    setError('')
    try {
      const response = await api.get('/incidents', {
        params: {
          page: 1,
          page_size: 100,
          ...(filters.status ? { status: filters.status } : {}),
          ...(filters.severity ? { severity: filters.severity } : {}),
          ...(filters.type ? { type: filters.type } : {}),
          ...(filters.q ? { q: filters.q } : {}),
        },
      })
      setItems(response.data.data.items || [])
      setLastRefreshedAt(new Date().toISOString())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    fetchIncidents()
  }, [fetchIncidents])

  usePolling(fetchIncidents, undefined, !loading)

  const openCount = items.filter((item) => item.status === 'open').length
  const failedCount = items.filter((item) => item.playbook_status === 'failed' || item.status === 'failed').length

  if (loading) {
    return <LoadingState label="Loading incidents..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchIncidents} />
  }

  return (
    <Panel title="Incident Management" subtitle="Search, filter, and investigate incidents">
      <div className="mb-4 grid gap-2 md:grid-cols-3">
        <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
          Visible incidents: <span className="font-semibold text-cyan-100">{items.length}</span>
        </div>
        <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
          Open incidents: <span className="font-semibold text-yellow-300">{openCount}</span>
        </div>
        <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
          Failed incidents: <span className="font-semibold text-red-300">{failedCount}</span>
        </div>
      </div>

      <div className="mb-4 grid gap-2 md:grid-cols-4">
        <input
          value={filters.q}
          onChange={(event) => {
            const value = event.target.value
            setFilters((prev) => ({ ...prev, q: value }))
            setQuery(value)
          }}
          placeholder="Search incidents..."
          className="rounded-md border border-soc-700 bg-soc-950 px-3 py-2 text-sm text-slate-100"
        />
        <select
          value={filters.status}
          onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}
          className="rounded-md border border-soc-700 bg-soc-950 px-3 py-2 text-sm text-slate-100"
        >
          <option value="">All Status</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
          <option value="failed">Failed</option>
        </select>
        <select
          value={filters.severity}
          onChange={(event) => setFilters((prev) => ({ ...prev, severity: event.target.value }))}
          className="rounded-md border border-soc-700 bg-soc-950 px-3 py-2 text-sm text-slate-100"
        >
          <option value="">All Severity</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <input
          value={filters.type}
          onChange={(event) => setFilters((prev) => ({ ...prev, type: event.target.value }))}
          placeholder="Type filter (e.g. phishing)"
          className="rounded-md border border-soc-700 bg-soc-950 px-3 py-2 text-sm text-slate-100"
        />
      </div>

      <p className="mb-3 text-xs text-slate-500">Last refreshed: {lastRefreshedAt ? new Date(lastRefreshedAt).toLocaleTimeString() : 'n/a'}</p>

      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b border-soc-700 text-slate-400">
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Severity</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {items.map((incident) => (
              <tr
                key={incident.id}
                onClick={() => navigate(`/incidents/${incident.id}`)}
                className="cursor-pointer border-b border-soc-800 hover:bg-soc-800/60"
              >
                <td className="px-3 py-3 font-semibold text-cyan-100">#{incident.id}</td>
                <td className="px-3 py-3 text-slate-200">{incident.title}</td>
                <td className="px-3 py-3"><SeverityBadge severity={incident.severity} /></td>
                <td className="px-3 py-3"><StatusBadge status={incident.playbook_status} /></td>
                <td className="px-3 py-3 text-slate-400">{new Date(incident.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {!items.length ? (
              <tr>
                <td colSpan={5} className="px-3 py-8 text-center text-slate-500">No incidents match current filters.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </Panel>
  )
}
