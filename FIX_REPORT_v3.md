# 修复报告 - Monitoring Dashboard

## 修复时间
2025-02-08

## 修复问题

### 1. WebSocket 连接问题 (✅ 已修复)
**问题**: WebSocket 显示 disconnected，无法保持长连接

**原因**: 
- 后端发送 `ping` 文本消息保持连接
- 前端尝试用 `JSON.parse` 解析所有消息，导致解析错误

**修复**:
- 前端 (`stores/index.js`): 添加 ping/pong 消息处理，在 JSON 解析前检查消息类型
- 后端 (`main.py`): 优化 WebSocket 消息循环，正确处理客户端响应

### 2. 进程检测准确性问题 (✅ 已修复)
**问题**: OpenClaw Gateway/Node 实际运行但显示 stopped

**原因**:
- macOS 上这些进程的 `name` 字段是 `node` 而不是 `openclaw-*`
- 原代码只检查 cmdline，没有检查进程名

**修复**:
- 添加 `proc_name_patterns` 参数到 `find_process_by_cmdline_keywords()` 函数
- 同时匹配进程名和命令行参数

### 3. 其他进程检测修复
- **Monitoring Dashboard**: 改为先检测端口 8081，再检测 cmdline
- **Personal Dashboard**: 修复为检测 Python uvicorn 后端 (port 8000)，而非 Vite 前端

## 验证结果

```
✅ OpenClaw Gateway: pid=17745, port=18789
✅ OpenClaw Node: pid=89719
✅ OpenClaw TUI: pid=1430
✅ Ollama: pid=1121, port=11434
✅ Cloudflared: pid=20431
✅ Monitoring Dashboard: pid=21828, port=8081
✅ Knowledge Graph API: pid=14636, port=8000
✅ Knowledge Graph UI: pid=14675, port=5173
✅ Personal Dashboard: pid=14636, port=8000
```

所有进程现在都能正确检测，WebSocket 连接保持稳定。

## 提交记录
```
commit 59b83b9
Fix WebSocket connection and process detection issues
```

## 文件修改
- `backend/main.py` - 进程检测逻辑和 WebSocket 处理
- `frontend/src/stores/index.js` - WebSocket 消息处理
- `frontend/dist/` - 重新构建的前端文件
