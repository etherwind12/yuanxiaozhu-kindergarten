import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { assetApi } from '../../api'
import { errMsg } from '../../api/client'
import { Tag } from '../../components/ui'

export default function ScanPage() {
  const { token } = useParams()
  const [card, setCard] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    assetApi.scan(token).then(setCard).catch((e) => setError(errMsg(e)))
  }, [token])

  const shell = (children) => <div className="scan-page"><div className="scan-card">{children}</div></div>

  if (error) {
    return shell(<><div className="scan-bad">✕</div><h2>查询失败</h2><p className="scan-note">{error}</p></>)
  }
  if (!card) {
    return shell(<p className="muted">正在校验二维码…</p>)
  }
  if (!card.valid) {
    return shell(<><div className="scan-bad">✕</div><h2>无效二维码</h2><p className="scan-note">{card.message}</p></>)
  }

  return shell(
    <>
      <div className="scan-ok">✓</div>
      <h2>{card.name}</h2>
      <p className="scan-org">{card.category} · {card.org_name}</p>
      <div className="scan-grid">
        <div><span>资产编号</span><b className="mono">{card.code}</b></div>
        <div><span>状态</span><b><Tag tone={card.status_tone}>{card.status_text || card.status}</Tag></b></div>
        <div><span>存放位置</span><b>{card.location || '—'}</b></div>
        <div><span>数量</span><b>{card.quantity} {card.unit}</b></div>
        <div><span>适龄段</span><b>{card.age_range || '—'}</b></div>
        <div><span>安全等级</span><b>{card.safety_level || '—'}</b></div>
      </div>
      <p className="scan-note">{card.message}</p>
    </>,
  )
}
