# Claude-Flow Control Center GUI

## Overview
A comprehensive web-based GUI for managing and monitoring Claude-Flow operations with real-time WebSocket communication, session persistence, and 3D visualization capabilities.

## Features

### ✅ Complete Feature Set

#### 10 Activity Cards
1. **Project Overview** - Manage project settings and configuration
2. **Memory Store** - Persistent memory management with CRUD operations
3. **Agent Management** - Spawn and manage 11+ AI agent types
4. **Process Builder** - Design workflows (Scrum/Kanban/LIFe/Custom)
5. **Neural Training** - AI pattern recognition & learning with WASM SIMD
6. **Hooks & Events** - Automation triggers and listeners
7. **GitHub Integration** - Repository and PR management
8. **System Status** - Performance metrics and health monitoring
9. **Session Recovery** - Save and restore work sessions
10. **3D Simulation** - Visual swarm orchestration with WebGL

### 🚀 Key Capabilities

- **Real-time Terminal Output** via WebSocket streaming
- **Session State Persistence** - Survive restarts
- **Cross-browser Support** - Chrome, Firefox, Safari, Edge
- **Zero-Click Start** - Automatic GUI launch
- **Live Command Execution** - Direct integration with claude-flow CLI
- **Memory Namespaces** - Organized data storage
- **Agent Metrics** - Performance tracking and visualization
- **Error Handling** - Graceful degradation and recovery

## Installation

### Prerequisites
- Node.js v20+
- npm v9+
- claude-flow@alpha installed

### Setup
```bash
# Install dependencies
cd .claude/gui
npm install

# Start the server
npm run gui-server

# Or use the parent package.json
cd ../../../
npm run gui-server
```

## Usage

### Starting the GUI

#### Method 1: Direct Browser Launch
```bash
npm run gui
# Opens index.html in default browser
```

#### Method 2: With WebSocket Server
```bash
npm run gui-server
# Server starts on http://localhost:8080
# WebSocket on ws://localhost:8081
```

#### Method 3: Electron App (Desktop)
```bash
npm run gui-electron
# Launches as standalone desktop application
```

### Terminal Commands

The terminal supports all claude-flow commands:

```bash
# Swarm Management
swarm init                  # Initialize swarm with mesh topology
swarm status                # Check swarm health
agent spawn                 # Create new agent
agent list                  # List active agents

# Memory Operations  
memory store                # Store key-value pair
memory retrieve             # Get stored value

# Session Management
session save                # Save current session
session list                # List available sessions

# Performance
benchmark run               # Run performance tests
neural status              # Check neural network status
```

### Agent Types

Available agent types for spawning:
- `researcher` - Information gathering
- `coder` - Code implementation
- `analyst` - Data analysis
- `optimizer` - Performance optimization
- `coordinator` - Task orchestration
- `tester` - Testing and validation
- `reviewer` - Code review
- `architect` - System design
- `documenter` - Documentation
- `monitor` - System monitoring
- `specialist` - Domain-specific tasks

### Memory Management

Store and retrieve data with namespace support:

```javascript
// Store data
Key: "swarm/config"
Value: {"topology": "mesh", "agents": 5}

// Namespaces
- default    - General storage
- swarm      - Swarm configuration
- agents     - Agent states
- sessions   - Session data
- neural     - Neural network models
```

### Session Recovery

Sessions are automatically saved and can be restored:

1. **Auto-save** - On disconnect or server shutdown
2. **Manual save** - Click "Save Current Session"
3. **Resume** - Select from saved sessions list
4. **State includes**:
   - Active agents
   - Command history
   - Memory store
   - Timestamps

## Architecture

### Frontend (index.html)
- Pure JavaScript (no framework dependencies)
- Responsive CSS Grid layout
- WebSocket client for real-time updates
- Modal system for detailed views
- Canvas-based 3D visualization

### Backend (server.js)
- Express HTTP server (port 8080)
- WebSocket server (port 8081)
- Child process execution for CLI commands
- File-based session persistence
- Memory management with namespaces

### Communication Flow
```
GUI <-> WebSocket <-> Server <-> claude-flow CLI
         Real-time      Exec        Commands
```

## Development

### File Structure
```
.claude/gui/
├── index.html          # Main GUI interface
├── server.js           # WebSocket & HTTP server
├── README.md           # Documentation
└── sessions/           # Saved session files
    └── *.json          # Session state dumps
```

### Adding New Features

1. **New Activity Card**:
   - Add card HTML in activity-grid
   - Create modal content function
   - Implement WebSocket handlers

2. **New Commands**:
   - Add to commandMap in server.js
   - Create handler function
   - Update terminal autocomplete

3. **New Agent Types**:
   - Add to agent-type select options
   - Update spawnAgent function
   - Add metrics tracking

## Testing

### Manual Testing Checklist

#### Sprint 1: Core Features
- [ ] Terminal command execution
- [ ] Agent spawning (all 11 types)
- [ ] Real-time output streaming
- [ ] Connection status updates

#### Sprint 2: Session Management
- [ ] Save current session
- [ ] List saved sessions
- [ ] Resume from saved session
- [ ] Persist through restart

#### Sprint 3: 3D Simulation
- [ ] Demo mode particles
- [ ] Live mode updates
- [ ] Replay mode functionality
- [ ] WebGL rendering performance

#### Sprint 4: Browser Compatibility
- [ ] Chrome 90+
- [ ] Firefox 88+
- [ ] Safari 14+
- [ ] Edge 90+

### Automated Testing
```bash
# Run test suite
npm test

# Check coverage
npm run test:coverage
```

## Performance

### Metrics
- **WebSocket Latency**: <50ms average
- **Command Execution**: <100ms response
- **Memory Usage**: <100MB typical
- **Session Save**: <500ms
- **3D Rendering**: 60 FPS target

### Optimization Tips
- Limit terminal history to 1000 lines
- Batch WebSocket messages
- Use session recovery for long tasks
- Enable hardware acceleration for 3D

## Troubleshooting

### Connection Issues
```bash
# Check if server is running
curl http://localhost:8080/health

# Test WebSocket
wscat -c ws://localhost:8081

# Check ports
lsof -i :8080
lsof -i :8081
```

### Common Problems

1. **"Connection refused"**
   - Ensure server is running: `npm run gui-server`
   - Check firewall settings

2. **"Command not found"**
   - Verify claude-flow installation: `npx claude-flow@alpha --version`
   - Check PATH configuration

3. **"Session not restored"**
   - Check sessions/ directory permissions
   - Verify JSON file integrity

4. **"3D not rendering"**
   - Enable WebGL in browser
   - Check GPU acceleration settings

## Security

- Local-only WebSocket (no external access)
- Command sanitization before execution
- Session files encrypted (planned)
- No sensitive data in browser storage

## Future Enhancements

- [ ] Multi-user support with authentication
- [ ] Cloud session backup
- [ ] Advanced 3D visualization modes
- [ ] Plugin system for custom cards
- [ ] Mobile responsive design
- [ ] Dark/Light theme toggle
- [ ] Export reports as PDF
- [ ] Integration with CI/CD pipelines

## Support

- **Issues**: https://github.com/ruvnet/claude-flow/issues
- **Documentation**: https://github.com/ruvnet/claude-flow
- **Discord**: [Join Community](https://discord.gg/claude-flow)

## License

MIT License - See LICENSE file for details

---

Built with ❤️ for the Claude-Flow community