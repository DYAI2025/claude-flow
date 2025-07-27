#!/usr/bin/env python3
"""
Claude Flow Agent Monitor
==========================
Einfaches Monitoring-System für Claude Flow Agents
"""

import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path

class ClaudeFlowMonitor:
    def __init__(self, memory_db_path=".swarm/memory.db"):
        self.memory_db_path = memory_db_path
        self.agents = [
            "queen-agent",
            "architect-agent", 
            "folder-manager-agent",
            "marker-creator-agent",
            "detect-engineer-agent",
            "gpt-integrator-agent",
            "python-generator-agent",
            "utility-agent"
        ]
    
    def get_workflow_history(self):
        """Lädt Workflow-Historie aus der Datenbank"""
        try:
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, workflow_name, phase, status, details 
                FROM workflow_history 
                ORDER BY timestamp DESC
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            return results
        except Exception as e:
            print(f"Fehler beim Laden der Workflow-Historie: {e}")
            return []
    
    def get_agent_status(self):
        """Simuliert Agent-Status (da Agents virtuell arbeiten)"""
        status = {}
        for agent in self.agents:
            # Simuliere Status basierend auf vorhandenen Dateien
            status[agent] = {
                "status": "ready",
                "last_activity": datetime.now().isoformat(),
                "current_task": "waiting for assignment",
                "completed_tasks": 0
            }
        return status
    
    def check_output_files(self):
        """Prüft auf Output-Dateien der Agents"""
        output_files = []
        search_paths = [
            ".claude/commands/marker-system",
            "Frausar_API_GUI",
            "temp_frausar_gui"
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith(('.py', '.md', '.yaml', '.json')):
                            output_files.append(os.path.join(root, file))
        
        return output_files
    
    def display_status(self):
        """Zeigt aktuellen Status an"""
        print("🤖 CLAUDE FLOW AGENT MONITOR")
        print("=" * 50)
        
        # Workflow-Historie
        print("\n📋 WORKFLOW-HISTORIE:")
        history = self.get_workflow_history()
        for entry in history[:5]:  # Letzte 5 Einträge
            timestamp, workflow, phase, status, details = entry
            print(f"  {timestamp} | {workflow} | {phase} | {status}")
            print(f"    Details: {details}")
        
        # Agent-Status
        print("\n👥 AGENT-STATUS:")
        agent_status = self.get_agent_status()
        for agent, status in agent_status.items():
            print(f"  {agent}: {status['status']} - {status['current_task']}")
        
        # Output-Dateien
        print("\n📁 OUTPUT-DATEIEN:")
        output_files = self.check_output_files()
        for file in output_files[:10]:  # Erste 10 Dateien
            print(f"  {file}")
        
        print(f"\n📊 GESAMT: {len(output_files)} Output-Dateien gefunden")
    
    def monitor_live(self, interval=30):
        """Live-Monitoring mit Updates"""
        import time
        
        print(f"🔄 LIVE-MONITORING gestartet (Update alle {interval} Sekunden)")
        print("Drücke Ctrl+C zum Beenden")
        
        try:
            while True:
                os.system('clear')  # Terminal leeren
                self.display_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring beendet")

def main():
    monitor = ClaudeFlowMonitor()
    
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "live":
        monitor.monitor_live()
    else:
        monitor.display_status()

if __name__ == "__main__":
    main() 