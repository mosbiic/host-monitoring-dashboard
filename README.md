# Host Monitoring Dashboard

Real-time system monitoring dashboard for Mac Mini with OpenClaw process health tracking.

![Dashboard Preview](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![Vue.js](https://img.shields.io/badge/vue.js-3.4+-green)

## Features

- 📊 **System Monitoring**: Real-time CPU usage, memory consumption, and disk space
- 🔧 **Process Monitoring**: Track OpenClaw Gateway/Node, Ollama, and Cloudflared status
- 📈 **Historical Data**: 24-hour and 7-day trend charts with Chart.js
- 🔄 **Real-time Updates**: WebSocket live data streaming (updates every 5 seconds)
- 🔐 **Security**: Bearer Token authentication middleware
- 📱 **Responsive**: Mobile-friendly dark theme UI

## Architecture

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│   Vue3 Frontend │ ◄────────────────► │  FastAPI Backend│
│   (Port 3000)   │                    │   (Port 8080)   │
│   Chart.js      │     HTTP API       │   psutil        │
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
| Ollama | Port Check | 11434 | Ollama AI service |
| Cloudflared | Process Check | - | Cloudflare tunnel daemon |

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

   # Terminal 2 - Frontend
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the dashboard**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8080/docs

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/health` | Health check | No |
| GET | `/api/metrics/system` | Current system metrics | Bearer |
| GET | `/api/metrics/processes` | Process status | Bearer |
| GET | `/api/metrics/history?hours=24` | Historical data | Bearer |
| WS | `/ws/metrics?token=xxx` | Real-time metrics stream | Query param |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_TOKEN` | `changeme` | Authentication token |
| `BACKEND_PORT` | `8080` | API server port |
| `VITE_API_BASE` | `http://localhost:8080` | API base URL |

### Token Authentication

1. Set a strong token in `.env`:
   ```bash
   DASHBOARD_TOKEN=your-secure-token-here
   ```

2. Login at http://localhost:3000 with your token

## Deployment

### Production Build

```bash
# Build frontend
cd frontend
npm run build

# The built files will be in frontend/dist/
# Serve with any static file server or configure FastAPI to serve them
```

### Using Docker (optional)

```dockerfile
# Dockerfile coming soon
```

### Systemd Service (Linux)

```ini
# /etc/systemd/system/host-dashboard.service
[Unit]
Description=Host Monitoring Dashboard
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/host-monitoring-dashboard
Environment=DASHBOARD_TOKEN=your-token
ExecStart=/path/to/host-monitoring-dashboard/start.sh
Restart=always

[Install]
WantedBy=multi-user.target
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
│   │   ├── views/           # Vue pages
│   │   ├── stores/          # Pinia stores
│   │   ├── router.js        # Vue Router
│   │   └── assets/          # Styles
│   ├── package.json
│   └── vite.config.js
├── start.sh                 # Startup script
└── README.md
```

### Adding New Process Monitors

Edit `backend/main.py` and add to `get_process_metrics()`:

```python
# Example: Add new process check
new_proc = find_process_by_name("my-process")
if new_proc:
    processes.append(ProcessStatus(
        name="My Process",
        running=True,
        pid=new_proc.pid,
        # ... other fields
    ))
```

## Troubleshooting

### WebSocket Connection Failed
- Check if backend is running on port 8080
- Verify token is correct
- Check browser console for errors

### Permission Denied (psutil)
- On macOS, grant Terminal "Full Disk Access" in System Preferences
- Some process info may require elevated permissions

### Port Already in Use
- Change ports in `.env` if 8080 or 3000 are occupied

## License

MIT License - See [LICENSE](LICENSE) for details.

## Changelog

### v1.0.0 (2024-02-08)
- Initial release
- System metrics (CPU, Memory, Disk)
- Process monitoring (OpenClaw, Ollama, Cloudflared)
- WebSocket real-time updates
- 24h/7d historical charts
- Token authentication
