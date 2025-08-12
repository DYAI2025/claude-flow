const WebSocket = require('ws');
const express = require('express');
const path = require('path');
const { exec } = require('child_process');
const fs = require('fs').promises;

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 8080;
const WS_PORT = process.env.WS_PORT || 8081;

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname)));

// CORS headers for development
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

// Session storage
const sessions = new Map();
const activeAgents = new Map();
const memoryStore = new Map();

// WebSocket server
const wss = new WebSocket.Server({ port: WS_PORT });

console.log(`WebSocket server running on ws://localhost:${WS_PORT}`);
console.log(`HTTP server will run on http://localhost:${PORT}`);

// WebSocket connection handler
wss.on('connection', (ws) => {
    const sessionId = generateSessionId();
    sessions.set(sessionId, {
        id: sessionId,
        startTime: Date.now(),
        agents: [],
        commands: [],
        memory: new Map()
    });

    console.log(`New client connected: ${sessionId}`);

    // Send initial session info
    ws.send(JSON.stringify({
        type: 'session-update',
        sessionId: sessionId
    }));

    // Handle messages from client
    ws.on('message', async (message) => {
        try {
            const data = JSON.parse(message);
            await handleClientMessage(ws, sessionId, data);
        } catch (error) {
            console.error('Error handling message:', error);
            ws.send(JSON.stringify({
                type: 'error',
                message: error.message
            }));
        }
    });

    // Handle disconnection
    ws.on('close', () => {
        console.log(`Client disconnected: ${sessionId}`);
        // Save session state for recovery
        saveSessionState(sessionId);
    });

    // Handle errors
    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
    });
});

// Handle client messages
async function handleClientMessage(ws, sessionId, data) {
    const session = sessions.get(sessionId);
    
    switch(data.type) {
        case 'execute-command':
            await executeCommand(ws, session, data.command);
            break;
            
        case 'spawn-agent':
            spawnAgent(ws, session, data.agentType);
            break;
            
        case 'store-memory':
            storeMemory(ws, session, data.key, data.value);
            break;
            
        case 'retrieve-memory':
            retrieveMemory(ws, session, data.key);
            break;
            
        case 'save-session':
            await saveSessionState(sessionId);
            ws.send(JSON.stringify({
                type: 'message',
                text: `Session ${sessionId} saved successfully`
            }));
            break;
            
        case 'list-sessions':
            const savedSessions = await listSavedSessions();
            ws.send(JSON.stringify({
                type: 'sessions-list',
                sessions: savedSessions
            }));
            break;
            
        case 'resume-session':
            await resumeSession(ws, data.sessionId);
            break;
            
        case 'get-status':
            sendSystemStatus(ws);
            break;
            
        default:
            ws.send(JSON.stringify({
                type: 'error',
                message: `Unknown command type: ${data.type}`
            }));
    }
}

// Execute shell command
async function executeCommand(ws, session, command) {
    console.log(`Executing command: ${command}`);
    session.commands.push({
        command: command,
        timestamp: Date.now()
    });

    // Map GUI commands to actual npx claude-flow commands
    const commandMap = {
        'help': 'npx claude-flow@alpha --help',
        'swarm init': 'npx claude-flow@alpha swarm init mesh',
        'agent spawn': 'npx claude-flow@alpha agent spawn researcher',
        'list agents': 'npx claude-flow@alpha agent list',
        'swarm status': 'npx claude-flow@alpha swarm status',
        'memory store': 'npx claude-flow@alpha memory store',
        'memory retrieve': 'npx claude-flow@alpha memory retrieve',
        'neural status': 'npx claude-flow@alpha neural status',
        'hooks list': 'npx claude-flow@alpha hooks list',
        'session save': 'npx claude-flow@alpha session save',
        'session list': 'npx claude-flow@alpha session list',
        'benchmark run': 'npx claude-flow@alpha benchmark run'
    };

    const actualCommand = commandMap[command] || command;

    exec(actualCommand, { maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
        if (error) {
            ws.send(JSON.stringify({
                type: 'command-output',
                output: `Error: ${error.message}`
            }));
            return;
        }

        if (stderr) {
            ws.send(JSON.stringify({
                type: 'command-output',
                output: `Warning: ${stderr}`
            }));
        }

        // Send output in chunks for better streaming
        const lines = stdout.split('\n');
        lines.forEach(line => {
            if (line.trim()) {
                ws.send(JSON.stringify({
                    type: 'command-output',
                    output: line
                }));
            }
        });

        // Parse output for agent updates
        if (command.includes('agent')) {
            updateAgentCount(ws, session);
        }
    });
}

// Spawn agent
function spawnAgent(ws, session, agentType) {
    const agentId = `agent-${Date.now()}`;
    const agent = {
        id: agentId,
        type: agentType,
        status: 'active',
        startTime: Date.now()
    };
    
    session.agents.push(agent);
    activeAgents.set(agentId, agent);
    
    ws.send(JSON.stringify({
        type: 'agent-update',
        count: session.agents.filter(a => a.status === 'active').length
    }));
    
    ws.send(JSON.stringify({
        type: 'command-output',
        output: `Agent ${agentType} (${agentId}) spawned successfully`
    }));
}

