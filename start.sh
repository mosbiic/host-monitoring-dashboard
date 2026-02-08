#!/bin/bash

# Host Monitoring Dashboard Startup Script
# 固定端口配置: 前端 3000, 后端 8081

set -e

# 固定端口
FRONTEND_PORT=3000
BACKEND_PORT=8081

echo "🚀 Starting Host Monitoring Dashboard..."
echo "   Frontend Port: $FRONTEND_PORT"
echo "   Backend Port: $BACKEND_PORT"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi

# Set default token if not set
if [ -z "$DASHBOARD_TOKEN" ]; then
    export DASHBOARD_TOKEN="mosbiic-dashboard-secure-token-2024"
    echo "⚠️  Using default token"
fi

# Install backend dependencies if needed
cd backend
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing backend dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

# Start backend in background
echo "🟢 Starting backend server on port $BACKEND_PORT..."
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Install frontend dependencies if needed
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend
echo "🟢 Starting frontend dev server on port $FRONTEND_PORT..."
npm run dev -- --port $FRONTEND_PORT &
FRONTEND_PID=$!

echo ""
echo "✅ Dashboard is starting up!"
echo ""
echo "📊 Frontend: http://localhost:$FRONTEND_PORT"
echo "🔌 Backend API: http://localhost:$BACKEND_PORT"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Handle shutdown
function cleanup {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $FRONTEND_PID 2>/dev/null || true
    kill $BACKEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup INT TERM

# Wait for both processes
wait
