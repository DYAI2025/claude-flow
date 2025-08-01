"""Memory watcher for monitoring file changes in observer_stream and core_memory."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Callable, Optional, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from models import MemoryEvent, MemoryEventType


class MemoryEventHandler(FileSystemEventHandler):
    """Handler for file system events in memory directories."""
    
    def __init__(self, callback: Callable[[MemoryEvent], None], agent_id: Optional[str] = None):
        self.callback = callback
        self.agent_id = agent_id
        
    def _create_memory_event(self, event: FileSystemEvent, event_type: MemoryEventType) -> Optional[MemoryEvent]:
        """Create a memory event from a file system event."""
        if event.is_directory:
            return None
            
        # Only process JSON files
        if not event.src_path.endswith('.json'):
            return None
            
        try:
            content = None
            if event_type != MemoryEventType.DELETED and os.path.exists(event.src_path):
                with open(event.src_path, 'r') as f:
                    content = json.load(f)
                    
            memory_event = MemoryEvent(
                id=f"{event_type.value}_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                event_type=event_type,
                agent_id=self.agent_id,
                file_path=event.src_path,
                content=content,
                metadata={
                    'file_size': os.path.getsize(event.src_path) if os.path.exists(event.src_path) else 0,
                    'file_name': os.path.basename(event.src_path)
                }
            )
            
            return memory_event
            
        except Exception as e:
            print(f"Error creating memory event: {e}")
            return None
            
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        memory_event = self._create_memory_event(event, MemoryEventType.CREATED)
        if memory_event:
            self.callback(memory_event)
            
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        memory_event = self._create_memory_event(event, MemoryEventType.MODIFIED)
        if memory_event:
            self.callback(memory_event)
            
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        memory_event = self._create_memory_event(event, MemoryEventType.DELETED)
        if memory_event:
            self.callback(memory_event)


class MemoryWatcher:
    """Watcher for monitoring memory directories."""
    
    def __init__(self, memory_base_dir: str = "/mnt/memory"):
        self.memory_base_dir = Path(memory_base_dir)
        self.observers: Dict[str, Observer] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self._running = False
        
    async def start(self):
        """Start the memory watcher."""
        self._running = True
        
        # Create base directory if it doesn't exist
        self.memory_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Start monitoring existing directories
        await self._scan_and_watch_directories()
        
        # Start directory scanner task
        asyncio.create_task(self._directory_scanner())
        
    async def stop(self):
        """Stop the memory watcher."""
        self._running = False
        
        # Stop all observers
        for observer in self.observers.values():
            observer.stop()
            observer.join()
            
        self.observers.clear()
        
    def subscribe(self, event_type: str, callback: Callable[[MemoryEvent], None]):
        """Subscribe to memory events."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(callback)
        
    def unsubscribe(self, event_type: str, callback: Callable[[MemoryEvent], None]):
        """Unsubscribe from memory events."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].remove(callback)
            
    def _emit_event(self, event: MemoryEvent):
        """Emit a memory event to all subscribers."""
        # Emit to specific event type handlers
        event_type_key = f"memory:{event.event_type.value}"
        if event_type_key in self.event_handlers:
            for handler in self.event_handlers[event_type_key]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
                    
        # Emit to all event handlers
        if "memory:all" in self.event_handlers:
            for handler in self.event_handlers["memory:all"]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
                    
    async def _scan_and_watch_directories(self):
        """Scan for memory directories and start watching them."""
        # Watch the base memory directory
        self._watch_directory(str(self.memory_base_dir), None)
        
        # Watch subdirectories (agent memory directories)
        for subdir in self.memory_base_dir.iterdir():
            if subdir.is_dir():
                agent_id = subdir.name
                
                # Watch observer_stream directory
                observer_stream_dir = subdir / "observer_stream"
                if observer_stream_dir.exists():
                    self._watch_directory(str(observer_stream_dir), agent_id)
                    
                # Watch core_memory directory
                core_memory_dir = subdir / "core_memory"
                if core_memory_dir.exists():
                    self._watch_directory(str(core_memory_dir), agent_id)
                    
    def _watch_directory(self, path: str, agent_id: Optional[str] = None):
        """Start watching a directory."""
        if path in self.observers:
            return  # Already watching
            
        try:
            event_handler = MemoryEventHandler(self._emit_event, agent_id)
            observer = Observer()
            observer.schedule(event_handler, path, recursive=True)
            observer.start()
            
            self.observers[path] = observer
            print(f"Started watching directory: {path}")
            
        except Exception as e:
            print(f"Error watching directory {path}: {e}")
            
    async def _directory_scanner(self):
        """Periodically scan for new directories to watch."""
        while self._running:
            await asyncio.sleep(10)  # Check every 10 seconds
            
            try:
                # Check for new agent directories
                for subdir in self.memory_base_dir.iterdir():
                    if subdir.is_dir():
                        agent_id = subdir.name
                        
                        # Check observer_stream directory
                        observer_stream_dir = subdir / "observer_stream"
                        if observer_stream_dir.exists() and str(observer_stream_dir) not in self.observers:
                            self._watch_directory(str(observer_stream_dir), agent_id)
                            
                        # Check core_memory directory
                        core_memory_dir = subdir / "core_memory"
                        if core_memory_dir.exists() and str(core_memory_dir) not in self.observers:
                            self._watch_directory(str(core_memory_dir), agent_id)
                            
            except Exception as e:
                print(f"Error in directory scanner: {e}")
                
    async def get_memory_files(self, agent_id: Optional[str] = None, 
                             memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all memory files for an agent or all agents."""
        files = []
        
        if agent_id:
            # Get files for specific agent
            agent_dir = self.memory_base_dir / agent_id
            if agent_dir.exists():
                files.extend(await self._scan_memory_directory(agent_dir, agent_id, memory_type))
        else:
            # Get files for all agents
            for subdir in self.memory_base_dir.iterdir():
                if subdir.is_dir():
                    files.extend(await self._scan_memory_directory(subdir, subdir.name, memory_type))
                    
        return files
        
    async def _scan_memory_directory(self, agent_dir: Path, agent_id: str, 
                                   memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scan a memory directory for JSON files."""
        files = []
        
        directories = []
        if memory_type:
            if memory_type == "observer_stream" and (agent_dir / "observer_stream").exists():
                directories.append(agent_dir / "observer_stream")
            elif memory_type == "core_memory" and (agent_dir / "core_memory").exists():
                directories.append(agent_dir / "core_memory")
        else:
            # Scan both directories
            if (agent_dir / "observer_stream").exists():
                directories.append(agent_dir / "observer_stream")
            if (agent_dir / "core_memory").exists():
                directories.append(agent_dir / "core_memory")
                
        for directory in directories:
            for json_file in directory.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        content = json.load(f)
                        
                    files.append({
                        'agent_id': agent_id,
                        'memory_type': directory.name,
                        'file_path': str(json_file),
                        'file_name': json_file.name,
                        'content': content,
                        'modified_at': datetime.fromtimestamp(json_file.stat().st_mtime),
                        'size': json_file.stat().st_size
                    })
                except Exception as e:
                    print(f"Error reading file {json_file}: {e}")
                    
        return files
        
    def get_active_watchers(self) -> int:
        """Get the number of active directory watchers."""
        return len(self.observers)