// Memory operations
function storeMemory(ws, session, key, value) {
    session.memory.set(key, value);
    memoryStore.set(`${session.id}:${key}`, value);
    
    ws.send(JSON.stringify({
        type: 'memory-update',
        memory: Array.from(session.memory.entries())
    }));
    
    ws.send(JSON.stringify({
        type: 'command-output',
        output: `Memory stored: ${key}`
    }));
}

function retrieveMemory(ws, session, key) {
    const value = session.memory.get(key);
    
    ws.send(JSON.stringify({
        type: 'command-output',
        output: value ? `${key}: ${value}` : `Key not found: ${key}`
    }));
}

// Session management
async function saveSessionState(sessionId) {
    const session = sessions.get(sessionId);
    if (!session) return;
    
    const sessionData = {
        id: session.id,
        startTime: session.startTime,
        endTime: Date.now(),
        agents: session.agents,
        commands: session.commands,
        memory: Array.from(session.memory.entries())
    };
    
    const sessionsDir = path.join(__dirname, 'sessions');
    await fs.mkdir(sessionsDir, { recursive: true });
    
    const filePath = path.join(sessionsDir, `${sessionId}.json`);
    await fs.writeFile(filePath, JSON.stringify(sessionData, null, 2));
    
    console.log(`Session ${sessionId} saved to ${filePath}`);
}

async function listSavedSessions() {
    const sessionsDir = path.join(__dirname, 'sessions');
    
    try {
        const files = await fs.readdir(sessionsDir);
        const sessions = [];
        
        for (const file of files) {
            if (file.endsWith('.json')) {
                const filePath = path.join(sessionsDir, file);
                const data = await fs.readFile(filePath, 'utf8');
                const session = JSON.parse(data);
                sessions.push({
                    id: session.id,
                    startTime: session.startTime,
                    endTime: session.endTime,
                    agentCount: session.agents.length,
                    commandCount: session.commands.length
                });
            }
        }
        
        return sessions;
    } catch (error) {
        console.error('Error listing sessions:', error);
        return [];
    }
}

async function resumeSession(ws, sessionId) {
    const sessionsDir = path.join(__dirname, 'sessions');
    const filePath = path.join(sessionsDir, `${sessionId}.json`);
    
    try {
        const data = await fs.readFile(filePath, 'utf8');
        const sessionData = JSON.parse(data);
        
        // Restore session
        const session = {
            id: sessionData.id,
            startTime: sessionData.startTime,
            agents: sessionData.agents,
            commands: sessionData.commands,
            memory: new Map(sessionData.memory)
        };
        
        sessions.set(sessionData.id, session);
        
        // Restore agents
        sessionData.agents.forEach(agent => {
            activeAgents.set(agent.id, agent);
        });
        
        ws.send(JSON.stringify({
            type: 'session-restored',
            session: sessionData
        }));
        
        ws.send(JSON.stringify({
            type: 'command-output',
            output: `Session ${sessionId} restored successfully`
        }));
        
    } catch (error) {
        ws.send(JSON.stringify({
            type: 'error',
            message: `Failed to restore session: ${error.message}`
        }));
    }
}

// System status
function sendSystemStatus(ws) {
    const status = {
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        activeSessions: sessions.size,
        activeAgents: activeAgents.size,
        timestamp: Date.now()
    };
    
    ws.send(JSON.stringify({
        type: 'status-update',
        status: status
    }));
}

// Update agent count
function updateAgentCount(ws, session) {
    exec('npx claude-flow@alpha agent list', (error, stdout) => {
        if (!error && stdout) {
            // Parse agent count from output
            const matches = stdout.match(/(\d+) active agents?/i);
            if (matches) {
                const count = parseInt(matches[1]);
                ws.send(JSON.stringify({
                    type: 'agent-update',
                    count: count
                }));
            }
        }
    });
}

// Utility functions
function generateSessionId() {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// HTTP routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        uptime: process.uptime(),
        sessions: sessions.size,
        agents: activeAgents.size
    });
});

app.get('/api/sessions', async (req, res) => {
    const savedSessions = await listSavedSessions();
    res.json(savedSessions);
});

app.get('/api/agents', (req, res) => {
    res.json(Array.from(activeAgents.values()));
});

app.get('/api/memory', (req, res) => {
    res.json(Array.from(memoryStore.entries()));
});

// Start HTTP server
app.listen(PORT, () => {
    console.log(`HTTP server running on http://localhost:${PORT}`);
    console.log(`Open http://localhost:${PORT} in your browser to access the GUI`);
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\nShutting down gracefully...');
    
    // Save all active sessions
    for (const [sessionId] of sessions) {
        await saveSessionState(sessionId);
    }
    
    // Close WebSocket server
    wss.close(() => {
        console.log('WebSocket server closed');
    });
    
    process.exit(0);
});

// Error handling
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});