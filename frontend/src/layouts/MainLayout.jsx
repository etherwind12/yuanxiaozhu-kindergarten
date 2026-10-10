import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import Assistant from '../components/Assistant'
import { useAuth } from '../store/auth'

const MENUS = [
  { to: '/dashboard', label: '总览', icon: '▦' },
  { to: '/assets', label: '资产台账', icon: '▤', perm: 'asset:view' },
  { to: '/borrow', label: '借还登记', icon: '⇄', perm: 'borrow' },
  { to: '/inventory', label: '盘点管理', icon: '☰', perm: 'inventory' },
  { to: '/inspection', label: '巡检预警', icon: '⏰', perm: 'inspection' },
  { to: '/teaching', label: '教学预留', icon: '✦', perm: 'reserve:apply' },
  { to: '/report', label: '统计报表', icon: '◔', perm: 'report' },
  { to: '/system', label: '系统管理', icon: '⚙', perm: 'user:manage' },
]

export default function MainLayout() {
  const { user, has, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-logo">园</span>
          <div>
            <div className="brand-title">园小助</div>
            <div className="brand-sub">园务资产管理系统</div>
          </div>
        </div>
        <nav className="nav">
          {MENUS.filter((m) => has(m.perm)).map((m) => (
            <NavLink key={m.to} to={m.to} className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
              <span className="nav-icon">{m.icon}</span>
              {m.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="topbar-title">幼儿园园务管理辅助系统</div>
          <div className="topbar-user">
            <span className="avatar">{(user?.full_name || user?.username || '·').slice(0, 1)}</span>
            <div className="user-meta">
              <b>{user?.full_name || user?.username}</b>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={handleLogout}>退出</button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>

      <Assistant />
    </div>
  )
}
