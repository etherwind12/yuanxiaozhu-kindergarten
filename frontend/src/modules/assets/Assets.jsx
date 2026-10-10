import { useEffect, useMemo, useState } from 'react'

import { assetApi, orgApi } from '../../api'
import { errMsg } from '../../api/client'
import Confirm from '../../components/Confirm'
import Modal from '../../components/Modal'
import { Button, Card, Empty, Field, Loading, Tag, fmtDate } from '../../components/ui'
import { useAuth } from '../../store/auth'
import { dictText, dictTone, useDict } from '../../store/dict'

const emptyForm = {
  name: '', code: '', category_id: '', org_unit_id: '', quantity: 1, unit: '件',
  location: '', age_range: '', safety_level: '', purchase_date: '', disinfect_due: '',
  safety_check_due: '', remark: '', tag_ids: [],
}

function flattenCats(list, depth = 0, out = []) {
  list.forEach((c) => {
    out.push({ id: c.id, label: `${'　'.repeat(depth)}${depth ? '└ ' : ''}${c.name}`, kind: c.kind })
    if (c.children?.length) flattenCats(c.children, depth + 1, out)
  })
  return out
}

function flattenOrgs(list, depth = 0, out = []) {
  list.forEach((u) => {
    out.push({ id: u.id, label: `${'　'.repeat(depth)}${u.name}` })
    if (u.children?.length) flattenOrgs(u.children, depth + 1, out)
  })
  return out
}

