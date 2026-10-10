import { useEffect, useState } from 'react'

import { reportApi } from '../../api'
import { errMsg } from '../../api/client'
import Modal from '../../components/Modal'
import { Button, Card, Empty, Loading, Tag, fmtDate, fmtTime } from '../../components/ui'
import { useAuth } from '../../store/auth'
import { dictText, useDict } from '../../store/dict'

function saveBlob(res, fallback) {
  const cd = res.headers['content-disposition'] || ''
  let name = fallback
  const m = /filename\*=UTF-8''([^;]+)/i.exec(cd)
  if (m) {
    try { name = decodeURIComponent(m[1]) } catch { name = m[1] }
  }
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}

export default function Report() {
  const { has } = useAuth()
  const dict = useDict()
  const canTrace = has('report:trace')

  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [days, setDays] = useState(7)
  const [exporting, setExporting] = useState(false)
  const [notice, setNotice] = useState('')
  const [logs, setLogs] = useState([])
  const [traceOpen, setTraceOpen] = useState(false)
  const [traceCode, setTraceCode] = useState('')
  const [traceRes, setTraceRes] = useState(null)
  const [traceErr, setTraceErr] = useState('')

  useEffect(() => {
    setData(null)
    reportApi.overview(days).then(setData).catch((e) => setError(errMsg(e)))
  }, [days])

  useEffect(() => {
    if (!canTrace) return
    reportApi.exportLogs().then(setLogs).catch(() => setLogs([]))
  }, [canTrace, exporting])

  const doExport = async () => {
    setError('')
    setNotice('')
    setExporting(true)
    try {
      const res = await reportApi.exportExcel(days)
      saveBlob(res, `园务资产报表_${days}天.xlsx`)
      const code = res.headers['x-watermark-code']
      setNotice(code ? `导出成功，本次文件暗水印溯源码：${code}` : '导出成功')
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setExporting(false)
    }
  }

  const openTrace = (code = '') => {
    setTraceCode(code)
    setTraceRes(null)
    setTraceErr('')
    setTraceOpen(true)
  }

  const doTrace = async () => {
    setTraceErr('')
    setTraceRes(null)
    try {
      setTraceRes(await reportApi.trace(traceCode.trim()))
    } catch (e) {
      setTraceErr(errMsg(e))
    }
  }

  if (error) return <div className="alert">{error}</div>
  if (!data) return <Loading />

  const total = data.asset_total || 1
  const maxCat = Math.max(1, ...data.by_category.map((c) => c.count))
  const maxDomain = Math.max(1, ...data.by_domain.map((d) => d.count))

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>统计报表</h2>
          <div className="sub">导出的 Excel 已内嵌可溯源暗水印，可反查导出人与数据域</div>
        </div>
        <div className="flex wrap">
          <select style={{ maxWidth: 170 }} value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={3}>预警范围 3 天</option>
            <option value={7}>预警范围 7 天</option>
            <option value={30}>预警范围 30 天</option>
            <option value={90}>预警范围 90 天</option>
          </select>
          {canTrace && <Button variant="ghost" onClick={() => openTrace()}>水印溯源</Button>}
          <Button onClick={doExport} disabled={exporting}>{exporting ? '导出中…' : '导出 Excel'}</Button>
        </div>
      </div>

      {notice && <div className="alert alert-ok">{notice}</div>}

      <div className="stat-grid">
        <div className="stat"><div className="label">资产总数</div><div className="value">{data.asset_total}<small>件</small></div></div>
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

        <Card title="按领域分布">
          <div className="legend">
            {data.by_domain.map((d) => (
              <div className="legend-row" key={d.name}>
                <span>{d.name}</span>
                <div className="bar" style={{ width: `${Math.max((d.count / maxDomain) * 100, 1)}%` }} />
                <span className="muted">{d.count}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card title="按分类统计">
        {data.by_category.length === 0 ? <Empty /> : (
          <div className="legend">
            {data.by_category.map((c) => (
              <div className="legend-row" key={c.name}>
                <span>{c.name}</span>
                <div className="bar" style={{ width: `${Math.max((c.count / maxCat) * 100, 1)}%` }} />
                <span className="muted">{c.count}</span>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title={`到期预警（${days} 天内，共 ${data.due_soon.length} 项）`}>
        {data.due_soon.length === 0 ? <Empty text="暂无到期事项" /> : (
          <div className="table-wrap">
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
                      {it.days_left < 0
                        ? <Tag tone="danger">逾期 {Math.abs(it.days_left)} 天</Tag>
                        : <Tag tone="warn">{it.days_left} 天</Tag>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {canTrace && (
        <Card title={`导出记录（最近 ${logs.length} 条）`}>
          {logs.length === 0 ? <Empty text="暂无导出记录" /> : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>溯源码</th><th>导出人</th><th>数据域</th><th>记录数</th><th>导出时间</th><th>操作</th></tr>
                </thead>
                <tbody>
                  {logs.map((l) => (
                    <tr key={l.id}>
                      <td className="mono wm-code">{l.watermark}</td>
                      <td>{l.full_name || l.username}</td>
                      <td>{dictText(dict.data_scope, l.scope)}</td>
                      <td>{l.row_count}</td>
                      <td>{fmtTime(l.created_at)}</td>
                      <td><button className="link" onClick={() => openTrace(l.watermark)}>溯源</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      <Modal
        open={traceOpen}
        title="导出文件水印溯源"
        onClose={() => setTraceOpen(false)}
        width={520}
        footer={<>
          <Button variant="ghost" onClick={() => setTraceOpen(false)}>关闭</Button>
          <Button onClick={doTrace} disabled={!traceCode.trim()}>开始溯源</Button>
        </>}
      >
        <label className="field">
          <span className="field-label">水印溯源码</span>
          <input className="mono" placeholder="粘贴 Excel 页脚或文件属性中的溯源码"
            value={traceCode} onChange={(e) => setTraceCode(e.target.value)} />
        </label>
        <p className="muted" style={{ fontSize: 12, marginTop: -4 }}>
          打开可疑 Excel 后，右键查看「文件属性-备注」、列表页页脚，或最后一列（XFD 列）的隐藏内容。
        </p>

        {traceErr && <div className="alert">{traceErr}</div>}

        {traceRes && (traceRes.valid ? (
          <div className="trace-ok">
            <div className="trace-title">✓ 水印有效，来源可追溯</div>
            <div className="trace-rows">
              <span>导出人</span><b>{traceRes.full_name || traceRes.username}</b>
              <span>账号</span><b>{traceRes.username}</b>
              <span>数据域</span><b>{dictText(dict.data_scope, traceRes.scope)}</b>
              <span>记录数</span><b>{traceRes.row_count}</b>
              <span>导出时间</span><b>{traceRes.exported_at}</b>
              <span>溯源码</span><b className="wm-code">{traceCode.trim().toUpperCase()}</b>
            </div>
          </div>
        ) : (
          <div className="trace-bad">
            <div className="trace-title">✕ 未通过校验</div>
            {traceRes.message || '该溯源码不存在或已被篡改，无法追溯到合法导出记录。'}
          </div>
        ))}
      </Modal>
    </div>
  )
}
