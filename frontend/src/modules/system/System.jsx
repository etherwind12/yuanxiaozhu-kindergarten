import { useEffect, useMemo, useState } from 'react'

import { authApi, orgApi } from '../../api'
import { errMsg } from '../../api/client'
import Modal from '../../components/Modal'
import { Button, Card, Empty, Field, Loading, Tag, fmtTime } from '../../components/ui'
import { useAuth } from '../../store/auth'
import { dictText, useDict } from '../../store/dict'

function flattenOrgs(list, depth = 0, out = []) {
  list.forEach((u) => {
    out.push({ id: u.id, label: `${'　'.repeat(depth)}${u.name}`, type: u.type, parent_id: u.parent_id })
    if (u.children?.length) flattenOrgs(u.children, depth + 1, out)
  })
  return out
}

const emptyUser = {
  username: '', password: '', full_name: '', role: 'teacher',
  phone: '', org_unit_id: '', data_scope: 'self', is_active: true,
}
const emptyOrg = { name: '', parent_id: '', type: 'class' }

export default function System() {
  const { user: me, roleName } = useAuth()
  const dict = useDict()
  const [tab, setTab] = useState('users')
  const [error, setError] = useState('')

  const [users, setUsers] = useState(null)
  const [orgs, setOrgs] = useState([])

  const [userOpen, setUserOpen] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [userForm, setUserForm] = useState(emptyUser)
  const [userErr, setUserErr] = useState('')

  const [orgOpen, setOrgOpen] = useState(false)
  const [editingOrg, setEditingOrg] = useState(null)
  const [orgForm, setOrgForm] = useState(emptyOrg)
  const [orgErr, setOrgErr] = useState('')

  const orgOptions = useMemo(() => flattenOrgs(orgs), [orgs])
  const orgName = useMemo(() => Object.fromEntries(orgOptions.map((o) => [o.id, o.label.replace(/^[　 ]+/, '')])), [orgOptions])

  const loadUsers = () => authApi.listUsers().then(setUsers).catch((e) => setError(errMsg(e)))
  const loadOrgs = () => orgApi.tree().then(setOrgs).catch((e) => setError(errMsg(e)))

  useEffect(() => { loadUsers(); loadOrgs() }, [])

  const openCreateUser = () => {
    setEditingUser(null)
    setUserForm(emptyUser)
    setUserErr('')
    setUserOpen(true)
  }

  const openEditUser = (u) => {
    setEditingUser(u)
    setUserForm({
      username: u.username, password: '', full_name: u.full_name, role: u.role,
      phone: '', org_unit_id: u.org_unit_id ?? '', data_scope: u.data_scope,
      is_active: u.is_active,
    })
    setUserErr('')
    setUserOpen(true)
  }

  const submitUser = async () => {
    setUserErr('')
    const payload = { ...userForm, org_unit_id: userForm.org_unit_id === '' ? null : Number(userForm.org_unit_id) }
    try {
      if (editingUser) {
        delete payload.username
        delete payload.password
        if (userForm.password) payload.password = userForm.password
        if (!userForm.phone) delete payload.phone
        await authApi.updateUser(editingUser.id, payload)
      } else {
        if (!payload.username) return setUserErr('请填写登录账号')
        if (!payload.password) return setUserErr('请填写初始密码（至少 6 位）')
        await authApi.createUser(payload)
      }
      setUserOpen(false)
      loadUsers()
    } catch (e) {
      setUserErr(errMsg(e))
    }
  }

  const openCreateOrg = (parent = null) => {
    setEditingOrg(null)
    setOrgForm({ ...emptyOrg, parent_id: parent ? parent.id : '', type: parent ? (parent.type === 'building' ? 'class' : 'building') : 'park' })
    setOrgErr('')
    setOrgOpen(true)
  }

  const openEditOrg = (unit) => {
    setEditingOrg(unit)
    setOrgForm({ name: unit.name, parent_id: unit.parent_id ?? '', type: unit.type })
    setOrgErr('')
    setOrgOpen(true)
  }

  const submitOrg = async () => {
    setOrgErr('')
    if (!orgForm.name.trim()) return setOrgErr('请填写名称')
    const payload = {
      name: orgForm.name.trim(),
      parent_id: orgForm.parent_id === '' ? null : Number(orgForm.parent_id),
      type: orgForm.type,
    }
    try {
      if (editingOrg) await orgApi.update(editingOrg.id, payload)
      else await orgApi.create(payload)
      setOrgOpen(false)
      loadOrgs()
    } catch (e) {
      setOrgErr(errMsg(e))
    }
  }

  const renderOrgRows = (list, depth = 0) =>
    list.flatMap((u) => [
      <tr key={u.id}>
        <td>{'　'.repeat(depth)}{depth ? '└ ' : ''}{u.name}</td>
        <td><Tag>{dictText(dict.org_type, u.type)}</Tag></td>
        <td>
          <div className="row-actions">
            <button className="link" onClick={() => openEditOrg(u)}>编辑</button>
            {u.type !== 'class' && <button className="link" onClick={() => openCreateOrg(u)}>加下级</button>}
          </div>
        </td>
      </tr>,
      ...(u.children?.length ? renderOrgRows(u.children, depth + 1) : []),
    ])

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>系统管理</h2>
          <div className="sub">用户与功能权限、组织数据域维护</div>
        </div>
        {tab === 'users'
          ? <Button onClick={openCreateUser}>+ 新建用户</Button>
          : <Button onClick={() => openCreateOrg(null)}>+ 新建组织域</Button>}
      </div>

      {error && <div className="alert">{error}</div>}

      <div className="tabs">
        <button className={`tab${tab === 'users' ? ' active' : ''}`} onClick={() => setTab('users')}>用户管理</button>
        <button className={`tab${tab === 'orgs' ? ' active' : ''}`} onClick={() => setTab('orgs')}>组织与数据域</button>
      </div>

      {tab === 'users' && (
        <Card className="mb0">
          {!users ? <Loading /> : users.length === 0 ? <Empty /> : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>账号</th><th>姓名</th><th>角色</th><th>数据范围</th>
                    <th>归属域</th><th>手机号</th><th>状态</th><th>创建时间</th><th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td className="mono">{u.username}{u.id === me?.id && <Tag tone="info">我</Tag>}</td>
                      <td>{u.full_name || '—'}</td>
                      <td><Tag tone="info">{roleName(u.role)}</Tag></td>
                      <td>{dictText(dict.data_scope, u.data_scope)}</td>
                      <td>{orgName[u.org_unit_id] || '—'}</td>
                      <td className="mono">{u.phone || '—'}</td>
                      <td>{u.is_active ? <Tag tone="ok">启用</Tag> : <Tag tone="muted">停用</Tag>}</td>
                      <td>{fmtTime(u.created_at)}</td>
                      <td><button className="link" onClick={() => openEditUser(u)}>编辑</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {tab === 'orgs' && (
        <Card className="mb0">
          {orgs.length === 0 ? <Empty /> : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>名称</th><th>类型</th><th>操作</th></tr>
                </thead>
                <tbody>{renderOrgRows(orgs)}</tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      <Modal
        open={userOpen}
        title={editingUser ? `编辑用户 · ${editingUser.username}` : '新建用户'}
        onClose={() => setUserOpen(false)}
        width={560}
        footer={<>
          <Button variant="ghost" onClick={() => setUserOpen(false)}>取消</Button>
          <Button onClick={submitUser}>{editingUser ? '保存' : '创建'}</Button>
        </>}
      >
        {userErr && <div className="alert">{userErr}</div>}
        <div className="grid-2">
          <Field label="登录账号" required={!editingUser}>
            <input value={userForm.username} disabled={!!editingUser}
              onChange={(e) => setUserForm({ ...userForm, username: e.target.value })} />
          </Field>
          <Field label={editingUser ? '重置密码（留空不改）' : '初始密码'} required={!editingUser}>
            <input type="password" value={userForm.password} placeholder="至少 6 位"
              onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} />
          </Field>
          <Field label="姓名">
            <input value={userForm.full_name} onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })} />
          </Field>
          <Field label="角色">
            <select value={userForm.role} onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}>
              {dict.role.map((r) => <option key={r.value} value={r.value}>{r.name}</option>)}
            </select>
          </Field>
          <Field label="手机号">
            <input value={userForm.phone} placeholder={editingUser ? '留空则不变（密文存储）' : '密文存储'}
              onChange={(e) => setUserForm({ ...userForm, phone: e.target.value })} />
          </Field>
          <Field label="数据范围">
            <select value={userForm.data_scope} onChange={(e) => setUserForm({ ...userForm, data_scope: e.target.value })}>
              {dict.data_scope.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
            </select>
          </Field>
          <Field label="归属数据域">
            <select value={userForm.org_unit_id} onChange={(e) => setUserForm({ ...userForm, org_unit_id: e.target.value })}>
              <option value="">未指定</option>
              {orgOptions.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
            </select>
          </Field>
          {editingUser && (
            <Field label="账号状态">
              <select value={String(userForm.is_active)}
                onChange={(e) => setUserForm({ ...userForm, is_active: e.target.value === 'true' })}>
                <option value="true">启用</option>
                <option value="false">停用</option>
              </select>
            </Field>
          )}
        </div>
      </Modal>

      <Modal
        open={orgOpen}
        title={editingOrg ? `编辑组织域 · ${editingOrg.name}` : '新建组织域'}
        onClose={() => setOrgOpen(false)}
        footer={<>
          <Button variant="ghost" onClick={() => setOrgOpen(false)}>取消</Button>
          <Button onClick={submitOrg}>{editingOrg ? '保存' : '创建'}</Button>
        </>}
      >
        {orgErr && <div className="alert">{orgErr}</div>}
        <Field label="名称" required>
          <input value={orgForm.name} onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })} />
        </Field>
        <Field label="类型">
          <select value={orgForm.type} onChange={(e) => setOrgForm({ ...orgForm, type: e.target.value })}>
            {dict.org_type.map((o) => <option key={o.value} value={o.value}>{o.text}</option>)}
          </select>
        </Field>
        <Field label="上级组织域">
          <select value={orgForm.parent_id} onChange={(e) => setOrgForm({ ...orgForm, parent_id: e.target.value })}>
            <option value="">无（顶级园区）</option>
            {orgOptions.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
          </select>
        </Field>
      </Modal>
    </div>
  )
}
