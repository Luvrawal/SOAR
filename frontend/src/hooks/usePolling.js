import { useEffect, useRef } from 'react'

function getDefaultInterval() {
  const stored = window.localStorage.getItem('soc.pollingMs')
  if (!stored) {
    return 3000
  }
  const value = Number(stored)
  return Number.isFinite(value) ? Math.min(15000, Math.max(1000, value)) : 3000
}

export function usePolling(callback, intervalMs, enabled = true) {
  const callbackRef = useRef(callback)
  const effectiveInterval = intervalMs ?? getDefaultInterval()

  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  useEffect(() => {
    if (!enabled) {
      return undefined
    }

    const run = () => callbackRef.current?.()
    const id = window.setInterval(run, effectiveInterval)
    return () => window.clearInterval(id)
  }, [effectiveInterval, enabled])
}
