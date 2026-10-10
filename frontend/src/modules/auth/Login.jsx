import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { errMsg } from '../../api/client'
import { Button, Field } from '../../components/ui'
import { useAuth } from '../../store/auth'

const PRESETS = [
  { label: '园长', username: 'admin' },
  { label: '后勤', username: 'logistics' },
  { label: '教师', username: 'teacher' },
]

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ username: 'admin', password: 'admin123' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await login(form.username.trim(), form.password)
      navigate(location.state?.from || '/dashboard', { replace: true })
    } catch (err) {
      setError(errMsg(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <div className="login-brand">
          <div className="logo">园</div>
          <h1>园小助</h1>
          <p>幼儿园园务管理辅助系统</p>
        </div>

        {error && <div className="alert">{error}</div>}

        <Field label="账号" required>
          <input
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            placeholder="请输入用户名"
            autoComplete="username"
          />
        </Field>
        <Field label="密码" required>
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            placeholder="请输入密码"
            autoComplete="current-password"
          />
        </Field>

        <Button type="submit" disabled={busy} style={{ width: '100%', justifyContent: 'center' }}>
          {busy ? '登录中…' : '登 录'}
        </Button>

        <div className="flex wrap" style={{ justifyContent: 'center', marginTop: 12 }}>
          {PRESETS.map((p) => (
            <Button
              key={p.username}
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setForm({ username: p.username, password: 'admin123' })}
            >
              {p.label}
            </Button>
          ))}
        </div>
        <div className="login-hint">默认密码均为 admin123</div>
      </form>
    </div>
  )
}
