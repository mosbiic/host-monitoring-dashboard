# Host Monitoring Dashboard

Real-time system monitoring dashboard for Mac Mini with OpenClaw process health tracking.

![Dashboard Preview](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![React](https://img.shields.io/badge/react-18+-61DAFB)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-3178C6)

## ✅ Completed Features

- 📊 **Real-time System Monitoring**: CPU usage, memory consumption, and disk space
  - Updates every 5 seconds via WebSocket
  - Visual progress bars with color-coded thresholds
  
- 🔧 **OpenClaw Process Monitoring**: Track critical service status
  - OpenClaw Gateway (Port 18789)
  - OpenClaw Node (Process check)
  - OpenClaw TUI (Process check)
  - Ollama AI Service (Port 11434)
  - Cloudflared Tunnel (Process check)
  - Monitoring Dashboard itself (Port 8081)
  - Knowledge Graph API/UI (when running)
  - Personal Dashboard (when running)

- 📈 **Historical Trend Charts**: 24-hour and 7-day data visualization
  - Chart.js line charts for CPU and Memory trends
  - Automatic data downsampling for performance
  - Data retention: 7 days

- 🔐 **Flexible Authentication**: Multiple auth modes supported
  - Cloudflare Access (production)
  - Token-based authentication (local development)
  - Localhost auto-authentication (dev mode)

- 🔄 **Real-time Updates**: WebSocket live data streaming
- 📱 **Responsive Dark Theme**: Mobile-friendly UI with Tailwind CSS

## Architecture

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│  React Frontend │ ◄────────────────► │  FastAPI Backend│
│   (Port 3000)   │                    │   (Port 8081)   │
│  TypeScript     │     HTTP API       │   psutil        │
│  Chart.js       │                    │   WebSocket     │
└─────────────────┘                    └─────────────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │  System Data │
                                        │  - CPU       │
                                        │  - Memory    │
                                        │  - Disk      │
                                        │  - Processes │
                                        └──────────────┘
```

## Monitored Processes

| Process | Type | Port | Description |
|---------|------|------|-------------|
| OpenClaw Gateway | Port Check | 18789 | OpenClaw Gateway service |
| OpenClaw Node | Process Check | - | OpenClaw Node process |
| OpenClaw TUI | Process Check | - | OpenClaw TUI process |
| Ollama | Port/Name Check | 11434 | Ollama AI service |
| Cloudflared | Process Check | - | Cloudflare tunnel daemon |
| Monitoring Dashboard | Port Check | 8081 | This dashboard |
| Knowledge Graph API | Port Check | 8000/8001 | Knowledge Graph backend |
| Knowledge Graph UI | Port Check | 5173 | Knowledge Graph frontend |
| Personal Dashboard | Port Check | 8000 | Personal dashboard app |

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mosbiic/host-monitoring-dashboard.git
   cd host-monitoring-dashboard
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and set DASHBOARD_TOKEN
   ```

3. **Start the application**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   Or start manually:
   ```bash
   # Terminal 1 - Backend
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python main.py

   # Terminal 2 - Frontend (dev mode)
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the dashboard**
   - Development: http://localhost:3000
   - Production (built-in): http://localhost:8081
   - API Docs: http://localhost:8081/docs

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/health` | Health check | No |
| GET | `/api/auth/config` | Auth mode configuration | No |
| GET | `/api/metrics/system` | Current system metrics | Yes |
| GET | `/api/metrics/processes` | Process status | Yes |
| GET | `/api/metrics/history?hours=24` | Historical data (24h or 168h) | Yes |
| WS | `/ws/metrics` | Real-time metrics stream | Yes |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CF_ACCESS_ENABLED` | `true` | Enable Cloudflare Access auth |
| `DASHBOARD_TOKEN` | `changeme` | Token for local auth |
| `BACKEND_PORT` | `8081` | API server port |
| `WS_ALLOW_NO_AUTH` | `false` | Allow WebSocket without auth (for tunnels) |

### Authentication Modes

#### Cloudflare Access (Production)
```bash
CF_ACCESS_ENABLED=true
```
Access via Cloudflare Tunnel with Access policies.

#### Token-based (Local Development)
```bash
CF_ACCESS_ENABLED=false
DASHBOARD_TOKEN=your-secure-token-2024
```
Login with token at the dashboard login page.

#### Localhost Auto-auth (Development)
When `CF_ACCESS_ENABLED=false` and accessing from localhost, auth is automatic.

## Deployment

### Production with Cloudflare Tunnel

1. **Configure Cloudflare Tunnel**
   ```yaml
   # ~/.cloudflared/config.yml
   tunnel: YOUR_TUNNEL_ID
   credentials-file: ~/.cloudflared/YOUR_TUNNEL_ID.json
   
   ingress:
     - hostname: monitoring.mosbiic.com
       service: http://localhost:8081
     - service: http_status:404
   ```

2. **Environment for production**
   ```bash
   CF_ACCESS_ENABLED=true
   BACKEND_PORT=8081
   ```

3. **Build and run**
   ```bash
   cd frontend && npm run build
   cd ../backend
   source venv/bin/activate
   python main.py
   ```

### macOS LaunchAgent (Auto-start)

Create `~/Library/LaunchAgents/com.mosbiic.monitoring-dashboard.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mosbiic.monitoring-dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/sh</string>
        <string>-c</string>
        <string>cd /Users/mosbiic/.openclaw/workspace/host-monitoring-dashboard &amp;&amp; source backend/venv/bin/activate &amp;&amp; python backend/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/monitoring-dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/monitoring-dashboard.error.log</string>
</dict>
</plist>
```

Load and start:
```bash
launchctl load ~/Library/LaunchAgents/com.mosbiic.monitoring-dashboard.plist
launchctl start com.mosbiic.monitoring-dashboard
```

## Development

### Project Structure

```
host-monitoring-dashboard/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages (Dashboard, Login)
│   │   ├── components/      # React components
│   │   ├── stores/          # Zustand state management
│   │   ├── hooks/           # Custom React hooks
│   │   ├── utils/           # Helper functions
│   │   └── types/           # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── start.sh                 # Startup script
├── .env                     # Environment configuration
└── README.md
```

### Technology Stack

- **Backend**: Python 3.9+, FastAPI, Uvicorn, psutil, WebSockets
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Chart.js
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Icons**: Lucide React

### Adding New Process Monitors

Edit `backend/main.py` and add to `get_process_metrics()`:

```python
# Example: Add new process check
new_info = find_process_by_cmdline_keywords(
    ['my-process'],
    exclude_keywords=['grep'],
    proc_name_patterns=['my-process']
)
if new_info:
    new_info['port'] = 8080
    processes.append(ProcessStatus(name="My Process", running=True, **new_info))
else:
    processes.append(ProcessStatus(name="My Process", running=False))
```

## Troubleshooting

### WebSocket Connection Failed
- Check if backend is running on port 8081
- Verify token is correct
- Check browser console for errors
- Ensure `WS_ALLOW_NO_AUTH=true` if behind Cloudflare Tunnel

### Permission Denied (psutil)
- On macOS, grant Terminal "Full Disk Access" in System Preferences
- Some process info may require elevated permissions

### Port Already in Use
- Change ports in `.env` if 8081 or 3000 are occupied
- Check with `lsof -i :8081`

## License

MIT License

## Changelog

### v1.0.0 (2025-02-11)
- ✅ Initial release with all core features
- ✅ Real-time CPU/Memory/Disk monitoring
- ✅ OpenClaw process status tracking (Gateway, Node, TUI)
- ✅ External service monitoring (Ollama, Cloudflared)
- ✅ Historical trend charts (24h/7d)
- ✅ WebSocket real-time updates
- ✅ Flexible authentication (Cloudflare Access + Token)
- ✅ Responsive dark theme UI
