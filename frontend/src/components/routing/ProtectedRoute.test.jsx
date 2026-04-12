import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './ProtectedRoute'

const mockUseAuth = vi.fn()

vi.mock('../../app/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

function renderProtectedRoute(initialPath = '/protected') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route path="/unauthorized" element={<div>Unauthorized Page</div>} />
        <Route
          path="/protected"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('renders loading state while auth context is initializing', () => {
    mockUseAuth.mockReturnValue({
      isLoading: true,
      isAuthenticated: false,
      user: null,
    })

    renderProtectedRoute()

    expect(screen.getByText('Checking session...')).toBeInTheDocument()
  })

  it('redirects unauthenticated users to login', () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: false,
      user: null,
    })

    renderProtectedRoute()

    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })

  it('redirects authenticated users without required role to unauthorized', () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: true,
      user: { role: 'analyst' },
    })

    renderProtectedRoute()

    expect(screen.getByText('Unauthorized Page')).toBeInTheDocument()
  })

  it('renders protected content when user has required role', () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: true,
      user: { role: 'admin' },
    })

    renderProtectedRoute()

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })
})
