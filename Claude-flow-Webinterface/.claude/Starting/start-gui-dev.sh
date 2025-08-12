#!/bin/bash
# Claude-Flow GUI Development Mode
# Starts server with auto-reload for development

echo "═══════════════════════════════════════════════════════════"
echo "   Claude-Flow Control Center - Development Mode"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Navigate to GUI directory
cd ../../gui

# Check if nodemon is installed
if [ ! -f "node_modules/.bin/nodemon" ]; then
    echo "📦 Installing development dependencies..."
    npm install nodemon --save-dev
fi

# Start server with nodemon
echo "🔄 Starting server with auto-reload..."
echo "📍 Watching for file changes..."
echo ""

npx nodemon server.js

echo ""
echo "✅ Development server stopped"