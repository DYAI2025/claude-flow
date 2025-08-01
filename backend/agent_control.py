"""Agent control functions for managing HiveMemory agents."""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
import uuid
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

from models import Agent, AgentStatus, AgentType, AgentConfig, AgentControlResponse, AgentAction


class AgentController:
    """Controller for managing agents."""
    
    def __init__(self, agents_dir: str = "./agents", memory_dir: str = "/mnt/memory"):
        self.agents_dir = Path(agents_dir)
        self.memory_dir = Path(memory_dir)
        self.agents: Dict[str, Agent] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self._running = True
        
        # Create directories if they don't exist
        self.agents_dir.mkdir(exist_ok=True)
        self.memory_dir.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize the agent controller."""
        await self.load_agent_configs()
        asyncio.create_task(self._monitor_agents())
        
    async def load_agent_configs(self):
        """Load agent configurations from YAML files."""
        config_files = list(self.agents_dir.glob("*.yaml")) + list(self.agents_dir.glob("*.yml"))
        
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                    
                agent_config = AgentConfig(
                    name=config_data.get('name', config_file.stem),
                    type=AgentType(config_data.get('type', 'custom')),
                    description=config_data.get('description'),
                    capabilities=config_data.get('capabilities', []),
                    config_path=str(config_file),
                    environment=config_data.get('environment', {}),
                    max_restarts=config_data.get('max_restarts', 3),
                    restart_delay=config_data.get('restart_delay', 5)
                )
                
                agent_id = config_data.get('id', str(uuid.uuid4()))
                agent = Agent(
                    id=agent_id,
                    name=agent_config.name,
                    type=agent_config.type,
                    status=AgentStatus.STOPPED,
                    config=agent_config,
                    memory_path=str(self.memory_dir / agent_id)
                )
                
                self.agents[agent_id] = agent
                
            except Exception as e:
                print(f"Error loading config from {config_file}: {e}")
                
    async def start_agent(self, agent_id: str) -> AgentControlResponse:
        """Start an agent."""
        if agent_id not in self.agents:
            return AgentControlResponse(
                success=False,
                agent_id=agent_id,
                action=AgentAction.START,
                status=AgentStatus.ERROR,
                error="Agent not found"
            )
            
        agent = self.agents[agent_id]
        
        if agent.status == AgentStatus.RUNNING:
            return AgentControlResponse(
                success=False,
                agent_id=agent_id,
                action=AgentAction.START,
                status=agent.status,
                error="Agent is already running"
            )
            
        try:
            # Update agent status
            agent.status = AgentStatus.STARTING
            agent.started_at = datetime.now()
            
            # Create agent memory directory
            agent_memory_dir = Path(agent.memory_path)
            agent_memory_dir.mkdir(parents=True, exist_ok=True)
            
            # Prepare environment
            env = os.environ.copy()
            env.update(agent.config.environment)
            env['AGENT_ID'] = agent_id
            env['AGENT_NAME'] = agent.name
            env['AGENT_TYPE'] = agent.type.value
            env['MEMORY_PATH'] = str(agent_memory_dir)
            
            # Start the agent process
            # This is a placeholder - in real implementation, this would start the actual agent
            cmd = [sys.executable, "-c", f"""
import time
import json
from pathlib import Path

agent_id = '{agent_id}'
memory_path = Path('{agent_memory_dir}')

# Simulate agent running
while True:
    # Write heartbeat
    heartbeat_file = memory_path / 'heartbeat.json'
    heartbeat_file.write_text(json.dumps({{
        'agent_id': agent_id,
        'timestamp': time.time(),
        'status': 'running'
    }}))
    time.sleep(5)
