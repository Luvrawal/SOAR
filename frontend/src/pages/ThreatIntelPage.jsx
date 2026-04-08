import { useEffect, useMemo, useState } from 'react'
import { useGlobalSearch } from '../app/SearchContext'
import { ErrorState } from '../components/ui/ErrorState'
import { LoadingState } from '../components/ui/LoadingState'
import { Panel } from '../components/ui/Panel'
import { api } from '../lib/api'

function inferIndicatorType(value) {
  const normalized = value.trim().toLowerCase()
  if (!normalized) {
    return 'ip'
  }
  if (/^https?:\/\//.test(normalized)) {
    return 'url'
  }
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(normalized)) {
    return 'ip'
  }
  if (/^[a-f0-9]{32}$|^[a-f0-9]{40}$|^[a-f0-9]{64}$/.test(normalized)) {
    return 'hash'
  }
  return 'domain'
}


function riskColorClasses(severity) {
  if (severity === 'high') {
    return 'border-red-500/50 bg-red-500/15 text-red-100'
  }
  if (severity === 'medium') {
    return 'border-amber-500/50 bg-amber-500/15 text-amber-100'
  }
  return 'border-emerald-500/50 bg-emerald-500/15 text-emerald-100'
}

export function ThreatIntelPage() {
  const { query } = useGlobalSearch()
  const [indicator, setIndicator] = useState('')
  const [indicatorType, setIndicatorType] = useState('ip')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])

  useEffect(() => {
    const normalized = query.trim()
    if (!normalized) {
      return
    }
    setIndicator(normalized)
    setIndicatorType(inferIndicatorType(normalized))
  }, [query])

  const inferredType = useMemo(() => inferIndicatorType(indicator), [indicator])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await api.post('/threat-intel/query', {
        indicator,
        indicator_type: indicatorType,
      })
      const payload = response.data.data
      setResult(payload)
      setHistory((previous) => [
        {
          indicator: payload.indicator,
          indicatorType: payload.indicator_type,
          label: payload.risk_summary.label,
          confidence: payload.risk_summary.confidence,
          score: payload.risk_summary.score,
          timestamp: new Date().toISOString(),
        },
        ...previous,
      ].slice(0, 8))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const providerRows = result
    ? [
        {
          provider: 'VirusTotal',
          details: result.results?.virustotal,
        },
        {
          provider: 'AbuseIPDB',
          details: result.results?.abuseipdb,
        },
        {
          provider: 'AlienVault OTX',
          details: result.results?.alienvault,
        },
        {
          provider: 'MalwareBazaar',
          details: result.results?.malwarebazaar,
        },
      ]
    : []

  return (
    <div className="space-y-5">
      <Panel title="Threat Intelligence" subtitle="Analyze IP, domain, URL, or hash indicators">
        <form onSubmit={handleSubmit} className="grid gap-3 md:grid-cols-4">
          <input
            value={indicator}
            onChange={(event) => setIndicator(event.target.value)}
            placeholder="Enter indicator..."
            className="rounded-md border border-soc-700 bg-soc-950 px-3 py-2 text-sm text-slate-100 md:col-span-2"
            required
          />
          <select
            value={indicatorType}
            onChange={(event) => setIndicatorType(event.target.value)}
            className="rounded-md border border-soc-700 bg-soc-950 px-3 py-2 text-sm text-slate-100"
          >
            <option value="ip">IP</option>
            <option value="domain">Domain</option>
            <option value="url">URL</option>
            <option value="hash">Hash</option>
          </select>
          <button
            type="submit"
            className="rounded-md border border-cyan-500/60 bg-cyan-500/20 px-3 py-2 text-sm font-semibold text-cyan-100 hover:bg-cyan-500/30"
          >
            Query Intel
          </button>
        </form>
        <p className="mt-2 text-xs text-slate-500">Detected type: {inferredType}</p>
      </Panel>

      {loading ? <LoadingState label="Querying threat intelligence providers..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {result ? (
        <Panel title="Intelligence Results" subtitle={`Risk: ${result.risk_summary.label.toUpperCase()} (${result.risk_summary.score}/100)`}>
          <div className="mb-3 grid gap-3 md:grid-cols-3">
            <div className={`rounded-md border p-3 text-sm ${riskColorClasses(result.risk_summary.severity)}`}>
              Threat score: {result.risk_summary.score}/100 ({result.risk_summary.severity})
            </div>
            <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
              Confidence: {result.risk_summary.confidence}
            </div>
            <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
              Degraded mode: {result.risk_summary.degraded ? 'Yes' : 'No'}
            </div>
            <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
              Indicator: {result.indicator}
            </div>
            <div className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
              Type: {result.indicator_type}
            </div>
          </div>

          <div className="mb-4 rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-200">
            <p className="font-semibold text-cyan-100">Scoring factors</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-slate-300">
              {(result.risk_summary.factors || []).map((factor, index) => (
                <li key={`${factor}-${index}`}>{factor}</li>
              ))}
            </ul>
          </div>

          <div className="mb-4 grid gap-3 md:grid-cols-2">
            {providerRows.map((row) => (
              <div key={row.provider} className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
                <p className="font-semibold text-cyan-100">{row.provider}</p>
                <pre className="mt-2 max-h-36 overflow-auto text-xs text-slate-300">
                  {JSON.stringify(row.details || { status: 'no-data' }, null, 2)}
                </pre>
              </div>
            ))}
          </div>

          {Object.keys(result.risk_summary.provider_errors || {}).length > 0 ? (
            <pre className="mb-4 overflow-auto rounded-md border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-200">
              {JSON.stringify(result.risk_summary.provider_errors, null, 2)}
            </pre>
          ) : null}

          <pre className="max-h-[420px] overflow-auto rounded-md border border-soc-700 bg-soc-950/60 p-3 text-xs text-slate-300">
            {JSON.stringify(result.results, null, 2)}
          </pre>
        </Panel>
      ) : null}

      <Panel title="Recent Queries" subtitle="Latest IOC lookups in this session">
        {!history.length ? (
          <p className="text-sm text-slate-400">No queries yet.</p>
        ) : (
          <div className="space-y-2">
            {history.map((item, index) => (
              <div key={`${item.indicator}-${item.timestamp}-${index}`} className="rounded-md border border-soc-700 bg-soc-950/50 p-3 text-sm text-slate-300">
                <p className="font-semibold text-cyan-100">{item.indicator}</p>
                <p className="mt-1 text-xs text-slate-400">{item.indicatorType} | {new Date(item.timestamp).toLocaleTimeString()}</p>
                <p className="mt-1">Risk: {item.label.toUpperCase()} ({item.score}/100) | Confidence: {item.confidence}</p>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}
