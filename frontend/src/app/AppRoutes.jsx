import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '../components/routing/ProtectedRoute'
import { AppLayout } from '../components/layout/AppLayout'
import { LoadingState } from '../components/ui/LoadingState'

const DashboardPage = lazy(() => import('../pages/DashboardPage').then((m) => ({ default: m.DashboardPage })))
const IncidentsPage = lazy(() => import('../pages/IncidentsPage').then((m) => ({ default: m.IncidentsPage })))
const IncidentDetailPage = lazy(() =>
  import('../pages/IncidentDetailPage').then((m) => ({ default: m.IncidentDetailPage })),
)
const PlaybooksPage = lazy(() => import('../pages/PlaybooksPage').then((m) => ({ default: m.PlaybooksPage })))
const ThreatIntelPage = lazy(() =>
  import('../pages/ThreatIntelPage').then((m) => ({ default: m.ThreatIntelPage })),
)
const SimulationLabPage = lazy(() =>
  import('../pages/SimulationLabPage').then((m) => ({ default: m.SimulationLabPage })),
)
const SettingsPage = lazy(() => import('../pages/SettingsPage').then((m) => ({ default: m.SettingsPage })))
const LoginPage = lazy(() => import('../pages/LoginPage').then((m) => ({ default: m.LoginPage })))
const UnauthorizedPage = lazy(() =>
  import('../pages/UnauthorizedPage').then((m) => ({ default: m.UnauthorizedPage })),
)

export function AppRoutes() {
  return (
    <Suspense fallback={<LoadingState label="Loading SOC module..." />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />
        <Route element={<AppLayout />}>
          <Route
            path="/"
            element={
              <ProtectedRoute allowedRoles={['admin', 'analyst']}>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/incidents"
            element={
              <ProtectedRoute allowedRoles={['admin', 'analyst']}>
                <IncidentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/incidents/:incidentId"
            element={
              <ProtectedRoute allowedRoles={['admin', 'analyst']}>
                <IncidentDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/playbooks"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <PlaybooksPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/threat-intelligence"
            element={
              <ProtectedRoute allowedRoles={['admin', 'analyst']}>
                <ThreatIntelPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/simulation-lab"
            element={
              <ProtectedRoute allowedRoles={['admin', 'analyst']}>
                <SimulationLabPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