"""]
            
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes[agent_id] = process
            agent.pid = process.pid
            agent.status = AgentStatus.RUNNING
            agent.error_message = None
            
            return AgentControlResponse(
                success=True,
                agent_id=agent_id,
                action=AgentAction.START,
                status=agent.status,
                message=f"Agent {agent.name} started successfully"
            )
            
        except Exception as e:
            agent.status = AgentStatus.ERROR
            agent.error_message = str(e)
            
            return AgentControlResponse(
                success=False,
                agent_id=agent_id,
                action=AgentAction.START,
                status=agent.status,
                error=str(e)
            )
            
    async def stop_agent(self, agent_id: str) -> AgentControlResponse:
        """Stop an agent."""
        if agent_id not in self.agents:
            return AgentControlResponse(
                success=False,
                agent_id=agent_id,
                action=AgentAction.STOP,
                status=AgentStatus.ERROR,
                error="Agent not found"
            )
            
        agent = self.agents[agent_id]
        
        if agent.status != AgentStatus.RUNNING:
            return AgentControlResponse(
                success=False,
                agent_id=agent_id,
                action=AgentAction.STOP,
                status=agent.status,
                error="Agent is not running"
            )
            
        try:
            agent.status = AgentStatus.STOPPING
            
            if agent_id in self.processes:
                process = self.processes[agent_id]
                
                # Try graceful shutdown first
                process.terminate()
                
                # Wait for process to terminate
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    process.kill()
                    process.wait()
                    
                del self.processes[agent_id]
                
            agent.status = AgentStatus.STOPPED
            agent.pid = None
            
            return AgentControlResponse(
                success=True,
                agent_id=agent_id,
                action=AgentAction.STOP,
                status=agent.status,
                message=f"Agent {agent.name} stopped successfully"
            )
            
        except Exception as e:
            agent.status = AgentStatus.ERROR
            agent.error_message = str(e)
            
            return AgentControlResponse(
                success=False,
                agent_id=agent_id,
                action=AgentAction.STOP,
                status=agent.status,
                error=str(e)
            )
            
    async def restart_agent(self, agent_id: str) -> AgentControlResponse:
        """Restart an agent."""
        # First stop the agent
        stop_response = await self.stop_agent(agent_id)
        
        if not stop_response.success and stop_response.error != "Agent is not running":
            return AgentControlResponse(
                success=False,
                agent_id=agent_id,
                action=AgentAction.RESTART,
                status=stop_response.status,
                error=f"Failed to stop agent: {stop_response.error}"
            )
            
        # Wait for restart delay
        agent = self.agents.get(agent_id)
        if agent:
            await asyncio.sleep(agent.config.restart_delay)
            agent.restart_count += 1
            
        # Start the agent
        start_response = await self.start_agent(agent_id)
        
        return AgentControlResponse(
            success=start_response.success,
            agent_id=agent_id,
            action=AgentAction.RESTART,
            status=start_response.status,
            message=f"Agent restarted successfully" if start_response.success else None,
            error=start_response.error
        )
        
    async def get_agent_status(self, agent_id: str) -> AgentControlResponse:
        """Get agent status."""
        if agent_id not in self.agents:
            return AgentControlResponse(
                success=False,
                agent_id=agent_id,
                action=AgentAction.STATUS,
                status=AgentStatus.ERROR,
                error="Agent not found"
            )
            
        agent = self.agents[agent_id]
        
        # Check if process is still running
        if agent.status == AgentStatus.RUNNING and agent_id in self.processes:
            process = self.processes[agent_id]
            if process.poll() is not None:
                # Process has terminated
                agent.status = AgentStatus.ERROR
                agent.error_message = "Process terminated unexpectedly"
                agent.pid = None
                del self.processes[agent_id]
                
        return AgentControlResponse(
            success=True,
            agent_id=agent_id,
            action=AgentAction.STATUS,
            status=agent.status,
            message=f"Agent {agent.name} is {agent.status.value}"
        )
        
    async def get_all_agents(self) -> List[Agent]:
        """Get all agents."""
        return list(self.agents.values())
        
    async def _monitor_agents(self):
        """Monitor agent health and restart if necessary."""
        while self._running:
            for agent_id, agent in self.agents.items():
                if agent.status == AgentStatus.RUNNING:
                    # Check heartbeat
                    heartbeat_file = Path(agent.memory_path) / 'heartbeat.json'
                    
                    if heartbeat_file.exists():
                        try:
                            with open(heartbeat_file, 'r') as f:
                                heartbeat = json.load(f)
                                last_heartbeat = heartbeat.get('timestamp', 0)
                                
                            # Check if heartbeat is recent (within 30 seconds)
                            if time.time() - last_heartbeat > 30:
                                agent.status = AgentStatus.ERROR
                                agent.error_message = "Heartbeat timeout"
                                
                                # Auto-restart if under max restarts
                                if agent.restart_count < agent.config.max_restarts:
                                    await self.restart_agent(agent_id)
                        except Exception:
                            pass
                            
                    # Update last heartbeat
                    agent.last_heartbeat = datetime.now()
                    
            await asyncio.sleep(10)
            
    async def shutdown(self):
        """Shutdown all agents and cleanup."""
        self._running = False
        
        # Stop all running agents
        for agent_id in list(self.agents.keys()):
            if self.agents[agent_id].status == AgentStatus.RUNNING:
                await self.stop_agent(agent_id)