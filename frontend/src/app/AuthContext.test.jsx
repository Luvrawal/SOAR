import React from 'react'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from './AuthContext'
import { __getTokenGetter, __getUnauthorizedHandler, api } from '../lib/api'

vi.mock('../lib/api', () => {
  const state = {
    tokenGetter: null,
    unauthorizedHandler: null,
  }

  return {
    api: {
      get: vi.fn(),
      post: vi.fn(),
    },
    setAuthTokenGetter: (getter) => {
      state.tokenGetter = getter
    },
    setUnauthorizedHandler: (handler) => {
      state.unauthorizedHandler = handler
    },
    __getTokenGetter: () => state.tokenGetter,
    __getUnauthorizedHandler: () => state.unauthorizedHandler,
  }
})

function AuthProbe() {
  const { isLoading, isAuthenticated, user, login } = useAuth()

  return (
    <div>
      <p data-testid="loading">{String(isLoading)}</p>
      <p data-testid="authenticated">{String(isAuthenticated)}</p>
      <p data-testid="role">{user?.role || 'none'}</p>
      <button
        type="button"
        onClick={() => login({ email: 'admin@soar.local', password: 'ChangeMe123!' })}
      >
        Login
      </button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
    api.get.mockResolvedValue({ data: { data: { user: { id: 1, role: 'admin', email: 'admin@soar.local' } } } })
  })

  it('initializes unauthenticated state when no token is stored', async () => {
    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    })

    expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
    expect(screen.getByTestId('role')).toHaveTextContent('none')
  })

  it('stores token and user on login', async () => {
    api.post.mockResolvedValueOnce({
      data: {
        data: {
          access_token: 'token-admin',
          user: { id: 1, role: 'admin', email: 'admin@soar.local' },
        },
      },
    })

    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    })

    fireEvent.click(screen.getByRole('button', { name: 'Login' }))

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
    })

    expect(localStorage.getItem('soar_auth_token')).toBe('token-admin')
    expect(localStorage.getItem('soar_auth_user')).toContain('admin@soar.local')
    expect(__getTokenGetter()()).toBe('token-admin')
  })

  it('clears stale storage when bootstrap /auth/me fails', async () => {
    localStorage.setItem('soar_auth_token', 'stale-token')
    localStorage.setItem('soar_auth_user', JSON.stringify({ id: 2, role: 'analyst' }))
    api.get.mockRejectedValueOnce(new Error('Unauthorized'))

    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    })

    expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
    expect(localStorage.getItem('soar_auth_token')).toBeNull()
    expect(localStorage.getItem('soar_auth_user')).toBeNull()
  })

  it('unauthorized handler triggers logout flow', async () => {
    window.history.pushState({}, '', '/login')
    localStorage.setItem('soar_auth_token', 'live-token')
    localStorage.setItem(
      'soar_auth_user',
      JSON.stringify({ id: 2, role: 'analyst', email: 'analyst@soar.local' }),
    )

    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
    })

    const unauthorizedHandler = __getUnauthorizedHandler()
    await act(async () => {
      unauthorizedHandler(new Error('401'))
    })

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
    })
  })
})
