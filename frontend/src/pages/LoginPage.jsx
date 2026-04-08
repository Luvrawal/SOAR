import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../app/AuthContext'
import { api } from '../lib/api'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, register } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState('analyst')
  const [mode, setMode] = useState('login')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [requiresBootstrap, setRequiresBootstrap] = useState(null)

  useEffect(() => {
    let isCancelled = false

    async function loadBootstrapStatus() {
      try {
        const response = await api.get('/auth/bootstrap-status')
        const status = response?.data?.data?.requires_bootstrap
        if (!isCancelled && typeof status === 'boolean') {
          setRequiresBootstrap(status)
        }
      } catch {
        if (!isCancelled) {
          setRequiresBootstrap(null)
        }
      }
    }

    loadBootstrapStatus()
    return () => {
      isCancelled = true
    }
  }, [])

  const redirectTo = location.state?.from || '/'

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setBusy(true)

    try {
      if (mode === 'login') {
        await login({ email, password })
        navigate(redirectTo, { replace: true })
      } else {
        await register({ email, password, full_name: fullName || null, role })
        setMode('login')
      }
    } catch (submitError) {
      setError(submitError.message || 'Authentication failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-soc-950 px-4">
      <div className="w-full max-w-md rounded-xl border border-soc-700 bg-soc-900/90 p-6 shadow-xl">
        <h1 className="font-display text-2xl text-cyan-100">SOAR Access</h1>
        <p className="mt-1 text-sm text-slate-400">
          {mode === 'login'
            ? 'Sign in to continue to SOC modules.'
            : requiresBootstrap === true
              ? 'Register a user (first user becomes admin).'
              : 'Register a user (admin sign-in is required after bootstrap).'}
        </p>

        <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
          {mode === 'register' ? (
            <label className="block text-sm text-slate-300">
              Full name
              <input
                className="mt-1 w-full rounded-lg border border-soc-700 bg-soc-950 px-3 py-2 text-slate-100 outline-none focus:ring-2 focus:ring-soc-accent/60"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="SOC Analyst"
              />
            </label>
          ) : null}

          <label className="block text-sm text-slate-300">
            Email
            <input
              type="email"
              required
              className="mt-1 w-full rounded-lg border border-soc-700 bg-soc-950 px-3 py-2 text-slate-100 outline-none focus:ring-2 focus:ring-soc-accent/60"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="analyst@soar.local"
            />
          </label>

          <label className="block text-sm text-slate-300">
            Password
            <input
              type="password"
              required
              minLength={8}
              className="mt-1 w-full rounded-lg border border-soc-700 bg-soc-950 px-3 py-2 text-slate-100 outline-none focus:ring-2 focus:ring-soc-accent/60"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Minimum 8 characters"
            />
          </label>

          {mode === 'register' ? (
            <label className="block text-sm text-slate-300">
              Role
              <select
                value={role}
                onChange={(event) => setRole(event.target.value)}
                className="mt-1 w-full rounded-lg border border-soc-700 bg-soc-950 px-3 py-2 text-slate-100 outline-none focus:ring-2 focus:ring-soc-accent/60"
              >
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
              </select>
            </label>
          ) : null}

          {error ? <p className="text-sm text-red-300">{error}</p> : null}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-soc-accent px-4 py-2 text-sm font-semibold text-soc-950 disabled:opacity-70"
          >
            {busy ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Register'}
          </button>
        </form>

        <button
          type="button"
          onClick={() => setMode((current) => (current === 'login' ? 'register' : 'login'))}
          className="mt-4 text-sm text-cyan-300"
        >
          {mode === 'login' ? 'Need to create an account?' : 'Already have an account? Sign in'}
        </button>
      </div>
    </div>
  )
}
