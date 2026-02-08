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
    cmdline: Optional[str] = None

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

def find_processes_by_name(name_patterns: List[str], exclude_patterns: List[str] = None) -> List[psutil.Process]:
    """Find processes matching any of the name patterns"""
    matches = []
    exclude_patterns = exclude_patterns or []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            proc_name = proc.info['name'] or ''
            cmdline = ' '.join(proc.info['cmdline'] or [])
            full_text = f"{proc_name} {cmdline}".lower()
            
            # Check if any pattern matches
            matches_pattern = any(pattern.lower() in full_text for pattern in name_patterns)
            
            # Check if any exclude pattern matches
            excluded = any(exclude.lower() in full_text for exclude in exclude_patterns)
            
            if matches_pattern and not excluded:
                matches.append(psutil.Process(proc.info['pid']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return matches

def find_process_by_port(port: int) -> Optional[psutil.Process]:
    """Find the process listening on a specific port"""
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.status == 'LISTEN':
                try:
                    return psutil.Process(conn.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return None

def get_process_info(proc: psutil.Process, now: float) -> Dict:
    """Extract process information"""
    try:
        with proc.oneshot():
            cmdline = ' '.join(proc.cmdline() or [])
            return {
                'pid': proc.pid,
                'cpu_percent': round(proc.cpu_percent(interval=0.1), 2),
                'memory_percent': round(proc.memory_percent(), 2),
                'uptime_seconds': round(now - proc.create_time(), 2),
                'cmdline': cmdline[:100] + '...' if len(cmdline) > 100 else cmdline
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

def get_process_metrics() -> ProcessMetrics:
    """Collect OpenClaw, project process metrics"""
    processes = []
    now = time.time()
    
    # Helper function to find process by name in cmdline
    def find_by_cmdline(patterns):
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                for pattern in patterns:
                    if pattern.lower() in cmdline.lower():
                        return psutil.Process(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    # 1. OpenClaw Gateway - check by cmdline
    gateway_proc = find_by_cmdline(['openclaw-gateway'])
    if gateway_proc:
        info = get_process_info(gateway_proc, now)
        if info:
            processes.append(ProcessStatus(
                name="OpenClaw Gateway",
                running=True,
                pid=info['pid'],
                port=18789,
                cpu_percent=info['cpu_percent'],
                memory_percent=info['memory_percent'],
                uptime_seconds=info['uptime_seconds'],
                cmdline=info['cmdline']
            ))
        else:
            processes.append(ProcessStatus(name="OpenClaw Gateway", running=False))
    else:
        # Fallback to port check
        gateway_proc = find_process_by_port(18789)
        if gateway_proc:
            info = get_process_info(gateway_proc, now)
            if info:
                processes.append(ProcessStatus(
                    name="OpenClaw Gateway",
                    running=True,
                    pid=info['pid'],
                    port=18789,
                    cpu_percent=info['cpu_percent'],
                    memory_percent=info['memory_percent'],
                    uptime_seconds=info['uptime_seconds'],
                    cmdline=info['cmdline']
                ))
            else:
                processes.append(ProcessStatus(name="OpenClaw Gateway", running=False))
        else:
            processes.append(ProcessStatus(name="OpenClaw Gateway", running=False))
    
    # 2. OpenClaw Node - check by cmdline
    node_proc = find_by_cmdline(['openclaw-node'])
    if node_proc:
        info = get_process_info(node_proc, now)
        if info:
            processes.append(ProcessStatus(
                name="OpenClaw Node",
                running=True,
                pid=info['pid'],
                cpu_percent=info['cpu_percent'],
                memory_percent=info['memory_percent'],
                uptime_seconds=info['uptime_seconds'],
                cmdline=info['cmdline']
            ))
        else:
            processes.append(ProcessStatus(name="OpenClaw Node", running=False))
    else:
        processes.append(ProcessStatus(name="OpenClaw Node", running=False))
    
    # 3. OpenClaw TUI - check by process name
    tui_procs = find_processes_by_name(
        ['openclaw-tui'],
        exclude_patterns=['grep']
    )
    
    if tui_procs:
        proc = tui_procs[0]
        info = get_process_info(proc, now)
        if info:
            processes.append(ProcessStatus(
                name="OpenClaw TUI",
                running=True,
                pid=info['pid'],
                cpu_percent=info['cpu_percent'],
                memory_percent=info['memory_percent'],
                uptime_seconds=info['uptime_seconds'],
                cmdline=info['cmdline']
            ))
        else:
            processes.append(ProcessStatus(name="OpenClaw TUI", running=False))
    else:
        processes.append(ProcessStatus(name="OpenClaw TUI", running=False))
    
    # 4. Ollama - check by port or process name
    ollama_procs = find_processes_by_name(
        ['ollama'],
        exclude_patterns=['grep']
    )
    
    if ollama_procs:
        proc = ollama_procs[0]
        info = get_process_info(proc, now)
        if info:
            processes.append(ProcessStatus(
                name="Ollama",
                running=True,
                pid=info['pid'],
                port=11434,
                cpu_percent=info['cpu_percent'],
                memory_percent=info['memory_percent'],
                uptime_seconds=info['uptime_seconds'],
                cmdline=info['cmdline']
            ))
        else:
            processes.append(ProcessStatus(name="Ollama", running=False))
    else:
        # Fallback to port check
        ollama_proc = find_process_by_port(11434)
        if ollama_proc:
            info = get_process_info(ollama_proc, now)
            if info:
                processes.append(ProcessStatus(
                    name="Ollama",
                    running=True,
                    pid=info['pid'],
                    port=11434,
                    cpu_percent=info['cpu_percent'],
                    memory_percent=info['memory_percent'],
                    uptime_seconds=info['uptime_seconds'],
                    cmdline=info['cmdline']
                ))
            else:
                processes.append(ProcessStatus(name="Ollama", running=False))
        else:
            processes.append(ProcessStatus(name="Ollama", running=False))
    
    # 5. Cloudflared - check by process name
    cloudflared_procs = find_processes_by_name(
        ['cloudflared'],
        exclude_patterns=['grep']
    )
    
    if cloudflared_procs:
        proc = cloudflared_procs[0]
        info = get_process_info(proc, now)
        if info:
            processes.append(ProcessStatus(
                name="Cloudflared",
                running=True,
                pid=info['pid'],
                cpu_percent=info['cpu_percent'],
                memory_percent=info['memory_percent'],
                uptime_seconds=info['uptime_seconds'],
                cmdline=info['cmdline']
            ))
        else:
            processes.append(ProcessStatus(name="Cloudflared", running=False))
    else:
        processes.append(ProcessStatus(name="Cloudflared", running=False))
    
    # 6. Monitoring Dashboard - check by process path and main.py
    dashboard_procs = find_processes_by_name(
        ['host-monitoring-dashboard'],
        exclude_patterns=['grep', 'tail']
    )
    
    if dashboard_procs:
        proc = dashboard_procs[0]
        info = get_process_info(proc, now)
        if info:
            processes.append(ProcessStatus(
                name="Monitoring Dashboard",
                running=True,
                pid=info['pid'],
                port=8081,
                cpu_percent=info['cpu_percent'],
                memory_percent=info['memory_percent'],
                uptime_seconds=info['uptime_seconds'],
                cmdline=info['cmdline']
            ))
        else:
            processes.append(ProcessStatus(name="Monitoring Dashboard", running=False))
    else:
        # Fallback to port check
        dashboard_proc = find_process_by_port(8081)
        if dashboard_proc:
            info = get_process_info(dashboard_proc, now)
            if info:
                processes.append(ProcessStatus(
                    name="Monitoring Dashboard",
                    running=True,
                    pid=info['pid'],
                    port=8081,
                    cpu_percent=info['cpu_percent'],
                    memory_percent=info['memory_percent'],
                    uptime_seconds=info['uptime_seconds'],
                    cmdline=info['cmdline']
                ))
            else:
                processes.append(ProcessStatus(name="Monitoring Dashboard", running=False))
        else:
            processes.append(ProcessStatus(name="Monitoring Dashboard", running=False))
    
    # 7. Knowledge Graph Backend - check by port 8000/8001 or process path
    kg_backend_procs = find_processes_by_name(
        ['knowledge-graph', 'uvicorn'],
        exclude_patterns=['grep', 'esbuild']
    )
    
    # Filter to only those actually in knowledge-graph path
    kg_backend = None
    for proc in kg_backend_procs:
        try:
            cmdline = ' '.join(proc.cmdline() or [])
            if 'knowledge-graph' in cmdline.lower():
                kg_backend = proc
                break
        except:
            pass
    
    if kg_backend:
        info = get_process_info(kg_backend, now)
        if info:
            # Try to find the port
            port = None
            try:
                for conn in kg_backend.connections(kind='inet'):
                    if conn.status == 'LISTEN':
                        port = conn.laddr.port
                        break
            except:
                pass
            
            processes.append(ProcessStatus(
                name="Knowledge Graph API",
                running=True,
                pid=info['pid'],
                port=port or 8000,
                cpu_percent=info['cpu_percent'],
                memory_percent=info['memory_percent'],
                uptime_seconds=info['uptime_seconds'],
                cmdline=info['cmdline']
            ))
        else:
            processes.append(ProcessStatus(name="Knowledge Graph API", running=False))
    else:
        processes.append(ProcessStatus(name="Knowledge Graph API", running=False))
    
    # 8. Knowledge Graph Frontend - check by vite and path
    kg_frontend_procs = find_processes_by_name(
        ['knowledge-graph'],
        exclude_patterns=['grep', 'esbuild', 'backend', 'uvicorn']
    )
    
    kg_frontend = None
    for proc in kg_frontend_procs:
        try:
            cmdline = ' '.join(proc.cmdline() or [])
            if 'vite' in cmdline.lower() and 'frontend' in cmdline.lower():
                kg_frontend = proc
                break
        except:
            pass
    
    if kg_frontend:
        info = get_process_info(kg_frontend, now)
        if info:
            processes.append(ProcessStatus(
                name="Knowledge Graph UI",
                running=True,
                pid=info['pid'],
                port=5174,
                cpu_percent=info['cpu_percent'],
                memory_percent=info['memory_percent'],
                uptime_seconds=info['uptime_seconds'],
                cmdline=info['cmdline']
            ))
        else:
            processes.append(ProcessStatus(name="Knowledge Graph UI", running=False))
    else:
        processes.append(ProcessStatus(name="Knowledge Graph UI", running=False))
    
    # 9. Personal Dashboard Frontend - check by vite and path
    personal_dashboard_procs = find_processes_by_name(
        ['personal-dashboard'],
        exclude_patterns=['grep', 'esbuild']
    )
    
    personal_frontend = None
    for proc in personal_dashboard_procs:
        try:
            cmdline = ' '.join(proc.cmdline() or [])
            if 'vite' in cmdline.lower():
                personal_frontend = proc
                break
        except:
            pass
    
    if personal_frontend:
        info = get_process_info(personal_frontend, now)
        if info:
            processes.append(ProcessStatus(
                name="Personal Dashboard",
                running=True,
                pid=info['pid'],
                port=5173,
                cpu_percent=info['cpu_percent'],
                memory_percent=info['memory_percent'],
                uptime_seconds=info['uptime_seconds'],
                cmdline=info['cmdline']
            ))
        else:
            processes.append(ProcessStatus(name="Personal Dashboard", running=False))
    else:
        processes.append(ProcessStatus(name="Personal Dashboard", running=False))
    
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

@app.get("/dashboard")
async def dashboard():
    """Serve frontend HTML for /dashboard route"""
    frontend_html = os.path.join(frontend_path, "index.html")
    if os.path.exists(frontend_html):
        return FileResponse(frontend_html)
    raise HTTPException(status_code=404, detail="Frontend not built")

@app.get("/login")
async def login():
    """Serve frontend HTML for /login route"""
    frontend_html = os.path.join(frontend_path, "index.html")
    if os.path.exists(frontend_html):
        return FileResponse(frontend_html)
    raise HTTPException(status_code=404, detail="Frontend not built")

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
    uvicorn.run(app, host="0.0.0.0", port=8081)
