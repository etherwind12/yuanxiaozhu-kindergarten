import { useEffect, useState } from 'react'

import { assetApi, authApi, inspectionApi } from '../../api'
import { errMsg } from '../../api/client'
import Modal from '../../components/Modal'
import { Button, Card, Empty, Field, Loading, Tag, fmtDate, fmtTime } from '../../components/ui'
import { useAuth } from '../../store/auth'
import { useDict } from '../../store/dict'

const emptyForm = { title: '', type: 'disinfect', asset_id: '', assignee_id: '', due_date: '', note: '' }

export default function Inspection() {
  const { has } = useAuth()
  const dict = useDict()
  const [rows, setRows] = useState(null)
  const [assets, setAssets] = useState([])
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({ type: '', status: '' })

  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [formErr, setFormErr] = useState('')

  const [records, setRecords] = useState(null)
  const [recordOpen, setRecordOpen] = useState(false)
  const [complete, setComplete] = useState(null)
  const [completeForm, setCompleteForm] = useState({ result: 'pass', note: '' })

  const load = () => {
    const params = {}
    Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v })
    inspectionApi.list(params).then(setRows).catch((e) => setError(errMsg(e)))
  }

  useEffect(() => {
    assetApi.list({}).then(setAssets).catch(() => {})
    if (has('user:manage')) authApi.listUsers().then(setUsers).catch(() => {})
    // eslint-disable-next-line
  }, [])

  useEffect(() => { load() /* eslint-disable-next-line */ }, [filters])

  const openCreate = () => { setForm(emptyForm); setFormErr(''); setOpen(true) }

  const submit = async () => {
    setFormErr('')
    if (!form.title.trim()) return setFormErr('请填写任务名称')
    const payload = {
      title: form.title.trim(), type: form.type,
      asset_id: form.asset_id ? Number(form.asset_id) : null,
      assignee_id: form.assignee_id ? Number(form.assignee_id) : null,
      due_date: form.due_date || null, note: form.note,
    }
    try {
      await inspectionApi.create(payload)
      setOpen(false)
      load()
    } catch (e) {
      setFormErr(errMsg(e))
    }
  }

  const generate = async () => {
    try {
      const created = await inspectionApi.generateFromDue(7)
      alert(`已按 7 天内到期项生成 ${created.length} 条巡检任务`)
      load()
    } catch (e) {
      alert(errMsg(e))
    }
  }

  const openRecords = async (task) => {
    setRecords({ task, list: null })
    setRecordOpen(true)
    try {
      setRecords({ task, list: await inspectionApi.records(task.id) })
    } catch (e) {
      setRecords({ task, list: [], error: errMsg(e) })
    }
  }

  const openComplete = (task) => {
    setComplete(task)
    setCompleteForm({ result: 'pass', note: '' })
  }

  const submitComplete = async () => {
    try {
      await inspectionApi.complete(complete.id, completeForm)
      setComplete(null)
      load()
    } catch (e) {
      alert(errMsg(e))
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>巡检预警</h2>
          <div className="sub">消毒与安全检查任务的到期提醒与完成闭环</div>
        </div>
        <div className="flex gap">
          <Button variant="ghost" onClick={generate}>按到期自动生成</Button>
          <Button onClick={openCreate}>+ 新建巡检</Button>
        </div>
      </div>

      {error && <div className="alert">{error}</div>}

      <Card className="mb0">
        <div className="toolbar">
          <select style={{ maxWidth: 150 }} value={filters.type} onChange={(e) => setFilters({ ...filters, type: e.target.value })}>
            <option value="">全部类型</option>
            {dict.inspection_type.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
          </select>
          <select style={{ maxWidth: 150 }} value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <option value="">全部状态</option>
            {dict.inspection_status.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
          </select>
          <Button variant="ghost" size="sm" onClick={() => setFilters({ type: '', status: '' })}>重置</Button>
        </div>

        {!rows ? <Loading /> : rows.length === 0 ? <Empty text="暂无巡检任务" /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>任务</th><th>类型</th><th>关联资产</th><th>负责人</th>
                  <th>到期日</th><th>状态</th><th>备注</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((t) => (
                  <tr key={t.id}>
                    <td>{t.title}</td>
                    <td><Tag tone={t.type_tone}>{t.type_text || t.type}</Tag></td>
                    <td>{t.asset_name || '—'}</td>
                    <td>{t.assignee_name || '—'}</td>
                    <td>{fmtDate(t.due_date)}</td>
                    <td><Tag tone={t.status_tone}>{t.status_text || t.status}</Tag></td>
                    <td>{t.note || '—'}</td>
                    <td>
                      <div className="row-actions">
                        <button className="link" onClick={() => openRecords(t)}>记录</button>
                        {t.status === 'pending' && <button className="link" onClick={() => openComplete(t)}>完成</button>}
                      </div>
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
        title="新建巡检任务"
        onClose={() => setOpen(false)}
        width={520}
        footer={<>
          <Button variant="ghost" onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={submit}>创建</Button>
        </>}
      >
        {formErr && <div className="alert">{formErr}</div>}
        <Field label="任务名称" required>
          <input value={form.title} placeholder="如 小一班玩教具消毒"
            onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </Field>
        <div className="grid-2">
          <Field label="类型">
            <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              {dict.inspection_type.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
            </select>
          </Field>
          <Field label="到期日">
            <input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
          </Field>
          <Field label="关联资产">
            <select value={form.asset_id} onChange={(e) => setForm({ ...form, asset_id: e.target.value })}>
              <option value="">不关联</option>
              {assets.map((a) => <option key={a.id} value={a.id}>{a.code} · {a.name}</option>)}
            </select>
          </Field>
          {has('user:manage') && (
            <Field label="负责人">
              <select value={form.assignee_id} onChange={(e) => setForm({ ...form, assignee_id: e.target.value })}>
                <option value="">不指定</option>
                {users.map((u) => <option key={u.id} value={u.id}>{u.full_name || u.username}</option>)}
              </select>
            </Field>
          )}
        </div>
        <Field label="备注">
          <textarea value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
        </Field>
      </Modal>

      <Modal
        open={!!complete}
        title={complete ? `完成巡检 · ${complete.title}` : ''}
        onClose={() => setComplete(null)}
        footer={<>
          <Button variant="ghost" onClick={() => setComplete(null)}>取消</Button>
          <Button onClick={submitComplete}>提交</Button>
        </>}
      >
        <Field label="检查结果">
          <select value={completeForm.result} onChange={(e) => setCompleteForm({ ...completeForm, result: e.target.value })}>
            {dict.inspection_result.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
          </select>
        </Field>
        <Field label="说明">
          <textarea value={completeForm.note} onChange={(e) => setCompleteForm({ ...completeForm, note: e.target.value })} />
        </Field>
      </Modal>

      <Modal
        open={recordOpen}
        title={records ? `巡检记录 · ${records.task.title}` : ''}
        onClose={() => setRecordOpen(false)}
        width={560}
      >
        {records && (records.list === null ? <Loading /> : records.list.length === 0 ? <Empty text="暂无巡检记录" /> : (
          <table>
            <thead>
              <tr><th>检查人</th><th>结果</th><th>说明</th><th>时间</th></tr>
            </thead>
            <tbody>
              {records.list.map((r) => (
                <tr key={r.id}>
                  <td>{r.checker_name || '—'}</td>
                  <td><Tag tone={r.result_tone}>{r.result_text || r.result}</Tag></td>
                  <td>{r.note || '—'}</td>
                  <td>{fmtTime(r.checked_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}
      </Modal>
    </div>
  )
}
