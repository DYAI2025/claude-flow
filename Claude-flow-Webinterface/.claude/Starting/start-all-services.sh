#!/bin/bash
# Claude-Flow Complete Service Starter
# Starts all Claude-Flow services

echo "═══════════════════════════════════════════════════════════"
echo "   Claude-Flow - Starting All Services"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Navigate to project root
cd ../../../

# Function to check if port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
    return $?
}

# Start GUI Server
if ! check_port 8080; then
    echo "🌐 Starting GUI Server..."
    npm run gui-server &
    GUI_PID=$!
    sleep 2
else
    echo "⚠️  Port 8080 already in use (GUI Server might be running)"
fi

# Initialize Swarm
echo "🐝 Initializing Claude-Flow Swarm..."
npx claude-flow@alpha swarm init mesh --max-agents 8

# Check swarm status
echo "📊 Checking swarm status..."
npx claude-flow@alpha swarm status

# Open GUI
echo "🚀 Opening Control Center..."
open http://localhost:8080

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ All services started successfully!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📍 GUI: http://localhost:8080"
echo "📍 WebSocket: ws://localhost:8081"
echo "📍 Health: http://localhost:8080/health"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep script running
if [ ! -z "$GUI_PID" ]; then
    wait $GUI_PID
fi