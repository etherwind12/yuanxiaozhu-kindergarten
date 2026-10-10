import { client } from './client'

export const authApi = {
  login: (username, password) => client.post('/auth/login', { username, password }).then((r) => r.data),
  me: () => client.get('/auth/me').then((r) => r.data),
  listUsers: () => client.get('/auth/users').then((r) => r.data),
  createUser: (data) => client.post('/auth/users', data).then((r) => r.data),
  updateUser: (id, data) => client.patch(`/auth/users/${id}`, data).then((r) => r.data),
}

export const orgApi = {
  tree: () => client.get('/org/units').then((r) => r.data),
  create: (data) => client.post('/org/units', data).then((r) => r.data),
  update: (id, data) => client.patch(`/org/units/${id}`, data).then((r) => r.data),
}

export const assetApi = {
  list: (params) => client.get('/assets', { params }).then((r) => r.data),
  get: (id) => client.get(`/assets/${id}`).then((r) => r.data),
  create: (data) => client.post('/assets', data).then((r) => r.data),
  update: (id, data) => client.patch(`/assets/${id}`, data).then((r) => r.data),
  remove: (id) => client.delete(`/assets/${id}`).then((r) => r.data),
  categories: () => client.get('/assets/categories').then((r) => r.data),
  createCategory: (data) => client.post('/assets/categories', data).then((r) => r.data),
  tags: () => client.get('/assets/tags').then((r) => r.data),
  createTag: (data) => client.post('/assets/tags', data).then((r) => r.data),
  updateTag: (id, data) => client.patch(`/assets/tags/${id}`, data).then((r) => r.data),
  removeTag: (id) => client.delete(`/assets/tags/${id}`).then((r) => r.data),
  // 二维码贴纸（PNG blob）与扫码验签
  qrcode: (id) => client.get(`/assets/${id}/qrcode`, { responseType: 'blob' }),
  scan: (token) => client.get(`/assets/scan/${token}`).then((r) => r.data),
}

export const borrowApi = {
  list: (params) => client.get('/borrow', { params }).then((r) => r.data),
  create: (data) => client.post('/borrow', data).then((r) => r.data),
  returnAsset: (id) => client.post(`/borrow/${id}/return`).then((r) => r.data),
}

export const inventoryApi = {
  list: () => client.get('/inventory').then((r) => r.data),
  create: (data) => client.post('/inventory', data).then((r) => r.data),
  get: (id) => client.get(`/inventory/${id}`).then((r) => r.data),
  items: (id) => client.get(`/inventory/${id}/items`).then((r) => r.data),
  scan: (id, data) => client.post(`/inventory/${id}/scan`, data).then((r) => r.data),
  finish: (id) => client.post(`/inventory/${id}/finish`).then((r) => r.data),
}

export const inspectionApi = {
  list: (params) => client.get('/inspection', { params }).then((r) => r.data),
  create: (data) => client.post('/inspection', data).then((r) => r.data),
  generateFromDue: (withinDays = 7) =>
    client.post('/inspection/generate-from-due', null, { params: { within_days: withinDays } }).then((r) => r.data),
  records: (id) => client.get(`/inspection/${id}/records`).then((r) => r.data),
  complete: (id, data) => client.post(`/inspection/${id}/complete`, data).then((r) => r.data),
}

export const teachingApi = {
  available: (params) => client.get('/teaching/available', { params }).then((r) => r.data),
  list: (params) => client.get('/teaching', { params }).then((r) => r.data),
  create: (data) => client.post('/teaching', data).then((r) => r.data),
  approve: (id) => client.post(`/teaching/${id}/approve`).then((r) => r.data),
  reject: (id) => client.post(`/teaching/${id}/reject`).then((r) => r.data),
  finish: (id) => client.post(`/teaching/${id}/finish`).then((r) => r.data),
}

export const reportApi = {
  overview: (withinDays = 7) => client.get('/report/overview', { params: { within_days: withinDays } }).then((r) => r.data),
  // 返回完整响应对象，便于读取水印码响应头与文件名
  exportExcel: (withinDays = 7) =>
    client.get('/report/export', { params: { within_days: withinDays }, responseType: 'blob' }),
  trace: (code) => client.post('/report/watermark/trace', { code }).then((r) => r.data),
  exportLogs: () => client.get('/report/export-logs').then((r) => r.data),
}

export const assistantApi = {
  chat: (message) => client.post('/assistant/chat', { message }).then((r) => r.data),
}

export const metaApi = {
  // 系统字典：状态 / 类型 / 领域 / 数据域 / 组织类型 / 角色权限
  dictionaries: () => client.get('/meta/dictionaries').then((r) => r.data),
}
