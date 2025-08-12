#!/bin/bash
# Claude-Flow Quick Start (Double-click to run on macOS)
# This file can be double-clicked in Finder to start the GUI

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to script directory
cd "$DIR"

# Clear terminal
clear

# Display banner
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         Claude-Flow Control Center Quick Start           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Run the GUI starter
bash start-gui.sh

# Keep terminal open
echo ""
echo "Press any key to exit..."
read -n 1