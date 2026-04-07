import { Search, UserCircle2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useGlobalSearch } from '../../app/SearchContext'

export function Topbar() {
  const navigate = useNavigate()
  const { query, setQuery } = useGlobalSearch()

  const handleSubmit = (event) => {
    event.preventDefault()
    const normalized = query.trim()
    if (!normalized) {
      return
    }

    if (normalized.includes('.') || normalized.includes('http') || normalized.includes(':')) {
      navigate('/threat-intelligence')
      return
    }

    navigate('/incidents')
  }

  return (
    <header className="sticky top-0 z-20 border-b border-soc-700/60 bg-soc-900/75 px-4 py-3 backdrop-blur md:px-6">
      <div className="flex items-center justify-between gap-4">
        <form onSubmit={handleSubmit} className="w-full max-w-xl">
          <label className="relative flex items-center">
            <Search className="pointer-events-none absolute left-3 h-4 w-4 text-slate-400" />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search incidents, indicators, playbooks..."
              className="w-full rounded-lg border border-soc-700 bg-soc-950/80 py-2 pl-9 pr-3 text-sm text-slate-100 outline-none ring-soc-accent/60 placeholder:text-slate-500 focus:ring-2"
            />
          </label>
        </form>

        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-lg border border-soc-700 bg-soc-950/80 px-3 py-2 text-sm text-slate-200"
        >
          <UserCircle2 className="h-5 w-5 text-soc-accent" />
          Analyst
        </button>
      </div>
    </header>
  )
}
