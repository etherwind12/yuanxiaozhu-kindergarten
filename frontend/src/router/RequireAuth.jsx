import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../store/auth'

export default function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <div className="page-loading">加载中…</div>
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />
  return children
}
