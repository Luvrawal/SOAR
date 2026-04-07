import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ErrorState } from '../components/ui/ErrorState'
import { LoadingState } from '../components/ui/LoadingState'
import { Panel } from '../components/ui/Panel'
import { api } from '../lib/api'

const simulations = [
  { key: 'brute-force', label: 'Simulate Brute Force', count: 20 },
  { key: 'phishing', label: 'Simulate Phishing', count: 20 },
  { key: 'malware', label: 'Simulate Malware', count: 20 },
  { key: 'network-anomaly', label: 'Simulate Anomaly', count: 20 },
  { key: 'all', label: 'Simulate All Scenarios', count: 10 },
]

export function SimulationLabPage() {
  const navigate = useNavigate()
  const [running, setRunning] = useState('')
  const [error, setError] = useState('')
  const [summary, setSummary] = useState(null)
  const [recentRuns, setRecentRuns] = useState([])
  const [countByType, setCountByType] = useState(
    simulations.reduce((acc, item) => ({ ...acc, [item.key]: item.count }), {}),
  )

  const triggerSimulation = async (simulationType, count) => {
    setRunning(simulationType)
    setError('')
    try {
      const response = await api.post(`/simulations/${simulationType}`, null, { params: { count } })
      const payload = response.data?.data
      setSummary(payload)
      setRecentRuns((previous) => [
        {
          type: simulationType,
          count,
          incidents: payload?.incidents_created ?? 0,
          latestIncidentId: payload?.latest_incident_id,
          timestamp: new Date().toISOString(),
        },
        ...previous,
      ].slice(0, 8))

      const latestIncidentId = response.data?.data?.latest_incident_id
      if (latestIncidentId) {
        navigate(`/incidents/${latestIncidentId}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setRunning('')
    }
  }

  return (
    <div className="space-y-5">
      <Panel title="Simulation Lab" subtitle="Trigger controlled attack scenarios and inspect live outcomes">
        <div className="grid gap-3 md:grid-cols-2">
          {simulations.map((simulation) => (
            <div key={simulation.key} className="rounded-lg border border-soc-700 bg-soc-950/70 p-4">
              <p className="font-display text-lg text-cyan-100">{simulation.label}</p>
              <div className="mt-3 flex items-center gap-2">
                <label className="text-xs uppercase tracking-wider text-slate-400" htmlFor={`count-${simulation.key}`}>
                  Count
                </label>
                <input
                  id={`count-${simulation.key}`}
                  type="number"
                  min={1}
                  max={100}
                  value={countByType[simulation.key]}
                  onChange={(event) =>
                    setCountByType((previous) => ({
                      ...previous,
                      [simulation.key]: Number(event.target.value || simulation.count),
                    }))
                  }
                  className="w-24 rounded-md border border-soc-700 bg-soc-950 px-2 py-1 text-sm text-slate-100"
                />
              </div>
              <button
                type="button"
                disabled={Boolean(running)}
                onClick={() => triggerSimulation(simulation.key, countByType[simulation.key])}
                className="mt-3 rounded-md border border-cyan-500/60 bg-cyan-500/20 px-3 py-2 text-sm font-semibold text-cyan-100 hover:bg-cyan-500/30 disabled:opacity-50"
              >
                Run
              </button>
            </div>
          ))}
        </div>
      </Panel>

      {running ? <LoadingState label={`Running ${running} simulation...`} /> : null}
      {error ? <ErrorState message={error} /> : null}

      <Panel title="Last Run Summary" subtitle="Latest execution contract snapshot">
        {!summary ? (
          <p className="text-sm text-slate-400">No simulation runs yet.</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
              <p>Type: {summary.simulation_type}</p>
              <p className="mt-1">Requested count: {summary.requested_count}</p>
              <p className="mt-1">Alerts generated: {summary.alerts_generated}</p>
              <p className="mt-1">Incidents created: {summary.incidents_created}</p>
            </div>
            <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
              <p>Contract: {summary.contract_version}</p>
              <p className="mt-1">Pipeline: {(summary.pipeline_flow || []).join(' -> ')}</p>
              <p className="mt-1">Latest incident: {summary.latest_incident_id ?? 'n/a'}</p>
            </div>
          </div>
        )}
      </Panel>

      <Panel title="Recent Runs" subtitle="Session-level launch history">
        {!recentRuns.length ? (
          <p className="text-sm text-slate-400">No runs recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-soc-700 text-slate-400">
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Count</th>
                  <th className="px-3 py-2">Incidents</th>
                  <th className="px-3 py-2">Latest ID</th>
                  <th className="px-3 py-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {recentRuns.map((run, index) => (
                  <tr key={`${run.timestamp}-${index}`} className="border-b border-soc-800 text-slate-300">
                    <td className="px-3 py-2">{run.type}</td>
                    <td className="px-3 py-2">{run.count}</td>
                    <td className="px-3 py-2">{run.incidents}</td>
                    <td className="px-3 py-2">{run.latestIncidentId ?? 'n/a'}</td>
                    <td className="px-3 py-2">{new Date(run.timestamp).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  )
}
