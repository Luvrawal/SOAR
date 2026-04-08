import { ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'

export function UnauthorizedPage() {
  return (
    <div className="mx-auto max-w-lg rounded-xl border border-red-500/30 bg-soc-900/80 p-8 text-center">
      <ShieldAlert className="mx-auto mb-4 h-10 w-10 text-red-400" />
      <h2 className="font-display text-2xl text-red-100">Access denied</h2>
      <p className="mt-2 text-sm text-slate-300">Your account role does not have permission to view this module.</p>
      <Link
        to="/"
        className="mt-6 inline-flex rounded-lg border border-soc-600 bg-soc-800 px-4 py-2 text-sm text-cyan-100"
      >
        Back to dashboard
      </Link>
    </div>
  )
}
