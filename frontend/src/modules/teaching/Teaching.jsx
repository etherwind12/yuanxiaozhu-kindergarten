import { useEffect, useState } from 'react'

import { teachingApi } from '../../api'
import { errMsg } from '../../api/client'
import Confirm from '../../components/Confirm'
import Modal from '../../components/Modal'
import { Button, Card, Empty, Field, Loading, Tag, fmtDate } from '../../components/ui'
import { useAuth } from '../../store/auth'
import { dictText, dictTone, useDict } from '../../store/dict'

export default function Teaching() {
  const { has } = useAuth()
  const dict = useDict()
  const canApprove = has('reserve:approve')

  const [avail, setAvail] = useState(null)
  const [availFilters, setAvailFilters] = useState({ use_date: '', domain: '', keyword: '' })
  const [error, setError] = useState('')

  const [rows, setRows] = useState(null)
  const [status, setStatus] = useState('')

  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ asset_id: '', course_title: '', use_date: '', quantity: 1, note: '' })
  const [formErr, setFormErr] = useState('')
  const [picked, setPicked] = useState(null)
  const [ask, setAsk] = useState(null)

  const searchAvail = () => {
    const params = {}
    Object.entries(availFilters).forEach(([k, v]) => { if (v) params[k] = v })
    teachingApi.available(params).then(setAvail).catch((e) => setError(errMsg(e)))
  }

  const loadRows = () => {
    const params = {}
    if (status) params.status = status
    teachingApi.list(params).then(setRows).catch((e) => setError(errMsg(e)))
  }

  useEffect(() => { searchAvail() /* eslint-disable-next-line */ }, [availFilters])
  useEffect(() => { loadRows() /* eslint-disable-next-line */ }, [status])

  const openReserve = (asset) => {
    setPicked(asset)
    setForm({
      asset_id: asset.id, course_title: '', use_date: availFilters.use_date || '',
      quantity: 1, note: '',
    })
    setFormErr('')
    setOpen(true)
  }

  const submit = async () => {
    setFormErr('')
    if (!form.course_title.trim()) return setFormErr('请填写课程/活动名称')
    if (!form.use_date) return setFormErr('请选择使用日期')
    const qty = Number(form.quantity)
    if (!qty || qty < 1) return setFormErr('预留数量至少为 1')
    if (picked && qty > picked.remaining_quantity)
      return setFormErr(`当日最多还可预留 ${picked.remaining_quantity} ${picked.unit || '件'}`)
    try {
      await teachingApi.create({
        asset_id: form.asset_id, course_title: form.course_title.trim(),
        use_date: form.use_date, quantity: qty, note: form.note,
      })
      setOpen(false)
      loadRows()
      searchAvail()
    } catch (e) {
      setFormErr(errMsg(e))
    }
  }

  const act = async () => {
    try {
      await ask.fn(ask.row.id)
      setAsk(null)
      loadRows()
      searchAvail()
    } catch (e) {
      alert(errMsg(e))
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>教学预留</h2>
          <div className="sub">按五大领域与使用日期检索可用教具，按数量预留、教学不冲突</div>
        </div>
      </div>

      {error && <div className="alert">{error}</div>}

      <Card title="可预留教具">
        <div className="toolbar">
          <input style={{ maxWidth: 200 }} placeholder="搜索教具名称" value={availFilters.keyword}
            onChange={(e) => setAvailFilters({ ...availFilters, keyword: e.target.value })} />
          <select style={{ maxWidth: 140 }} value={availFilters.domain}
            onChange={(e) => setAvailFilters({ ...availFilters, domain: e.target.value })}>
            <option value="">全部领域</option>
            {dict.domain.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
          </select>
          <input type="date" style={{ maxWidth: 160 }} value={availFilters.use_date}
            onChange={(e) => setAvailFilters({ ...availFilters, use_date: e.target.value })} />
          <Button variant="ghost" size="sm" onClick={() => setAvailFilters({ use_date: '', domain: '', keyword: '' })}>重置</Button>
        </div>

        {!avail ? <Loading /> : avail.length === 0 ? <Empty text="没有符合条件的可用教具" /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>编号</th><th>名称</th><th>分类</th><th>总量</th><th>当日可预留</th>
                  <th>领域标签</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                {avail.map((a) => (
                  <tr key={a.id}>
                    <td className="mono">{a.code}</td>
                    <td>{a.name}</td>
                    <td>{a.category?.name || '—'}</td>
                    <td>{a.quantity} {a.unit}</td>
                    <td>{a.remaining_quantity} {a.unit}</td>
                    <td>{(a.tags || []).map((t) => <Tag key={t.id}>{t.domain}</Tag>)}</td>
                    <td><button className="link" onClick={() => openReserve(a)}>预留</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card title="预留记录">
        <div className="toolbar">
          <select style={{ maxWidth: 150 }} value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">全部状态</option>
            {dict.reservation_status.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
          </select>
          <Button variant="ghost" size="sm" onClick={loadRows}>刷新</Button>
        </div>

        {!rows ? <Loading /> : rows.length === 0 ? <Empty text="暂无预留记录" /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>教具</th><th>课程/活动</th><th>申请人</th><th>使用日期</th><th>数量</th>
                  <th>状态</th><th>备注</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td>{r.asset_name}</td>
                    <td>{r.course_title}</td>
                    <td>{r.teacher_name}</td>
                    <td>{fmtDate(r.use_date)}</td>
                    <td>{r.quantity}</td>
                    <td><Tag tone={dictTone(dict.reservation_status, r.status)}>{dictText(dict.reservation_status, r.status)}</Tag></td>
                    <td>{r.note || '—'}</td>
                    <td>
                      {canApprove && (
                        <div className="row-actions">
                          {r.status === 'pending' && <>
                            <button className="link" onClick={() => setAsk({ fn: teachingApi.approve, row: r, label: '通过' })}>通过</button>
                            <button className="link" style={{ color: 'var(--danger)' }} onClick={() => setAsk({ fn: teachingApi.reject, row: r, label: '驳回' })}>驳回</button>
                          </>}
                          {r.status === 'approved' && (
                            <button className="link" onClick={() => setAsk({ fn: teachingApi.finish, row: r, label: '结束' })}>结束</button>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal
        open={open}
        title={picked ? `预留教具 · ${picked.name}` : '发起预留'}
        onClose={() => setOpen(false)}
        footer={<>
          <Button variant="ghost" onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={submit}>提交申请</Button>
        </>}
      >
        {formErr && <div className="alert">{formErr}</div>}
        <Field label="课程 / 活动名称" required>
          <input value={form.course_title} placeholder="如 大班科学活动《磁铁的秘密》"
            onChange={(e) => setForm({ ...form, course_title: e.target.value })} />
        </Field>
        <Field label="使用日期" required>
          <input type="date" value={form.use_date} onChange={(e) => setForm({ ...form, use_date: e.target.value })} />
        </Field>
        <Field
          label="预留数量"
          required
          hint={picked ? `该教具共 ${picked.quantity} ${picked.unit || '件'}，当日可预留 ${picked.remaining_quantity} ${picked.unit || '件'}` : ''}
        >
          <input type="number" min="1" max={picked?.remaining_quantity || undefined} value={form.quantity}
            onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
        </Field>
        <Field label="备注">
          <textarea value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
        </Field>
      </Modal>

      <Confirm
        open={!!ask}
        title="操作确认"
        text={`确认${ask?.label || ''}「${ask?.row?.asset_name}」的预留申请？`}
        onOk={act}
        onCancel={() => setAsk(null)}
      />
    </div>
  )
}
