#!/bin/bash
# Claude-Flow GUI Server Only
# Starts only the WebSocket server without opening browser

echo "═══════════════════════════════════════════════════════════"
echo "   Claude-Flow Control Center - Server Mode"
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
echo "🚀 Starting WebSocket server..."
echo "📍 HTTP Server: http://localhost:8080"
echo "📍 WebSocket: ws://localhost:8081"
echo ""

npm run gui-server

echo ""
echo "✅ Server stopped"