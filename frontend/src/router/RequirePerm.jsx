import { useAuth } from '../store/auth'

export default function RequirePerm({ perm, children }) {
  const { has } = useAuth()
  if (!has(perm)) {
    return (
      <div className="empty">
        <div className="empty-code">403</div>
        <p>无权限访问该功能，请联系园长分配权限。</p>
      </div>
    )
  }
  return children
}
