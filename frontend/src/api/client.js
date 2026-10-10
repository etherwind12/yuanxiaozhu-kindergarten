import axios from 'axios'

export const baseURL = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'

export const TOKEN_KEY = 'yxz_token'

export const client = axios.create({ baseURL })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      if (window.location.pathname !== '/login') window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function errMsg(err) {
  const d = err?.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg).join('；')
  if (typeof d === 'string') return d
  return err?.message || '请求失败'
}