export default function Assets() {
  const { has, user } = useAuth()
  const dict = useDict()
  const canWrite = has('asset:write')

  const [rows, setRows] = useState(null)
  const [cats, setCats] = useState([])
  const [tags, setTags] = useState([])
  const [orgs, setOrgs] = useState([])
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({ keyword: '', status: '', category_id: '', domain: '' })

  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formErr, setFormErr] = useState('')
  const [detail, setDetail] = useState(null)
  const [confirmDel, setConfirmDel] = useState(null)

  const [selected, setSelected] = useState([])
  const [stickers, setStickers] = useState(null)
  const [scanOpen, setScanOpen] = useState(false)
  const [scanInput, setScanInput] = useState('')
  const [scanRes, setScanRes] = useState(null)
  const [scanErr, setScanErr] = useState('')

  const [tagOpen, setTagOpen] = useState(false)
  const [tagForm, setTagForm] = useState({ id: null, name: '', domain: '' })
  const [tagErr, setTagErr] = useState('')
  const [confirmDelTag, setConfirmDelTag] = useState(null)

  const catOptions = useMemo(() => flattenCats(cats), [cats])
  const catName = useMemo(() => {
    const map = {}
    catOptions.forEach((c) => (map[c.id] = c.label.replace(/^[　└ ]+/, '')))
    return map
  }, [catOptions])
  const orgOptions = useMemo(() => flattenOrgs(orgs), [orgs])
  const orgName = useMemo(() => Object.fromEntries(orgOptions.map((o) => [o.id, o.label.replace(/^[　 ]+/, '')])), [orgOptions])

  const load = () => {
    const params = {}
    Object.entries(filters).forEach(([k, v]) => { if (v !== '' && v != null) params[k] = v })
    assetApi.list(params).then(setRows).catch((e) => setError(errMsg(e)))
  }

  useEffect(() => {
    Promise.all([assetApi.categories(), assetApi.tags(), orgApi.tree()])
      .then(([c, t, o]) => { setCats(c); setTags(t); setOrgs(o) })
      .catch((e) => setError(errMsg(e)))
  }, [])

  useEffect(() => { load() /* eslint-disable-next-line */ }, [filters])

  const loadTags = () => assetApi.tags().then(setTags).catch((e) => setError(errMsg(e)))

  const openTagMgr = () => {
    setTagForm({ id: null, name: '', domain: '' })
    setTagErr('')
    setTagOpen(true)
  }

  const editTag = (t) => {
    setTagForm({ id: t.id, name: t.name, domain: t.domain })
    setTagErr('')
  }

  const resetTagForm = () => setTagForm({ id: null, name: '', domain: '' })

  const submitTag = async () => {
    setTagErr('')
    const name = tagForm.name.trim()
    if (!name) return setTagErr('请填写标签名称')
    if (!tagForm.domain) return setTagErr('请选择所属领域')
    try {
      const payload = { name, domain: tagForm.domain }
      if (tagForm.id) await assetApi.updateTag(tagForm.id, payload)
      else await assetApi.createTag(payload)
      resetTagForm()
      loadTags()
      load()
    } catch (e) {
      setTagErr(errMsg(e))
    }
  }

  const doRemoveTag = async () => {
    try {
      await assetApi.removeTag(confirmDelTag.id)
      if (tagForm.id === confirmDelTag.id) resetTagForm()
      setConfirmDelTag(null)
      loadTags()
      load()
    } catch (e) {
      alert(errMsg(e))
    }
  }

  const openCreate = () => {
    setEditing(null)
    setForm({ ...emptyForm, org_unit_id: user?.org_unit_id ?? '' })
    setFormErr('')
    setOpen(true)
  }

  const openEdit = (row) => {
    setEditing(row)
    setForm({
      ...emptyForm, ...row,
      category_id: row.category?.id ?? '', org_unit_id: row.org_unit_id ?? '',
      purchase_date: row.purchase_date || '', disinfect_due: row.disinfect_due || '',
      safety_check_due: row.safety_check_due || '', tag_ids: (row.tags || []).map((t) => t.id),
    })
    setFormErr('')
    setOpen(true)
  }

  const submit = async () => {
    setFormErr('')
    const payload = { ...form }
    ;['category_id', 'org_unit_id', 'quantity'].forEach((k) => {
      if (payload[k] === '' || payload[k] == null) payload[k] = null
    })
    ;['purchase_date', 'disinfect_due', 'safety_check_due'].forEach((k) => { if (!payload[k]) payload[k] = null })
    if (payload.quantity == null) payload.quantity = 1
    if (editing) delete payload.code
    try {
      if (editing) await assetApi.update(editing.id, payload)
      else await assetApi.create(payload)
      setOpen(false)
      load()
    } catch (e) {
      setFormErr(errMsg(e))
    }
  }

  const remove = async () => {
    try {
      await assetApi.remove(confirmDel.id)
      setConfirmDel(null)
      load()
    } catch (e) {
      alert(errMsg(e))
    }
  }

  const toggleSelect = (id) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))
  const allSelected = !!rows?.length && selected.length === rows.length
  const toggleAll = () => setSelected(allSelected ? [] : (rows || []).map((r) => r.id))

  // 一物一码：批量取回贴纸 PNG（后端按资产签名生成，含溯源信息）
  const openStickers = async (list) => {
    if (!list.length) return
    setStickers({ loading: true, items: [] })
    const items = await Promise.all(
      list.map(async (r) => {
        try {
          const res = await assetApi.qrcode(r.id)
          return { id: r.id, code: r.code, name: r.name, url: URL.createObjectURL(res.data) }
        } catch {
          return { id: r.id, code: r.code, name: r.name, url: '' }
        }
      }),
    )
    setStickers({ loading: false, items })
  }

  const closeStickers = () => {
    (stickers?.items || []).forEach((it) => it.url && URL.revokeObjectURL(it.url))
    setStickers(null)
  }

  const doScan = async () => {
    setScanErr('')
    setScanRes(null)
    const raw = scanInput.trim()
    if (!raw) return
    const token = raw.includes('/s/') ? raw.split('/s/').pop().split(/[?#]/)[0] : raw
    try {
      setScanRes(await assetApi.scan(token))
    } catch (e) {
      setScanErr(errMsg(e))
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>资产台账</h2>
          <div className="sub">覆盖玩具、教具、图书、设备、消防等全类资产，一物一码</div>
        </div>
        {canWrite && <Button onClick={openCreate}>+ 新增资产</Button>}
      </div>

      {error && <div className="alert">{error}</div>}

      <Card className="mb0">
        <div className="toolbar">
          <input style={{ maxWidth: 220 }} placeholder="搜索名称 / 编号 / 位置" value={filters.keyword}
            onChange={(e) => setFilters({ ...filters, keyword: e.target.value })} />
          <select style={{ maxWidth: 150 }} value={filters.category_id}
            onChange={(e) => setFilters({ ...filters, category_id: e.target.value })}>
            <option value="">全部分类</option>
            {catOptions.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
          </select>
          <select style={{ maxWidth: 140 }} value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <option value="">全部状态</option>
            {dict.asset_status.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
          </select>
          <select style={{ maxWidth: 140 }} value={filters.domain}
            onChange={(e) => setFilters({ ...filters, domain: e.target.value })}>
            <option value="">全部领域</option>
            {dict.domain.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
          </select>
          <Button variant="ghost" size="sm" onClick={() => setFilters({ keyword: '', status: '', category_id: '', domain: '' })}>重置</Button>
          <span style={{ flex: 1 }} />
          <Button variant="ghost" size="sm" onClick={() => openStickers((rows || []).filter((r) => selected.includes(r.id)))} disabled={!selected.length}>
            批量打印贴纸{selected.length ? `（${selected.length}）` : ''}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => { setScanInput(''); setScanRes(null); setScanErr(''); setScanOpen(true) }}>
            扫码查询
          </Button>
          {canWrite && <Button variant="ghost" size="sm" onClick={openTagMgr}>标签管理</Button>}
        </div>

        {!rows ? <Loading /> : rows.length === 0 ? <Empty /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th className="check-col"><input type="checkbox" checked={allSelected} onChange={toggleAll} /></th>
                  <th>编号</th><th>名称</th><th>分类</th><th>数量</th><th>归属域</th>
                  <th>状态</th><th>消毒到期</th><th>安全检查到期</th><th>标签</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td className="check-col"><input type="checkbox" checked={selected.includes(r.id)} onChange={() => toggleSelect(r.id)} /></td>
                    <td className="mono">{r.code}</td>
                    <td><button className="link" onClick={() => setDetail(r)}>{r.name}</button></td>
                    <td>{r.category?.name || '—'}</td>
                    <td>{r.quantity} {r.unit}</td>
                    <td>{orgName[r.org_unit_id] || '—'}</td>
                    <td><Tag tone={dictTone(dict.asset_status, r.status)}>{dictText(dict.asset_status, r.status)}</Tag></td>
                    <td>{fmtDate(r.disinfect_due)}</td>
                    <td>{fmtDate(r.safety_check_due)}</td>
                    <td>{(r.tags || []).map((t) => <Tag key={t.id}>{t.name}</Tag>)}</td>
                    <td>
                      <div className="row-actions">
                        <button className="link" onClick={() => openStickers([r])}>二维码</button>
                        {canWrite && <button className="link" onClick={() => openEdit(r)}>编辑</button>}
                        {canWrite && <button className="link" style={{ color: 'var(--danger)' }} onClick={() => setConfirmDel(r)}>删除</button>}
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
        title={editing ? `编辑资产 · ${editing.code}` : '新增资产'}
        onClose={() => setOpen(false)}
        width={640}
        footer={<>
          <Button variant="ghost" onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={submit}>{editing ? '保存' : '创建'}</Button>
        </>}
      >
        {formErr && <div className="alert">{formErr}</div>}
        <div className="grid-2">
          <Field label="资产名称" required>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="资产编号">
            <input value={form.code || ''} disabled={!!editing} placeholder={editing ? '' : '留空自动生成 ZCxxxxx'}
              onChange={(e) => setForm({ ...form, code: e.target.value })} />
          </Field>
          <Field label="资产分类">
            <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
              <option value="">未分类</option>
              {catOptions.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
            </select>
          </Field>
          <Field label="归属数据域">
            <select value={form.org_unit_id} onChange={(e) => setForm({ ...form, org_unit_id: e.target.value })}>
              <option value="">默认（本人所属域）</option>
              {orgOptions.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
            </select>
          </Field>
          <Field label="数量">
            <input type="number" min="0" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
          </Field>
          <Field label="计量单位">
            <input value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
          </Field>
          <Field label="存放位置">
            <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
          </Field>
          <Field label="适龄段">
            <input placeholder="如 3-4" value={form.age_range} onChange={(e) => setForm({ ...form, age_range: e.target.value })} />
          </Field>
          <Field label="安全等级">
            <input placeholder="如 A / B" value={form.safety_level} onChange={(e) => setForm({ ...form, safety_level: e.target.value })} />
          </Field>
          <Field label="采购日期">
            <input type="date" value={form.purchase_date || ''} onChange={(e) => setForm({ ...form, purchase_date: e.target.value })} />
          </Field>
          <Field label="消毒到期">
            <input type="date" value={form.disinfect_due || ''} onChange={(e) => setForm({ ...form, disinfect_due: e.target.value })} />
          </Field>
          <Field label="安全检查到期">
            <input type="date" value={form.safety_check_due || ''} onChange={(e) => setForm({ ...form, safety_check_due: e.target.value })} />
          </Field>
        </div>
        <Field label="领域标签">
          <div className="flex wrap">
            {tags.map((t) => {
              const on = form.tag_ids.includes(t.id)
              return (
                <Button key={t.id} size="sm" variant={on ? 'primary' : 'ghost'} type="button"
                  onClick={() => setForm({ ...form, tag_ids: on ? form.tag_ids.filter((x) => x !== t.id) : [...form.tag_ids, t.id] })}>
                  {t.name}·{t.domain}
                </Button>
              )
            })}
          </div>
        </Field>
        <Field label="备注">
          <textarea value={form.remark} onChange={(e) => setForm({ ...form, remark: e.target.value })} />
        </Field>
      </Modal>

      <Modal open={!!detail} title="资产详情" onClose={() => setDetail(null)} width={560}>
        {detail && (
          <table>
            <tbody>
              <tr><th>编号</th><td className="mono">{detail.code}</td></tr>
              <tr><th>名称</th><td>{detail.name}</td></tr>
              <tr><th>分类</th><td>{detail.category?.name || '—'}</td></tr>
              <tr><th>归属域</th><td>{orgName[detail.org_unit_id] || '—'}</td></tr>
              <tr><th>数量</th><td>{detail.quantity} {detail.unit}</td></tr>
              <tr><th>状态</th><td><Tag tone={dictTone(dict.asset_status, detail.status)}>{dictText(dict.asset_status, detail.status)}</Tag></td></tr>
              <tr><th>位置</th><td>{detail.location || '—'}</td></tr>
              <tr><th>适龄段</th><td>{detail.age_range || '—'}</td></tr>
              <tr><th>安全等级</th><td>{detail.safety_level || '—'}</td></tr>
              <tr><th>消毒到期</th><td>{fmtDate(detail.disinfect_due)}</td></tr>
              <tr><th>安全检查到期</th><td>{fmtDate(detail.safety_check_due)}</td></tr>
              <tr><th>领域标签</th><td>{(detail.tags || []).map((t) => <Tag key={t.id}>{t.name}</Tag>)}</td></tr>
              <tr><th>备注</th><td>{detail.remark || '—'}</td></tr>
            </tbody>
          </table>
        )}
      </Modal>

      <Modal
        open={!!stickers}
        title="资产二维码贴纸"
        onClose={closeStickers}
        width={640}
        footer={<>
          <Button variant="ghost" onClick={closeStickers}>关闭</Button>
          <Button onClick={() => window.print()} disabled={!stickers?.items?.some((it) => it.url)}>打印贴纸</Button>
        </>}
      >
        {stickers?.loading ? <Loading text="正在生成贴纸…" /> : stickers?.items?.length ? (
          <div className="print-sheet">
            <div className="sticker-grid">
              {stickers.items.map((it) => (
                <div className="sticker-item" key={it.id}>
                  {it.url
                    ? <img src={it.url} alt={it.code} />
                    : <div className="sticker-empty">生成失败</div>}
                </div>
              ))}
            </div>
          </div>
        ) : <Empty text="未选择资产" />}
      </Modal>

      <Modal
        open={scanOpen}
        title="扫码查询"
        onClose={() => setScanOpen(false)}
        width={540}
        footer={<>
          <Button variant="ghost" onClick={() => setScanOpen(false)}>关闭</Button>
          <Button onClick={doScan} disabled={!scanInput.trim()}>查询</Button>
        </>}
      >
        <label className="field">
          <span className="field-label">二维码内容 / 落地链接</span>
          <input className="mono" placeholder="粘贴扫码得到的链接或令牌"
            value={scanInput} onChange={(e) => setScanInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') doScan() }} />
        </label>
        <p className="muted" style={{ fontSize: 12, marginTop: -4 }}>
          贴纸二维码指向公开只读页，扫码即可查看资产基础信息与验签结果。
        </p>

        {scanErr && <div className="alert">{scanErr}</div>}

        {scanRes && (scanRes.valid ? (
          <div className="trace-ok">
            <div className="trace-title">✓ 验签通过 · {scanRes.name}</div>
            <div className="trace-rows">
              <span>资产编号</span><b className="mono">{scanRes.code}</b>
              <span>当前状态</span><b>{scanRes.status_text || dictText(dict.asset_status, scanRes.status)}</b>
              <span>所属园所</span><b>{scanRes.org_name || '—'}</b>
              <span>存放位置</span><b>{scanRes.location || '—'}</b>
              <span>数量</span><b>{scanRes.quantity} {scanRes.unit}</b>
              <span>适龄段</span><b>{scanRes.age_range || '—'}</b>
            </div>
          </div>
        ) : (
          <div className="trace-bad">
            <div className="trace-title">✕ 验签失败</div>
            {scanRes.message || '二维码无效或已被篡改，请核验贴纸来源。'}
          </div>
        ))}
      </Modal>

      <Modal
        open={tagOpen}
        title="标签管理"
        onClose={() => setTagOpen(false)}
        width={560}
        footer={<Button variant="ghost" onClick={() => setTagOpen(false)}>关闭</Button>}
      >
        {tagErr && <div className="alert">{tagErr}</div>}
        <div className="toolbar" style={{ marginBottom: 12 }}>
          <input style={{ maxWidth: 200 }} placeholder="标签名称，如 绘画" value={tagForm.name}
            onChange={(e) => setTagForm({ ...tagForm, name: e.target.value })} />
          <select style={{ maxWidth: 150 }} value={tagForm.domain}
            onChange={(e) => setTagForm({ ...tagForm, domain: e.target.value })}>
            <option value="">所属领域</option>
            {dict.domain.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
          </select>
          <Button size="sm" onClick={submitTag}>{tagForm.id ? '保存' : '新增'}</Button>
          {tagForm.id && <Button variant="ghost" size="sm" onClick={resetTagForm}>取消</Button>}
        </div>
        {tags.length === 0 ? <Empty text="暂无标签" /> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>标签名称</th><th>所属领域</th><th>操作</th></tr></thead>
              <tbody>
                {tags.map((t) => (
                  <tr key={t.id}>
                    <td>{t.name}</td>
                    <td>{t.domain ? <Tag>{t.domain}</Tag> : '—'}</td>
                    <td>
                      <div className="row-actions">
                        <button className="link" onClick={() => editTag(t)}>编辑</button>
                        <button className="link" style={{ color: 'var(--danger)' }} onClick={() => setConfirmDelTag(t)}>删除</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="muted" style={{ fontSize: 12, marginTop: 8 }}>
          标签用于给资产打标与按领域筛选；删除标签会同时从相关资产上移除。
        </p>
      </Modal>

      <Confirm
        open={!!confirmDelTag}
        title="删除标签"
        text={`确认删除标签「${confirmDelTag?.name}」？删除后将同步从相关资产上移除该标签。`}
        okText="删除"
        danger
        onOk={doRemoveTag}
        onCancel={() => setConfirmDelTag(null)}
      />

      <Confirm
        open={!!confirmDel}
        title="删除确认"
        text={`确认删除资产「${confirmDel?.name}」？`}
        okText="删除"
        danger
        onOk={remove}
        onCancel={() => setConfirmDel(null)}
      />
    </div>
  )
}
