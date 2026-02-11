#!/usr/bin/env python3
"""
Host Monitoring Dashboard - 生产环境启动脚本
使用 Python 同时托管后端 API 和前端静态文件
端口: 后端 18081, 前端 13000
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# 配置
PROJECT_DIR = Path.home() / "Projects" / "host-monitoring-dashboard"
BACKEND_PORT = 18082  # 使用不同端口避免冲突
FRONTEND_PORT = 13001  # 使用不同端口避免冲突
DASHBOARD_TOKEN = os.getenv("DASHBOARD_TOKEN", "mosbiic-dashboard-secure-token-2024")

# 全局进程
backend_proc = None
frontend_proc = None

def signal_handler(sig, frame):
    print("\n🛑 Shutting down...")
    if backend_proc:
        backend_proc.terminate()
    if frontend_proc:
        frontend_proc.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_backend():
    """启动后端服务"""
    backend_dir = PROJECT_DIR / "backend"
    env = os.environ.copy()
    env["BACKEND_PORT"] = str(BACKEND_PORT)
    env["DASHBOARD_TOKEN"] = DASHBOARD_TOKEN
    env["WS_ALLOW_NO_AUTH"] = "true"
    
    # 激活虚拟环境并启动
    cmd = f"cd {backend_dir} && source venv/bin/activate && python main.py"
    
    return subprocess.Popen(
        cmd,
        shell=True,
        executable="/bin/bash",
        cwd=backend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

def start_frontend():
    """启动前端静态文件服务"""
    frontend_dir = PROJECT_DIR / "frontend"
    dist_dir = frontend_dir / "dist"
    
    # 如果没有构建产物，先构建
    if not dist_dir.exists():
        print("📦 Building frontend...")
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
    
    # 使用 Python http.server 托管静态文件
    env = os.environ.copy()
    env["PORT"] = str(FRONTEND_PORT)
    
    return subprocess.Popen(
        [sys.executable, "-m", "http.server", str(FRONTEND_PORT), "--directory", str(dist_dir)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

def main():
    global backend_proc, frontend_proc
    
    print("🚀 Starting Host Monitoring Dashboard (Production)")
    print(f"   Backend: http://localhost:{BACKEND_PORT}")
    print(f"   Frontend: http://localhost:{FRONTEND_PORT}")
    print()
    
    # 启动后端
    print("🟢 Starting backend...")
    backend_proc = start_backend()
    time.sleep(3)
    
    # 启动前端
    print("🟢 Starting frontend...")
    frontend_proc = start_frontend()
    time.sleep(2)
    
    print()
    print("✅ Dashboard is running!")
    print(f"   Backend PID: {backend_proc.pid}")
    print(f"   Frontend PID: {frontend_proc.pid}")
    print()
    
    # 等待进程
    try:
        while True:
            backend_status = backend_proc.poll()
            frontend_status = frontend_proc.poll()
            
            if backend_status is not None:
                print(f"⚠️ Backend exited with code {backend_status}")
                break
            if frontend_status is not None:
                print(f"⚠️ Frontend exited with code {frontend_status}")
                break
                
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
