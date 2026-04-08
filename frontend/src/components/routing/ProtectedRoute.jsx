import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../app/AuthContext'
import { LoadingState } from '../ui/LoadingState'

export function ProtectedRoute({ children, allowedRoles = [] }) {
  const location = useLocation()
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return <LoadingState label="Checking session..." />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/unauthorized" replace />
  }

  return children
}
