#!/bin/bash
# Claude-Flow GUI Starter Script
# Starts the web-based control center

echo "═══════════════════════════════════════════════════════════"
echo "   Claude-Flow Control Center - Starting GUI"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Navigate to project root
cd ../../../

# Check if dependencies are installed
if [ ! -d "Claude-flow-Webinterface/.claude/gui/node_modules" ]; then
    echo "📦 Installing dependencies..."
    cd Claude-flow-Webinterface/.claude/gui
    npm install
    cd ../../../
fi

# Start the server
echo "🚀 Starting WebSocket server on port 8080..."
npm run gui-server &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Open GUI in browser
echo "🌐 Opening GUI in browser..."
npm run gui

echo ""
echo "✅ GUI is running at: http://localhost:8080"
echo "📝 Server PID: $SERVER_PID"
echo ""
echo "Press Ctrl+C to stop the server"

# Keep script running
wait $SERVER_PID