import { useEffect, useState } from 'react'

import { inventoryApi } from '../../api'
import { errMsg } from '../../api/client'
import Confirm from '../../components/Confirm'
import Modal from '../../components/Modal'
import { Button, Card, Empty, Field, Loading, Tag, fmtTime } from '../../components/ui'
import { dictText, dictTone, useDict } from '../../store/dict'

export default function Inventory() {
  const dict = useDict()
  const [rows, setRows] = useState(null)
  const [error, setError] = useState('')

  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState({ title: '', note: '' })
  const [formErr, setFormErr] = useState('')

  const [current, setCurrent] = useState(null)
  const [items, setItems] = useState([])
  const [scan, setScan] = useState({ asset_id: '', actual_qty: 0, note: '' })
  const [scanErr, setScanErr] = useState('')
  const [askFinish, setAskFinish] = useState(false)

  const load = () => {
    inventoryApi.list().then(setRows).catch((e) => setError(errMsg(e)))
  }

  useEffect(() => { load() }, [])

  const openDetail = async (task) => {
    setCurrent(task)
    setItems([])
    setScan({ asset_id: '', actual_qty: 0, note: '' })
    setScanErr('')
    try {
      setItems(await inventoryApi.items(task.id))
    } catch (e) {
      setScanErr(errMsg(e))
    }
  }

  const refreshDetail = async (taskId) => {
    setItems(await inventoryApi.items(taskId))
    load()
  }

  const submitCreate = async () => {
    setFormErr('')
    if (!form.title.trim()) return setFormErr('请填写盘点任务名称')
    try {
      await inventoryApi.create({ title: form.title.trim(), note: form.note })
      setCreateOpen(false)
      setForm({ title: '', note: '' })
      load()
    } catch (e) {
      setFormErr(errMsg(e))
    }
  }

  const pickAsset = (val) => {
    const it = items.find((i) => String(i.asset_id) === val)
    setScan({ ...scan, asset_id: val, actual_qty: it ? it.expected_qty : 0 })
  }

  const submitScan = async () => {
    setScanErr('')
    if (!scan.asset_id) return setScanErr('请选择要登记的资产')
    try {
      await inventoryApi.scan(current.id, {
        asset_id: Number(scan.asset_id), actual_qty: Number(scan.actual_qty) || 0, note: scan.note,
      })
      setScan({ asset_id: '', actual_qty: 0, note: '' })
      refreshDetail(current.id)
    } catch (e) {
      setScanErr(errMsg(e))
    }
  }

  const doFinish = async () => {
    try {
      await inventoryApi.finish(current.id)
      setAskFinish(false)
      setCurrent(null)
      load()
    } catch (e) {
      alert(errMsg(e))
    }
  }

  const pending = items.filter((i) => i.result === 'pending')

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>盘点管理</h2>
          <div className="sub">发起盘点任务，扫码/逐项登记实际数量，自动生成差异</div>
        </div>
        <Button onClick={() => { setFormErr(''); setCreateOpen(true) }}>+ 发起盘点</Button>
      </div>

      {error && <div className="alert">{error}</div>}

      <Card className="mb0">
        {!rows ? <Loading /> : rows.length === 0 ? <Empty text="暂无盘点任务" /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>任务</th><th>发起人</th><th>发起时间</th><th>状态</th>
                  <th>进度</th><th>差异项</th><th>备注</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((t) => (
                  <tr key={t.id}>
                    <td><button className="link" onClick={() => openDetail(t)}>{t.title}</button></td>
                    <td>{t.created_by_name || '—'}</td>
                    <td>{fmtTime(t.created_at)}</td>
                    <td><Tag tone={dictTone(dict.inventory_task_status, t.status)}>{dictText(dict.inventory_task_status, t.status)}</Tag></td>
                    <td>{t.checked} / {t.total}</td>
                    <td>{t.diff_count > 0 ? <Tag tone="danger">{t.diff_count}</Tag> : '0'}</td>
                    <td>{t.note || '—'}</td>
                    <td><button className="link" onClick={() => openDetail(t)}>明细</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal
        open={createOpen}
        title="发起盘点任务"
        onClose={() => setCreateOpen(false)}
        footer={<>
          <Button variant="ghost" onClick={() => setCreateOpen(false)}>取消</Button>
          <Button onClick={submitCreate}>发起</Button>
        </>}
      >
        {formErr && <div className="alert">{formErr}</div>}
        <Field label="任务名称" required>
          <input value={form.title} placeholder="如 2026 年 10 月资产盘点"
            onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </Field>
        <Field label="备注">
          <textarea value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
        </Field>
        <p className="muted">系统将自动为当前数据域内的全部资产生成盘点明细。</p>
      </Modal>

      <Modal
        open={!!current}
        title={current ? `盘点明细 · ${current.title}` : ''}
        onClose={() => setCurrent(null)}
        width={720}
        footer={current?.status === 'open'
          ? <Button variant="danger" onClick={() => setAskFinish(true)}>结束盘点</Button>
          : null}
      >
        {current && (
          <>
            {current.status === 'open' && (
              <div className="card" style={{ marginBottom: 12 }}>
                <div className="card-head"><h3>登记实际数量</h3></div>
                <div className="card-body">
                  {scanErr && <div className="alert">{scanErr}</div>}
                  <div className="toolbar">
                    <select style={{ minWidth: 240 }} value={scan.asset_id} onChange={(e) => pickAsset(e.target.value)}>
                      <option value="">选择资产（仅显示未盘项）</option>
                      {pending.map((i) => (
                        <option key={i.id} value={i.asset_id}>{i.asset_code} · {i.asset_name}（应有 {i.expected_qty}）</option>
                      ))}
                    </select>
                    <input type="number" min="0" style={{ maxWidth: 110 }} value={scan.actual_qty}
                      onChange={(e) => setScan({ ...scan, actual_qty: e.target.value })} />
                    <input style={{ maxWidth: 180 }} placeholder="备注" value={scan.note}
                      onChange={(e) => setScan({ ...scan, note: e.target.value })} />
                    <Button size="sm" onClick={submitScan}>登记</Button>
                  </div>
                </div>
              </div>
            )}

            {items.length === 0 ? <Empty text="暂无盘点明细" /> : (
              <div className="table-wrap" style={{ maxHeight: 360, overflowY: 'auto' }}>
                <table>
                  <thead>
                    <tr><th>编号</th><th>资产</th><th>应有</th><th>实盘</th><th>结果</th><th>备注</th></tr>
                  </thead>
                  <tbody>
                    {items.map((i) => (
                      <tr key={i.id}>
                        <td className="mono">{i.asset_code}</td>
                        <td>{i.asset_name}</td>
                        <td>{i.expected_qty}</td>
                        <td>{i.actual_qty ?? '—'}</td>
                        <td><Tag tone={dictTone(dict.inventory_result, i.result)}>{dictText(dict.inventory_result, i.result)}</Tag></td>
                        <td>{i.note || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </Modal>

      <Confirm
        open={askFinish}
        title="结束盘点"
        text={`确认结束盘点任务「${current?.title}」？结束后不可再登记。`}
        okText="结束盘点"
        danger
        onOk={doFinish}
        onCancel={() => setAskFinish(false)}
      />
    </div>
  )
}
