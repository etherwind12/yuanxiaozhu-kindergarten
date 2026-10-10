import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { authApi } from '../api'
import { TOKEN_KEY } from '../api/client'
import { loadDict } from './dict'

const AuthContext = createContext({ user: null, loading: true, perms: [], roleName: () => '', has: () => false })

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [dict, setDict] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setLoading(false)
      return
    }
    Promise.all([authApi.me(), loadDict().catch(() => null)])
      .then(([profile, d]) => {
        setUser(profile)
        setDict(d)
      })
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (username, password) => {
    const { access_token } = await authApi.login(username, password)
    localStorage.setItem(TOKEN_KEY, access_token)
    const [profile, d] = await Promise.all([authApi.me(), loadDict().catch(() => null)])
    setUser(profile)
    setDict(d)
    return profile
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
    setDict(null)
  }, [])

  const value = useMemo(() => {
    const perms = (user && dict?.permissions?.[user.role]) || []
    return {
      user,
      loading,
      login,
      logout,
      perms,
      has: (perm) => (perm ? perms.includes(perm) : true),
      roleName: (role) => dict?.role.find((r) => r.value === role)?.name || role || '',
    }
  }, [user, dict, loading, login, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
