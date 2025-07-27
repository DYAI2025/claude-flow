# Frawser GUI Upgrade Command

## Purpose
Orchestrates the Frawser GUI upgrade project using Claude Flow agents, integrating legacy features into the new AP-GUI with MongoDB support.

## Usage
```bash
frawser-upgrade <operation> [options]
```

## Operations
- `status`: Show current upgrade progress and agent status
- `fix-bugs`: Activate bug-fix-agent for UI stabilization
- `migrate-features`: Activate feature-migrator for legacy feature integration
- `setup-mongodb`: Activate mongodb-integrator for database connection
- `run-tests`: Activate test-agent for quality assurance
- `full-upgrade`: Execute complete upgrade pipeline
- `dashboard`: Launch upgrade monitoring dashboard

## Parameters
- `operation`: Upgrade operation to perform
- `--agents`: Specify which agents to use
- `--parallel`: Run agents in parallel mode
- `--monitor`: Enable real-time monitoring
- `--legacy-path`: Path to legacy Frawser GUI
- `--ap-gui-path`: Path to new AP-GUI
- `--mongodb-uri`: MongoDB connection string

## Examples
```bash
# Check current status
frawser-upgrade status

# Fix UI bugs
frawser-upgrade fix-bugs --monitor

# Migrate legacy features
frawser-upgrade migrate-features --parallel

# Complete upgrade pipeline
frawser-upgrade full-upgrade --monitor --parallel

# Launch upgrade dashboard
frawser-upgrade dashboard
```

## Agent Integration

### bug-fix-agent (30% Progress)
- **Role**: UI Stabilisierung
- **Tasks**:
  - Upload-Feld reparieren
  - Layout-Resize-Probleme beheben
  - Popup-Handler stabilisieren
  - Responsive Design sicherstellen

### feature-migrator (10% Progress)
- **Role**: Legacy Feature Migration
- **Tasks**:
  - GPT-YAML Generator übernehmen
  - Strukturanalyse implementieren
  - Lücken-Detektor einbauen
  - YAML ↔ JSON Konvertierung
  - Erweiterter Batch-Manager

### mongodb-integrator (Ready)
- **Role**: Database Integration
- **Tasks**:
  - MongoDB-Connector aktivieren
  - Marker-CRUD implementieren
  - Validierungsstatus speichern
  - Logs und Performance-Tracking

### test-agent (Idle)
- **Role**: Quality Assurance
- **Tasks**:
  - Feature-Regression-Tests
  - DB-CRUD-Tests
  - UI-Verhalten-Tests
  - Performance-Tests

## Project Structure
```
Frawser Upgrade Project
├── legacy_gui_path: FrawserGUIPython
├── ap_gui_path: FrawserAPGUI
├── database: MongoDB (connection preset)
├── dashboard: http://localhost:6023
└── agents: bug-fix, feature-migrator, mongodb-integrator, test
```

## Integration with Marker System
- **Marker Validator Convert**: Repair/Convert Agents reparieren
- **Frausar API GUI**: Multi-Marker-Management erweitern
- **Claude Flow**: Zentrale Orchestrierung
- **MongoDB**: Einheitliche Datenhaltung

## Expected Outcome
- Stabile, erweiterbare GUI
- Vollständiges Feature-Set aus Legacy
- MongoDB-Anbindung aktiv
- Modulare Agent-Architektur
- Real-time Monitoring Dashboard 