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

def find_process_by_cmdline_keywords(keywords: List[str], exclude_keywords: List[str] = None, port: int = None, 
                                      proc_name_patterns: List[str] = None) -> Optional[Dict]:
    """Find process by keywords in cmdline or process name, optionally verify by port"""
    exclude_keywords = exclude_keywords or []
    proc_name_patterns = proc_name_patterns or []
    now = time.time()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            proc_name = proc.info['name'] or ''
            cmdline_list = proc.info['cmdline'] or []
            cmdline = ' '.join(cmdline_list)
            cmdline_lower = cmdline.lower()
            proc_name_lower = proc_name.lower()
            
            # Check if all keywords match in cmdline
            matches_cmdline = all(kw.lower() in cmdline_lower for kw in keywords)
            
            # Check if process name matches any pattern
            matches_name = any(pattern.lower() in proc_name_lower for pattern in proc_name_patterns)
            
            # Check if any exclude keyword matches
            excluded = any(excl.lower() in cmdline_lower for excl in exclude_keywords)
            
            if (matches_cmdline or matches_name) and not excluded:
                # If port specified, verify the process is listening on that port
                if port:
                    try:
                        p = psutil.Process(proc.info['pid'])
                        for conn in p.connections(kind='inet'):
                            if conn.status == 'LISTEN' and conn.laddr.port == port:
                                info = get_process_info(p, now)
                                if info:
                                    info['port'] = port
                                    return info
                    except:
                        pass
                else:
                    info = get_process_info(psutil.Process(proc.info['pid']), now)
                    if info:
                        return info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def find_ollama_process(now: float) -> Optional[Dict]:
    """Find Ollama process by name or port"""
    # First try by process name
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            proc_name = (proc.info['name'] or '').lower()
            if 'ollama' in proc_name:
                info = get_process_info(psutil.Process(proc.info['pid']), now)
                if info:
                    info['port'] = 11434
                    return info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Fallback: find by port
    proc = find_process_by_port(11434)
    if proc:
        info = get_process_info(proc, now)
        if info:
            info['port'] = 11434
            return info
    return None

