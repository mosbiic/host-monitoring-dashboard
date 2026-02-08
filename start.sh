#!/bin/bash

# Host Monitoring Dashboard Startup Script

echo "🚀 Starting Host Monitoring Dashboard..."

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
    export DASHBOARD_TOKEN="changeme"
    echo "⚠️  Using default token: changeme"
    echo "   Set DASHBOARD_TOKEN environment variable to change it"
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
echo "🟢 Starting backend server on port 8080..."
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
echo "🟢 Starting frontend dev server on port 3000..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Dashboard is starting up!"
echo ""
echo "📊 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Handle shutdown
function cleanup {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $FRONTEND_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Wait for both processes
wait
