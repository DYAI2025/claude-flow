# HiveMemory Dashboard Backend

FastAPI backend for the HiveMemory multi-agent system dashboard.

## Features

- **Agent Management**: Start, stop, restart, and monitor agents
- **Memory Monitoring**: Real-time file watching for observer_stream and core_memory
- **WebSocket Support**: Real-time updates to connected clients
- **REST API**: Comprehensive API for agent control and memory queries
- **YAML Configuration**: Load agent configurations from YAML files

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create necessary directories:
```bash
mkdir -p /mnt/memory
mkdir -p agents
mkdir -p logs
```

3. Add agent configuration files to the `agents/` directory

4. Start the server:
```bash
python main.py
# or
bash start.sh
```

## API Endpoints

### Agent Management

- `GET /api/agents` - Get all agents
- `GET /api/agents/{agent_id}` - Get specific agent
- `POST /api/agents/control` - Control agent (start/stop/restart/status)

### Memory

- `GET /api/memory/files` - Get memory files with optional filters
- `POST /api/memory/query` - Query memory events

### System

- `GET /api/system/status` - Get overall system status
- `GET /health` - Health check endpoint

### WebSocket

- `WS /ws` - WebSocket endpoint for real-time updates

## WebSocket Events

The WebSocket connection receives the following event types:

- `initial_state` - Initial system state when connected
- `agent_update` - Agent status changes
- `memory_event` - Memory file events (created/modified/deleted)

## Configuration

Agent configurations are loaded from YAML files in the `agents/` directory. Example:

```yaml
id: agent-researcher-001
name: Research Agent
type: researcher
description: Agent responsible for researching and gathering information
capabilities:
  - information_gathering
  - web_search
  - document_analysis
environment:
  AGENT_ROLE: researcher
max_restarts: 3
restart_delay: 5
```

## Memory Structure

The backend monitors the following directory structure:

```
/mnt/memory/
├── {agent_id}/
│   ├── observer_stream/
│   │   └── *.json
│   └── core_memory/
│       └── *.json
```

## Development

Run with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Testing

You can test the WebSocket connection using:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```