# 🔍 AGENT MONITORING GUIDE - Claude Flow

## 📊 **WIE DU DIE AGENTS ARBEITEN SIEHST**

Die Claude Flow Agents arbeiten "virtuell" - sie sind nicht als separate Prozesse sichtbar, sondern arbeiten innerhalb des Claude Flow Systems. Hier sind alle Möglichkeiten, ihre Arbeit zu verfolgen:

## 🎯 **MONITORING-TOOLS**

### **1. 📊 EINFACHES MONITORING-SCRIPT**
```bash
# Status anzeigen
./monitor-agents.sh status

# Live-Monitoring (alle 30 Sekunden Update)
./monitor-agents.sh live

# Orchestrierung starten
./monitor-agents.sh start

# Hilfe anzeigen
./monitor-agents.sh help
```

### **2. 🐍 PYTHON MONITORING-SCRIPT**
```bash
# Einmaliger Status
python3 monitor-agents.py

# Live-Monitoring
python3 monitor-agents.py live
```

### **3. 🗄️ DATENBANK-ABFRAGEN**
```bash
# Workflow-Historie anzeigen
sqlite3 .swarm/memory.db "SELECT * FROM workflow_history ORDER BY timestamp DESC;"

# Spezifische Workflows
sqlite3 .swarm/memory.db "SELECT * FROM workflow_history WHERE workflow_name='frausar-gui-upgrade';"
```

### **4. 🎯 CLAUDE FLOW KOMMANDOS**
```bash
# Agent-Status überprüfen
claude-flow frausar-orchestrate status

# Workflow-Status
claude-flow team status
claude-flow team progress

# Agent-spezifische Tasks
claude-flow agent folder-manager status
claude-flow agent marker-creator status
```

## 📁 **OUTPUT-VERFOLGUNG**

### **Agent-Output-Dateien:**
Die Agents erstellen Dateien in diesen Verzeichnissen:
- `.claude/commands/marker-system/` - Kommando-Definitionen
- `Frausar_API_GUI/` - Implementierte Features
- `temp_frausar_gui/` - Vollständige GUI (Referenz)

### **Dateitypen zu überwachen:**
- `*.py` - Python-Implementierungen
- `*.md` - Dokumentation und Anleitungen
- `*.yaml` - Konfigurationen
- `*.json` - Daten und Metadaten

## 🚀 **AGENTS STARTEN & VERFOLGEN**

### **Option 1: Vollständige Orchestrierung**
```bash
# Alle Agents starten
claude-flow frausar-orchestrate start

# Dann Monitoring starten
./monitor-agents.sh live
```

### **Option 2: Phase-spezifisch**
```bash
# Phase 1 starten (Folder Manager Agent)
claude-flow frausar-orchestrate phase 1

# Status überprüfen
claude-flow frausar-orchestrate status
```

### **Option 3: Agent-spezifisch**
```bash
# Spezifischen Agent starten
claude-flow frausar-orchestrate agent folder-manager "Implementiere Quellordner-Auswahl"

# Agent-Status prüfen
claude-flow agent folder-manager status
```

## 📊 **WAS DAS MONITORING ZEIGT**

### **Workflow-Historie:**
- ✅ Abgeschlossene Tasks
- 🔄 Laufende Tasks
- ❌ Fehlgeschlagene Tasks
- 📝 Detaillierte Beschreibungen

### **Agent-Status:**
- 🟢 Ready - Bereit für Tasks
- 🟡 Working - Arbeitet an Task
- 🔴 Error - Fehler aufgetreten
- ✅ Completed - Task abgeschlossen

### **Output-Dateien:**
- 📁 Neue Dateien
- 🔄 Geänderte Dateien
- 📊 Statistiken und Reports

## 🎯 **PRAKTISCHE BEISPIELE**

### **Beispiel 1: Vollständige Orchestrierung starten**
```bash
# Terminal 1: Orchestrierung starten
claude-flow frausar-orchestrate start

# Terminal 2: Live-Monitoring
./monitor-agents.sh live
```

### **Beispiel 2: Phase-spezifisch arbeiten**
```bash
# Phase 1 starten
claude-flow frausar-orchestrate phase 1

# Status überprüfen
claude-flow frausar-orchestrate status

# Output-Dateien prüfen
find . -name "*.py" -newer .swarm/memory.db
```

### **Beispiel 3: Agent-spezifisch**
```bash
# Folder Manager Agent starten
claude-flow frausar-orchestrate agent folder-manager "Implementiere Quellordner-Auswahl"

# Agent-Status prüfen
claude-flow agent folder-manager status

# Output prüfen
ls -la Frausar_API_GUI/
```

## 🔍 **TROUBLESHOOTING**

### **Agents reagieren nicht:**
```bash
# Claude Flow Status prüfen
claude-flow status

# Memory-Datenbank prüfen
sqlite3 .swarm/memory.db ".tables"

# Logs prüfen
claude-flow logs
```

### **Keine Output-Dateien:**
```bash
# Verzeichnisse prüfen
ls -la .claude/commands/marker-system/
ls -la Frausar_API_GUI/

# Dateien suchen
find . -name "*frausar*" -o -name "*marker*"
```

### **Monitoring funktioniert nicht:**
```bash
# Script-Berechtigungen prüfen
ls -la monitor-agents.sh

# Python-Script testen
python3 monitor-agents.py

# Datenbank prüfen
sqlite3 .swarm/memory.db "SELECT COUNT(*) FROM workflow_history;"
```

## 📈 **ERWARTETE ERGEBNISSE**

### **Nach Phase 1:**
- ✅ Ordnerverwaltung implementiert
- ✅ Dateidialog funktioniert
- ✅ Dynamische Ordner-Wechsel

### **Nach Phase 2:**
- ✅ Marker-Erstellung (Einzel + Batch)
- ✅ Multi-YAML Support
- ✅ Vorschau-Funktionalität

### **Nach Phase 3:**
- ✅ Dateioperationen
- ✅ Struktur-Analyse
- ✅ Sichere Löschung

### **Nach Phase 4:**
- ✅ DETECT.py System
- ✅ GPT-YAML Generator
- ✅ Python Detectors

### **Nach Phase 5:**
- ✅ Erweiterte Features
- ✅ Konvertierung
- ✅ Merge-Funktionalität

## 🎯 **ZUSAMMENFASSUNG**

**Die Agents arbeiten virtuell, aber du kannst ihre Arbeit verfolgen durch:**

1. **📊 Monitoring-Scripts** - `./monitor-agents.sh`
2. **🗄️ Datenbank-Abfragen** - SQLite Memory
3. **📁 Output-Dateien** - Neue/geänderte Dateien
4. **🎯 Claude Flow Kommandos** - Status-Abfragen

**Starte das Monitoring mit: `./monitor-agents.sh live`** 