import { useEffect, useState } from 'react'

import { assetApi, borrowApi } from '../../api'
import { errMsg } from '../../api/client'
import Confirm from '../../components/Confirm'
import Modal from '../../components/Modal'
import { Button, Card, Empty, Field, Loading, Tag, fmtDate, fmtTime } from '../../components/ui'
import { useDict } from '../../store/dict'

const emptyForm = { asset_id: '', due_at: '', note: '' }

export default function Borrow() {
  const dict = useDict()
  const [rows, setRows] = useState(null)
  const [assets, setAssets] = useState([])
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')

  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [formErr, setFormErr] = useState('')
  const [returnRow, setReturnRow] = useState(null)

  const load = () => {
    const params = {}
    if (status) params.status = status
    borrowApi.list(params).then(setRows).catch((e) => setError(errMsg(e)))
  }

  useEffect(() => { load() /* eslint-disable-next-line */ }, [status])

  const openCreate = () => {
    setForm(emptyForm)
    setFormErr('')
    setOpen(true)
    assetApi.list({ status: 'in_stock' }).then(setAssets).catch((e) => setFormErr(errMsg(e)))
  }

  const submit = async () => {
    setFormErr('')
    if (!form.asset_id) return setFormErr('请选择要借出的资产')
    const payload = { asset_id: Number(form.asset_id), due_at: form.due_at || null, note: form.note }
    try {
      await borrowApi.create(payload)
      setOpen(false)
      load()
    } catch (e) {
      setFormErr(errMsg(e))
    }
  }

  const doReturn = async () => {
    try {
      await borrowApi.returnAsset(returnRow.id)
      setReturnRow(null)
      load()
    } catch (e) {
      alert(errMsg(e))
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>借还登记</h2>
          <div className="sub">扫码/选择资产借出，归还后自动释放库存</div>
        </div>
        <Button onClick={openCreate}>+ 借出登记</Button>
      </div>

      {error && <div className="alert">{error}</div>}

      <Card className="mb0">
        <div className="toolbar">
          <select style={{ maxWidth: 160 }} value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">全部状态</option>
            {dict.borrow_status.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
          </select>
          <Button variant="ghost" size="sm" onClick={load}>刷新</Button>
        </div>

        {!rows ? <Loading /> : rows.length === 0 ? <Empty /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>资产</th><th>借用人</th><th>借出时间</th><th>应还日期</th>
                  <th>归还时间</th><th>状态</th><th>备注</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td>{r.asset_name}</td>
                    <td>{r.borrower_name}</td>
                    <td>{fmtTime(r.borrow_at)}</td>
                    <td>{fmtDate(r.due_at)}</td>
                    <td>{fmtTime(r.return_at)}</td>
                    <td><Tag tone={r.status_tone}>{r.status_text || r.status}</Tag></td>
                    <td>{r.note || '—'}</td>
                    <td>
                      {r.status === 'borrowing' && (
                        <button className="link" onClick={() => setReturnRow(r)}>归还</button>
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
        title="借出登记"
        onClose={() => setOpen(false)}
        width={520}
        footer={<>
          <Button variant="ghost" onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={submit}>确认借出</Button>
        </>}
      >
        {formErr && <div className="alert">{formErr}</div>}
        <Field label="资产" required>
          <select value={form.asset_id} onChange={(e) => setForm({ ...form, asset_id: e.target.value })}>
            <option value="">请选择（仅显示在库资产）</option>
            {assets.map((a) => <option key={a.id} value={a.id}>{a.code} · {a.name}</option>)}
          </select>
        </Field>
        <Field label="应还日期">
          <input type="date" value={form.due_at} onChange={(e) => setForm({ ...form, due_at: e.target.value })} />
        </Field>
        <Field label="备注">
          <textarea value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
        </Field>
      </Modal>

      <Confirm
        open={!!returnRow}
        title="归还确认"
        text={`确认归还资产「${returnRow?.asset_name}」？`}
        okText="确认归还"
        onOk={doReturn}
        onCancel={() => setReturnRow(null)}
      />
    </div>
  )
}
