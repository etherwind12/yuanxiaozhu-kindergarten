import { createContext, useContext, useEffect, useState } from 'react'

import { metaApi } from '../api'

let pending = null

// 字典全局只请求一次：登录流程与页面渲染共用同一份结果
export function loadDict() {
  if (!pending) {
    pending = metaApi.dictionaries().catch((err) => {
      pending = null
      throw err
    })
  }
  return pending
}

const DictContext = createContext(null)

export function DictProvider({ children }) {
  const [dict, setDict] = useState(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let alive = true
    loadDict()
      .then((d) => { if (alive) setDict(d) })
      .catch(() => { if (alive) setFailed(true) })
    return () => { alive = false }
  }, [])

  if (failed) return <div className="alert">系统字典加载失败，请刷新页面重试。</div>
  if (!dict) return <div className="page-loading">加载中…</div>
  return <DictContext.Provider value={dict}>{children}</DictContext.Provider>
}

export function useDict() {
  return useContext(DictContext)
}

export function dictText(list, value) {
  return list?.find((x) => x.value === value)?.text || value || '—'
}

export function dictTone(list, value) {
  return list?.find((x) => x.value === value)?.tone || 'default'
}
