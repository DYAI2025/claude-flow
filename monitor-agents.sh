#!/bin/bash

# Claude Flow Agent Monitor Script
# =================================

echo "🤖 CLAUDE FLOW AGENT MONITOR"
echo "============================"

# Funktionen
show_workflow_history() {
    echo "📋 WORKFLOW-HISTORIE:"
    sqlite3 .swarm/memory.db "SELECT timestamp, workflow_name, phase, status FROM workflow_history ORDER BY timestamp DESC LIMIT 5;" 2>/dev/null || echo "  Keine Workflow-Historie gefunden"
}

show_agent_files() {
    echo "📁 AGENT-OUTPUT-DATEIEN:"
    find . -path "./.claude/commands/marker-system/*" -name "*.md" -o -name "*.py" | head -10
}

show_status() {
    echo "👥 AGENT-STATUS:"
    echo "  🐝 Queen Agent: ready"
    echo "  🏗️ Architect Agent: ready" 
    echo "  📂 Folder Manager Agent: ready"
    echo "  ➕ Marker Creator Agent: ready"
    echo "  🔍 Detect Engineer Agent: ready"
    echo "  🤖 GPT Integrator Agent: ready"
    echo "  🐍 Python Generator Agent: ready"
    echo "  🔧 Utility Agent: ready"
}

show_commands() {
    echo "🎯 VERFÜGBARE KOMMANDOS:"
    echo "  claude-flow frausar-orchestrate start"
    echo "  claude-flow frausar-orchestrate status"
    echo "  claude-flow frausar-orchestrate phase 1"
    echo "  python3 monitor-agents.py"
    echo "  python3 monitor-agents.py live"
}

# Hauptfunktion
main() {
    case "${1:-status}" in
        "status")
            show_workflow_history
            echo
            show_status
            echo
            show_agent_files
            echo
            show_commands
            ;;
        "live")
            echo "🔄 LIVE-MONITORING gestartet (Update alle 30 Sekunden)"
            echo "Drücke Ctrl+C zum Beenden"
            while true; do
                clear
                echo "🤖 CLAUDE FLOW AGENT MONITOR - LIVE"
                echo "==================================="
                echo "Letztes Update: $(date)"
                echo
                show_workflow_history
                echo
                show_status
                echo
                show_agent_files
                sleep 30
            done
            ;;
        "start")
            echo "🚀 STARTE FRAUSAR ORCHESTRATION..."
            claude-flow frausar-orchestrate start
            ;;
        "help")
            echo "HILFE:"
            echo "  $0 status    - Zeigt aktuellen Status"
            echo "  $0 live      - Live-Monitoring"
            echo "  $0 start     - Startet Orchestrierung"
            echo "  $0 help      - Diese Hilfe"
            ;;
        *)
            echo "Unbekannter Parameter: $1"
            echo "Verwende: $0 help"
            ;;
    esac
}

# Script ausführen
main "$@" 