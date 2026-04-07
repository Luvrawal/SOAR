import { useEffect, useState } from 'react'
import { API_BASE_URL, api } from '../../lib/api'

export function BackendStatusBanner() {
  const [status, setStatus] = useState('checking')
  const [detail, setDetail] = useState('')

  useEffect(() => {
    let mounted = true

    const checkBackend = async () => {
      try {
        await api.get('/health')
        if (mounted) {
          setStatus('ok')
          setDetail('')
        }
      } catch (error) {
        if (mounted) {
          setStatus('error')
          setDetail(error.message)
        }
      }
    }

    checkBackend()
    const id = window.setInterval(checkBackend, 10000)

    return () => {
      mounted = false
      window.clearInterval(id)
    }
  }, [])

  if (status === 'ok') {
    return null
  }

  return (
    <div className="mx-4 mt-4 rounded-md border border-amber-500/50 bg-amber-500/10 p-3 text-sm text-amber-100 md:mx-6">
      <p className="font-semibold">Backend connectivity issue</p>
      <p className="mt-1 text-amber-200/90">
        {status === 'checking'
          ? `Checking API at ${API_BASE_URL}...`
          : `${detail} | Expected health endpoint: ${API_BASE_URL}/health`}
      </p>
    </div>
  )
}
