import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api, setAuthTokenGetter, setUnauthorizedHandler } from '../lib/api'

const TOKEN_KEY = 'soar_auth_token'
const USER_KEY = 'soar_auth_user'

const AuthContext = createContext(null)

function readStoredUser() {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState(() => readStoredUser())
  const [isLoading, setIsLoading] = useState(true)

  const logout = (forceRedirect = false) => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)

    if (forceRedirect && window.location.pathname !== '/login') {
      window.location.assign('/login')
    }
  }

  useEffect(() => {
    setAuthTokenGetter(() => token)
    setUnauthorizedHandler(() => logout(true))

    return () => {
      setAuthTokenGetter(null)
      setUnauthorizedHandler(null)
    }
  }, [token])

  useEffect(() => {
    let cancelled = false

    async function bootstrapSession() {
      if (!token) {
        if (!cancelled) {
          setIsLoading(false)
        }
        return
      }

      try {
        const response = await api.get('/auth/me')
        const resolvedUser = response?.data?.data?.user
        if (!cancelled && resolvedUser) {
          setUser(resolvedUser)
          localStorage.setItem(USER_KEY, JSON.stringify(resolvedUser))
        }
      } catch {
        if (!cancelled) {
          logout(false)
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    bootstrapSession()

    return () => {
      cancelled = true
    }
  }, [token])

  const login = async ({ email, password }) => {
    const response = await api.post('/auth/login', { email, password })
    const authData = response?.data?.data

    if (!authData?.access_token || !authData?.user) {
      throw new Error('Invalid authentication response from server')
    }

    localStorage.setItem(TOKEN_KEY, authData.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(authData.user))
    setToken(authData.access_token)
    setUser(authData.user)
    return authData.user
  }

  const register = async ({ email, password, full_name, role }) => {
    await api.post('/auth/register', { email, password, full_name, role })
  }

  const value = useMemo(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: Boolean(token && user),
      login,
      logout,
      register,
    }),
    [user, token, isLoading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
