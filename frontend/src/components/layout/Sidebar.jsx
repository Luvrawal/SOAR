import { useMemo, useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  Beaker,
  Bot,
  ChevronLeft,
  Gauge,
  Settings,
  Shield,
} from 'lucide-react'
import clsx from 'clsx'
import { useAuth } from '../../app/AuthContext'

const navItems = [
  { to: '/', label: 'Dashboard', icon: Gauge, roles: ['admin', 'analyst'] },
  { to: '/incidents', label: 'Incidents', icon: AlertTriangle, roles: ['admin', 'analyst'] },
  { to: '/playbooks', label: 'Playbooks', icon: Bot, roles: ['admin'] },
  { to: '/threat-intelligence', label: 'Threat Intelligence', icon: Shield, roles: ['admin', 'analyst'] },
  { to: '/simulation-lab', label: 'Simulation Lab', icon: Beaker, roles: ['admin', 'analyst'] },
  { to: '/settings', label: 'Settings', icon: Settings, roles: ['admin'] },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const { user } = useAuth()

  const widthClass = useMemo(() => (collapsed ? 'w-[82px]' : 'w-[250px]'), [collapsed])
  const visibleNavItems = useMemo(() => {
    const role = user?.role
    return navItems.filter((item) => !role || item.roles.includes(role))
  }, [user])

  return (
    <aside className={clsx('relative hidden border-r border-soc-700/60 bg-soc-900/85 md:flex md:flex-col', widthClass)}>
      <button
        type="button"
        onClick={() => setCollapsed((value) => !value)}
        className="absolute -right-3 top-5 rounded-full border border-soc-600 bg-soc-900 p-1 text-cyan-200"
      >
        <ChevronLeft className={clsx('h-4 w-4 transition-transform', collapsed && 'rotate-180')} />
      </button>

      <div className="grid-bg border-b border-soc-700/60 px-4 py-6">
        <div className="flex items-center gap-3">
          <Activity className="h-6 w-6 text-soc-accent" />
          {!collapsed ? <h1 className="font-display text-xl font-bold tracking-wider text-cyan-100">SOAR SOC</h1> : null}
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {visibleNavItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition',
                  isActive
                    ? 'bg-soc-700/60 text-cyan-100 shadow-inner'
                    : 'text-slate-300 hover:bg-soc-800/80 hover:text-cyan-100',
                )
              }
            >
              <Icon className="h-5 w-5" />
              {!collapsed ? <span>{item.label}</span> : null}
            </NavLink>
          )
        })}
      </nav>

      <div className="border-t border-soc-700/60 p-4 text-xs uppercase tracking-[0.2em] text-slate-500">
        {!collapsed ? 'Monitoring online' : 'Online'}
      </div>
    </aside>
  )
}
