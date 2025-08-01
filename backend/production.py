"""Production-ready configuration for the HiveMemory Dashboard backend."""

import os
import logging
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with production defaults."""
    
    # Application settings
    app_name: str = "HiveMemory Dashboard API"
    app_version: str = "1.0.0"
    environment: str = "production"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", "8000"))
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Memory and agent settings
    memory_path: str = "/mnt/memory"
    agents_path: str = "/app/agents"
    logs_path: str = "/app/logs"
    
    # CORS settings
    cors_origins: list[str] = ["*"]  # Configure appropriately for production
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # WebSocket settings
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10
    
    # Agent control settings
    max_agent_restarts: int = 3
    agent_restart_delay: int = 5
    agent_startup_timeout: int = 30
    
    # Memory watcher settings
    memory_watch_recursive: bool = True
    memory_event_buffer_size: int = 1000
    
    # Performance settings
    max_workers: Optional[int] = None
    keep_alive: int = 2
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def setup_logging() -> None:
    """Configure application logging for production."""
    settings = get_settings()
    
    # Create logs directory if it doesn't exist
    os.makedirs(settings.logs_path, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=settings.log_format,
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(
                os.path.join(settings.logs_path, "app.log"),
                mode='a',
                encoding='utf-8'
            )
        ]
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("websockets").setLevel(logging.WARNING)


def create_required_directories() -> None:
    """Create required directories for production deployment."""
    settings = get_settings()
    
    directories = [
        settings.memory_path,
        settings.agents_path,
        settings.logs_path,
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Ensured directory exists: {directory}")


# Production-specific configurations
PRODUCTION_CONFIG = {
    "host": "0.0.0.0",
    "port": int(os.getenv("PORT", "8000")),
    "log_level": "info",
    "access_log": True,
    "server_header": False,  # Hide server header for security
    "date_header": False,    # Hide date header for security
    "workers": 1,            # Single worker for now, can be scaled
    "worker_class": "uvicorn.workers.UvicornWorker",
    "keepalive": 2,
    "max_requests": 1000,
    "max_requests_jitter": 100,
    "timeout": 30,
    "graceful_timeout": 30,
}


if __name__ == "__main__":
    """Production entry point."""
    import uvicorn
    from main import app
    
    # Setup production environment
    setup_logging()
    create_required_directories()
    
    settings = get_settings()
    
    logging.info(f"Starting {settings.app_name} v{settings.app_version}")
    logging.info(f"Environment: {settings.environment}")
    logging.info(f"Port: {settings.port}")
    logging.info(f"Memory path: {settings.memory_path}")
    logging.info(f"Agents path: {settings.agents_path}")
    
    # Run with production configuration
    uvicorn.run(
        app,
        **PRODUCTION_CONFIG
    )