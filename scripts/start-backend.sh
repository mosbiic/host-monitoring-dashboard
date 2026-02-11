#!/bin/bash
# Start Monitoring Dashboard Backend

cd "$HOME/Projects/host-monitoring-dashboard/backend"
source venv/bin/activate

export BACKEND_PORT=18082
export DASHBOARD_TOKEN=mosbiic-dashboard-secure-token-2024
export WS_ALLOW_NO_AUTH=true

exec "$HOME/Projects/host-monitoring-dashboard/backend/venv/bin/python" main.py