def find_cloudflared_process(now: float) -> Optional[Dict]:
    """Find Cloudflared process by name"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            proc_name = (proc.info['name'] or '').lower()
            cmdline = ' '.join(proc.info['cmdline'] or []).lower()
            if 'cloudflared' in proc_name or 'cloudflared' in cmdline:
                info = get_process_info(psutil.Process(proc.info['pid']), now)
                if info:
                    return info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def find_knowledge_graph_backend(now: float) -> Optional[Dict]:
    """Find Knowledge Graph backend by cmdline containing port 8000 or 8001"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            cmdline_lower = cmdline.lower()
            
            # Match uvicorn with port 8000 or 8001
            if 'uvicorn' in cmdline_lower:
                port = None
                if '--port 8000' in cmdline or 'port 8000' in cmdline_lower:
                    port = 8000
                elif '--port 8001' in cmdline or 'port 8001' in cmdline_lower:
                    port = 8001
                
                if port:
                    info = get_process_info(psutil.Process(proc.info['pid']), now)
                    if info:
                        info['port'] = port
                        return info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def find_vite_process_by_path(path_keyword: str, default_port: int, now: float) -> Optional[Dict]:
    """Find Vite dev server by path keyword, extract port from cmdline"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            cmdline_lower = cmdline.lower()
            
            # Match node process with vite in the path containing the keyword
            is_node = 'node' in (proc.info['name'] or '').lower() or 'node' in cmdline_lower
            has_vite = 'vite' in cmdline_lower
            has_path = path_keyword.lower() in cmdline_lower
            
            if is_node and has_vite and has_path:
                info = get_process_info(psutil.Process(proc.info['pid']), now)
                if info:
                    # Extract port from cmdline (e.g., --port 3001 or --port=3001)
                    port = default_port
                    import re
                    port_match = re.search(r'--port[=\s]*(\d+)', cmdline)
                    if port_match:
                        port = int(port_match.group(1))
                    else:
                        # Try to get from connections (if we have permission)
                        try:
                            for conn in psutil.Process(proc.info['pid']).connections(kind='inet'):
                                if conn.status == 'LISTEN':
                                    port = conn.laddr.port
                                    break
                        except:
                            pass
                    info['port'] = port
                    return info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def get_process_metrics() -> ProcessMetrics:
    """Collect OpenClaw, project process metrics"""
    processes = []
    now = time.time()
    
    # 1. OpenClaw Gateway - check by process name or cmdline
    gateway_info = find_process_by_cmdline_keywords(
        ['openclaw-gateway'],
        exclude_keywords=['grep'],
        proc_name_patterns=['openclaw-gateway']
    )
    if gateway_info:
        gateway_info['port'] = 18789
        processes.append(ProcessStatus(name="OpenClaw Gateway", running=True, **gateway_info))
    else:
        processes.append(ProcessStatus(name="OpenClaw Gateway", running=False))
    
    # 2. OpenClaw Node - check by process name or cmdline
    node_info = find_process_by_cmdline_keywords(
        ['openclaw-node'],
        exclude_keywords=['grep'],
        proc_name_patterns=['openclaw-node']
    )
    if node_info:
        processes.append(ProcessStatus(name="OpenClaw Node", running=True, **node_info))
    else:
        processes.append(ProcessStatus(name="OpenClaw Node", running=False))
    
    # 3. OpenClaw TUI - check by process name or cmdline
    tui_info = find_process_by_cmdline_keywords(
        ['openclaw-tui'],
        exclude_keywords=['grep'],
        proc_name_patterns=['openclaw-tui']
    )
    if tui_info:
        processes.append(ProcessStatus(name="OpenClaw TUI", running=True, **tui_info))
    else:
        processes.append(ProcessStatus(name="OpenClaw TUI", running=False))
    
    # 4. Ollama - check by process name or port
    ollama_info = find_ollama_process(now)
    if ollama_info:
        processes.append(ProcessStatus(name="Ollama", running=True, **ollama_info))
    else:
        processes.append(ProcessStatus(name="Ollama", running=False))
    
    # 5. Cloudflared - check by process name
    cloudflared_info = find_cloudflared_process(now)
    if cloudflared_info:
        processes.append(ProcessStatus(name="Cloudflared", running=True, **cloudflared_info))
    else:
        processes.append(ProcessStatus(name="Cloudflared", running=False))
    
    # 6. Monitoring Dashboard Backend - check by port 8081 or path/cmdline
    dashboard_proc = find_process_by_port(8081)
    if dashboard_proc:
        dashboard_info = get_process_info(dashboard_proc, now)
        if dashboard_info:
            dashboard_info['port'] = 8081
            processes.append(ProcessStatus(name="Monitoring Dashboard", running=True, **dashboard_info))
        else:
            processes.append(ProcessStatus(name="Monitoring Dashboard", running=False))
    else:
        # Fallback: try to find by cmdline keywords
        dashboard_info = find_process_by_cmdline_keywords(
            ['main.py'],
            exclude_keywords=['grep', 'node', 'vite', 'personal-dashboard', 'knowledge-graph']
        )
        if dashboard_info:
            dashboard_info['port'] = 8081
            processes.append(ProcessStatus(name="Monitoring Dashboard", running=True, **dashboard_info))
        else:
            processes.append(ProcessStatus(name="Monitoring Dashboard", running=False))
    
    # 7. Knowledge Graph Backend
    kg_backend_info = find_knowledge_graph_backend(now)
    if kg_backend_info:
        processes.append(ProcessStatus(name="Knowledge Graph API", running=True, **kg_backend_info))
    else:
        processes.append(ProcessStatus(name="Knowledge Graph API", running=False))
    
    # 8. Knowledge Graph Frontend - Vite dev server
    kg_frontend_info = find_vite_process_by_path('knowledge-graph', 5173, now)
    if kg_frontend_info:
        processes.append(ProcessStatus(name="Knowledge Graph UI", running=True, **kg_frontend_info))
    else:
        processes.append(ProcessStatus(name="Knowledge Graph UI", running=False))
    
    # 9. Personal Dashboard Backend - Python uvicorn on port 8000
    personal_info = find_process_by_cmdline_keywords(
        ['personal-dashboard', 'uvicorn'],
        exclude_keywords=['grep']
    )
    if personal_info:
        personal_info['port'] = 8000
        processes.append(ProcessStatus(name="Personal Dashboard", running=True, **personal_info))
    else:
        # Fallback: check port 8000
        personal_proc = find_process_by_port(8000)
        if personal_proc:
            personal_info = get_process_info(personal_proc, now)
            if personal_info:
                personal_info['port'] = 8000
                processes.append(ProcessStatus(name="Personal Dashboard", running=True, **personal_info))
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

def downsample_data(data: List[Dict], max_points: int = 500) -> List[Dict]:
    """Downsample data to max_points for efficient rendering"""
    if len(data) <= max_points:
        return data
    
    # Use systematic sampling to reduce points
    step = len(data) // max_points
    return data[::step]

@app.get("/api/metrics/history")
async def get_metrics_history(
    hours: int = 24,
    token: str = Depends(verify_token)
):
    """Get historical metrics for the specified time period with downsampling"""
    cutoff = time.time() - (hours * 3600)
    filtered_history = [m for m in metrics_history if m["timestamp"] > cutoff]
    
    # Sort by timestamp to ensure correct order
    filtered_history.sort(key=lambda x: x["timestamp"])
    
    # Downsample based on time range
    # Longer periods need more aggressive downsampling
    if hours <= 24:
        max_points = 500
    elif hours <= 72:  # 3 days
        max_points = 400
    else:  # 7 days
        max_points = 300
    
    downsampled = downsample_data(filtered_history, max_points)
    
    return {
        "hours": hours,
        "data_points": len(downsampled),
        "total_points": len(filtered_history),
        "data": downsampled
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
                # Use timeout to allow periodic checks
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle ping/pong from client
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "pong":
                    # Client responded to our ping, connection is alive
                    pass
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
