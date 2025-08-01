"""Main FastAPI application for HiveMemory Dashboard."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent_control import AgentController
from memory_watcher import MemoryWatcher, MemoryEvent
from models import (
    Agent, AgentControlRequest, AgentControlResponse, AgentStatus,
    MemoryQuery, SystemStatus, WebSocketMessage
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manager for WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def broadcast(self, message: WebSocketMessage):
        """Broadcast a message to all connected clients."""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message.model_dump(mode='json'))
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
                
        # Clean up disconnected clients
        for connection in disconnected:
            try:
                self.disconnect(connection)
            except Exception:
                pass


# Global instances
agent_controller: Optional[AgentController] = None
memory_watcher: Optional[MemoryWatcher] = None
ws_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global agent_controller, memory_watcher
    
    # Startup
    logger.info("Starting HiveMemory Dashboard backend...")
    
    # Initialize agent controller
    agent_controller = AgentController()
    await agent_controller.initialize()
    
    # Initialize memory watcher
    memory_watcher = MemoryWatcher()
    await memory_watcher.start()
    
    # Subscribe to memory events
    def on_memory_event(event: MemoryEvent):
        """Handle memory events and broadcast to WebSocket clients."""
        asyncio.create_task(ws_manager.broadcast(WebSocketMessage(
            type="memory_event",
            data=event.model_dump(mode='json')
        )))
        
    memory_watcher.subscribe("memory:all", on_memory_event)
    
    logger.info("HiveMemory Dashboard backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down HiveMemory Dashboard backend...")
    
    await agent_controller.shutdown()
    await memory_watcher.stop()
    
    logger.info("HiveMemory Dashboard backend shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="HiveMemory Dashboard API",
    description="Backend API for HiveMemory multi-agent system dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# Agent management endpoints
@app.get("/api/agents", response_model=List[Agent])
async def get_agents():
    """Get all agents."""
    return await agent_controller.get_all_agents()


@app.get("/api/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    """Get a specific agent."""
    agents = await agent_controller.get_all_agents()
    agent = next((a for a in agents if a.id == agent_id), None)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    return agent


@app.post("/api/agents/control", response_model=AgentControlResponse)
async def control_agent(request: AgentControlRequest):
    """Control an agent (start, stop, restart, status)."""
    if request.action == "start":
        response = await agent_controller.start_agent(request.agent_id)
    elif request.action == "stop":
        response = await agent_controller.stop_agent(request.agent_id)
    elif request.action == "restart":
        response = await agent_controller.restart_agent(request.agent_id)
    elif request.action == "status":
        response = await agent_controller.get_agent_status(request.agent_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    # Broadcast agent status update
    agent = next((a for a in await agent_controller.get_all_agents() if a.id == request.agent_id), None)
    if agent:
        await ws_manager.broadcast(WebSocketMessage(
            type="agent_update",
            data=agent.model_dump(mode='json')
        ))
        
    return response


# Memory endpoints
@app.get("/api/memory/files")
async def get_memory_files(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type (observer_stream or core_memory)")
):
    """Get memory files."""
    files = await memory_watcher.get_memory_files(agent_id, memory_type)
    return files


@app.post("/api/memory/query")
async def query_memory(query: MemoryQuery):
    """Query memory events."""
    # This is a placeholder - implement actual query logic based on your requirements
    return {
        "results": [],
        "total": 0,
        "query": query.model_dump()
    }


# System status endpoint
@app.get("/api/system/status", response_model=SystemStatus)
async def get_system_status():
    """Get overall system status."""
    agents = await agent_controller.get_all_agents()
    
    return SystemStatus(
        agents=agents,
        total_memory_events=0,  # Implement actual counting
        active_watchers=memory_watcher.get_active_watchers(),
        system_health="healthy" if all(a.status != AgentStatus.ERROR for a in agents) else "degraded",
        uptime=0.0  # Implement actual uptime tracking
    )


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await ws_manager.connect(websocket)
    
    try:
        # Send initial status
        agents = await agent_controller.get_all_agents()
        await websocket.send_json({
            "type": "initial_state",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "agents": [agent.model_dump(mode='json') for agent in agents]
            }
        })
        
        # Keep connection alive
        while True:
            # Wait for client messages
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Use production configuration if available
    if os.getenv("ENVIRONMENT") == "production":
        try:
            from production import setup_logging, create_required_directories, PRODUCTION_CONFIG
            setup_logging()
            create_required_directories()
            uvicorn.run(app, **PRODUCTION_CONFIG)
        except ImportError:
            # Fallback to development configuration
            uvicorn.run(
                "main:app",
                host="0.0.0.0",
                port=int(os.getenv("PORT", "8000")),
                log_level="info"
            )
    else:
        # Development configuration
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8000")),
            reload=True,
            log_level="info"
        )