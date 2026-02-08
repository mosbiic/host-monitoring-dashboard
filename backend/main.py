from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import psutil
import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Configuration
DASHBOARD_TOKEN = os.getenv("DASHBOARD_TOKEN", "changeme")
DATA_RETENTION_HOURS = 24 * 7  # 7 days

# Global state
metrics_history: List[Dict] = []
active_connections: List[WebSocket] = []

# Pydantic models
class SystemMetrics(BaseModel):
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    boot_time: float

class ProcessStatus(BaseModel):
    name: str
    running: bool
    pid: Optional[int] = None
    port: Optional[int] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    uptime_seconds: Optional[float] = None

class ProcessMetrics(BaseModel):
    timestamp: float
    processes: List[ProcessStatus]

class HealthResponse(BaseModel):
    status: str
    timestamp: float

# Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != DASHBOARD_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

def get_system_metrics() -> SystemMetrics:
    """Collect current system metrics using psutil"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    boot_time = psutil.boot_time()
    
    return SystemMetrics(
        timestamp=time.time(),
        cpu_percent=round(cpu_percent, 2),
        memory_percent=round(memory.percent, 2),
        memory_used_gb=round(memory.used / (1024**3), 2),
        memory_total_gb=round(memory.total / (1024**3), 2),
        disk_percent=round(disk.percent, 2),
        disk_used_gb=round(disk.used / (1024**3), 2),
        disk_total_gb=round(disk.total / (1024**3), 2),
        boot_time=boot_time
    )

def check_port_open(port: int) -> bool:
    """Check if a port is open/listening"""
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return True
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def find_process_by_name(name: str) -> Optional[psutil.Process]:
    """Find a process by name"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name.lower() in proc.info['name'].lower():
                return psutil.Process(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def get_process_metrics() -> ProcessMetrics:
    """Collect OpenClaw and related process metrics"""
    processes = []
    now = time.time()
    
    # Check OpenClaw Gateway (port 18789)
    gateway_running = check_port_open(18789)
    gateway_pid = None
    gateway_cpu = None
    gateway_mem = None
    gateway_uptime = None
    
    if gateway_running:
        # Find the process listening on port 18789
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == 18789 and conn.status == 'LISTEN':
                try:
                    proc = psutil.Process(conn.pid)
                    gateway_pid = conn.pid
                    gateway_cpu = round(proc.cpu_percent(interval=0.1), 2)
                    gateway_mem = round(proc.memory_percent(), 2)
                    gateway_uptime = now - proc.create_time()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                break
    
    processes.append(ProcessStatus(
        name="OpenClaw Gateway",
        running=gateway_running,
        pid=gateway_pid,
        port=18789,
        cpu_percent=gateway_cpu,
        memory_percent=gateway_mem,
        uptime_seconds=round(gateway_uptime, 2) if gateway_uptime else None
    ))
    
    # Check OpenClaw Node (process name contains 'openclaw' and 'node')
    node_proc = None
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'openclaw' in proc.info['name'].lower() and 'node' in cmdline.lower():
                node_proc = psutil.Process(proc.info['pid'])
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if node_proc:
        try:
            processes.append(ProcessStatus(
                name="OpenClaw Node",
                running=True,
                pid=node_proc.pid,
                cpu_percent=round(node_proc.cpu_percent(interval=0.1), 2),
                memory_percent=round(node_proc.memory_percent(), 2),
                uptime_seconds=round(now - node_proc.create_time(), 2)
            ))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            processes.append(ProcessStatus(name="OpenClaw Node", running=False))
    else:
        processes.append(ProcessStatus(name="OpenClaw Node", running=False))
    
    # Check Ollama (port 11434)
    ollama_running = check_port_open(11434)
    ollama_pid = None
    ollama_cpu = None
    ollama_mem = None
    ollama_uptime = None
    
    if ollama_running:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == 11434 and conn.status == 'LISTEN':
                try:
                    proc = psutil.Process(conn.pid)
                    ollama_pid = conn.pid
                    ollama_cpu = round(proc.cpu_percent(interval=0.1), 2)
                    ollama_mem = round(proc.memory_percent(), 2)
                    ollama_uptime = now - proc.create_time()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                break
    
    processes.append(ProcessStatus(
        name="Ollama",
        running=ollama_running,
        pid=ollama_pid,
        port=11434,
        cpu_percent=ollama_cpu,
        memory_percent=ollama_mem,
        uptime_seconds=round(ollama_uptime, 2) if ollama_uptime else None
    ))
    
    # Check Cloudflared (process name)
    cloudflared_proc = find_process_by_name("cloudflared")
    if cloudflared_proc:
        try:
            processes.append(ProcessStatus(
                name="Cloudflared",
                running=True,
                pid=cloudflared_proc.pid,
                cpu_percent=round(cloudflared_proc.cpu_percent(interval=0.1), 2),
                memory_percent=round(cloudflared_proc.memory_percent(), 2),
                uptime_seconds=round(now - cloudflared_proc.create_time(), 2)
            ))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            processes.append(ProcessStatus(name="Cloudflared", running=False))
    else:
        processes.append(ProcessStatus(name="Cloudflared", running=False))
    
    return ProcessMetrics(timestamp=now, processes=processes)

async def metrics_collector():
    """Background task to collect metrics periodically"""
    global metrics_history
    while True:
        try:
            system_metrics = get_system_metrics()
            process_metrics = get_process_metrics()
            
            combined = {
                "timestamp": system_metrics.timestamp,
                "system": system_metrics.model_dump(),
                "processes": [p.model_dump() for p in process_metrics.processes]
            }
            
            metrics_history.append(combined)
            
            # Keep only last 7 days of data
            cutoff = time.time() - (DATA_RETENTION_HOURS * 3600)
            metrics_history = [m for m in metrics_history if m["timestamp"] > cutoff]
            
            # Broadcast to all connected WebSocket clients
            await broadcast_metrics(combined)
            
            await asyncio.sleep(5)  # Collect every 5 seconds
        except Exception as e:
            print(f"Error in metrics collector: {e}")
            await asyncio.sleep(5)

async def broadcast_metrics(metrics: Dict):
    """Broadcast metrics to all connected WebSocket clients"""
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(metrics)
        except Exception:
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    collector_task = asyncio.create_task(metrics_collector())
    yield
    # Shutdown
    collector_task.cancel()

app = FastAPI(
    title="Host Monitoring Dashboard API",
    description="Real-time system and process monitoring API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files - serve frontend build
frontend_path = "/Users/mosbii/.openclaw/workspace/host-monitoring-dashboard/frontend/dist"
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

@app.get("/")
async def root():
    """Serve frontend HTML"""
    frontend_html = os.path.join(frontend_path, "index.html")
    if os.path.exists(frontend_html):
        return FileResponse(frontend_html)
    return HealthResponse(status="healthy", timestamp=time.time())

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", timestamp=time.time())

@app.get("/api/metrics/system", response_model=SystemMetrics)
async def get_current_system_metrics(token: str = Depends(verify_token)):
    """Get current system metrics"""
    return get_system_metrics()

@app.get("/api/metrics/processes", response_model=ProcessMetrics)
async def get_current_process_metrics(token: str = Depends(verify_token)):
    """Get current process metrics"""
    return get_process_metrics()

@app.get("/api/metrics/history")
async def get_metrics_history(
    hours: int = 24,
    token: str = Depends(verify_token)
):
    """Get historical metrics for the specified time period"""
    cutoff = time.time() - (hours * 3600)
    filtered_history = [m for m in metrics_history if m["timestamp"] > cutoff]
    return {
        "hours": hours,
        "data_points": len(filtered_history),
        "data": filtered_history
    }

@app.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await websocket.accept()
    
    # Verify token from query params or headers
    token = websocket.query_params.get("token")
    if token != DASHBOARD_TOKEN:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    active_connections.append(websocket)
    
    try:
        # Send current metrics immediately
        system_metrics = get_system_metrics()
        process_metrics = get_process_metrics()
        await websocket.send_json({
            "timestamp": system_metrics.timestamp,
            "system": system_metrics.model_dump(),
            "processes": [p.model_dump() for p in process_metrics.processes]
        })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Use timeout to allow periodic metrics updates even without client messages
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle ping/pong or other client messages
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
            except WebSocketDisconnect:
                break
            except Exception:
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
