import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { reportApi } from '../../api'
import { errMsg } from '../../api/client'
import { Card, Empty, Loading, Tag, fmtDate } from '../../components/ui'
import { useAuth } from '../../store/auth'
import { dictText, useDict } from '../../store/dict'

export default function Dashboard() {
  const { user } = useAuth()
  const dict = useDict()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    reportApi.overview(7).then(setData).catch((e) => setError(errMsg(e)))
  }, [])

  if (error) return <div className="alert">{error}</div>
  if (!data) return <Loading />

  const overdue = data.due_soon.filter((i) => i.days_left < 0)

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>欢迎回来，{user?.full_name || user?.username}</h2>
        </div>
        <Link className="btn btn-ghost btn-sm" to="/report">查看完整报表</Link>
      </div>

      <div className="stat-grid">
        <div className="stat"><div className="label">资产总数</div><div className="value">{data.asset_total}<small>件/类</small></div></div>
        <div className="stat"><div className="label">借出中</div><div className="value">{data.borrowing_count}<small>笔</small></div></div>
        <div className="stat"><div className="label">逾期未还</div><div className="value" style={{ color: data.overdue_borrow_count ? 'var(--danger)' : undefined }}>{data.overdue_borrow_count}<small>笔</small></div></div>
        <div className="stat"><div className="label">待处理巡检</div><div className="value">{data.inspection_pending}<small>项</small></div></div>
        <div className="stat"><div className="label">巡检已逾期</div><div className="value" style={{ color: data.inspection_overdue ? 'var(--danger)' : undefined }}>{data.inspection_overdue}<small>项</small></div></div>
        <div className="stat"><div className="label">进行中盘点</div><div className="value">{data.inventory_open}<small>个</small></div></div>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <Card title="资产状态分布">
          <div className="legend">
            {dict.asset_status.map((o) => {
              const count = data.status_counts[o.value] || 0
              const total = data.asset_total || 1
              return (
                <div className="legend-row" key={o.value}>
                  <span>{o.text}</span>
                  <div className="bar" style={{ width: `${Math.max((count / total) * 100, 1)}%` }} />
                  <span className="muted">{count}</span>
                </div>
              )
            })}
          </div>
        </Card>

        <Card title={`到期预警（7 天内，共 ${data.due_soon.length} 项）`}>
          {data.due_soon.length === 0 ? (
            <Empty text="近 7 天无消毒 / 安全检查到期事项" />
          ) : (
            <div className="table-wrap" style={{ maxHeight: 320, overflowY: 'auto' }}>
              <table>
                <thead>
                  <tr><th>资产</th><th>类型</th><th>到期日</th><th>剩余</th></tr>
                </thead>
                <tbody>
                  {data.due_soon.map((it, i) => (
                    <tr key={i}>
                      <td>{it.asset_name}</td>
                      <td>{dictText(dict.inspection_type, it.type)}</td>
                      <td>{fmtDate(it.due_date)}</td>
                      <td>
                        {it.days_left < 0 ? <Tag tone="danger">逾期 {Math.abs(it.days_left)} 天</Tag> : <Tag tone="warn">{it.days_left} 天</Tag>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      {overdue.length > 0 && (
        <Card title="需重点关注">
          <p className="muted">存在 <b style={{ color: 'var(--danger)' }}>{overdue.length}</b> 项已逾期的消毒 / 安全检查，请尽快处理。</p>
        </Card>
      )}
    </div>
  )
}
