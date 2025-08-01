"""Pydantic models for HiveMemory Dashboard."""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class AgentType(str, Enum):
    """Agent type enumeration."""
    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    COORDINATOR = "coordinator"
    CUSTOM = "custom"


class AgentConfig(BaseModel):
    """Agent configuration model."""
    name: str
    type: AgentType
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    config_path: Optional[str] = None
    environment: Dict[str, str] = Field(default_factory=dict)
    max_restarts: int = 3
    restart_delay: int = 5


class Agent(BaseModel):
    """Agent model with runtime information."""
    id: str
    name: str
    type: AgentType
    status: AgentStatus
    pid: Optional[int] = None
    started_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    restart_count: int = 0
    error_message: Optional[str] = None
    config: AgentConfig
    memory_path: Optional[str] = None


class MemoryEventType(str, Enum):
    """Memory event type enumeration."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    ACCESSED = "accessed"


class MemoryEvent(BaseModel):
    """Memory event model."""
    id: str
    timestamp: datetime
    event_type: MemoryEventType
    agent_id: Optional[str] = None
    file_path: str
    content: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentAction(str, Enum):
    """Agent control actions."""
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    STATUS = "status"


class AgentControlRequest(BaseModel):
    """Request model for agent control."""
    agent_id: str
    action: AgentAction


class AgentControlResponse(BaseModel):
    """Response model for agent control."""
    success: bool
    agent_id: str
    action: AgentAction
    status: AgentStatus
    message: Optional[str] = None
    error: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any]


class MemoryQuery(BaseModel):
    """Query model for memory search."""
    query: Optional[str] = None
    agent_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_types: Optional[List[MemoryEventType]] = None
    limit: int = 100
    offset: int = 0


class SystemStatus(BaseModel):
    """System status model."""
    agents: List[Agent]
    total_memory_events: int
    active_watchers: int
    system_health: str
    uptime: float
    last_update: datetime = Field(default_factory=datetime.now)