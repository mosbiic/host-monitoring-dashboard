#!/bin/bash

# Host Monitoring Dashboard - Production Startup Script
# 端口配置匹配 Cloudflare Tunnel: 前端 13000, 后端 18081

set -e

# 生产端口 (匹配 Cloudflare Tunnel)
FRONTEND_PORT=13000
BACKEND_PORT=18081

echo "🚀 Starting Host Monitoring Dashboard (Production)..."
echo "   Frontend Port: $FRONTEND_PORT"
echo "   Backend Port: $BACKEND_PORT"

# 设置 Token
export DASHBOARD_TOKEN="${DASHBOARD_TOKEN:-mosbiic-dashboard-secure-token-2024}"

# 项目目录
PROJECT_DIR="$HOME/Projects/host-monitoring-dashboard"
cd "$PROJECT_DIR"

# 启动后端
echo "🟢 Starting backend server on port $BACKEND_PORT..."
cd backend
source venv/bin/activate
# 使用环境变量覆盖端口
export BACKEND_PORT=$BACKEND_PORT
python main.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端 (生产构建)
echo "🟢 Starting frontend on port $FRONTEND_PORT..."
cd frontend
# 检查是否有生产构建
if [ ! -d "dist" ]; then
    echo "📦 Building frontend for production..."
    npm run build
fi
# 使用 http-server 启动静态文件 (更可靠)
npx http-server dist -p $FRONTEND_PORT --cors &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Dashboard is running!"
echo ""
echo "📊 Frontend: http://localhost:$FRONTEND_PORT"
echo "🔌 Backend API: http://localhost:$BACKEND_PORT"
echo ""
echo "Process IDs - Backend: $BACKEND_PID, Frontend: $FRONTEND_PID"
echo ""

# 保持运行
wait
