# 园小助 · 幼儿园园务资产管理系统

一套面向幼儿园的园务资产管理系统，把玩具、教具、图书、教学设备、电器家具、体育器材、办公用品、生活用品、消防安防等资产统一数字化管理，覆盖 **台账 → 借还 → 盘点 → 巡检（消毒/安全检查）→ 教学预留 → 统计报表** 的完整闭环，并内置 **分权分域** 与 **数据加密**。

## 功能概览

| 模块 | 核心功能 |
| --- | --- |
| 登录与鉴权 | 账号密码登录、JWT 鉴权、角色与权限、数据范围 |
| 总览仪表盘 | 资产统计卡、状态分布、到期预警、待办 |
| 资产台账 | 资产 CRUD、自动编号、多条件筛选、分类树、领域标签、二维码贴纸、标签管理 |
| 借还登记 | 借出、归还、记录查询、逾期标记 |
| 盘点 | 发起盘点、扫码登记、差异统计、结束盘点 |
| 巡检 | 消毒/安全检查任务、按到期批量生成、完成登记、结果留痕 |
| 教学预留 | 可预留教具检索、预留申请、审批、结束 |
| 统计报表 | 资产总览与分布、到期预警汇总、Excel 导出（含暗水印溯源） |
| 系统管理 | 用户管理、组织与数据域维护（仅园长） |
| AI 资产机器人 | 自然语言问答资产情况（规则引擎 + 可选大模型） |

## 技术栈

- **后端**：Python ≥ 3.10、FastAPI、SQLAlchemy 2.0、SQLite、PyJWT、cryptography
- **前端**：Node.js ≥ 18、React 18、react-router-dom 6、axios、Vite 5
- **架构**：前后端分离，业务逻辑与数据统一收敛至后端

## 目录结构

```
kindergarten/
├── backend/            # FastAPI 后端
│   ├── app/
│   │   ├── core/       # 配置、数据库、安全、加密
│   │   ├── common/     # 权限依赖、数据域过滤
│   │   ├── db/         # 建表与示例数据初始化
│   │   └── modules/    # 按业务域划分的 router/service/models/schemas
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/           # React + Vite 前端
│   ├── src/
│   │   ├── api/  router/  layouts/  modules/  store/
│   ├── vercel.json
│   └── package.json
├── docs/               # 设计与测试文档
├── render.yaml         # Render 后端部署蓝图
└── README.md
```

## 本地运行

### 1. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows；macOS/Linux 使用 source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- 接口文档：http://127.0.0.1:8000/docs
- 首次启动会自动建表并写入示例数据（数据库文件 `backend/kindergarten.db`）

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev                        # 默认 http://127.0.0.1:5173
```

前端通过环境变量 `VITE_API_BASE` 访问后端（默认 `http://127.0.0.1:8000/api`）。

### 3. 演示账号

| 账号 | 密码 | 角色 | 数据范围 |
| --- | --- | --- | --- |
| admin | admin123 | 园长 | 全园 |
| logistics | admin123 | 后勤 | 本域及下级 |
| teacher | admin123 | 教师 | 仅本人 |
| caregiver | admin123 | 保育员 | 仅本人 |

## 环境变量

后端（见 `backend/.env.example`）：

| 变量 | 说明 |
| --- | --- |
| `SECRET_KEY` | 鉴权密钥（JWT / 二维码 / 导出水印共用），生产环境务必替换 |
| `DATA_ENCRYPTION_KEY` | 敏感字段 AES 加密密钥，变更后历史密文将无法解密 |
| `CORS_ORIGINS` | 允许跨域的前端地址，多个用逗号分隔 |
| `PUBLIC_BASE_URL` | 二维码扫码落地页基地址 |
| `DEEPSEEK_API_KEY` | 可选，配置后 AI 助手走大模型 |

前端（见 `frontend/.env.example`）：`VITE_API_BASE`。

## 部署到公网

### 后端 → Render

1. 在 [Render](https://render.com) 选择 **New > Blueprint**，关联本仓库，将按 `render.yaml` 自动创建 Web 服务。
2. 部署完成后，在服务 **Environment** 中补充：
   - `CORS_ORIGINS` = 前端公网地址（如 `https://xxx.vercel.app`）
   - `PUBLIC_BASE_URL` = 前端公网地址
3. 记录后端地址（形如 `https://xxx.onrender.com`）。

> 免费 plan 的磁盘为临时存储，每次重新部署/重启后 SQLite 数据会重置（服务启动会自动重新初始化示例数据）。如需持久化，请为服务挂载 Persistent Disk 并让数据库指向该目录。

### 前端 → Vercel

1. 在 [Vercel](https://vercel.com) **New Project** 导入本仓库，Root Directory 选择 `frontend`。
2. 添加环境变量 `VITE_API_BASE` = `https://<后端地址>/api`。
3. 部署完成后，将 Vercel 域名回填到后端 `CORS_ORIGINS` 与 `PUBLIC_BASE_URL`。

## 安全说明

- 分权：RBAC（用户 → 角色 → 权限点），接口级鉴权兜底
- 分域：`all / org / self` 三级数据范围，列表与详情强制过滤，跨域 403
- 密码：PBKDF2 加盐哈希，不可逆存储
- 敏感字段：手机号等 AES 加密落库；列表脱敏，仅本人可见明文
- 审计：导出等关键操作留痕，导出文件带暗水印可溯源

> ⚠️ 本项目默认携带演示数据与弱口令演示账号（`admin/admin123`），仅用于演示与体验。正式使用前请务必修改默认口令并替换所有开发用密钥。