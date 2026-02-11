#!/bin/bash
# Start Monitoring Dashboard Frontend

cd "$HOME/Projects/host-monitoring-dashboard/frontend"

# Build if needed
if [ ! -d "dist" ]; then
    /opt/homebrew/bin/npm run build
fi

# Serve on port 13001
exec /opt/homebrew/bin/npx http-server dist -p 13001 --cors
