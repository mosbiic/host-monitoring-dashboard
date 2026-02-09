# Monitoring Dashboard 认证配置指南

## 修复内容

### 1. 后端 (`backend/main.py`)
- 新增 `/api/auth/config` 端点，返回当前认证模式配置
- 前端可查询此端点决定显示登录表单还是 Cloudflare Access 加载状态

### 2. 前端 (`frontend/src/views/Login.vue`)
- 页面加载时先查询 `/api/auth/config`
- 根据配置决定行为：
  - **Cloudflare Access 模式**: 显示加载状态，等待 CF 自动认证
  - **本地 Token 模式**: 显示登录表单
  - **开发模式**: 尝试自动登录（无 Token 验证）

## 认证模式配置

### 模式 1: Cloudflare Access (生产环境)

编辑 `backend/.env`:
```env
CF_ACCESS_ENABLED=true
DASHBOARD_TOKEN=changeme  # 可选，CF 模式不检查此 Token
```

特点：
- 用户通过 Cloudflare Access 登录后自动访问 Dashboard
- 不需要输入本地 Token
- 后端验证 `CF-Access-Authenticated-User-Email` header

### 模式 2: 本地 Token (本地开发)

编辑 `backend/.env`:
```env
CF_ACCESS_ENABLED=false
DASHBOARD_TOKEN=your-secure-token
```

特点：
- 需要输入 Token 才能访问
- Token 保存在浏览器 localStorage
- 适合本地开发或没有 Cloudflare Access 的环境

### 模式 3: 开发自动登录 (快速开发)

编辑 `backend/.env`:
```env
CF_ACCESS_ENABLED=false
DASHBOARD_TOKEN=changeme  # 或删除此行
```

特点：
- 无需输入 Token 自动登录
- 仅用于本地开发
- 安全风险：任何人都可以访问

## 测试

运行测试脚本:
```bash
cd host-monitoring-dashboard
./test_auth.sh
```

## 部署后检查清单

1. **Cloudflare Access 模式**:
   - [ ] `CF_ACCESS_ENABLED=true` 已设置
   - [ ] Cloudflare Tunnel 正确配置
   - [ ] Cloudflare Access 应用策略已配置
   - [ ] 访问页面时自动跳转到 CF 登录页

2. **本地 Token 模式**:
   - [ ] `CF_ACCESS_ENABLED=false` 已设置
   - [ ] `DASHBOARD_TOKEN` 设置为安全随机字符串
   - [ ] 访问页面时显示 Token 输入框

3. **开发模式**:
   - [ ] `DASHBOARD_TOKEN=changeme` 或删除
   - [ ] 访问页面时自动跳转到 Dashboard
