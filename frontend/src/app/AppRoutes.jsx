import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
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

export function AppRoutes() {
  return (
    <Suspense fallback={<LoadingState label="Loading SOC module..." />}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/incidents/:incidentId" element={<IncidentDetailPage />} />
          <Route path="/playbooks" element={<PlaybooksPage />} />
          <Route path="/threat-intelligence" element={<ThreatIntelPage />} />
          <Route path="/simulation-lab" element={<SimulationLabPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
