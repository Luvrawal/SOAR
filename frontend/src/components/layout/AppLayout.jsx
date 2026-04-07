import { Outlet } from 'react-router-dom'
import { SearchProvider } from '../../app/SearchContext'
import { BackendStatusBanner } from './BackendStatusBanner'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

export function AppLayout() {
  return (
    <SearchProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar />
          <BackendStatusBanner />
          <main className="flex-1 p-4 md:p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </SearchProvider>
  )
}
